#!/usr/bin/env bash
# Linux 桌面壳环境引导（唯一正确建法——禁止裸 `uv sync` 重建 venv）
#
# 为什么：窗口后端依赖系统 python3-gi（PyGObject）——PyPI 仅发 sdist，
# 本机无 GNOME dev 头件编不动；唯一可用来源=apt 的 python3-gi（绑系统
# Python 3.12）。因此 venv 必须：①基于 /usr/bin/python3.12 建；②带
# --system-site-packages（裸 `uv sync` 自建的 venv 该开关=false，gi
# 不可见，启动即"QT or GTK ... installed"失败——pyproject 头注同口径）。
#
# 前置（一次性）：sudo apt install python3-gi gir1.2-webkit2-4.1
set -euo pipefail
cd "$(dirname "$0")"

uv python pin /usr/bin/python3.12
rm -rf .venv
uv venv --python /usr/bin/python3.12 --system-site-packages
uv sync

# 引导末验：gi 链+WebKit2 typelib 不通即非零退出（不静默）
uv run python -c "import gi; gi.require_version('Gtk','3.0'); gi.require_version('WebKit2','4.1'); print('GTK 后端 OK')"
