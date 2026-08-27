"""紫外消毒清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_ziwai.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KZ-F1~F11 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_ziwai"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=3 渠/b_channel=1.7 m/
#   h_channel=1.2 m；p_lamp=250 W/n_layer=6 支每排/d_long=0.12 m 排间距/
#   xi_total=3 局部损失系数和/n_t=1.5 透光指数；t254=65 %——带键
#   60.0/70.0 百分数存储口径[0.5.0 R1 批内修正]，公式 (t254/100)**n_t
#   以百分数入参）；系数不落本表——设计剂量+流速带+穿透率带（60~70
#   高于市政 55~65 档）+老化系数+结垢系数（矿井水矿物度特征键，市政
#   面无）+几何效率+水损构造下限+超高+壁厚系数+高程水损全部经
#   factor.mine_ziwai.* 键消费（app._unit_params 线感知投影，mine_
#   限定）；去除率经 removal.mine_ziwai.{ss,cod}.mod_default 键
#   （物理消毒无去除，显式 0.0 穿流——消毒对象为回用卫生指标
#   GB/T 31392-2022 而非市政粪大肠面；BOD5 全线不建键）。
# 【公式注册（D1）】KZ-F1~F11 逐条 FormulaSpec+register；expression=
#   表公式串转受限 DSL——data 包系数（dose/eta_geo/f_aging/f_fouling/
#   loss_min/h_super）一律符号绑定（零系数字面量）；结构常数内联
#   （本文件=units_lib manifest 白名单区）：×3600（m3/s→m³/h 流量
#   口径注记——表内 q_ch 展开内联，KZ-F1/KZ-F3 往返同型）、÷100
#   （穿透率百分数入参折算）、÷10（W/m²→mW/cm² 量纲链折算——表
#   KZ-F5 原文）、g=9.81 m/s²（物理条文常量，表头内联注记——区别
#   M1A g_gravity 符号绑定形态，本表串原文直书）；max 直接用
#   （KZ-F10 构造裕量下限）。DSL 无 ceil：灯管排数向上取整在
#   compute 收口（取整前 n_rows_raw 审计面）。
# 【灯管布置实算主线】区别市政 ziwai 单灯处理量概算锚路线（无
#   q_per_lamp/粪大肠键族）：辐照强度→单排剂量→排数 ceil 满足设计
#   剂量→实算剂量校核（≥dose 合格面由 ceil 结构保证，constraints
#   声明）；渠内公式水损与 elevation_loss 经验键双轨语义（公式值走
#   校核面/经验值走高程链——表追认点 14）。
# 【声明五件】params（range 仅表内有出处带者：t254 穿透率带一条；
#   渠数/渠宽/水深/灯功率/每排灯数/排间距/损失系数和/透光指数构造
#   参数无范围来源不设）/ports 两口 WATER/removal_refs 双指标零去除
#   键/norm_refs 三源标记（GB/T 31392-2022+GB/T 41019-2021+给水排水
#   设计手册）/condition_mappings=()/constraint_refs 三键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_ziwai"

_GT = (
    "GB/T 31392-2022（矿井水回用消毒卫生指标与剂量，条号待核对；"
    "docs/norms/mine_water_ziwai.md 起草表 2026-08-27，待追认）"
)
_GB = (
    "GB/T 41019-2021（矿井水处理工艺消毒段/灯套管结垢衰减，条号待核对；"
    "docs/norms/mine_water_ziwai.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 3 册 城镇给水）》紫外消毒灯管布置/渠内"
    "流速/渠道水损常用带（docs/norms/mine_water_ziwai.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KZ-F1",
        "q_ch = q_design * 3600 / n",
        {
            "q_design": (
                _F,
                "最高时设计流量 m3/s（×3600 转 m³/h 口径——表内 q_ch 展开内联）",
            ),
            "n": (_D, "渠数（参数 n，检修兼顾 ≥2，副算例 n=1 检修极限工况可算）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KZ-F2",
        "a_ch = b_channel * h_channel",
        {
            "b_channel": (_L, "渠宽 m（参数 b_channel）"),
            "h_channel": (_L, "渠内有效水深 m（参数 h_channel）"),
        },
        _A,
        _HB,
    ),
    FormulaSpec(
        "KZ-F3",
        "v_ch = (q_ch / 3600) / a_ch",
        {
            "q_ch": (_D, "单渠流量 m3/h（KZ-F1；÷3600 折 m³/s 口径）"),
            "a_ch": (_A, "渠断面积 m2（KZ-F2）"),
        },
        _V,
        _HB,
    ),
    FormulaSpec(
        "KZ-F4",
        "t_eff = (t254 / 100) ** n_t",
        {
            "t254": (_D, "254 nm 穿透率 %（参数 t254，百分数口径——÷100 折分数）"),
            "n_t": (_D, "透光指数（参数 n_t，构造默认 1.5）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KZ-F5",
        "i_avg = p_lamp * n_layer * eta_geo * t_eff * f_aging * f_fouling / (10 * a_ch)",
        {
            "p_lamp": (_D, "单灯功率 W（参数 p_lamp）"),
            "n_layer": (_D, "每排灯数（参数 n_layer）"),
            "eta_geo": (_D, "几何效率（factor.mine_ziwai.eta_geo）"),
            "t_eff": (_D, "有效穿透率（KZ-F4）"),
            "f_aging": (_D, "灯管老化系数（factor.mine_ziwai.f_aging——寿命末期输出保持比）"),
            "f_fouling": (
                _D,
                "灯套管结垢系数（factor.mine_ziwai.f_fouling——矿井水矿物度特征键，市政无）",
            ),
            "a_ch": (_A, "渠断面积 m2（KZ-F2；÷10=W/m²→mW/cm² 量纲链折算——表原文）"),
        },
        _D,
        f"{_HB}；{_GB}",
    ),
    FormulaSpec(
        "KZ-F6",
        "dose_row = i_avg * d_long / v_ch",
        {
            "i_avg": (_D, "辐照强度 mW/cm2（KZ-F5）"),
            "d_long": (_L, "灯排间距 m（参数 d_long——d_long/v=单排曝光时间）"),
            "v_ch": (_V, "渠内流速 m/s（KZ-F3）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KZ-F7",
        "n_rows = dose / dose_row",
        {
            "dose": (_D, "设计剂量 mJ/cm2（factor.mine_ziwai.dose——排数向上取整）"),
            "dose_row": (_D, "单排剂量 mJ/cm2（KZ-F6）"),
        },
        _D,
        _GT,
    ),
    FormulaSpec(
        "KZ-F8",
        "dose_act = n_rows * dose_row",
        {
            "n_rows": (_D, "灯管排数（ceil 后）"),
            "dose_row": (_D, "单排剂量 mJ/cm2（KZ-F6）"),
        },
        _D,
        _GT,
    ),
    FormulaSpec(
        "KZ-F9",
        "t_contact = n_rows * d_long / v_ch",
        {
            "n_rows": (_D, "灯管排数（ceil 后）"),
            "d_long": (_L, "灯排间距 m（参数 d_long）"),
            "v_ch": (_V, "渠内流速 m/s（KZ-F3）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KZ-F10",
        "h_loss = max(xi_total * v_ch ** 2 / (2 * 9.81), loss_min)",
        {
            "xi_total": (_D, "渠内局部损失系数和（参数 xi_total；g=9.81 m/s² 物理条文常量内联）"),
            "v_ch": (_V, "渠内流速 m/s（KZ-F3）"),
            "loss_min": (
                _D,
                "渠道水损构造裕量下限 m（factor.mine_ziwai.loss_min——经验值走高程链键）",
            ),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KZ-F11",
        "h_total = h_super + h_channel",
        {
            "h_super": (_L, "超高 m（factor.mine_ziwai.superheight）"),
            "h_channel": (_L, "渠内有效水深 m（参数 h_channel）"),
        },
        _L,
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
        "i18n_key": "units.mine_water_ziwai",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_ziwai.md 参数档）；
        # range 仅一条有出处带参数（t254_band 60~70 百分数口径——滤后清
        # 矿井水高于市政 55~65 档），渠数/渠宽/水深/灯功率/每排灯数/
        # 排间距/损失系数和/透光指数构造参数无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 3.0},
            {"field_id": "b_channel", "dim": "LENGTH", "default": 1.7},
            {"field_id": "h_channel", "dim": "LENGTH", "default": 1.2},
            {"field_id": "p_lamp", "dim": "DIMENSIONLESS", "default": 250.0},
            {"field_id": "n_layer", "dim": "DIMENSIONLESS", "default": 6.0},
            {"field_id": "d_long", "dim": "LENGTH", "default": 0.12},
            {"field_id": "xi_total", "dim": "DIMENSIONLESS", "default": 3.0},
            {"field_id": "n_t", "dim": "DIMENSIONLESS", "default": 1.5},
            {
                "field_id": "t254",
                "dim": "DIMENSIONLESS",
                "default": 65.0,
                "range": {"min": 60.0, "max": 70.0},
            },
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_ziwai.ss.mod_default",
            "CODCR": "removal.mine_ziwai.cod.mod_default",
        },
        "norm_refs": [
            "GB/T 31392-2022（矿井水回用消毒卫生指标与剂量，条号待核对）",
            "GB/T 41019-2021（矿井水处理工艺消毒段/灯套管结垢衰减，条号待核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》紫外消毒灯管布置/渠内流速常用带",
            "docs/norms/mine_water_ziwai.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_ziwai.velocity_band",
            "mine_water_ziwai.t254_band",
            "mine_water_ziwai.dose_check",
        ],
    }
)
