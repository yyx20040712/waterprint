"""旋流沉砂池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表签字真源（docs/norms/chenshachi.md，2026-08-23）+ data/coefficients 0.1.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ CS-F1~F18 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_chenshachi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 值逐字（n=2/q_surf=150/t=30/T_clean=2/
#   θ=55°/d_r=0.5/B渠=0.8/v渠=1.0/取整步长 0.1/sec_per_hour=3600[CS-F1
#   时换算系数，三表系数行]）；系数不落本表——X/安全系数/h₃/超高/含水率/
#   VS/密度/直段系数/出水渠比/四条校核带/壁厚系数全部经
#   factor.chenshachi.* 键消费（app._unit_params 投影，D4）；去除率经
#   removal.chenshachi.*.mod_default 键（NH3N/TN/TP 不建条目）。
# 【公式注册（D2）】CS-F1~F18 逐条 FormulaSpec+register；expression=三表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构常数
#   （4、2、3、3600、86400、10⁶）内联（本文件=units_lib manifest 白名单
#   区）；π 经符号 pi 绑定 math.pi；tanθ 预处理符号传入。DSL 函数名
#   （sqrt/max）M1b D4 豁免后不计入 Name 集（registry 白名单函数名剔除，
#   占位符号与 float(0) 绑定已删——治本 M1a I-2）。DSL 无 ceil：
#   池径 D/h_cyl/总高 H 的 0.1m 离散在 compute 收口（步长=length_disc_step）。
# 【norm_ref 口径】节级"GB 50014-2021 §6.4（条文号待核对原文）"；引
#   中期报告式号者（3-21/3-22/3-24/3-25/3-27/4-26~4-29）逐字保留注记
#   "中期报告 §3.3（毕业设计内部资料，待核对映射条文）"——条文级核对挂账。
# 【DSL 单输出注记】Q₁h/A渠/Q_wet/V_storage 为 F1/F14/F12 的导出量，
#   在 compute 以参数化算术合成（零字面量，无新工程常数）。
# 【矛盾 3 挂账】t=30 与校核带 25~60 s（mod.json min=30）不一致——
#   总控工程惯例裁定 2026-08-25：表载 t=30 生效（签字值优先，30 在校核
#   带内）；待领域专家追认（见 .workflow/pending-domain-expert.md §2）。
# 【档位声明（Ruling ④）】池数 n grid=[2,3,4,5,6]（GB 50014 池数≥2 精神+
#   CASS n_pool 先例档，M2-SOL §7 档位补齐，待追认）；档位下限归 grid
#   层承载，compute 只保 n>0 数学有效性。
# 【声明五件】params/ports/removal_refs/norm_refs/condition_mappings=()。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_chenshachi"

_GB = "GB 50014-2021 §6.4（条文号待核对原文；docs/norms/chenshachi.md 签字表 2026-08-23）"
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_V = DimKey.VELOCITY
_T = DimKey.TIME
_VOL = DimKey.VOLUME
_M = DimKey.MASS

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "CS-F1",
        "q1 = q_design / n",
        {"q_design": (_F, "最大设计流量 m3/s"), "n": (_D, "池数")},
        _F,
        _GB,
    ),
    FormulaSpec(
        "CS-F2",
        "d_raw = sqrt(4 * q1 * sec_per_hour / (pi * q_surf))",
        {
            "q1": (_F, "单池流量 m3/s"),
            "sec_per_hour": (_D, "时换算系数 s/h（参数 sec_per_hour）"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "q_surf": (_D, "表面负荷 m3/(m2.h)"),
        },
        _L,
        "中期报告 §3.3 式(3-21)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F3",
        "h2 = q_surf * t_retention / 3600",
        {"q_surf": (_D, "表面负荷 m3/(m2.h)"), "t_retention": (_T, "停留时间 s")},
        _L,
        "中期报告 §3.3 式(3-22)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F4",
        "ratio_dh2 = d / h2",
        {"d": (_L, "池径（ceil 后）m"), "h2": (_L, "有效水深 m")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "CS-F5",
        "v_eff = pi * (d / 2) ** 2 * h2",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "d": (_L, "池径（ceil 后）m"),
            "h2": (_L, "有效水深 m"),
        },
        _VOL,
        _GB,
    ),
    FormulaSpec(
        "CS-F6",
        "t_actual = v_eff / q1",
        {"v_eff": (_VOL, "有效容积 m3"), "q1": (_F, "单池流量 m3/s")},
        _T,
        _GB,
    ),
    FormulaSpec(
        "CS-F7",
        "v_sand = q_avg_daily * 86400 * x_sand / (n * 1000000)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s"),
            "x_sand": (_D, "沉砂量 X m3/1e6m3（factor.chenshachi.sand_yield_x）"),
            "n": (_D, "池数"),
        },
        _VOL,
        "中期报告 §3.3 式(3-24)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F8",
        "v_hopper = v_sand * t_clean * safety",
        {
            "v_sand": (_VOL, "单池日沉砂量 m3/d"),
            "t_clean": (_D, "清砂间隔 d（参数 t_clean）"),
            "safety": (_D, "砂斗容积安全系数（factor.chenshachi.hopper.safety）"),
        },
        _VOL,
        "中期报告 §3.3 式(3-25)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F9",
        "d_upper = upper_ratio * d",
        {
            "upper_ratio": (_D, "砂斗上口径比（factor.chenshachi.hopper_upper_ratio）"),
            "d": (_L, "池径（ceil 后）m"),
        },
        _L,
        _GB,
    ),
    FormulaSpec(
        "CS-F10",
        "h4 = (d_upper - d_r) / (2 * tan_theta)",
        {
            "d_upper": (_L, "砂斗上口直径 m"),
            "d_r": (_L, "排砂口直径 m"),
            "tan_theta": (_D, "tanθ 预处理值"),
        },
        _L,
        "中期报告 §3.3 式(3-27)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F11",
        "v_cone = pi * h4 / 3 * ((d_upper / 2) ** 2 + (d_upper / 2) * (d_r / 2) + (d_r / 2) ** 2)",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "h4": (_L, "砂斗高度 m"),
            "d_upper": (_L, "砂斗上口直径 m"),
            "d_r": (_L, "排砂口直径 m"),
        },
        _VOL,
        _GB,
    ),
    FormulaSpec(
        "CS-F12",
        "h_cyl_raw = (v_hopper - v_cone) / (pi * (d_upper / 2) ** 2)",
        {
            "v_hopper": (_VOL, "砂斗容积 m3"),
            "v_cone": (_VOL, "圆台容积 m3"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "d_upper": (_L, "砂斗上口直径 m"),
        },
        _L,
        _GB,
    ),
    FormulaSpec(
        "CS-F13",
        "h_total_raw = h1_super + h2 + h3_buffer + h4 + h_cyl",
        {
            "h1_super": (_L, "超高 m（factor.chenshachi.superheight）"),
            "h2": (_L, "有效水深 m"),
            "h3_buffer": (_L, "缓冲层 m（factor.chenshachi.buffer_h3）"),
            "h4": (_L, "砂斗高度 m"),
            "h_cyl": (_L, "圆柱储砂段高（ceil 后）m"),
        },
        _L,
        _GB,
    ),
    FormulaSpec(
        "CS-F14",
        "h_channel = q1 / (v_channel * b_channel)",
        {
            "q1": (_F, "单池流量 m3/s"),
            "v_channel": (_V, "进水流速 m/s"),
            "b_channel": (_L, "进水渠宽 m"),
        },
        _L,
        "中期报告 §3.3 式(4-26)~(4-27)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F15",
        "l_straight = max(straight_mult * b_channel, straight_min)",
        {
            "straight_mult": (_D, "直段长宽比（factor.chenshachi.channel.straight_mult）"),
            "b_channel": (_L, "进水渠宽 m"),
            "straight_min": (_L, "直段最小长 m（factor.chenshachi.channel.straight_min）"),
        },
        _L,
        "中期报告 §3.3 式(4-28)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F16",
        "b_outlet = outlet_mult * b_channel",
        {
            "outlet_mult": (_D, "出水渠宽比（factor.chenshachi.channel.outlet_mult）"),
            "b_channel": (_L, "进水渠宽 m"),
        },
        _L,
        "中期报告 §3.3 式(4-29)（毕业设计内部资料，待核对映射条文）；" + _GB,
    ),
    FormulaSpec(
        "CS-F17",
        "ds_grit = v_sand * (1 - moisture) * grit_density * n",
        {
            "v_sand": (_VOL, "单池日沉砂量 m3/d"),
            "moisture": (_D, "沉砂含水率 P（factor.chenshachi.grit.moisture）"),
            "grit_density": (_D, "沉砂密度 kg/m3（factor.chenshachi.grit.density）"),
            "n": (_D, "池数"),
        },
        _M,
        _GB,
    ),
    FormulaSpec(
        "CS-F18",
        "v_concrete = pi * (d / 2) ** 2 * h_total * n * wall_coef",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "d": (_L, "池径（ceil 后）m"),
            "h_total": (_L, "总高（ceil 后）m"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.chenshachi.wall_thickness_coef，概算口径）"),
        },
        _VOL,
        _GB,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.municipal_chenshachi",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/chenshachi.md 参数行）；
        # range 仅停留时间带（retention_band 25~60 三表校核带出处，含
        # mod.json min=30 与带不一致矛盾 3：总控工程惯例裁定 2026-08-25
        # 表载 t=30 生效、待领域专家追认），其余参数无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2, 3, 4, 5, 6]},
            {
                "field_id": "q_surf",
                "dim": "DIMENSIONLESS",
                "default": 150.0,
                "range": {"min": 150.0, "max": 200.0},
            },
            {
                "field_id": "t_retention",
                "dim": "TIME",
                "default": 30.0,
                "range": {"min": 25.0, "max": 60.0},
            },
            {"field_id": "t_clean", "dim": "DIMENSIONLESS", "default": 2.0},
            {"field_id": "theta", "dim": "DIMENSIONLESS", "default": 55.0},
            {"field_id": "d_r", "dim": "LENGTH", "default": 0.5},
            {"field_id": "b_channel", "dim": "LENGTH", "default": 0.8},
            {"field_id": "v_channel", "dim": "VELOCITY", "default": 1.0},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
            {"field_id": "sec_per_hour", "dim": "DIMENSIONLESS", "default": 3600.0},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.chenshachi.bod5.mod_default",
            "CODCR": "removal.chenshachi.cod.mod_default",
            "SS": "removal.chenshachi.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §6.4（条文号待核对原文）",
            "中期报告 §3.3（毕业设计内部资料，待核对映射条文）",
            "docs/norms/chenshachi.md（2026-08-23 领域专家签字手算对照表）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "chenshachi.surface_load_band",
            "chenshachi.h2_band",
            "chenshachi.ratio_dh2_band",
            "chenshachi.retention_band",
        ],
    }
)
