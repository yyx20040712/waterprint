"""桌面壳桥实现：pywebview js_api 对象（按 webapp desktopBridge.ts 冻结契约）。

输入:  ConfigStore+RuntimeSupervisor（+on_role_applied 回调——main 层窗口
        导航接线位，缺席=纯逻辑态）
输出:  DesktopBridge（getConfig/setNetworkRole——方法名 camelCase 与 TS
        契约逐名对齐；pywebview js_api 按方法名直投 JS）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028；镜像测试 desktop/tests/
# test_bridge.py）
#
# 【公开接口】（TS 契约对齐——webapp/src/app/desktopBridge.ts）
#   getConfig() -> {role, shellOrigin, engineOrigin}：
#      role=四角色串（"unconfigured"=首启向导注入态——webapp
#      OnboardingGate 消费）；shellOrigin/engineOrigin=string|null
#      （未运行面 null——窗口导航与降级展示消费）
#   setNetworkRole(role) -> {ok, restartRequired}：
#      role∈{"standalone","server","client"}（b5 冻结签名——b7 扩
#      "client" 联合成员供首启三选，签名形状不变）；
#      成功={ok:true, restartRequired:false}（活体重启由壳在本调用内
#      完成——「重启生效」的壳侧承担语义）；
#      装配失败={ok:false, restartRequired:true}（配置已持久化，下次
#      应用启动按新角色装配——诚实信号非静默失败）；
#      未知角色={ok:false, restartRequired:false}。
#
# 【行为规格】
#   R1 返回键集恰两/三槽（TS 冻结面）——错误细节不进返回体（桥层零
#      日志写 token 红线：装配异常 repr 不含 token——异常面为绑定/
#      启动类，token 不流经异常文本）。
#   R2 on_role_applied 回调：装配成功后同步回调（main 层接窗口导航
#      ——standalone/server 装好后窗口切引擎 origin；测试缺省 None=
#      纯逻辑态可无头验证）。
#   R3 桥不持角色真源：role 读写全经 ConfigStore/Supervisor（本件零
#      状态缓存——多次 getConfig 一致性由持久层保证）。
#
# 【测试要求】键集恰契约面/四角色 getConfig/三合法角色切换+持久化断言/
#   未知角色拒/装配失败转译/回调触发。
#
# 【参照】ADR-028；webapp desktopBridge.ts（b5 冻结+b7 扩面）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from waterprint_desktop.config import ConfigStore
from waterprint_desktop.runtime import RuntimeSupervisor

# setNetworkRole 合法角色面（b5 冻结 "standalone"|"server" + b7 扩
# "client"——首启三选稿 onboarding.html；"unconfigured" 不是可切换
# 目标=初始态非选项）
SWITCHABLE_ROLES: Final[tuple[str, ...]] = ("standalone", "server", "client")


class DesktopBridge:
    """pywebview js_api 桥对象（方法名=TS 契约 camelCase——ruff N802 豁免在册）。"""

    def __init__(
        self,
        config_store: ConfigStore,
        supervisor: RuntimeSupervisor,
        on_role_applied: Callable[[str], None] | None = None,
    ) -> None:
        self._config_store = config_store
        self._supervisor = supervisor
        self._on_role_applied = on_role_applied

    def getConfig(self) -> dict[str, object]:  # noqa: N802——TS 契约名（pyproject 豁免在册，docstring 双注记）
        """配置探询（webapp OnboardingGate/降级展示消费——R3 零缓存）。"""
        config = self._config_store.load()
        return {
            "role": config.role,
            "shellOrigin": self._supervisor.shell_origin(),
            "engineOrigin": self._supervisor.engine_origin(),
        }

    def setNetworkRole(self, role: str) -> dict[str, bool]:  # noqa: N802——同上
        """角色切换（活体重启在本调用内完成——成功即已生效）。"""
        if role not in SWITCHABLE_ROLES:
            return {"ok": False, "restartRequired": False}
        try:
            self._supervisor.apply_role(role)
        except (OSError, RuntimeError, ValueError, TimeoutError):
            # R4 失败语义：配置已持久化（apply_role 先持久化后装配）——
            # 下次应用启动按新角色装配=restartRequired 诚实信号
            return {"ok": False, "restartRequired": True}
        if self._on_role_applied is not None:
            self._on_role_applied(role)
        return {"ok": True, "restartRequired": False}
