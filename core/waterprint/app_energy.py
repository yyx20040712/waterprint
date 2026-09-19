"""能耗药耗全厂聚合投影：单元级日耗能/药耗 dims 键 → summary 平键（ADR-024）。

输入:  PlantResult.conditions（逐工况单元快照 dims——e_*/m_* 键名约定）
输出:  energy_summary_of（app.run_full_calc 与 _summary_of 六指标族合并注入
       summary——开放映射槽位，result_schema 零改）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（ADR-024 D2/D3；镜像测试 tests/app/test_app_energy.py；
#   app_trust.py 拆分先例同构第五例——根模块聚合投影件，不进
#   import-linter layers 契约（app_trust 同款 unconstrained）。
#
# 【公开接口】
#   energy_summary_of(plant) -> dict[工况→dict[平键→float]]
#       纯投影：逐工况 Σ 全部单元 dims 中的能耗/药耗键。
#
# 【键名约定聚合（D2）】零单元耦合表——单元以标准键名自报消耗：
#   能耗：e_aeration（kWh/d，AAO AO-F23/CASS CA-F31）、e_pump（TS-F16/
#       BZ-F20）、e_stir（AO-F25/CA-F33/TJ-F14/KT-F13/GM-F21/KN-F16）
#       → power_aeration_kwh_d / power_pump_kwh_d / power_stir_kwh_d；
#   药耗：m_pac/m_pam（gaomidu GM-F14/15、ningjiao KN-F11/12）、
#       w_pam（tuoshui TU-F1——PAM 族并入）、m_seed_net（cifenli
#       磁种净耗——循环补充口径；m_seed 毛耗为循环投加量不计消费）
#       → dose_pac_kg_d / dose_pam_kg_d / dose_seed_kg_d；
#   合计：power_total_kwh_d=Σ在场 power_* 分项（有分项才立合计——
#       无耗能单元的工况合计键不立）。
#
# 【行为口径】
#   R1 sparse：键有则录无则略（_summary_of 六指标同口径——泥线工况
#      若无耗能单元则空映射合法，loop 案既有语义延续）。
#   R2 纯投影：不重算不造数——Σ 由 float 加法；serialize sort_keys
#      保证确定性。
#   R3 同名键多单元叠加合法（m_pac 在 gaomidu+ningjiao 并存场景）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 0。
#
# 【测试要求】sparse 键族/同键多单元叠加/power_total 合成律/空工况
#   空映射/纯函数同输入同输出。
#
# 【参照】ADR-024；app.py _summary_of；app_trust.py（先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Final

from waterprint.contracts.result_schema import PlantResult

# 单元级日耗能 dims 键 → summary 平键（运营消耗计算面契约，ADR-024 D2）
_POWER_FIELDS: Final[dict[str, str]] = {
    "e_aeration": "power_aeration_kwh_d",
    "e_pump": "power_pump_kwh_d",
    "e_stir": "power_stir_kwh_d",
}
# 单元级日药耗 dims 键 → summary 平键（w_pam 并入 PAM 族；m_seed 毛耗
# 不聚合——磁种循环投加非净消费，cifenli m_seed_net 承载补充口径）
_DOSE_FIELDS: Final[dict[str, str]] = {
    "m_pac": "dose_pac_kg_d",
    "m_pam": "dose_pam_kg_d",
    "w_pam": "dose_pam_kg_d",
    "m_seed_net": "dose_seed_kg_d",
}
_POWER_TOTAL: Final[str] = "power_total_kwh_d"


def energy_summary_of(plant: PlantResult) -> dict[str, dict[str, float]]:
    """D3 纯投影：逐工况 Σ 单元 dims 能耗/药耗键（有则录无则略——sparse）。"""
    summary: dict[str, dict[str, float]] = {}
    for condition_key, snapshot in plant.conditions.items():
        totals: dict[str, float] = {}
        for unit in snapshot.values():
            for source, target in (*_POWER_FIELDS.items(), *_DOSE_FIELDS.items()):
                value = unit.dims.get(source)
                if value is not None:
                    totals[target] = totals.get(target, 0.0) + value
        power_keys = {v for v in _POWER_FIELDS.values() if v in totals}
        if power_keys:
            totals[_POWER_TOTAL] = sum(totals[k] for k in power_keys)
        summary[condition_key] = totals
    return summary
