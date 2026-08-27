"""集水井清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/conveyance_jishuijing.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.7.0 键名（factor.jishuijing.* 裸短名 9 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ JS-F1~JS-F7 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "conveyance_jishuijing"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（t_well=5 min/h_well=3.0 m；
#   井径 0.5 m 构造档）；系数不落本表——停留带/水深带/井径带/超高/
#   壁厚系数/高程水损共 9 键全经 factor.jishuijing.*（裸短名——
#   app._unit_params 剥 conveyance_ 前缀投影，M3a1 期四线预置零改造）；
#   removal_refs 全空（穿流单元零 removal 键——manifest 声明面注记，
#   removal_rates.yaml 0.7.0 零新增口径，照 M3b1 污泥批先例）。
# 【公式注册（D1）】JS-F1~JS-F7 逐条 FormulaSpec+register；expression=
#   表公式串逐字；π=3.14159265 内联截断常量、60 为 min→s 换算常量、
#   4 为圆面积-直径换算常量（表串原文常量，本文件=units_lib manifest
#   白名单区）；无构造档取整进 DSL——井径 0.5 m 档 ceil 在 compute 收口。
# 【流量口径】容积/停留按最高时 flow.q_design（表头流量口径节逐字）；
#   出流=入流双量透传（穿流守恒——不经公式面，compute 直通）。
# 【声明五件】params（t_well/h_well 两参数带=factor 带键逐字；
#   dia_disc_step 构造档）/ports 两口 WATER/removal_refs 空映射/
#   norm_refs 双源标记（GB 50014-2021 §6.1 参照+§6 超高+手册第 5 册）/
#   condition_mappings=()/constraint_refs 三键（t_band/depth_band/d_band）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "conveyance_jishuijing"

_GB61 = (
    "GB 50014-2021 §6.1（泵站集水池容积参照口径——汇流无泵工况，"
    "条号随追认核对；docs/norms/conveyance_jishuijing.md 起草表"
    " 2026-08-27，待追认）"
)
_GB6 = (
    "GB 50014-2021 §6（超高一般要求，条号随追认核对；"
    "docs/norms/conveyance_jishuijing.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施有效"
    "容积/有效水深/停留常用带；docs/norms/conveyance_jishuijing.md"
    " 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_T = DimKey.TIME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "JS-F1",
        "v_well = q_design * 60 * t_well",
        {
            "q_design": (_F, "最高时设计流量 m3/s（入流 flow.q_design）"),
            "t_well": (_D, "汇流停留时间 min（参数 t_well，×60 折 s 入式）"),
        },
        _VOL,
        f"{_GB61}；{_HB}",
    ),
    FormulaSpec(
        "JS-F2",
        "a_well = v_well / h_well",
        {
            "v_well": (_VOL, "汇流集水有效容积 m3（JS-F1）"),
            "h_well": (_L, "集水井有效水深 m（参数 h_well）"),
        },
        _A,
        _HB,
    ),
    FormulaSpec(
        "JS-F3",
        "d_raw = sqrt(4 * a_well / 3.14159265)",
        {
            "a_well": (_A, "需要井平面面积 m2（JS-F2）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "JS-F4",
        "a_act = 3.14159265 * d ** 2 / 4",
        {
            "d": (_L, "井径离散档值 m（ceil(d_raw, dia_disc_step)——compute 收口）"),
        },
        _A,
        _HB,
    ),
    FormulaSpec(
        "JS-F5",
        "t_act = a_act * h_well / q_design",
        {
            "a_act": (_A, "实际井平面面积 m2（JS-F4）"),
            "h_well": (_L, "集水井有效水深 m"),
            "q_design": (_F, "最高时设计流量 m3/s"),
        },
        _T,
        _HB,
    ),
    FormulaSpec(
        "JS-F6",
        "h_total = h_super + h_well",
        {
            "h_super": (_D, "井超高 m（factor.jishuijing.superheight）"),
            "h_well": (_L, "集水井有效水深 m"),
        },
        _L,
        f"{_GB6}；{_HB}",
    ),
    FormulaSpec(
        "JS-F7",
        "v_concrete = a_act * h_total * wall_coef",
        {
            "a_act": (_A, "实际井平面面积 m2（JS-F4）"),
            "h_total": (_L, "井总深 m（JS-F6）"),
            "wall_coef": (_D, "壁厚系数（factor.jishuijing.wall_thickness_coef）"),
        },
        _VOL,
        f"{_HB}（概算口径——wushui_tisheng TS-F14 同式）",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.conveyance_jishuijing",
        "version": "1.0",
        "business_line": "conveyance",
        # 默认值=表主算例逐字（出处 docs/norms/conveyance_jishuijing.md
        # 参数档）；t_well/h_well 带=factor 同名带键逐字（range 面），
        # dia_disc_step=井径 0.5 m 构造档（nongsuo/xiaohua 同键先例）
        "params": [
            {
                "field_id": "t_well",
                "dim": "DIMENSIONLESS",
                "default": 5.0,
                "range": {"min": 2.0, "max": 10.0},
            },
            {
                "field_id": "h_well",
                "dim": "LENGTH",
                "default": 3.0,
                "range": {"min": 2.0, "max": 4.0},
            },
            {"field_id": "dia_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        # 集水类=汇流单出流：in 口多股经图入边汇流（propagate 合并面），
        # out 口穿流透传（零去除——水量/水质双透传）
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        # 穿流单元无水质去除概念——removal_refs 恒空（水量/水质全透传，
        # removal_rates.yaml 0.7.0 零新增；M3c 变更记录注记在册）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §6.1（泵站集水池容积参照口径——条号随追认核对）",
            "GB 50014-2021 §6（超高一般要求，条号随追认核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施常用带）",
            "docs/norms/conveyance_jishuijing.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "conveyance_jishuijing.t_band",
            "conveyance_jishuijing.depth_band",
            "conveyance_jishuijing.d_band",
        ],
    }
)
