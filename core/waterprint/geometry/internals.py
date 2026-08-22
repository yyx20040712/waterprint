"""内部构件布局：曝气头/搅拌器/填料的数量与摆放（实例数来自计算结果）。

输入:  单元结果（设备台数/个数/间距类字段 ID）+ assumptions
输出:  实例化图元组（instance_count + 阵列变换，GPU InstancedMesh 数据源）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/geometry/test_internals.py）
#
# 【公开接口】
#   internal_instances(unit_result, assumptions) -> tuple[InstanceGroup, ...]
#   class InstanceGroup：semantic（aerator/paddle/media/gate/pipe）、
#       prototype（Primitive）、count（实例数）、placements
#       （阵列参数：origin/step/rows/cols——展开由渲染层或显式列表）
#
# 【行为规格】
#   R1 数量唯一真源 = 计算结果字段（曝气头个数、搅拌器台数、填料体积
#      换算个数等已在单元 compute 完成）；几何层只摆放不计数
#      （双源漂移根除，§10.5）。
#   R2 布局规则（曝气头均布行列、填料支架层高、搅拌器安装位）来自
#      assumptions/coefficients（出处入库），节点标注来源键。
#   R3 阵列表达优先于逐实例列表：千级构件用 (origin, step, rows, cols)
#      参数化（数据量 O(1)）；不规则摆放才允许显式坐标列表。
#   R4 语义标签稳定集合：aerator/paddle/media/gate/opening/pipe…
#      新增语义先登记 scene.py 规格（前端材质映射依赖）。
#   R5 开口/穿孔（CSG 场景）：kind=opening 的实例组显式声明，
#      供前端 three-bvh-csg 定点使用（§12.6 CSG 仅限开口）。
#
# 【测试要求】count == 结果字段值、阵列参数展开数 == count、
#   语义标签 ∈ 稳定集合、来源键标注。
#
# 【参照】重写计划 §10.5/§12.6
# ══════════════════════════════════════════════════════════════════
