"""污泥消化清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/sludge_xiaohua.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.6.0 键名（factor.xiaohua.* 裸短名 13 键）
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ XH-F1~XH-F11 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3b2 实装：M3b1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "sludge_xiaohua"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（t_digest=20 d 消化时间/
#   n=2 池/eta_vs=0.45 VS 降解率/r_biogas=0.9 m³/kgVS 产气率）；
#   系数不落本表——消化时间带/温度/挥发分占比/降解带/产气带/负荷带/
#   高径比/壁厚/高程水损共 13 键全经 factor.xiaohua.*（裸短名投影）；
#   removal_refs 全空（VS 降解走泥量减量链不走水质去除键）。
# 【符号统一（M3b1 移交顺改）】DSL/参数面 t_digest=消化时间（d，
#   XH-F2 入参）；温度经参数 t_digest_temp 承载（默认 35 ℃ 中温档
#   ——UF-09 未裁前的参数面口径，表内注记三处在册；v1 温度不进
#   DSL 公式[恒 35 档]，factor.xiaohua.temp 键登记不消费——高温
#   55 档归追认/设备批）。
# 【公式注册（D1）】XH-F1~XH-F11 逐条 FormulaSpec+register；expression=
#   表公式串逐字（消化减量 DS 守恒链 XH-F7~F9——降解 VS 以沼气
#   离开系统+出泥三量链联立）；表串内联 3.14159265 经符号 pi 绑
#   math.pi；1000 为 kg-t 换算常量、0.33333333 为 1/3 指数内联
#   常量（池径立方根式——表串原文）。
# 【DSL 收口】池径 0.5 m 档向上取整不入 DSL（SIDE_DISC_STEP 模块
#   常量——本文件=数值白名单区，compute 收口 ceil）。
# 【单位换算（实装面）】表公式全按工程口径 m³/d、kg/d；出入流
#   SludgeFlow 契约口径——SECS_PER_DAY 模块常量由 compute 消费。
# 【声明五件】params（t_digest/eta_vs/r_biogas 三参数带=同名 factor
#   带键逐字；n 池数 grid [2,3,4]——nongsuo 同口径；t_digest_temp
#   range 33~37=中温档表参数档逐字[UF-09 承载注记]）/ports 两口
#   SLUDGE/removal_refs 空/norm_refs 双源标记/condition_mappings=()/
#   constraint_refs 四键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "sludge_xiaohua"

_GB = (
    "GB 50014-2021 §8（污泥章——消化时间/挥发分降解率/产气率，条号待"
    "核对；docs/norms/sludge_xiaohua.md 起草表 2026-08-27，待追认）"
)
_HB5 = (
    "《给水排水设计手册（第 5 册 城镇排水）》污泥消化章（中温消化参数"
    "带/沼气产率/池型构造常用值；docs/norms/sludge_xiaohua.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS

# 单位换算常量（工程口径 m³/d、kg/d ↔ 契约口径 m3/s、kg/s）与构造档
# 步长（池径 0.5 m 档向上取整——表公式表头注记口径；manifest=数值
# 白名单区，compute 零字面量消费）。
SECS_PER_DAY: Final[float] = 86400.0
SIDE_DISC_STEP: Final[float] = 0.5

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "XH-F1",
        "w_vs = ds_in * f_vs",
        {
            "ds_in": (_D, "入流干固体量 kg/d（nongsuo 底流出流实值）"),
            "f_vs": (_D, "进泥挥发分占 DS 比（factor.xiaohua.f_vs）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F2",
        "v_total = q_wet * t_digest",
        {
            "q_wet": (_D, "入流湿泥量 m³/d"),
            "t_digest": (_D, "消化时间 d（参数 t_digest）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "XH-F3",
        "v_single = v_total / n",
        {
            "v_total": (_D, "消化池总容积 m³（XH-F2）"),
            "n": (_D, "池数（参数 n，≥2）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F4",
        "w_vs_deg = w_vs * eta_vs",
        {
            "w_vs": (_D, "进泥挥发分 kgVS/d（XH-F1）"),
            "eta_vs": (_D, "挥发分降解率（参数 eta_vs）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "XH-F5",
        "v_biogas = w_vs_deg * r_biogas",
        {
            "w_vs_deg": (_D, "降解挥发分 kgVS/d（XH-F4）"),
            "r_biogas": (_D, "产气率 m³/kgVS（参数 r_biogas）"),
        },
        _D,
        _GB,
    ),
    FormulaSpec(
        "XH-F6",
        "l_vs = w_vs / v_total",
        {
            "w_vs": (_D, "进泥挥发分 kgVS/d（XH-F1）"),
            "v_total": (_D, "消化池总容积 m³（XH-F2）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F7",
        "ds_out = ds_in - w_vs_deg",
        {
            "ds_in": (_D, "入流干固体量 kg/d"),
            "w_vs_deg": (_D, "降解挥发分 kgVS/d（XH-F4——以沼气离开系统）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F8",
        "q_out = q_wet - w_vs_deg / 1000",
        {
            "q_wet": (_D, "入流湿泥量 m³/d"),
            "w_vs_deg": (_D, "降解挥发分 kgVS/d（ρ≈1000 kg/m³ 体积折减）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F9",
        "p_out = 1 - ds_out / (q_out * 1000)",
        {
            "ds_out": (_D, "出泥干固体量 kg/d（XH-F7）"),
            "q_out": (_D, "出泥体积 m³/d（XH-F8）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F10",
        "d_raw = (4 * v_single / (pi * r_dh)) ** 0.33333333",
        {
            "v_single": (_D, "单池容积 m³（XH-F3）"),
            "pi": (_D, "圆周率（math.pi 绑定，表内联 3.14159265 等价形态）"),
            "r_dh": (_D, "圆柱高径比 H/D（factor.xiaohua.ratio_dh）"),
        },
        _D,
        _HB5,
    ),
    FormulaSpec(
        "XH-F11",
        "v_concrete = v_total * wall_coef",
        {
            "v_total": (_D, "消化池总容积 m³（XH-F2）"),
            "wall_coef": (
                _D,
                "壁厚系数（factor.xiaohua.wall_thickness_coef——含底板/保温构造概算）",
            ),
        },
        _D,
        _HB5,
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.sludge_xiaohua",
        "version": "1.0",
        "business_line": "sludge",
        # 默认值=表主算例逐字（出处 docs/norms/sludge_xiaohua.md 参数档）；
        # t_digest/eta_vs/r_biogas 三参数带=同名 factor 带键逐字；n 池数
        # grid=≥2 构造冗余口径（nongsuo 同型）；t_digest_temp range=
        # 中温 33~37 档（表参数档逐字——UF-09 参数承载注记）
        "params": [
            {
                "field_id": "t_digest",
                "dim": "DIMENSIONLESS",
                "default": 20.0,
                "range": {"min": 15.0, "max": 30.0},
            },
            {
                "field_id": "n",
                "dim": "DIMENSIONLESS",
                "default": 2.0,
                "grid": [2.0, 3.0, 4.0],
            },
            {
                "field_id": "t_digest_temp",
                "dim": "DIMENSIONLESS",
                "default": 35.0,
                "range": {"min": 33.0, "max": 37.0},
            },
            {
                "field_id": "eta_vs",
                "dim": "DIMENSIONLESS",
                "default": 0.45,
                "range": {"min": 0.3, "max": 0.6},
            },
            {
                "field_id": "r_biogas",
                "dim": "DIMENSIONLESS",
                "default": 0.9,
                "range": {"min": 0.8, "max": 1.1},
            },
        ],
        "ports": [
            {"port_id": "in", "fluid": "SLUDGE", "direction": "IN"},
            {"port_id": "out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        # 污泥单元无水质去除概念——removal_refs 恒空（VS 降解走泥量
        # 减量链 XH-F7 不走水质去除键；0.6.0 零新增口径）
        "removal_refs": {},
        "norm_refs": [
            "GB 50014-2021 §8（污泥章——消化时间/挥发分降解率/产气率；条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》污泥消化章"
            "（中温消化参数带/沼气产率/池型构造常用值）",
            "docs/norms/sludge_xiaohua.md（2026-08-27 起草手算对照表，"
            "数据策略 v2，待追认；CJJ 131-2009 仅叙述性依据——"
            "数值 source 不标，I3 挂账）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "sludge_xiaohua.time_band",
            "sludge_xiaohua.eta_vs_band",
            "sludge_xiaohua.biogas_rate_band",
            "sludge_xiaohua.vs_load_band",
        ],
    }
)
