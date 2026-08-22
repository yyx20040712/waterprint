"""项目文件 design/view 双态 schema（可复算与 git 友好的分界，ADR-004）。

输入:  项目 JSON（磁盘/网络边界）
输出:  ProjectFile 校验模型（pydantic 严格模式：未知字段拒绝）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_project_schema.py）
#
# 【公开接口】
#   class DesignState：参与 content-hash 与可复算的一切——
#       nodes（单元实例+参数覆盖）、edges、约束选择、工况受检单元、
#       假设覆盖（assumptions 键→值）、进水/标准绑定
#   class ViewState：不参与哈希——画布布局、相机位姿、窗口布局、时间戳
#   class Metadata：format_version / content_hash / engine_version / data_version
#   class ProjectFile：design + view + metadata
#   parse_project(data: Mapping) -> ProjectFile   严格校验正门
#
# 【行为规格】
#   R1 双态分界是 R10 病灶的根除：view 任何变化不算 dirty、不触发重算、
#      不进 content_hash；design 变化才产生新 hash（§12.3）。
#   R2 pydantic strict + extra="forbid"：未知字段、错误类型、深度/大小
#      超限（安全上限，server 层配置）一律拒绝（§18 文件上传面）。
#   R3 可复算三元组记录在 metadata：content_hash(design) + engine_version
#      + data_version；三者任一变化 = 全部结果过期（§16 A8）。
#   R4 项目内禁止随机 ID/时间戳进入 design 态（确定性序列化前提，
#      序列化规则在 project/io.py 执行，本文件只定义 schema）。
#   R5 format_version 迁移由 project/migration.py 链式处理，本 schema
#      永远只描述当前版。
#
# 【测试要求】view 变更不改 content_hash、未知字段拒绝、
#   序列化往返无损（与 project/io 联合）。
#
# 【参照】重写计划 §12.3/§11 R10；ADR-004
# ══════════════════════════════════════════════════════════════════
