"""项目 CRUD 端点：创建/读取/保存/列表/校验（薄，只做协议转换）。

输入:  pydantic 请求（项目数据/列表查询）
输出:  pydantic 响应（项目元数据/校验报告）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/routers/test_projects.py）
#
# 【端点集（v1 冻结）】
#   POST   /api/projects                    创建（空项目或导入 JSON）
#   GET    /api/projects                    列表（名称/哈希/时间元数据）
#   GET    /api/projects/{id}               读取（完整 ProjectFile）
#   PUT    /api/projects/{id}               保存（design+view，返回新
#                                          content_hash 与 dirty 状态）
#   POST   /api/projects/{id}/validate      校验（零计算快速反馈）
#
# 【行为规格】
#   R1 路径安全：{id} 白名单字符集校验（拒绝 ../ 与绝对路径），
#      文件操作全部限制在 Settings.projects_dir 内。
#   R2 上传防弹（§18）：JSON 大小/深度上限（Settings）；
#      校验失败 422 带字段路径错误清单（core parse_project 透传）。
#   R3 保存语义：返回新 content_hash；design 变更与 view 变更在
#      响应中区分（view-only 保存不触发 dirty 重算语义 §17.1）。
#   R4 并发防护：同项目写锁探测（.lock——冲突 409 带持有者信息，
#      §17.3 v1 单用户最低成本方案）。
#   R5 禁 pickle：项目 IO 永远 JSON（§18 IPC 行）。
#
# 【测试要求】CRUD 往返、越界 id 拒绝、大小/深度炸弹 422、
#   写锁 409、校验端点错误清单。
#
# 【参照】重写计划 §13.4/§17.3/§18
# ══════════════════════════════════════════════════════════════════
