"""联合枚举正门：选项 schema+编排入口+末空级诊断（批6g 拆件后主门面）。

输入:  ProjectFile+unit_ids+ConditionSet+RunEnv+选项（网格/约束覆盖+出水标准族）
输出:  JointOutcome（search_semantics+combos+diagnosis+budget_usage）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 终裁定稿 .workflow/b4-3/design-final.md——2026-09-20；
#   镜像测试 tests/solution/test_beam.py+benchmark/test_bench_joint.py）
#
# 【公开接口】
#   run_joint_enumerate(project, unit_ids, conditions, env, options)
#       -> JointOutcome（ADR-025 决策 1~6 落地正门；app 再导出=server
#       单入口 UF-33）
#   class JointEnumerationOptions(不可变)：grids（unit_id→轴声明覆盖，
#       缺省=manifest grid 档）/constraints（unit_id→单元级约束，server
#       装配 constraint_kb 同单单元源）/standards（出水标准族，worker 注入）
#       /assemble（类注入防环面——app 正门装配注入）/capex_data_dir
#       （批2b capex 装配数据目录——worker 注入 data_dir 同源单价包）
#   class JointOutcome(不可变)：search_semantics 四键（W3/W4/B1）+combos
#       +diagnosis+budget_usage{rows_evaluated,full_plant_evals,elapsed_ms,
#       truncated}（W1 截断：先到闸即停+部分结果诚实返回不报错）
#   class JointEnumerationTooLarge(Exception)：静态预检超限（rows>
#       max_total_rows 或 N>max_units）——422 面（W7 事前拒绝优于事后
#       截断；双闸定序：rows 静态预检为主，timeout 运行兜底）
#   estimate_rows(grid_sizes, beam_width, multiplier) -> float：g·(k^N−1)/(k−1)·W_s（k=1→g·N）
#
# 【行为规格】
#   R1 交付结构=分层序列化 beam（决策 2）：拓扑序逐单元枚举（基线上下文
#      冻结——B1 口径）→top-k 冻结传播→末段 k 组合全厂真值复验（W6 终裁：
#      直调 execute_graph 既有编排，不新写拓扑序不构成双轨）。
#   R2 评估口径=逐行 unit.compute 绕过缓存（决策 3）；CacheKey 挂账 B12。
#   R3 工况=基线搜索+末段全 ConditionSet 复验（决策 4；validation_
#      conditions 选择器 0=「all」/1=all_outer——后者静态预检乘 W_s，W5）。
#   R4 护栏键 solution.joint.* 全量经 assumption() 取值（W8 零魔法数）；
#      预算双轴 rows+full_plant_evals（N2）分别计费，静态 422+截断标注。
#   R5~R6 末段硬门/真键映射/降权标记=final_eval 件规格（W9/W10/W12/N6）。
#   R7 诊断分层：首空级=stage_conflicts（既有 diagnose 委托+前缀注记）；
#      末空级=relax_grid_specs 一次放宽（range 域面，离散档诚实原样）。
#      【批5 事由分叉（AUD-W7/P2）】末空级诊断三支：timeout 截断
#      （timeout_truncated=True——截断态不启动重试）/预算拒（放宽后
#      行估计超限 skip）/无域可放（名义放宽=离散档原样不重试）；放宽
#      重试回路迁 relax.py 伴生件（真实/名义放宽区分与 RetryOutcome
#      事由面见该件规格头）。
#   R8 回路冻结=基线快照已知近似（决策 6/B1）；B12 后升级不动点迭代。
#
# 【批6g 拆分注记】（2026-09-26，wave6 §批6g——批5 拆件后 481 行仍距
#   腾位目标 ≤450 差 31 行）：编排器主题段（_ordered_targets+
#   _JointSearch+_Prefix 族+_SEARCH_SEMANTICS+其运行期构造消费的三
#   公开名 JointOutcome/JointEnumerationTooLarge/estimate_rows）整体
#   迁 search.py 兄弟件（relax/final_eval 先例第三例；B3 R1 整域逐字
#   搬运——行为等价双跑 diff=0 烤验）；本文件经 search 再导出三名，
#   公开 import 路径/__init__ 五名/消费面零改动。选项 schema 与正门
#   编排+末空级诊断载荷留守（run_joint_enumerate 主循环语义注记
#   见各段注释）。
#
# 【层序注记】solution→waterprint.graph 唯一 import 现场=包根
#   joint_enumeration/__init__.py（execute_graph 直调——W6；§1c 登记
#   independence=true）。app_assembly=类注入防环（options.assemble，
#   app 正门注入点——assumptions_design_map 类注入先例）。
#
# 【测试要求】两单元小网格全链/静态预检 422/k=1 边界/超预算拒/截断语义。
# 【参照】.workflow/b4-3/design-final.md 全文；ADR-025
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, final

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.quality import EffluentStandard
from waterprint.contracts.run_env import RunEnv
from waterprint.solution.constraints import Constraint
from waterprint.solution.joint_enumeration import relax as joint_relax

# 批6g 拆件（wave6 §批6g）：编排器主题段+其构造消费的三公开名迁 search.py
# 兄弟件（relax 先例）；本文件再导出保公开 import 路径与 __init__ 五名不变。
from waterprint.solution.joint_enumeration.search import (
    JointEnumerationTooLarge,
    JointOutcome,
    _JointSearch,
    estimate_rows,
)
from waterprint.solution.joint_enumeration.stage import (
    AssembleFn,
    InvalidJointEnumerationError,
)


@dataclass(frozen=True)
@final
class JointEnumerationOptions:
    """联合枚举选项（不可变）：网格/单元级约束覆盖+出水标准族。"""

    grids: Mapping[str, tuple[Mapping[str, Any], ...]] = field(default_factory=dict)
    constraints: Mapping[str, tuple[Constraint, ...]] = field(default_factory=dict)
    standards: tuple[EffluentStandard, ...] = ()
    assemble: AssembleFn | None = None  # 类注入防环（app 正门装配面注入）
    capex_data_dir: Path | None = None  # 批2b：capex 装配数据目录（worker 注入）

    def __post_init__(self) -> None:
        """映射归一（裸 str 拒——I-2 同款防线）。"""
        if isinstance(self.grids, str) or isinstance(self.constraints, str):
            raise TypeError(
                "JointEnumerationOptions.grids/constraints 须为映射，不接受裸 str"
                f"（逐字符拆解为伪键）：得到 {self.grids!r}/{self.constraints!r}"
            )
        object.__setattr__(self, "grids", dict(self.grids))
        object.__setattr__(self, "constraints", dict(self.constraints))


def run_joint_enumerate(
    project: ProjectFile, unit_ids: Sequence[str], conditions: ConditionSet,
    env: RunEnv, options: JointEnumerationOptions | None = None,
) -> JointOutcome:
    """联合枚举正门（ADR-025）：静态预检→基线→分层 beam→末段复验→排序。"""
    chosen = options if options is not None else JointEnumerationOptions()
    if not conditions.baseline and not conditions.sensitivity:
        raise InvalidJointEnumerationError(
            "conditions 为空集（正门 build_condition_set 恒非空——M-5 同口径）"
        )
    search = _JointSearch(project, unit_ids, conditions, env, chosen)
    grids = search.grids()
    search.static_precheck(grids)
    source, baseline = search.baseline()
    staged = search.staged(source, grids)
    if isinstance(staged, Mapping):  # 首空级：分层诊断交付（空组合=合法终态）
        return search.outcome((), {"kind": "stage_empty", "stage": staged})
    combos = search.final_eval([params for params, _ in staged], baseline)
    if not any(combo.feasible for combo in combos):
        skip_reason: str | None = None
        if not search.truncated:  # 截断态不启动放宽重试（复验未完成非域拒结论）
            widened = joint_relax.relaxed_grids(chosen.grids, search.guards.relax_factor)
            if widened:  # 真实域扩才重试（名义放宽=离散档原样诚实跳过）
                retry = joint_relax.retry_joint(
                    search, replace(chosen, grids={**chosen.grids, **widened}), baseline
                )
                if retry.outcome is not None:
                    return retry.outcome
                skip_reason = retry.skip_reason
        return search.outcome(
            combos, _final_infeasible_diagnosis(search.truncated, skip_reason)
        )
    return search.outcome(combos, None)


def _final_infeasible_diagnosis(truncated: bool, skip_reason: str | None) -> dict[str, Any]:
    """末空级诊断载荷（批5 事由分叉：timeout 维度/预算拒/无域可放——AUD-W7）。"""
    payload: dict[str, Any] = {
        "kind": "final_infeasible", "relaxed": False, "timeout_truncated": truncated,
    }
    if truncated:
        payload["note"] = (
            "末段因 timeout 截断——复验未完成即返（非域拒结论；截断态不启动放宽重试）"
        )
    elif skip_reason == "budget":
        payload["note"] = (
            "末段组合全不可行且存在可放宽 range 域，但放宽后行估计超 "
            "max_total_rows——静态预检口径统一执法不重试"
        )
    else:
        payload["note"] = (
            "末段组合全不可行且无可放宽 range 域（离散档网格无连续域——"
            "名义放宽不重试）"
        )
    return payload


__all__ = [
    "JointEnumerationOptions",
    "JointEnumerationTooLarge",
    "JointOutcome",
    "estimate_rows",
    "run_joint_enumerate",
]
