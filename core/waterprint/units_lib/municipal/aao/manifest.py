"""AAO 生物池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表起草真源（docs/norms/aao.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.2.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ AO-F1~F14 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收；
#   公式路线 = ADR-008 ①逐字落地：负荷法主线+泥龄校核带）
#
# 【固定形态】UNIT_ID = "municipal_aao"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 逐字（n=2/Ns=0.10/X=4000/t_p=1.5 h/
#   R=1.0/Ri=2.0/TN_eff=15[出水标准数据条目，一级 A]/sec_per_hour=3600
#   [时换算，M1a 同款参数形态]）；系数不落本表——Kde/y/a′/b′/vss_ratio/
#   P/七条校核带全部经 factor.aao.* 键消费（app._unit_params 投影）；
#   去除率经 removal.aao.*.mod_default 键（六指标全键：BOD5/CODCR/SS+
#   NH3N/TN/TP——N/P 三键 NP1 起草 0.8.0、RATIFY3 追认 2026-08-28）。
# 【公式注册（D2）】AO-F1~F14 逐条 FormulaSpec+register；expression=三表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构常数
#   （24/1000/4.57/2.86/86400）内联（本文件=units_lib manifest 白名单区；
#   4.57/2.86=氧当量条文常量，出处=norm_ref）。流量换算 86400/流量
#   口径注记（WaterFlow 规范单位 m3/s，表口径 m3/d/m3/h——AO-F13/F14 的
#   q_design_h/q_avg_h 为符号、由 compute 经 sec_per_hour 合成）。
# 【追认口径按表冻结】AO-F8 好氧泥龄判断口径（全池口径备考注记）；
#   AO-F13 外回流泵按最高时 q_design_h / AO-F14 内回流泵按平均时
#   q_avg_h（双口径相差 Kz 倍，各有工程做法依据——统一与否待领域专家
#   追认裁定）——逐字实现，代码零裁量。
# 【DSL 单输出导出量】delta_n（=TN_in−tn_eff，AO-F4 入参）、x_vss（=
#   vss_ratio×x_mlss，AO-F9 入参）、bod5_out（=bod5_in×(1−removal.aao.
#   bod5)，AO-F6/F9 入参）、v_total/t_total/v_o_series（容积合成/HRT/
#   单系列）在 compute 以符号算术合成（零字面量，无新工程常数）。
# 【档位声明（Ruling ④）】池数 n grid=[2,3,4,5,6]（GB 50014 池数≥2 精神+
#   CASS n_pool 先例档，M2-SOL §7 档位补齐，待追认）；档位下限归 grid
#   层承载，compute 只保 n>0 数学有效性。
# 【声明五件】params（range 仅表内有出处带者：Ns/X/t_p/R/Ri 五参数）/
#   ports 两口 WATER+sludge_out SLUDGE 产股口（GOLDEN4a D3——无条件产股，
#   无边也产；nongsuo sup 先例同构）/removal_refs/norm_refs 双源标记
#   （GB 50014-2021+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 七键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_aao"

_GB = "GB 50014-2021 §7.6（docs/norms/aao.md 起草表 2026-08-25，待追认）"
_HB = "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/aao.md 起草表 2026-08-25，待追认）"
_D = DimKey.DIMENSIONLESS
_C = DimKey.CONCENTRATION
_F = DimKey.FLOW
_VOL = DimKey.VOLUME
_M = DimKey.MASS

# 单位换算常量（GOLDEN4a D3 产股口：排泥工程口径 m³/d、kg/d → SludgeFlow
# 契约口径 m3/s、kg/s——manifest=数值白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "AO-F1",
        "v_o = q_avg_daily * 86400 * bod5_in / (ns * x_mlss)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "bod5_in": (_C, "进流 BOD5 mg/L"),
            "ns": (_D, "BOD5 污泥负荷 kgBOD5/(kgMLSS·d)（参数 ns）"),
            "x_mlss": (_C, "设计 MLSS mg/L（参数 x_mlss）"),
        },
        _VOL,
        "GB 50014-2021 §7.6.10（容积公式；docs/norms/aao.md 起草表 2026-08-25，待追认）",
    ),
    FormulaSpec(
        "AO-F2",
        "t_o = 24 * v_o / (q_avg_daily * 86400)",
        {"v_o": (_VOL, "好氧区容积 m3"), "q_avg_daily": (_F, "平均日流量 m3/s")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "AO-F3",
        "v_anaerobic = q_avg_daily * 86400 * t_p / 24",
        {"q_avg_daily": (_F, "平均日流量 m3/s"), "t_p": (_D, "厌氧区 HRT h（参数 t_p）")},
        _VOL,
        "GB 50014-2021 §7.6.39（厌氧区 HRT 1~2h；docs/norms/aao.md 起草表 2026-08-25，待追认）",
    ),
    FormulaSpec(
        "AO-F4",
        "v_anoxic = q_avg_daily * 86400 * delta_n / (k_denit * x_mlss)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "delta_n": (_C, "反硝化脱氮量 mg/L（=TN_in−tn_eff）"),
            "k_denit": (_D, "反硝化速率 Kde（factor.aao.k_denit）"),
            "x_mlss": (_C, "设计 MLSS mg/L（参数 x_mlss）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "AO-F5",
        "t_n = 24 * v_anoxic / (q_avg_daily * 86400)",
        {"v_anoxic": (_VOL, "缺氧区容积 m3"), "q_avg_daily": (_F, "平均日流量 m3/s")},
        _D,
        _HB,
    ),
    FormulaSpec(
        "AO-F6",
        "s_y = q_avg_daily * 86400 * (bod5_in - bod5_out) * y_yield / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "bod5_in": (_C, "进流 BOD5 mg/L"),
            "bod5_out": (_C, "出流 BOD5 mg/L（=bod5_in×(1−removal.aao.bod5)）"),
            "y_yield": (_D, "污泥产率 y（factor.aao.yield.y）"),
        },
        _M,
        "GB 50014-2021 §8.1.4 表 5（AAO 污泥产率 0.4~0.6；"
        "docs/norms/aao.md 起草表 2026-08-25，待追认）",
    ),
    FormulaSpec(
        "AO-F7",
        "q_wet = s_y / ((1 - p_moisture) * 1000)",
        {
            "s_y": (_M, "剩余污泥干固体 kg/d"),
            "p_moisture": (_D, "剩余污泥含水率（factor.aao.sludge.moisture）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "AO-F8",
        "theta_c = v_o * x_mlss / (1000 * s_y)",
        {
            "v_o": (_VOL, "好氧区容积 m3"),
            "x_mlss": (_C, "设计 MLSS mg/L"),
            "s_y": (_M, "剩余污泥干固体 kg/d"),
        },
        _D,
        "GB 50014-2021 §7.6（AAO 泥龄 11~23d；判断口径=好氧泥龄，全池口径"
        "备考注记见 docs/norms/aao.md——待领域专家追认）",
    ),
    FormulaSpec(
        "AO-F9",
        "o2_carbon = a_prime * q_avg_daily * 86400 * (bod5_in - bod5_out) / 1000"
        " + b_prime * v_o * x_vss / 1000",
        {
            "a_prime": (_D, "碳化需氧系数 a′（factor.aao.o2.a_prime）"),
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "bod5_in": (_C, "进流 BOD5 mg/L"),
            "bod5_out": (_C, "出流 BOD5 mg/L"),
            "b_prime": (_D, "内源耗氧系数 b′（factor.aao.o2.b_prime）"),
            "v_o": (_VOL, "好氧区容积 m3"),
            "x_vss": (_C, "MLVSS mg/L（=vss_ratio×x_mlss）"),
        },
        _M,
        _HB,
    ),
    FormulaSpec(
        "AO-F10",
        "o2_nit = 4.57 * q_avg_daily * 86400 * (tkn_in - tn_eff) / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "tkn_in": (_C, "进水 TN mg/L（凯氏氮口径）"),
            "tn_eff": (_C, "设计出水 TN mg/L（参数 tn_eff，出水标准数据条目）"),
        },
        _M,
        "《给水排水设计手册（第 5 册 城镇排水）》硝化氧当量 4.57"
        "（docs/norms/aao.md 起草表 2026-08-25，待追认）",
    ),
    FormulaSpec(
        "AO-F11",
        "o2_denit = 2.86 * q_avg_daily * 86400 * (tkn_in - tn_eff) / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "tkn_in": (_C, "进水 TN mg/L"),
            "tn_eff": (_C, "设计出水 TN mg/L（参数 tn_eff）"),
        },
        _M,
        "《给水排水设计手册（第 5 册 城镇排水）》反硝化氧当量 2.86"
        "（docs/norms/aao.md 起草表 2026-08-25，待追认）",
    ),
    FormulaSpec(
        "AO-F12",
        "o2_total = o2_carbon + o2_nit - o2_denit",
        {
            "o2_carbon": (_M, "碳化需氧量 kg/d"),
            "o2_nit": (_M, "硝化需氧量 kg/d"),
            "o2_denit": (_M, "反硝化供氧回收 kg/d"),
        },
        _M,
        _HB,
    ),
    FormulaSpec(
        "AO-F13",
        "q_return = r_external * q_design_h",
        {
            "r_external": (_D, "外回流比（参数 r_external）"),
            "q_design_h": (_D, "最高时流量 m3/h（=q_design×sec_per_hour）"),
        },
        _D,
        "《给水排水设计手册（第 5 册 城镇排水）》AAO 外回流常用带；"
        "外回流泵按最高时流量口径（与二沉最高时水力联动配套，双口径"
        "注记见 docs/norms/aao.md——待领域专家追认）",
    ),
    FormulaSpec(
        "AO-F14",
        "q_internal = r_internal * q_avg_h",
        {
            "r_internal": (_D, "内回流比（参数 r_internal）"),
            "q_avg_h": (_D, "平均时流量 m3/h（=q_avg_daily×sec_per_hour）"),
        },
        _D,
        "《给水排水设计手册（第 5 册 城镇排水）》AAO 内回流常用带；"
        "内回流泵按平均时流量口径（平均日运行+变频调节，双口径注记"
        "见 docs/norms/aao.md——待领域专家追认）",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.municipal_aao",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/aao.md 参数档/算例输入行）；
        # range 仅七条有出处带参数（ns_band/mlss_band/hrt_anaerobic_band/
        # r_external_band/r_internal_band 五参数+L7 池体图元批 h2/ratio_lb
        # 两参数——CASS 同值同 range 平移），tn_eff 出水标准值与构造参数
        # n/sec_per_hour/side_disc_step 无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2, 3, 4, 5, 6]},
            {
                "field_id": "ns",
                "dim": "DIMENSIONLESS",
                "default": 0.10,
                "range": {"min": 0.05, "max": 0.15},
            },
            {
                "field_id": "x_mlss",
                "dim": "CONCENTRATION",
                "default": 4000.0,
                "range": {"min": 3500.0, "max": 4500.0},
            },
            {
                "field_id": "t_p",
                "dim": "DIMENSIONLESS",
                "default": 1.5,
                "range": {"min": 1.0, "max": 2.0},
            },
            {
                "field_id": "r_external",
                "dim": "DIMENSIONLESS",
                "default": 1.0,
                "range": {"min": 0.5, "max": 1.0},
            },
            {
                "field_id": "r_internal",
                "dim": "DIMENSIONLESS",
                "default": 2.0,
                "range": {"min": 1.0, "max": 3.0},
            },
            # tn_eff 双口径并存记档（NP2）：池容 AO-F4 设计目标 tn_eff=15
            # （AO-F4 入参 delta_n=TN_in−tn_eff，辖池容机理链）与出流水质
            # 键族 TN=TN_in×(1−removal.aao.tn)（辖出流水质链）双口径并行
            # ——语义不冲突（机理池容 vs 出流浓度两链各辖其面）。
            {"field_id": "tn_eff", "dim": "CONCENTRATION", "default": 15.0},
            {"field_id": "sec_per_hour", "dim": "DIMENSIONLESS", "default": 3600.0},
            # L7 池体图元批几何形态参数三件（CASS 同值同 range 平移——
            # 出处=GB 50014-2021 §6+给水排水设计手册第 5 册，CASS manifest
            # 先例措辞；h2=有效水深 m、ratio_lb=池长宽比、side_disc_step=
            # 边长圆整档 m——AO-F15~F19 几何族消费）
            {"field_id": "h2", "dim": "LENGTH", "default": 5.0, "range": {"min": 4.0, "max": 6.0}},
            {
                "field_id": "ratio_lb",
                "dim": "DIMENSIONLESS",
                "default": 2.5,
                "range": {"min": 2.0, "max": 3.0},
            },
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
            # GOLDEN4a D3 产股口（2026-08-28）：无条件产股（无边也产——
            # nongsuo sup 先例同构）；产股三量=AO-F6/F7 全厂口径投影
            # （ds=s_y——hebing 注入 ds_bio 链路同源；moisture=
            # factor.aao.sludge.moisture 0.994，与 sludge_hebing p_bio
            # 默认同源声明）。
            {"port_id": "sludge_out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.aao.bod5.mod_default",
            "CODCR": "removal.aao.cod.mod_default",
            "SS": "removal.aao.ss.mod_default",
            "NH3N": "removal.aao.nh3n.mod_default",
            "TN": "removal.aao.tn.mod_default",
            "TP": "removal.aao.tp.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §7.6（§7.6.10 容积公式、§7.6.39 厌氧区 HRT）、"
            "§8.1.4 表 5",
            "《给水排水设计手册（第 5 册 城镇排水）》AAO 工艺分区/需氧量/回流比常用值",
            "docs/norms/aao.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "aao.ns_band",
            "aao.mlss_band",
            "aao.hrt_anaerobic_band",
            "aao.hrt_anoxic_band",
            "aao.sludge_age_band",
            "aao.r_external_band",
            "aao.r_internal_band",
        ],
    }
)
