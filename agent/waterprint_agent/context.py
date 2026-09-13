"""agent 面装配束（D2/E2）：私有 Manager+绝对路径 Settings+SessionLog+PathGuard。

输入:  沙箱根（env 解析或显式传入）
输出:  AgentContext（工具面共享装配束）+get_context 懒加载单例
"""

# ══════════════════════════════════════════════════════════════════
# 契约头（AI1-TRACK-B 2026-09-13）
#   路径：agent/waterprint_agent/context.py
#   职责：工具运行装配（PathGuard 守卫+server Settings/ServiceContext
#       私有实例+SessionLog）；run_tool 工具包装（会话日志 span+错误
#       兜底 dict——禁 raise 裸异常给 MCP 客户端）。
#   禁区：本模块顶层 import server 面（Settings/Manager/ServiceContext）
#       ——故 main 顶层禁 import 本模块（懒加载铁律：工具函数体内经
#       get_context 触达）；禁提交任何后台任务（Manager 仅装配填充，
#       E2/A3——与 webapp 互不互通）。
#
# 【公开接口】
#   AgentContext(guard, settings, service_ctx, session_log[, session_id])
#   build_context(sandbox_root: Path) -> AgentContext
#   get_context() -> AgentContext（懒加载单例——沙箱根取 sandbox.sandbox_root()）
#   reset_context() -> None（测试面——换沙箱根后重建）
#   run_tool(ctx, tool, arguments, run, hint) -> dict（日志 span+错误兜底）
#
# 【行为规格】
#   R1 路径全绝对：Settings 三基点=沙箱/projects、沙箱/exports、仓库/data
#      （cwd 敏感实证 K3——私有子类钉死 env_file=None，.env 通道关闭）；
#      PathGuard 外部只读白名单根=正式 projects 区（仓库级+server 级）
#      +golden 数据区（门一 FIX-2——_external_readonly_roots 装配面）。
#   R2 私有 Manager（E2）：ThreadPoolExecutor(max_workers=1)+运行中事件环
#      （无环=新建占位环——同步装配面同构）+registry/cancel 目录=沙箱
#      tasks/ 子树；不调 start()、不提交任务（装配填充语义）。
#   R3 工具包装：tool_call/tool_result 事件自动记录；run 内抛异常或返回
#      含 "error" 键的 dict → 记 ok=False 并透传错误 dict（+hint）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import atexit
import threading
import uuid
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from waterprint_server.jobs.manager import Manager
from waterprint_server.services import ServiceContext
from waterprint_server.settings import Settings

from waterprint_agent.pathguard import PathGuard
from waterprint_agent.sandbox import data_asset_root, init_workspace, repo_root
from waterprint_agent.sessionlog import SessionLog

__all__ = ["AgentContext", "build_context", "get_context", "reset_context", "run_tool"]


def _external_readonly_roots() -> tuple[Path, ...]:
    """外部只读根白名单（门一 FIX-2——repo 相对组织，禁绝对路径硬编码）。

    正式 projects 区（仓库级+server 级）+golden 数据区（种子真源）——
    open_readonly_external 的装载域（D4 正式区语义）。"""
    repo = repo_root()
    return (
        repo / "projects",
        repo / "server" / "projects",
        repo / "core" / "tests" / "golden" / "golden_data",
    )


class _AgentSettings(Settings):
    """agent 面私有配置面：禁 .env 文件（cwd 敏感 K3 收口）+忽略未知
    WATERPRINT_* 环境变量（本面自有 WATERPRINT_AI_SANDBOX 非字段不炸构造）。"""

    # pydantic model_config 面约定=类属性 dict（ClassVar 注记会脱离配置识别）
    model_config = {  # noqa: RUF012
        **Settings.model_config,
        "env_file": None,
        "extra": "ignore",
    }


@dataclass(frozen=True)
class AgentContext:
    """工具运行装配束（每 MCP 进程一份；四冻结字段+会话标识）。"""

    guard: PathGuard
    settings: Settings
    service_ctx: ServiceContext
    session_log: SessionLog
    session_id: str = ""


def _current_loop() -> asyncio.AbstractEventLoop:
    """R2：优先运行中事件环（server 生命周期内）；同步装配面（测试/首建）
    无环=新建占位环（不 run 不调度——仅 Manager 装配填充引用）。"""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        atexit.register(loop.close)  # 占位环进程退出收口（从未 run，close 安全）
        return loop


def build_context(sandbox_root: Path) -> AgentContext:
    """装配（幂等前置：工作区建树）——返回冻结装配束。"""
    root = init_workspace(Path(sandbox_root))
    guard = PathGuard(root, external_roots=_external_readonly_roots())
    settings = _AgentSettings(
        projects_dir=root / "projects",
        exports_dir=root / "exports",
        data_dir=data_asset_root(),
    )
    tasks_dir = root / "tasks"
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="wp-agent")
    manager = Manager(
        executor,
        cancel_dir=tasks_dir / "cancel",
        loop=_current_loop(),
        registry_dir=tasks_dir / "registry",
        artifacts_dir=tasks_dir,
    )
    atexit.register(executor.shutdown)  # 空池退出收口（从未提交任务）
    return AgentContext(
        guard=guard,
        settings=settings,
        service_ctx=ServiceContext(settings=settings, manager=manager),
        session_log=SessionLog(root),
        session_id=uuid.uuid4().hex,
    )


_CONTEXT: AgentContext | None = None
_CONTEXT_LOCK = threading.Lock()


def get_context() -> AgentContext:
    """懒加载单例（首次工具调用装配——重模块 import 均发生在工具体内）。"""
    global _CONTEXT  # noqa: PLW0603
    if _CONTEXT is None:
        with _CONTEXT_LOCK:
            if _CONTEXT is None:
                from waterprint_agent import sandbox  # 局部 import：读 env 定沙箱根

                _CONTEXT = build_context(sandbox.sandbox_root())
    return _CONTEXT


def reset_context() -> None:
    """测试面：清单例（换沙箱根/env 后重建装配）。"""
    global _CONTEXT  # noqa: PLW0603
    with _CONTEXT_LOCK:
        _CONTEXT = None


def run_tool(
    ctx: AgentContext,
    tool: str,
    arguments: Mapping[str, Any],
    run: Callable[[], dict[str, Any]],
    hint: str,
) -> dict[str, Any]:
    """工具运行包装：会话日志 span（tool_call/tool_result）+错误兜底 dict。

    run 抛异常或返回含 "error" 键的 dict → ok=False 记账并以
    {"error", "hint"} 形态返回客户端（禁 raise 裸异常——§3 工具条款）。
    """
    ctx.session_log.tool_call(ctx.session_id, tool, arguments)
    try:
        result = run()
        ok = "error" not in result
    except Exception as exc:  # 兜底面：领域异常一律转错误 dict
        ctx.session_log.tool_result(
            ctx.session_id, tool, ok=False, summary={"error": f"{type(exc).__name__}: {exc}"}
        )
        return {"error": f"{type(exc).__name__}: {exc}", "hint": hint}
    summary: dict[str, Any] = {}
    if ok and "count" in result:
        summary["count"] = result["count"]
    ctx.session_log.tool_result(
        ctx.session_id, tool, ok=ok, summary=summary or {"error": result.get("error")}
    )
    if ok:
        return result
    return {"error": str(result.get("error", "未知错误")), "hint": str(result.get("hint", hint))}
