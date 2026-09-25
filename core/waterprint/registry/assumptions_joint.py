"""B4-3 联合枚举护栏假设伴生件：solution.joint.* 键族全量声明（W7/W8/N2）。

输入:  类注入（Assumption/TuningImpact——assumptions 主件装配点传入）
输出:  joint_entries(…) → 联合枚举假设条目元组（主件 DEFAULT_ASSUMPTIONS 解包）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B4-3 终裁定稿 .workflow/b4-3/design-final.md §二/终裁修正
#   表 W7/W8/N2/N3——2026-09-20；assumptions_design_map.py 伴生件先例
#   第二例 registry 同构）
#
# 【定位】assumptions.py 主件解包追加同制（伴生件零 waterprint import——
#   Assumption/TuningImpact 经 joint_entries 参数注入类注入防环；TypeVar
#   类型面，mypy 零 Any 逃逸）。数值真源唯一在此（GR-15）；主件装载序
#   （YAML ordered_files 四件+design_map 伴生）零扰动，本件尾挂其后。
#
# 【键族与 float 单值约束】定稿键族九名中 stage_proxy_weights/
#   objective_weights 为配比概念——Assumption 契约仅收 float 默认
#   （assumptions.py R1 六守卫），故分解落地：objective_weights 四分
#   （opex/energy/carbon/capex 各一键——批2b capex 扩键）、
#   stage_proxy_weights 单键承载裕度份额（能耗代理份额=1−值，两分量
#   配比单键化）——九概念族 → 12 float 键（实现裁量：B4-3 commit 注记
#   +批2b）。
#
# 【键语义（消费面 solution/joint_enumeration/*+server 门面）】
#   max_units：请求单元数上限（名义护栏 N 默认 6；硬上限 8 不另立常数——
#   静态预检 rows 公式天然守域，终裁 N3/N5 口径）。
#   beam_width：beam 宽 k（默认 5；上限 20 同由 rows 公式守域不另立常数）。
#   max_total_rows：分级枚举行预算（静态预检 422 主闸，W7）。
#   timeout_s：看门狗秒（运行时兜底——超时返回已完成部分+truncated）。
#   max_full_plant_evals：末段全厂真值复验次数预算（N2 双轴第二轴）。
#   relax_factor：末空级网格放宽倍数（diagnose 面一次放宽，W8）。
#   stage_proxy_weights：阶段代理分裕度份额（0~1；能耗份额=1−值）。
#   objective_weight_{opex,energy,carbon,capex}：排序目标四键权重（批2b
#       2026-09-25 audit-norms 裁决②重排：成本面 opex+capex 合计 0.5 守恒
#       内部对半 .25/.25、energy .30/carbon .20 维持——初值专家追认制；
#       capex 真键=cost_capex_yuan 概算 grand_total，AUD-W11 纯几何参数
#       零区分度修复）。
#   validation_conditions：0=「all」（基线工况搜索+末段全 ConditionSet
#       复验——默认）；1=all_outer（搜索亦全工况——静态预检乘 W_s，W5）。
#
# 【测试要求】主件 DEFAULT_ASSUMPTIONS 含全 12 键；覆盖值经 assumption()
#   正门生效；装载序零扰动（[0] safety.superheight 锚不动）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from typing import Final

_SOURCE: Final[str] = (
    "B4-3 联合枚举终裁（2026-09-20 .workflow/b4-3/design-final.md §二——"
    "默认域锚 N≤6/g≤500/k≤3 ≈1.8e5 行≈29s）；待专家追认（R-B43-4 呈批）"
)
_SOURCE_B2B: Final[str] = (
    "B4-3 键族批2b 重排（backend-calc-complete——2026-09-25 .workflow/"
    "audit-norms-20260925/report.md §三裁决②用户裁决立项；初值专家追认制）"
)
_NOTE_HEAD: Final[str] = (
    "联合枚举（solution.joint_enumeration+server 门面）护栏键——数值真源"
    "唯一在此（GR-15）；"
)
_TUNING_GUARD: Final[str] = (
    "增大→搜索面放宽但耗时上升（静态预检 rows 公式统一执法），减小→护栏更严"
)


def joint_entries[T](
    assumption: Callable[..., T], tuning_impact: Callable[..., object]
) -> tuple[T, ...]:
    """联合枚举假设条目（类注入防环——主件装配点传 Assumption/TuningImpact）。"""
    return (
        assumption(
            "solution.joint.max_units",
            6.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "请求单元数上限（名义 N=6；硬上限 8 由 rows 公式天然守域——终裁 N3）",
            tuning_impact(_TUNING_GUARD, ()),
        ),
        assumption(
            "solution.joint.beam_width",
            5.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "beam 宽 k（上限 20 同由 rows 公式守域，不另立常数）",
            tuning_impact(_TUNING_GUARD, ()),
        ),
        assumption(
            "solution.joint.max_total_rows",
            500000.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "分级枚举行预算（静态预检主闸：rows=g·(k^N−1)/(k−1)·W_s≤值否则 422，W7）",
            tuning_impact(_TUNING_GUARD, ()),
        ),
        assumption(
            "solution.joint.timeout_s",
            120.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "看门狗秒（运行兜底：超时返回已完成部分+truncated=true，W1 截断语义）",
            tuning_impact("增大→容忍更长搜索，减小→更早诚实截断", ()),
        ),
        assumption(
            "solution.joint.max_full_plant_evals",
            25.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "末段全厂复验次数预算（N2 双轴第二轴；25=beam_width5×5 冗余上界）",
            tuning_impact(_TUNING_GUARD, ()),
        ),
        assumption(
            "solution.joint.relax_factor",
            2.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "末空级网格放宽倍数（一次放宽：range 域两侧各扩 (值−1)/2 比例，W8）",
            tuning_impact("增大→放宽域更宽（可行面大但行数涨），减小→放宽更保守", ()),
        ),
        assumption(
            "solution.joint.stage_proxy_weights",
            0.5,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD
            + "阶段代理分裕度份额（0~1；能耗代理份额=1−值——两分量配比 float 单键承载）",
            tuning_impact("增大→代理分偏可行裕度，减小→偏单元能耗估计", ()),
        ),
        assumption(
            "solution.joint.objective_weight_opex",
            0.25,
            "DIMENSIONLESS",
            _SOURCE_B2B,
            _NOTE_HEAD + "排序目标 opex 权重（cost_opex_yuan_a，design 工况——批2b 重排"
            "成本面与 capex 对半 .25/.25）",
            tuning_impact("增大→排序偏运行成本优先", ()),
        ),
        assumption(
            "solution.joint.objective_weight_energy",
            0.3,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "排序目标 energy 权重（power_total_kwh_d，design 工况）",
            tuning_impact("增大→排序偏能耗优先", ()),
        ),
        assumption(
            "solution.joint.objective_weight_carbon",
            0.2,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD + "排序目标 carbon 权重（carbon_intensity_kgco2e_m3，design 工况）",
            tuning_impact("增大→排序偏碳强度优先", ()),
        ),
        assumption(
            "solution.joint.objective_weight_capex",
            0.25,
            "DIMENSIONLESS",
            _SOURCE_B2B,
            _NOTE_HEAD + "排序目标 capex 权重（cost_capex_yuan 概算 grand_total，design"
            "工况——批2b 第四真键；kit 缺席时 N6 重分配承接）",
            tuning_impact("增大→排序偏建设投资优先", ()),
        ),
        assumption(
            "solution.joint.validation_conditions",
            0.0,
            "DIMENSIONLESS",
            _SOURCE,
            _NOTE_HEAD
            + "复验口径选择：0=「all」基线搜索+末段全 ConditionSet 复验；1=all_outer"
            "（搜索亦全工况——静态预检乘 W_s，W5 备选）",
            tuning_impact("1→all_outer 全工况搜索（行数×工况数，静态预检统一执法）", ()),
        ),
    )
