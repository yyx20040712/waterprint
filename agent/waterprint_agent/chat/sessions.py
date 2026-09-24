"""聊天会话存储：沙箱 sessions/chat/ 追加式 JSONL+滑动窗口+项目绑定+决策纪要。

输入:  AgentContext（PathGuard 定基点）+会话 ID/消息文本/决策四键
输出:  ChatSession（消息记录/项目绑定/决策段）+窗口投影（LLM 上下文构造用）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 1 2026-09-24）
#   路径：agent/waterprint_agent/chat/sessions.py
#   职责：多轮对话会话态唯一存储面——append-only JSONL（禁改写既有行，
#       绑定/注记以新记录形态追加后读生效）；滑动窗口投影（近 N 轮全文，
#       设计终裁 W2：无摘要调用）；决策纪要段（轨道丙回填素材）。
#   禁区：禁 import core/server/fastmcp（纯 stdlib）；禁 LLM/工具调用
#       （本件只管存储投影，编排在 loop.py）；禁写 sessions/chat/ 之外
#       任何位置（PathGuard sessions 区门）。
#
# 【行为规格】
#   R1 存储：sessions/chat/<session_id>.jsonl 逐行 JSON（UTF-8 追加式）；
#       记录四族=meta/binding/note/message/decision（record 键判别）；
#       读侧顺序扫描取最新 binding 为当前项目绑定。
#   R2 窗口：window(turns=20)=按 turn 分组取末 N 轮的 message 投影
#       [{role,text,tool_steps}]（窗口外整轮丢弃——无摘要层）。
#   R3 绑定：bind_project 追加 binding 记录（后读生效覆盖语义）；
#       会话-项目 1:1（设计终裁 §二）。
#   R4 决策：append_decision 四键（topic/conclusion/rationale/turn）
#       ——轨道丙 decisions 素材真源（叙述草稿经 narrative_fills 采用）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # 仅类型面——运行期零重依赖
    from waterprint_agent.context import AgentContext

__all__ = [
    "ChatSession",
    "append_decision",
    "append_message",
    "append_note",
    "bind_project",
    "create_session",
    "list_sessions",
    "load_session",
    "new_session_id",
    "read_decisions",
    "read_history",
    "window",
]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def new_session_id() -> str:
    """新会话 ID（uuid4 hex——与项目 ID 同形态，无序语义）。"""
    return uuid.uuid4().hex


@dataclass
class ChatSession:
    """会话运行态句柄（存储真源=JSONL 文件，本类零缓存）。"""

    session_id: str
    path: Path
    project_id: str | None = None
    created_at: str = ""
    title: str = ""


def session_path(ctx: AgentContext, session_id: str) -> Path:
    """会话文件路径（PathGuard sessions 区守卫——注入/逃逸拒）。"""
    return ctx.guard.resolve_in(Path(f"chat/{session_id}.jsonl"), area="sessions")


def _append(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _records(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def create_session(ctx: AgentContext, title: str = "") -> ChatSession:
    """建会话（meta 首行落盘）——返回运行态句柄。"""
    session_id = new_session_id()
    path = session_path(ctx, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = _now()
    _append(
        path, {"record": "meta", "session_id": session_id, "created_at": created, "title": title}
    )
    return ChatSession(session_id, path, None, created, title)


def load_session(ctx: AgentContext, session_id: str) -> ChatSession | None:
    """重载会话（不存在=None；绑定取最新 binding 记录）。"""
    path = session_path(ctx, session_id)
    if not path.is_file():
        return None
    meta: dict[str, Any] = {}
    project_id: str | None = None
    for record in _records(path):
        kind = record.get("record")
        if kind == "meta":
            meta = record
        elif kind == "binding":
            project_id = record.get("project_id")
    return ChatSession(
        session_id,
        path,
        project_id,
        str(meta.get("created_at", "")),
        str(meta.get("title", "")),
    )


def append_message(  # noqa: PLR0913  # 五字段=消息记录存储 schema 面（非逻辑参数面）
    session: ChatSession,
    role: str,
    text: str,
    *,
    turn: int,
    truncated: bool = False,
    tool_steps: list[dict[str, Any]] | None = None,
) -> None:
    """追加消息记录（user/assistant；assistant 可带工具步轨迹+截断标记）。"""
    record: dict[str, Any] = {
        "record": "message",
        "role": role,
        "text": text,
        "turn": turn,
        "truncated": truncated,
        "ts": _now(),
        "tool_steps": tool_steps or [],
    }
    _append(session.path, record)


def bind_project(ctx: AgentContext, session: ChatSession, project_id: str) -> None:
    """绑定项目（追加 binding 记录——后读生效，1:1 覆盖语义）。"""
    _append(session.path, {"record": "binding", "project_id": project_id, "ts": _now()})
    session.project_id = project_id


def append_note(session: ChatSession, text: str) -> None:
    """追加注记（降级/上下文失效提示等系统面叙述——不入 LLM 上下文）。"""
    _append(session.path, {"record": "note", "text": text, "ts": _now()})


def append_decision(
    session: ChatSession, topic: str, conclusion: str, rationale: str, turn: int
) -> None:
    """追加决策纪要（轨道丙回填素材四键）。"""
    _append(
        session.path,
        {
            "record": "decision",
            "topic": topic,
            "conclusion": conclusion,
            "rationale": rationale,
            "turn": turn,
            "ts": _now(),
        },
    )


def read_history(ctx: AgentContext, session_id: str) -> list[dict[str, Any]]:
    """消息全量回读（CLI --history/前端历史面）。"""
    path = session_path(ctx, session_id)
    if not path.is_file():
        return []
    return [
        {
            "role": r.get("role"),
            "text": r.get("text"),
            "turn": r.get("turn"),
            "truncated": r.get("truncated", False),
            "tool_steps": r.get("tool_steps", []),
        }
        for r in _records(path)
        if r.get("record") == "message"
    ]


def window(ctx: AgentContext, session_id: str, turns: int = 20) -> list[dict[str, Any]]:
    """滑动窗口投影：末 N 轮 message（R2——窗口外整轮丢弃）。"""
    history = read_history(ctx, session_id)
    if not history:
        return []
    last_turn = max(int(m["turn"]) for m in history)
    start = last_turn - turns + 1
    return [
        {"role": m["role"], "text": m["text"], "tool_steps": m["tool_steps"]}
        for m in history
        if int(m["turn"]) >= start
    ]


def read_decisions(ctx: AgentContext, session_id: str) -> list[dict[str, Any]]:
    """决策纪要回读（四键投影）。"""
    path = session_path(ctx, session_id)
    if not path.is_file():
        return []
    return [
        {
            "topic": r.get("topic"),
            "conclusion": r.get("conclusion"),
            "rationale": r.get("rationale"),
            "turn": r.get("turn"),
        }
        for r in _records(path)
        if r.get("record") == "decision"
    ]


def list_sessions(ctx: AgentContext) -> list[dict[str, Any]]:
    """会话清单（chat/ 目录扫描——标题/绑定/轮数摘要）。"""
    root = ctx.guard.resolve_in(Path("chat"), area="sessions")
    if not root.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.jsonl")):
        session_id = path.stem
        meta: dict[str, Any] = {}
        project_id: str | None = None
        turns = 0
        for record in _records(path):
            kind = record.get("record")
            if kind == "meta":
                meta = record
            elif kind == "binding":
                project_id = record.get("project_id")
            elif kind == "message" and record.get("role") == "user":
                turns += 1
        items.append(
            {
                "session_id": session_id,
                "title": str(meta.get("title", "")),
                "created_at": str(meta.get("created_at", "")),
                "project_id": project_id,
                "turns": turns,
            }
        )
    return items
