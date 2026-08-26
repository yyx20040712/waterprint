"""plan_view 镜像测试：单体平面图（标注完备/工况标注/纯投影接线）。

输入:  waterprint.drafting.plan_view 公开符号
输出:  平面图契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.drafting.plan_view")
unit_plan = getattr(_mod, "unit_plan", None)

pytestmark = pytest.mark.skipif(
    unit_plan is None,
    reason="实现未就绪：waterprint.drafting.plan_view（M2）",
)


def _snap(uid: str, dims: dict[str, float]):
    from waterprint.contracts.result_schema import UnitResultSnapshot

    return UnitResultSnapshot(
        unit_id=uid, outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _styles():
    from waterprint.drafting.styles import base_styles

    return base_styles()


def test_entrypoint_frozen() -> None:
    """入口冻结：unit_plan(unit_result, manifest, styles, condition_key, options)。"""
    assert callable(unit_plan)


def test_annotation_completeness_wiring() -> None:
    """R3 接线断言（M2 实质化）：已知矩形池平面含总尺寸/分格/标高标注实体。

    占位实质化（DRAFT 批总授权先例）：chenshachi（总尺寸 l_straight/d +
    水深标高 h2）与 cugeshan（总尺寸 L/B + 分格 n_gap）两类矩形池平面——
    三类标注实体（dim_linear 总尺寸/分格跨 + elev_symbol 标高）全存在，
    且标注取数 dims 键经 source_key 可回溯（R1 纯投影）。
    """
    from waterprint.contracts.drawing_projection import PROJECTION_TABLE

    grit = unit_plan(
        _snap("municipal_chenshachi",
              {"l_straight": 4.5, "d": 3.0, "h2": 1.25, "h_total": 3.0}),
        PROJECTION_TABLE["municipal_chenshachi"], _styles(), "design",
    )
    dims = [e for e in grit.entities if e.kind == "dim_linear"]
    elevs = [e for e in grit.entities if e.kind == "elev_symbol"]
    assert {e.source_key for e in dims} >= {"l_straight", "d"}  # 总尺寸双向
    assert {e.source_key for e in elevs} == {"h2"}  # 标高符号（水深键）
    assert any(e.params.get("water_depth") == pytest.approx(1.25) for e in elevs)
    assert any("condition=design" in e.text for e in grit.entities)  # R4 工况

    screen = unit_plan(
        _snap("municipal_cugeshan",
              {"L": 1.8, "B": 0.7, "n_gap": 20.0, "H": 1.0}),
        PROJECTION_TABLE["municipal_cugeshan"], _styles(), "design",
    )
    spans = [e for e in screen.entities if e.kind == "dim_linear"
             and e.source_key == "n_gap"]
    assert spans  # 分格尺寸标注存在（gap_count 驱动）
    partitions = [e for e in screen.entities if e.kind == "line"
                  and e.source_key == "n_gap"]
    assert partitions  # 分格线图元存在
