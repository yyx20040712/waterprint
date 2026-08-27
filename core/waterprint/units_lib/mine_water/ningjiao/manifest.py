"""混凝反应池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_ningjiao.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KN-F1~F15 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_ningjiao"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=2 池/t_mix=1.0 min/t_seed=
#   2.0 min/t_floc=3.0 min/t_ripen=1.5 min/h2=3.0 m/ratio_lb=1.2；
#   B 0.5 m 档）；系数不落本表——四区停留四带+四 G 值+GT 带+水深带+
#   分区长宽比带+PAC/PAM/磁种投加+超高+壁厚系数+高程水损全部经
#   factor.mine_ningjiao.* 键消费（app._unit_params 线感知投影，
#   mine_ 限定）；去除率经 removal.mine_ningjiao.{ss,cod}.mod_default
#   键（反应无分离显式 0.0 穿流——去除挂下游分离单元，与市政线把
#   混合絮凝沉淀并入 gaomidu 一体单元的键挂口径互为镜像，表内
#   追认点 7；BOD5 全线不建键）。
# 【公式注册（D1）】KN-F1~F15 逐条 FormulaSpec+register；expression=
#   表公式串转受限 DSL——data 包系数（g_mix/g_seed/g_floc/g_ripen/
#   dose_pac/dose_pam/dose_seed）一律符号绑定（零系数字面量）；
#   结构常数内联（本文件=units_lib manifest 白名单区）：μ=0.001
#   Pa·s（20 ℃ 水动力粘度，表头物理条文常量）、/1000（W→kW 与
#   mg/L→kg/d 折算）、/60（min→h）、×3600（m3/s→m³/h 流量口径
#   注记——表内 q1=q_design_h/n 展开内联，单输出导出量 q1 不单列
#   公式，市政 CC-F1 q1h 先例的展开形态）、×86400（药剂耗量按
#   平均日 m3/d 口径）；π 不入本组公式（矩形分区）；sqrt 直接用。
#   DSL 无 ceil：池宽 B（0.5 m 档）离散在 compute 收口（步长=参数）。
# 【泛式展开】KN-F6（p_i）/KN-F7（a_i）/KN-F9（l_i）为表内下标泛
#   式——各注册一条 DSL 公式（符号 g_i/v_i/a_i/b 为合法名），compute
#   四次 apply 绑不同区值（p1~p4/a1~a4/l1~l4）；formula_ids 每号
#   一次（表号与 DSL 号一一对应）。
# 【声明五件】params（range 仅表内有出处带者：四区停留/h2/ratio_lb
#   六参数；池数 n=2 构造参数无档位来源不设 grid）/ports 两口 WATER/
#   removal_refs 双指标键/norm_refs 双源标记（GB/T 41019-2021+给水
#   排水设计手册）/condition_mappings=()/constraint_refs 七键。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_ningjiao"

_GB = (
    "GB/T 41019-2021（矿井水处理工艺——混凝路线与药剂，条号待核对；"
    "docs/norms/mine_water_ningjiao.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 3 册 城镇给水）》混合/絮凝 G 值法"
    "（P=μG²V）与 GT 校核常用带（docs/norms/mine_water_ningjiao.md"
    " 起草表 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KN-F1",
        "v1 = q_design * 3600 * t_mix / (60 * n)",
        {
            "q_design": (
                _F,
                "最高时设计流量 m3/s（×3600 转 m3/h 口径——表内 q1=q_design_h/n 展开内联）",
            ),
            "t_mix": (_D, "混合区停留 min（参数 t_mix，÷60 折 h 入式）"),
            "n": (_D, "池数"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KN-F2",
        "v2 = q_design * 3600 * t_seed / (60 * n)",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×3600 转 m3/h 口径）"),
            "t_seed": (_D, "磁种混合区停留 min（参数 t_seed）"),
            "n": (_D, "池数"),
        },
        _VOL,
        _GB,
    ),
    FormulaSpec(
        "KN-F3",
        "v3 = q_design * 3600 * t_floc / (60 * n)",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×3600 转 m3/h 口径）"),
            "t_floc": (_D, "絮凝区停留 min（参数 t_floc）"),
            "n": (_D, "池数"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KN-F4",
        "v4 = q_design * 3600 * t_ripen / (60 * n)",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×3600 转 m3/h 口径）"),
            "t_ripen": (_D, "熟化区停留 min（参数 t_ripen）"),
            "n": (_D, "池数"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KN-F5",
        "t_total = (v1 + v2 + v3 + v4) * 60 * n / (q_design * 3600)",
        {
            "v1": (_VOL, "混合区容积 m3"),
            "v2": (_VOL, "磁种混合区容积 m3"),
            "v3": (_VOL, "絮凝区容积 m3"),
            "v4": (_VOL, "熟化区容积 m3"),
            "q_design": (_F, "最高时设计流量 m3/s（×3600 转 m3/h 口径）"),
            "n": (_D, "池数"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KN-F6",
        "p_i = 0.001 * g_i ** 2 * v_i / 1000",
        {
            "g_i": (_D, "各区速度梯度 s⁻¹（g_mix/g_seed/g_floc/g_ripen 四键，四次求值）"),
            "v_i": (_VOL, "各区容积 m3（v1~v4 四次求值）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KN-F7",
        "a_i = v_i / h2",
        {
            "v_i": (_VOL, "各区容积 m3（v1~v4 四次求值）"),
            "h2": (_L, "有效水深 m（参数 h2）"),
        },
        _A,
        _HB,
    ),
    FormulaSpec(
        "KN-F8",
        "b_raw = sqrt(a_max / ratio_lb)",
        {
            "a_max": (_A, "最大区面积 m2（絮凝区 a3）"),
            "ratio_lb": (_D, "最大区长宽比（参数 ratio_lb，即 cell_ratio_lb 取值）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KN-F9",
        "l_i = a_i / b",
        {
            "a_i": (_A, "各区面积 m2（a1~a4 四次求值）"),
            "b": (_L, "池宽（0.5 m 档 ceil 后）m（构造值不取整，狭长分格）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KN-F10",
        (
            "gt_total = g_mix * t_mix * 60 + g_seed * t_seed * 60"
            " + g_floc * t_floc * 60 + g_ripen * t_ripen * 60"
        ),
        {
            "g_mix": (_D, "混合区速度梯度 s⁻¹（factor.mine_ningjiao.g_mix）"),
            "t_mix": (_D, "混合区停留 min（参数 t_mix）"),
            "g_seed": (_D, "磁种混合区速度梯度 s⁻¹（factor.mine_ningjiao.g_seed）"),
            "t_seed": (_D, "磁种混合区停留 min（参数 t_seed）"),
            "g_floc": (_D, "絮凝区速度梯度 s⁻¹（factor.mine_ningjiao.g_floc）"),
            "t_floc": (_D, "絮凝区停留 min（参数 t_floc）"),
            "g_ripen": (_D, "熟化区速度梯度 s⁻¹（factor.mine_ningjiao.g_ripen）"),
            "t_ripen": (_D, "熟化区停留 min（参数 t_ripen）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KN-F11",
        "m_pac = q_avg_daily * 86400 * dose_pac / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径——药剂耗量按平均日）"),
            "dose_pac": (_D, "PAC 投加 mg/L（factor.mine_ningjiao.dose.pac）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KN-F12",
        "m_pam = q_avg_daily * 86400 * dose_pam / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "dose_pam": (_D, "PAM 助凝投加 mg/L（factor.mine_ningjiao.dose.pam）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KN-F13",
        "m_seed = q_avg_daily * 86400 * dose_seed / 1000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "dose_seed": (
                _D,
                "磁种投加 mg/L（factor.mine_ningjiao.seed.dose，回收循环见 cifenli 表）",
            ),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "KN-F14",
        "h_total = h_super + h2",
        {
            "h_super": (_L, "超高 m（factor.mine_ningjiao.superheight）"),
            "h2": (_L, "有效水深 m（参数 h2）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KN-F15",
        "v_concrete = (v1 + v2 + v3 + v4) / h2 * h_total * n * wall_coef",
        {
            "v1": (_VOL, "混合区容积 m3"),
            "v2": (_VOL, "磁种混合区容积 m3"),
            "v3": (_VOL, "絮凝区容积 m3"),
            "v4": (_VOL, "熟化区容积 m3"),
            "h2": (_L, "有效水深 m"),
            "h_total": (_L, "池总高 m"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.mine_ningjiao.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.mine_water_ningjiao",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_ningjiao.md 参数档）；
        # range 仅六条有出处带参数（四区停留四带 0.5~2/1~3/2~4/1~2 min、
        # depth_band 2.5~4.0/cell_ratio_lb_band 0.8~1.5），池数/取整档
        # 无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0},
            {
                "field_id": "t_mix",
                "dim": "DIMENSIONLESS",
                "default": 1.0,
                "range": {"min": 0.5, "max": 2.0},
            },
            {
                "field_id": "t_seed",
                "dim": "DIMENSIONLESS",
                "default": 2.0,
                "range": {"min": 1.0, "max": 3.0},
            },
            {
                "field_id": "t_floc",
                "dim": "DIMENSIONLESS",
                "default": 3.0,
                "range": {"min": 2.0, "max": 4.0},
            },
            {
                "field_id": "t_ripen",
                "dim": "DIMENSIONLESS",
                "default": 1.5,
                "range": {"min": 1.0, "max": 2.0},
            },
            {
                "field_id": "h2",
                "dim": "LENGTH",
                "default": 3.0,
                "range": {"min": 2.5, "max": 4.0},
            },
            {
                "field_id": "ratio_lb",
                "dim": "DIMENSIONLESS",
                "default": 1.2,
                "range": {"min": 0.8, "max": 1.5},
            },
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_ningjiao.ss.mod_default",
            "CODCR": "removal.mine_ningjiao.cod.mod_default",
        },
        "norm_refs": [
            "GB/T 41019-2021（矿井水处理工艺——混凝路线与药剂，条号待核对）",
            "《给水排水设计手册（第 3 册 城镇给水）》混合/絮凝 G 值法（P=μG²V）与 GT 校核常用带",
            "docs/norms/mine_water_ningjiao.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_ningjiao.gt_band",
            "mine_water_ningjiao.t_mix_band",
            "mine_water_ningjiao.t_seed_band",
            "mine_water_ningjiao.t_floc_band",
            "mine_water_ningjiao.t_ripen_band",
            "mine_water_ningjiao.depth_band",
            "mine_water_ningjiao.cell_ratio_lb_band",
        ],
    }
)
