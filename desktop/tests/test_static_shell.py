"""static_shell.py 镜像测试：静态壳无头冒烟（联机第七批 ADR-028）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import MakeDist, http_get, port_open
from waterprint_desktop.roles import SHELL_BIND_HOST
from waterprint_desktop.static_shell import build_static_app, serve_static


def test_build_static_app_missing_dist_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="webapp dist 不完整"):
        build_static_app(tmp_path / "empty")


def test_serve_static_serves_index_and_assets(make_dist: MakeDist) -> None:
    dist = make_dist()
    handle = serve_static(dist, port=0)  # 临时端口（探测形态）
    try:
        port = handle.actual_port
        status, body, _ = http_get(f"http://{SHELL_BIND_HOST}:{port}/")
        assert status == 200
        assert "wp-test" in body  # index.html 主体（html=True 根回退）
        status_js, js_body, _ = http_get(f"http://{SHELL_BIND_HOST}:{port}/assets/app.js")
        assert status_js == 200
        assert "wp-test" in js_body
        status_404, _, _ = http_get(f"http://{SHELL_BIND_HOST}:{port}/no-such-file.css")
        assert status_404 == 404  # 缺资产 404（SPA 根回退不兜真实资产缺位）
    finally:
        port = handle.actual_port  # 停前取（停后 sockets 清空——actual_port 语义=运行期）
        handle.stop()
    assert not port_open(SHELL_BIND_HOST, port)  # 停后端口关


def test_serve_handle_restart_requires_new_handle(make_dist: MakeDist) -> None:
    dist = make_dist()
    handle = serve_static(dist, port=0)
    try:
        with pytest.raises(ValueError, match="一次性"):
            handle.start()  # R2：句柄一次性——重启=新句柄
    finally:
        handle.stop()
