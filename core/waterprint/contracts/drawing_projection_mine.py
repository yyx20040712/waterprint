"""矿井水线出图取数表（UF-32 方案②）：矿井单元冻结几何取数声明（分线表②）。

输入:  矿井单元 compute 实跑 dims 键全量（矿井链单点图实跑提取，
       2026-08-27 M3D1 实录 107 键）
输出:  MINE_PROJECTIONS（plan/section/primitive/counts/non_drawn 五类
       取数声明 + 每键量纲列——聚合正门 drawing_projection 消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3D1 D1 新建分线表②——条目面随 M3D1 D2 落表；对账锁定
#   测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   MINE_PROJECTIONS: Final[Mapping[str, UnitProjection]]  矿井水线
#       8 单元逐个声明（unit_id 前缀 mine_water_）
#
# 【行为规格】
#   R1 表覆盖=单元 dims 键全量：plan∪section∪primitive∪counts∪non_drawn
#      == 该单元 compute 实际 dims 输出键集（对账测试以矿井链单点图
#      实跑为证）；non_drawn 与四类取数不相交（校核量不上图）。
#   R2 五类语义不静默：每键归入至少一类（禁遗漏）；plan/primitive
#      重叠合法（取数面非互斥分区）。
#   R3 dim_of 逐键合法：全部 ∈ DimKey 枚举；量纲起草依据=矿井各包
#      manifest FormulaSpec output_dim（KI/KT/KC/KN/KS/KG/KV/KZ 族）
#      与市政线同名键先例——AI 起草待领域专家追认。
#   R5 只读消费 dims 键名（字符串），不 import units_lib、不做任何
#      计算——纯声明面（L0 准入类别①，GR-36）。
#
# 【起草口径】分类原则=几何上图量入取数类（plan/section/primitive/
#   counts），校核/过程/衡算量入 non_drawn；未被 plan_view v1 消费的
#   键亦可入 plan_keys 声明面（approach_width/outlet_width 市政先例）；
#   对账测试是覆盖最终裁决（缺键/多键即红）。
#
# 【禁止事项】不得出现数值字面量（纯键名映射+量纲枚举）；不得
#   import units_lib 或任何 L2+ 层。
#
# 【测试要求】tests/contracts/test_drawing_projection.py：矿井 8 单元
#   链式单点图实跑键集对账 + DimKey 合法性 + 分线键集 disjoint。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；数据策略 v2；
#   M3D1 简报 D1/D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from waterprint.contracts.drawing_projection_types import UnitProjection
from waterprint.contracts.quantity import DimKey

__all__ = ["MINE_PROJECTIONS"]

_L = DimKey.LENGTH
_D = DimKey.DIMENSIONLESS
_F = DimKey.FLOW
_A = DimKey.AREA
_V = DimKey.VOLUME
_VEL = DimKey.VELOCITY

# ── 矿井水线 8 单元取数表（2026-08-27 全链单点图实跑提取 107 键逐键
#    归位；AI 起草待追认。分类原则=几何上图量入取数类，校核/过程/衡算
#    量入 non_drawn——对账测试是覆盖最终裁决，缺键/多键即红）────
MINE_PROJECTIONS: Final[Mapping[str, UnitProjection]] = MappingProxyType({
    # 线首注入节点：无池体——流量/标高七键全 non_drawn（z_water/z_bottom
    # 标高语义归 elevation 总线，不进表取数面）
    "mine_water_input": UnitProjection(
        "mine_water_input",
        plan_keys={},
        section_keys={},
        primitive_dims={},
        instance_counts={},
        non_drawn=("freeboard", "q_avg_h", "q_design", "v_inlet",
                   "z_bottom", "z_pipe_bottom", "z_water"),
        dim_of={"freeboard": _L, "q_avg_h": _D, "q_design": _F,
                "v_inlet": _VEL, "z_bottom": _L, "z_pipe_bottom": _L,
                "z_water": _L},
    ),
    # 矿井调节池：p_stir 搅拌功率 kW（DIMENSIONLESS 裸值——KT-F9
    # output_dim 口径，与市政调节池 TJ-F9 同款）
    "mine_water_tiaojiechi": UnitProjection(
        "mine_water_tiaojiechi",
        plan_keys={"overall_length": "l", "overall_width": "b"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"length": "l", "width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a1", "a_act", "b_raw", "d_out_raw", "dn_out", "l_raw",
                   "p_stir", "t_reg_act", "v1", "v_act_total", "v_concrete",
                   "v_total"),
        dim_of={"a1": _A, "a_act": _A, "b": _L, "b_raw": _L,
                "d_out_raw": _L, "dn_out": _L, "h_total": _L, "l": _L,
                "l_raw": _L, "p_stir": _D, "t_reg_act": _D, "v1": _V,
                "v_act_total": _V, "v_concrete": _V, "v_total": _V},
    ),
    # 矿井平流沉砂池：l_weir 出水堰长（KC-F7）；v_hopper 斗容积（KC-F6
    # 容积量——不上图入 non_drawn，与市政 h4 斗深键义区分）
    "mine_water_chenshachi": UnitProjection(
        "mine_water_chenshachi",
        plan_keys={"overall_length": "l_cell", "overall_width": "b",
                   "weir_length": "l_weir"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"length": "l_cell", "width": "b",
                        "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_cross", "b_raw", "l_cell_raw", "q_weir", "v_concrete",
                   "v_h_act", "v_hopper", "v_sand"),
        dim_of={"a_cross": _A, "b": _L, "b_raw": _L, "h_total": _L,
                "l_cell": _L, "l_cell_raw": _L, "l_weir": _L, "q_weir": _D,
                "v_concrete": _V, "v_h_act": _VEL, "v_hopper": _V,
                "v_sand": _V},
    ),
    # 矿井絮凝池：四区 l1~l4 分段长（KN-F9 逐区）；无总长单键——Σl 计算
    # 被纯投影铁律禁止，box 三槽不全不触发图元（width/depth 两槽声明面
    # 保留）；p1~p4/p_total 功率 kW 裸值（KN-F6 output_dim=DIMENSIONLESS）
    "mine_water_ningjiao": UnitProjection(
        "mine_water_ningjiao",
        plan_keys={"overall_width": "b", "zone_length_1": "l1",
                   "zone_length_2": "l2", "zone_length_3": "l3",
                   "zone_length_4": "l4"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a1", "a2", "a3", "a4", "b_raw", "gt_total", "m_pac",
                   "m_pam", "m_seed", "p1", "p2", "p3", "p4", "p_total",
                   "t_total", "v1", "v2", "v3", "v4", "v_concrete"),
        dim_of={"a1": _A, "a2": _A, "a3": _A, "a4": _A, "b": _L,
                "b_raw": _L, "gt_total": _D, "h_total": _L, "l1": _L,
                "l2": _L, "l3": _L, "l4": _L, "m_pac": _D, "m_pam": _D,
                "m_seed": _D, "p1": _D, "p2": _D, "p3": _D, "p4": _D,
                "p_total": _D, "t_total": _D, "v1": _V, "v2": _V,
                "v3": _V, "v4": _V, "v_concrete": _V},
    ),
    # 磁分离：n_disks 磁盘盘片数→实例数（disk 语义标签——scene
    # _INSTANCE_KINDS 本批 M3D1 D4 登记）；设备类无池体图元
    "mine_water_cifenli": UnitProjection(
        "mine_water_cifenli",
        plan_keys={},
        section_keys={},
        primitive_dims={},
        instance_counts={"disk": "n_disks"},
        non_drawn=("a_disk", "a_total_req", "m_seed_net", "n_disks_raw",
                   "q_1h", "q_sludge", "v_line", "w_ss"),
        dim_of={"a_disk": _A, "a_total_req": _A, "m_seed_net": _D,
                "n_disks": _D, "n_disks_raw": _D, "q_1h": _D,
                "q_sludge": _V, "v_line": _VEL, "w_ss": _D},
    ),
    # 矿井高密度澄清池：l/b 档取整后池长/池宽（KG-F5/F6 raw 键对照）
    "mine_water_gaomidu": UnitProjection(
        "mine_water_gaomidu",
        plan_keys={"overall_length": "l", "overall_width": "b"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"length": "l", "width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_settle", "b_raw", "l_raw", "q1h", "q_surf_act",
                   "v_axial", "v_concrete", "v_floc", "v_mix"),
        dim_of={"a_settle": _A, "b": _L, "b_raw": _L, "h_total": _L,
                "l": _L, "l_raw": _L, "q1h": _D, "q_surf_act": _D,
                "v_axial": _VEL, "v_concrete": _V, "v_floc": _V,
                "v_mix": _V},
    ),
    # 矿井 V 型滤池：t_bw 三阶段反冲停滤历时（合成量——p_total 单输出
    # 导出量先例口径，DIMENSIONLESS）
    "mine_water_vxinglvchi": UnitProjection(
        "mine_water_vxinglvchi",
        plan_keys={"overall_length": "l", "overall_width": "b"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"length": "l", "width": "b", "depth": "h_total"},
        instance_counts={},
        non_drawn=("b_raw", "eta_wash", "f_single", "f_total", "l_raw",
                   "q_d", "t_bw", "t_w", "v_concrete", "v_force_act",
                   "w_wash"),
        dim_of={"b": _L, "b_raw": _L, "eta_wash": _D, "f_single": _A,
                "f_total": _A, "h_total": _L, "l": _L, "l_raw": _L,
                "q_d": _D, "t_bw": _D, "t_w": _D, "v_concrete": _V,
                "v_force_act": _D, "w_wash": _D},
    ),
    # 矿井紫外消毒：n_rows 灯管排数→实例数（lamp 语义在 _INSTANCE_KINDS
    # 既有集内）；无 b/l 键——无 box 槽（municipal_aao 空组形态同款）
    "mine_water_ziwai": UnitProjection(
        "mine_water_ziwai",
        plan_keys={},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={},
        instance_counts={"lamp_row": "n_rows"},
        non_drawn=("a_ch", "dose_act", "dose_row", "h_loss", "i_avg",
                   "n_rows_raw", "q_ch", "t_contact", "t_eff", "v_ch"),
        dim_of={"a_ch": _A, "dose_act": _D, "dose_row": _D, "h_loss": _L,
                "h_total": _L, "i_avg": _D, "n_rows": _D,
                "n_rows_raw": _D, "q_ch": _D, "t_contact": _D,
                "t_eff": _D, "v_ch": _VEL},
    ),
})
