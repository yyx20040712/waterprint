"""test_chat_llm——OpenAI 兼容客户端：urllib 零依赖+tool_calls 解析+不可用收敛。

输入:  本地 http 假端点（ canned 响应）/封闭端口
输出:  请求形态/解析/密钥零泄漏断言（B4-4b 子批 1）
"""

from __future__ import annotations

import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from waterprint_agent.chat.llm import (
    ChatConfig,
    LlmReply,
    LlmUnavailableError,
    ToolCall,
    chat_completion,
)

_KEY = "sk-test-secret-key"


def _start_server(handler: type[BaseHTTPRequestHandler]) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/v1"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_config_from_env(monkeypatch) -> None:
    """三中性键 env 装载；缺失=available() False。"""
    monkeypatch.delenv("WATERPRINT_AI_BASE_URL", raising=False)
    monkeypatch.delenv("WATERPRINT_AI_API_KEY", raising=False)
    monkeypatch.delenv("WATERPRINT_AI_MODEL", raising=False)
    empty = ChatConfig.from_env()
    assert empty.available() is False
    monkeypatch.setenv("WATERPRINT_AI_BASE_URL", "http://x/v1")
    monkeypatch.setenv("WATERPRINT_AI_API_KEY", _KEY)
    monkeypatch.setenv("WATERPRINT_AI_MODEL", "m-x")
    assert ChatConfig.from_env().available() is True


def test_completion_parses_tool_calls() -> None:
    """canned OpenAI 响应：content/tool_calls 解析+请求形态（model/tools/鉴权头）。"""
    seen: list[dict] = []
    auth: list[str] = []

    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            auth.append(self.headers.get("Authorization", ""))
            reply = {
                "choices": [
                    {
                        "message": {
                            "content": "先看单元目录",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "wp_list_units",
                                        "arguments": "{\"category\": \"municipal\"}",
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
            data = json.dumps(reply).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args: object) -> None:  # 静默
            return

    server, base = _start_server(_Handler)
    try:
        config = ChatConfig(base_url=base, api_key=_KEY, model="m-x", timeout_s=10)
        tools = [{"type": "function", "function": {"name": "wp_list_units", "parameters": {}}}]
        reply = chat_completion(config, [{"role": "user", "content": "看目录"}], tools)
    finally:
        server.shutdown()
    assert seen[0]["model"] == "m-x"
    assert seen[0]["tools"] == tools
    assert seen[0]["tool_choice"] == "auto"
    assert auth[0] == f"Bearer {_KEY}"
    assert isinstance(reply, LlmReply)
    assert reply.content == "先看单元目录"
    assert reply.tool_calls == (
        ToolCall(id="call-1", name="wp_list_units", arguments={"category": "municipal"}),
    )


def test_unavailable_on_connection_refused() -> None:
    """封闭端口：LlmUnavailableError 且消息不含密钥。"""
    config = ChatConfig(
        base_url=f"http://127.0.0.1:{_free_port()}/v1", api_key=_KEY, model="m-x", timeout_s=2
    )
    with pytest.raises(LlmUnavailableError) as err:
        chat_completion(config, [{"role": "user", "content": "x"}], [])
    assert _KEY not in str(err.value)


def test_unavailable_on_http_error() -> None:
    """HTTP 500：错误消息只含状态码（响应体不回显——密钥零泄漏面）。"""
    body_echo: list[bytes] = []

    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body_echo.append(self.rfile.read(int(self.headers["Content-Length"])))
            data = b'{"error": "upstream rejected sk-test-secret-key"}'
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args: object) -> None:
            return

    server, base = _start_server(_Handler)
    try:
        config = ChatConfig(base_url=base, api_key=_KEY, model="m-x", timeout_s=10)
        with pytest.raises(LlmUnavailableError) as err:
            chat_completion(config, [{"role": "user", "content": "x"}], [])
    finally:
        server.shutdown()
    assert "500" in str(err.value)
    assert _KEY not in str(err.value)
