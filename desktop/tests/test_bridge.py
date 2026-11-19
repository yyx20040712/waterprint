"""bridge.py 镜像测试：桥 API 契约（TS 冻结签名对齐——联机第七批 ADR-028）。"""

from __future__ import annotations

from pathlib import Path

from waterprint_desktop.bridge import SWITCHABLE_ROLES, DesktopBridge
from waterprint_desktop.config import ConfigStore, DesktopConfig


class _FakeSupervisor:
    """桥层测试替身（origin/apply 记录+持久化契约镜像——装配本体在
    test_runtime 实测；apply_role 的「先持久化后装配」契约在此复刻，
    使桥层失败语义测试与真监督件同构）。"""

    def __init__(self, store: ConfigStore, *, fail_apply: bool = False) -> None:
        self._store = store
        self.applied: list[str] = []
        self.fail_apply = fail_apply

    def shell_origin(self) -> str | None:
        return "http://127.0.0.1:8620"

    def engine_origin(self) -> str | None:
        return None

    def apply_role(self, role: str) -> None:
        config = self._store.load()
        self._store.save(DesktopConfig(role=role, api_token=config.api_token))
        if self.fail_apply:
            raise OSError("engine start failed")
        self.applied.append(role)


def _bridge(tmp_path: Path, *, fail_apply: bool = False) -> tuple[DesktopBridge, ConfigStore, _FakeSupervisor]:
    store = ConfigStore(tmp_path / "desktop.json")
    supervisor = _FakeSupervisor(store, fail_apply=fail_apply)
    return DesktopBridge(store, supervisor), store, supervisor


def test_switchable_roles_surface() -> None:
    # b5 冻结 "standalone"|"server" + b7 扩 "client"（首启三选）
    assert SWITCHABLE_ROLES == ("standalone", "server", "client")


def test_getconfig_keys_match_ts_contract(tmp_path: Path) -> None:
    bridge, _, _ = _bridge(tmp_path)
    snapshot = bridge.getConfig()
    assert set(snapshot) == {"role", "shellOrigin", "engineOrigin"}  # 键集恰契约面
    assert snapshot["role"] == "unconfigured"  # 首启注入态（OnboardingGate 消费）
    assert snapshot["shellOrigin"] == "http://127.0.0.1:8620"
    assert snapshot["engineOrigin"] is None


def test_setnetworkrole_returns_frozen_shape_and_persists(tmp_path: Path) -> None:
    bridge, store, supervisor = _bridge(tmp_path)
    result = bridge.setNetworkRole("server")
    assert set(result) == {"ok", "restartRequired"}  # TS 冻结返回面恰两键
    assert result == {"ok": True, "restartRequired": False}  # 活体重启在调用内完成
    assert supervisor.applied == ["server"]
    assert store.load().role == "server"


def test_setnetworkrole_invalid_role_rejected(tmp_path: Path) -> None:
    bridge, _, supervisor = _bridge(tmp_path)
    for bad in ("unconfigured", "lan", ""):
        assert bridge.setNetworkRole(bad) == {"ok": False, "restartRequired": False}
    assert supervisor.applied == []  # 早拒——不触装配


def test_setnetworkrole_assembly_failure_honest_signal(tmp_path: Path) -> None:
    bridge, store, _ = _bridge(tmp_path, fail_apply=True)
    result = bridge.setNetworkRole("standalone")
    # R4：配置已持久化（下次应用启动按新角色装配）=restartRequired 诚实信号
    assert result == {"ok": False, "restartRequired": True}
    assert store.load().role == "standalone"


def test_role_applied_callback_invoked(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "desktop.json")
    seen: list[str] = []
    bridge = DesktopBridge(store, _FakeSupervisor(store), on_role_applied=seen.append)
    bridge.setNetworkRole("client")
    assert seen == ["client"]  # main 层窗口导航接线位（R2）


def test_getconfig_reads_persisted_role_no_cache(tmp_path: Path) -> None:
    bridge, store, _ = _bridge(tmp_path)
    store.save(DesktopConfig(role="client"))
    assert bridge.getConfig()["role"] == "client"  # R3 零缓存——每次读持久层
