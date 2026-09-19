"""运行成本（opex）全厂投影：summary 能耗药耗平键 × factor.opex.* 单价 → 年成本平键。

输入:  base（app.run_full_calc 的 _with_energy 合并面——power_*/dose_* 平键）
       + RunEnv.coefficients（CoefficientsView 协议只读面——factor.opex.* 五键）
输出:  opex_summary_of（app.run_full_calc 经 _with_opex 合并注入 summary——
       开放映射槽位，result_schema 零改）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（B4-2b 终裁定案 .workflow/briefs/b4-2b-master-ruling-r2.md §三；
#   镜像测试 tests/app/test_app_opex.py；app_energy.py 拆分先例同构
#   第六例——根模块聚合投影件，不进 import-linter layers 契约
#   （app_trust 同款 unconstrained）。
#
# 【公开接口】
#   opex_summary_of(base, coefficients) -> dict[工况→dict[平键→float]]
#       纯投影：逐工况按 F1~F3 合成年运行成本键（sparse）。
#   _with_opex(base, extra) -> dict[...]
#       summary 合并注入（_with_energy 同语义——同工况字典 update、
#       base 键族优先，两族键集无交集由命名域保证）。
#
# 【公式（F1~F3，逐工况 sparse——键有则录无则略）】
#   F1 cost_electricity_yuan_a = power_total_kwh_d
#       × factor.opex.electricity × factor.opex.days_per_year
#   F2 cost_chemicals_yuan_a = Σ在场 dose_{pac,pam,seed}_kg_d
#       × factor.opex.{pac,pam,magnetic_seed} × factor.opex.days_per_year
#       （单价元/kg 口径——÷1000 消除；年化因子 R-B42b-3 口径③：
#       365 天年化适用于可算面全体——呈批报告公式表 F2 列系简写
#       笔误，锚表算式+键名量纲 yuan/a 为准）
#   F3 cost_opex_yuan_a = Σ在场{F1, F2}（无分项不立合计）
#
# 【行为口径】
#   R1 sparse：单价键经 coefficients.keys("factor.opex.") 前缀列举判
#      在场（get 失联键=领域异常禁 None——registry get 语义实录）；
#      单键缺席→该分项跳过；全缺席→无 cost 键（factor.opex.* 未装载
#      的系数包合法——sparse 从众）。
#   R2 纯投影：不重算不造数——单价×日耗的乘加；serialize sort_keys
#      保证确定性。
#   R3 口径：年化 365 天连续运行（factor.opex.days_per_year 承载——与
#      B4-2a ×24h/d 假设同源）；可算面=电费+药剂费（行业口径两大
#      单项），人工/维修/污泥处置/折旧显式挂账不造零值键；吨水指标
#      （元/m³）挂账后移（无规范全厂流量键——终裁 D4 维持）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量无（仅空迭代求和）。
#
# 【测试要求】sparse 键族/分项合成/合计律/纯函数双跑/factor 缺席容错。
#
# 【参照】.workflow/briefs/b4-2b-master-ruling-r2.md；app.py _with_energy；
#   app_energy.py（先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from waterprint.contracts.run_env import CoefficientsView

_OPX_PREFIX: Final[str] = "factor.opex."
_KEY_ELECTRICITY: Final[str] = "factor.opex.electricity"
_KEY_DAYS: Final[str] = "factor.opex.days_per_year"
_SOURCE_POWER: Final[str] = "power_total_kwh_d"
_COST_ELECTRICITY: Final[str] = "cost_electricity_yuan_a"
_COST_CHEMICALS: Final[str] = "cost_chemicals_yuan_a"
_COST_OPEX: Final[str] = "cost_opex_yuan_a"
# summary 药耗平键 → factor.opex.* 单价键（终裁 W3：单价直接以元/kg 计）
_DOSE_PRICES: Final[dict[str, str]] = {
    "dose_pac_kg_d": "factor.opex.pac",
    "dose_pam_kg_d": "factor.opex.pam",
    "dose_seed_kg_d": "factor.opex.magnetic_seed",
}


def opex_summary_of(
    base: Mapping[str, Mapping[str, float]], coefficients: CoefficientsView
) -> dict[str, dict[str, float]]:
    """F1~F3 纯投影：逐工况 summary 能耗药耗平键 × 单价 → 年成本平键（sparse）。"""
    prices = set(coefficients.keys(_OPX_PREFIX))
    has_days = _KEY_DAYS in prices
    summary: dict[str, dict[str, float]] = {}
    for condition_key, fields in base.items():
        costs: dict[str, float] = {}
        power_total = fields.get(_SOURCE_POWER)
        if power_total is not None and _KEY_ELECTRICITY in prices and has_days:
            costs[_COST_ELECTRICITY] = (
                power_total
                * coefficients.get(_KEY_ELECTRICITY).value
                * coefficients.get(_KEY_DAYS).value
            )
        chemical_parts = [
            fields[dose] * coefficients.get(price).value
            * coefficients.get(_KEY_DAYS).value
            for dose, price in _DOSE_PRICES.items()
            if dose in fields and price in prices and has_days
        ]
        if chemical_parts:
            costs[_COST_CHEMICALS] = sum(chemical_parts)
        parts = [costs[k] for k in (_COST_ELECTRICITY, _COST_CHEMICALS) if k in costs]
        if parts:
            costs[_COST_OPEX] = sum(parts)
        summary[condition_key] = costs
    return summary


def _with_opex(
    base: dict[str, dict[str, float]], extra: dict[str, dict[str, float]]
) -> dict[str, dict[str, float]]:
    """summary 合并注入：既有平键族 + cost_* 年成本键（B4-2b 终裁——同工况
    字典 update；base 键族优先，两族键集无交集由命名域保证）。"""
    for condition_key, fields in extra.items():
        if condition_key in base:
            base[condition_key].update(fields)
    return base
