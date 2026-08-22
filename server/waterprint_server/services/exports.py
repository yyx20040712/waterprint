"""导出服务用例：计算书/图纸/概算/审计的产物编排（stale 守门）。

输入:  项目 id + 导出 kind + condition_key + 选项
输出:  产物文件路径与元数据（含三元组摘要）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_exports.py）
#
# 【公开接口】
#   create_export(project_id, kind, condition_key, options,
#                 force=False) -> ExportHandle
#   list_exports(project_id) -> tuple[ExportMeta, ...]
#
# 【行为规格】
#   R1 stale 守门（§17.1 导出行）：最近结果集三元组 vs 当前项目
#      hash 不一致且未 force → 拒绝（上游 409）；force 导出的产物
#      文件名与元数据显式标注旧三元组（产物永不冒充）。
#   R2 产物编排：core 各渲染器（calcbook/audit/dxf/estimate）产出
#      写入 exports_dir；产物注册表（列表查询）只记元数据不复制数据。
#   R3 批量导出走低优先级队列（§17.1）；单产物即时生成上限（超过
#      阈值转任务，防同步请求超时）。
#   R4 文件名确定性：项目 id + kind + condition + 三元组摘要
#      （禁止当前时钟——同名同输入即同文件，幂等重导出覆盖校验）。
#
# 【测试要求】stale 拒绝与 force 标注、确定性命名、批量转任务。
#
# 【参照】重写计划 §17.1/§18
# ══════════════════════════════════════════════════════════════════
