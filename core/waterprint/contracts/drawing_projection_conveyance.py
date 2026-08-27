"""输送线出图取数表（UF-32 方案②）：输送单元冻结几何取数声明（分线表④）。

输入:  输送单元 compute 实跑 dims 键全量（输送链单点图实跑提取，
       2026-08-27 M3D3 实录 39 键）
输出:  CONVEYANCE_PROJECTIONS（plan/section/primitive/counts/non_drawn 五类
       取数声明 + 每键量纲列——聚合正门 drawing_projection 消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M3D3 D1 新建分线表④——战役收口批：四线 32/32 全覆盖；
#   对账锁定测试 tests/contracts/test_drawing_projection.py）
#
# 【公开接口】
#   CONVEYANCE_PROJECTIONS: Final[Mapping[str, UnitProjection]]  输送线
#       4 单元逐个声明（unit_id 前缀 conveyance_）
#
# 【行为规格】
#   R1 表覆盖=单元 dims 键全量：plan∪section∪primitive∪counts∪non_drawn
#      == 该单元 compute 实际 dims 输出键集（对账测试以输送链实跑为证
#      ——inlet→jishuijing→peishuijing→jipeishuijing→peishuiqu 链式，
#      动态多口单元下游边直接引 out_1 口）；non_drawn 与四类取数不
#      相交（穿流校核量不上图）。
#   R2 五类语义不静默：每键归入至少一类（禁遗漏）；plan/primitive
#      重叠合法（取数面非互斥分区）。
#   R3 dim_of 逐键合法：全部 ∈ DimKey 枚举；量纲起草依据=输送 4 包
#      manifest FormulaSpec output_dim 实读 35 条（JS-F1~F7/PJ-F1~F12/
#      JP-F1~F9/PQ-F1~F7——与污泥线全 DIMENSIONLESS 不同，输送线
#      公式输出即真量纲 _L/_A/_V/_T/_F/_VEL）+非公式导出键按市政
#      同名先例（d/d_well 档取整几何键 _L——bashi_jiliangcao d/
#      nongsuo d 先例）——AI 起草待领域专家追认。
#   R5 只读消费 dims 键名（字符串），不 import units_lib、不做任何
#      计算——纯声明面（L0 准入类别①，GR-36）。
#
# 【起草口径】分类原则同前批=几何上图量入取数类，穿流校核量
#   （q_each/q_series/a_act/t_act/v_act/h_head 等）全 non_drawn；
#   三井 cylinder(d,h_total) 两槽全触发（peishuijing 井室为体、
#   孔口为口——primitive 取井室径 d_well，plan 双径槽分记孔口/井室）；
#   peishuiqu 全线唯一 water_depth 语义键=h_water（PQ-F3 渠内水深）
#   入 section，无总长键（渠长是参数）→无 plan/primitive 槽——深度
#   键入 section 不入 primitive，避免误导性半槽（M3D1 ziwai 同裁）；
#   四单元 instance_counts 全空（n 是分流口数/并联系列数非设备台数
#   ——台数语义缺失，不造键）。
#
# 【禁止事项】不得出现数值字面量（纯键名映射+量纲枚举）；不得
#   import units_lib 或任何 L2+ 层。
#
# 【测试要求】tests/contracts/test_drawing_projection.py：输送 4 单元
#   链式实跑键集对账 + DimKey 合法性 + 分线键集 disjoint（四线）+
#   32/32 收口断言；test_drawing_projection_conveyance.py 薄镜像
#   （宪法 §6）。
#
# 【参照】Ruling ①（2026-08-26）；UF-32；ADR-006；重写计划 §7 验收行
#   （32 单元四件套）；M3D3 简报 D1；explore-M3D1-freeze §四输送表
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from waterprint.contracts.drawing_projection_types import UnitProjection
from waterprint.contracts.quantity import DimKey

__all__ = ["CONVEYANCE_PROJECTIONS"]

_L = DimKey.LENGTH
_A = DimKey.AREA
_V = DimKey.VOLUME
_T = DimKey.TIME
_F = DimKey.FLOW
_VEL = DimKey.VELOCITY

# ── 输送线 4 单元取数表（2026-08-27 输送链实跑提取 39 键逐键归位；
#    AI 起草待追认。分类原则=几何上图量入取数类，穿流校核量入
#    non_drawn——对账测试是覆盖最终裁决，缺键/多键即红）────
CONVEYANCE_PROJECTIONS: Final[Mapping[str, UnitProjection]] = MappingProxyType({
    # 集水井：d 井径档取整（JS-F3 d_raw 原始径 non_drawn 对照）+
    # h_total 井总深——cylinder(d, h_total) 两槽全触发
    "conveyance_jishuijing": UnitProjection(
        "conveyance_jishuijing",
        plan_keys={"overall_diameter": "d"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"diameter": "d", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_act", "a_well", "d_raw", "t_act", "v_concrete",
                   "v_well"),
        dim_of={"a_act": _A, "a_well": _A, "d": _L, "d_raw": _L,
                "h_total": _L, "t_act": _T, "v_concrete": _V,
                "v_well": _V},
    ),
    # 配水井：井室为体、孔口为口——primitive 取井室径 d_well（cylinder
    # 两槽全触发），plan 双径槽分记孔口 d/井室 d_well；h_head 孔口
    # 作用水头为校核量 non_drawn
    "conveyance_peishuijing": UnitProjection(
        "conveyance_peishuijing",
        plan_keys={"outlet_diameter": "d", "chamber_diameter": "d_well"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"diameter": "d_well", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_act", "a_out", "a_well", "a_well_act", "d_raw",
                   "d_well_raw", "h_head", "q_each", "q_series", "v_act",
                   "v_concrete"),
        dim_of={"a_act": _A, "a_out": _A, "a_well": _A, "a_well_act": _A,
                "d": _L, "d_raw": _L, "d_well": _L, "d_well_raw": _L,
                "h_head": _L, "h_total": _L, "q_each": _F,
                "q_series": _F, "v_act": _VEL, "v_concrete": _V},
    ),
    # 集配水井：集水（v_well/a_well/d/t_act）+分流（q_each/q_series）
    # 合一井——cylinder(d, h_total) 两槽全触发（jishuijing 同构）
    "conveyance_jipeishuijing": UnitProjection(
        "conveyance_jipeishuijing",
        plan_keys={"overall_diameter": "d"},
        section_keys={"pool_depth": "h_total"},
        primitive_dims={"diameter": "d", "depth": "h_total"},
        instance_counts={},
        non_drawn=("a_act", "a_well", "d_raw", "q_each", "q_series",
                   "t_act", "v_concrete", "v_well"),
        dim_of={"a_act": _A, "a_well": _A, "d": _L, "d_raw": _L,
                "h_total": _L, "q_each": _F, "q_series": _F, "t_act": _T,
                "v_concrete": _V, "v_well": _V},
    ),
    # 配水渠：全线唯一 water_depth 语义键=h_water（PQ-F3 渠内水深）
    # +pool_depth=h_total 渠总深——无总长键（渠长是布置面参数）→无
    # plan/primitive 槽，深度键入 section 不入 primitive（避免误导性
    # 半槽，M3D1 ziwai 同裁；h_weir 堰顶水头/断面量为校核 non_drawn）
    "conveyance_peishuiqu": UnitProjection(
        "conveyance_peishuiqu",
        plan_keys={},
        section_keys={"water_depth": "h_water", "pool_depth": "h_total"},
        primitive_dims={},
        instance_counts={},
        non_drawn=("a_channel", "h_weir", "q_each", "q_series", "v_end"),
        dim_of={"a_channel": _A, "h_total": _L, "h_water": _L,
                "h_weir": _L, "q_each": _F, "q_series": _F,
                "v_end": _VEL},
    ),
})
