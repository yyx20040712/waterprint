"""桌面壳入口（薄窗口层——pywebview 装配，不进测试面）。

输入:  无（模块入口；环境面=WATERPRINT_DESKTOP_* 三键）
输出:  进程退出码（窗口关闭后 0；GUI 后端缺席 1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（联机第七批 2026-11-19——ADR-028）
#
# 【公开接口】
#   python -m waterprint_desktop.main    桌面应用入口
#   bootstrap_origin(supervisor) -> str 起始 origin 决策（引擎在场=引擎
#      origin；否则壳 origin——unconfigured/client 态）——纯函数可测
#
# 【行为规格】
#   R1 薄层红线：本件只做 pywebview 窗口装配与回调接线（窗口面真实
#      验证=用户手测——测试禁开任何窗口，AGENTS 前台焦点红线）；全部
#      逻辑（配置/装配/桥）在 config/roles/engine/static_shell/
#      runtime/bridge 六件（无头测试覆盖）。
#   R2 起始页决策：引擎角色（standalone/server）窗口指向引擎 origin
#      （UI 与 API 同源）；unconfigured/client 指向静态壳 8620（首启
#      向导/厚客户端）。
#   R3 角色切换窗口导航：桥 on_role_applied 回调——切至引擎角色=窗口
#      load_url 引擎 origin（引擎已活体重启完成）；切至 client=留在壳
#      origin（页面 reload 拉起客户端连接面）。
#   R4 GUI 后端缺席（Linux 无 webkit2gtk 等）=stderr 明确提示+退出码
#      1（诚实失败非静默）。
#
# 【测试要求】bootstrap_origin 纯函数（desktop/tests/test_main_entry.py
#   ——supervisor 探询面 mock，零 pywebview import）。
#
# 【参照】ADR-028；pywebview linux 后置依赖（webkit2gtk）见
#   desktop/packaging/README.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys

from waterprint_desktop.config import ConfigStore, default_config_path
from waterprint_desktop.runtime import RuntimeSupervisor
from waterprint_desktop.static_shell import resolve_webapp_dist

# 首启等待桥装配的窗口尺寸（px——产品面值非工程量）
_WINDOW_WIDTH = 1280
_WINDOW_HEIGHT = 800


def bootstrap_origin(supervisor: RuntimeSupervisor) -> str:
    """起始 origin 决策（R2——纯函数：引擎在场优先，壳兜底）。"""
    engine = supervisor.engine_origin()
    if engine is not None:
        return engine
    shell = supervisor.shell_origin()
    if shell is not None:
        return shell
    raise RuntimeError(
        "无可用 origin：引擎与静态壳均未运行（dist 缺失或装配失败——"
        "检查 WATERPRINT_DESKTOP_WEBAPP_DIST 与配置文件）"
    )


def main() -> int:
    """桌面应用入口：装配监督件+桥→开窗口→随窗口生命周期停机。"""
    import webview  # 惰性导入：pywebview=GUI 依赖，不进逻辑层 import 面

    config_store = ConfigStore(default_config_path())
    supervisor = RuntimeSupervisor(config_store, resolve_webapp_dist())
    supervisor.start()

    def on_role_applied(role: str) -> None:
        # R3 窗口导航：引擎角色切 origin；client 留壳面 reload
        engine = supervisor.engine_origin()
        if engine is not None:
            window.load_url(engine)
        else:
            window.evaluate_js("window.location.reload()")

    from waterprint_desktop.bridge import DesktopBridge

    bridge = DesktopBridge(config_store, supervisor, on_role_applied=on_role_applied)
    window = webview.create_window(
        "WaterPrint",
        bootstrap_origin(supervisor),
        js_api=bridge,
        width=_WINDOW_WIDTH,
        height=_WINDOW_HEIGHT,
    )
    try:
        webview.start()
    # GUI 后端失败族宽（豁免登记 gate_patterns.WIDE_EXCEPT_WAIVERS）；R4 诚实提示出口
    except Exception as exc:
        print(
            f"桌面窗口启动失败：{exc}\n"
            "Linux 需要 webkit2gtk（如 Debian/Ubuntu：sudo apt install "
            "python3-gi gir1.2-webkit2-4.1）；详见 desktop/packaging/README.md",
            file=sys.stderr,
        )
        return 1
    finally:
        supervisor.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
