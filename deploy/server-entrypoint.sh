#!/bin/sh
# C-1（e2e-fix-round3 R4 2026-09-25）：uvicorn 直启面启动校验收敛——
# Docker CMD/运维 uvicorn 直启先跑与 python -m 入口同源的
# validate_data_packages（缺包/manifest 空损=可执行文案拒绝启动，容器
# 非零码退出，healthcheck 永不转绿——请求期 500 晚拒在部署面终结），
# 再 exec uvicorn（exec 替换进程=PID 1 信号语义保持，docker stop 优雅
# 停机不受影响）。数据根经 env WATERPRINT_DATA_DIR（镜像 ENV 已钉
# /app/data；卷遮蔽场景同受防护）。
set -e
python -c "from waterprint_server.settings import get_settings, validate_data_packages; validate_data_packages(get_settings())"
exec "$@"
