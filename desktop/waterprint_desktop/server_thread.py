"""uvicorn 显式启停线程件（引擎与静态壳共用的服务器句柄）。

输入:  ASGI app+绑定面（host/port——port=0=临时端口探测）+超时参数
输出:  UvicornServeHandle（start 阻塞至就绪/stop 优雅停/actual_port 实端口）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_static_shell.py+test_runtime.py）
#
# 【公开接口】
#   UvicornServeHandle(app, host, port)：
#       start(timeout_s)——起守护线程跑 uvicorn Server.serve()，轮询
#         server.started 至就绪（超时 TimeoutError——fail fast 不静默）
#       actual_port——实际绑定端口（port=0 探测形态下=内核分配值；
#         测试与端口冲突自愈消费）
#       stop(timeout_s)——should_exit=True+join（线程退出即端口释放）
#       is_running——started 且线程存活
#
# 【行为规格】
#   R1 单进程多线程进程模型（ADR-028）：uvicorn 不经 uvicorn.run 子命令
#      面（那会抢占信号处理），经 Server 对象显式驱动——角色切换重启=
#      stop 旧句柄+start 新句柄，窗口主线程不受影响。
#   R2 每句柄一次性：start 后再 start=ValueError；stop 幂等（未启动/
#      已停=无操作）。
#   R3 日志降噪：log_level="warning"（引擎业务日志面归 server structlog
#      通道，access log 在桌面壳=噪音）。
#
# 【测试要求】启停可达（curl /api/meta）/stop 后端口关闭/actual_port
#   探测形态/重复 start 拒。
#
# 【参照】ADR-028；uvicorn Server.should_exit 优雅停协议（uvicorn 文档）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import threading
from typing import Final

import uvicorn

# 启动就绪轮询间隔（秒）
_POLL_INTERVAL_S: Final[float] = 0.05


class UvicornServeHandle:
    """uvicorn.Server 显式驱动句柄（线程承载 serve() 协程）。"""

    def __init__(self, app: object, host: str, port: int) -> None:
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread: threading.Thread | None = None
        self._started = False

    @property
    def is_running(self) -> bool:
        return self._started and self._thread is not None and self._thread.is_alive()

    @property
    def actual_port(self) -> int:
        """实际绑定端口（port=0 探测形态=内核分配值；未启动=ValueError）。"""
        for server in self._server.servers:
            for sock in server.sockets:
                return int(sock.getsockname()[1])
        raise ValueError("服务器未绑定端口（未启动或已停止）")

    def start(self, timeout_s: float = 15.0) -> None:
        """起服务线程并阻塞至就绪（uvicorn started 旗标；超时=TimeoutError）。"""
        if self._started:
            raise ValueError("句柄已启动（一次性——重启=新句柄，R2）")
        self._thread = threading.Thread(
            target=lambda: asyncio.run(self._server.serve()), daemon=True,
            name="waterprint-desktop-server",
        )
        self._thread.start()
        self._started = True
        waited = 0.0
        while not self._server.started:
            if not self._thread.is_alive():
                raise RuntimeError("服务线程启动即退出（绑定冲突或应用异常）")
            if waited >= timeout_s:
                self._server.should_exit = True
                raise TimeoutError(f"服务启动超时（>{timeout_s}s）")
            threading.Event().wait(_POLL_INTERVAL_S)
            waited += _POLL_INTERVAL_S

    def stop(self, timeout_s: float = 10.0) -> None:
        """优雅停（should_exit 协议+线程汇合；幂等）。"""
        if not self._started or self._thread is None:
            return
        self._server.should_exit = True
        self._thread.join(timeout=timeout_s)
        self._started = False
