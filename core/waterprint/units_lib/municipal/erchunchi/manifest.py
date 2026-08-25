"""辐流二沉池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表起草真源（docs/norms/erchunchi.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.2.0/0.2.1 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ EC-F1~F15 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收；
#   公式路线 = ADR-008 ②逐字落地：清水表面负荷主控+固体负荷校核）
#
# 【固定形态】UNIT_ID = "municipal_erchunchi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 逐字（n=2/q_nom=1.2/X=4000[联动 AAO]/
#   R=1.0[联动 AAO]/h2=3.0/r_pit=1.0/D 档 0.5 m/长度档 0.1 m）；系数不落
#   本表——G_max/v_center/i_slope/h_super/h_buf/壁厚系数/清水负荷带/堰
#   荷限/水深带全部经 factor.erchunchi.* 键消费（Xr 带/HRT 带为 0.2.1
#   前置键）；去除率经 removal.erchunchi.*.mod_default 键（NH3N/TN/TP
#   不建条目）。
# 【公式注册（D2）】EC-F1~F15 逐条 FormulaSpec+register；expression=三表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构常数
#   （4/2/24/1000/3600）内联（本文件=units_lib manifest 白名单区）；π 经
#   符号 pi 绑定 math.pi（M1a 惯例）；max 为白名单函数经 M1b D4 Name 豁免
#   直接用（EC-F5 主控面积取大）。DSL 无 ceil：池径 D（0.5 m 档）/
#   d_center/h4/h_total（0.1 m 档）离散在 compute 收口（步长=参数）。
# 【追认口径按表冻结】EC-F11 周边双侧出水堰堰圈取 D（堰长 L=2πD；与
#   chuchenchi 表取 D−1 口径不对称系起草取舍，互换不翻转合格性——
#   待领域专家追认）；EC-F3/F10 与 AAO 表回流比/MLSS 联动（三表注记
#   联动 factor.aao.r_external_band——各包独立声明同值参数）。
# 【DSL 单输出导出量】q1（=q_design/n 清水口径单池秒流量）、v_check
#   （=a_act×h2 校核容积）/t_hrt（=v_check/q1h 校核 HRT）/q_return_sludge
#   （=r_external×q1h 回流污泥量）在 compute 以符号算术合成（零字面量）。
# 【档位声明（Ruling ④）】池数 n grid=[2,3,4,5,6]（GB 50014 池数≥2 精神+
#   CASS n_pool 先例档，M2-SOL §7 档位补齐，待追认）；档位下限归 grid
#   层承载，compute 只保 n>0 数学有效性。
# 【声明五件】params（range 仅三条有出处带参数：q_nom/h2/r_external）/
#   ports 两口 WATER/removal_refs/norm_refs 双源标记（GB 50014-2021+
#   给水排水设计手册）/condition_mappings=()/constraint_refs 六键
#   （含 0.2.1 两带键）。
# ══════════════════════════════════════════════════════════════════

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_erchunchi"

_GB = "GB 50014-2021 表 7.5.1+§7.6.15/§7.6.16（docs/norms/erchunchi.md 起草表 2026-08-25，待追认）"
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》"
    "（docs/norms/erchunchi.md 起草表 2026-08-25，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_M = DimKey.MASS
_C = DimKey.CONCENTRATION
_V = DimKey.VELOCITY

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "EC-F1",
        "q1h = q_design * 3600 / n",
        {"q_design": (_F, "最高时设计流量 m3/s（清水口径，不含回流）"), "n": (_D, "池数")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "EC-F2",
        "a_q = q1h / q_nom",
        {"q1h": (_D, "单池流量 m3/h"), "q_nom": (_D, "名义清水表面负荷 m3/(m2.h)（参数 q_nom）")},
        _A,
        _GB,
    ),
    FormulaSpec(
        "EC-F3",
        "m_solid = (1 + r_external) * q1h * 24 * x_mlss / 1000",
        {
            "r_external": (_D, "外回流比（参数 r_external，联动 AAO 表）"),
            "q1h": (_D, "单池流量 m3/h"),
            "x_mlss": (_C, "MLSS mg/L（参数 x_mlss，联动 AAO 表）"),
        },
        _M,
        _GB,
    ),
    FormulaSpec(
        "EC-F4",
        "a_solid = m_solid / g_max",
        {
            "m_solid": (_M, "单池固体负荷 kg/d"),
            "g_max": (_D, "固体面积负荷上限 kg/(m2.d)（factor.erchunchi.solid_load.center_inlet）"),
        },
        _A,
        _GB,
    ),
    FormulaSpec(
        "EC-F5",
        "a_tank = max(a_q, a_solid)",
        {"a_q": (_A, "清水负荷需蓄面积 m2"), "a_solid": (_A, "固体负荷需蓄面积 m2")},
        _A,
        "GB 50014-2021 表 7.5.1 + §7.6.15/§7.6.16（清水负荷与固体负荷双控取大）",
    ),
    FormulaSpec(
        "EC-F6",
        "d_raw = sqrt(4 * a_tank / pi)",
        {"a_tank": (_A, "主控面积 m2"), "pi": (_D, "圆周率（math.pi 绑定）")},
        _L,
        _GB,
    ),
    FormulaSpec(
        "EC-F7",
        "a_act = pi * D ** 2 / 4",
        {"pi": (_D, "圆周率（math.pi 绑定）"), "D": (_L, "池径（0.5 m 档 ceil 后）m")},
        _A,
        _GB,
    ),
    FormulaSpec(
        "EC-F8",
        "q_act = q1h / a_act",
        {"q1h": (_D, "单池流量 m3/h"), "a_act": (_A, "实际单池面积 m2")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "EC-F9",
        "g_act = m_solid / a_act",
        {"m_solid": (_M, "单池固体负荷 kg/d"), "a_act": (_A, "实际单池面积 m2")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "EC-F10",
        "x_r = x_mlss * (1 + r_external) / r_external",
        {"x_mlss": (_C, "MLSS mg/L"), "r_external": (_D, "外回流比")},
        _C,
        _HB,
    ),
    FormulaSpec(
        "EC-F11",
        "q_weir = q1 * 1000 / (2 * pi * D)",
        {
            "q1": (_F, "单池流量 m3/s"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "D": (_L, "池径（0.5 m 档 ceil 后）m"),
        },
        _D,
        "GB 50014-2021（沉淀池堰负荷，二沉档）；堰构造口径=周边双侧出水堰"
        "（堰长 L=2πD），待领域专家追认",
    ),
    FormulaSpec(
        "EC-F12",
        "d_center_raw = sqrt(4 * (1 + r_external) * q1 / (pi * v_center))",
        {
            "r_external": (_D, "外回流比（含回流流量口径）"),
            "q1": (_F, "单池流量 m3/s"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "v_center": (_V, "中心配水筒流速 m/s（factor.erchunchi.center_velocity）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "EC-F13",
        "h4_raw = i_slope * (D / 2 - r_pit)",
        {
            "i_slope": (_D, "池底坡度（factor.erchunchi.bottom_slope）"),
            "D": (_L, "池径 m"),
            "r_pit": (_L, "中心配水井半径 m（参数 r_pit）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "EC-F14",
        "h_total_raw = h_super + h2 + h_buf + h4",
        {
            "h_super": (_L, "超高 m（factor.erchunchi.superheight）"),
            "h2": (_L, "池边有效水深 m（参数 h2）"),
            "h_buf": (_L, "缓冲层 m（factor.erchunchi.buffer_h3）"),
            "h4": (_L, "池底坡降（0.1 m 档 ceil 后）m"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "EC-F15",
        "v_concrete = pi * (D / 2) ** 2 * h_total * n * wall_coef",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "D": (_L, "池径（ceil 后）m"),
            "h_total": (_L, "总高（ceil 后）m"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.erchunchi.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.municipal_erchunchi",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/erchunchi.md 参数档/算例输入行；
        # x_mlss/r_external 与 AAO 表联动同值——各包独立声明）；range 仅三条
        # 有出处带参数（surface_load_band 0.6~1.5/depth_band 2.5~3.5/
        # r_external_band 0.5~1.0[联动 AAO 带出处]），构造参数与取整档不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2, 3, 4, 5, 6]},
            {
                "field_id": "q_nom",
                "dim": "DIMENSIONLESS",
                "default": 1.2,
                "range": {"min": 0.6, "max": 1.5},
            },
            {"field_id": "x_mlss", "dim": "CONCENTRATION", "default": 4000.0},
            {
                "field_id": "r_external",
                "dim": "DIMENSIONLESS",
                "default": 1.0,
                "range": {"min": 0.5, "max": 1.0},
            },
            {
                "field_id": "h2",
                "dim": "LENGTH",
                "default": 3.0,
                "range": {"min": 2.5, "max": 3.5},
            },
            {"field_id": "r_pit", "dim": "LENGTH", "default": 1.0},
            {"field_id": "dia_disc_step", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.erchunchi.bod5.mod_default",
            "CODCR": "removal.erchunchi.cod.mod_default",
            "SS": "removal.erchunchi.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 表 7.5.1（清水表面负荷）+§7.6.15/§7.6.16（固体面积负荷）",
            "《给水排水设计手册（第 5 册 城镇排水）》二沉池几何/堰负荷/回流污泥浓度常用值",
            "docs/norms/erchunchi.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "erchunchi.surface_load_band",
            "erchunchi.solid_load",
            "erchunchi.weir_load",
            "erchunchi.depth_band",
            "erchunchi.x_r_band",
            "erchunchi.hrt_band",
        ],
    }
)
