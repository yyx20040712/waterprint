"""平流沉砂池清单声明：参数/端口/去除率引用/条文/工况映射+公式注册（真源）。

输入:  手算表真源（docs/norms/mine_water_chenshachi.md，2026-08-27，数据策略 v2 待追认）+
       data/coefficients 0.5.0 键名
输出:  UnitManifest 实例（load_manifest 静态校验通过才算合法）+ KC-F1~F10 公式登记
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3a2 实装：M3a1 数据先行批的代码落地/M3 正式验收）
#
# 【固定形态】UNIT_ID = "mine_water_chenshachi"；manifest = load_manifest({...})。
# 【数值真源】参数默认值=表主算例逐字（n=8 格/v_h=0.25 m/s/t_stay=60 s/
#   h2=0.5 m/t_clean=2 d；池长 l_cell 0.5 m 档/池宽 B 0.1 m 档）；
#   系数不落本表——流速/停留/水深三校核带+单格宽下限+沉砂量+贮砂
#   安全系数+堰负荷上限+超高+壁厚系数+高程水损全部经
#   factor.mine_chenshachi.* 键消费（app._unit_params 线感知投影，
#   mine_ 限定）；去除率仅 removal.mine_chenshachi.ss.mod_default 键
#   （0.15 砂粒组分——COD 非混凝沉淀滤池段不建键，BOD5 全线不建键）。
# 【公式注册（D1）】KC-F1~F10+MS-F2 逐条 FormulaSpec+register（MS-F2=矿井
#   泥线链级衔接式沉砂股干基——GOLDEN4b R1 登记 2026-08-28，sludge_out
#   产股消费）；expression=
#   表公式串转受限 DSL——data 包系数一律符号绑定（零系数字面量）；
#   结构常数（2/1000/1000000）内联（本文件=units_lib manifest 白名单
#   区，表串原文常量；10⁶=沉砂量 X m³/10⁶m³ 折算、×1000=m3/s→L/s
#   堰负荷口径、×86400=流量口径注记同 KT-F1 先例）；π 不入本组公式
#   （平流矩形断面无圆截面）；sqrt 直接用。DSL 无 ceil：池长 l_cell
#   （0.5 m 档）/池宽 B（0.1 m 档）离散在 compute 收口（步长=参数）。
# 【物理隔离】与市政同名包 municipal/chenshachi（旋流型）零 import
#   零参数复用（§14.3）：本表=平流型主线（水平流速 0.15~0.30 m/s ×
#   停留 30~60 s 主控、浅池 0.4~1.2 m，表边界差异节——同 ID 不同型
#   构筑物，键空间经 mine_ 限定物理隔离）。
# 【声明五件】params（range 仅表内有出处带者：v_h/t_stay/h2 三参数；
#   格数 n=8/清砂周期 t_clean=2 构造参数无档位来源不设 grid）/
#   ports 两口 WATER+sludge_out SLUDGE 产股口（GOLDEN4a D3——无条件
#   产股，无边也产；nongsuo sup 先例同构）/removal_refs 仅 SS 键/
#   norm_refs 双源标记（GB/T 41019-2021+给水排水设计手册）/
#   condition_mappings=()/constraint_refs 五键。
# ══════════════════════════════════════════════════════════════════

from typing import Final

from waterprint.contracts.manifest import load_manifest
from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, register

UNIT_ID = "mine_water_chenshachi"

_GB = (
    "GB/T 41019-2021（矿井水处理工艺——预处理除砂，条号待核对；"
    "docs/norms/mine_water_chenshachi.md 起草表 2026-08-27，待追认）"
)
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》平流沉砂池水平流速/"
    "停留时间/砂斗常用带（docs/norms/mine_water_chenshachi.md 起草表"
    " 2026-08-27，待追认）"
)
_D = DimKey.DIMENSIONLESS
_L = DimKey.LENGTH
_F = DimKey.FLOW
_A = DimKey.AREA
_VOL = DimKey.VOLUME
_V = DimKey.VELOCITY

# GOLDEN4a D3 产股口常量（数值白名单区，compute 零字面量消费）——
# 手算表 mine_water_sludge_line.md MS-F2 链级衔接式三键：RHO_SAND_WET
# 湿砂容重 1.6 t/m³（带 1.5~1.7 取 1.6）/MOISTURE_SAND 湿砂含水率 0.10
# （带 0.05~0.15 取 0.10——hebing p_bio 注入位同源）/KG_PER_TON t→kg
# 换算。三键系链级参数档无现库系数键——直值注记，系数键化归后续批
# 裁量呈报不扩 coefficients（D3 零新系数键）。
SECS_PER_DAY: Final[float] = 86400.0
RHO_SAND_WET: Final[float] = 1.6
MOISTURE_SAND: Final[float] = 0.10
KG_PER_TON: Final[float] = 1000.0

_FORMULAS: tuple[FormulaSpec, ...] = (
    FormulaSpec(
        "KC-F1",
        "l_cell_raw = v_h * t_stay",
        {
            "v_h": (_V, "设计水平流速 m/s（参数 v_h，平流型主控参数）"),
            "t_stay": (_D, "停留时间 s（参数 t_stay）"),
        },
        _L,
        f"{_GB}；{_HB}",
    ),
    FormulaSpec(
        "KC-F2",
        "a_cross = q_design / (n * v_h)",
        {
            "q_design": (_F, "最高时设计流量 m3/s（池体水力口径）"),
            "n": (_D, "格数"),
            "v_h": (_V, "设计水平流速 m/s（参数 v_h）"),
        },
        _A,
        _HB,
    ),
    FormulaSpec(
        "KC-F3",
        "b_raw = a_cross / h2",
        {
            "a_cross": (_A, "单格过水断面积 m2"),
            "h2": (_L, "有效水深 m（参数 h2，浅池沉砂）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KC-F4",
        "v_h_act = q_design / (n * b * h2)",
        {
            "q_design": (_F, "最高时设计流量 m3/s"),
            "n": (_D, "格数"),
            "b": (_L, "单格宽（0.1 m 档 ceil 后）m"),
            "h2": (_L, "有效水深 m"),
        },
        _V,
        _HB,
    ),
    FormulaSpec(
        "KC-F5",
        "v_sand = q_avg_daily * 86400 * x_sand / 1000000",
        {
            "q_avg_daily": (_F, "平均日流量 m3/s（×86400 转 m3/d 口径——贮砂量按平均日）"),
            "x_sand": (
                _D,
                "沉砂量 m3/10⁶m3（factor.mine_chenshachi.sand_yield_x，SS 800 可沉组分折算）",
            ),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KC-F6",
        "v_hopper = v_sand * t_clean * safety",
        {
            "v_sand": (_VOL, "每日沉砂量 m3/d"),
            "t_clean": (_D, "清砂周期 d（参数 t_clean，声明面默认 2）"),
            "safety": (_D, "贮砂安全系数（factor.mine_chenshachi.hopper.safety）"),
        },
        _VOL,
        _HB,
    ),
    FormulaSpec(
        "KC-F7",
        "l_weir = n * (l_cell + 2 * b)",
        {
            "n": (_D, "格数"),
            "l_cell": (_L, "池长（0.5 m 档 ceil 后）m"),
            "b": (_L, "单格宽（ceil 后）m"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KC-F8",
        "q_weir = q_design * 1000 / l_weir",
        {
            "q_design": (_F, "最高时设计流量 m3/s（×1000 转 L/s 口径）"),
            "l_weir": (_L, "出水堰可用堰长 m（池壁两侧+末端）"),
        },
        _D,
        _HB,
    ),
    FormulaSpec(
        "KC-F9",
        "h_total = h_super + h2",
        {
            "h_super": (_L, "超高 m（factor.mine_chenshachi.superheight）"),
            "h2": (_L, "有效水深 m（参数 h2）"),
        },
        _L,
        _HB,
    ),
    FormulaSpec(
        "KC-F10",
        "v_concrete = l_cell * b * h_total * n * wall_coef",
        {
            "l_cell": (_L, "池长（ceil 后）m"),
            "b": (_L, "单格宽（ceil 后）m"),
            "h_total": (_L, "池总高 m"),
            "n": (_D, "格数"),
            "wall_coef": (_D, "壁厚系数（factor.mine_chenshachi.wall_thickness_coef，概算口径）"),
        },
        _VOL,
        _HB,
    ),
    # GOLDEN4b R1（总控裁决 2026-08-28）：矿井泥线链级衔接式 MS-F2 沉砂股
    # ——GOLDEN4a 终裁 I-2"乘积系实质计算非纯投影"更正落点；登记于本产泥
    # 包 manifest（审计口径"formula_ids=实际应用"保持——sludge_out 产股
    # 消费此式，compute 内联同式实现由包内测试 R4 背书）。
    FormulaSpec(
        "MS-F2",
        "ds_bio = v_sand * rho_sand_wet * (1 - p_sand) * 1000",
        {
            "v_sand": (_D, "湿砂体积 m³/d（KC-F5 链值）"),
            "rho_sand_wet": (_D, "湿砂容重 t/m³（常量 RHO_SAND_WET=1.6——带 1.5~1.7 取中）"),
            "p_sand": (_D, "湿砂含水率（常量 MOISTURE_SAND=0.10——hebing p_bio 位同源）"),
        },
        _D,
        "docs/norms/mine_water_sludge_line.md（矿井泥线三股语义映射表——MS-F2 "
        "沉砂干基链级衔接式，GOLDEN4b R1 登记 2026-08-28）+《给水排水设计手册"
        "（第 5 册 城镇排水）》砂斗排砂容重/湿砂含水常用带",
    ),
)

for _spec in _FORMULAS:
    register(_spec)

# 公式号全量（compute 的 formula_ids 声明面——避免在 compute 侧重复列号）
FORMULA_IDS: tuple[str, ...] = tuple(spec.formula_id for spec in _FORMULAS)

manifest = load_manifest(
    {
        "unit_id": UNIT_ID,
        "i18n_key": "units.mine_water_chenshachi",
        "version": "1.0",
        "business_line": "mine_water",
        # 默认值=表主算例逐字（出处 docs/norms/mine_water_chenshachi.md 参数档）；
        # range 仅三条有出处带参数（velocity_band 0.15~0.30/retention_band
        # 30~60/depth_band 0.4~1.2——平流型主控三带，区别市政旋流表面
        # 负荷口径），格数/清砂周期/取整档无范围来源不设
        "params": [
            {"field_id": "n", "dim": "DIMENSIONLESS", "default": 8.0},
            {
                "field_id": "v_h",
                "dim": "VELOCITY",
                "default": 0.25,
                "range": {"min": 0.15, "max": 0.3},
            },
            {
                "field_id": "t_stay",
                "dim": "DIMENSIONLESS",
                "default": 60.0,
                "range": {"min": 30.0, "max": 60.0},
            },
            {
                "field_id": "h2",
                "dim": "LENGTH",
                "default": 0.5,
                "range": {"min": 0.4, "max": 1.2},
            },
            {"field_id": "t_clean", "dim": "DIMENSIONLESS", "default": 2.0},
            {"field_id": "side_disc_step", "dim": "LENGTH", "default": 0.5},
            {"field_id": "length_disc_step", "dim": "LENGTH", "default": 0.1},
        ],
        "ports": [
            {"port_id": "in", "fluid": "WATER", "direction": "IN"},
            {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
            # GOLDEN4a D3 产股口（2026-08-28）：无条件产股（无边也产——
            # nongsuo sup 先例同构）；产股三量=MS-F2 衔接式计算（终裁 I-2
            # 更正：乘积系实质计算非纯投影——FormulaSpec 登记本批
            # [GOLDEN4b R1]；ds=v_sand×ρ湿砂×(1−p_sand)×1000 干基——
            # hebing 注入 ds_bio 位链路同源；q_wet=v_sand 湿砂体积直算
            # 口径；moisture=p_sand——三键直值注记见上常量节）。
            {"port_id": "sludge_out", "fluid": "SLUDGE", "direction": "OUT"},
        ],
        "removal_refs": {
            "SS": "removal.mine_chenshachi.ss.mod_default",
        },
        "norm_refs": [
            "GB/T 41019-2021（矿井水处理工艺——预处理除砂，条号待核对）",
            "《给水排水设计手册（第 5 册 城镇排水）》平流沉砂池水平流速/停留时间/砂斗常用带",
            "docs/norms/mine_water_chenshachi.md（2026-08-27 起草手算对照表，数据策略 v2，待追认）",
        ],
        "condition_mappings": [],
        "constraint_refs": [
            "mine_water_chenshachi.velocity_band",
            "mine_water_chenshachi.retention_band",
            "mine_water_chenshachi.depth_band",
            "mine_water_chenshachi.cell_width",
            "mine_water_chenshachi.weir_load",
        ],
    }
)
