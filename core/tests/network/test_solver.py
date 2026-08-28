"""solver 镜像测试：管径枚举设计（确定性/跌水井判定/无解显式接线）。

输入:  waterprint.network.solver 公开符号
输出:  设计语义断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.network.solver")
design_pipes = getattr(_mod, "design_pipes")
DesignOptions = getattr(_mod, "DesignOptions")
PipeSegment = getattr(_mod, "PipeSegment")

pytestmark = pytest.mark.skipif(
    design_pipes is None,
    reason="实现未就绪：waterprint.network.solver（M3）",
)


def test_entrypoint_frozen() -> None:
    """入口冻结：design_pipes(segments, options)——约束值全部来自数据（R4）。"""
    assert callable(design_pipes)


def test_infeasible_segment_reports_reasons_wiring() -> None:
    """R5 接线断言（NET2 填真实现）：无解段显式失败+违反约束清单含约束名。

    构造不可行段：Q=50 m³/s 超全部可选管径满流输水能力（承压）且埋深
    12 m 超上限 6 m——失败原因清单须完整含 max_fill_ratio 与 max_depth
    两约束名（禁止静默选最接近）；并联双管半量仍无解（R3 不越权补救）。
    """
    options = DesignOptions(
        available_diameters=(
            0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.5,
        ),
        min_velocity=0.6,
        max_velocity=3.0,
        max_depth=6.0,
        fill_ratio_steps=((0.3, 0.55), (0.45, 0.65), (0.9, 0.70), (1.5, 0.75)),
        roughness=0.013,
    )
    segment = PipeSegment(
        segment_id="W9-W10",
        design_flow=50.0,
        length=150.0,
        ground_start=52.0,
        ground_end=51.4,
        upstream_invert=40.0,
    )
    design = design_pipes([segment], options)
    assert len(design.failures) == 1
    assert design.failures[0].segment_id == "W9-W10"
    reasons = "\n".join(design.failures[0].reasons)
    assert "max_fill_ratio" in reasons
    assert "max_depth" in reasons
    assert design.results == ()
    assert design.parallel == ()
