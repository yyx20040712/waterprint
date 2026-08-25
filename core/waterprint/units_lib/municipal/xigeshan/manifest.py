"""细格栅清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（声明式唯一真源）。

输入:  三表签字真源（docs/norms/xigeshan.md，2026-08-23）+ data/coefficients 0.1.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ XG-F1~F14 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M1a 实装：M1 先行示范（本批实装）/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_xigeshan"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 值逐字（n=3/b=8mm/α=70°/h=0.6/
#   v=0.8/v₁=0.7/s=3mm/bar_shape=0/g=9.81/取整步长 0.1）；系数不落本表
#   ——β/k/超高/裕量/W₁/含水率/清渣阈值/流速带/壁厚系数全部经
#   factor.screen.*|factor.xigeshan.* 键消费（app._unit_params 投影，
#   D4）；去除率经 removal.xigeshan.*.mod_default 键（NH3N/TN/TP 依
#   data 包头部注记不建条目）。
# 【公式注册（D2）】XG-F1~F14 逐条 FormulaSpec+register（import 时登记）：
#   expression=三表公式串转受限 DSL——β/k/裕量/超高/W₁/阈值/含水率/
#   壁厚系数等 data 包系数一律符号绑定（零系数字面量）；公式自身结构
#   常数（2g 之 2、(4/3) 指数、86400/1000 量纲换算）按 registry DSL
#   "常量是公式自身的条文系数"规则内联（本文件=units_lib manifest 白名单
#   区，出处随 norm_ref 走三表）。DSL 无 ceil/三角函数：n_gap 取整与
#   0.1m 构造步长离散在 compute 收口（步长=manifest 参数 length_disc_step，
#   出处三表 XG-F3/F9/F10；共用 _BarScreenBase 公式体系同 cugeshan）；
#   sin/tan 预处理值以符号传入（sqrt_sin_alpha/sin_alpha/tan_alpha）。
# 【norm_ref 口径】节级引用"GB 50014-2021 §6.3（条文号待核对原文）"，
#   条文级核对挂账（三表条文摘录表在册）；XG-F10 固定段 1.0/0.5/(0.2+h)
#   三表标注"旧系统无出处注释"——挂账同三表。
# 【声明五件】params/ports/removal_refs/norm_refs/condition_mappings
#   （v1 三单元无受检降级需求=()，D3 裁决）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_xigeshan"

_NORM = "GB 50014-2021 §6.3（条文号待核对原文；docs/norms/xigeshan.md 签字表 2026-08-23）"
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_V = DimKey.VELOCITY
_VOL = DimKey.VOLUME
_M = DimKey.MASS

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "XG-F1",
        "q = q_design / n",
        {"q_design": (_F, "最大设计流量 m3/s"), "n": (_D, "格栅台数")},
        _F,
        _NORM,
    ),
    FormulaSpec(
        "XG-F2",
        "n_gap_ratio = q * sqrt_sin_alpha / (b * h * v)",
        {
            "q": (_F, "单台流量 m3/s"),
            "sqrt_sin_alpha": (_D, "√(sinα) 预处理值"),
            "b": (_L, "栅条间隙 m"),
            "h": (_L, "栅前水深 m"),
            "v": (_V, "过栅流速设计值 m/s"),
        },
        _D,
        _NORM,
    ),
    FormulaSpec(
        "XG-F3",
        "b_raw = s * (n_gap - 1) + b * n_gap + margin",
        {
            "s": (_L, "栅条宽 m"),
            "n_gap": (_D, "栅条间隙数（ceil 后）"),
            "b": (_L, "栅条间隙 m"),
            "margin": (_L, "栅槽宽构造裕量 m（factor.screen.trough_width_margin）"),
        },
        _L,
        _NORM,
    ),
    FormulaSpec(
        "XG-F4",
        "b1_raw = q / (h * v1)",
        {"q": (_F, "单台流量 m3/s"), "h": (_L, "栅前水深 m"), "v1": (_V, "栅前流速 m/s")},
        _L,
        _NORM,
    ),
    FormulaSpec(
        "XG-F5",
        "v_checked = q * sqrt_sin_alpha / (b * h * n_gap)",
        {
            "q": (_F, "单台流量 m3/s"),
            "sqrt_sin_alpha": (_D, "√(sinα) 预处理值"),
            "b": (_L, "栅条间隙 m"),
            "h": (_L, "栅前水深 m"),
            "n_gap": (_D, "栅条间隙数（ceil 后）"),
        },
        _V,
        _NORM,
    ),
    FormulaSpec(
        "XG-F6",
        "v1_checked = q / (h * b1)",
        {
            "q": (_F, "单台流量 m3/s"),
            "h": (_L, "栅前水深 m"),
            "b1": (_L, "进水渠宽 B1（ceil 后）m"),
        },
        _V,
        _NORM,
    ),
    FormulaSpec(
        "XG-F7",
        "xi = beta * s_over_b ** (4 / 3)",
        {
            "beta": (_D, "栅条形状系数 β（factor.screen.beta.*）"),
            "s_over_b": (_D, "s/b 同单位比值"),
        },
        _D,
        _NORM,
    ),
    FormulaSpec(
        "XG-F8",
        "h1 = k_headloss * xi * v_checked ** 2 / (2 * g) * sin_alpha",
        {
            "k_headloss": (_D, "水头损失安全系数 k（factor.screen.headloss.k）"),
            "xi": (_D, "栅条阻力系数 ξ"),
            "v_checked": (_V, "校核过栅流速 m/s"),
            "g": (_D, "重力加速度 m/s2（参数 g_gravity）"),
            "sin_alpha": (_D, "sinα 预处理值"),
        },
        _L,
        _NORM,
    ),
    FormulaSpec(
        "XG-F9",
        "h_total_raw = h + h1 + superheight",
        {
            "h": (_L, "栅前水深 m"),
            "h1": (_L, "过栅水头损失 m"),
            "superheight": (_L, "超高 m（factor.screen.superheight）"),
        },
        _L,
        _NORM,
    ),
    FormulaSpec(
        "XG-F10",
        "l_raw = (B - b1) / (2 * tan_alpha) + (B - b1) / (4 * tan_alpha)"
        " + l3_fixed + l4_fixed + (drop_constant + h) / tan_alpha",
        {
            "B": (_L, "栅槽宽（ceil 后）m"),
            "b1": (_L, "进水渠宽 B1（ceil 后）m"),
            "tan_alpha": (_D, "tanα 预处理值"),
            "l3_fixed": (_L, "固定段一 m（factor.screen.trough_length.l3_fixed）"),
            "l4_fixed": (_L, "固定段二 m（factor.screen.trough_length.l4_fixed）"),
            "drop_constant": (_L, "渐窄段起算常数 m（…drop_constant）"),
            "h": (_L, "栅前水深 m"),
        },
        _L,
        _NORM,
    ),
    FormulaSpec(
        "XG-F11",
        "w_slag = q_design * 86400 * w1 / (kz * 1000)",
        {
            "q_design": (_F, "最大设计流量 m3/s"),
            "w1": (_D, "栅渣量系数 W1 m3/1e3m3（factor.xigeshan.w1_slag）"),
            "kz": (_D, "总变化系数"),
        },
        _VOL,
        _NORM,
    ),
    FormulaSpec(
        "XG-F12",
        "mech_margin = w_slag - mech_clean_threshold",
        {
            "w_slag": (_VOL, "日栅渣量 m3/d"),
            "mech_clean_threshold": (_VOL, "机械清渣阈值 m3/d（…mech_clean_threshold）"),
        },
        _VOL,
        _NORM,
    ),
    FormulaSpec(
        "XG-F13",
        "ds_slag = w_slag * (1 - moisture) * 1000",
        {
            "w_slag": (_VOL, "日栅渣量 m3/d"),
            "moisture": (_D, "栅渣含水率 P（factor.screen.slag.moisture）"),
        },
        _M,
        _NORM,
    ),
    FormulaSpec(
        "XG-F14",
        "v_concrete = L * B * H * n * wall_coef",
        {
            "L": (_L, "栅槽总长（ceil 后）m"),
            "B": (_L, "栅槽宽（ceil 后）m"),
            "H": (_L, "栅后总高（ceil 后）m"),
            "n": (_D, "格栅台数"),
            "wall_coef": (_D, "壁厚系数（factor.screen.wall_thickness_coef，概算口径）"),
        },
        _VOL,
        _NORM,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.municipal_xigeshan",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/xigeshan.md 参数行）；
        # range 只在流速带（factor.screen.velocity_band，三表校核带）落，
        # 其余参数三表无范围来源不设（数值纪律：禁编造）
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 3.0},
            {
                "field_id": "b",
                "dim": "LENGTH",
                "default": 0.008,
                "range": {"min": 0.0015, "max": 0.01},
            },  # 三表：b=5mm（1.5~10）
            {"field_id": "alpha", "dim": "DIMENSIONLESS", "default": 70.0},
            {"field_id": "h", "dim": "LENGTH", "default": 0.6},
            {"field_id": "v", "dim": "VELOCITY", "default": 0.8, "range": {"min": 0.6, "max": 1.0}},
            {
                "field_id": "v1",
                "dim": "VELOCITY",
                "default": 0.7,
                "range": {"min": 0.4, "max": 0.9},
            },
            {"field_id": "s", "dim": "LENGTH", "default": 0.003},
            {"field_id": "bar_shape", "dim": "DIMENSIONLESS", "default": 0.0},
            {"field_id": "g_gravity", "dim": "DIMENSIONLESS", "default": 9.81},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.xigeshan.bod5.mod_default",
            "CODCR": "removal.xigeshan.cod.mod_default",
            "SS": "removal.xigeshan.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §6.3（条文号待核对原文）",
            "docs/norms/xigeshan.md（2026-08-23 领域专家签字手算对照表）",
        ],
        "condition_mappings": [],
        "constraint_refs": ["xigeshan.velocity_band.v", "xigeshan.velocity_band.v1"],
    }
)
