"""出图取数对照契约（UF-32 方案②）：13 单元冻结几何取数表 + ElevationProfile L0 类型。

输入:  单元 compute 实跑 dims 键全量（golden 项目 + 逐单元单点提取，
       2026-08-26 实录 249 键）+ registry/dimensions 既有 DimKey
输出:  PROJECTION_TABLE（plan/section/primitive/counts/non_drawn 五类
       取数声明 + 每键量纲列）+ ProfileStation / ElevationProfile
       （elevation 与 drafting 共同消费的 L0 类型——L3 互不 import 红线的解法）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（DRAFT 批 D1 裁决=Ruling ① UF-32 方案②轻量几何取数契约；
#   对账锁定测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   class UnitProjection(不可变)：单单元取数声明六字段——
#       unit_id: str
#       plan_keys: Mapping[图纸语义→dims 键]   平面图取数（总尺寸/分格/标注类）
#       section_keys: Mapping[剖面语义→dims 键] 剖面取数（水深 water_depth/
#           池深 pool_depth/标高关联键——water_depth 语义键是 elevation
#           build_profile 定池底的取数口）
#       primitive_dims: Mapping[三维槽位→dims 键]（length/width/depth 或
#           diameter——box/cylinder 图元取数）
#       instance_counts: Mapping[实例语义→dims 键]（台数/格数/灯数→InstanceGroup）
#       non_drawn: tuple[str, ...]  不上图纯校核量显式列（禁静默遗漏）
#       dim_of: Mapping[dims 键→DimKey]  量纲列（逐键；公式输出按 FormulaSpec
#           output_dim 定[∗ 项]，参数复用键按 registry/dimensions 登记）
#   PROJECTION_TABLE: Final[Mapping[str, UnitProjection]]  13 单元逐个声明
#       （cugeshan/xigeshan 同构不合并——总控 D1 明文）
#   class ProfileStation(不可变)：单站纵断——unit_id/water_level/floor_elev/
#       ground_elev/bury_depth/freeboard/water_depth/loss_in/design_flow
#   class ElevationProfile(不可变)：stations（沿流程拓扑序）/condition_key/
#       trace（公式迹）/warnings（埋深越界等）+ station_of(unit_id) 查询
#
# 【行为规格】
#   R1 表覆盖=单元 dims 键全量：plan∪section∪primitive∪counts∪non_drawn
#      == 该单元 compute 实际 dims 输出键集（对账测试以 golden 实跑为证，
#      13 单元全）；non_drawn 与四类取数不相交（校核量不上图）。
#   R2 五类语义不静默：每键归入至少一类（禁遗漏）；同一键可同时服务
#      平面标注与三维图元（plan/primitive 重叠合法——取数面非互斥分区）。
#   R3 dim_of 逐键合法：全部 ∈ DimKey 枚举（对账测试断言）；量纲起草
#      依据=FormulaSpec output_dim（∗ 公式输出项）与 registry/dimensions
#      既有登记——AI 起草待领域专家追认（pending §D1）。
#   R4 ElevationProfile 是标高唯一真源（L0）：elevation 产出、drafting
#      （section_view/profile_drawing）与 cost(M3) 消费同一类型——
#      本文件不 import 任何 L3（独立于两消费方，import-linter 绿）。
#   R5 本文件只读消费 dims 键名（字符串），不 import units_lib、
#      不做任何计算——纯声明面（L0 准入类别①冻结 schema，GR-36）。
#
# 【起草口径】分类与量纲列按 docs/norms 13 单元起草表（2026-08-25/26
#   数据策略 v2）+ 公式注册表 output_dim 归纳——AI 起草，整表+量纲列
#   待领域专家追认（.workflow/pending-domain-expert.md §DRAFT）。
#
# 【测试要求】tests/contracts/test_drawing_projection.py：13 单元
#   golden 实跑键集对账 + DimKey 合法性 + 表键集==13 市政单元。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；ADR-009 B7；
#   重写计划 §10.2/§10.5/§12.5/§13.6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, final

from waterprint.contracts.quantity import DimKey
from waterprint.contracts.result_schema import TraceNode
from waterprint.contracts.unit_api import Warning

__all__ = [
    "PROJECTION_TABLE",
    "ElevationProfile",
    "ProfileStation",
    "UnitProjection",
]

_L = DimKey.LENGTH
_D = DimKey.DIMENSIONLESS
_F = DimKey.FLOW
_A = DimKey.AREA
_V = DimKey.VOLUME
_M = DimKey.MASS
_T = DimKey.TIME
_VEL = DimKey.VELOCITY
_C = DimKey.CONCENTRATION
_P = DimKey.POWER


@dataclass(frozen=True)
@final
class UnitProjection:
    """单单元出图取数声明（六字段，Mapping 字段构造即只读快照）。"""

    unit_id: str
    plan_keys: Mapping[str, str]
    section_keys: Mapping[str, str]
    primitive_dims: Mapping[str, str]
    instance_counts: Mapping[str, str]
    non_drawn: tuple[str, ...]
    dim_of: Mapping[str, DimKey]

    def __post_init__(self) -> None:
        """Mapping 只读快照（T3A-01 防线同款：外部改原容器不泄漏）。"""
        for name in ("plan_keys", "section_keys", "primitive_dims",
                     "instance_counts", "dim_of"):
            object.__setattr__(
                self, name, MappingProxyType(dict(getattr(self, name)))
            )

    def drawn_keys(self) -> frozenset[str]:
        """四类取数键并集（R1 对账面：∪ non_drawn == dims 全量）。"""
        return frozenset(self.plan_keys.values()) | frozenset(
            self.section_keys.values()
        ) | frozenset(self.primitive_dims.values()) | frozenset(
            self.instance_counts.values()
        )


@dataclass(frozen=True)
@final
class ProfileStation:
    """纵断单站（不可变）：水面/池底/地面/埋深/超高/水深/进站损失/设计流量。"""

    unit_id: str
    water_level: float
    floor_elev: float
    ground_elev: float
    bury_depth: float
    freeboard: float
    water_depth: float
    loss_in: float
    design_flow: float


@dataclass(frozen=True)
@final
class ElevationProfile:
    """纵断数据唯一真源（不可变，L0）：站位序列 + 工况 + 公式迹 + 警告。"""

    stations: tuple[ProfileStation, ...]
    condition_key: str
    trace: tuple[TraceNode, ...]
    warnings: tuple[Warning, ...]

    def station_of(self, unit_id: str) -> ProfileStation | None:
        """按 unit_id 查站（drafting section_view 取标高的正门）。"""
        for station in self.stations:
            if station.unit_id == unit_id:
                return station
        return None


# ── 13 单元冻结取数表（2026-08-26 实跑提取 249 键逐键归位；AI 起草
#    待追认。cugeshan/xigeshan 同构不合并——逐行各自声明，D1 明文）────
_SCREEN_NON_DRAWN: Final[tuple[str, ...]] = (
    "ds_slag", "q", "v1_checked", "v_checked", "v_concrete", "w_slag", "xi",
)
# 粗/细格栅共用键集（同构键面；值域各池不同——两行声明不合并）
_SCREEN_DIM_OF: Final[Mapping[str, DimKey]] = {
    "B": _L, "B1": _L, "H": _L, "L": _L, "ds_slag": _M, "h1": _L,
    "mech_clean": _D, "n_gap": _D, "q": _F, "v1_checked": _VEL,
    "v_checked": _VEL, "v_concrete": _V, "w_slag": _V, "xi": _D,
}

PROJECTION_TABLE: Final[Mapping[str, UnitProjection]] = MappingProxyType({
    # 粗格栅：h1=过栅水头损失（CG-F8，非水深——栅前水深是参数 h 不在 dims）
    "municipal_cugeshan": UnitProjection(
        "municipal_cugeshan",
        plan_keys={"overall_length": "L", "overall_width": "B",
                   "approach_width": "B1", "gap_count": "n_gap"},
        section_keys={"pool_depth": "H", "head_loss": "h1"},
        primitive_dims={"length": "L", "width": "B", "depth": "H"},
        instance_counts={"mech_cleaner": "mech_clean"},
        non_drawn=_SCREEN_NON_DRAWN,
        dim_of=_SCREEN_DIM_OF,
    ),
    # 细格栅：与粗格栅同构键面（XG-F 族同名键，B/B1/H/L 值不同——不合并）
    "municipal_xigeshan": UnitProjection(
        "municipal_xigeshan",
        plan_keys={"overall_length": "L", "overall_width": "B",
                   "approach_width": "B1", "gap_count": "n_gap"},
        section_keys={"pool_depth": "H", "head_loss": "h1"},
        primitive_dims={"length": "L", "width": "B", "depth": "H"},
        instance_counts={"mech_cleaner": "mech_clean"},
        non_drawn=_SCREEN_NON_DRAWN,
        dim_of=_SCREEN_DIM_OF,
    ),
    # 平流沉砂池：a_channel 渠道过水断面积（CS-F14）、q_wet 湿砂量（CS-F17）
    "municipal_chenshachi": UnitProjection(
        "municipal_chenshachi",
        plan_keys={"overall_length": "l_straight", "overall_width": "d",
                   "outlet_width": "b_outlet"},
        section_keys={"water_depth": "h2", "pool_depth": "h_total",
                      "hopper_depth": "h4", "storage_height": "h_cyl",
                      "channel_depth": "h_channel"},
        primitive_dims={"length": "l_straight", "width": "d",
                        "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_channel", "ds_grit", "d_upper", "q1", "q1h", "q_wet",
                   "ratio_bh", "ratio_dh2", "t_actual", "v_concrete",
                   "v_cone", "v_eff", "v_hopper", "v_sand", "v_storage"),
        dim_of={"a_channel": _A, "b_outlet": _L, "d": _L, "d_upper": _L,
                "ds_grit": _M, "h2": _L, "h4": _L, "h_channel": _L,
                "h_cyl": _L, "h_total": _L, "l_straight": _L, "q1": _F,
                "q1h": _D, "q_wet": _V, "ratio_bh": _D, "ratio_dh2": _D,
                "t_actual": _T, "v_concrete": _V, "v_cone": _V,
                "v_eff": _V, "v_hopper": _V, "v_sand": _V, "v_storage": _V},
    ),
    # 辐流初沉池：d 池径（0.5 m 档取整后）、d_center 中心配水筒径
    "municipal_chuchenchi": UnitProjection(
        "municipal_chuchenchi",
        plan_keys={"overall_diameter": "d", "center_diameter": "d_center"},
        section_keys={"water_depth": "h2", "pool_depth": "h_total",
                      "bottom_slope_drop": "h4"},
        primitive_dims={"diameter": "d", "depth": "h_total"},
        instance_counts={},
        non_drawn=("d_raw", "f_act", "f_req", "q1", "q1h", "q_prime_act",
                   "q_weir", "ratio_dh2", "s_dry_1", "s_wet_1", "ss_out",
                   "v1_hopper", "v2_cone", "v_concrete", "v_need",
                   "v_storage"),
        dim_of={"d": _L, "d_center": _L, "d_raw": _L, "f_act": _A,
                "f_req": _A, "h2": _L, "h4": _L, "h_total": _L, "q1": _F,
                "q1h": _D, "q_prime_act": _D, "q_weir": _D,
                "ratio_dh2": _D, "s_dry_1": _M, "s_wet_1": _V,
                "ss_out": _C, "v1_hopper": _V, "v2_cone": _V,
                "v_concrete": _V, "v_need": _V, "v_storage": _V},
    ),
    # AAO 生物池：容积法主导——v1 无平面总尺寸/水深键（尺寸分格归 M3 方案
    # 批），19 键全列 non_drawn（显式不静默，R1）
    "municipal_aao": UnitProjection(
        "municipal_aao",
        plan_keys={},
        section_keys={},
        primitive_dims={},
        instance_counts={},
        non_drawn=("delta_n", "o2_carbon", "o2_denit", "o2_nit", "o2_total",
                   "q_internal", "q_return", "q_wet", "s_y", "t_n", "t_o",
                   "t_total", "theta_c", "v_anaerobic", "v_anoxic", "v_o",
                   "v_o_series", "v_total", "x_vss"),
        dim_of={"delta_n": _C, "o2_carbon": _M, "o2_denit": _M,
                "o2_nit": _M, "o2_total": _M, "q_internal": _D,
                "q_return": _D, "q_wet": _V, "s_y": _M, "t_n": _D,
                "t_o": _D, "t_total": _D, "theta_c": _D,
                "v_anaerobic": _V, "v_anoxic": _V, "v_o": _V,
                "v_o_series": _V, "v_total": _V, "x_vss": _C},
    ),
    # CASS 生物池：n_decant 滗水器台数（CA-F 族 ceil 收口）→实例数
    "municipal_cass": UnitProjection(
        "municipal_cass",
        plan_keys={"overall_length": "l_pool", "overall_width": "b_pool"},
        section_keys={"water_depth": "h_draw", "pool_depth": "h_pool",
                      "high_water": "h_draw_max"},
        primitive_dims={"length": "l_pool", "width": "b_pool",
                        "depth": "h_pool"},
        instance_counts={"decant": "n_decant"},
        non_drawn=("a_draw", "a_load", "a_pool", "b_pool_raw", "l_pool_raw",
                   "n_cycle", "n_decant_raw", "ns_act", "o2_carbon",
                   "o2_denit", "o2_nit", "o2_total", "q_decant", "q_wet",
                   "s_y", "t_phase_sum", "theta_c", "v_bio", "v_concrete",
                   "v_draw", "v_load", "v_plant", "v_pool", "v_selector",
                   "x_vss"),
        dim_of={"a_draw": _A, "a_load": _A, "a_pool": _A, "b_pool": _L,
                "b_pool_raw": _L, "h_draw": _L, "h_draw_max": _L,
                "h_pool": _L, "l_pool": _L, "l_pool_raw": _L,
                "n_cycle": _D, "n_decant": _D, "n_decant_raw": _D,
                "ns_act": _D, "o2_carbon": _M, "o2_denit": _M,
                "o2_nit": _M, "o2_total": _M, "q_decant": _D, "q_wet": _V,
                "s_y": _M, "t_phase_sum": _T, "theta_c": _D, "v_bio": _V,
                "v_concrete": _V, "v_draw": _V, "v_load": _V,
                "v_plant": _V, "v_pool": _V, "v_selector": _V,
                "x_vss": _C},
    ),
    # 高密沉淀池：宽度档 b（0.5 m 档）；无池长键（长度由面积/宽推导归 M3）
    "municipal_gaomidu": UnitProjection(
        "municipal_gaomidu",
        plan_keys={"overall_width": "b"},
        section_keys={"settling_zone_depth": "h_settle",
                      "flocculation_depth": "h_floc_calc",
                      "tube_zone_depth": "h_tube_zone",
                      "pool_depth": "h_total"},
        primitive_dims={"width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_act", "a_incl_req", "b_raw", "gt_floc", "h_total_raw",
                   "m_pac", "m_pam", "p_floc", "p_mix", "q1h", "q_design_h",
                   "q_return", "q_sludge", "q_surface_act", "s_dry",
                   "ss_out", "v_concrete", "v_floc", "v_mix"),
        dim_of={"a_act": _A, "a_incl_req": _A, "b": _L, "b_raw": _L,
                "gt_floc": _D, "h_floc_calc": _L, "h_settle": _L,
                "h_total": _L, "h_total_raw": _L, "h_tube_zone": _L,
                "m_pac": _M, "m_pam": _M, "p_floc": _P, "p_mix": _P,
                "q1h": _D, "q_design_h": _D, "q_return": _D,
                "q_sludge": _V, "q_surface_act": _D, "s_dry": _M,
                "ss_out": _C, "v_concrete": _V, "v_floc": _V, "v_mix": _V},
    ),
    # V 型滤池：h_total 池总高（滤板/砂层/水深构成，剖面池深语义）
    "municipal_vxinglvchi": UnitProjection(
        "municipal_vxinglvchi",
        plan_keys={"overall_length": "l", "overall_width": "b"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"length": "l", "width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_cell", "a_cell_act", "a_total_act", "a_total_req",
                   "b_raw", "l_raw", "q_air", "q_filter", "q_sweep",
                   "q_wash", "q_wash_sim", "ratio_wash", "v_air_per",
                   "v_concrete", "v_filter_act", "v_forced_act",
                   "v_wash_daily", "v_wash_per"),
        dim_of={"a_cell": _A, "a_cell_act": _A, "a_total_act": _A,
                "a_total_req": _A, "b": _L, "b_raw": _L, "h_total": _L,
                "l": _L, "l_raw": _L, "q_air": _F, "q_filter": _D,
                "q_sweep": _F, "q_wash": _F, "q_wash_sim": _F,
                "ratio_wash": _D, "v_air_per": _V, "v_concrete": _V,
                "v_filter_act": _D, "v_forced_act": _D,
                "v_wash_daily": _V, "v_wash_per": _V},
    ),
    # 紫外消毒：n_lamp 灯管支数/n_module 模块数/n_module_series 系列模块数
    "municipal_ziwai": UnitProjection(
        "municipal_ziwai",
        plan_keys={"channel_length": "l_channel",
                   "lamp_zone_length": "l_lamp_zone"},
        section_keys={"water_depth": "h_w", "channel_depth": "h_channel",
                      "submergence": "h_submerge"},
        primitive_dims={"length": "l_channel", "depth": "h_channel"},
        instance_counts={"lamp": "n_lamp", "module": "n_module",
                         "module_series": "n_module_series"},
        non_drawn=("c_fecal_out", "h_w_raw", "n_lamp_raw", "n_module_raw",
                   "q_c", "t_exp", "v_channel_act", "v_concrete"),
        dim_of={"c_fecal_out": _D, "h_channel": _L, "h_submerge": _L,
                "h_w": _L, "h_w_raw": _L, "l_channel": _L,
                "l_lamp_zone": _L, "n_lamp": _D, "n_lamp_raw": _D,
                "n_module": _D, "n_module_raw": _D, "n_module_series": _D,
                "q_c": _F, "t_exp": _T, "v_channel_act": _VEL,
                "v_concrete": _V},
    ),
    # 巴歇尔计量槽：n_depress 喉道底跌落 0.23 m/k_margin 槽身边距 0.08 m
    # （BJ 标准型构造常量，几何长度非数量——ADR-009 B7 七档喉宽口径）
    "municipal_bashi_jiliangcao": UnitProjection(
        "municipal_bashi_jiliangcao",
        plan_keys={"overall_length": "l_total", "approach_width": "b1",
                   "diffuser_width": "b2"},
        section_keys={"upstream_head_avg": "ha_avg",
                      "upstream_head_design": "ha_design",
                      "total_loss": "h_loss", "crest_drop": "n_depress",
                      "side_margin": "k_margin"},
        primitive_dims={"length": "l_total", "width": "b2",
                        "depth": "ha_design"},
        instance_counts={},
        non_drawn=("l1", "l_diffuse", "l_throat", "q_meas", "sigma"),
        dim_of={"b1": _L, "b2": _L, "h_loss": _L, "ha_avg": _L,
                "ha_design": _L, "k_margin": _L, "l1": _L,
                "l_diffuse": _L, "l_throat": _L, "l_total": _L,
                "n_depress": _L, "q_meas": _F, "sigma": _D},
    ),
    # 污水提升泵房：n_pump_total 泵位总数（工作+备用）→实例数
    "municipal_wushui_tisheng": UnitProjection(
        "municipal_wushui_tisheng",
        plan_keys={"pipe_diameter": "d_pipe"},
        section_keys={"well_depth": "h_well_total"},
        primitive_dims={"depth": "h_well_total"},
        instance_counts={"pump": "n_pump_total", "pump_duty": "n_pump_duty"},
        non_drawn=("a_well", "d_pipe_raw", "h_friction", "h_local", "h_loss",
                   "h_pump", "n_pump_raw", "n_start", "q_design_h",
                   "q_pump", "q_pump_si", "v_concrete", "v_pipe_act",
                   "v_well"),
        dim_of={"a_well": _A, "d_pipe": _L, "d_pipe_raw": _L,
                "h_friction": _L, "h_local": _L, "h_loss": _L,
                "h_pump": _L, "h_well_total": _L, "n_pump_duty": _D,
                "n_pump_raw": _D, "n_pump_total": _D, "n_start": _D,
                "q_design_h": _D, "q_pump": _D, "q_pump_si": _F,
                "v_concrete": _V, "v_pipe_act": _VEL, "v_well": _V},
    ),
    # 调节池：p_stir 搅拌功率 kW（POWER——功率量纲首个 dims 键）
    "municipal_tiaojiechi": UnitProjection(
        "municipal_tiaojiechi",
        plan_keys={"overall_length": "l", "overall_width": "b",
                   "overflow_diameter": "d_overflow"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"length": "l", "width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a1", "a_act", "b_raw", "l_raw", "p_stir", "q_pump1",
                   "t_reg_act", "v1", "v_act_total", "v_concrete",
                   "v_total"),
        dim_of={"a1": _A, "a_act": _A, "b": _L, "b_raw": _L,
                "d_overflow": _L, "h_total": _L, "l": _L, "l_raw": _L,
                "p_stir": _P, "q_pump1": _D, "t_reg_act": _D, "v1": _V,
                "v_act_total": _V, "v_concrete": _V, "v_total": _V},
    ),
    # 辐流二沉池：h2 有效水深是参数（联动 AAO）不在 dims——剖面池深取
    # h_total、池底坡降 h4；v_check 校核容积/t_hrt 校核 HRT（EC 复合导出）
    "municipal_erchunchi": UnitProjection(
        "municipal_erchunchi",
        plan_keys={"overall_diameter": "d", "center_diameter": "d_center"},
        section_keys={"pool_depth": "h_total", "bottom_slope_drop": "h4"},
        primitive_dims={"diameter": "d", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_act", "a_q", "a_solid", "a_tank", "d_raw", "g_act",
                   "m_solid", "q1", "q1h", "q_act", "q_return_sludge",
                   "q_weir", "t_hrt", "v_check", "v_concrete", "x_r"),
        dim_of={"a_act": _A, "a_q": _A, "a_solid": _A, "a_tank": _A,
                "d": _L, "d_center": _L, "d_raw": _L, "g_act": _D,
                "h4": _L, "h_total": _L, "m_solid": _M, "q1": _F,
                "q1h": _D, "q_act": _D, "q_return_sludge": _D,
                "q_weir": _D, "t_hrt": _D, "v_check": _V,
                "v_concrete": _V, "x_r": _C},
    ),
})
