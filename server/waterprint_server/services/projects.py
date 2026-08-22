"""项目服务用例：创建/读取/保存/列表/校验/迁移导入（core project 层的编排壳）。

输入:  项目 id / ProjectFile 数据（routers 透传）
输出:  项目元数据 / ProjectFile / 校验报告（core 产出包装）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_projects.py）
#
# 【公开接口】
#   create_project(payload) / list_projects() / read_project(id) /
#   save_project(id, project) -> SaveOutcome（新 hash + design_changed）
#   validate_project(id) -> ValidationReport
#   import_legacy(payload) -> ImportReport（M4，best-effort 映射清单）
#
# 【行为规格】
#   R1 文件操作只经 core.project.io（确定性序列化/原子保存/锁探测
#      在 core 实现）；本层加目录白名单与 id 校验（§18）。
#   R2 save 返回 design_changed 布尔（hash 对比）——routers 据此响应
#      dirty 语义（§17.1 项目保存行：保存只写 view 态不触发计算）。
#   R3 导入旧格式：core.project.migration + best-effort 字段映射，
#      未映射字段清单必须完整返回（禁止静默丢弃）。
#   R4 禁 pickle（§18）；项目列表元数据来自文件读取（无独立索引库）。
#
# 【测试要求】往返保存 design_changed 语义、导入未映射清单、
#   id 白名单、锁冲突透传。
#
# 【参照】重写计划 §13.4/§17.1/§18
# ══════════════════════════════════════════════════════════════════
