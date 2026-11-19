"""三角色装配决策（纯逻辑）：角色 → 引擎绑定/静态壳/UI 挂载/token 门槛。

输入:  DesktopRole（config.py 四角色）
输出:  AssemblyPlan（frozen dataclass）+plan_for（角色→装配方案唯一决策）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_roles.py）
#
# 【公开接口】
#   SHELL_BIND_HOST/SHELL_PORT：客户端/引导态静态壳绑定面——
#      127.0.0.1:8620（8620=server CORS 缺省白名单约定端口
#      WATERPRINT_ALLOWED_ORIGINS——b5/b6 契约对齐，改端口须同批改
#      server settings 缺省）
#   DEFAULT_ENGINE_PORT：桌面壳引擎缺省端口 8621（8620 壳位相邻+1；
#      8000 留给裸机 dev server——WATERPRINT_PORT env 可覆盖，见
#      engine.resolve_engine_port）
#   ENGINE_LOOPBACK_BIND/ENGINE_LAN_BIND：角色派生绑定地址单源
#   AssemblyPlan：role/engine_bind_host/serve_static_shell/
#      mount_ui_on_engine/require_token 五槽
#   plan_for(role) -> AssemblyPlan：唯一决策正门
#
# 【行为规格】（用户裁决三角色模型——一个安装包永远全量）
#   unconfigured：首启引导——不起引擎，静态壳 8620 供 UI（onboarding
#      面经桥 getConfig 注入 webapp）；无 token 门槛
#   standalone：本地引擎 127.0.0.1:engine_port +UI 同源挂载（窗口指向
#      引擎 origin）；无 token（回环绑定，server R-6 防线面内）
#   server：本地引擎照常 +0.0.0.0 绑定 +token 强制 +局域网可连；UI
#      同源挂载（窗口仍指本机引擎 origin——远程客户端各自走本地壳）
#   client：不起引擎——静态壳 8620 供 UI，全部 API 走远程（b6 厚客户
#      端通路；CORS 由远程服务端 WATERPRINT_ALLOWED_ORIGINS 承载）
#
# 【测试要求】四角色决策矩阵恰四态（绑定/壳/UI/token 四列）+未知角色拒。
#
# 【参照】ADR-028；联机第五批「绑定地址即角色」；frontend-redesign/
#   onboarding.html 批准稿
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from waterprint_desktop.config import VALID_ROLES, DesktopRole

# 静态壳绑定面（客户端模式/首启引导）：127.0.0.1:8620——端口=server CORS
# 缺省白名单约定值（b5/b6 契约；本件为桌面侧单源，CORS 对端真源=
# server settings.allowed_origins 缺省串）。
SHELL_BIND_HOST: Final[str] = "127.0.0.1"
SHELL_PORT: Final[int] = 8620  # 桌面壳约定端口（CORS 契约值——非工程量）
# 桌面壳引擎缺省端口：8621（壳位相邻；8000=裸机 dev server 保留位）。
DEFAULT_ENGINE_PORT: Final[int] = 8621  # 桌面壳约定端口（契约值——非工程量）
# 角色派生绑定地址（联机第五批「绑定地址即角色」——role=绑定的唯一真源，
# WATERPRINT_HOST 在壳内被忽略：角色配置与绑定不得双真源）。
ENGINE_LOOPBACK_BIND: Final[str] = "127.0.0.1"
ENGINE_LAN_BIND: Final[str] = "0.0.0.0"


@dataclass(frozen=True)
class AssemblyPlan:
    """单角色装配方案（RuntimeSupervisor 消费——五槽全量派生自角色）。"""

    role: DesktopRole
    engine_bind_host: str | None
    serve_static_shell: bool
    mount_ui_on_engine: bool
    require_token: bool


def plan_for(role: str) -> AssemblyPlan:
    """角色 → 装配方案唯一决策（未知角色 ValueError——fail fast）。

    | role         | 引擎绑定        | 静态壳 8620 | UI 挂引擎 | token 门槛 |
    |--------------|-----------------|-------------|-----------|------------|
    | unconfigured | 不起            | 是（引导）  | 否        | 无         |
    | standalone   | 127.0.0.1:engine| 否          | 是        | 无         |
    | server       | 0.0.0.0:engine  | 否          | 是        | 强制       |
    | client       | 不起            | 是          | 否        | 无         |
    """
    if role not in VALID_ROLES:
        raise ValueError(f"未知桌面壳角色：{role!r}（合法={VALID_ROLES}）")
    if role == "unconfigured":
        return AssemblyPlan(role=role, engine_bind_host=None,
                            serve_static_shell=True, mount_ui_on_engine=False,
                            require_token=False)
    if role == "standalone":
        return AssemblyPlan(role=role, engine_bind_host=ENGINE_LOOPBACK_BIND,
                            serve_static_shell=False, mount_ui_on_engine=True,
                            require_token=False)
    if role == "server":
        return AssemblyPlan(role=role, engine_bind_host=ENGINE_LAN_BIND,
                            serve_static_shell=False, mount_ui_on_engine=True,
                            require_token=True)
    return AssemblyPlan(role=role, engine_bind_host=None,
                        serve_static_shell=True, mount_ui_on_engine=False,
                        require_token=False)
