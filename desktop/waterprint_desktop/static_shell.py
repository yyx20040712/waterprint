"""客户端模式静态壳：webapp dist 本地静态服务（127.0.0.1:8620）。

输入:  webapp dist 目录（pnpm -C webapp build 产物——vite 默认 dist/）
输出:  build_static_app（Starlette StaticFiles html=True）+serve_static
       （UvicornServeHandle 起停便捷门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_static_shell.py）
#
# 【公开接口】
#   resolve_webapp_dist() -> Path：WATERPRINT_DESKTOP_WEBAPP_DIST env
#      覆盖，缺省=仓库根 webapp/dist（包定位上溯——desktop/ 顶层包
#      parents[2]=仓库根；打包形态经 env 指向安装器布局，见
#      desktop/packaging/README.md）
#   build_static_app(dist) -> Starlette：StaticFiles(directory=dist,
#      html=True) 挂 "/"——SPA index.html 回退（vite 产物约定）+子路径
#      静态资产直供；无 API 面（客户端模式全部 API 走远程——b6 通路）
#   serve_static(dist, port) -> UvicornServeHandle：起静态壳便捷门
#      （绑定恒 127.0.0.1——roles.SHELL_BIND_HOST 单源；端口默认
#      SHELL_PORT，测试传 0=临时端口）
#
# 【行为规格】
#   R1 静态壳无引擎语义：本件零 waterprint_server import——客户端模式
#      「本地不起引擎」由 import 面结构保证（check_module_graph 真实
#      import 扫描强制）。
#   R2 dist 缺席=ValueError（fail fast：壳无产物即无服务面——不装空壳
#      静默 404）。
#
# 【测试要求】静态可达（GET / =index.html）/子路径资产/缺席拒绝。
#
# 【参照】ADR-028；CORS 对端=server settings.allowed_origins 缺省
#   http://127.0.0.1:8620（b5/b6 契约）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from waterprint_desktop.roles import SHELL_BIND_HOST, SHELL_PORT
from waterprint_desktop.server_thread import UvicornServeHandle


def resolve_webapp_dist() -> Path:
    """webapp dist 解析：env 覆盖，缺省=仓库根 webapp/dist（包定位）。"""
    override = os.environ.get("WATERPRINT_DESKTOP_WEBAPP_DIST")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "webapp" / "dist"


def build_static_app(dist: Path) -> Starlette:
    """静态壳应用（纯静态；dist 缺席 ValueError fail fast）。"""
    if not (dist / "index.html").is_file():
        raise ValueError(
            f"webapp dist 不完整（缺 index.html）：{dist}——先 pnpm -C webapp"
            " build 或设 WATERPRINT_DESKTOP_WEBAPP_DIST 指向产物目录"
        )
    return Starlette(routes=[
        Mount("/", app=StaticFiles(directory=dist, html=True), name="shell"),
    ])


def serve_static(dist: Path, port: int = SHELL_PORT) -> UvicornServeHandle:
    """起静态壳（127.0.0.1 固定绑定——单源 SHELL_BIND_HOST）。"""
    app = build_static_app(dist)
    handle = UvicornServeHandle(app, host=SHELL_BIND_HOST, port=port)
    handle.start()
    return handle
