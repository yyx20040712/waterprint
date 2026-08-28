"""solver golden 测试：三段管线设计（docs/norms/network_manning.md 追认值）。

输入:  tmp 三段 xlsx fixture（手算表输入表逐字：W1-W2/W2-W3/W3-W4）
       + 真库 coefficients（load_network_coefficients 装配——cli 同口径）
输出:  三段设计结果 vs 手算表"三段结果表"期望值逐段断言

容差口径（docstring 记档——冻结 §三 D 条"实现者按实现形态取"）：
- 管径/跌水：精确断言（枚举入选值恰 DN400/DN500/DN500，本例三井跌水 0）；
- h/D 与流速：1e-4（手算表期望值为 4dp 誊录，实现为解析式——誊录舍入
  误差上界 5e-5，取 1e-4 工程容差带）；
- 坡度与管底标高：1e-9（纯算术链 (g_s−g_e)/L 与 invert−slope·L，
  浮点噪声量级远小于 1e-9）；
- 满流参照 v_full（补充锚）：1e-4（同誊录口径）。
"""

from __future__ import annotations

import importlib
from pathlib import Path

from openpyxl import Workbook

_excel = importlib.import_module("waterprint.network.excel_io")
read_network_excel = getattr(_excel, "read_network_excel")
write_result_sheet = getattr(_excel, "write_result_sheet")
_solver = importlib.import_module("waterprint.network.solver")
PipeSegment = getattr(_solver, "PipeSegment")
build_design_options = getattr(_solver, "build_design_options")
design_pipes = getattr(_solver, "design_pipes")
load_network_coefficients = getattr(_solver, "load_network_coefficients")
_manning = importlib.import_module("waterprint.network.manning")
manning_velocity = getattr(_manning, "manning_velocity")

# 期望值唯一来源=docs/norms/network_manning.md（RATIFY4 追认 2026-08-28）：
# 三段结果表 + 满流参照补充锚 + 弃用链（DN300 h/D 0.6875>0.55 等）。
_COLUMNS = (
    "segment_id",
    "design_flow",
    "length",
    "ground_start",
    "ground_end",
    "upstream_invert",
    "pipe_type",
)
_SEGMENTS = (
    ("W1-W2", 0.050, 150.0, 52.00, 51.40, 48.00, "concrete"),
    ("W2-W3", 0.120, 200.0, 51.40, 50.60, None, "concrete"),
    ("W3-W4", 0.200, 180.0, 50.60, 49.60, None, "concrete"),
)
# (segment_id, DN m, 坡度, h/D, v, 起管底, 末管底, v_full)
_EXPECTED = (
    ("W1-W2", 0.400, 0.004, 0.4272, 0.9762, 48.00, 47.40, 1.0481),
    ("W2-W3", 0.500, 0.004, 0.5015, 1.2178, 47.40, 46.60, 1.2163),
    ("W3-W4", 0.500, 1.0 / 180.0, 0.6227, 1.5558, 46.60, 45.60, 1.4334),
)


def _write_fixture(path: Path) -> None:
    """照模板 v1.0.0 形态写三段 fixture（表头+注记行+三数据行）。"""
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "pipes"
    sheet.append(list(_COLUMNS))
    sheet.append(("模板版本 v1.0.0（golden fixture——手算表三段输入逐字）。",))
    for row in _SEGMENTS:
        sheet.append(row)
    workbook.save(path)


def _design_with_real_library(xlsx: Path):
    """read→真库装配 options→design（cli network 子命令同口径）。"""
    segments = read_network_excel(xlsx)
    options = build_design_options(load_network_coefficients(), "concrete")
    return design_pipes(segments, options)


def test_three_segment_golden_values(tmp_path: Path) -> None:
    """三段主表：管径/坡度/h/D/v/管底标高逐段对照手算表追认值。"""
    xlsx = tmp_path / "pipes.xlsx"
    _write_fixture(xlsx)
    design = _design_with_real_library(xlsx)
    assert tuple(result.segment_id for result in design.results) == (
        "W1-W2",
        "W2-W3",
        "W3-W4",
    )
    for result, expected in zip(design.results, _EXPECTED, strict=True):
        _, diameter, slope, depth, velocity, start, end, _ = expected
        assert result.diameter == diameter
        assert abs(result.slope - slope) < 1e-9
        assert abs(result.depth_ratio - depth) < 1e-4
        assert abs(result.velocity - velocity) < 1e-4
        assert abs(result.invert_start - start) < 1e-9
        assert abs(result.invert_end - end) < 1e-9


def test_golden_anchors_and_clean_run(tmp_path: Path) -> None:
    """补充锚：满流 v_full 参照+三井跌水 0+无失败/警示/并联+埋深恒 4.0。"""
    xlsx = tmp_path / "pipes.xlsx"
    _write_fixture(xlsx)
    design = _design_with_real_library(xlsx)
    assert design.failures == ()
    assert design.drop_wells == ()
    assert design.parallel == ()
    assert design.warnings == ()
    for result, expected in zip(design.results, _EXPECTED, strict=True):
        v_full_ref = expected[7]
        v_full = manning_velocity(result.diameter, result.slope, 0.013)
        assert abs(v_full - v_full_ref) < 1e-4
    grounds = {row[0]: (row[3], row[4]) for row in _SEGMENTS}
    for result in design.results:
        start_ground, end_ground = grounds[result.segment_id]
        assert abs(start_ground - result.invert_start - 4.0) < 1e-9
        assert abs(end_ground - result.invert_end - 4.0) < 1e-9


def test_golden_determinism_double_run(tmp_path: Path) -> None:
    """确定性双跑：同输入两次设计逐字段相等（R1 枚举语义显式）。"""
    xlsx = tmp_path / "pipes.xlsx"
    _write_fixture(xlsx)
    first = _design_with_real_library(xlsx)
    second = _design_with_real_library(xlsx)
    assert first == second


def test_golden_result_sheet_roundtrip(tmp_path: Path) -> None:
    """cli 闭环末端：design → write_result_sheet 落盘可读（零公式展示面）。"""
    xlsx = tmp_path / "pipes.xlsx"
    _write_fixture(xlsx)
    design = _design_with_real_library(xlsx)
    references = {
        result.segment_id: (
            manning_velocity(result.diameter, result.slope, 0.013),
            _manning.full_flow_capacity(result.diameter, result.slope, 0.013),
        )
        for result in design.results
    }
    out = write_result_sheet(xlsx, design, references)
    assert out == xlsx
    assert read_network_excel(xlsx) == read_network_excel(xlsx)
