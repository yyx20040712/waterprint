"""高密沉淀清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_gaomidu.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KG-F1~F10 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a3 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_gaomidu"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=2 池/t_mix=0.5 min/t_floc=
#   12.0 min/q_surf=6.0 m³/(m²·h)；l_tube=1.0 m 倾角 60°/h_clear=1.0/
#   h_dist=1.5/h_thick=0.5 构造区高；B/L 0.5 m 档）；系数不落本表——
#   液面负荷带（低负荷 5~8 档）+快混/絮凝停留双带+长宽比+轴向流速
#   上限+超高+壁厚系数+高程水损全部经 factor.mine_gaomidu.* 键消费
#   （app._unit_params 线感知投影，mine_ 限定）；去除率经
#   removal.mine_gaomidu.{ss,cod}.mod_default 键（ss 0.90/cod 0.30
#   低浓度进水保安段——磁分离段已载大部分 SS，本单元为保安沉淀段；
#   BOD5 全线不建键）。
# 【公式注册（D1）】KG-F1~F10 逐条 FormulaSpec+register；expression=
#   表公式串转受限 DSL——data 包系数（ratio_lb/h_super/wall_coef）一律
#   符号绑定（零系数字面量）；结构常数内联（本文件=units_lib manifest
#   白名单区）：×3600（m3/s→m³/h 流量口径注记——表内 q_design_h 展开
#   内联）/÷60（min→h）/sin60°=0.86602540（斜管倾角 60° 构造常量，
#   表串原文直书 KG-F8/KG-F9 两处）；sqrt 直接用。DSL 无 ceil：B/L
#   （0.5 m 档）离散在 compute 收口（步长=参数，取整前 b_raw/l_raw
#   审计面）。
# 【无回流主线】与市政同名包 municipal/gaomidu（ADR-008 ③ Densadeg
#   污泥回流型，含 r_sludge/q_return 回流链 GM-F11）零 import 零参数
#   复用——本表无污泥回流键族（泥渣直接外排：磁分离段已载泥回流失效，
#   表边界差异节），键空间经 mine_ 限定物理隔离（§14.3）。
# 【声明五件】params（range 仅表内有出处带者：t_mix/t_floc/q_surf
#   三有出处带者；池数/斜管长/三构造区高/取整档无范围来源不设）/
#   ports 两口 WATER/removal_refs 双指标键/norm_refs 双源标记
#   （GB/T 41019-2021+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 五键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_gaomidu"

_GB = (
    "GB/T 41019-2021（矿井水处理工艺——混凝沉淀负荷，条号待核对；"
    "docs/norms/mine_water_gaomidu.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 3 册 城镇给水）》斜管沉淀池轴向流速/"
    "构造常用带（docs/norms/mine_water_gaomidu.md 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KG-F1",
        "q1h = q_design * 3600 / n",
        {
            "q_design": (
                _F,
                "最高时设计流量 m3/s（×3600 转 m³/h 口径——表内 q_design_h 展开内联）",
            ),
            "n": (_D, "池数"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KG-F2",
        "v_mix = q1h * t_mix / 60",
        {
            "q1h": (_D, "单池流量 m3/h（KG-F1）"),
            "t_mix": (_D, "快速混合停留 min（参数 t_mix，÷60 折 h）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KG-F3",
        "v_floc = q1h * t_floc / 60",
        {
            "q1h": (_D, "单池流量 m3/h（KG-F1）"),
            "t_floc": (_D, "絮凝停留 min（参数 t_floc，磁絮体熟化延续）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KG-F4",
        "a_settle = q1h / q_surf",
        {
            "q1h": (_D, "单池流量 m3/h（KG-F1）"),
            "q_surf": (_D, "斜管清水区液面负荷 m3/(m2·h)（参数 q_surf，主控参数——低负荷保浊度）"),
        },
        _A,
        _GB,
    ),
    FormulaSpec(
        "KG-F5",
        "b_raw = sqrt(a_settle / ratio_lb)",
        {
            "a_settle": (_A, "沉淀面积 m2（KG-F4）"),
            "ratio_lb": (_D, "池长宽比（factor.mine_gaomidu.ratio_lb，矩形池构造常量）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KG-F6",
        "l_raw = a_settle / b",
        {
            "a_settle": (_A, "沉淀面积 m2（KG-F4）"),
            "b": (_L, "池宽（0.5 m 档 ceil 后）m"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KG-F7",
        "q_surf_act = q1h / (l * b)",
        {
            "q1h": (_D, "单池流量 m3/h（KG-F1）"),
            "l": (_L, "池长（0.5 m 档 ceil 后）m"),
            "b": (_L, "池宽（0.5 m 档 ceil 后）m"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KG-F8",
        "v_axial = q_surf / (3600 * 0.86602540)",
        {
            "q_surf": (_D, "斜管清水区液面负荷 m3/(m2·h)（参数 q_surf；÷3600 折 m³/(m²·s)）",
            ),
        },
        _V,
        _HB,
    ),
    FormulaSpec(
        "KG-F9",
        "h_total = h_super + h_clear + h_dist + h_thick + l_tube * 0.86602540",
        {
            "h_super": (_L, "超高 m（factor.mine_gaomidu.superheight）"),
            "h_clear": (_L, "清水区高 m（参数 h_clear）"),
            "h_dist": (_L, "布水区高 m（参数 h_dist）"),
            "h_thick": (_L, "浓缩泥区高 m（参数 h_thick）"),
            "l_tube": (_L, "斜管长 m（参数 l_tube，倾角 60° 投影）"),
        },
        _L,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "KG-F10",
        "v_concrete = l * b * h_total * n * wall_coef",
        {
            "l": (_L, "池长（ceil 后）m"),
            "b": (_L, "池宽（ceil 后）m"),
            "h_total": (_L, "池总高 m（KG-F9）"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.mine_gaomidu.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.mine_water_gaomidu",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_gaomidu.md 参数档）；
        # range 仅三条有出处带参数（surface_load_band 5~8 低负荷保浊度——异于
        # 市政 10~20 档、t_mix_band 0.5~2.0、t_floc_band 8~15），池数/斜管长/
        # 三构造区高/取整档无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0},
            {
                "field_id": "t_mix",
                "dim": "DIMENSIONLESS",
                "default": 0.5,
                "range": {"min": 0.5, "max": 2.0},
            },
            {
                "field_id": "t_floc",
                "dim": "DIMENSIONLESS",
                "default": 12.0,
                "range": {"min": 8.0, "max": 15.0},
            },
            {
                "field_id": "q_surf",
                "dim": "DIMENSIONLESS",
                "default": 6.0,
                "range": {"min": 5.0, "max": 8.0},
            },
            {"field_id": "l_tube", "dim": "LENGTH", "default": 1.0},
            {"field_id": "h_clear", "dim": "LENGTH", "default": 1.0},
            {"field_id": "h_dist", "dim": "LENGTH", "default": 1.5},
            {"field_id": "h_thick", "dim": "LENGTH", "default": 0.5},
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_gaomidu.ss.mod_default",
            "CODCR": "removal.mine_gaomidu.cod.mod_default",
        },
        "norm_refs": [
            "GB/T 41019-2021（矿井水处理工艺——混凝沉淀负荷，条号待核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》斜管沉淀池轴向流速/构造常用带",
            "docs/norms/mine_water_gaomidu.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_gaomidu.surface_load_band",
            "mine_water_gaomidu.surface_load_act",
            "mine_water_gaomidu.axial_velocity",
            "mine_water_gaomidu.t_mix_band",
            "mine_water_gaomidu.t_floc_band",
        ],
    }
)
