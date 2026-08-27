"""污泥干化清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_ganhua.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.ganhua.* 裸短名 8 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ GH-F1~GH-F8 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_ganhua"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（p_out=0.25 半干化档/
#   t_op=24 h 连续运行档/r_evap=8 kg/(m²·h) 蒸发强度带中值）；
#   系数不落本表——干化含水率带/蒸发潜热/热效率/蒸发强度带/
#   天然气热值/高程水损共 8 键全经 factor.ganhua.*（裸短名投影）；
#   removal_refs 全空。
# 【公式注册（D1）】GH-F1~GH-F8 逐条 FormulaSpec+register；expression=
#   表公式串逐字（蒸发水量干基差式——与旧系统湿质量差式同值异形
#   [DS 项相消，等价性追认注记]；质量守恒校核 GH-F5 差 0——
#   contracts.sludge R1 镜像）；1000 为 kg-t 换算常量（表串原文）。
# 【机档口径】method 枚举（thermal 主线/solar）v1 不进参数面
#   （executor 参数面只收数值——thermal 单线无分支；solar 档蒸发
#   速率参数归档位重定义——表交叉对照"追认点"，本批注记不建）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d（质量基 kg/d
#   与体积基 m³/d 并存——ρ≈1000 假设归 registry/assumptions 面，
#   contracts.sludge R2 同精神）；出入流 SludgeFlow 契约口径——
#   SECS_PER_DAY 模块常量由 compute 消费。
# 【声明五件】params（p_out 带=moisture_out_band 键逐字；t_op grid
#   [8,16,24]=表"8/16 h 间歇档归 grid 枚举面"逐字；r_evap 带=
#   evap_rate_band 键逐字）/ports 两口 SLUDGE/removal_refs 空/
#   norm_refs 双源标记/condition_mappings=()/constraint_refs 两键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_ganhua"

_GB = (
    "GB 50014-2021 §8（污泥章——干化/处置相关条文，条号待核对；"
    "docs/norms/sludge_ganhua.md 起草表 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥干化章（干化后含水率"
    "档/蒸发潜热近似/热效率/传热面积蒸发强度常用带；"
    "docs/norms/sludge_ganhua.md 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s——表头
# "单位换算归 M3b2 实装面"授权；manifest=数值白名单区，compute 零
# 字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "GH-F1",
        "m_in = ds_in / (1 - p_in)",
        {
            "ds_in": (_D, "入流干固体量 kg/d（tuoshui 泥饼出流实值——DS 不变）"),
            "p_in": (_D, "入流含水率（泥饼）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "GH-F2",
        "w_evap = ds_in * (p_in / (1 - p_in) - p_out / (1 - p_out))",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "p_in": (_D, "入流含水率"),
            "p_out": (_D, "干化后含水率（参数 p_out）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "GH-F3",
        "q_out = ds_in / ((1 - p_out) * 1000)",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "p_out": (_D, "干化后含水率（参数 p_out）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "GH-F4",
        "m_out = ds_in / (1 - p_out)",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "p_out": (_D, "干化后含水率（参数 p_out）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "GH-F5",
        "m_check = m_in - w_evap",
        {
            "m_in": (_D, "进泥湿质量 kg/d（GH-F1）"),
            "w_evap": (_D, "蒸发水量 kg/d（GH-F2）"),
        },
        _D,
        "contracts.sludge R1 镜像（质量守恒校核=m_out，差 0——DS 不变·水量差=蒸发量）",
    ),
    FormulaSpec(
        "GH-F6",
        "q_heat = w_evap * h_evap / eta_thermal",
        {
            "w_evap": (_D, "蒸发水量 kg/d（GH-F2）"),
            "h_evap": (_D, "蒸发潜热工程近似 kJ/kg（factor.ganhua.h_evap）"),
            "eta_thermal": (_D, "干化系统热效率（factor.ganhua.eta_thermal）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "GH-F7",
        "w_fuel = q_heat / q_cal_fuel",
        {
            "q_heat": (_D, "干化热需 kJ/d（GH-F6）"),
            "q_cal_fuel": (_D, "天然气低热值 kJ/Nm³（factor.ganhua.fuel_calorific）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "GH-F8",
        "a_dry = w_evap / (r_evap * t_op)",
        {
            "w_evap": (_D, "蒸发水量 kg/d（GH-F2）"),
            "r_evap": (_D, "传热面积蒸发强度 kg/(m²·h)（参数 r_evap）"),
            "t_op": (_D, "日运行时 h（参数 t_op，grid 8/16/24）"),
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
        "i18n_key": "units.sludge_ganhua",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（出处 docs/norms/sludge_ganhua.md 参数档）；
        # p_out/r_evap 两参数带=同名 factor 带键逐字；t_op grid=
        # 表"8/16 h 间歇档归 grid 枚举面"（24 连续档）
        "params": [
            {
                "field_id": "p_out",
                "dim": "DIMENSIONLESS",
                "default": 0.25,
                "range": {"min": 0.2, "max": 0.4},
            },
            {
                "field_id": "t_op",
                "dim": "DIMENSIONLESS",
                "default": 24.0,
                "grid": [8.0, 16.0, 24.0],
            },
            {
                "field_id": "r_evap",
                "dim": "DIMENSIONLESS",
                "default": 8.0,
                "range": {"min": 4.0, "max": 15.0},
            },
        ],
        "ports": [
            {"port_id": "in", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（0.6.0 零新增口径）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §8（污泥章——干化/处置相关条文；条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥干化章"
            "（干化后含水率档/蒸发潜热近似/热效率/传热面积蒸发强度常用带）",
            "docs/norms/sludge_ganhua.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_ganhua.moisture_out_band",
            "sludge_ganhua.evap_rate_band",
        ],
    }
)
