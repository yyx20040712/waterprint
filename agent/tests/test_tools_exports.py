"""test_tools_exports——导出组 #17~#21：产物+边车+说明书管线。

输入:  tmp_path 沙箱（模块级单例——一次 wp_run_calc 供五工具复读）
输出:  确定性命名/八键边车/说明书 verify 全绿+叙述拒绝面断言
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from waterprint_agent import context
from waterprint_agent.report.anchors import validate_narrative
from waterprint_agent.tools import calc, exports, projects

_META_KEYS = {
    "project_id", "kind", "condition_key", "file_name",
    "design_digest", "engine_version", "data_version", "stale_labeled",
}


@pytest.fixture(scope="module")
def sandbox() -> Path:
    """模块级沙箱：建项+算一次（五工具复读同一结果集）。"""
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="wp-exports-")) / "sb"
    patch = pytest.MonkeyPatch()
    patch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    created = asyncio.run(projects.wp_create_project(name="导出组", seed="municipal_34760"))
    outcome = asyncio.run(calc.wp_run_calc(created["project_id"]))
    assert "error" not in outcome, outcome
    yield root
    patch.undo()
    context.reset_context()


@pytest.fixture(scope="module")
def pid(sandbox: Path) -> str:
    files = list((sandbox / "projects").glob("*.wp.json"))
    assert len(files) == 1
    return files[0].name.removesuffix(".wp.json")


def _meta_of(sandbox: Path, file_name: str) -> dict:
    meta = sandbox / "exports" / f"{file_name}.meta.json"
    assert meta.is_file(), f"边车缺失：{meta}"
    return json.loads(meta.read_text(encoding="utf-8"))


def test_export_calcbook(sandbox: Path, pid: str) -> None:
    """#17：计算书 xlsx——确定性命名 {pid}-calcbook-all-{digest10}+八键边车。"""
    data = asyncio.run(exports.wp_export_calcbook(pid))
    assert "error" not in data, data
    name = data["file_name"]
    assert name.startswith(f"{pid}-calcbook-all-") and name.endswith(".xlsx")
    assert (sandbox / "exports" / name).is_file()
    meta = _meta_of(sandbox, name)
    assert set(meta) == _META_KEYS
    assert meta["kind"] == "calcbook" and meta["stale_labeled"] is False


def test_export_audit(sandbox: Path, pid: str) -> None:
    """#18：审计 HTML（flows.export_flow("audit") 正门）+.audit.html 诚实后缀。"""
    data = asyncio.run(exports.wp_export_audit(pid))
    assert "error" not in data, data
    name = data["file_name"]
    assert name.startswith(f"{pid}-audit-all-") and name.endswith(".audit.html")
    content = (sandbox / "exports" / name).read_text(encoding="utf-8")
    assert "<html" in content.lower()
    meta = _meta_of(sandbox, name)
    assert meta["kind"] == "audit" and meta["file_name"] == name


def test_export_dxf_plant_level(sandbox: Path, pid: str) -> None:
    """#19：DXF 总图（design 工况+site 装配）——{pid}-dxf-design-{digest10}.dxf。"""
    data = asyncio.run(exports.wp_export_dxf(pid))
    assert "error" not in data, data
    name = data["file_name"]
    assert name.startswith(f"{pid}-dxf-design-") and name.endswith(".dxf")
    assert (sandbox / "exports" / name).is_file()
    _meta_of(sandbox, name)


def test_export_dxf_unit_level(sandbox: Path, pid: str) -> None:
    """#19 单元图：unit 分量进名（{pid}-dxf-{unit}-design-…）。"""
    data = asyncio.run(
        exports.wp_export_dxf(pid, unit_id="municipal_aao", condition_key="avg")
    )
    assert "error" not in data, data
    assert data["file_name"].startswith(f"{pid}-dxf-municipal_aao-avg-")


def test_export_ifc(sandbox: Path, pid: str) -> None:
    """#20：IFC 模型——{pid}-ifc-design-{digest10}.ifc+边车。"""
    data = asyncio.run(exports.wp_export_ifc(pid))
    assert "error" not in data, data
    name = data["file_name"]
    assert name.startswith(f"{pid}-ifc-design-") and name.endswith(".ifc")
    assert (sandbox / "exports" / name).is_file()
    _meta_of(sandbox, name)


