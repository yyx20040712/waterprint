"""污泥泵站清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_bengzhan.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.bengzhan.* 裸短名 17 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ BZ-F1~BZ-F18 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_bengzhan"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n_standby=1 备用 1 台/
#   h_static=10.0 m 静扬程[8~15 常用带中值]/l_pipe=100 m 出泥管长/
#   v_pipe=1.5 m/s 名义流速/v… 参数面六键——dimensions 登记全复用
#   M2C wushui_tisheng 泵族字段[零新增登记]）；系数不落本表——泵组
#   锚/单泵流量带/自由水头/启停上限/出泥管流速带/局部损失/沿程 λ/
#   污泥粘度修正/集泥井时间水深双带/超高/壁厚/高程水损共 17 键全经
#   factor.bengzhan.*（裸短名投影）；removal_refs 全空。
# 【公式注册（D1）】BZ-F1~BZ-F18 逐条 FormulaSpec+register；expression=
#   表公式串逐字（wushui_tisheng 泵族先例形态——扬程三分量[静+管损+
#   自由水头]、比阻表改 λ 式[污泥管 DN50~DN200 细管档]）；表串内联
#   3.14159265 经符号 pi 绑 math.pi、9.81/900/3600 为表串原文常量
#   （900=3600/4 启停周期条文常量，TS-F12 同源）。
# 【DSL 收口】泵台数整台向上取整与管径 0.025 m 档（DN25 步进）不入
#   DSL（n_pump_duty/d_pipe 由 compute 收口 ceil 后作下游公式输入
#   符号——PIPE_DISC_STEP 模块常量）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d；出入流
#   SludgeFlow 契约口径——SECS_PER_DAY 模块常量由 compute 消费。
# 【声明五件】params（t_well/h_well 双带与 v_pipe 流速带有出处带设
#   range；n_standby/h_static/l_pipe 无带不设）/ports 两口 SLUDGE/
#   removal_refs 空/norm_refs 双源标记/condition_mappings=()/
#   constraint_refs 五键（单泵流量带/出泥管流速带/启停上限/集泥井
#   时间带/水深带）。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_bengzhan"

_GB = (
    "GB 50014-2021 §6.1（泵站集水池容积/备用泵一般要求）与 §8（污泥章"
    "——污泥管道流速/泵扬程，条号待核对；docs/norms/sludge_bengzhan.md"
    " 起草表 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥泵站章（泵组选型/"
    "集泥井/管路损失常用值；docs/norms/sludge_bengzhan.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）与构造档
# 步长（出泥管径 DN25=0.025 m 档向上取整——表公式表头注记口径；
# manifest=数值白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0
PIPE_DISC_STEP: Final[float] = 0.025

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "BZ-F1",
        "q_h = q_wet / 24",
        {"q_wet": (_D, "泵站入流 m³/d（shusong 出流实值，24 h 连续提升）")},
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F2",
        "n_pump_raw = q_h / q_per_pump",
        {
            "q_h": (_D, "时入流量 m³/h（BZ-F1）"),
            "q_per_pump": (_D, "单泵流量概算锚 m³/h（factor.bengzhan.pump.q_per_unit）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F3",
        "q_pump_h = q_h / n_pump_duty",
        {
            "q_h": (_D, "时入流量 m³/h（BZ-F1）"),
            "n_pump_duty": (_D, "工作泵台数（n_pump_raw 整台向上取整）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F4",
        "q_pump_si = q_pump_h / 3600",
        {"q_pump_h": (_D, "单泵流量 m³/h（BZ-F3）")},
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F5",
        "n_total = n_pump_duty + n_standby",
        {
            "n_pump_duty": (_D, "工作泵台数（取整后）"),
            "n_standby": (_D, "备用泵台数（参数 n_standby，1 用 1 备/2 用 1 备档）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "BZ-F6",
        "d_raw = sqrt(4 * q_pump_si / (pi * v_pipe))",
        {
            "q_pump_si": (_D, "单泵秒流量 m³/s（BZ-F4）"),
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "v_pipe": (_D, "出泥管名义流速 m/s（参数 v_pipe）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "BZ-F7",
        "v_act = 4 * q_pump_si / (pi * d_pipe ** 2)",
        {
            "q_pump_si": (_D, "单泵秒流量 m³/s（BZ-F4）"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "d_pipe": (_D, "出泥管径 m（d_raw 经 0.025 m 档向上取整）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "BZ-F8",
        "h_friction = lambda_f * (l_pipe / d_pipe) * v_act ** 2 / (2 * 9.81)",
        {
            "lambda_f": (
                _D,
                "沿程阻力系数 λ（factor.bengzhan.friction_lambda——污泥管细管档 λ 式承载）",
            ),
            "l_pipe": (_D, "出泥管长 m（参数 l_pipe）"),
            "d_pipe": (_D, "出泥管径 m（取整后）"),
            "v_act": (_D, "实际流速 m/s（BZ-F7）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F9",
        "h_local = zeta_total * v_act ** 2 / (2 * 9.81)",
        {
            "zeta_total": (_D, "局部损失系数和（factor.bengzhan.pipe.zeta_total）"),
            "v_act": (_D, "实际流速 m/s（BZ-F7）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F10",
        "h_loss = (h_friction + h_local) * k_sludge",
        {
            "h_friction": (_D, "沿程损失 m（BZ-F8）"),
            "h_local": (_D, "局部损失 m（BZ-F9）"),
            "k_sludge": (_D, "污泥粘度修正系数（factor.bengzhan.k_sludge——清水水损放大）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F11",
        "h_pump = h_static + h_loss + h_free",
        {
            "h_static": (_D, "静扬程 m（参数 h_static）"),
            "h_loss": (_D, "管路损失 m（BZ-F10 污泥修正后）"),
            "h_free": (_D, "自由水头 m（factor.bengzhan.pump.free_head）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F12",
        "v_well = q_pump_si * 60 * t_well",
        {
            "q_pump_si": (_D, "最大一台泵秒流量 m³/s（BZ-F4）"),
            "t_well": (_D, "集泥井调节时间 min（参数 t_well）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "BZ-F13",
        "a_well = v_well / h_well",
        {
            "v_well": (_D, "集泥井调节容积 m³（BZ-F12）"),
            "h_well": (_D, "集泥井有效水深 m（参数 h_well）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F14",
        "n_start = 900 * q_pump_si / v_well",
        {
            "q_pump_si": (_D, "单泵秒流量 m³/s（BZ-F4）"),
            "v_well": (_D, "集泥井调节容积 m³（BZ-F12）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F15",
        "h_well_total = h_super + h_well",
        {
            "h_super": (_D, "超高 m（factor.bengzhan.superheight）"),
            "h_well": (_D, "集泥井有效水深 m（参数 h_well）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "BZ-F16",
        "v_concrete = a_well * h_well_total * wall_coef",
        {
            "a_well": (_D, "集泥井面积 m²（BZ-F13）"),
            "h_well_total": (_D, "井总高 m（BZ-F15）"),
            "wall_coef": (_D, "壁厚系数（factor.bengzhan.wall_thickness_coef，概算口径）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "BZ-F17",
        "ds_out = ds_in",
        {"ds_in": (_D, "入流干固体量 kg/d（穿流——泵送不改泥质）")},
        _D,
        "contracts.sludge R1（DS 守恒不变量——穿流显式）",
    ),
    FormulaSpec(
        "BZ-F18",
        "p_out = p_in",
        {"p_in": (_D, "入流含水率（穿流——泵送不改泥质）")},
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
        "i18n_key": "units.sludge_bengzhan",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（出处 docs/norms/sludge_bengzhan.md 参数档）；
        # t_well/h_well 双带与 v_pipe 流速带有出处带设 range（数值=表
        # 参数档逐字）；n_standby/h_static/l_pipe 无带不设
        "params": [
            {"field_id": "n_standby", "dim": "DIMENSIONLESS", "default": 1.0},
            {"field_id": "h_static", "dim": "LENGTH", "default": 10.0},
            {"field_id": "l_pipe", "dim": "LENGTH", "default": 100.0},
            {
                "field_id": "v_pipe",
                "dim": "VELOCITY",
                "default": 1.5,
                "range": {"min": 1.0, "max": 2.0},
            },
            {
                "field_id": "t_well",
                "dim": "DIMENSIONLESS",
                "default": 10.0,
                "range": {"min": 5.0, "max": 15.0},
            },
            {
                "field_id": "h_well",
                "dim": "LENGTH",
                "default": 2.0,
                "range": {"min": 1.5, "max": 2.5},
            },
        ],
        "ports": [
            {"port_id": "in", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（0.6.0 零新增口径）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §6.1（泵站集水池容积/备用泵一般要求）",
            "GB 50014-2021 §8（污泥章——污泥管道流速/泵扬程；条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥泵站章"
            "（泵组选型/集泥井/管路损失常用值）",
            "docs/norms/sludge_bengzhan.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_bengzhan.pump_q_flow_band",
            "sludge_bengzhan.pipe_velocity_band",
            "sludge_bengzhan.pump_start_band",
            "sludge_bengzhan.well_t_band",
            "sludge_bengzhan.well_depth_band",
        ],
    }
)
