"""CASS 能耗公式族声明件：CA-F29~F33（B4-2a 碳核算前置一；ADR-024）。

输入:  registry FormulaSpec 声明依赖（纯声明——manifest 并组注册）
输出:  FORMULAS_ENERGY（供气量→风机轴功率→日耗电+选择区搅拌五式）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（ADR-024 D1；预算墙拆件——manifest.py 499 行+5 规格超 500 上限，
# 能耗公式族立独立声明件：条目仍在单元包内（B2-5 D1-B「条目留 manifest
# 原位」的单元包原位读法——manifest.py 并组注册保持单注册口），能耗
# 计算段住 energy.py（compute 400 行墙同因拆件）。
# 【公式族】CA-F29~F33（计算逻辑经用户审查 R-B42a-1；系数档=
#   factor.cass.blower.*/factor.cass.stir.* 六带，data 1.3.0）：
#   与 AAO AO-F21~F25 同族平移，两处 CASS 特化——①e_aeration 含
#   duty_ratio（CASS 周期曝气间歇运行 4h 周期 2h 曝气典型档，异于
#   AAO 连续流×24 满时）；②p_stir 取选择区（预反应区）容积
#   （CA-F28 注记口径——选择区仅搅拌/微量曝气）。
# 【挂账】同 AAO：AOR→SOR 五系数分列修正；电机/装机功率口径。
# 【量纲】q_air=FLOW；功率/日电耗 DIMENSIONLESS（kW 语义 meaning
#   承载——TJ-F9/KN-F6 先例）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec

_D = DimKey.DIMENSIONLESS
_F = DimKey.FLOW
_VOL = DimKey.VOLUME
_M = DimKey.MASS

_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》供气量法与风机轴功率"
    "（B4-2a 能耗面起草 2026-09-19，计算逻辑经用户审查 R-B42a-1——"
    "待领域专家追认）"
)

FORMULAS_ENERGY: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "CA-F29",
        "q_air = o2_total * f_sor / (o2_per_air * ea * 86400)",
        {
            "o2_total": (_M, "总需氧量 kg/d（CA-F22）"),
            "f_sor": (_D, "AOR→SOR 折算系数（factor.cass.blower.sor_factor）"),
            "o2_per_air": (_D, "标态空气含氧质量浓度 kg/m3（factor.cass.blower.o2_per_air）"),
            "ea": (_D, "微孔曝气氧利用率（factor.cass.blower.oxygen_transfer_eff）"),
        },
        _F,
        f"{_HB}；Gs=O2/(0.28·EA) 手册口径（86400=d→s 换算；AOR→SOR "
        "五系数分列修正挂账 B4-2b——综合折算系数 f_sor 承载）",
    ),
    FormulaSpec(
        "CA-F30",
        "p_blower = q_air * p_pressure / eta_blower",
        {
            "q_air": (_F, "供气量 m3/s（CA-F29）"),
            "p_pressure": (_D, "风机出口压力 kPa（factor.cass.blower.pressure_kpa）"),
            "eta_blower": (_D, "罗茨风机综合效率（factor.cass.blower.efficiency）"),
        },
        _D,
        f"{_HB}；P=Q·Δp/η（m3/s×kPa=kW 直读）；Δp=有效水深+管损"
        "裕量档",
    ),
    FormulaSpec(
        "CA-F31",
        "e_aeration = p_blower * 24 * duty_ratio",
        {
            "p_blower": (_D, "风机轴功率 kW（CA-F30）"),
            "duty_ratio": (_D, "周期曝气占空比（factor.cass.blower.duty_ratio）"),
        },
        _D,
        f"{_HB}；CASS 间歇曝气口径：e=P·24·duty_ratio（4 h 周期 2 h "
        "曝气典型档——连续流 AAO 为 ×24 满时异档）",
    ),
    FormulaSpec(
        "CA-F32",
        "p_stir = v_selector * w_stir / 1000",
        {
            "v_selector": (_VOL, "选择区（预反应区）容积 m3（CA-F4）"),
            "w_stir": (_D, "潜水搅拌功率密度 W/m3（factor.cass.stir.power_density）"),
        },
        _D,
        f"{_HB}；选择区潜水搅拌（CA-F28 注记口径——选择区仅搅拌/微量"
        "曝气不入满布面积；/1000=W→kW）",
    ),
    FormulaSpec(
        "CA-F33",
        "e_stir = p_stir * 24",
        {
            "p_stir": (_D, "搅拌装机功率 kW（CA-F32）"),
        },
        _D,
        f"{_HB}；选择区搅拌连续运行 24 h/d（kW×h=kWh/d）",
    ),
)