def test_export_requires_fresh_result(sandbox: Path) -> None:
    """导出组错误面：未算项目→错误 dict（先 wp_run_calc）。"""
    created = asyncio.run(projects.wp_create_project(name="未算导出", seed="blank"))
    data = asyncio.run(exports.wp_export_calcbook(created["project_id"]))
    assert "error" in data


def test_export_stale_refused(sandbox: Path, pid: str) -> None:
    """导出组 stale 门：改参后旧结果→拒导出（提示重算）+复原。"""
    asyncio.run(
        projects.wp_update_params(
            pid, patches=[{"unit_id": "municipal_chenshachi", "key": "n", "value": 4.0}]
        )
    )
    data = asyncio.run(exports.wp_export_calcbook(pid))
    assert "error" in data and "重算" in data["error"]
    asyncio.run(
        projects.wp_update_params(
            pid, patches=[{"unit_id": "municipal_chenshachi", "key": "n", "value": 2.0}]
        )
    )
    assert "error" not in asyncio.run(calc.wp_run_calc(pid))


def test_export_report_green_with_narrative(sandbox: Path, pid: str) -> None:
    """#21：说明书管线——estimate/layout 接线+verify 全绿落盘+叙述回填。"""
    fills = {
        "process_selection": "本工程采用粗细格栅与旋流砂池预处理，主体工艺为生化池"
        "后续深度处理与紫外消毒，污泥线浓缩脱水后外运处置；该组合适应进水水质"
        "波动，运行灵活且便于扩建。",
        "layout_narrative": "厂区布置按工艺流程顺序展开，预处理区靠近进水侧，"
        "生化区居中，深度处理与消毒出水居末；高程设计尽量自流衔接以减少提升"
        "能耗，并预留远期扩建用地与检修通道。",
    }
    data = asyncio.run(exports.wp_export_report(pid, narrative_fills=fills))
    assert "error" not in data, data
    path = Path(data["path"])
    assert path.is_file() and path.parent.name == "reports"  # normcase 归一比较
    summary = data["verify_summary"]
    assert summary["ok"] is True and summary["anchors_checked"] > 0
    assert data["rejected_narratives"] == {}
    markdown = path.read_text(encoding="utf-8")
    assert "本工程采用粗细格栅" in markdown  # 叙述回填在场
    assert "工程总投资" in markdown  # 第 6 章概算接线（D5① 收口）
    assert "布置数据块" in markdown  # 第 5 章布置接线（D5① 收口）
    assert "数据待接线" not in markdown  # 三个可选面全部就位


def test_export_report_rejects_digit_bearing_narrative(sandbox: Path, pid: str) -> None:
    """#21 叙述守卫：含数字回填被拒入 rejected_narratives（该槽回落占位）。"""
    bad = {"layout_narrative": "厂区占地约 3.5 公顷，日处理能力 34760 吨。"}
    data = asyncio.run(exports.wp_export_report(pid, narrative_fills=bad))
    assert "error" not in data, data
    rejected = data["rejected_narratives"]
    assert list(rejected) == ["layout_narrative"]
    assert rejected["layout_narrative"][0]["rule"] in {"arabic", "decimal", "unit_adjacent"}
    path = Path(data["path"])
    markdown = path.read_text(encoding="utf-8")
    assert "34760" not in markdown.split("## 附录")[0]  # 拒绝文本未入正文
    # validate_narrative 抽查（D8③）：占位文案零违例
    assert validate_narrative("（本段由撰写管线生成——见管线说明）") == []


def test_export_report_name_digest(sandbox: Path, pid: str) -> None:
    """#21 落盘名：reports/{pid}-report-{digest10}.md（digest 与结果一致）。"""
    data = asyncio.run(exports.wp_export_report(pid))
    assert "error" not in data, data
    results = sorted((sandbox / "results").glob(f"{pid}-*.result.json"))
    digest10 = results[-1].name.split("-")[-1].removesuffix(".result.json")
    assert Path(data["path"]).name == f"{pid}-report-{digest10}.md"
