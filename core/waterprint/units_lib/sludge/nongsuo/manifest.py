"""污泥浓缩清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_nongsuo.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.nongsuo.* 裸短名 12 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ NS-F1~NS-F12 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_nongsuo"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（q_solid=50 固体负荷带中值/
#   t_thicken=16 h/h_eff=4.0 m/n=2 池/p_out=0.96 底流含水率/h_cone=
#   2.0 m 锥底构造默认）；系数不落本表——固体负荷带/浓缩时间带/
#   有效水深带/底流含水率带/截留率/超高/壁厚/高程水损共 12 键全经
#   factor.nongsuo.*（裸短名投影）；removal_refs 全空（上清液带出
#   DS 走泥量链不走水质去除键——0.6.0 注记在册）。
# 【公式注册（D1）】NS-F1~NS-F12 逐条 FormulaSpec+register；expression=
#   表公式串逐字（双主线取大 max 为 DSL 白名单函数——erchunchi 表
#   先例同款）；表串内联 3.14159265 经符号 pi 绑 math.pi、1000 为
#   mg-L/kg-m³ 换算常量。
# 【DSL 收口】池径 0.5 m 档向上取整不入 DSL（SIDE_DISC_STEP 模块
#   常量——本文件=数值白名单区，compute 收口 ceil）。
# 【回流口（Q1 未裁）】ports 三口：in/out SLUDGE 常规 + sup 上清液
#   出流口 recycle=True 声明先行（默认关=边不连——business-logic
#   §6 口径，UF-11 Ruling ②；打开后泥量/水量双向守恒入图迭代归
#   追认批，本实装 sup 口不产股、量走 dims q_sup/ds_sup 回显）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d；出入流
#   SludgeFlow 契约口径——SECS_PER_DAY 模块常量由 compute 消费。
# 【声明五件】params（q_solid/t_thicken/h_eff/p_out 四参数带=同名
#   factor 带键逐字；n 池数 grid [2,3,4]——旧 1~4 下限抬 2 构造冗余
#   口径[表交叉对照行]；h_cone 构造默认无带不设）/ports 三口 SLUDGE
#   （sup 带 recycle 标记）/removal_refs 空/norm_refs 双源标记/
#   condition_mappings=()/constraint_refs 四键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_nongsuo"

_GB = (
    "GB 50014-2021 §8（污泥章——重力浓缩固体负荷/浓缩时间/有效水深，"
    "旧 mod 引 §8.2.1 口径待核对；docs/norms/sludge_nongsuo.md 起草表"
    " 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥浓缩章（底流含固/"
    "固体截留率/圆形池构造常用带；docs/norms/sludge_nongsuo.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）与构造档
# 步长（池径 0.5 m 档向上取整——表公式表头注记口径；manifest=数值
# 白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0
SIDE_DISC_STEP: Final[float] = 0.5

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "NS-F1",
        "a_load = ds_in / q_solid",
        {
            "ds_in": (_D, "入流干固体量 kg/d（bengzhan 出流实值）"),
            "q_solid": (_D, "固体负荷 kgDS/(m²·d)（参数 q_solid）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "NS-F2",
        "a_time = q_wet * t_thicken / (24 * h_eff)",
        {
            "q_wet": (_D, "入流湿泥量 m³/d"),
            "t_thicken": (_D, "浓缩时间 h（参数 t_thicken）"),
            "h_eff": (_D, "有效水深 m（参数 h_eff）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "NS-F3",
        "a_req = max(a_load, a_time)",
        {
            "a_load": (_D, "固体通量主线需要面积 m²（NS-F1）"),
            "a_time": (_D, "浓缩时间主线需要面积 m²（NS-F2）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F4",
        "a_single = a_req / n",
        {
            "a_req": (_D, "需要面积全厂 m²（NS-F3 取大）"),
            "n": (_D, "池数（参数 n，≥2）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F5",
        "d_raw = sqrt(4 * a_single / pi)",
        {
            "a_single": (_D, "单池面积 m²（NS-F4）"),
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F6",
        "q_solid_act = ds_in / a_req",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "a_req": (_D, "需要面积全厂 m²（NS-F3）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "NS-F7",
        "ds_out = ds_in * eta_capture",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "eta_capture": (_D, "固体截留率（factor.nongsuo.eta_capture）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F8",
        "q_thick = ds_out / ((1 - p_out) * 1000)",
        {
            "ds_out": (_D, "底流干固体量 kg/d（NS-F7 截留）"),
            "p_out": (_D, "底流含水率（参数 p_out）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F9",
        "q_sup = q_wet - q_thick",
        {
            "q_wet": (_D, "入流湿泥量 m³/d"),
            "q_thick": (_D, "底流浓缩污泥量 m³/d（NS-F8）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F10",
        "ds_sup = ds_in - ds_out",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "ds_out": (_D, "底流干固体量 kg/d（NS-F7）"),
        },
        _D,
        "contracts.sludge R1（DS 守恒闭合：ds_in=ds_out+ds_sup）",
    ),
    FormulaSpec(
        "NS-F11",
        "h_total = h_super + h_eff + h_cone",
        {
            "h_super": (_D, "超高 m（factor.nongsuo.superheight）"),
            "h_eff": (_D, "有效水深 m（参数 h_eff）"),
            "h_cone": (_D, "锥底高 m（参数 h_cone，构造默认 2.0）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "NS-F12",
        "v_concrete = a_single * h_total * wall_coef * n",
        {
            "a_single": (_D, "单池面积 m²（NS-F4）"),
            "h_total": (_D, "池总高 m（NS-F11）"),
            "wall_coef": (_D, "壁厚系数（factor.nongsuo.wall_thickness_coef，概算口径）"),
            "n": (_D, "池数"),
        },
        _D,
        _HB5,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.sludge_nongsuo",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（出处 docs/norms/sludge_nongsuo.md 参数档）；
        # 四参数带=同名 factor 带键逐字（用户面与键面并存——ningjiao
        # h2/depth_band 先例）；n 池数 grid=旧 1~4 下限抬 2（表交叉对照
        # "≥2 grid"行——构造冗余口径）；h_cone 构造默认无出处带不设
        "params": [
            {
                "field_id": "q_solid",
                "dim": "DIMENSIONLESS",
                "default": 50.0,
                "range": {"min": 30.0, "max": 60.0},
            },
            {
                "field_id": "t_thicken",
                "dim": "DIMENSIONLESS",
                "default": 16.0,
                "range": {"min": 12.0, "max": 24.0},
            },
            {
                "field_id": "h_eff",
                "dim": "LENGTH",
                "default": 4.0,
                "range": {"min": 3.0, "max": 5.0},
            },
            {
                "field_id": "n",
                "dim": "DIMENSIONLESS",
                "default": 2.0,
                "grid": [2.0, 3.0, 4.0],
            },
            {
                "field_id": "p_out",
                "dim": "DIMENSIONLESS",
                "default": 0.96,
                "range": {"min": 0.95, "max": 0.98},
            },
            {"field_id": "h_cone", "dim": "LENGTH", "default": 2.0},
        ],
        # 三口 SLUDGE：in/out 常规 + sup 上清液回流口（recycle=True 声明
        # 先行——Q1 未裁默认关=边不连，business-logic §6；UF-11 Ruling ②）
        "ports": [
            {"port_id": "in", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
            {
                "port_id": "sup",
                "fluid": "SLUDGE",
                "direction": "OUT",
                "recycle": True,
            },
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（上清液带出 DS
        # 走泥量链 NS-F9/F10，不走水质去除键；0.6.0 零新增口径）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §8（污泥章——重力浓缩固体负荷/浓缩时间/有效水深；条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥浓缩章"
            "（底流含固/固体截留率/圆形池构造常用带）",
            "docs/norms/sludge_nongsuo.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_nongsuo.solid_load_band",
            "sludge_nongsuo.time_band",
            "sludge_nongsuo.depth_band",
            "sludge_nongsuo.moisture_out_band",
        ],
    }
)
