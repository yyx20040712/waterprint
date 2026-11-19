"""desktop 测试共用 fixture：临时 webapp dist 构造 +HTTP 探测工具。

输入:  pytest（tmp_path/monkeypatch）
输出:  make_dist（两文件 dist 夹具工厂）+http_get/http_status（urllib
       零新依赖探测——无头冒烟正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028）：
#   测试禁开任何窗口（AGENTS 前台焦点红线）——本目录全部无头：逻辑层
#   单测+uvicorn/静态壳后台线程（无 create window）+urllib 探测。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

import pytest

# dist 夹具工厂类型别名（各测试消费面签名用）
MakeDist = Callable[[], Path]


@pytest.fixture
def make_dist(tmp_path: Path) -> Callable[[], Path]:
    """两文件 webapp dist 夹具工厂（index.html+assets/app.js——静态壳
    消费的最小完整产物形态）。"""

    def _make() -> Path:
        dist = tmp_path / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text(
            "<!doctype html><title>wp-test</title>", encoding="utf-8"
        )
        (dist / "assets" / "app.js").write_text(
            "console.log('wp-test');", encoding="utf-8"
        )
        return dist

    return _make


def http_get(url: str, headers: dict[str, str] | None = None) -> tuple[int, str, dict[str, str]]:
    """GET 探测（返回 状态码/主体/响应头小写键形态）——4xx/5xx 不抛。"""
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return (
                response.status,
                response.read().decode("utf-8"),
                {k.lower(): v for k, v in response.headers.items()},
            )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, body, {k.lower(): v for k, v in exc.headers.items()}


def http_get_json(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict, dict[str, str]]:
    """GET JSON 探测（meta/runtime 端点消费）。"""
    status, body, headers_ = http_get(url, headers)
    return status, json.loads(body) if status != 404 else {}, headers_


def port_open(host: str, port: int) -> bool:
    """TCP 端口探测（引擎确停断言——连接被拒=关）。"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, port)) == 0
