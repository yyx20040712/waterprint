"""运行监督件：角色 → 引擎/静态壳生命周期（启动/角色切换重启/停机）。

输入:  ConfigStore+webapp dist+端口/数据基点参数（测试注入位）
输出:  RuntimeSupervisor（start/apply_role/shutdown+origin 探询面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_runtime.py+test_remote_path.py）
#
# 【公开接口】
#   RuntimeSupervisor(config_store, webapp_dist, *, engine_port=None,
#       shell_port=SHELL_PORT, data_root=None, executor_factory=None):
#     start()——按配置当前角色装配（首启正门）
#     apply_role(role)——角色切换：持久化+活体重装（引擎 stop→按新
#       方案 start；静态壳按需起停）——Minecraft 式开关不经应用重启
#     shutdown()——全停（幂等；窗口关闭消费）
#     engine_origin()/shell_origin()——origin 探询（桥 getConfig 与
#       窗口导航消费；引擎未运行 engine_origin=None）
#
# 【行为规格】
#   R1 装配决策单源=roles.plan_for：本件只做生命周期编排，零角色
#      if 语义（决策列全在 plan 五槽）。
#   R2 引擎角色间切换=全量重启（uvicorn 绑定在 start 期固化——
#      standalone↔server 换绑定必经重启；端口不变）。
#   R3 token 流程：进入 server 角色前 config_store.ensure_server_token()
#      （首启生成+持久化+重启稳定）；standalone 不消费 token。
#   R4 失败语义：新方案装配抛异常时已停的旧面不复活（下一应用启动
#      按已持久化新角色装配——桥层转译 {ok:False, restartRequired:True}）；
#      apply_role 前置角色校验（未知角色 ValueError 早于持久化）。
#   R5 测试注入位：engine_port/shell_port（临时端口 0 形态）/
#      data_root（tmp 数据基点）/executor_factory（ThreadPoolExecutor
#      跳过进程池——server 工厂既有注入口）。
#
# 【测试要求】三角色起停矩阵/角色切换活体重启（端口连续+新绑定生效）/
#   client 态引擎确停/停机幂等。
#
# 【参照】ADR-028；联机第五批 setNetworkRole 语义（重启生效=壳侧承担）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Final

from waterprint_desktop.config import ConfigStore, DesktopConfig, default_data_root
from waterprint_desktop.engine import (
    build_engine_app,
    build_engine_settings,
    resolve_engine_port,
)
from waterprint_desktop.roles import (
    DEFAULT_ENGINE_PORT,
    SHELL_BIND_HOST,
    SHELL_PORT,
    AssemblyPlan,
    plan_for,
)
from waterprint_desktop.server_thread import UvicornServeHandle
from waterprint_desktop.static_shell import build_static_app

# origin 串形态（桥 getConfig 消费——webapp desktopBridge.ts 同形对齐）
_LOOPBACK_ORIGIN: Final[str] = "http://127.0.0.1"


class RuntimeSupervisor:
    """三角色生命周期监督（单进程多线程——引擎与壳各一线程句柄）。"""

    # 装配参数束：两生产位+三测试注入位同门（拆第二配置对象无增益）
    def __init__(  # noqa: PLR0913
        self,
        config_store: ConfigStore,
        webapp_dist: Path,
        *,
        engine_port: int | None = None,
        shell_port: int = SHELL_PORT,
        data_root: Path | None = None,
        executor_factory: Callable[[], object] | None = None,
    ) -> None:
        self._config_store = config_store
        self._webapp_dist = webapp_dist
        self._engine_port = engine_port if engine_port is not None else resolve_engine_port()
        self._shell_port = shell_port
        self._data_root = data_root
        self._executor_factory = executor_factory
        self._engine: UvicornServeHandle | None = None
        self._shell: UvicornServeHandle | None = None
        self._current_plan: AssemblyPlan | None = None

    # ── 探询面（桥/窗口导航消费）────────────────────────────────

    def engine_origin(self) -> str | None:
        """引擎 origin（未运行=None——client/unconfigured 态）。"""
        if self._engine is None or not self._engine.is_running:
            return None
        return f"{_LOOPBACK_ORIGIN}:{self._engine.actual_port}"

    def shell_origin(self) -> str | None:
        """静态壳 origin（未运行=None——standalone/server 态）。"""
        if self._shell is None or not self._shell.is_running:
            return None
        return f"{_LOOPBACK_ORIGIN}:{self._shell.actual_port}"

    # ── 生命周期 ────────────────────────────────────────────────

    def start(self) -> None:
        """首启装配：按配置当前角色活体装配（不写配置）。"""
        config = self._config_store.load()
        self._apply(plan_for(config.role))

    def apply_role(self, role: str) -> None:
        """角色切换正门：校验→持久化→活体重装（R2/R4）。"""
        plan = plan_for(role)  # 未知角色 ValueError 早于持久化（R4）
        token = self._config_store.ensure_server_token() if plan.require_token else ""
        config = self._config_store.load()
        self._config_store.save(DesktopConfig(role=plan.role, api_token=token or config.api_token))
        self._apply(plan)

    def shutdown(self) -> None:
        """全停（幂等；窗口关闭消费）。"""
        for attr in ("_engine", "_shell"):
            handle = getattr(self, attr)
            if handle is not None:
                handle.stop()
                setattr(self, attr, None)
        self._current_plan = None

    # ── 内部装配 ────────────────────────────────────────────────

    def _apply(self, plan: AssemblyPlan) -> None:
        """按方案装到目标态（引擎全量重启语义 R2+壳按需起停）。"""
        engine_alive = self._engine is not None and self._engine.is_running
        if self._current_plan is not None and self._current_plan == plan and engine_alive:
            return  # 同方案幂等（重复 setNetworkRole 同角色；引擎已死不算幂等——走全量重启）
        # 引擎面：目标态不起引擎→停；起引擎→全量重启（绑定/token 变更面）
        if plan.engine_bind_host is None:
            self._stop_engine()
        else:
            self._stop_engine()
            self._start_engine(plan)
        # 壳面：按需起停
        if plan.serve_static_shell:
            if self._shell is None or not self._shell.is_running:
                self._shell = UvicornServeHandle(
                    build_static_app(self._webapp_dist),
                    host=SHELL_BIND_HOST,
                    port=self._shell_port,
                )
                self._shell.start()
        else:
            self._stop_shell()
        self._current_plan = plan

    def _stop_engine(self) -> None:
        if self._engine is not None:
            self._engine.stop()
            self._engine = None

    def _stop_shell(self) -> None:
        if self._shell is not None:
            self._shell.stop()
            self._shell = None

    def _start_engine(self, plan: AssemblyPlan) -> None:
        """引擎起：server 角色 token 门槛先行（R3）——ensure_server_token
        在 apply_role 已持久化；start 路径（非切换）从配置读取既有 token。"""
        config = self._config_store.load()
        token = config.api_token
        if plan.require_token and token == "":
            token = self._config_store.ensure_server_token()
        data_root = self._data_root if self._data_root is not None else default_data_root()
        # Settings.port 须 ≥1（server WP1 值域校验）；uvicorn 实际绑定不经
        # settings.port（本件显式传参）——探针形态 engine_port=0 时以缺省
        # 端口占位（settings.port 在桌面形态无消费面，仅构造合法性）。
        settings_port = self._engine_port if self._engine_port > 0 else DEFAULT_ENGINE_PORT
        settings = build_engine_settings(plan, token, settings_port, data_root)
        executor = self._executor_factory() if self._executor_factory is not None else None
        dist = self._webapp_dist if plan.mount_ui_on_engine else None
        app = build_engine_app(settings, dist, executor)
        self._engine = UvicornServeHandle(app, host=plan.engine_bind_host, port=self._engine_port)
        self._engine.start()
