"""配水渠清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/conveyance_peishuiqu.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.7.0 键名（factor.peishuiqu.* 裸短名 12 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ PQ-F1~PQ-F7 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3c 实装：M3 数据前置批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "conveyance_peishuiqu"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=2 路/b_channel=1.2 m 渠宽/
#   v_channel=0.8 m/s 渠内流速/b=2.0 m 每系列堰长）；系数不落本表
#   ——渠内/渠末流速带/堰流量系数/堰顶水头带/不均匀系数+带/超高/
#   高程水损共 12 键全经 factor.peishuiqu.*（裸短名——app._unit_params
#   剥 conveyance_ 前缀投影）；removal_refs 全空（穿流单元零 removal
#   键——manifest 声明面注记，removal_rates.yaml 0.7.0 零新增口径，
#   照 M3b1 污泥批先例）；无 wall_thickness_coef（渠道无井体概算面
#   ——渠长归布置面，shusong 管道单元不建概算键同口径）。
# 【公式注册（D1）】PQ-F1~PQ-F7 逐条 FormulaSpec+register；expression=
#   表公式串逐字；2/3 次幂内联 0.66666667（xiaohua 0.33333333 立方根
#   指数同款先例——表期望值按该截断指数手算）、2 为动能/√(2g) 常量
#   （表串原文常量，本文件=units_lib manifest 白名单区）；
#   g_gravity=9.81 m/s² 为参数（chenshachi M1A 同键先例）。
# 【多出流口口径（表内冻结）】与 peishuijing 表同款——ports 声明单
#   OUT 口 "out"（流体/方向声明锚点）；compute 按参数 n 动态产
#   out_1~out_n 多键出流（每口 WaterFlow(q_avg_daily=入流/n, kz)+
#   水质恒等透传）——executor flows/qualities 两池按 PortRef 键化、
#   图边直接引 out_i 口（app 装配不对账边与端口声明——T6 装配对账
#   挂账在册口径）。
# 【流量口径】断面/堰水力面按最高时 flow.q_design；出流每口按平均日
#   q_avg_daily/n 分流（守恒：Σ口 q_avg=入流）。
# 【声明五件】params（n grid [2,3,4]——§7.1 并联系列≥2 精神；
#   b_channel/v_channel/b 带=range 面逐字；g_gravity 构造承载）/
#   ports 两口 WATER/removal_refs 空映射/norm_refs 双源标记
#   （GB 50014-2021 §4 渠道流速/超高+§7.1+手册第 3 册）/
#   condition_mappings=()/constraint_refs 三键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "conveyance_peishuiqu"

_GB4 = (
    "GB 50014-2021 §4（排水管渠——渠道设计流速/超高，条号随追认核对；"
    "docs/norms/conveyance_peishuiqu.md 起草表 2026-08-27，待追认）"
)
_GB4V = (
    "GB 50014-2021 §4（最小流速防淤积，条号随追认核对；"
    "docs/norms/conveyance_peishuiqu.md 起草表 2026-08-27，待追认）"
)
_GB71 = (
    "GB 50014-2021 §7.1（处理构筑物并联系列一般规定——条号随追认"
    "核对；docs/norms/conveyance_peishuiqu.md 起草表 2026-08-27，"
    "待追认）"
)
_HB3 = (
    "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（矩形渠道/"
    "薄壁堰/不均匀系数常用带；docs/norms/conveyance_peishuiqu.md"
    " 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_V = DimKey.VELOCITY
_A = DimKey.AREA

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "PQ-F1",
        "q_each = q_design / n",
        {
            "q_design": (_F, "最高时设计流量 m3/s（入流 flow.q_design）"),
            "n": (_D, "出流口数/并联系列数（参数 n，grid [2,3,4]）"),
        },
        _F,
        _GB71,
    ),
    FormulaSpec(
        "PQ-F2",
        "a_channel = q_design / v_channel",
        {
            "q_design": (_F, "最高时设计流量 m3/s"),
            "v_channel": (_V, "渠内设计流速 m/s（参数 v_channel）"),
        },
        _A,
        f"{_GB4}；{_HB3}",
    ),
    FormulaSpec(
        "PQ-F3",
        "h_water = a_channel / b_channel",
        {
            "a_channel": (_A, "渠道需要过流断面 m2（PQ-F2）"),
            "b_channel": (_L, "渠宽 m（参数 b_channel，矩形断面）"),
        },
        _L,
        _HB3,
    ),
    FormulaSpec(
        "PQ-F4",
        "h_weir = (q_each / (m_weir * b * sqrt(2 * g_gravity))) ** 0.66666667",
        {
            "q_each": (_F, "每路分配流量 m3/s（PQ-F1）"),
            "m_weir": (_D, "堰流量系数 m（factor.peishuiqu.m_weir）"),
            "b": (_L, "每系列堰长 m（参数 b）"),
            "g_gravity": (_D, "重力加速度 m/s2（参数 g_gravity=9.81）"),
        },
        _L,
        _HB3,
    ),
    FormulaSpec(
        "PQ-F5",
        "q_series = q_each * k_uneven",
        {
            "q_each": (_F, "每路分配流量 m3/s（PQ-F1）"),
            "k_uneven": (_D, "配水不均匀系数（factor.peishuiqu.k_uneven）"),
        },
        _F,
        f"{_GB71}；{_HB3}",
    ),
    FormulaSpec(
        "PQ-F6",
        "h_total = h_super + h_water",
        {
            "h_super": (_D, "渠道超高 m（factor.peishuiqu.superheight）"),
            "h_water": (_L, "渠内水深 m（PQ-F3）"),
        },
        _L,
        f"{_GB4}；{_HB3}",
    ),
    FormulaSpec(
        "PQ-F7",
        "v_end = q_each / a_channel",
        {
            "q_each": (_F, "每路分配流量 m3/s（PQ-F1）"),
            "a_channel": (_A, "渠道过流断面 m2（PQ-F2）"),
        },
        _V,
        _GB4V,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.conveyance_peishuiqu",
        "version": "1.0",
        "business_line": "conveyance",
        # 默认值=表主算例逐字（出处 docs/norms/conveyance_peishuiqu.md
        # 参数档）；n=grid 档（§7.1 并联系列≥2 精神）；b_channel/
        # v_channel/b 带=range 面逐字；g_gravity=物理常数参数承载
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2.0, 3.0, 4.0]},
            {
                "field_id": "b_channel",
                "dim": "LENGTH",
                "default": 1.2,
                "range": {"min": 0.8, "max": 2.0},
            },
            {
                "field_id": "v_channel",
                "dim": "VELOCITY",
                "default": 0.8,
                "range": {"min": 0.6, "max": 1.0},
            },
            {
                "field_id": "b",
                "dim": "LENGTH",
                "default": 2.0,
                "range": {"min": 1.5, "max": 3.0},
            },
            {"field_id": "g_gravity", "dim": "DIMENSIONLESS", "default": 9.81},
        ],
        # 配水渠=动态多口：ports 声明单 OUT 口 "out"（流体/方向声明锚点），
        # compute 按参数 n 产 out_1~out_n 多键出流（表内冻结口径——
        # 与 peishuijing 表同款）
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        # 穿流单元无水质去除概念——removal_refs 恒空（水量/水质全透传，
        # removal_rates.yaml 0.7.0 零新增；M3c 变更记录注记在册）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §4（排水管渠——渠道设计流速/超高，条号随追认核对）",
            "GB 50014-2021 §4（最小流速防淤积，条号随追认核对）",
            "GB 50014-2021 §7.1（处理构筑物并联系列一般规定——条号随追认核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》配水设施章（矩形渠道/薄壁堰/不均匀系数）",
            "docs/norms/conveyance_peishuiqu.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "conveyance_peishuiqu.v_channel_band",
            "conveyance_peishuiqu.h_weir_band",
            "conveyance_peishuiqu.v_end_band",
        ],
    }
)
