"""高密沉淀池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  四表起草真源（docs/norms/gaomidu.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.3.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ GM-F1~F20 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_gaomidu"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=四表算例 1 逐字（n=2/q_surface=15/r_sludge=0.04/
#   t_mix=1.5 min/t_floc=12 min/斜管长 1.0 倾角 60°/清水区 1.2/布水区 1.2/
#   浓缩泥区 2.0；B 档 0.5 m/h_total 档 0.1 m）；系数不落本表——液面
#   负荷/回流比/快混絮凝停留/GT 五校核带+双 G 值+排泥含固率+PAC/PAM
#   投加量+超高+壁厚系数+高程水损全部经 factor.gaomidu.* 键消费
#   （app._unit_params 投影）；去除率经 removal.gaomidu.*.mod_default 键
#   （NH3N/TN/TP 不建条目——深度处理段无化学除磷主线，除磷归后续批）。
# 【公式注册（D1）】GM-F1~F20 逐条 FormulaSpec+register；expression=四表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构
#   常数（2/60/1000/86400/3600）内联（本文件=units_lib manifest 白名单区）；
#   μ=0.001 Pa·s（20 ℃ 水的动力粘度）与 sin60°=0.86602540（斜管倾角 60°
#   构造常量）按四表条文内联；×86400=流量口径注记（WaterFlow 规范单位
#   m3/s → 药剂耗量/干泥量按 m3/d 口径，GM-F12/F14/F15 同 CC-F10 M2a2
#   先例）；×3600=时换算条文常量（GM-F1 单池 m3/h 口径）；sqrt 经 M1b
#   D4 Name 豁免直接用。DSL 无 ceil：池边长 B（0.5 m 档）/池总高 h_total
#   （0.1 m 档）离散在 compute 收口（步长=参数）。
# 【DSL 单输出导出量】q_design_h（=q1h×n，GM-F11 全厂回流泵 m3/h）与
#   ss_out（=ss_in×(1−removal.gaomidu.ss)，GM-F12 入参）在 compute 以
#   符号算术合成——零字面量、无新工程常数（registry 单输出限制导出面）。
# 【追认口径按表冻结】仅污泥回流型高密度沉淀池（Densadeg 类，ADR-008
#   ③ 逐字）——Actiflo（微砂型）与磁混凝不纳入；GM-F12 干泥量仅计 SS
#   去除项（PAC 水解絮体泥量增量未计入主线——增量系数化归领域专家
#   追认后可补键）。
# 【声明五件】params（range 仅表内有出处带者：q_surface/r_sludge/t_mix/
#   t_floc 四参数）/ports 两口 WATER/removal_refs/norm_refs 双源标记
#   （GB/T 50335-2016+GB 50013-2018+给水排水设计手册）/
#   condition_mappings=()/constraint_refs 五键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_gaomidu"

_GT = (
    "GB/T 50335-2016 §5.4.3（污水再生利用：高密斜管清水区液面负荷；"
    "docs/norms/gaomidu.md 起草表 2026-08-25，待追认）"
)
_GS = (
    "GB 50013-2018 §9.4.24（给水侧同型池成套参数，ADR-008 双源标记；"
    "docs/norms/gaomidu.md 起草表 2026-08-25，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》混合/絮凝 G 值法与斜管沉淀常用值"
    "（docs/norms/gaomidu.md 起草表 2026-08-25，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_M = DimKey.MASS
_C = DimKey.CONCENTRATION

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "GM-F1",
        "q1h = q_design * 3600 / n",
        {"q_design": (_F, "最高时设计流量 m3/s"), "n": (_D, "池数")},
        _D,
        _GT,
    ),
    FormulaSpec(
        "GM-F2",
        "a_incl_req = q1h / q_surface",
        {
            "q1h": (_D, "单池流量 m3/h"),
            "q_surface": (_D, "斜管清水区液面负荷 m3/(m2.h)（参数 q_surface，主控）"),
        },
        _A,
        f"{_GT}；{_GS}",
    ),
    FormulaSpec(
        "GM-F3",
        "b_raw = sqrt(a_incl_req)",
        {"a_incl_req": (_A, "需蓄斜管区面积 m2")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "GM-F4",
        "a_act = B ** 2",
        {"B": (_L, "方形池边长（0.5 m 档 ceil 后）m")},
        _A,
        _HB,
    ),
    FormulaSpec(
        "GM-F5",
        "q_surface_act = q1h / a_act",
        {"q1h": (_D, "单池流量 m3/h"), "a_act": (_A, "单池实取斜管区面积 m2")},
        _D,
        _GT,
    ),
    FormulaSpec(
        "GM-F6",
        "v_mix = q1h * t_mix / 60",
        {"q1h": (_D, "单池流量 m3/h"), "t_mix": (_D, "快速混合停留时间 min（参数 t_mix）")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "GM-F7",
        "v_floc = q1h * t_floc / 60",
        {"q1h": (_D, "单池流量 m3/h"), "t_floc": (_D, "絮凝停留时间 min（参数 t_floc）")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "GM-F8",
        "p_mix = 0.001 * g_mix ** 2 * v_mix / 1000",
        {
            "g_mix": (_D, "快速混合速度梯度 s-1（factor.gaomidu.g_mix）"),
            "v_mix": (_VOL, "快速混合区容积 m3（μ=0.001 Pa·s@20 ℃ 条文内联）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "GM-F9",
        "p_floc = 0.001 * g_floc ** 2 * v_floc / 1000",
        {
            "g_floc": (_D, "絮凝速度梯度 s-1（factor.gaomidu.g_floc）"),
            "v_floc": (_VOL, "絮凝区容积 m3（μ=0.001 Pa·s@20 ℃ 条文内联）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "GM-F10",
        "gt_floc = g_floc * t_floc * 60",
        {"g_floc": (_D, "絮凝速度梯度 s-1"), "t_floc": (_D, "絮凝停留时间 min（参数 t_floc）")},
        _D,
        _HB,
    ),
    FormulaSpec(
        "GM-F11",
        "q_return = r_sludge * q_design_h",
        {
            "r_sludge": (_D, "污泥回流比（参数 r_sludge，浓缩区→快速混合器）"),
            "q_design_h": (_D, "全厂最高时流量 m3/h（=q1h×n 导出量）"),
        },
        _D,
        f"{_GT}；{_GS}",
    ),
    FormulaSpec(
        "GM-F12",
        "s_dry = q_avg_daily * 86400 * (ss_in - ss_out) / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "ss_in": (_C, "进流 SS mg/L"),
            "ss_out": (_C, "出流 SS mg/L（=ss_in×(1−removal.gaomidu.ss)）"),
        },
        _M,
        _HB,
    ),
    FormulaSpec(
        "GM-F13",
        "q_sludge = s_dry / c_sludge",
        {
            "s_dry": (_M, "全厂干泥量 kg/d（仅计 SS 去除项——药剂泥量注记见表）"),
            "c_sludge": (_D, "浓缩区排泥含固率 kg/m3（factor.gaomidu.sludge.concentration）"),
        },
        _VOL,
        _GS,
    ),
    FormulaSpec(
        "GM-F14",
        "m_pac = q_avg_daily * 86400 * dose_pac / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "dose_pac": (_D, "PAC 投加量 mg/L 商品计（factor.gaomidu.dose.pac）"),
        },
        _M,
        _HB,
    ),
    FormulaSpec(
        "GM-F15",
        "m_pam = q_avg_daily * 86400 * dose_pam / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "dose_pam": (_D, "PAM 投加量 mg/L（factor.gaomidu.dose.pam）"),
        },
        _M,
        _HB,
    ),
    FormulaSpec(
        "GM-F16",
        "h_tube_zone = l_tube * 0.86602540",
        {"l_tube": (_L, "斜管长度 m（参数 l_tube，倾角 60° 构造常量 sin60° 内联）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "GM-F17",
        "h_settle = h_clear + h_tube_zone + h_buffer + h_thick",
        {
            "h_clear": (_L, "清水区高度 m（参数 h_clear）"),
            "h_tube_zone": (_L, "斜管区高度 m"),
            "h_buffer": (_L, "斜管下布水区高 m（参数 h_buffer）"),
            "h_thick": (_L, "浓缩泥区高 m（参数 h_thick）"),
        },
        _L,
        f"{_GS}；{_HB}",
    ),
    FormulaSpec(
        "GM-F18",
        "h_total_raw = h_super + h_settle",
        {"h_super": (_L, "超高 m（factor.gaomidu.superheight）"), "h_settle": (_L, "沉淀区总高 m")},
        _L,
        "GB 50014-2021 §6（超高一般要求；docs/norms/gaomidu.md 起草表 2026-08-25，待追认）",
    ),
    FormulaSpec(
        "GM-F19",
        "h_floc_calc = v_floc / a_act",
        {"v_floc": (_VOL, "絮凝区容积 m3"), "a_act": (_A, "单池实取斜管区面积 m2")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "GM-F20",
        "v_concrete = a_act * h_total * n * wall_coef",
        {
            "a_act": (_A, "单池实取斜管区面积 m2"),
            "h_total": (_L, "池总高（0.1 m 档 ceil 后）m"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.gaomidu.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.municipal_gaomidu",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=四表算例 1 逐字（出处 docs/norms/gaomidu.md 参数档/构造参数段）；
        # range 仅四条有出处带参数（surface_load_band 10~20/r_sludge_band
        # 0.03~0.05/t_mix_band 1~2/t_floc_band 8~15），构造参数（池数/斜管
        # 几何/分区高度/取整档）无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0},
            {
                "field_id": "q_surface",
                "dim": "DIMENSIONLESS",
                "default": 15.0,
                "range": {"min": 10.0, "max": 20.0},
            },
            {
                "field_id": "r_sludge",
                "dim": "DIMENSIONLESS",
                "default": 0.04,
                "range": {"min": 0.03, "max": 0.05},
            },
            {
                "field_id": "t_mix",
                "dim": "DIMENSIONLESS",
                "default": 1.5,
                "range": {"min": 1.0, "max": 2.0},
            },
            {
                "field_id": "t_floc",
                "dim": "DIMENSIONLESS",
                "default": 12.0,
                "range": {"min": 8.0, "max": 15.0},
            },
            {"field_id": "l_tube", "dim": "LENGTH", "default": 1.0},
            {"field_id": "h_clear", "dim": "LENGTH", "default": 1.2},
            {"field_id": "h_buffer", "dim": "LENGTH", "default": 1.2},
            {"field_id": "h_thick", "dim": "LENGTH", "default": 2.0},
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.gaomidu.bod5.mod_default",
            "CODCR": "removal.gaomidu.cod.mod_default",
            "SS": "removal.gaomidu.ss.mod_default",
        },
        "norm_refs": [
            "GB/T 50335-2016 §5.4.3（污水再生利用：高密斜管清水区液面负荷）",
            "GB 50013-2018 §9.4.24（给水侧同型池成套参数，ADR-008 双源）",
            "《给水排水设计手册（第 5 册 城镇排水）》混合/絮凝 G 值法与斜管沉淀常用值",
            "docs/norms/gaomidu.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "gaomidu.surface_load_band",
            "gaomidu.r_sludge_band",
            "gaomidu.t_mix_band",
            "gaomidu.t_floc_band",
            "gaomidu.gt_band",
        ],
    }
)
