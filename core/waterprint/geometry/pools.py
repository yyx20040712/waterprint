"""池体/渠道/水面几何图元生成：单体构筑物的盒体/拉伸/水面包络。

输入:  单元结果（几何字段 ID：池长/宽/有效水深/超高/渠道断面…）+ assumptions
输出:  单体的图元+变换列表（供 scene.build_scene 装配）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/geometry/test_pools.py）
#
# 【公开接口】
#   pool_primitives(unit_result, assumptions) -> tuple[Node, ...]
#   channel_primitives(unit_result, assumptions) -> tuple[Node, ...]
#   water_surface_node(unit_result, assumptions) -> Node
#
# 【行为规格】
#   R1 尺寸字段只按 field_id 取（如 pool_length/pool_width/
#      water_depth/freeboard）；几何层零业务公式——池体尺寸是计算
#      结果，不在此重新计算（纯投影铁律）。
#   R2 超高/壁厚/板厚类构造尺寸来自 assumptions（带出处），标注于
#      节点 source_assumption_keys（三维上可查假设来源）。
#   R3 水面语义：water_surface 独立图元（半透明材质由前端按 semantic
#      渲染）；水位 = 池底 + 水深，这一加法是几何投影允许的唯一运算。
#   R4 并联池组：n_active 池按 manifest 工况语义排布（列间距来自
#      assumptions）；检修工况 n-1 池时场景图标注缺失池位置（警示渲染）。
#   R5 多格池（AAO 厌氧/缺氧/好氧分格）：分格尺寸来自结果字段，
#      隔墙图元 semantic=partition。
#
# 【测试要求】图元尺寸与结果字段一致、水面高程=底+深、
#   n_active 排布与检修标注、假设键标注完整。
#
# 【参照】重写计划 §10.5/§14.1
# ══════════════════════════════════════════════════════════════════
