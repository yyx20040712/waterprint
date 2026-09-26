"""联合枚举末空级放宽重试件（beam.py 500 行贴墙拆件——批5 结构债）。

输入:  _JointSearch 编排器（预算/基线/beam 主循环复用）+选项+基线指标
输出:  RetryOutcome（重试产出 / skip 事由 no_domain|budget）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批5 2026-09-26 拆件：beam.py 500 行恰满零余量——批1 裁决部
#   P2「beam.py 零行余量结构债」+批2b 欠账③兑现；final_eval 拆件先例
#   同构。语义自 beam._relaxed_grids/_relaxed_retry 迁入，除批5 三处
#   分叉强化（AUD-W7 后半/P2）：
#   ①名义/真实放宽区分：relaxed_grids 仅收录经放宽实际变化的单元
#     （range 域扩宽）——离散档原样=名义放宽不重试（旧行为=原样网格
#     全量重跑同结果且注记误导「已放宽」）；
#   ②预算拒注记分叉：放宽后行估计超 max_total_rows → skip_reason=
#     "budget"（旧=静默 None，调用面注记误报「无可放宽 range 域」）；
#   ③timeout 维度：放宽后末段截断 → final_infeasible 诊断附
#     timeout_truncated=True（旧行为=截断与域拒不可区分）。
#
# 【公开接口】（包内私有面——不经子包 __init__ 再导出，消费=beam 单点）
#   relaxed_grids(grids, factor) -> dict[unit_id, 放宽声明]：真实域扩
#       单元集（factor<=1 由 diagnose.relax_grid_specs 域守卫拒）
#   retry_joint(search, options, baseline) -> RetryOutcome：全量目标
#       重搜索（merged 网格覆盖）+末段复验；预算超限 skip；诊断载荷
#       relaxed=True 面（stage_empty/final_infeasible）随件产出
#   class RetryOutcome(不可变)：outcome（JointOutcome|None）+
#       skip_reason（"budget"|"no_domain"|None——outcome 非 None 时恒 None）
#
# 【行为规格】与 beam 原实现同源（W8/R7：一次放宽不迭代；基线重执行；
#   静态预检口径统一执法——超预算不重试不抛）。
#
# 【测试要求】经 beam 全链测试覆盖（本件拆件非独立规格面——final_eval
#   先例）；skip 事由三支点由批5 草稿用例锚（.workflow 呈批件）。
#
# 【参照】.workflow/b4-3/design-final.md §一 W8/R7；audit-norms-20260925
#   AUD-W7/P2；AGENTS §2 预算墙拆件纪律
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

from waterprint.solution.joint_enumeration import diagnose as joint_diagnose
from waterprint.solution.joint_enumeration import stage as joint_stage

if TYPE_CHECKING:  # 编排器与选项类型面（beam 定义——运行期零导入防环）
    from waterprint.solution.joint_enumeration.beam import (
        JointEnumerationOptions,
        _JointSearch,
    )


@dataclass(frozen=True)
@final
class RetryOutcome:
    """放宽重试产出（不可变）：outcome=None 时 skip_reason 必非空（事由分叉）。"""

    outcome: Any | None  # JointOutcome（TYPE_CHECKING 面注记——见上）
    skip_reason: str | None


def relaxed_grids(
    grids: Mapping[str, tuple[Mapping[str, Any], ...]], factor: float
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    """末空级一次放宽的真实域扩覆盖（批5 名义/真实放宽区分）。

    仅收录经 relax_grid_specs 后实际变化的单元（range 域两侧各扩
    (factor−1)/2×域宽）；离散档原样=名义放宽不进重试面（重跑同网格
    零信息量且「已放宽」注记失实——诚实跳过归调用面注记）。
    """
    widened: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for unit_id, specs in grids.items():
        if not specs:
            continue
        relaxed = joint_diagnose.relax_grid_specs(specs, factor)
        if relaxed != tuple(specs):
            widened[unit_id] = relaxed
    return widened


def retry_joint(
    search: _JointSearch,  # 包内私有协作面（beam 编排器——拆件消费单点）
    options: JointEnumerationOptions,
    baseline: Mapping[str, float],
) -> RetryOutcome:
    """末空级放宽一次（W8/R7）：merged 网格全量目标重搜索+末段复验。

    预算超限=skip_reason "budget"（不抛——静态预检口径统一执法；调用
    面按事由分叉注记）；stage_empty/final_infeasible 诊断面随 retry 产
    出标注 relaxed=True；timeout 截断维度透出（timeout_truncated）。
    """
    grids = {
        unit_id: joint_stage.grid_of(
            joint_stage.resolve_grid_specs(
                unit_id, search.assembled, options.grids.get(unit_id)
            ),
            search.env.assumptions,
        )
        for unit_id in search.targets
    }
    if not search.within_budget(grids):
        return RetryOutcome(None, "budget")
    source, _ = search.baseline()
    staged = search.staged(source, grids)
    if isinstance(staged, Mapping):
        return RetryOutcome(
            search.outcome((), {"kind": "stage_empty", "stage": staged, "relaxed": True}),
            None,
        )
    combos = search.final_eval([params for params, _ in staged], baseline)
    if any(combo.feasible for combo in combos):
        return RetryOutcome(search.outcome(combos, None), None)
    return RetryOutcome(
        search.outcome(combos, {
            "kind": "final_infeasible", "relaxed": True,
            "timeout_truncated": search.truncated,
            "note": (
                "末空级已按 relax_factor 放宽一次后复验仍无可行组合"
                + ("；timeout 截断——复验未完成" if search.truncated else "")
            ),
        }),
        None,
    )


__all__ = ["RetryOutcome", "relaxed_grids", "retry_joint"]
