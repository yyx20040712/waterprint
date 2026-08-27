"""污泥线出图取数表（UF-32 方案②）：污泥单元冻结几何取数声明（分线表③）。

输入:  污泥单元 compute 实跑 dims 键全量（污泥链单点图实跑提取，
       2026-08-27 M3D2 实录 112 键）
输出:  SLUDGE_PROJECTIONS（plan/section/primitive/counts/non_drawn 五类
       取数声明 + 每键量纲列——聚合正门 drawing_projection 消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3D2 D1 新建分线表③——条目面随本批落表；对账锁定
#   测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   SLUDGE_PROJECTIONS: Final[Mapping[str, UnitProjection]]  污泥线
#       7 单元逐个声明（unit_id 前缀 sludge_）
#
# 【行为规格】
#   R1 表覆盖=单元 dims 键全量：plan∪section∪primitive∪counts∪non_drawn
#      == 该单元 compute 实际 dims 输出键集（对账测试以污泥链单点图
#      实跑为证）；non_drawn 与四类取数不相交（校核量不上图）。
#   R2 五类语义不静默：每键归入至少一类（禁遗漏）；plan/primitive
#      重叠合法（取数面非互斥分区）。
#   R3 dim_of 逐键合法：全部 ∈ DimKey 枚举；量纲起草依据=污泥 7 包
#      manifest FormulaSpec output_dim 实读 79 条（HB-F1~F13/ST-F1~F9/
#      BZ-F1~F18/NS-F1~F12/XH-F1~F11/TU-F1~F8/GH-F1~F8——全线公式
#      输出均为 DIMENSIONLESS，工程口径 m³/d、kg/d、小数含水率裸值）
#      +非公式导出键按市政同名先例——AI 起草待领域专家追认。
#   R5 只读消费 dims 键名（字符串），不 import units_lib、不做任何
#      计算——纯声明面（L0 准入类别①，GR-36）。
#
# 【起草口径】分类原则=几何上图量入取数类（plan/section/primitive/
#   counts），校核/过程/衡算量入 non_drawn；衔接链键 q_in/ds_in/
#   p_in/q_out/ds_out/p_out 全线 non_drawn（总控裁定：全链贯穿衡算
#   量不上图）；非公式键量纲归属——d_pipe/d=档取整几何键按市政同名
#   先例 _L（municipal_wushui_tisheng d_pipe/bashi_jiliangcao d），
#   n_pump_duty/n_machine_duty=整台取整键 _D（n_pump_duty 市政同名），
#   衔接链六量 _D（ganhua q_out=GH-F3 公式直接输出 _D——全线同族
#   一致照录）；跨线不一致同名键照录（d_raw/h_well_total 市政 _L
#   vs 污泥公式 _D——pending §13 M3D2 追认点登记）。
#
# 【禁止事项】不得出现数值字面量（纯键名映射+量纲枚举）；不得
#   import units_lib 或任何 L2+ 层。
#
# 【测试要求】tests/contracts/test_drawing_projection.py：污泥 7 单元
#   链式单点图实跑键集对账 + DimKey 合法性 + 分线键集 disjoint；
#   test_drawing_projection_sludge.py 薄镜像（宪法 §6）。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；数据策略 v2；
#   M3D2 简报 D1/D2；explore-M3D1-freeze §四污泥表
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from waterprint.contracts.drawing_projection_types import UnitProjection
from waterprint.contracts.quantity import DimKey

__all__ = ["SLUDGE_PROJECTIONS"]

_L = DimKey.LENGTH
_D = DimKey.DIMENSIONLESS

# ── 污泥线 7 单元取数表（2026-08-27 全链单点图实跑提取 112 键逐键
#    归位；AI 起草待追认。分类原则=几何上图量入取数类，校核/过程/衡算
#    量入 non_drawn——对账测试是覆盖最终裁决，缺键/多键即红）────
SLUDGE_PROJECTIONS: Final[Mapping[str, UnitProjection]] = MappingProxyType({
    # 污泥合并：三股汇流/产率互校/闭合校核衡算单元——13 键全 non_drawn
    # （municipal_aao 容积法主导全 non_drawn 先例）
    "sludge_hebing": UnitProjection(
        "sludge_hebing",
        plan_keys={},
        section_keys={},
        primitive_dims={},
        instance_counts={},
        non_drawn=("dev_close", "dev_pct", "ds_check", "ds_total",
                   "dx_bio", "k_dt", "p_merged", "q_bio", "q_chem",
                   "q_primary", "q_total", "s_y", "w_water"),
        dim_of={"dev_close": _D, "dev_pct": _D, "ds_check": _D,
                "ds_total": _D, "dx_bio": _D, "k_dt": _D,
                "p_merged": _D, "q_bio": _D, "q_chem": _D,
                "q_primary": _D, "q_total": _D, "s_y": _D,
                "w_water": _D},
    ),
    # 污泥输送：管道类——d_pipe 管径档取整键（ST-F3 d_raw 原始管径
    # non_drawn 对照）；i_req/i_slope 坡度校核量不上图
    "sludge_shusong": UnitProjection(
        "sludge_shusong",
        plan_keys={"pipe_diameter": "d_pipe"},
        section_keys={},
        primitive_dims={},
        instance_counts={},
        non_drawn=("d_raw", "ds_in", "ds_out", "i_req", "i_slope", "p_in",
                   "p_out", "q_h", "q_in", "q_out", "q_si", "v_act",
                   "v_grav"),
        dim_of={"d_pipe": _L, "d_raw": _D, "ds_in": _D, "ds_out": _D,
                "i_req": _D, "i_slope": _D, "p_in": _D, "p_out": _D,
                "q_h": _D, "q_in": _D, "q_out": _D, "q_si": _D,
                "v_act": _D, "v_grav": _D},
    ),
    # 污泥提升泵站：逐槽镜像 municipal_wushui_tisheng（plan 1/section 1/
    # primitive 1/counts 2 同构——泵位键名 n_total=BZ-F5，市政
    # n_pump_total 同义）；head 子字典四键水头损失校核量 non_drawn
    "sludge_bengzhan": UnitProjection(
        "sludge_bengzhan",
        plan_keys={"pipe_diameter": "d_pipe"},
        section_keys={"well_depth": "h_well_total"},
        primitive_dims={"depth": "h_well_total"},
        instance_counts={"pump": "n_total", "pump_duty": "n_pump_duty"},
        non_drawn=("a_well", "d_raw", "ds_in", "ds_out", "h_friction",
                   "h_local", "h_loss", "h_pump", "n_pump_raw", "n_start",
                   "p_in", "p_out", "q_h", "q_in", "q_out", "q_pump_h",
                   "q_pump_si", "v_act", "v_concrete", "v_well"),
        dim_of={"a_well": _D, "d_pipe": _L, "d_raw": _D, "ds_in": _D,
                "ds_out": _D, "h_friction": _D, "h_local": _D,
                "h_loss": _D, "h_pump": _D, "h_well_total": _D,
                "n_pump_duty": _D, "n_pump_raw": _D, "n_start": _D,
                "n_total": _D, "p_in": _D, "p_out": _D, "q_h": _D,
                "q_in": _D, "q_out": _D, "q_pump_h": _D,
                "q_pump_si": _D, "v_act": _D, "v_concrete": _D,
                "v_well": _D},
    ),
    # 污泥重力浓缩池：d 池径档取整（NS-F5 d_raw 原始径对照）+
    # h_total 有效水深——cylinder(d, h_total) 两槽全触发
    "sludge_nongsuo": UnitProjection(
        "sludge_nongsuo",
        plan_keys={"overall_diameter": "d"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"diameter": "d", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_load", "a_req", "a_single", "a_time", "d_raw",
                   "ds_in", "ds_out", "ds_sup", "p_in", "p_out", "q_in",
                   "q_out", "q_solid_act", "q_sup", "q_thick",
                   "v_concrete"),
        dim_of={"a_load": _D, "a_req": _D, "a_single": _D, "a_time": _D,
                "d": _L, "d_raw": _D, "ds_in": _D, "ds_out": _D,
                "ds_sup": _D, "h_total": _D, "p_in": _D, "p_out": _D,
                "q_in": _D, "q_out": _D, "q_solid_act": _D,
                "q_sup": _D, "q_thick": _D, "v_concrete": _D},
    ),
    # 污泥消化：d 池径档取整（XH-F10 d_raw 对照）；无 h_total 键——
    # cylinder 两槽不全不触发图元（空组，ningjiao box 三槽不全先例）；
    # v_single 是单池容积非台数——counts 禁用
    "sludge_xiaohua": UnitProjection(
        "sludge_xiaohua",
        plan_keys={"overall_diameter": "d"},
        section_keys={},
        primitive_dims={"diameter": "d"},
        instance_counts={},
        non_drawn=("d_raw", "ds_in", "ds_out", "l_vs", "p_in", "p_out",
                   "q_in", "q_out", "v_biogas", "v_concrete", "v_single",
                   "v_total", "w_vs", "w_vs_deg"),
        dim_of={"d": _L, "d_raw": _D, "ds_in": _D, "ds_out": _D,
                "l_vs": _D, "p_in": _D, "p_out": _D, "q_in": _D,
                "q_out": _D, "v_biogas": _D, "v_concrete": _D,
                "v_single": _D, "v_total": _D, "w_vs": _D,
                "w_vs_deg": _D},
    ),
    # 污泥脱水：n_machine_total 脱水机台数（工作+备用）→实例数
    # （machine 新语义标签——scene _INSTANCE_KINDS 本批 M3D2 D2 登记）
    "sludge_tuoshui": UnitProjection(
        "sludge_tuoshui",
        plan_keys={},
        section_keys={},
        primitive_dims={},
        instance_counts={"machine": "n_machine_total",
                         "machine_duty": "n_machine_duty"},
        non_drawn=("ds_cake", "ds_filtrate", "ds_in", "ds_out",
                   "n_machine_raw", "p_in", "p_out", "q_cake",
                   "q_filtrate", "q_in", "q_in_h", "q_out", "w_pam"),
        dim_of={"ds_cake": _D, "ds_filtrate": _D, "ds_in": _D,
                "ds_out": _D, "n_machine_duty": _D, "n_machine_raw": _D,
                "n_machine_total": _D, "p_in": _D, "p_out": _D,
                "q_cake": _D, "q_filtrate": _D, "q_in": _D,
                "q_in_h": _D, "q_out": _D, "w_pam": _D},
    ),
    # 污泥干化：设备/热量质量衡算类——13 键全 non_drawn（m_in/m_out
    # 干泥量、q_heat/w_fuel 热量、a_dry 干化场面积均衡算校核量）
    "sludge_ganhua": UnitProjection(
        "sludge_ganhua",
        plan_keys={},
        section_keys={},
        primitive_dims={},
        instance_counts={},
        non_drawn=("a_dry", "ds_in", "ds_out", "m_check", "m_in",
                   "m_out", "p_in", "p_out", "q_heat", "q_in", "q_out",
                   "w_evap", "w_fuel"),
        dim_of={"a_dry": _D, "ds_in": _D, "ds_out": _D, "m_check": _D,
                "m_in": _D, "m_out": _D, "p_in": _D, "p_out": _D,
                "q_heat": _D, "q_in": _D, "q_out": _D, "w_evap": _D,
                "w_fuel": _D},
    ),
})
