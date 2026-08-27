"""污泥脱水清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_tuoshui.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.tuoshui.* 裸短名 8 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ TU-F1~TU-F8 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_tuoshui"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（machine_type=1 带式主线档
#   [双机档离散枚举面——executor 参数面只收数值的契约约束下，
#   equip_type belt/centrifuge 的 float 化：1=belt 2=centrifuge，
#   grid [1,2]]；dose_pam=4 g/kgDS 带式档；p_cake=0.78 带式主线；
#   n_standby=1 备用台）；系数不落本表——泥饼含水率带/PAM 带/
#   回收率/带式·离心单机容量/高程水损共 8 键全经 factor.tuoshui.*
#   （裸短名投影）；removal_refs 全空（滤液带出 DS 走泥量链）。
# 【公式注册（D1）】TU-F1~TU-F8 逐条 FormulaSpec+register；expression=
#   表公式串逐字（DS 守恒回收链 TU-F5~F8——泥饼/滤液分流闭合）；
#   1000 为 g/kg→kg/t 换算常量（表串原文）。
# 【DSL 收口】脱水机台数整台向上取整（≥1）不入 DSL（n_machine_duty
#   由 compute 收口 ceil 后作下游公式输入符号）。
# 【双机档键选】TU-F3 的 q_machine 按 machine_type 选键绑定（1=belt
#   →factor.tuoshui.machine.belt_capacity；2=centrifuge→machine.
#   centrifuge_capacity——MACHINE_BELT/MACHINE_CENTRIFUGE 模块常量）。
# 【回流口（Q1 未裁）】ports 三口：in/out SLUDGE 常规 + filtrate 滤液
#   出流口 recycle=True 声明先行（默认关=边不连——business-logic §6
#   口径；UF-11 Ruling ②；本实装 filtrate 口不产股、量走 dims
#   q_filtrate/ds_filtrate 回显）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d；出入流
#   SludgeFlow 契约口径——SECS_PER_DAY 模块常量由 compute 消费。
# 【声明五件】params（dose_pam/p_cake 两参数带=同名 factor 带键逐字；
#   machine_type grid [1,2] 机档枚举；n_standby 无带不设）/ports 三
#   口 SLUDGE（filtrate 带 recycle 标记）/removal_refs 空/norm_refs
#   双源标记/condition_mappings=()/constraint_refs 两键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_tuoshui"

_GB = (
    "GB 50014-2021 §8（污泥章——机械脱水泥饼含水率/PAM 投加，条号待"
    "核对；docs/norms/sludge_tuoshui.md 起草表 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥脱水章"
    "（带式/离心机型档/固体回收率/加药量常用带；"
    "docs/norms/sludge_tuoshui.md 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）与双机档
# 数值枚举（表"衔接参数"equip_type belt/centrifuge 的 float 化——
# executor 参数面只收数值[bool 拒/float 归一]的契约约束下唯一形态；
# manifest=数值白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0
MACHINE_BELT: Final[float] = 1.0
MACHINE_CENTRIFUGE: Final[float] = 2.0

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "TU-F1",
        "w_pam = ds_in * dose_pam / 1000",
        {
            "ds_in": (_D, "入流干固体量 kg/d（xiaohua 出流实值）"),
            "dose_pam": (_D, "PAM 投加量 g/kgDS（参数 dose_pam）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "TU-F2",
        "q_in_h = q_wet / 24",
        {"q_wet": (_D, "入流湿泥量 m³/d（24 h 连续进泥）")},
        _D,
        _HB5,
    ),
    FormulaSpec(
        "TU-F3",
        "n_machine_raw = q_in_h / q_machine",
        {
            "q_in_h": (_D, "进泥时流量 m³/h（TU-F2）"),
            "q_machine": (
                _D,
                "单机处理量 m³/h（机型档键——belt_capacity/centrifuge_capacity）",
            ),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "TU-F4",
        "n_machine_total = n_machine_duty + n_standby",
        {
            "n_machine_duty": (_D, "工作台数（n_machine_raw 整台向上取整 ≥1）"),
            "n_standby": (_D, "备用台数（参数 n_standby，1 备档）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "TU-F5",
        "ds_cake = ds_in * eta_capture",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "eta_capture": (_D, "固体回收率（factor.tuoshui.eta_capture）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "TU-F6",
        "q_cake = ds_cake / ((1 - p_cake) * 1000)",
        {
            "ds_cake": (_D, "泥饼干固体量 kg/d（TU-F5 回收）"),
            "p_cake": (_D, "泥饼含水率（参数 p_cake）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "TU-F7",
        "q_filtrate = q_wet - q_cake",
        {
            "q_wet": (_D, "入流湿泥量 m³/d"),
            "q_cake": (_D, "泥饼量 m³/d（TU-F6）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "TU-F8",
        "ds_filtrate = ds_in - ds_cake",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "ds_cake": (_D, "泥饼干固体量 kg/d（TU-F5）"),
        },
        _D,
        "contracts.sludge R1（DS 守恒闭合：ds_in=ds_cake+ds_filtrate）",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.sludge_tuoshui",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（带式主线档；出处 docs/norms/sludge_tuoshui.md
        # 参数档）；dose_pam/p_cake 两参数带=同名 factor 带键逐字；
        # machine_type grid=双机档离散枚举（1 带式/2 离心）
        "params": [
            {
                "field_id": "machine_type",
                "dim": "DIMENSIONLESS",
                "default": 1.0,
                "grid": [1.0, 2.0],
            },
            {
                "field_id": "dose_pam",
                "dim": "DIMENSIONLESS",
                "default": 4.0,
                "range": {"min": 2.0, "max": 8.0},
            },
            {
                "field_id": "p_cake",
                "dim": "DIMENSIONLESS",
                "default": 0.78,
                "range": {"min": 0.75, "max": 0.8},
            },
            {"field_id": "n_standby", "dim": "DIMENSIONLESS", "default": 1.0},
        ],
        # 三口 SLUDGE：in/out 常规 + filtrate 滤液回流口（recycle=True
        # 声明先行——Q1 未裁默认关=边不连，business-logic §6；UF-11 ②）
        "ports": [
            {"port_id": "in", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
            {
                "port_id": "filtrate",
                "fluid": "SLUDGE",
                "direction": "OUT",
                "recycle": True,
            },
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（滤液带出 DS 走
        # 泥量链 TU-F7/F8，不走水质去除键；0.6.0 零新增口径）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §8（污泥章——机械脱水泥饼含水率/PAM 投加；条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥脱水章"
            "（带式/离心机型档/固体回收率/加药量常用带）",
            "docs/norms/sludge_tuoshui.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_tuoshui.cake_moisture_band",
            "sludge_tuoshui.dose_pam_band",
        ],
    }
)
