"""环境配置：env → Settings（pydantic-settings，一切可调参数的唯一住所）。

输入:  环境变量 / .env
输出:  Settings（不可变，应用启动注入）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/test_settings.py）
#
# 【公开接口】
#   class Settings(BaseSettings)：模型字段——
#       projects_dir（项目文件根，路径安全基点）
#       exports_dir（导出产物根，路径安全基点）
#       data_dir（数据包根：单价/系数/模板）
#       calc_workers（进程池大小，默认 CPU−1）
#       max_upload_mb / max_excel_rows（§18 上传面）
#       cache_entries / cache_mb（LRU 与落盘上限 §17.2）
#       task_queue_priorities（FIFO 优先级 §17.1）
#       log_level / log_file
#   get_settings() -> Settings（lru_cache，测试可覆盖）
#
# 【行为规格】
#   R1 一切路径类配置只作基点：业务路径 = 基点内拼接 + 分量校验
#      （拒绝 ".."/绝对路径，§18 路径安全——routers/services 全部遵守，
#      测试构造越界路径断言拒绝）。
#   R2 配置校验：目录存在或可创建；calc_workers >= 1；
#      非法值启动即失败（fail fast，不静默默认）。
#   R3 密钥/外发零依赖：内网工具无外部服务配置项；不出现任何
#      出站 URL 配置（§18 出站请求面——零外部请求是产品约束）。
#
# 【测试要求】默认值合法、非法值拒绝、路径越界防护的消费方行为。
#
# 【参照】重写计划 §18/§17.2
# ══════════════════════════════════════════════════════════════════
