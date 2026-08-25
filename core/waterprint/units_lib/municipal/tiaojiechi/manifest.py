"""调节池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  四表起草真源（docs/norms/tiaojiechi.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.3.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ TJ-F1~F13 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_tiaojiechi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=四表算例 1 逐字（n=2/t_reg=8.0 h/h2=5.0 m/
#   ratio_lb=2.5/n_pump_duty=2 用 1 备/B·L 档 0.5 m/DN 档 0.1 m）；系数
#   不落本表——hrt/depth/ratio_lb 三校核带+搅拌功率密度+溢流管流速+超高+
#   壁厚系数+高程水损全部经 factor.tiaojiechi.* 键消费（app._unit_params
#   投影）；去除率经 removal.tiaojiechi.*.mod_default 键（物理均化无去除，
#   全 0.0；NH3N/TN/TP 不建条目）。
# 【公式注册（D1）】TJ-F1~F13 逐条 FormulaSpec+register；expression=四表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构常数
#   （24/1000/4/3600/86400）内联（本文件=units_lib manifest 白名单区）；
#   ×86400=流量口径注记（WaterFlow 规范单位 m3/s → 调节容积按 m3/d 口径，
#   TJ-F1/F8 同 CC-F10 M2a2 先例）；×3600=时换算条文常量（TJ-F10 出水泵
#   按平均时均匀输出，m3/h 口径）；π 经符号 pi 绑定 math.pi（四表内联
#   3.14159265 的 M2a2 等价形态惯例）；sqrt 经 M1b D4 Name 豁免直接用。
#   DSL 无 ceil：池宽 B/池长 L（0.5 m 档）/溢流管 DN（0.1 m 档）离散在
#   compute 收口（步长=参数）。
# 【追认口径按表冻结】调节池沉砂后位置（入流=chenshachi 出流口径，与
#   chuchenchi 表同源；调节容积法 HRT 主线——无进水流量过程线资料）。
# 【声明五件】params（range 仅表内有出处带者：t_reg/h2/ratio_lb 三参数）/
#   ports 两口 WATER/removal_refs（全 0.0 键同引用）/norm_refs 双源标记
#   （GB 50014-2021+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 三键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_tiaojiechi"

_GB = (
    "GB 50014-2021 §3.3/§6（流量调节与构筑物一般规定；"
    "docs/norms/tiaojiechi.md 起草表 2026-08-25，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》调节池/泵站章"
    "（docs/norms/tiaojiechi.md 起草表 2026-08-25，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "TJ-F1",
        "v_total = q_avg_daily * 86400 * t_reg / 24",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "t_reg": (_D, "调节停留时间 h（参数 t_reg，停留时间法）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "TJ-F2",
        "v1 = v_total / n",
        {"v_total": (_VOL, "需调节容积 m3"), "n": (_D, "池数")},
        _VOL,
        _GB,
    ),
    FormulaSpec(
        "TJ-F3",
        "a1 = v1 / h2",
        {"v1": (_VOL, "单池容积 m3"), "h2": (_L, "有效水深 m（参数 h2）")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "TJ-F4",
        "b_raw = sqrt(a1 / ratio_lb)",
        {"a1": (_A, "单池平面面积 m2"), "ratio_lb": (_D, "池长宽比（参数 ratio_lb）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "TJ-F5",
        "l_raw = a1 / B",
        {"a1": (_A, "单池平面面积 m2"), "B": (_L, "池宽（0.5 m 档 ceil 后）m")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "TJ-F6",
        "a_act = B * L",
        {"B": (_L, "池宽（ceil 后）m"), "L": (_L, "池长（0.5 m 档 ceil 后）m")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "TJ-F7",
        "v_act_total = a_act * h2 * n",
        {
            "a_act": (_A, "单池实取平面面积 m2"),
            "h2": (_L, "有效水深 m"),
            "n": (_D, "池数"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "TJ-F8",
        "t_reg_act = v_act_total * 24 / (q_avg_daily * 86400)",
        {
            "v_act_total": (_VOL, "实际调节容积 m3"),
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "TJ-F9",
        "p_stir = v_act_total * w_stir / 1000",
        {
            "v_act_total": (_VOL, "实际调节容积 m3"),
            "w_stir": (_D, "防沉积搅拌功率密度 W/m3（factor.tiaojiechi.stir.power_density）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "TJ-F10",
        "q_pump1 = q_avg_daily * 3600 / n_pump_duty",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×3600 转 m3/h 口径）"),
            "n_pump_duty": (_D, "工作泵台数（参数 n_pump_duty，2 用 1 备）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "TJ-F11",
        "d_overflow_raw = sqrt(4 * q_design / (pi * v_overflow))",
        {
            "q_design": (_F, "最高时设计流量 m3/s"),
            "pi": (_D, "圆周率（math.pi 绑定，四表内联 3.14159265 等价形态）"),
            "v_overflow": (_V, "溢流/超越管流速 m/s（factor.tiaojiechi.overflow_velocity）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "TJ-F12",
        "h_total = h_super + h2",
        {
            "h_super": (_L, "超高 m（factor.tiaojiechi.superheight）"),
            "h2": (_L, "有效水深 m（参数 h2）"),
        },
        _L,
        _GB,
    ),
    FormulaSpec(
        "TJ-F13",
        "v_concrete = a_act * h_total * n * wall_coef",
        {
            "a_act": (_A, "单池实取平面面积 m2"),
            "h_total": (_L, "池总高 m"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.tiaojiechi.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.municipal_tiaojiechi",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=四表算例 1 逐字（出处 docs/norms/tiaojiechi.md 参数档）；
        # range 仅三条有出处带参数（hrt_band 6~12/depth_band 4.0~6.0/
        # ratio_lb_band 2.0~3.0），构造参数（池数/泵台数/取整档）无范围
        # 来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0},
            {
                "field_id": "t_reg",
                "dim": "DIMENSIONLESS",
                "default": 8.0,
                "range": {"min": 6.0, "max": 12.0},
            },
            {
                "field_id": "h2",
                "dim": "LENGTH",
                "default": 5.0,
                "range": {"min": 4.0, "max": 6.0},
            },
            {
                "field_id": "ratio_lb",
                "dim": "DIMENSIONLESS",
                "default": 2.5,
                "range": {"min": 2.0, "max": 3.0},
            },
            {"field_id": "n_pump_duty", "dim": "DIMENSIONLESS", "default": 2.0},
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.tiaojiechi.bod5.mod_default",
            "CODCR": "removal.tiaojiechi.cod.mod_default",
            "SS": "removal.tiaojiechi.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §3.3/§6（流量变化与调节/构筑物一般规定）",
            "《给水排水设计手册（第 5 册 城镇排水）》调节池/泵站章",
            "docs/norms/tiaojiechi.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "tiaojiechi.hrt_band",
            "tiaojiechi.depth_band",
            "tiaojiechi.ratio_lb_band",
        ],
    }
)
