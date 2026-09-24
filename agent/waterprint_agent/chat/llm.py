"""LLM 客户端（OpenAI 兼容 /chat/completions——stdlib urllib 零新依赖）。

输入:  ChatConfig（三中性键 env）+messages+tools schema
输出:  LlmReply（content/tool_calls 解析面）；不可用=LlmUnavailableError（密钥零泄漏）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/llm.py
#   职责：对话编排 LLM 单步调用面——urllib.request 直连（禁第三方 http
#       库=依赖零破面，审 W1 处置）；ChatConfig 三中性键 env 装载。
#   禁区：禁 import core/server/fastmcp（纯 stdlib）；禁密钥落任何异常
#       消息/日志（HTTP 错误只回显状态码——响应体不透传，N3 值级脱敏
#       前置）；禁流式协议（环按步请求，流式由桥层承载——设计终裁 §一）。
#
# 【行为规格】
#   R1 配置：三键=WATERPRINT_AI_BASE_URL/API_KEY/MODEL（无缺省——
#      未配置=available() False，调用方 fail-fast 降级，N2 处置）；
#      timeout_s 缺省 120（设计终裁 §七：社区长推理上限保守取小）。
#   R2 调用：POST {base}/chat/completions，payload={model,messages,
#      tools,tool_choice:"auto"}；Bearer 鉴权头。
#   R3 不可用族：HTTPError（只回显码）/URLError/超时/OSError →
#      LlmUnavailableError（type 名+状态码，零 body 零密钥）。
#   R4 解析：choices[0].message——content 空串容错；tool_calls
#      arguments JSON 串解析失败=空 dict（不炸环）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

__all__ = [
    "ChatConfig",
    "LlmReply",
    "LlmUnavailableError",
    "ToolCall",
    "chat_completion",
]

_BASE_URL_KEY = "WATERPRINT_AI_BASE_URL"
_API_KEY_KEY = "WATERPRINT_AI_API_KEY"
_MODEL_KEY = "WATERPRINT_AI_MODEL"
_TIMEOUT_KEY = "WATERPRINT_AI_LLM_TIMEOUT_S"
_DEFAULT_TIMEOUT_S = 120


class LlmUnavailableError(RuntimeError):
    """LLM 端点不可用族（网络/HTTP/配置）——环降级唯一信号。"""


@dataclass(frozen=True)
class ChatConfig:
    """环配置（三中性键+环旋钮——frozen 值对象）。"""

    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_s: int = _DEFAULT_TIMEOUT_S
    max_iterations: int = 12
    window_turns: int = 20

    @classmethod
    def from_env(cls) -> ChatConfig:
        """env 装载（三键无缺省；timeout 可调）。"""
        raw_timeout = os.environ.get(_TIMEOUT_KEY, "")
        timeout = _DEFAULT_TIMEOUT_S
        if raw_timeout.isdecimal():
            timeout = int(raw_timeout)
        return cls(
            base_url=os.environ.get(_BASE_URL_KEY, ""),
            api_key=os.environ.get(_API_KEY_KEY, ""),
            model=os.environ.get(_MODEL_KEY, ""),
            timeout_s=timeout,
        )

    def available(self) -> bool:
        """三键齐备才可调（缺一=降级 fail-fast）。"""
        return bool(self.base_url and self.api_key and self.model)


@dataclass(frozen=True)
class ToolCall:
    """单条工具调用（arguments 已解析为 dict）。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LlmReply:
    """单步回复（content 与 tool_calls 可同时在场——并行调用语义）。"""

    content: str
    tool_calls: tuple[ToolCall, ...]


def chat_completion(
    config: ChatConfig, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
) -> LlmReply:
    """单步对话补全（urllib 直连——R2/R3/R4）。"""
    url = config.base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": config.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {config.api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_s) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise LlmUnavailableError(f"LLM 端点 HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LlmUnavailableError(f"LLM 端点不可达（{type(exc).__name__}）") from None
    choices = body.get("choices") or []
    if not choices:
        raise LlmUnavailableError("LLM 响应缺 choices（端点兼容性）")
    message = choices[0].get("message") or {}
    calls: list[ToolCall] = []
    for call in message.get("tool_calls") or ():
        function = call.get("function") or {}
        raw_args = function.get("arguments") or "{}"
        try:
            arguments = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
        except ValueError:
            arguments = {}
        calls.append(
            ToolCall(
                id=str(call.get("id", "")),
                name=str(function.get("name", "")),
                arguments=arguments,
            )
        )
    return LlmReply(content=str(message.get("content") or ""), tool_calls=tuple(calls))
