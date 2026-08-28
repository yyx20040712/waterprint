"""辐流初沉池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  三表起草真源（docs/norms/chuchenchi.md，2026-08-25，数据策略 v2 待追认）+
       data/coefficients 0.2.0/0.2.1 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ CC-F1~F18 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2a2 实装：M2a1 数据先行批的代码落地/M2 正式验收）
#
# 【固定形态】UNIT_ID = "municipal_chuchenchi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=三表算例 1 逐字（n=2/q'=2.3/T=1.2 h/T_sludge=2 d/
#   r1=1.8/r2=0.8/h5=1.5/D 档 0.5 m/长度档 0.1 m）；系数不落本表——
#   v_center/P/i_slope/h_super/h_buf/壁厚系数/四条校核带+排泥周期带全部经
#   factor.chuchenchi.* 键消费（app._unit_params 投影）；去除率经
#   removal.chuchenchi.*.mod_default 键（NH3N/TN/TP 不建条目）。
# 【公式注册（D2）】CC-F1~F18 逐条 FormulaSpec+register；expression=三表
#   公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；结构常数
#   （4/2/3/1000/3600/86400）内联（本文件=units_lib manifest 白名单区）；
#   π 经符号 pi 绑定 math.pi（M1a 惯例）；流量换算 86400=流量口径注记
#   （WaterFlow 规范单位 m3/s → 排泥按 m3/d 口径，CC-F10 同 CS-F7 先例）；
#   sqrt 经 M1b D4 Name 豁免直接用。DSL 无 ceil：池径 D（0.5 m 档）/
#   d_center/h4/h_total（0.1 m 档）离散在 compute 收口（步长=参数）。
# 【追认口径按表冻结】CC-F9 周边双侧出水堰堰圈中心线 D−1（堰长
#   L=2π(D−1)，单侧口径敏感性见三表注记——待领域专家追认）。
# 【DSL 单输出导出量】q1（=q_design/n，CC-F8/F9 的单池秒流量）在 compute
#   以参数化算术合成（零字面量，无新工程常数）。
# 【档位声明（Ruling ④）】池数 n grid=[2,3,4,5,6]（GB 50014 池数≥2 精神+
#   CASS n_pool 先例档，M2-SOL §7 档位补齐，待追认）；档位下限归 grid
#   层承载，compute 只保 n>0 数学有效性。
# 【声明五件】params（range 仅表内有出处带者：q'/T/排泥周期三参数）/
#   ports 两口 WATER+sludge_out SLUDGE 产股口（GOLDEN4a D3——无条件产股，
#   无边也产；nongsuo sup 先例同构）/removal_refs/norm_refs 双源标记
#   （GB 50014-2021+给水排水设计手册）/condition_mappings=()/
#   constraint_refs 五键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "municipal_chuchenchi"

_GB = "GB 50014-2021 §6.5（沉淀池；docs/norms/chuchenchi.md 起草表 2026-08-25，待追认）"
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》初次沉淀池章"
    "（docs/norms/chuchenchi.md 起草表 2026-08-25，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_M = DimKey.MASS
_C = DimKey.CONCENTRATION
_V = DimKey.VELOCITY

# 单位换算常量（GOLDEN4a D3 产股口：排泥工程口径 m³/d、kg/d → SludgeFlow
# 契约口径 m3/s、kg/s——manifest=数值白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "CC-F1",
        "q1h = q_design * 3600 / n",
        {"q_design": (_F, "最高时设计流量 m3/s"), "n": (_D, "池数")},
        _D,
        _GB,
    ),
    FormulaSpec(
        "CC-F2",
        "f_req = q1h / q_prime",
        {"q1h": (_D, "单池流量 m3/h"), "q_prime": (_D, "表面水力负荷 m3/(m2.h)（参数 q_prime）")},
        _A,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "CC-F3",
        "d_raw = sqrt(4 * f_req / pi)",
        {"f_req": (_A, "需蓄面积 m2"), "pi": (_D, "圆周率（math.pi 绑定）")},
        _L,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "CC-F4",
        "f_act = pi * D ** 2 / 4",
        {"pi": (_D, "圆周率（math.pi 绑定）"), "D": (_L, "池径（0.5 m 档 ceil 后）m")},
        _A,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "CC-F5",
        "q_prime_act = q1h / f_act",
        {"q1h": (_D, "单池流量 m3/h"), "f_act": (_A, "实际单池面积 m2")},
        _D,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "CC-F6",
        "h2 = q_prime_act * t_settle",
        {
            "q_prime_act": (_D, "实际表面水力负荷 m3/(m2.h)"),
            "t_settle": (_D, "沉淀时间 h（参数 t_settle）"),
        },
        _L,
        _GB,
    ),
    FormulaSpec(
        "CC-F7",
        "ratio_dh2 = D / h2",
        {"D": (_L, "池径 m"), "h2": (_L, "有效水深 m")},
        _D,
        _HB,
    ),
    FormulaSpec(
        "CC-F8",
        "d_center_raw = sqrt(4 * q1 / (pi * v_center))",
        {
            "q1": (_F, "单池流量 m3/s"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "v_center": (_V, "中心管流速 m/s（factor.chuchenchi.center_velocity）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "CC-F9",
        "q_weir = q1 * 1000 / (2 * pi * (D - 1))",
        {
            "q1": (_F, "单池流量 m3/s"),
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "D": (_L, "池径（0.5 m 档 ceil 后）m"),
        },
        _D,
        f"{_GB}；堰构造口径=周边双侧出水堰（堰长 L=2π(D−1)），待领域专家追认",
    ),
    FormulaSpec(
        "CC-F10",
        "s_dry_1 = q_avg_daily * 86400 * (ss_in - ss_out) / (1000 * n)",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径）"),
            "ss_in": (_C, "进流 SS mg/L"),
            "ss_out": (_C, "出流 SS mg/L（=ss_in×(1−removal.chuchenchi.ss)）"),
            "n": (_D, "池数"),
        },
        _M,
        _GB,
    ),
    FormulaSpec(
        "CC-F11",
        "s_wet_1 = s_dry_1 / ((1 - p_moisture) * 1000)",
        {
            "s_dry_1": (_M, "单池干泥量 kg/d"),
            "p_moisture": (_D, "初沉污泥含水率（factor.chuchenchi.sludge.moisture）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CC-F12",
        "v_need = s_wet_1 * t_sludge",
        {
            "s_wet_1": (_VOL, "单池湿泥量 m3/d"),
            "t_sludge": (_D, "贮泥（排泥）周期 d（参数 t_sludge）"),
        },
        _VOL,
        _GB,
    ),
    FormulaSpec(
        "CC-F13",
        "v1_hopper = pi * h5 / 3 * (r1 ** 2 + r1 * r2 + r2 ** 2)",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "h5": (_L, "泥斗高 m（参数 h5）"),
            "r1": (_L, "泥斗上口半径 m（参数 r1）"),
            "r2": (_L, "泥斗下口半径 m（参数 r2）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CC-F14",
        "h4_raw = i_slope * (D / 2 - r1)",
        {
            "i_slope": (_D, "池底坡度（factor.chuchenchi.bottom_slope）"),
            "D": (_L, "池径 m"),
            "r1": (_L, "泥斗上口半径 m"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "CC-F15",
        "v2_cone = pi * h4 / 3 * ((D / 2) ** 2 + D / 2 * r1 + r1 ** 2)",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "h4": (_L, "池底坡降（0.1 m 档 ceil 后）m"),
            "D": (_L, "池径 m"),
            "r1": (_L, "泥斗上口半径 m"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CC-F16",
        "v_storage = v1_hopper + v2_cone",
        {"v1_hopper": (_VOL, "泥斗容积 m3"), "v2_cone": (_VOL, "池底坡锥台容积 m3")},
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "CC-F17",
        "h_total_raw = h_super + h2 + h_buf + h4 + h5",
        {
            "h_super": (_L, "超高 m（factor.chuchenchi.superheight）"),
            "h2": (_L, "有效水深 m"),
            "h_buf": (_L, "缓冲层 m（factor.chuchenchi.buffer_h3）"),
            "h4": (_L, "池底坡降（ceil 后）m"),
            "h5": (_L, "泥斗高 m（参数 h5）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "CC-F18",
        "v_concrete = pi * (D / 2) ** 2 * h_total * n * wall_coef",
        {
            "pi": (_D, "圆周率（math.pi 绑定）"),
            "D": (_L, "池径（ceil 后）m"),
            "h_total": (_L, "总高（ceil 后）m"),
            "n": (_D, "池数"),
            "wall_coef": (_D, "壁厚系数（factor.chuchenchi.wall_thickness_coef，概算口径）"),
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
        "i18n_key": "units.municipal_chuchenchi",
        "version": "1.0",
        "business_line": "municipal",
        # 默认值=三表算例 1 逐字（出处 docs/norms/chuchenchi.md 参数档）；
        # range 仅三条有出处带参数（surface_load_band 1.5~4.5/
        # retention_band 1.0~2.5/sludge_cycle_band 1~2[data 0.2.1]），
        # 构造参数（r1/r2/h5/取整档）无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 2.0, "grid": [2, 3, 4, 5, 6]},
            {
                "field_id": "q_prime",
                "dim": "DIMENSIONLESS",
                "default": 2.3,
                "range": {"min": 1.5, "max": 4.5},
            },
            {
                "field_id": "t_settle",
                "dim": "DIMENSIONLESS",
                "default": 1.2,
                "range": {"min": 1.0, "max": 2.5},
            },
            {
                "field_id": "t_sludge",
                "dim": "DIMENSIONLESS",
                "default": 2.0,
                "range": {"min": 1.0, "max": 2.0},
            },
            {"field_id": "r1", "dim": "LENGTH", "default": 1.8},
            {"field_id": "r2", "dim": "LENGTH", "default": 0.8},
            {"field_id": "h5", "dim": "LENGTH", "default": 1.5},
            {"field_id": "dia_disc_step", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
            # GOLDEN4a D3 产股口（2026-08-28）：无条件产股（无边也产——
            # nongsuo sup 先例同构）；产股三量=CC-F10/F11 全厂口径投影
            # （ds=s_dry_1×n——hebing 注入 ds_primary 链路同源；moisture=
            # factor.chuchenchi.sludge.moisture 0.96，与 sludge_hebing
            # p_primary 默认同源声明）。
            {"port_id": "sludge_out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        "removal_refs": {
            "BOD5": "removal.chuchenchi.bod5.mod_default",
            "CODCR": "removal.chuchenchi.cod.mod_default",
            "SS": "removal.chuchenchi.ss.mod_default",
        },
        "norm_refs": [
            "GB 50014-2021 §6.5（沉淀池）",
            "《给水排水设计手册（第 5 册 城镇排水）》初次沉淀池章",
            "docs/norms/chuchenchi.md（2026-08-25 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "chuchenchi.surface_load_band",
            "chuchenchi.depth_band",
            "chuchenchi.ratio_dh2_band",
            "chuchenchi.weir_load",
            "chuchenchi.sludge_cycle_band",
        ],
    }
)
