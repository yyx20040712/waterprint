"""会话日志（D7）：jsonl 事件流+脱敏条款（AI 行为可对账的最小溯源面）。

输入:  事件 payload（工具参数/结果摘要等自由结构）
输出:  {sandbox}/sessions/{session_id}.jsonl（同步追加+行级 flush）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13）
#   路径：agent/waterprint_agent/sessionlog.py
#   职责：MCP 会话事件溯源（指令→工具调用→结果→参数补丁）；
#       脱敏三条款（正式区绝对路径→哈希、沙箱内绝对路径→相对、
#       环境变量值→占位）——payload 落盘前一律过 _sanitize。
#   禁区：禁 import core/server/fastmcp（纯 stdlib——main 顶层懒加载链）；
#       禁写 sessions/ 之外（沙箱内唯一落点）。
#
# 【公开接口】
#   class SessionLog(root: Path)：append(session_id, actor, type, payload)
#      -> int（seq）；events(session_id) -> list[dict]（读面）；
#      tool_call/tool_result 便捷面（actor="tool" 固定）。
#   事件行六键：{ts, session_id, seq, actor, type, payload}——
#      actor ∈ user|agent|tool；type ∈ instruction|tool_call|tool_result|param_patch。
#
# 【行为规格】
#   R1 追加语义：同步写+行级 flush（append 返回即可读）；seq 每会话
#      单调递增，实例重建按既有文件行数续接（不回卷）。
#   R2 脱敏（防御性——工具层不应主动传敏感值，本层兜底）：
#      a) Windows 绝对路径：沙箱内 → 沙箱相对 posix 形态；
#         沙箱外（正式区） → "{path:sha256 前 16 位}" 哈希标记；
#      b) 环境变量值（长度 ≥8 的非退化值）→ "<env:NAME>"（后置——见
#         _mask_text 顺序铁律）；
#      c) Path 对象与嵌套容器递归同面。
#   R3 会话 id 分量白名单（文件名拼界面拒分隔符/点分量注入）。
#   R4 已知限：字符串内嵌含空格路径的正则不覆盖（本项目路径面无空格
#      场景；过度匹配只会多脱敏不漏敏）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import re
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Final, Literal

__all__ = ["Actor", "EventType", "SessionLog"]

Actor = Literal["user", "agent", "tool"]
EventType = Literal["instruction", "tool_call", "tool_result", "param_patch"]

# 会话 id 分量白名单（同 server settings 分量纪律——拒 ../ 分隔符注入）。
_SESSION_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
# Windows 绝对路径（盘符或 UNC 起头，不含空白/引号——R4 已知限）。
_ABS_PATH_SOURCE: Final[str] = r"[A-Za-z]:[\\/][^\s\"'<>|]*|\\\\[^\s\"'<>|]+"
_ABS_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(_ABS_PATH_SOURCE)
# 环境变量值脱敏门槛：过短值（如 "1"/"0"）会大面积误伤正常文本。
_ENV_VALUE_MIN_LEN: Final[int] = 8
_PATH_HASH_DIGITS: Final[int] = 2**4  # 16（十六进制位——哈希标记定长）


def _env_mask(text: str) -> str:
    """R2a：环境变量值 → 占位（值不落盘；名可示）。"""
    for name, value in os.environ.items():
        if len(value) >= _ENV_VALUE_MIN_LEN and value in text:
            text = text.replace(value, f"<env:{name}>")
    return text


class _Sanitizer:
    """R2 脱敏器（绑定沙箱根——沙箱内外路径分流）。"""

    def __init__(self, root: Path) -> None:
        self._root_norm = os.path.normcase(os.path.realpath(root))

    def _mask_path(self, raw: str) -> str:
        """单路径脱敏：沙箱内→相对；沙箱外→哈希标记。

        realpath 归一（8.3 短名/junction 折叠）后再与沙箱根比较——
        Windows TEMP 短名形态与长名同源不分流。
        """
        norm = os.path.normcase(os.path.realpath(raw))
        if norm == self._root_norm:
            return "."
        if norm.startswith(self._root_norm + os.sep):
            return norm[len(self._root_norm) + 1 :].replace(os.sep, "/")
        digest = sha256(norm.encode("utf-8")).hexdigest()[:_PATH_HASH_DIGITS]
        return f"{{path:{digest}}}"

    def _mask_text(self, text: str) -> str:
        """R2 顺序铁律：先路径（结构判定）后环境变量值——反序会让 env 占位
        吃掉盘符前缀致路径正则失配（TEMP/HOME 类路径值环境变量实测）。"""
        return _env_mask(_ABS_PATH_PATTERN.sub(lambda m: self._mask_path(m.group(0)), text))

    def sanitize(self, value: Any) -> Any:
        """递归净化（dict/list/Path/str/标量）。"""
        if isinstance(value, str):
            return self._mask_text(value)
        if isinstance(value, Path):
            text = os.fspath(value)
            return self._mask_path(text) if _ABS_PATH_PATTERN.fullmatch(text) else text
        if isinstance(value, Mapping):
            return {self._mask_text(str(k)): self.sanitize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.sanitize(item) for item in value]
        if value is None or isinstance(value, bool | int | float):
            return value
        return self._mask_text(str(value))


class SessionLog:
    """会话 jsonl 日志（同步追加——MCP 同步调用模型下无异步缓冲窗口）。"""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._dir = self._root / "sessions"
        self._sanitizer = _Sanitizer(self._root)
        self._lock = threading.Lock()
        self._seq: dict[str, int] = {}

    def _file(self, session_id: str) -> Path:
        if not _SESSION_ID_PATTERN.fullmatch(session_id):
            raise ValueError(
                f"会话 id 非法：{session_id!r}（分量白名单 [A-Za-z0-9][A-Za-z0-9_-]*——拒路径注入）"
            )
        return self._dir / f"{session_id}.jsonl"

    def _next_seq(self, session_id: str, path: Path) -> int:
        """R1：内存计数优先；新会话按既有文件行数续接。"""
        if session_id not in self._seq:
            self._seq[session_id] = (
                sum(1 for _ in path.open(encoding="utf-8")) if path.exists() else 0
            )
        self._seq[session_id] += 1
        return self._seq[session_id]

    def append(
        self, session_id: str, actor: Actor, type: EventType, payload: Mapping[str, Any]
    ) -> int:
        """追加一行事件（同步写+行级 flush）——返回本行 seq。"""
        path = self._file(session_id)
        with self._lock:
            seq = self._next_seq(session_id, path)
            line = {
                "ts": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "session_id": session_id,
                "seq": seq,
                "actor": actor,
                "type": type,
                "payload": self._sanitizer.sanitize(payload),
            }
            self._dir.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")
                handle.flush()
        return seq

    def events(self, session_id: str) -> list[dict[str, Any]]:
        """读面（调试/测试对账——逐行解析）。"""
        path = self._file(session_id)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def tool_call(self, session_id: str, tool: str, arguments: Mapping[str, Any]) -> None:
        """工具调用事件（actor=tool/type=tool_call 固定）。"""
        self.append(session_id, "tool", "tool_call", {"tool": tool, "arguments": dict(arguments)})

    def tool_result(
        self, session_id: str, tool: str, ok: bool, summary: Mapping[str, Any] | None = None
    ) -> None:
        """工具结果事件（ok=False 时 summary 应含 error 摘要）。"""
        payload: dict[str, Any] = {"tool": tool, "ok": ok}
        if summary:
            payload.update(summary)
        self.append(session_id, "tool", "tool_result", payload)
