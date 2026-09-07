"""快照回归首样：三导出产物内容哈希锚（ADR-010 落地，批 14）。

输入:  golden_data/municipal_34760（v1 正门一次实跑）+ 三产物正门
       （trace.calcbook/trace.audit/drafting.dxf_writer[经 plan_view 供实体]）
输出:  syrupy 快照断言——三产物渲染后取 sha256 内容哈希（十六进制入
       ambr）；快照文件本目录 __snapshots__/（不入锁定清单：更新走显式
       --snapshot-update+人审，与只读测试的人类解锁流程互补）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（ADR-010 D1~D7，2026-09-07 用户批复；设计简报 task-14-brief）：
#   对象面 v1=三产物（xlsx/DXF/HTML）；scene/IFC 不入 v1（D1）。
#   快照形态=内容哈希（D2）——锚产物内容，非时钟/注册序/压缩层噪声：
#   · HTML：全文件字节直读（零已知噪声）；
#   · xlsx：zip 条目链（名+解压载荷逐条拼接）；docProps/core.xml 载荷
#     内 dcterms:modified 值归一——openpyxl save/load 链路强制刷新该值
#     为落盘时刻（缺陷①挂账：R4 字节确定性跨秒证伪；created 保留仍锚）；
#   · DXF：文本行序列；CLASSES+OBJECTS 两段记录块按组码 0 分界排序归
#     一——ezdxf 1.4.4 类注册序跨进程双稳态（缺陷②挂账：R3 跨进程证
#     伪；HEADER/TABLES/BLOCKS/ENTITIES 序保留仍锚=自有插入序）。
#   输入源纪律（D5）：golden 版本化数据+模板 created 归一定值（save
#   覆盖 modified 但保留 created——模板构造时钟会内嵌产物 core.xml）；
#   DXF 实体=golden 实跑 dims 经 unit_plan 纯投影（非测试自编数字）。
#   与既有双跑字节同测试正交互补（D6）：双跑证进程内确定性（自证），
#   快照锚跨版本回归（他证）。漂移处置流（D7）：快照红≠自动更新——
#   预期漂移（依赖升级/渲染有意改动/模板录入/ezdxf 新翻转面）走
#   --snapshot-update 重录+diff 人审入批注记；非预期漂移=回归缺陷走
#   R 轮修复，禁改快照遮蔽。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from syrupy.assertion import SnapshotAssertion

if TYPE_CHECKING:
    from waterprint.contracts.result_schema import PlantResult

pytestmark = pytest.mark.skipif(
    not (
        Path(__file__).resolve().parent.parent
        / "golden"
        / "golden_data"
        / "municipal_34760"
        / "expected_summary.json"
    ).is_file(),
    reason="golden 数据未整理（快照锚依赖 municipal_34760 v1 案例供数）",
)

_CASE = "municipal_34760"
_SNAPSHOT_UNIT = "municipal_chenshachi"  # DXF 首批单元（M0 预注 M2 落点）
# 模板 created 归一定值（设计 TD2——test_calcbook 同源最小模板+时钟归一）：
# openpyxl save 覆盖 modified 但保留 created——模板构造时钟内嵌产物
# core.xml，归一后 created 面可复现（D5 禁时钟）。
_FIXED_EPOCH = datetime(2000, 1, 1, tzinfo=UTC)
# xlsx 规范化：仅归一 core.xml 的 dcterms:modified 值（openpyxl 落盘链
# 强制刷新为当时刻——非内容时钟；其余载荷逐字节全锚）。
_MODIFIED_RE = re.compile(rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)")


@pytest.fixture(scope="module")
def v1_plant(golden_data_dir: Path) -> PlantResult:
    """v1 案例正门一次实跑（module 级共享——三用例同源同跑）。

    与 golden e2e 同口径三件：load_project → RunEnv（engine/data 版本=
    golden expected 冻结值）→ run_full_calc；返回 plant（含 1260 节点
    迹树+五工况快照+summary 六指标投影）。
    """
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    case_dir = golden_data_dir / _CASE
    expected = json.loads(
        (case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )
    project = load_project(case_dir / "input_project.json")
    # parents[3]=仓库根（core/tests/snapshots/ 上溯三级——golden e2e 同式）
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(
            Path(__file__).resolve().parents[3] / "data" / "coefficients"
        ),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    return run_full_calc(
        project, build_condition_set(expected["checked_units"]), env
    ).plant


def _minimal_template(path: Path) -> Path:
    """测试夹具自造最小 xlsx 模板（test_calcbook 同源形态+created 归一）。

    A1=迹树标记；B1=迹树+汇总混排标记（summary 键取 v1 案例真有键 SS
    ——原形 total_sludge 系 loop 前身键，v1/loop 案例均无）。
    """
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.active["A1"] = "{{trace[0].formula_id}}"
    workbook.active["B1"] = "输出={{trace[0].output}}；SS={{summary.design.SS}}"
    workbook.properties.created = _FIXED_EPOCH
    workbook.save(path)
    return path


def _canonical_xlsx_sha(path: Path) -> str:
    """xlsx 内容哈希：zip 条目链（名+解压载荷），modified 值归一。

    条目序与全部载荷（含 created）均锚定；压缩层（deflate/zlib 构建）
    与 modified 时钟面不参与——跨平台/跨进程稳定。
    """
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            payload = archive.read(name)
            if name == "docProps/core.xml":
                payload = _MODIFIED_RE.sub(rb"\1FIXED\2", payload)
            digest.update(name.encode("utf-8") + b"\0" + payload + b"\0")
    return digest.hexdigest()


def _section_ranges(lines: list[str]) -> dict[str, tuple[int, int]]:
    """DXF 各段行界（SECTION/2/<名>…ENDSEC——组码 0 边界对；畸形致漏段
    由缺段断言响失败）。"""
    ranges: dict[str, tuple[int, int]] = {}
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip() == "0" and lines[i + 1] == "SECTION":
            head = i + 2
            if head + 1 < len(lines) and lines[head].strip() == "2":
                name = lines[head + 1]
                end = head + 2
                while end + 1 < len(lines) and not (
                    lines[end].strip() == "0" and lines[end + 1] == "ENDSEC"
                ):
                    end += 1
                if end + 1 >= len(lines):
                    raise ValueError(f"DXF 段 {name} 无 ENDSEC 终界（畸形输入）")
                ranges[name] = (head + 2, end)
                i = end
                continue
        i += 1
    return ranges


def _canonical_dxf_sha(path: Path) -> str:
    """DXF 内容哈希：文本行序列，CLASSES+OBJECTS 记录块排序归一。

    记录块按组码 0 分界（CLASS/对象各一块）；两段记录序=ezdxf 注册序
    （跨进程双稳态，非内容）。HEADER/TABLES/BLOCKS/ENTITIES 序保留
    ——自有代码插入序=内容。段体行数非偶（组码-值配对破缺）=畸形输入
    抛错响失败，禁静默丢行归一（遮蔽真回归的孔——D 一审 G1-01）。
    """
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    ranges = _section_ranges(lines)
    for name in ("CLASSES", "OBJECTS"):
        if name not in ranges:
            raise ValueError(f"DXF 缺 {name} 段（畸形输入——快照锚面响失败）")
    canonical = list(lines)
    for name in ("CLASSES", "OBJECTS"):
        start, end = ranges[name]
        body = lines[start:end]
        if len(body) % 2 != 0:
            raise ValueError(
                f"DXF {name} 段体行数 {len(body)} 非偶（组码-值配对破缺）"
            )
        blocks: list[tuple[str, ...]] = []
        current: list[str] = []
        for i in range(0, len(body), 2):
            if body[i].strip() == "0":
                if current:
                    blocks.append(tuple(current))
                current = [body[i], body[i + 1]]
            else:
                current.extend((body[i], body[i + 1]))
        if current:
            blocks.append(tuple(current))
        merged: list[str] = []
        for block in sorted(blocks):
            merged.extend(block)
        canonical[start:end] = merged
    return hashlib.sha256("\n".join(canonical).encode("utf-8")).hexdigest()


def test_calcbook_xlsx_content_hash(
    v1_plant: PlantResult, tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """快照锚①：计算书 xlsx 内容哈希（golden 迹树+汇总经最小模板渲染）。"""
    from waterprint.trace.calcbook import render_calcbook

    out = render_calcbook(
        v1_plant.trace,
        v1_plant,
        _minimal_template(tmp_path / "tpl.xlsx"),
        tmp_path / "calcbook.xlsx",
    )
    assert _canonical_xlsx_sha(out) == snapshot


def test_audit_html_content_hash(
    v1_plant: PlantResult, tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """快照锚②：审计报告 HTML 内容哈希（golden 迹树全量 1260 节点）。"""
    from waterprint.trace.audit import render_audit_html

    out = render_audit_html(
        v1_plant.trace,
        v1_plant,
        tmp_path / "audit.html",
    )
    assert hashlib.sha256(out.read_bytes()).hexdigest() == snapshot


def test_dxf_content_hash(
    v1_plant: PlantResult, tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """快照锚③：DXF 图纸内容哈希（golden 旋流沉砂池 design 平面图）。"""
    from waterprint.contracts.drawing_projection import PROJECTION_TABLE
    from waterprint.drafting.dxf_writer import DrawingMeta, write_dxf
    from waterprint.drafting.plan_view import unit_plan
    from waterprint.drafting.styles import base_styles

    styles = base_styles()
    unit_result = v1_plant.conditions["design"][_SNAPSHOT_UNIT]
    entities = unit_plan(
        unit_result, PROJECTION_TABLE[_SNAPSHOT_UNIT], styles, "design"
    )
    repro = v1_plant.repro
    meta = DrawingMeta(
        title="旋流沉砂池平面图",
        condition_key="design",
        repro=(repro.design_hash, repro.engine_version, repro.data_version),
    )
    out = write_dxf(entities, styles, tmp_path / "plan.dxf", meta)
    assert _canonical_dxf_sha(out) == snapshot
