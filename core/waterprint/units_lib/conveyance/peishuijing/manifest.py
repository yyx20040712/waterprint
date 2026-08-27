"""配水井清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/conveyance_peishuijing.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.7.0 键名（factor.peishuijing.* 裸短名 15 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ PJ-F1~PJ-F12 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "conveyance_peishuijing"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=2 路/v=1.0 m/s 名义出流/
#   v_channel=0.6 m/s 井室断面/h_well=2.0 m；出流口 0.1 m 档[DN 档，
#   wushui_tisheng 先例]+井径 0.5 m 档）；系数不落本表——流速带/
#   孔口 μ/水头带/不均匀系数+带/井室断面带/水深带/超高/壁厚/高程
#   水损共 15 键全经 factor.peishuijing.*（裸短名——app._unit_params
#   剥 conveyance_ 前缀投影）；removal_refs 全空（穿流单元零 removal
#   键——manifest 声明面注记，removal_rates.yaml 0.7.0 零新增口径，
#   照 M3b1 污泥批先例）。
# 【公式注册（D1）】PJ-F1~PJ-F12 逐条 FormulaSpec+register；expression=
#   表公式串逐字；π=3.14159265 内联截断常量、4 为圆面积-直径换算
#   常量、2 为动能/孔口式分母常量（表串原文常量，本文件=units_lib
#   manifest 白名单区）；出流口 0.1 m 档与井径 0.5 m 档 ceil 在
#   compute 收口（DSL 无 ceil）。g_gravity=9.81 m/s² 为参数
#   （chenshachi M1A 同键先例——物理常数入参数面承载）。
# 【多出流口口径（表内冻结）】ports 声明单 OUT 口 "out"（流体/方向
#   声明锚点）；compute 按参数 n 动态产 out_1~out_n 多键出流（每口
#   WaterFlow(q_avg_daily=入流/n, kz)+水质恒等透传）——executor
#   flows/qualities 两池按 PortRef 键化、图边直接引 out_i 口（app
#   装配不对账边与端口声明——T6 装配对账挂账在册口径）。
# 【流量口径】水力面按最高时 flow.q_design（表头流量口径节逐字）；
#   出流每口按平均日 q_avg_daily/n 分流（守恒：Σ口 q_avg=入流）。
# 【声明五件】params（n grid [2,3,4]——§7.1 并联系列≥2 精神，
#   tiaojiechi 池数档同口径；v/v_channel/h_well 带=range 面逐字；
#   g_gravity/length_disc_step/dia_disc_step 构造承载）/ports 两口
#   WATER/removal_refs 空映射/norm_refs 双源标记（GB 50014-2021
#   §7.1+§6 参照+手册第 3 册/第 5 册）/condition_mappings=()/
#   constraint_refs 四键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "conveyance_peishuijing"

_GB71 = (
    "GB 50014-2021 §7.1（处理构筑物并联系列一般规定——条号随追认"
    "核对；docs/norms/conveyance_peishuijing.md 起草表 2026-08-27，"
    "待追认）"
)
_GB6 = (
    "GB 50014-2021 §6（超高一般要求，条号随追认核对；"
    "docs/norms/conveyance_peishuijing.md 起草表 2026-08-27，待追认）"
)
_HB3 = (
    "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（孔口出流/"
    "不均匀系数常用带；docs/norms/conveyance_peishuijing.md 起草表"
    " 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施参照"
    "常用带；docs/norms/conveyance_peishuijing.md 起草表 2026-08-27，"
    "待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_V = DimKey.VELOCITY
_A = DimKey.AREA
_VOL = DimKey.VOLUME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "PJ-F1",
        "q_each = q_design / n",
        {
            "q_design": (_F, "最高时设计流量 m3/s（入流 flow.q_design）"),
            "n": (_D, "出流口数/并联系列数（参数 n，grid [2,3,4]）"),
        },
        _F,
        _GB71,
    ),
    FormulaSpec(
        "PJ-F2",
        "a_out = q_each / v_out",
        {
            "q_each": (_F, "每路分配流量 m3/s（PJ-F1）"),
            "v_out": (_V, "名义出流流速 m/s（参数 v）"),
        },
        _A,
        _HB3,
    ),
    FormulaSpec(
        "PJ-F3",
        "d_raw = sqrt(4 * a_out / 3.14159265)",
        {
            "a_out": (_A, "出流口需要面积 m2（PJ-F2）"),
        },
        _L,
        _HB3,
    ),
    FormulaSpec(
        "PJ-F4",
        "a_act = 3.14159265 * d ** 2 / 4",
        {
            "d": (_L, "出流口径离散档值 m（ceil(d_raw, length_disc_step)——compute 收口）"),
        },
        _A,
        _HB3,
    ),
    FormulaSpec(
        "PJ-F5",
        "v_act = q_each / a_act",
        {
            "q_each": (_F, "每路分配流量 m3/s（PJ-F1）"),
            "a_act": (_A, "出流口实际面积 m2（PJ-F4）"),
        },
        _V,
        _HB3,
    ),
    FormulaSpec(
        "PJ-F6",
        "h_head = v_act ** 2 / (2 * g_gravity * mu_out ** 2)",
        {
            "v_act": (_V, "实际出流流速 m/s（PJ-F5）"),
            "g_gravity": (_D, "重力加速度 m/s2（参数 g_gravity=9.81）"),
            "mu_out": (_D, "孔口流量系数 μ（factor.peishuijing.mu_out）"),
        },
        _L,
        _HB3,
    ),
    FormulaSpec(
        "PJ-F7",
        "q_series = q_each * k_uneven",
        {
            "q_each": (_F, "每路分配流量 m3/s（PJ-F1）"),
            "k_uneven": (_D, "配水不均匀系数（factor.peishuijing.k_uneven）"),
        },
        _F,
        f"{_GB71}；{_HB3}",
    ),
    FormulaSpec(
        "PJ-F8",
        "a_well = q_design / v_channel",
        {
            "q_design": (_F, "最高时设计流量 m3/s"),
            "v_channel": (_V, "井室过流断面流速 m/s（参数 v_channel）"),
        },
        _A,
        _HB5,
    ),
    FormulaSpec(
        "PJ-F9",
        "d_well_raw = sqrt(4 * a_well / 3.14159265)",
        {
            "a_well": (_A, "井室需要断面 m2（PJ-F8）"),
        },
        _L,
        _HB5,
    ),
    FormulaSpec(
        "PJ-F10",
        "a_well_act = 3.14159265 * d_well ** 2 / 4",
        {
            "d_well": (_L, "井径离散档值 m（ceil(d_well_raw, dia_disc_step)——compute 收口）"),
        },
        _A,
        _HB5,
    ),
    FormulaSpec(
        "PJ-F11",
        "h_total = h_super + h_well",
        {
            "h_super": (_D, "井超高 m（factor.peishuijing.superheight）"),
            "h_well": (_L, "配水井有效水深 m（参数 h_well）"),
        },
        _L,
        f"{_GB6}；{_HB5}",
    ),
    FormulaSpec(
        "PJ-F12",
        "v_concrete = a_well_act * h_total * wall_coef",
        {
            "a_well_act": (_A, "井室实际断面 m2（PJ-F10）"),
            "h_total": (_L, "井总深 m（PJ-F11）"),
            "wall_coef": (_D, "壁厚系数（factor.peishuijing.wall_thickness_coef）"),
        },
        _VOL,
        f"{_HB5}（概算口径）",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.conveyance_peishuijing",
        "version": "1.0",
        "business_line": "conveyance",
        # 默认值=表主算例逐字（出处 docs/norms/conveyance_peishuijing.md
        # 参数档）；n=grid 档（§7.1 并联系列≥2 精神，tiaojiechi 池数档
        # 同口径）；v/v_channel/h_well 带=range 面逐字；g_gravity=物理
        # 常数参数承载；出流口 0.1 m 档（DN 档）/井径 0.5 m 档
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2.0, 3.0, 4.0]},
            {"field_id": "v", "dim": "VELOCITY", "default": 1.0, "range": {"min": 0.8, "max": 1.5}},
            {"field_id": "g_gravity", "dim": "DIMENSIONLESS", "default": 9.81},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
            {
                "field_id": "v_channel",
                "dim": "VELOCITY",
                "default": 0.6,
                "range": {"min": 0.4, "max": 0.8},
            },
            {
                "field_id": "h_well",
                "dim": "LENGTH",
                "default": 2.0,
                "range": {"min": 1.5, "max": 2.5},
            },
            {"field_id": "dia_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        # 配水类=动态多口：ports 声明单 OUT 口 "out"（流体/方向声明锚点），
        # compute 按参数 n 产 out_1~out_n 多键出流（表内冻结口径——
        # executor 两池按 PortRef 键化，图边直接引 out_i 口）
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        # 穿流单元无水质去除概念——removal_refs 恒空（水量/水质全透传，
        # removal_rates.yaml 0.7.0 零新增；M3c 变更记录注记在册）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §7.1（处理构筑物并联系列一般规定——条号随追认核对）",
            "GB 50014-2021 §6（超高一般要求，条号随追认核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（孔口出流/不均匀系数）",
            "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施参照常用带）",
            "docs/norms/conveyance_peishuijing.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "conveyance_peishuijing.v_band",
            "conveyance_peishuijing.head_band",
            "conveyance_peishuijing.v_channel_band",
            "conveyance_peishuijing.depth_band",
        ],
    }
)
