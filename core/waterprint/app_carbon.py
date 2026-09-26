"""碳排放（三范围）全厂投影：summary 能耗/药耗/进水负荷平键 × factor.carbon.* → 碳排平键。

输入:  base（app.run_full_calc 的 _with_energy+_with_influent 合并面——
       power_*/dose_*/influent_*/effluent_tn_load_* 平键+批6b 碳上游供数
       fuel_gas_nm3_d/vs_degraded_kg_d/biogas_m3_d 平键）
       + RunEnv.coefficients（CoefficientsView 协议只读面——factor.carbon.* 键）
输出:  carbon_summary_of（app.run_full_calc 经 _with_carbon 合并注入 summary——
       开放映射槽位，result_schema 零改）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（B4-2c 终裁定案 .workflow/b4-2c/master-ruling.md D4/D5/D6/D8；
#   计算逻辑经用户审查 R-B42c-1~4 四项全批 2026-09-20；批6b 2026-09-26
#   增碳范围一 C-F10~F12——批3.5 追认已签〔b35-research §五〕实装面+
#   AUD-W4 能耗上游联动）；镜像测试
#   tests/app/test_app_carbon.py；app_opex.py 拆分先例同构第八例
#   ——根模块聚合投影件，不进 import-linter layers 契约（app_trust
#   同款 unconstrained）。
#
# 【公开接口】
#   carbon_summary_of(base, coefficients) -> dict[工况→dict[平键→float]]
#       纯投影：逐工况按 C-F1~F12 合成碳排平键（sparse——批6b 增
#       C-F10 燃料 CO₂/C-F11 燃烧次要/C-F12 消化净 CH₄ 三式）。
#   _with_carbon(base, extra) -> dict[...]
#       summary 合并注入（_with_opex 同语义——同工况字典 update、
#       base 键族优先，两族键集无交集由命名域保证）。
#
# 【公式（C-F1~F12，逐工况 sparse——键有则录无则略；单位换算与因子
#   全经 factor.carbon.* 键——魔法数字门禁：数值字面量零）】
#   C-F1 carbon_indirect_electricity_kgco2e_d = power_total_kwh_d
#       × factor.carbon.grid_co2（范围二：外购电力间接排放）
#   C-F2 carbon_indirect_chemicals_kgco2e_d = Σ在场 dose_{pac,pam,seed}_kg_d
#       × factor.carbon.{pac,pam,magnetic_seed}（范围三：药剂生产上游；
#       磁种键本批不立[无权威源 R-B42c-3⑤]→该分项恒跳过）
#   C-F3 carbon_direct_n2o_plant_kgco2e_d = influent_tn_load_kg_d
#       × factor.carbon.n2o_ef_plant × factor.carbon.molar_n2o_n
#       × factor.carbon.gwp_n2o（范围一：厂内 N2O——IPCC 2019 因子系）
#   C-F4 carbon_direct_n2o_effluent_kgco2e_d = effluent_tn_load_kg_d
#       × factor.carbon.n2o_ef_effluent × molar_n2o_n × gwp_n2o
#       （范围一：出水下游 N2O）
#   C-F5 carbon_direct_ch4_kgco2e_d = influent_bod5_load_kg_d
#       × factor.carbon.ch4_b0 × factor.carbon.ch4_mcf × factor.carbon.gwp_ch4
#       （范围一：好氧厂 CH4——2019 MCF 0.03）
#   C-F10 carbon_direct_fuel_co2_kgco2e_d = fuel_gas_nm3_d
#       × factor.carbon.ganhua_ef_co2（范围一：污泥干化天然气燃烧 CO₂
#       ——批3.5 追认 21.622 tCO₂/万Nm³=2.1622 kg/Nm³；批6b 增）
#   C-F11 carbon_direct_fuel_minor_kgco2e_d = fuel_gas_nm3_d
#       × (factor.carbon.ganhua_ef_ch4 × gwp_ch4 + factor.carbon.ganhua_ef_n2o
#       × gwp_n2o)（范围一：燃烧次要面 CH₄/N₂O——IPCC 2006 1 kg/TJ；
#       全因子键在场才立——批6b 增）
#   C-F12 carbon_direct_ch4_digest_kgco2e_d = (vs_degraded_kg_d
#       × factor.carbon.ch4_b0 × factor.carbon.dig_mcf − biogas_m3_d
#       × factor.carbon.dig_ch4_frac × factor.carbon.dig_gas_recovery
#       × factor.carbon.ch4_density_std) × factor.carbon.gwp_ch4
#       （范围一：污泥消化线净 CH₄——2019RF Table 6.3 消化档 0.8 案 A
#       独立核算〔gross−回收 R〕，废水线 C-F5 毯式 0.03 维持不动；
#       双源键（vs/biogas）+全因子键在场才立——批6b 增）
#   C-F6 carbon_direct_kgco2e_d = Σ在场{F3,F4,F5,F10,F11,F12}（≥1 分项才立）
#   C-F7 carbon_indirect_kgco2e_d = Σ在场{F1,F2}（≥1 分项才立）
#   C-F8 carbon_total_kgco2e_d = F6+F7——**双在场律（终裁 D4）**：
#       仅 direct 与 indirect 双在场时落键（防部分口径误读——单范围
#       缺席工况不立总量，mine 线无 BOD5/CH4 但有 N2O 仍属 direct 在场）
#   C-F9 carbon_intensity_kgco2e_m3 = F8 ÷ influent_flow_m3_d（吨水碳强度
#       ——total 与 Q 双在场才落）
#
# 【行为口径】
#   R1 sparse：数据键或因子键缺席→该式跳过；全缺席→无 carbon_* 键
#      （factor.carbon.* 未装载的系数包合法——sparse 从众，opex R1 同款）。
#   R2 纯投影：不重算不造数——负荷/能耗×因子×换算的乘加；serialize
#      sort_keys 保证确定性。
#   R3 口径：因子版本系=2019 Refinement+AR6（R-B42c-2 用户裁——真值锚
#      0.587 kgCO2e/m3 与全国城镇污水厂均值 0.589 偏差 0.3% 实证）；
#      电网因子 CO2 口径按 CO2e 计（知情点——量级影响可忽略）。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量无（仅空迭代求和）。
#
# 【测试要求】sparse 三态容错/分项合成/合计律/双在场律（total）/吨水
#   强度/纯函数双跑/量级带断言（T1~T7——B 案向量含供数联动）。
#
# 【参照】.workflow/b4-2c/master-ruling.md；app.py _with_opex；
#   app_opex.py（先例）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from waterprint.contracts.run_env import CoefficientsView

_CARBON_PREFIX: Final[str] = "factor.carbon."
_KEY_GRID: Final[str] = "factor.carbon.grid_co2"
_KEY_N2O_PLANT: Final[str] = "factor.carbon.n2o_ef_plant"
_KEY_N2O_EFFLUENT: Final[str] = "factor.carbon.n2o_ef_effluent"
_KEY_CH4_B0: Final[str] = "factor.carbon.ch4_b0"
_KEY_CH4_MCF: Final[str] = "factor.carbon.ch4_mcf"
_KEY_GWP_CH4: Final[str] = "factor.carbon.gwp_ch4"
_KEY_GWP_N2O: Final[str] = "factor.carbon.gwp_n2o"
_KEY_MOLAR: Final[str] = "factor.carbon.molar_n2o_n"
_SOURCE_POWER: Final[str] = "power_total_kwh_d"
_SOURCE_FLOW: Final[str] = "influent_flow_m3_d"
# 批6b 碳范围一：燃料/消化供数源键与因子键（C-F10~F12）
_KEY_FUEL_CO2: Final[str] = "factor.carbon.ganhua_ef_co2"
_KEY_FUEL_CH4: Final[str] = "factor.carbon.ganhua_ef_ch4"
_KEY_FUEL_N2O: Final[str] = "factor.carbon.ganhua_ef_n2o"
_KEY_DIG_MCF: Final[str] = "factor.carbon.dig_mcf"
_KEY_DIG_FRAC: Final[str] = "factor.carbon.dig_ch4_frac"
_KEY_DIG_RECOVER: Final[str] = "factor.carbon.dig_gas_recovery"
_KEY_CH4_DENSITY: Final[str] = "factor.carbon.ch4_density_std"
_SOURCE_FUEL: Final[str] = "fuel_gas_nm3_d"
_SOURCE_VS_DEG: Final[str] = "vs_degraded_kg_d"
_SOURCE_BIOGAS: Final[str] = "biogas_m3_d"
# summary 药耗平键 → factor.carbon.* 生产因子键（磁种键缺席恒跳过）
_DOSE_EFS: Final[dict[str, str]] = {
    "dose_pac_kg_d": "factor.carbon.pac",
    "dose_pam_kg_d": "factor.carbon.pam",
    "dose_seed_kg_d": "factor.carbon.magnetic_seed",
}
_ELECTRICITY: Final[str] = "carbon_indirect_electricity_kgco2e_d"
_CHEMICALS: Final[str] = "carbon_indirect_chemicals_kgco2e_d"
_N2O_PLANT: Final[str] = "carbon_direct_n2o_plant_kgco2e_d"
_N2O_EFFLUENT: Final[str] = "carbon_direct_n2o_effluent_kgco2e_d"
_CH4: Final[str] = "carbon_direct_ch4_kgco2e_d"
# 批6b 范围一新平键（C-F10~F12 输出面）
_FUEL_CO2: Final[str] = "carbon_direct_fuel_co2_kgco2e_d"
_FUEL_MINOR: Final[str] = "carbon_direct_fuel_minor_kgco2e_d"
_CH4_DIGEST: Final[str] = "carbon_direct_ch4_digest_kgco2e_d"
_DIRECT: Final[str] = "carbon_direct_kgco2e_d"
_INDIRECT: Final[str] = "carbon_indirect_kgco2e_d"
_TOTAL: Final[str] = "carbon_total_kgco2e_d"
_INTENSITY: Final[str] = "carbon_intensity_kgco2e_m3"
# 负荷源键 → (输出键, N2O 因子键)（C-F3/C-F4 共用换算+GWP 键）
_N2O_TERMS: Final[dict[str, tuple[str, str]]] = {
    "influent_tn_load_kg_d": (_N2O_PLANT, _KEY_N2O_PLANT),
    "effluent_tn_load_kg_d": (_N2O_EFFLUENT, _KEY_N2O_EFFLUENT),
}
_SOURCE_BOD_LOAD: Final[str] = "influent_bod5_load_kg_d"


def _scope1_fuel_and_digest(
    fields: Mapping[str, float], keys: set[str], coefficients: CoefficientsView
) -> dict[str, float]:
    """C-F10~F12 范围一补全（批6b）：燃料 CO₂/燃烧次要/消化净 CH₄ 三式。

    sparse 双律：因子键缺席→分式跳；消化式双源键（vs/biogas）缺一→整式跳。
    """
    terms: dict[str, float] = {}
    fuel = fields.get(_SOURCE_FUEL)
    if fuel is not None and _KEY_FUEL_CO2 in keys:
        terms[_FUEL_CO2] = fuel * coefficients.get(_KEY_FUEL_CO2).value
    if (
        fuel is not None
        and _KEY_FUEL_CH4 in keys
        and _KEY_FUEL_N2O in keys
        and _KEY_GWP_CH4 in keys
        and _KEY_GWP_N2O in keys
    ):
        terms[_FUEL_MINOR] = fuel * (
            coefficients.get(_KEY_FUEL_CH4).value * coefficients.get(_KEY_GWP_CH4).value
            + coefficients.get(_KEY_FUEL_N2O).value * coefficients.get(_KEY_GWP_N2O).value
        )
    vs_deg = fields.get(_SOURCE_VS_DEG)
    biogas = fields.get(_SOURCE_BIOGAS)
    if (
        vs_deg is not None
        and biogas is not None
        and _KEY_CH4_B0 in keys
        and _KEY_DIG_MCF in keys
        and _KEY_DIG_FRAC in keys
        and _KEY_DIG_RECOVER in keys
        and _KEY_CH4_DENSITY in keys
        and _KEY_GWP_CH4 in keys
    ):
        recovered = (
            biogas
            * coefficients.get(_KEY_DIG_FRAC).value
            * coefficients.get(_KEY_DIG_RECOVER).value
            * coefficients.get(_KEY_CH4_DENSITY).value
        )
        terms[_CH4_DIGEST] = (
            vs_deg * coefficients.get(_KEY_CH4_B0).value * coefficients.get(_KEY_DIG_MCF).value
            - recovered
        ) * coefficients.get(_KEY_GWP_CH4).value
    return terms


def carbon_summary_of(
    base: Mapping[str, Mapping[str, float]], coefficients: CoefficientsView
) -> dict[str, dict[str, float]]:
    """C-F1~F12 纯投影：逐工况负荷/能耗/药耗平键 × 因子 → 碳排平键（sparse）。"""
    keys = set(coefficients.keys(_CARBON_PREFIX))
    summary: dict[str, dict[str, float]] = {}
    for condition_key, fields in base.items():
        out: dict[str, float] = {}
        # C-F1 范围二（电）
        power_total = fields.get(_SOURCE_POWER)
        if power_total is not None and _KEY_GRID in keys:
            out[_ELECTRICITY] = power_total * coefficients.get(_KEY_GRID).value
        # C-F2 范围三（药——磁种键缺席恒跳过）
        chemical_parts = [
            fields[dose] * coefficients.get(ef).value
            for dose, ef in _DOSE_EFS.items()
            if dose in fields and ef in keys
        ]
        if chemical_parts:
            out[_CHEMICALS] = sum(chemical_parts)
        # C-F3/C-F4 范围一 N2O（厂内+出水——共用 molar+GWP 键）
        for source, (target, ef) in _N2O_TERMS.items():
            load = fields.get(source)
            if load is not None and ef in keys and _KEY_MOLAR in keys and _KEY_GWP_N2O in keys:
                out[target] = (
                    load
                    * coefficients.get(ef).value
                    * coefficients.get(_KEY_MOLAR).value
                    * coefficients.get(_KEY_GWP_N2O).value
                )
        # C-F5 范围一 CH4（好氧厂——废水线毯式，消化线见 C-F12）
        bod_load = fields.get(_SOURCE_BOD_LOAD)
        if (
            bod_load is not None
            and _KEY_CH4_B0 in keys
            and _KEY_CH4_MCF in keys
            and _KEY_GWP_CH4 in keys
        ):
            out[_CH4] = (
                bod_load
                * coefficients.get(_KEY_CH4_B0).value
                * coefficients.get(_KEY_CH4_MCF).value
                * coefficients.get(_KEY_GWP_CH4).value
            )
        # C-F10~F12 范围一补全（批6b——燃料/消化三式独立辅助件）
        out.update(_scope1_fuel_and_digest(fields, keys, coefficients))
        # C-F6/C-F7 分项合计（≥1 分项才立——批6b 扩 F10/F11/F12 入 direct）
        direct_parts = [
            out[k]
            for k in (_N2O_PLANT, _N2O_EFFLUENT, _CH4, _FUEL_CO2, _FUEL_MINOR, _CH4_DIGEST)
            if k in out
        ]
        if direct_parts:
            out[_DIRECT] = sum(direct_parts)
        indirect_parts = [out[k] for k in (_ELECTRICITY, _CHEMICALS) if k in out]
        if indirect_parts:
            out[_INDIRECT] = sum(indirect_parts)
        # C-F8 总量——双在场律（终裁 D4：direct+indirect 双在场才落键）
        if _DIRECT in out and _INDIRECT in out:
            out[_TOTAL] = out[_DIRECT] + out[_INDIRECT]
            # C-F9 吨水碳强度（total 与 Q 双在场且 Q>0——零流量退化面不落）
            flow = fields.get(_SOURCE_FLOW)
            if flow is not None and flow > 0.0:
                out[_INTENSITY] = out[_TOTAL] / flow
        summary[condition_key] = out
    return summary


def _with_carbon(
    base: dict[str, dict[str, float]], extra: dict[str, dict[str, float]]
) -> dict[str, dict[str, float]]:
    """summary 合并注入：既有平键族 + carbon_* 碳排键（B4-2c 终裁——同工况
    字典 update；base 键族优先，两族键集无交集由命名域保证）。"""
    for condition_key, fields in extra.items():
        if condition_key in base:
            base[condition_key].update(fields)
    return base
