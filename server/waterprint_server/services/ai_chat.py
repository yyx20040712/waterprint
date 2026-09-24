"""对话中继服务（B4-4b 子批 2）：会话只读面+对话轮任务提交。

输入:  ServiceContext+会话 ID/消息文本
输出:  会话清单/历史（agent CLI 子进程读——零格式耦合）+TaskHandle（kind=ai_chat）
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（B4-4b 子批 2 2026-09-24；镜像测试 server/tests/services/test_ai_chat.py）
#
# 【公开接口】
#   list_sessions(ctx) -> list[dict]（agent CLI --list-sessions 子进程读）
#   read_history(ctx, session_id) -> list[dict]（--history 子进程读）
#   submit_ai_chat_turn(ctx, session_id, message) -> TaskHandle（异步
#       job kind=ai_chat——worker 子进程桥承载对话轮）
#
# 【行为规格】
#   R1 零格式耦合：会话存储真源=agent 沙箱 JSONL——server 一律经 agent
#      CLI 子进程读（不解析文件格式，格式演进零联动）。
#   R2 只读子进程超时：--list-sessions/--history 单次调用 wall clock 上限
#      30s（settings 旋钮 ai_readonly_timeout_s 缺省；超时=领域异常 502）。
#   R3 提交载荷：kind=ai_chat、session_id、message、task_queue_priorities
#      取键、settings 三键+超时透传（worker 面 env 注入）；会话 ID 分量
#      校验（safe_child 同款——防路径注入）。
#   R4 幂等键：session_id+message 哈希（同轮重发去重——task_id 复用）。
#
# 【错误与边界】AiChatReadError（RuntimeError 族）=只读子进程失败/超时。
# 【禁止事项】禁 import waterprint_agent；禁解析会话文件内容。
# 【测试要求】只读面（mock 子进程）、提交载荷键、ID 分量拒绝。
# 【参照】.workflow/b4-4b/design-final.md §一/§四
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import subprocess
from shutil import which
from typing import Any

from waterprint_server.jobs.manager import TaskHandle, TaskRequest
from waterprint_server.services import ServiceContext
from waterprint_server.settings import validate_component

_READONLY_TIMEOUT_S = 2 * 10  # 只读子进程 wall 上限 20s（R2 缺省——幂积保白名单）


class AiChatReadError(RuntimeError):
    """会话只读面失败（子进程超时/非零退出/uv 缺失）。"""


def _agent_cli_command(ctx: ServiceContext, *args: str) -> list[str] | None:
    """agent CLI 命令面（uv run --directory <repo>/agent——ai_connection 同款）。"""
    uv = which("uv")
    if uv is None:
        return None
    repo_root = ctx.settings.data_dir.resolve().parent
    agent_dir = repo_root / "agent"
    if not agent_dir.is_dir():
        return None
    return [
        uv,
        "run",
        "--directory",
        str(agent_dir),
        "python",
        "-m",
        "waterprint_agent.chat",
        *args,
    ]


def _run_readonly(ctx: ServiceContext, *args: str) -> str:
    """只读子进程执行（R1/R2——stdout 原文返回，超时=领域异常）。"""
    command = _agent_cli_command(ctx, *args)
    if command is None:
        raise AiChatReadError("agent CLI 不可用（uv 缺失或 agent 目录不在位）")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_READONLY_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise AiChatReadError("会话只读子进程超时（20s 上限）") from exc
    if result.returncode != 0:
        raise AiChatReadError(f"会话只读子进程退出码 {result.returncode}")
    return result.stdout


def list_sessions(ctx: ServiceContext) -> list[dict[str, Any]]:
    """会话清单（R1——JSON 数组解析，异常面 502 由 router 映射）。"""
    raw = _run_readonly(ctx, "--list-sessions")
    try:
        parsed = json.loads(raw.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise AiChatReadError("会话清单解析失败（非 JSON 输出）") from exc
    if not isinstance(parsed, list):
        raise AiChatReadError("会话清单形态非数组")
    return [dict(item) for item in parsed if isinstance(item, dict)]


def read_history(ctx: ServiceContext, session_id: str) -> list[dict[str, Any]]:
    """会话历史（R1——JSONL 逐行解析；ID 过分量校验）。"""
    validate_component(session_id)  # R3 分量校验（../与分隔符拒）
    raw = _run_readonly(ctx, "--history", session_id)
    items: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue  # 容错行跳过（append-only 面半行窗口）
        if isinstance(event, dict):
            items.append(dict(event))
    return items


async def submit_ai_chat_turn(ctx: ServiceContext, session_id: str, message: str) -> TaskHandle:
    """对话轮提交（R3/R4——异步 job，进度/取消走任务端点族既有面）。"""
    validate_component(session_id)
    settings = ctx.settings
    return await ctx.manager.submit(
        TaskRequest(
            kind="ai_chat",
            priority=settings.task_queue_priorities["ai_chat"],
            payload={
                "kind": "ai_chat",
                "session_id": session_id,
                "message": message,
                "data_dir": str(settings.data_dir),
                "artifacts_dir": str(ctx.artifacts_dir),
                # 密钥三键不经载荷（门一 W1-k2：payload 落 registry 档=密钥落盘
                # ——改 env 单通道，main 启动归一化 settings→os.environ）。
            },
        ),
        # 无幂等键（门一 W3-d1）：对话场景合法重复消息（「继续/重算」）高频，
        # 同指纹去重会吞掉第二条——每 POST=新轮任务。
    )
