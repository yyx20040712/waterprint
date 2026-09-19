"""AAO 能耗公式族声明件：AO-F21~F25（B4-2a 碳核算前置一；ADR-024）。

输入:  registry FormulaSpec 声明依赖（纯声明——manifest 并组注册）
输出:  FORMULAS_ENERGY（供气量→风机轴功率→日耗电+缺氧/厌氧搅拌五式）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（ADR-024 D1；预算墙拆件——manifest.py 479 行+5 规格超 500 上限，
# 能耗公式族立独立声明件：条目仍在单元包内（B2-5 D1-B「条目留 manifest
# 原位」的单元包原位读法——manifest.py 并组注册保持单注册口），能耗
# 计算段住 energy.py（compute 400 行墙同因拆件）。
# 【公式族】AO-F21~F25（计算逻辑经用户审查 R-B42a-1；系数档=
#   factor.aao.blower.*/factor.aao.stir.* 五带+密度，data 1.3.0）：
#   q_air=O2·f_sor/(0.28·EA·86400)（供气量法——AO-F20 注记的供气量
#   面首落，曝气头校核仍挂账）；p_blower=Q·Δp/η（kPa×m3/s=kW 直读）；
#   e_aeration=P·24（连续曝气满时）；p_stir=(V缺+V厌)·w/1000；
#   e_stir=P·24（防沉积搅拌连续）。
# 【挂账】AOR→SOR 五系数分列修正（本批综合折算系数承载）；电机/
#   装机功率口径；紫外/污泥脱水设备电耗——归 B4-2b 运行成本面。
# 【量纲】q_air=FLOW（V 型滤池 XL-F10 先例）；功率/日电耗
#   DIMENSIONLESS（TJ-F9/KN-F6 kW 语义 meaning 承载先例——ENERGY
#   量纲扩成员归 B4-2b 一并评估）。
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
        "AO-F21",
        "q_air = o2_total * f_sor / (o2_per_air * ea * 86400)",
        {
            "o2_total": (_M, "总需氧量 kg/d（AO-F12）"),
            "f_sor": (_D, "AOR→SOR 折算系数（factor.aao.blower.sor_factor）"),
            "o2_per_air": (_D, "标态空气含氧质量浓度 kg/m3（factor.aao.blower.o2_per_air）"),
            "ea": (_D, "微孔曝气氧利用率（factor.aao.blower.oxygen_transfer_eff）"),
        },
        _F,
        f"{_HB}；Gs=O2/(0.28·EA) 手册口径（86400=d→s 换算；AOR→SOR "
        "五系数分列修正挂账 B4-2b——综合折算系数 f_sor 承载）",
    ),
    FormulaSpec(
        "AO-F22",
        "p_blower = q_air * p_pressure / eta_blower",
        {
            "q_air": (_F, "供气量 m3/s（AO-F21）"),
            "p_pressure": (_D, "风机出口压力 kPa（factor.aao.blower.pressure_kpa）"),
            "eta_blower": (_D, "罗茨风机综合效率（factor.aao.blower.efficiency）"),
        },
        _D,
        f"{_HB}；P=Q·Δp/η（m3/s×kPa=kW 直读）；Δp=有效水深+管损"
        "裕量档",
    ),
    FormulaSpec(
        "AO-F23",
        "e_aeration = p_blower * 24",
        {
            "p_blower": (_D, "风机轴功率 kW（AO-F22）"),
        },
        _D,
        f"{_HB}；连续曝气 24 h/d 满时口径（AAO 连续流，电机变频跟踪"
        "负荷；kW×h=kWh/d）",
    ),
    FormulaSpec(
        "AO-F24",
        "p_stir = (v_anoxic + v_anaerobic) * w_stir_bio / 1000",
        {
            "v_anoxic": (_VOL, "缺氧区容积 m3（AO-F4）"),
            "v_anaerobic": (_VOL, "厌氧区容积 m3（AO-F3）"),
            "w_stir_bio": (_D, "潜水搅拌功率密度 W/m3（factor.aao.stir.power_density）"),
        },
        _D,
        f"{_HB}；缺氧/厌氧区潜水搅拌（密度带同 tiaojiechi TJ-F9 族；"
        "好氧区曝气混合不另计；/1000=W→kW）",
    ),
    FormulaSpec(
        "AO-F25",
        "e_stir = p_stir * 24",
        {
            "p_stir": (_D, "搅拌装机功率 kW（AO-F24）"),
        },
        _D,
        f"{_HB}；防沉积搅拌连续运行 24 h/d（kW×h=kWh/d）",
    ),
)
