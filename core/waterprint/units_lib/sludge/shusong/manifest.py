"""污泥输送清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_shusong.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.shusong.* 裸短名 6 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ ST-F1~ST-F9 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_shusong"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（v_press=1.5 m/s 压力流名义
#   流速、d_grav=0.15 m DN150 重力段档；副算例 v_press=2.0、d_grav=
#   0.20）；系数不落本表——压力流速带/重力最小流速/最小坡度/曼宁
#   糙率/高程水损共 6 键全经 factor.shusong.*（裸短名投影）；
#   removal_refs 全空（污泥单元零 removal 键）。
# 【公式注册（D1）】ST-F1~ST-F9 逐条 FormulaSpec+register；expression=
#   表公式串逐字（ST-F8/F9 DS/含水率穿流恒等式——contracts.sludge
#   R1 守恒显式）；表串内联 3.14159265 按模板惯例经符号 pi 绑定
#   math.pi（KI/KT/KS 先例同型，差 <1e-9 断言容差覆盖）；0.66666667
#   为曼宁 R^(2/3) 指数内联常量（表串原文）。
# 【DSL 收口】管径 0.025 m 档（DN25 步进——细管档）向上取整不入 DSL
#   （PIPE_DISC_STEP 模块常量——本文件=数值白名单区，compute 收口
#   ceil）；ST-F6 v_grav 依赖 ST-F7 i_slope，compute 求值序 F5→F7→F6
#   （每条 apply 独立，formula_ids 仍按表号全量）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d；出入流
#   SludgeFlow 契约口径 m3/s、kg/s——SECS_PER_DAY 模块常量由 compute
#   消费（入流读量 ×换算、出流写量 /换算）。
# 【声明五件】params（v_press 有 velocity_band 出处带设 range；d_grav
#   无带不设）/ports 两口 SLUDGE/removal_refs 空/norm_refs 双源标记/
#   condition_mappings=()/constraint_refs 两键（压力流速带+重力最小
#   流速）。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_shusong"

_GB = (
    "GB 50014-2021 §8（污泥章——污泥管道压力流速，条号待核对；"
    "docs/norms/sludge_shusong.md 起草表 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥管道章（输泥量/重力"
    "自流最小坡度；docs/norms/sludge_shusong.md 起草表 2026-08-27，待追认）"
)
_HB1 = (
    "《给水排水设计手册（第 1 册 常用资料）》管渠水力（曼宁糙率与满流"
    "公式；docs/norms/sludge_shusong.md 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）与构造档
# 步长（管径 DN25=0.025 m 细管档向上取整——表公式表头注记口径；
# manifest=数值白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0
PIPE_DISC_STEP: Final[float] = 0.025

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "ST-F1",
        "q_h = q_wet / 24",
        {"q_wet": (_D, "输泥量 m³/d（hebing 出流实值，24 h 连续输送）")},
        _D,
        _HB5,
    ),
    FormulaSpec(
        "ST-F2",
        "q_si = q_h / 3600",
        {"q_h": (_D, "时输泥量 m³/h（ST-F1）")},
        _D,
        _HB5,
    ),
    FormulaSpec(
        "ST-F3",
        "d_raw = sqrt(4 * q_si / (pi * v_press))",
        {
            "q_si": (_D, "秒输泥量 m³/s（ST-F2）"),
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "v_press": (_D, "压力流设计流速 m/s（参数 v_press）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "ST-F4",
        "v_act = 4 * q_si / (pi * d_pipe ** 2)",
        {
            "q_si": (_D, "秒输泥量 m³/s（ST-F2）"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "d_pipe": (_D, "压力段管径 m（d_raw 经 0.025 m 档向上取整）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "ST-F5",
        "i_req = (v_grav_min * n_manning / ((d_grav / 4) ** 0.66666667)) ** 2",
        {
            "v_grav_min": (_D, "重力流最小流速 m/s（factor.shusong.gravity_v_min）"),
            "n_manning": (_D, "曼宁糙率（factor.shusong.n_manning）"),
            "d_grav": (_D, "重力段管径 m（参数 d_grav，满流水力半径 d/4）"),
        },
        _D,
        _HB1,
    ),
    FormulaSpec(
        "ST-F6",
        "v_grav = (1 / n_manning) * ((d_grav / 4) ** 0.66666667) * sqrt(i_slope)",
        {
            "n_manning": (_D, "曼宁糙率（factor.shusong.n_manning）"),
            "d_grav": (_D, "重力段管径 m（参数 d_grav）"),
            "i_slope": (_D, "整定坡度（ST-F7 max(i_req, slope_min)）"),
        },
        _D,
        _HB1,
    ),
    FormulaSpec(
        "ST-F7",
        "i_slope = max(i_req, slope_min)",
        {
            "i_req": (_D, "满流最小坡度需求（ST-F5 曼宁反解）"),
            "slope_min": (_D, "重力输泥管最小坡度（factor.shusong.slope_min）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "ST-F8",
        "ds_out = ds_in",
        {"ds_in": (_D, "入流干固体量 kg/d（穿流——输送不改泥质）")},
        _D,
        "contracts.sludge R1（DS 守恒不变量——穿流显式）",
    ),
    FormulaSpec(
        "ST-F9",
        "p_out = p_in",
        {"p_in": (_D, "入流含水率（穿流——输送不改泥质）")},
        _D,
        "contracts.sludge R1（含水率穿流显式）",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.sludge_shusong",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（出处 docs/norms/sludge_shusong.md 参数档）；
        # v_press 带=velocity_band（1.0~2.0——表参数档双源）；d_grav 输泥管
        # 常用档（主 DN150/副 DN200）无出处带不设 range
        "params": [
            {
                "field_id": "v_press",
                "dim": "VELOCITY",
                "default": 1.5,
                "range": {"min": 1.0, "max": 2.0},
            },
            {"field_id": "d_grav", "dim": "LENGTH", "default": 0.15},
        ],
        "ports": [
            {"port_id": "in", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（0.6.0 零新增口径）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §8（污泥章——污泥管道压力流速；条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥管道章"
            "（压力流流速/重力最小坡度/管径常用带）",
            "《给水排水设计手册（第 1 册 常用资料）》管渠水力（曼宁糙率表）",
            "docs/norms/sludge_shusong.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_shusong.velocity_band",
            "sludge_shusong.gravity_v_min",
        ],
    }
)
