#!/usr/bin/env bash
# WaterPrint 桌面启动入口（.desktop Exec 消费；亦可终端直跑）
# venv 已由 bootstrap.sh 建好（系统 Python 3.12+system-site-packages）——
# 此处只跑不建；若检测到 gi 不可用提示先跑 bootstrap.sh。
set -euo pipefail
cd "/home/yyx/work/智水蓝图/waterprint/desktop"

# WebKitGTK VM 白屏规避（与 main.py R5 同口径——双保险，先 export 后 exec）
export WEBKIT_DISABLE_DMABUF_RENDERER="${WEBKIT_DISABLE_DMABUF_RENDERER:-1}"
export WEBKIT_DISABLE_COMPOSITING_MODE="${WEBKIT_DISABLE_COMPOSITING_MODE:-1}"

if ! uv run python -c "import gi" 2>/dev/null; then
    echo "检测到 gi 不可用（venv 被重建丢失 system-site-packages？）——先跑 bootstrap.sh" >&2
    exit 1
fi
exec uv run python -m waterprint_desktop.main
