"""集配水井清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/conveyance_jipeishuijing.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.7.0 键名（factor.jipeishuijing.* 裸短名 12 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ JP-F1~JP-F9 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "conveyance_jipeishuijing"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（t_well=4 min/h_well=2.5 m/
#   n=2 路；井径 0.5 m 构造档）；系数不落本表——停留带/水深带/井径
#   带/不均匀系数+带/超高/壁厚/高程水损共 12 键全经 factor.
#   jipeishuijing.*（裸短名——app._unit_params 剥 conveyance_ 前缀
#   投影）；removal_refs 全空（穿流单元零 removal 键——manifest
#   声明面注记，removal_rates.yaml 0.7.0 零新增口径，照 M3b1 先例）。
# 【公式注册（D1）】JP-F1~JP-F9 逐条 FormulaSpec+register；expression=
#   表公式串逐字；π=3.14159265 内联截断常量、60 为 min→s 换算常量、
#   4 为圆面积-直径换算常量（表串原文常量，本文件=units_lib manifest
#   白名单区）；井径 0.5 m 档 ceil 在 compute 收口（DSL 无 ceil）。
# 【多出流口口径（表内冻结）】与 peishuijing 表同款——ports 声明单
#   OUT 口 "out"（流体/方向声明锚点）；compute 按参数 n 动态产
#   out_1~out_n 多键出流（每口 WaterFlow(q_avg_daily=入流/n, kz)+
#   水质恒等透传）——executor flows/qualities 两池按 PortRef 键化、
#   图边直接引 out_i 口（app 装配不对账边与端口声明——T6 装配对账
#   挂账在册口径）。
# 【流量口径】容积/停留/分流面按最高时 flow.q_design；出流每口按
#   平均日 q_avg_daily/n 分流（守恒：Σ口 q_avg=入流）。
# 【声明五件】params（t_well/h_well 带=range 面逐字；n grid [2,3,4]
#   ——§7.1 并联系列≥2 精神；dia_disc_step 构造档）/ports 两口
#   WATER/removal_refs 空映射/norm_refs 双源标记（GB 50014-2021
#   §6.1 参照+§6 超高+§7.1+手册第 5 册/第 3 册）/condition_mappings=()/
#   constraint_refs 三键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "conveyance_jipeishuijing"

_GB61 = (
    "GB 50014-2021 §6.1（泵站集水池容积参照口径——汇流无泵工况，"
    "条号随追认核对；docs/norms/conveyance_jipeishuijing.md 起草表"
    " 2026-08-27，待追认）"
)
_GB6 = (
    "GB 50014-2021 §6（超高一般要求，条号随追认核对；"
    "docs/norms/conveyance_jipeishuijing.md 起草表 2026-08-27，待追认）"
)
_GB71 = (
    "GB 50014-2021 §7.1（处理构筑物并联系列一般规定——条号随追认"
    "核对；docs/norms/conveyance_jipeishuijing.md 起草表 2026-08-27，"
    "待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施常用"
    "带；docs/norms/conveyance_jipeishuijing.md 起草表 2026-08-27，"
    "待追认）"
)
_HB3 = (
    "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（不均匀系数"
    "常用带；docs/norms/conveyance_jipeishuijing.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_T = DimKey.TIME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "JP-F1",
        "v_well = q_design * 60 * t_well",
        {
            "q_design": (_F, "最高时设计流量 m3/s（入流 flow.q_design）"),
            "t_well": (_D, "汇流停留时间 min（参数 t_well，×60 折 s 入式）"),
        },
        _VOL,
        f"{_GB61}；{_HB5}",
    ),
    FormulaSpec(
        "JP-F2",
        "a_well = v_well / h_well",
        {
            "v_well": (_VOL, "汇流集水有效容积 m3（JP-F1）"),
            "h_well": (_L, "集配水井有效水深 m（参数 h_well）"),
        },
        _A,
        _HB5,
    ),
    FormulaSpec(
        "JP-F3",
        "d_raw = sqrt(4 * a_well / 3.14159265)",
        {
            "a_well": (_A, "需要井平面面积 m2（JP-F2）"),
        },
        _L,
        _HB5,
    ),
    FormulaSpec(
        "JP-F4",
        "a_act = 3.14159265 * d ** 2 / 4",
        {
            "d": (_L, "井径离散档值 m（ceil(d_raw, dia_disc_step)——compute 收口）"),
        },
        _A,
        _HB5,
    ),
    FormulaSpec(
        "JP-F5",
        "t_act = a_act * h_well / q_design",
        {
            "a_act": (_A, "实际井平面面积 m2（JP-F4）"),
            "h_well": (_L, "集配水井有效水深 m"),
            "q_design": (_F, "最高时设计流量 m3/s"),
        },
        _T,
        _HB5,
    ),
    FormulaSpec(
        "JP-F6",
        "q_each = q_design / n",
        {
            "q_design": (_F, "最高时设计流量 m3/s"),
            "n": (_D, "出流口数/并联系列数（参数 n，grid [2,3,4]）"),
        },
        _F,
        _GB71,
    ),
    FormulaSpec(
        "JP-F7",
        "q_series = q_each * k_uneven",
        {
            "q_each": (_F, "每路分配流量 m3/s（JP-F6）"),
            "k_uneven": (_D, "配水不均匀系数（factor.jipeishuijing.k_uneven）"),
        },
        _F,
        f"{_GB71}；{_HB3}",
    ),
    FormulaSpec(
        "JP-F8",
        "h_total = h_super + h_well",
        {
            "h_super": (_D, "井超高 m（factor.jipeishuijing.superheight）"),
            "h_well": (_L, "集配水井有效水深 m"),
        },
        _L,
        f"{_GB6}；{_HB5}",
    ),
    FormulaSpec(
        "JP-F9",
        "v_concrete = a_act * h_total * wall_coef",
        {
            "a_act": (_A, "实际井平面面积 m2（JP-F4）"),
            "h_total": (_L, "井总深 m（JP-F8）"),
            "wall_coef": (_D, "壁厚系数（factor.jipeishuijing.wall_thickness_coef）"),
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
        "i18n_key": "units.conveyance_jipeishuijing",
        "version": "1.0",
        "business_line": "conveyance",
        # 默认值=表主算例逐字（出处 docs/norms/conveyance_jipeishuijing.md
        # 参数档）；t_well/h_well 带=range 面逐字（带上限区别单功能表
        # ——集配合一井分流面约束）；n=grid 档；dia_disc_step=井径
        # 0.5 m 构造档
        "params": [
            {
                "field_id": "t_well",
                "dim": "DIMENSIONLESS",
                "default": 4.0,
                "range": {"min": 3.0, "max": 10.0},
            },
            {
                "field_id": "h_well",
                "dim": "LENGTH",
                "default": 2.5,
                "range": {"min": 2.0, "max": 3.5},
            },
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2.0, 3.0, 4.0]},
            {"field_id": "dia_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        # 集配水类=汇流+动态多口：in 口多股经图入边汇流（propagate 合并
        # 面）；ports 声明单 OUT 口 "out"（声明锚点），compute 按参数 n
        # 产 out_1~out_n 多键出流（表内冻结口径——同 peishuijing 表）
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
            "GB 50014-2021 §7.1（处理构筑物并联系列一般规定——条号随追认核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》泵站章（集水设施常用带）",
            "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（不均匀系数）",
            "docs/norms/conveyance_jipeishuijing.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "conveyance_jipeishuijing.t_band",
            "conveyance_jipeishuijing.depth_band",
            "conveyance_jipeishuijing.d_band",
        ],
    }
)
