"""联合枚举诊断件：分层最小冲突集（首空级既有 diagnose+末空级一次放宽）。

输入:  首空级 pass_matrix+单元级约束+网格+冻结前缀 / 末空级网格声明+倍数
输出:  stage_conflicts 序列化诊断载荷（前缀注记）+ relax_grid_specs 放宽声明
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 定稿件 §一 W8/任务书 ②；镜像测试 tests/solution/test_joint_units.py）
#
# 【公开接口】
#   stage_conflicts(pass_matrix, constraints, grid, prefix) -> Mapping
#       首空级诊断：以冻结前缀为上下文调既有 diagnose_infeasibility
#       （solution/diagnose 正门——最小冲突集/失败计数/建议单源复用，
#       禁 B4 双胞胎）+frozen_prefix 注记（联合枚举语义面：该矩阵在
#       前缀参数下取得）。序列化=dataclasses.asdict（UI/载荷面）。
#   relax_grid_specs(specs, factor) -> tuple[Mapping, ...]
#       末空级一次放宽：range 域两侧各扩 (factor−1)/2×域宽（factor=2 →
#       域宽翻倍）；values 离散档（manifest 网格形态）无连续域可放=原样
#       保留（诚实注记归 beam 载荷——不编造档位）。
#
# 【行为规格】
#   R1 只建议不改值（solution/diagnose R5 同源——放宽重试由 beam 显式
#      二次调用承载，本件纯投影）。
#   R2 确定性：同输入同输出（进 UI 与日志）。
#
# 【测试要求】前缀注记+冲突集正确委托、range 放宽算式、离散档原样。
#
# 【参照】.workflow/b4-3/design-final.md §一 W8；solution/diagnose.py
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（enumerate 同款）

from waterprint.solution.diagnose import diagnose_infeasibility


def stage_conflicts(
    pass_matrix: pandas.DataFrame,
    constraints: Mapping[str, object],
    grid: object,
    prefix: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    """首空级诊断载荷：既有 diagnose 委托+冻结前缀注记（R1/规格头）。"""
    report = diagnose_infeasibility(pass_matrix, constraints, grid=grid)
    return {
        "minimal_conflicts": [sorted(conflict) for conflict in report.minimal_conflicts],
        "fail_counts": dict(report.fail_counts),
        "suggestions": [asdict(item) for item in report.suggestions],
        "frozen_prefix": {unit: dict(params) for unit, params in prefix.items()},
    }


def relax_grid_specs(
    specs: Sequence[Mapping[str, Any]], factor: float
) -> tuple[Mapping[str, Any], ...]:
    """末空级一次放宽：range 域两侧各扩 (factor−1)/2×域宽；离散档原样。"""
    if factor <= 1.0:
        raise ValueError(
            f"relax_factor 须 >1（放宽语义——registry solution.joint.relax_factor）：{factor!r}"
        )
    relaxed: list[Mapping[str, Any]] = []
    for spec in specs:
        rng = spec.get("range")
        if not (isinstance(rng, Mapping) and "min" in rng and "max" in rng):
            relaxed.append(spec)  # values 离散档：无连续域——原样（诚实注记归载荷）
            continue
        low, high = float(rng["min"]), float(rng["max"])
        pad = (high - low) * (factor - 1.0) / 2
        widened = dict(spec)
        widened["range"] = {"min": low - pad, "max": high + pad}
        relaxed.append(widened)
    return tuple(relaxed)


__all__ = ["relax_grid_specs", "stage_conflicts"]
