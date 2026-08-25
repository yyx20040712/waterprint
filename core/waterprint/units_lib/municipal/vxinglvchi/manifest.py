"""V型滤池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  四表起草真源（docs/norms/vxinglvchi.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.3.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ XL-F1~F19 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_vxinglvchi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=四表算例 1 逐字（n=6 分格/v_filter=8.0 m/h/
#   ratio_lb=2.5/砂上水深 1.3/砂层 1.3/滤板气水区 1.0/t_cycle=24 h；
#   B·L 档 0.5 m）；系数不落本表——正常·强制滤速/单格长宽比/滤层厚/
#   砂上水深/过滤周期六校核带+自用水系数+气水冲洗四强度+三历时+超高+
#   壁厚系数+高程水损全部经 factor.vxinglvchi.* 键消费（app._unit_params
#   投影）；去除率经 removal.vxinglvchi.*.mod_default 键（NH3N/TN/TP
#   不建条目）。
# 【公式注册（D1）】XL-F1~F19 逐条 FormulaSpec+register；expression=四表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构
#   常数（1000/24/60/3600/86400）内联（本文件=units_lib manifest 白名单区）；
#   ×3600=时换算条文常量（XL-F1 q_design m3/s→m3/h 口径，四表 q_design_h
#   等价形态）；×86400=流量口径注记（XL-F17 反冲耗水率按 m3/d 口径，
#   CC-F10 M2a2 先例）；sqrt 经 M1b D4 Name 豁免直接用。DSL 无 ceil：
#   单格宽 B/长 L（0.5 m 档）离散在 compute 收口（步长=参数）。
# 【强制滤速口径】XL-F9 校核带 11~13 为典型带——运行时按单向上限
#   （≤band.max）校核（四表算例 9.4626<11 注"合格"：低于带下限=保守
#   合格非越界），constraints 声明同口径。
# 【砂上水深/滤层】XL-F18 h_total=超高+砂上水深+砂层+滤板气水区（四表
#   池深组成逐字；均质滤料不设砾石承托层——滤板+长柄滤头直接支撑，
#   d10/K80 为滤料选型注记无计算面不建公式）。
# 【声明五件】params（range 仅表内有出处带者：v_filter/ratio_lb/
#   h_water_above/h_sand/t_cycle 五参数；n 分格数≥4 与 h_bottom 构造无
#   范围来源不设）/ports 两口 WATER/removal_refs/norm_refs 双源标记
#   （GB 50013-2018+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 六键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_vxinglvchi"

_GB = (
    "GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速与气水反冲洗强度；"
    "docs/norms/vxinglvchi.md 起草表 2026-08-25，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》V 型滤池构造常用值"
    "（docs/norms/vxinglvchi.md 起草表 2026-08-25，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "XL-F1",
        "q_filter = q_design * 3600 * selfuse_coef",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×3600 转 m3/h 口径，四表 q_design_h 等价形态）"),
            "selfuse_coef": (_D, "自用水系数（factor.vxinglvchi.selfuse_coef，反冲耗水补偿）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "XL-F2",
        "a_total_req = q_filter / v_filter",
        {
            "q_filter": (_D, "过滤流量 m3/h"),
            "v_filter": (_D, "正常滤速 m/h（参数 v_filter，主控）"),
        },
        _A,
        _GB,
    ),
    FormulaSpec(
        "XL-F3",
        "a_cell = a_total_req / n",
        {"a_total_req": (_A, "需过滤面积 m2"), "n": (_D, "分格数（参数 n，≥4 离散档）")},
        _A,
        _GB,
    ),
    FormulaSpec(
        "XL-F4",
        "b_raw = sqrt(a_cell / ratio_lb)",
        {"a_cell": (_A, "单格需面积 m2"), "ratio_lb": (_D, "单格长宽比（参数 ratio_lb）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "XL-F5",
        "l_raw = a_cell / B",
        {"a_cell": (_A, "单格需面积 m2"), "B": (_L, "单格宽（0.5 m 档 ceil 后）m")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "XL-F6",
        "a_cell_act = B * L",
        {"B": (_L, "单格宽（ceil 后）m"), "L": (_L, "单格长（0.5 m 档 ceil 后）m")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "XL-F7",
        "a_total_act = a_cell_act * n",
        {"a_cell_act": (_A, "单格实取过滤面积 m2"), "n": (_D, "分格数")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "XL-F8",
        "v_filter_act = q_filter / a_total_act",
        {"q_filter": (_D, "过滤流量 m3/h"), "a_total_act": (_A, "全池实取过滤面积 m2")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "XL-F9",
        "v_forced_act = q_filter / (a_total_act - a_cell_act)",
        {
            "q_filter": (_D, "过滤流量 m3/h"),
            "a_total_act": (_A, "全池实取过滤面积 m2"),
            "a_cell_act": (_A, "单格实取过滤面积 m2（一格冲洗时其余格过全部流量）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "XL-F10",
        "q_air = a_cell_act * w_air / 1000",
        {
            "a_cell_act": (_A, "单格实取过滤面积 m2"),
            "w_air": (_D, "气冲强度 L/(m2.s)（factor.vxinglvchi.wash.air）"),
        },
        _F,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "XL-F11",
        "q_wash_sim = a_cell_act * w_water_sim / 1000",
        {
            "a_cell_act": (_A, "单格实取过滤面积 m2"),
            "w_water_sim": (_D, "气水同时冲洗水强度（factor.vxinglvchi.wash.water_sim）"),
        },
        _F,
        _HB,
    ),
    FormulaSpec(
        "XL-F12",
        "q_wash = a_cell_act * w_water / 1000",
        {
            "a_cell_act": (_A, "单格实取过滤面积 m2"),
            "w_water": (_D, "单独水冲（漂洗）强度（factor.vxinglvchi.wash.water）"),
        },
        _F,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "XL-F13",
        "q_sweep = a_cell_act * w_sweep / 1000",
        {
            "a_cell_act": (_A, "单格实取过滤面积 m2"),
            "w_sweep": (_D, "表面扫洗强度（factor.vxinglvchi.wash.sweep，V 型槽进水扫洗）"),
        },
        _F,
        _HB,
    ),
    FormulaSpec(
        "XL-F14",
        "v_air_per = q_air * (t_air + t_sim) * 60",
        {
            "q_air": (_F, "单格气冲流量 m3/s"),
            "t_air": (_D, "气冲历时 min（factor.vxinglvchi.wash.t_air）"),
            "t_sim": (_D, "气水同时历时 min（factor.vxinglvchi.wash.t_sim）"),
        },
        _VOL,
        _GB,
    ),
    FormulaSpec(
        "XL-F15",
        "v_wash_per = (q_wash_sim * t_sim + q_wash * t_water"
        " + q_sweep * (t_air + t_sim + t_water)) * 60",
        {
            "q_wash_sim": (_F, "气水同时冲洗水流量 m3/s"),
            "q_wash": (_F, "单独水冲流量 m3/s"),
            "q_sweep": (_F, "表面扫洗流量 m3/s"),
            "t_air": (_D, "气冲历时 min（factor.vxinglvchi.wash.t_air）"),
            "t_sim": (_D, "气水同时历时 min（factor.vxinglvchi.wash.t_sim）"),
            "t_water": (_D, "水冲历时 min（factor.vxinglvchi.wash.t_water）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "XL-F16",
        "v_wash_daily = v_wash_per * n * 24 / t_cycle",
        {
            "v_wash_per": (_VOL, "单格次耗水 m3"),
            "n": (_D, "分格数"),
            "t_cycle": (_D, "过滤周期 h（参数 t_cycle）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "XL-F17",
        "ratio_wash = v_wash_daily / (q_avg_daily * 86400)",
        {
            "v_wash_daily": (_VOL, "全厂日耗水 m3/d"),
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "XL-F18",
        "h_total = h_super + h_water_above + h_sand + h_bottom",
        {
            "h_super": (_L, "超高 m（factor.vxinglvchi.superheight）"),
            "h_water_above": (_L, "砂上水深 m（参数 h_water_above，恒水位过滤）"),
            "h_sand": (_L, "砂层厚 m（参数 h_sand，均质滤料）"),
            "h_bottom": (_L, "滤板气水区高 m（参数 h_bottom，长柄滤头）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "XL-F19",
        "v_concrete = a_total_act * h_total * wall_coef",
        {
            "a_total_act": (_A, "全池实取过滤面积 m2"),
            "h_total": (_L, "滤池总高 m"),
            "wall_coef": (_D, "壁厚系数（factor.vxinglvchi.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.municipal_vxinglvchi",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=四表算例 1 逐字（出处 docs/norms/vxinglvchi.md 参数档/构造参数段）；
        # range 仅五条有出处带参数（v_filter_band 7~10/cell_ratio_lb_band
        # 2.0~3.0/water_above_band 1.2~1.5/media.depth_band 1.2~1.5/
        # cycle_band 24~48），构造参数（分格数/滤板气水区高/取整档）无
        # 范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 6.0},
            {
                "field_id": "v_filter",
                "dim": "DIMENSIONLESS",
                "default": 8.0,
                "range": {"min": 7.0, "max": 10.0},
            },
            {
                "field_id": "ratio_lb",
                "dim": "DIMENSIONLESS",
                "default": 2.5,
                "range": {"min": 2.0, "max": 3.0},
            },
            {
                "field_id": "h_water_above",
                "dim": "LENGTH",
                "default": 1.3,
                "range": {"min": 1.2, "max": 1.5},
            },
            {
                "field_id": "h_sand",
                "dim": "LENGTH",
                "default": 1.3,
                "range": {"min": 1.2, "max": 1.5},
            },
            {"field_id": "h_bottom", "dim": "LENGTH", "default": 1.0},
            {
                "field_id": "t_cycle",
                "dim": "DIMENSIONLESS",
                "default": 24.0,
                "range": {"min": 24.0, "max": 48.0},
            },
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.vxinglvchi.bod5.mod_default",
            "CODCR": "removal.vxinglvchi.cod.mod_default",
            "SS": "removal.vxinglvchi.ss.mod_default",
        },
        "norm_refs": [
            "GB 50013-2018 §9.5（滤池：均质滤料滤速/强制滤速与气水反冲洗强度）",
            "《给水排水设计手册（第 5 册 城镇排水）》V 型滤池构造常用值",
            "docs/norms/vxinglvchi.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "vxinglvchi.v_filter_band",
            "vxinglvchi.v_forced_band",
            "vxinglvchi.cell_ratio_lb_band",
            "vxinglvchi.media.depth_band",
            "vxinglvchi.water_above_band",
            "vxinglvchi.cycle_band",
        ],
    }
)
