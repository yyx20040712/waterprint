"""矿井水调节池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_tiaojiechi.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KT-F1~F12 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_tiaojiechi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=16 分格/t_reg=8.0 h/h2=3.0 m/
#   ratio_lb=3.0；B·L 档 0.5 m/DN 档 0.05 m）；系数不落本表——hrt/
#   depth/ratio_lb 三校核带+搅拌功率密度+出水管流速+超高+壁厚系数+
#   高程水损全部经 factor.mine_tiaojiechi.* 键消费（app._unit_params
#   线感知投影，mine_ 限定）；去除率经 removal.mine_tiaojiechi.{ss,
#   cod}.mod_default 键（纯均化零去除显式 0.0 穿流——旧预沉 0.30 归
#   追认点 1；BOD5 全线不建键）。
# 【公式注册（D1）】KT-F1~F12 逐条 FormulaSpec+register；expression=
#   表公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；
#   结构常数（24/1000）内联（本文件=units_lib manifest 白名单区）；
#   ×86400=流量口径注记（WaterFlow 规范单位 m3/s → 调节容积按 m3/d
#   口径，表内 q_avg_daily m³/d 直书的单位口径对齐，KT-F1/F8 同市政
#   TJ-F1/F8 M2b2 先例）；KT-F10 表串 q_avg_h/3600（m³/h→m3/s）与
#   规范单位流量等价——串内直用 q_avg_daily（平均时 m3/s 绑定，
#   市政 TJ-F11 同型）；π 经符号 pi 绑定 math.pi；sqrt 直接用。
#   DSL 无 ceil：池宽 B/池长 L（0.5 m 档）/出水管 DN（0.05 m 档）
#   离散在 compute 收口（步长=参数）。
# 【物理隔离】与市政同名包 municipal/tiaojiechi 零 import 零参数复用
#   （§14.3）：hrt_band 8~12（市政 6~12）/depth_band 3.0~5.0（市政
#   4.0~6.0）/搅拌 8 W/m³（市政 6）三带独立起草（表边界差异节）。
# 【声明五件】params（range 仅表内有出处带者：t_reg/h2/ratio_lb 三
#   参数；分格数 n=16 构造参数无档位来源不设 grid）/ports 两口 WATER/
#   removal_refs 双指标键/norm_refs 双源标记（GB/T 41019-2021+给水
#   排水设计手册）/condition_mappings=()/constraint_refs 三键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_tiaojiechi"

_GB = (
    "GB/T 41019-2021（矿井水处理工艺——调节构筑物容积口径，条号待核对；"
    "docs/norms/mine_water_tiaojiechi.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》调节池停留时间法/防沉积"
    "搅拌功率密度常用带（docs/norms/mine_water_tiaojiechi.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KT-F1",
        "v_total = q_avg_daily * 86400 * t_reg / 24",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径——表内 m³/d 直书对齐）"),
            "t_reg": (_D, "调节停留时间 h（参数 t_reg，停留时间法主线）"),
        },
        _VOL,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "KT-F2",
        "v1 = v_total / n",
        {"v_total": (_VOL, "需调节容积 m3"), "n": (_D, "分格数（多格检修兼顾）")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KT-F3",
        "a1 = v1 / h2",
        {"v1": (_VOL, "单格容积 m3"), "h2": (_L, "有效水深 m（参数 h2）")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "KT-F4",
        "b_raw = sqrt(a1 / ratio_lb)",
        {"a1": (_A, "单格平面面积 m2"), "ratio_lb": (_D, "池长宽比（参数 ratio_lb）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "KT-F5",
        "l_raw = a1 / B",
        {"a1": (_A, "单格平面面积 m2"), "B": (_L, "池宽（0.5 m 档 ceil 后）m")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "KT-F6",
        "a_act = B * L",
        {"B": (_L, "池宽（ceil 后）m"), "L": (_L, "池长（0.5 m 档 ceil 后）m")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "KT-F7",
        "v_act_total = a_act * h2 * n",
        {
            "a_act": (_A, "单格实取平面面积 m2"),
            "h2": (_L, "有效水深 m"),
            "n": (_D, "分格数"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KT-F8",
        "t_reg_act = v_act_total * 24 / (q_avg_daily * 86400)",
        {
            "v_act_total": (_VOL, "实际调节容积 m3"),
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
        },
        _D,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "KT-F9",
        "p_stir = v_act_total * w_stir / 1000",
        {
            "v_act_total": (_VOL, "实际调节容积 m3"),
            "w_stir": (_D, "防沉积搅拌功率密度 W/m3（factor.mine_tiaojiechi.stir.power_density）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KT-F10",
        "d_out_raw = sqrt(4 * q_avg_daily / (pi * v_out))",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（表串 q_avg_h/3600 即平均时 m3/s 规范单位等价）"),
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "v_out": (
                _V,
                "出水管流速 m/s（factor.mine_tiaojiechi.overflow_velocity，按平均时均匀输出）",
            ),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KT-F11",
        "h_total = h_super + h2",
        {
            "h_super": (_L, "超高 m（factor.mine_tiaojiechi.superheight）"),
            "h2": (_L, "有效水深 m（参数 h2）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KT-F12",
        "v_concrete = a_act * h_total * n * wall_coef",
        {
            "a_act": (_A, "单格实取平面面积 m2"),
            "h_total": (_L, "池总高 m"),
            "n": (_D, "分格数"),
            "wall_coef": (_D, "壁厚系数（factor.mine_tiaojiechi.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.mine_water_tiaojiechi",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_tiaojiechi.md 参数档）；
        # range 仅三条有出处带参数（hrt_band 8~12/depth_band 3.0~5.0/
        # ratio_lb_band 2.0~4.0——井下脉动+高 SS+地下式布置独立起草），
        # 分格数/取整档无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 16.0},
            {
                "field_id": "t_reg",
                "dim": "DIMENSIONLESS",
                "default": 8.0,
                "range": {"min": 8.0, "max": 12.0},
            },
            {
                "field_id": "h2",
                "dim": "LENGTH",
                "default": 3.0,
                "range": {"min": 3.0, "max": 5.0},
            },
            {
                "field_id": "ratio_lb",
                "dim": "DIMENSIONLESS",
                "default": 3.0,
                "range": {"min": 2.0, "max": 4.0},
            },
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.05},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_tiaojiechi.ss.mod_default",
            "CODCR": "removal.mine_tiaojiechi.cod.mod_default",
        },
        "norm_refs": [
            "GB/T 41019-2021（矿井水处理工艺——调节构筑物容积口径，条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》调节池停留时间法/防沉积搅拌功率密度常用带",
            "docs/norms/mine_water_tiaojiechi.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_tiaojiechi.hrt_band",
            "mine_water_tiaojiechi.depth_band",
            "mine_water_tiaojiechi.ratio_lb_band",
        ],
    }
)
