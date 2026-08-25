"""紫外消毒清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  四表起草真源（docs/norms/ziwai.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.3.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ ZW-F1~F13 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2b2 实装：M2b1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_ziwai"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=四表算例 1 逐字（n_channel=2 条并联/v_channel=
#   0.4 m/s/b_c=1.2 m/每模块 8 支灯 4×2/模块长 0.6/模块高 0.5/稳流段
#   1.2；h_w 档 0.1 m）；系数不落本表——渠内流速/有效接触时间两校核
#   带+设计剂量+单灯处理量+灯管老化系数+进水粪大肠设计值+log 去除
#   级数+超高+壁厚系数+高程水损全部经 factor.ziwai.* 键消费
#   （app._unit_params 投影）；去除率经 removal.ziwai.*.mod_default 键
#   （物理消毒无去除，全 0.0；NH3N/TN/TP 不建条目）。设计剂量 D=30
#   mJ/cm² 与穿透率 T254 档为选型参数（dose/t254_band 键）——剂量校核
#   语义=选型剂量≥设计剂量（ZW-F4 概算链承载，无独立公式）。
# 【公式注册（D1）】ZW-F1~F13 逐条 FormulaSpec+register；expression=四表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构
#   常数（2/10/3600）内联（本文件=units_lib manifest 白名单区）；×3600=
#   时换算条文常量（ZW-F4 q_design m3/s→m3/h 口径，四表 q_design_h
#   等价形态）。DSL 无 ceil：渠内水深 h_w（0.1 m 档）/灯管数 n_lamp
#   （整支）/模块数 n_module（整模块）/每渠串列 n_module_series 在
#   compute 收口。
# 【追认口径按表冻结（R1 微修后口径）】双渠并联同时运行各半过流+
#   超越/模块切换备用——灯组分置两渠（ZW-F5/F6 模块分置×n_channel）；
#   单渠事故工况 0.78 m/s 超 velocity_band.max=0.6 为表内注记非运行时
#   警告（运行时只校核实际过流态 v_channel_act）。
# 【声明五件】params（range 仅表内有出处带者：v_channel 一参数）/
#   ports 两口 WATER/removal_refs（全 0.0 键同引用）/norm_refs 双源
#   标记（GB 50014-2021+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 两键（h_submerge≥0 淹没校核为结果对常数零比较、
#   无 data 包键——仅 compute warnings 承载）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_ziwai"

_GB = (
    "GB 50014-2021 消毒章节（紫外线消毒一般规定；"
    "docs/norms/ziwai.md 起草表 2026-08-25，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》紫外剂量选档/灯管概算/渠道设计常用值"
    "（docs/norms/ziwai.md 起草表 2026-08-25，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_VOL = DimKey.VOLUME
_V = DimKey.VELOCITY
_T = DimKey.TIME

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "ZW-F1",
        "q_c = q_design / n_channel",
        {
            "q_design": (_F, "最高时设计流量 m3/s"),
            "n_channel": (_D, "渠道数（参数 n_channel，双渠并联各半过流——R1 口径）"),
        },
        _F,
        _HB,
    ),
    FormulaSpec(
        "ZW-F2",
        "h_w_raw = q_c / (v_channel * b_c)",
        {
            "q_c": (_F, "单渠流量 m3/s"),
            "v_channel": (_V, "渠内流速 m/s（参数 v_channel）"),
            "b_c": (_L, "渠宽 m（参数 b_c，构造）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "ZW-F3",
        "v_channel_act = q_c / (b_c * h_w)",
        {
            "q_c": (_F, "单渠流量 m3/s"),
            "b_c": (_L, "渠宽 m"),
            "h_w": (_L, "渠内水深（0.1 m 档 ceil 后）m"),
        },
        _V,
        _HB,
    ),
    FormulaSpec(
        "ZW-F4",
        "n_lamp_raw = q_design * 3600 / q_per_lamp / f_aging",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×3600 转 m3/h 口径，四表 q_design_h 等价形态）"),
            "q_per_lamp": (
                _D,
                "单灯处理量 m3/h/支（factor.ziwai.q_per_lamp，新灯 T254=60% 概算锚）",
            ),
            "f_aging": (_D, "灯管老化系数（factor.ziwai.f_aging，寿命末期输出保持比）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "ZW-F5",
        "n_module_raw = n_lamp / n_lamp_module",
        {
            "n_lamp": (_D, "灯管数（整支 ceil 后）"),
            "n_lamp_module": (_D, "每模块灯管数（参数 n_lamp_module，4×2 矩阵构造）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "ZW-F6",
        "n_module_series = n_module / n_channel",
        {
            "n_module": (_D, "模块数（整模块 ceil 后）"),
            "n_channel": (_D, "渠道数（灯组分置两渠口径）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "ZW-F7",
        "l_lamp_zone = n_module_series * l_module",
        {
            "n_module_series": (_D, "每渠串列模块数（ceil 后）"),
            "l_module": (_L, "模块长 m（参数 l_module，构造）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "ZW-F8",
        "l_channel = 2 * l_stab + l_lamp_zone",
        {
            "l_stab": (_L, "进/出水稳流段长 m（参数 l_stab，构造）"),
            "l_lamp_zone": (_L, "灯区长度 m"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "ZW-F9",
        "t_exp = b_c * h_w * l_lamp_zone / q_c",
        {
            "b_c": (_L, "渠宽 m"),
            "h_w": (_L, "渠内水深 m"),
            "l_lamp_zone": (_L, "灯区长度 m"),
            "q_c": (_F, "单渠流量 m3/s"),
        },
        _T,
        _HB,
    ),
    FormulaSpec(
        "ZW-F10",
        "c_fecal_out = c_fecal_in / 10 ** n_log",
        {
            "c_fecal_in": (_D, "进水粪大肠 个/L（factor.ziwai.fecal.c_in_design，设计假定）"),
            "n_log": (_D, "log 去除对数级（factor.ziwai.fecal.log_removal）"),
        },
        _D,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "ZW-F11",
        "h_submerge = h_w - h_module",
        {"h_w": (_L, "渠内水深 m"), "h_module": (_L, "模块高 m（参数 h_module，构造）")},
        _L,
        _HB,
    ),
    FormulaSpec(
        "ZW-F12",
        "h_channel = h_super + h_w",
        {"h_super": (_L, "渠超高 m（factor.ziwai.superheight）"), "h_w": (_L, "渠内水深 m")},
        _L,
        _GB,
    ),
    FormulaSpec(
        "ZW-F13",
        "v_concrete = l_channel * b_c * h_channel * n_channel * wall_coef",
        {
            "l_channel": (_L, "渠长 m"),
            "b_c": (_L, "渠宽 m"),
            "h_channel": (_L, "渠总高 m"),
            "n_channel": (_D, "渠道数"),
            "wall_coef": (_D, "壁厚系数（factor.ziwai.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.municipal_ziwai",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=四表算例 1 逐字（出处 docs/norms/ziwai.md 参数档/构造参数段）；
        # range 仅一条有出处带参数（velocity_band 0.3~0.6），构造参数
        # （渠道数/渠宽/模块几何/稳流段/取整档）无范围来源不设
        "params": [
            {"field_id": "n_channel", "dim": "DIMENSIONLESS", "default": 2.0},
            {
                "field_id": "v_channel",
                "dim": "VELOCITY",
                "default": 0.4,
                "range": {"min": 0.3, "max": 0.6},
            },
            {"field_id": "b_c", "dim": "LENGTH", "default": 1.2},
            {"field_id": "n_lamp_module", "dim": "DIMENSIONLESS", "default": 8.0},
            {"field_id": "l_module", "dim": "LENGTH", "default": 0.6},
            {"field_id": "l_stab", "dim": "LENGTH", "default": 1.2},
            {"field_id": "h_module", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.ziwai.bod5.mod_default",
            "CODCR": "removal.ziwai.cod.mod_default",
            "SS": "removal.ziwai.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 消毒章节（紫外线消毒一般规定）",
            "《给水排水设计手册（第 5 册 城镇排水）》紫外剂量选档/灯管概算/渠道设计常用值",
            "docs/norms/ziwai.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "ziwai.velocity_band",
            "ziwai.t_exp_band",
        ],
    }
)
