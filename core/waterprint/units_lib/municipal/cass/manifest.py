"""CASS 生物池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表起草真源（docs/norms/cass.md，2026-08-26，数据策略 v2 待追认）+
       data/coefficients 0.4.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ CA-F1~F27 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收；公式路线 =
#   周期循环工艺主线——4h 周期档+负荷法主容积[AAO 同族]+滗水容积
#   ≤池深 1/3 双控池面积[business-logic §8 行 8]）
#
# 【固定形态】UNIT_ID = "municipal_cass"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 逐字（n_pool=4/t_cycle=4 h/反应 2/
#   沉淀 1/滗水 1 h/Ns=0.10/X=4000[SBR 变体档]/t_selector=0.75 h/
#   h2=5.0 m/ratio_lb=2.5/TN_eff=15[出水标准数据条目]/L-B 档 0.5 m）；
#   系数不落本表——ns/mlss/泥龄/滗水/选择区五校核带+需氧量/剩余污泥
#   同族系数+滗水器单台能力+超高/壁厚/高程水损全部经 factor.cass.*
#   键消费（app._unit_params 投影）；去除率经 removal.cass.*.mod_default
#   （AAO 同族档 0.90/0.85/0.90；NH3N/TN/TP 不建条目）。
# 【公式注册（D1）】CA-F1~F27 逐条 FormulaSpec+register；expression=三表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构
#   常数（24/86400/1000/3/4.57/2.86）内联（本文件=units_lib manifest
#   白名单区；24=日时/86400=日秒/3=滗水上限 1/3 池深倒数/4.57·2.86=
#   氧当量条文常量，出处=norm_ref）。DSL 无 ceil：滗水器台数 n_decant
#   （整台）/池长 l_pool/池宽 b_pool（0.5 m 档）在 compute 收口。
# 【档位声明（Ruling ④）】池数 n_pool grid=[2,3,4,5,6]（档位下限 ≥2 由
#   grid 层承载）；周期 t_cycle grid=[4,6,8]（business-logic §7 周期档）
#   ——compute 只保 n>0 数学有效性，不硬编码 ≥2。
# 【声明五件】params（range 仅表内有出处带者：Ns/X/t_selector/h2/
#   ratio_lb 五参数）/ports 两口 WATER/removal_refs（AAO 同族键同引用
#   形态）/norm_refs 双源标记（GB 50014-2021+给水排水设计手册）/
#   condition_mappings=()/constraint_refs 五键（时段和=周期不变性为
#   compute 域拒非警告带——不在此声明）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_cass"

_GB = "GB 50014-2021 §7.6（docs/norms/cass.md 起草表 2026-08-26，待追认）"
_HB = "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/cass.md 起草表 2026-08-26，待追认）"
_D = DimKey.DIMENSIONLESS
_C = DimKey.CONCENTRATION
_F = DimKey.FLOW
_VOL = DimKey.VOLUME
_L = DimKey.LENGTH
_AREA = DimKey.AREA
_M = DimKey.MASS
_T = DimKey.TIME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "CA-F1",
        "n_cycle = 24 / t_cycle",
        {"t_cycle": (_D, "周期 h（参数 t_cycle，4h 档主线，business-logic §7 周期档）")},
        _D,
        _HB,
    ),
    FormulaSpec(
        "CA-F2",
        "v_draw = q_avg_daily * 86400 / (n_pool * n_cycle)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "n_pool": (_D, "池数（参数 n_pool，grid 层 ≥2 档）"),
            "n_cycle": (_D, "每日周期数 1/d"),
        },
        _VOL,
        f"{_GB}（序批式周期进水容积）；{_HB}",
    ),
    FormulaSpec(
        "CA-F3",
        "v_load = q_avg_daily * 86400 * bod5_in / (ns * x_mlss)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "bod5_in": (_C, "进流 BOD5 mg/L"),
            "ns": (_D, "BOD5 污泥负荷 kgBOD5/(kgMLSS·d)（参数 ns）"),
            "x_mlss": (_C, "设计 MLSS mg/L（参数 x_mlss，SBR 变体档）"),
        },
        _VOL,
        "GB 50014-2021 §7.6.10（容积公式，SBR 变体负荷档；"
        "docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F4",
        "v_selector = q_avg_daily * 86400 * t_selector / 24",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "t_selector": (_D, "生物选择区 HRT h（参数 t_selector）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CA-F5",
        "v_bio = v_load + v_selector",
        {"v_load": (_VOL, "负荷法主反应区容积 m3"), "v_selector": (_VOL, "生物选择区容积 m3")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CA-F6",
        "h_draw_max = h2 / 3",
        {"h2": (_L, "有效水深 m（参数 h2）")},
        _L,
        "business-logic §8 行 8（滗水容积 ≤ 池深 1/3）；"
        "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/cass.md 起草表，待追认）",
    ),
    FormulaSpec(
        "CA-F7",
        "a_draw = v_draw / h_draw_max",
        {"v_draw": (_VOL, "单池单周期滗水容积 m3"), "h_draw_max": (_L, "滗水深度上限 m")},
        _AREA,
        "business-logic §8 行 8；"
        "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/cass.md 起草表，待追认）",
    ),
    FormulaSpec(
        "CA-F8",
        "a_load = v_bio / (n_pool * h2)",
        {"v_bio": (_VOL, "生物反应总容积 m3"), "n_pool": (_D, "池数"), "h2": (_L, "有效水深 m")},
        _AREA,
        _HB,
    ),
    FormulaSpec(
        "CA-F9",
        "a_pool = max(a_load, a_draw)",
        {"a_load": (_AREA, "负荷法单池面积 m2"), "a_draw": (_AREA, "滗水控制单池面积 m2")},
        _AREA,
        "《给水排水设计手册（第 5 册 城镇排水）》双控取大设计法"
        "（docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F10",
        "h_draw = v_draw / a_pool",
        {"v_draw": (_VOL, "单池单周期滗水容积 m3"), "a_pool": (_AREA, "实取单池水面面积 m2")},
        _L,
        "business-logic §8 行 8；"
        "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/cass.md 起草表，待追认）",
    ),
    FormulaSpec(
        "CA-F11",
        "v_pool = a_pool * h2",
        {"a_pool": (_AREA, "单池水面面积 m2"), "h2": (_L, "有效水深 m")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CA-F12",
        "v_plant = v_pool * n_pool",
        {"v_pool": (_VOL, "单池有效容积 m3"), "n_pool": (_D, "池数")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CA-F13",
        "t_phase_sum = t_react + t_settle + t_draw",
        {
            "t_react": (_D, "反应时段 h（参数 t_react）"),
            "t_settle": (_D, "沉淀时段 h（参数 t_settle）"),
            "t_draw": (_D, "滗水时段 h（参数 t_draw）"),
        },
        _T,
        "GB 50014-2021 §7.6（序批式时段分配）；"
        "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/cass.md 起草表，待追认）",
    ),
    FormulaSpec(
        "CA-F14",
        "q_decant = v_draw / t_draw",
        {"v_draw": (_VOL, "单池单周期滗水容积 m3"), "t_draw": (_D, "滗水时段 h（参数 t_draw）")},
        _D,
        _HB,
    ),
    FormulaSpec(
        "CA-F15",
        "n_decant_raw = q_decant / q_per_decant",
        {
            "q_decant": (_D, "滗水能力需求 m3/h"),
            "q_per_decant": (_D, "单台滗水器滗水量 m3/h（factor.cass.decant.q_per_unit）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "CA-F16",
        "s_y = q_avg_daily * 86400 * (bod5_in - bod5_out) * y_yield / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "bod5_in": (_C, "进流 BOD5 mg/L"),
            "bod5_out": (_C, "出流 BOD5 mg/L（=bod5_in×(1−removal.cass.bod5)）"),
            "y_yield": (_D, "污泥产率 y（factor.cass.yield.y，AAO 同族口径）"),
        },
        _M,
        "GB 50014-2021 §8.1.4 表 5（AAO 同族口径；"
        "docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F17",
        "q_wet = s_y / ((1 - p_moisture) * 1000)",
        {
            "s_y": (_M, "剩余污泥干固体 kg/d"),
            "p_moisture": (_D, "剩余污泥含水率（factor.cass.sludge.moisture）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CA-F18",
        "theta_c = v_load * x_mlss / (1000 * s_y)",
        {
            "v_load": (_VOL, "主反应区容积 m3"),
            "x_mlss": (_C, "设计 MLSS mg/L"),
            "s_y": (_M, "剩余污泥干固体 kg/d"),
        },
        _D,
        "《给水排水设计手册（第 5 册 城镇排水）》CASS 泥龄 15~25d 常用带"
        "（主反应区口径；docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F19",
        "o2_carbon = a_prime * q_avg_daily * 86400 * (bod5_in - bod5_out) / 1000"
        " + b_prime * v_load * x_vss / 1000",
        {
            "a_prime": (_D, "碳化需氧系数 a′（factor.cass.o2.a_prime）"),
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "bod5_in": (_C, "进流 BOD5 mg/L"),
            "bod5_out": (_C, "出流 BOD5 mg/L"),
            "b_prime": (_D, "内源耗氧系数 b′（factor.cass.o2.b_prime）"),
            "v_load": (_VOL, "主反应区容积 m3"),
            "x_vss": (_C, "MLVSS mg/L（=vss_ratio×x_mlss）"),
        },
        _M,
        _HB,
    ),
    FormulaSpec(
        "CA-F20",
        "o2_nit = 4.57 * q_avg_daily * 86400 * (tkn_in - tn_eff) / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "tkn_in": (_C, "进水 TN mg/L（凯氏氮口径）"),
            "tn_eff": (_C, "设计出水 TN mg/L（参数 tn_eff，出水标准数据条目）"),
        },
        _M,
        "《给水排水设计手册（第 5 册 城镇排水）》硝化氧当量 4.57"
        "（AAO 同族口径；docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F21",
        "o2_denit = 2.86 * q_avg_daily * 86400 * (tkn_in - tn_eff) / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "tkn_in": (_C, "进水 TN mg/L"),
            "tn_eff": (_C, "设计出水 TN mg/L（参数 tn_eff）"),
        },
        _M,
        "《给水排水设计手册（第 5 册 城镇排水）》反硝化氧当量 2.86"
        "（AAO 同族口径；docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F22",
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
        "CA-F23",
        "ns_act = ns * v_bio / v_plant",
        {
            "ns": (_D, "设计污泥负荷"),
            "v_bio": (_VOL, "生物反应总容积 m3"),
            "v_plant": (_VOL, "全厂池容 m3"),
        },
        _D,
        "GB 50014-2021 §7.6.10（docs/norms/cass.md 起草表 2026-08-26，待追认）",
    ),
    FormulaSpec(
        "CA-F24",
        "h_pool = h_super + h2",
        {"h_super": (_L, "池超高 m（factor.cass.superheight）"), "h2": (_L, "有效水深 m")},
        _L,
        "GB 50014-2021 §6（超高一般要求）；"
        "《给水排水设计手册（第 5 册 城镇排水）》（docs/norms/cass.md 起草表，待追认）",
    ),
    FormulaSpec(
        "CA-F25",
        "l_pool_raw = sqrt(a_pool * ratio_lb)",
        {"a_pool": (_AREA, "单池水面面积 m2"), "ratio_lb": (_D, "池长宽比（参数 ratio_lb）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "CA-F26",
        "b_pool_raw = sqrt(a_pool / ratio_lb)",
        {"a_pool": (_AREA, "单池水面面积 m2"), "ratio_lb": (_D, "池长宽比（参数 ratio_lb）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "CA-F27",
        "v_concrete = a_pool * h_pool * n_pool * wall_coef",
        {
            "a_pool": (_AREA, "单池水面面积 m2"),
            "h_pool": (_L, "池总高 m"),
            "n_pool": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.cass.wall_thickness_coef，概算口径）"),
        },
        _VOL,
        _HB,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.municipal_cass",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/cass.md 参数档/算例输入行）；
        # grid=池数/周期离散档（Ruling ④：档位下限经 grid 声明，compute 只保
        # n>0）；range 仅五条有出处带参数（ns/mlss/t_selector/h2/ratio_lb），
        # 时段参数与 tn_eff/步长无范围来源不设
        "params": [
            {"field_id": "n_pool", "dim": "DIMENSIONLESS", "default": 4.0, "grid": [2, 3, 4, 5, 6]},
            {"field_id": "t_cycle", "dim": "DIMENSIONLESS", "default": 4.0, "grid": [4, 6, 8]},
            {"field_id": "t_react", "dim": "DIMENSIONLESS", "default": 2.0},
            {"field_id": "t_settle", "dim": "DIMENSIONLESS", "default": 1.0},
            {"field_id": "t_draw", "dim": "DIMENSIONLESS", "default": 1.0},
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
                "range": {"min": 3000.0, "max": 5000.0},
            },
            {
                "field_id": "t_selector",
                "dim": "DIMENSIONLESS",
                "default": 0.75,
                "range": {"min": 0.5, "max": 1.0},
            },
            {"field_id": "h2", "dim": "LENGTH", "default": 5.0, "range": {"min": 4.0, "max": 6.0}},
            {
                "field_id": "ratio_lb",
                "dim": "DIMENSIONLESS",
                "default": 2.5,
                "range": {"min": 2.0, "max": 3.0},
            },
            {"field_id": "tn_eff", "dim": "CONCENTRATION", "default": 15.0},
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.cass.bod5.mod_default",
            "CODCR": "removal.cass.cod.mod_default",
            "SS": "removal.cass.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §7.6（序批式活性污泥法 SBR 变体；§7.6.10 容积公式、"
            "§8.1.4 表 5——小节号随追认逐条核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》SBR/CASS 章（周期时段分配/"
            "滗水器选型/生物选择区常用值）",
            "docs/norms/cass.md（2026-08-26 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "cass.ns_band",
            "cass.mlss_band",
            "cass.sludge_age_band",
            "cass.draw_band",
            "cass.selector_band",
        ],
    }
)
