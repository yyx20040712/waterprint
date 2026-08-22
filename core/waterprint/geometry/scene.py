"""场景图 schema 与装配：图元/变换/语义标签的场景树（全厂 <100ms 的总入口）。

输入:  PlantResult（几何类字段 ID）+ assumptions（超高/壁厚等）
输出:  SceneGraph（可序列化 JSON：图元声明 + 局部变换 + 实例数 + 语义标签）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/geometry/test_scene.py）
#
# 【公开接口】
#   class Primitive(不可变)：kind（box/cylinder/plane/water_surface/
#      extrusion）、dims（规范单位 m 裸值）、semantic（语义标签：
#      pool_wall/water_surface/aerator/paddle/media/pipe…）
#   class Node(不可变)：node_id、primitive、position/rotation/scale
#      （局部变换）、children、instance_count（InstancedMesh 依据）
#   build_scene(plant_result, assumptions, condition_key) -> SceneGraph
#   class SceneGraph：root + nodes + scene_version + condition_key
#
# 【行为规格】
#   R1 纯投影：场景图只由结果字段与假设生成，同结果同场景图（确定性、
#      可快照回归）；改参数 → 计算变 → 场景图自动变，不存在
#      "改了图忘改模型"（§10.2 关键约束）。
#   R2 图元组合优先（§12.6）：池壁=盒体、水面=半透明盒、渠道=拉伸体；
#      CSG 仅开口/穿孔场景（由 internals 显式声明 kind=opening），
#      禁止全模型布尔。
#   R3 千级重复构件必须 instance_count 表达（曝气头/填料：每类构件
#      一次 draw call 的数据前提）；数量来自 compute 结果（台数/个数
#      字段 ID），不在几何层重新推算。
#   R4 单位与坐标：场景单位 m、Y-up 或 Z-up 在 scene_version 声明
#      （前端渲染器读取，禁止两处各自假设）；地面标高来自 elevation
#      总线数据（经 app 装配传入）。
#   R5 性能预算：全厂场景图生成 <100ms（§18.1，pytest-benchmark 守卫）；
#      图元量级 ~ 每单元几百声明，纯 Python/初等算术完成。
#
# 【测试要求】确定性（同结果双跑同 JSON）、instance_count 汇总正确、
#   语义标签集合稳定、性能基准（<100ms）。
#
# 【参照】重写计划 §10.5/§12.6/§16 A7/§18.1
# ══════════════════════════════════════════════════════════════════
