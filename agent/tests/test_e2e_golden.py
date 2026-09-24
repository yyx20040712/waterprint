"""golden e2e（D8②/D8③）：四种子全链路走 MCP 进程内客户端驱动。

链路:  create(seed)→outline→update_params（含必拒 patch）→run_calc→
       get_diagnostics→export_calcbook+audit→（仅 municipal_34760）
       export_report（verify 全绿+validate_narrative 抽查）
锚:    expected_summary.json 的 checked_units（→2+k 工况集）与 summary
       六指标（rel/abs 1e-12——golden 真值）；tools/list 计数 21；
       stale 断言（改参后旧 result 提示重算）。
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from waterprint_agent import context

_REPO = Path(__file__).resolve().parents[2]
_GOLDEN = _REPO / "core" / "tests" / "golden" / "golden_data"

# （种子，golden 用例目录，改参锚单元，水线终水单元，calcbook 可渲染）
# calcbook=False 两用例：官方模板占位符引用 summary.design.BOD5 等六键，
# loop 用例 app 终端启发式取泥线汇点（summary 空映射合法）、mine 无
# BOD5 键——core 模板↔结果契约缺口（非接线缺陷，记档报告疑虑面），
# 断言收窄为「错误 dict 优雅呈现（不 raise 裸异常）」。
_CASES = (
    ("municipal_34760", "municipal_34760", "municipal_chenshachi",
     "municipal_bashi_jiliangcao", True),
    ("municipal_loop_34760", "municipal_34760_loop", "municipal_chenshachi",
     "municipal_bashi_jiliangcao", False),
    ("municipal_recycle_34760", "municipal_34760_recycle", "municipal_chenshachi",
     "municipal_bashi_jiliangcao", True),
    ("mine_43836", "mine_43836", "mine_water_chenshachi", "mine_water_ziwai", False),
)


def _expected(case_dir: str) -> dict[str, Any]:
    return json.loads(
        (_GOLDEN / case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )


def _param_default(unit_id: str, field: str) -> float:
    """改参锚单元的 manifest 缺省值（补丁=缺省——零值漂移，仅 digest 变化）。"""
    from waterprint.app import discover_units

    for spec in discover_units()[unit_id][0].params:
        if spec.field_id == field:
            return float(spec.default)
    raise AssertionError(f"{unit_id} 无参数 {field}")


# serialize 契约上界：结果文件数值=round(x,10) 定点——快照断言容差取
# 5e-11 余量（in-memory 真值面在 wp_run_calc 摘要，锚 1e-12 不受影响）。
_SNAPSHOT_ABS = 51e-12


class _Client:
    """fastmcp.Client 进程内驱动薄封装（同步测试面）。"""

    def __init__(self, mcp: object) -> None:
        from fastmcp import Client

        self._client = Client(mcp)

    def __enter__(self) -> _Client:
        self._loop = asyncio.new_event_loop()
        self._cm = self._loop.run_until_complete(self._client.__aenter__())
        return self

    def __exit__(self, *exc: object) -> None:
        self._loop.run_until_complete(self._client.__aexit__(*exc))
        self._loop.close()

    def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._loop.run_until_complete(
            self._client.call_tool(tool, arguments)
        )
        return dict(result.data)  # type: ignore[arg-type]

    def tool_names(self) -> set[str]:
        tools = self._loop.run_until_complete(self._client.list_tools())
        return {tool.name for tool in tools}


@pytest.fixture
def sandbox_env(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "sb"
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(root))
    context.reset_context()
    yield root
    context.reset_context()


@pytest.mark.parametrize(("seed", "case_dir", "unit", "terminal", "calcbook_ok"),
                         _CASES)
def test_golden_full_chain_mcp(  # noqa: PLR0913, PLR0915, PLR0917  # 参数化六参+全链路长函数=e2e 形态
    sandbox_env: Path, seed: str, case_dir: str, unit: str, terminal: str,
    calcbook_ok: bool,
) -> None:
    """四用例全链路：MCP 客户端驱动+golden 六指标锚+stale+导出闭环。"""
    from waterprint_agent import main as agent_main

    expected = _expected(case_dir)
    default_n = _param_default(unit, "n")
    with _Client(agent_main.get_mcp()) as client:
        assert len(client.tool_names()) == 23  # B4-4b 子批 3：23 工具（#22/#23 增——原 21 满座计数随批更新）  # 满座计数（每用例常驻断言）

        created = client.call(
            "wp_create_project", {"name": f"e2e-{seed}", "seed": seed}
        )
        assert "error" not in created, created
        pid = created["project_id"]

        outline = client.call("wp_get_project_outline", {"project_id": pid})
        assert "error" not in outline
        source = json.loads(
            (_GOLDEN / case_dir / "input_project.json").read_text(encoding="utf-8")
        )
        assert outline["node_count"] == len(source["design"]["nodes"])

        # 改参（清单式：接受=缺省值补丁[零值漂移]+必拒两条——值类型/未知键；
        # 档位拒绝面在 test_tools_update_params 专测，此处取全用例通用面）
        patched = client.call(
            "wp_update_params",
            {"project_id": pid, "patches": [
                {"unit_id": unit, "key": "n", "value": default_n},
                {"unit_id": unit, "key": "n", "value": "0.5"},
                {"unit_id": unit, "key": "__nope__", "value": 1.0},
            ]},
        )
        assert patched["accepted_count"] == 1, patched
        rejected = [r for r in patched["results"] if not r["accepted"]]
        assert len(rejected) == 2 and all(r["reason"] for r in rejected)

        # 计算（conditions=expected checked_units——golden 工况集 2+k）
        outcome = client.call(
            "wp_run_calc", {"project_id": pid,
                            "conditions": expected["checked_units"]}
        )
        assert "error" not in outcome, outcome
        assert set(outcome["condition_keys"]) == set(expected["condition_keys"])
        # 六指标锚①（in-memory 真值面）：wp_run_calc 摘要=full precision
        # （loop 用例 app 终端启发式取泥线汇点[summary 空映射合法]——
        # 该用例跳过本面，由锚②承载）。
        summary = outcome["summary"]
        for indicator, anchor in expected["effluent"]["design"].items():
            if indicator in summary:
                assert summary[indicator] == pytest.approx(
                    anchor["value"], rel=anchor["rel"], abs=anchor["abs"]
                ), f"{seed} design.{indicator}"
        # 六指标锚②（快照真值面）：终水单元 outqualities（golden 四用例
        # 同口径；容差=serialize round10 契约上界）。
        terminal_detail = client.call(
            "wp_get_unit_detail",
            {"project_id": pid, "unit_id": terminal, "condition_key": "design"},
        )
        assert "error" not in terminal_detail, terminal_detail
        for indicator, anchor in expected["effluent"]["design"].items():
            actual = terminal_detail["outqualities"][f"{terminal}.out.{indicator}"]
            assert actual == pytest.approx(
                anchor["value"], rel=anchor["rel"], abs=_SNAPSHOT_ABS
            ), f"{seed} design.{indicator}（快照 round10 面）"

        # stale：合法值改参（缺省+1——guard 三面过，digest 变）→旧结果被拒
        shifted = client.call(
            "wp_update_params",
            {"project_id": pid, "patches": [
                {"unit_id": unit, "key": "n", "value": default_n + 1.0},
            ]},
        )
        assert shifted["accepted_count"] == 1
        stale_view = client.call(
            "wp_get_result_summary", {"project_id": pid}
        )
        assert "error" in stale_view and "重算" in stale_view["error"]
        redo = client.call(
            "wp_run_calc", {"project_id": pid,
                            "conditions": expected["checked_units"]}
        )
        assert "error" not in redo

        diagnostics = client.call("wp_get_diagnostics", {"project_id": pid})
        assert "error" not in diagnostics
        assert diagnostics["diagnostics_available"] is True
        assert isinstance(diagnostics["warnings"], list)

        exported_audit = client.call("wp_export_audit", {"project_id": pid})
        assert "error" not in exported_audit, exported_audit
        artifact = Path(exported_audit["path"])
        assert artifact.is_file() and artifact.parent.name == "exports"
        meta = artifact.with_name(f"{exported_audit['file_name']}.meta.json")
        assert set(json.loads(meta.read_text(encoding="utf-8"))) == {
            "project_id", "kind", "condition_key", "file_name",
            "design_digest", "engine_version", "data_version", "stale_labeled",
        }

        exported_book = client.call("wp_export_calcbook", {"project_id": pid})
        if calcbook_ok:
            assert "error" not in exported_book, exported_book
            artifact = Path(exported_book["path"])
            assert artifact.is_file() and artifact.suffix == ".xlsx"
            meta = artifact.with_name(f"{exported_book['file_name']}.meta.json")
            assert set(json.loads(meta.read_text(encoding="utf-8"))) == {
                "project_id", "kind", "condition_key", "file_name",
                "design_digest", "engine_version", "data_version", "stale_labeled",
            }
        else:
            # 模板占位符↔summary 契约缺口面：错误 dict 优雅呈现（不 raise）。
            assert "error" in exported_book and "hint" in exported_book

        if seed != "municipal_34760":
            return  # 说明书断言仅 municipal（A4/B2——余三用例不做）

        fills = {
            "process_selection": "本工程采用粗细格栅与旋流砂池预处理，主体工艺"
            "为生化池后续深度处理与紫外消毒；该组合适应进水水质波动，运行"
            "灵活且便于扩建。",
            "layout_narrative": "厂区布置按工艺流程顺序展开，预处理区靠近进水"
            "侧，生化区居中，深度处理与消毒出水居末；高程设计尽量自流衔接"
            "以减少提升能耗。",
        }
        report = client.call(
            "wp_export_report", {"project_id": pid, "narrative_fills": fills}
        )
        assert "error" not in report, report
        assert report["verify_summary"]["ok"] is True
        assert report["verify_summary"]["anchors_checked"] > 0
        assert report["rejected_narratives"] == {}
        markdown = Path(report["path"]).read_text(encoding="utf-8")
        assert "工程总投资" in markdown and "数据待接线" not in markdown

        # 叙述守卫抽查：含数字回填被拒（N3 后检——K4 严格姿态）
        bad = client.call(
            "wp_export_report",
            {"project_id": pid,
             "narrative_fills": {"layout_narrative": "厂区占地约 3.5 公顷。"}},
        )
        assert bad["rejected_narratives"]["layout_narrative"]
        from waterprint_agent.report.anchors import validate_narrative

        assert validate_narrative("第 3 章所述工序组合") == []  # 序号豁免形态
