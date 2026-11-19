"""runtime.py 镜像测试：三角色活体装配+角色切换重启（无头实网——联机第七批 ADR-028）。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tests.conftest import MakeDist, http_get, http_get_json, port_open
from waterprint_desktop.config import TOKEN_BYTES, ConfigStore, DesktopConfig
from waterprint_desktop.runtime import RuntimeSupervisor


def _supervisor(tmp_path: Path, dist: Path, role: str) -> RuntimeSupervisor:
    """测试装配：临时端口（0=探测）+tmp 数据基点+线程池替身（跳过进程池
    spawn——server 工厂既有 executor 注入口，窗口/进程面零涉）。"""
    store = ConfigStore(tmp_path / "desktop.json")
    store.save(DesktopConfig(role=role))
    return RuntimeSupervisor(
        store,
        dist,
        engine_port=0,
        shell_port=0,
        data_root=tmp_path / "data",
        executor_factory=lambda: ThreadPoolExecutor(max_workers=1),
    )


def _start(tmp_path: Path, dist: Path, role: str) -> tuple[RuntimeSupervisor, ConfigStore]:
    supervisor = _supervisor(tmp_path, dist, role)
    supervisor.start()
    return supervisor, supervisor._config_store  # 测试同包探针（构造注入面回读）


def test_standalone_engine_serves_meta_and_ui(tmp_path: Path, make_dist: MakeDist) -> None:
    supervisor, _ = _start(tmp_path, make_dist(), "standalone")
    try:
        origin = supervisor.engine_origin()
        assert origin is not None
        status, meta, _ = http_get_json(f"{origin}/api/meta")
        assert status == 200  # 引擎真在服务（豁免端点——版本握手面）
        assert meta["app_version"] != ""
        # UI 同源挂载（选型 A）：根路径回 webapp dist 的 index.html
        status_ui, body, _ = http_get(f"{origin}/")
        assert status_ui == 200
        assert "wp-test" in body
        assert supervisor.shell_origin() is None  # 引擎角色不起壳
    finally:
        supervisor.shutdown()


def test_role_switch_standalone_to_server_rebinds_with_token(
    tmp_path: Path, make_dist: MakeDist
) -> None:
    supervisor, store = _start(tmp_path, make_dist(), "standalone")
    try:
        supervisor.apply_role("server")
        token = store.load().api_token
        assert len(token) >= TOKEN_BYTES  # 首启 server 生成 token（≥16 红线）
        origin = supervisor.engine_origin()
        assert origin is not None
        status, runtime, _ = http_get_json(f"{origin}/api/runtime")
        assert status == 200
        assert runtime["role"] == "server"  # 新绑定 0.0.0.0 生效（绑定即角色）
        assert runtime["bind_host"] == "0.0.0.0"
        assert runtime["token_configured"] is True
        # token 门禁在体：受保面无凭据拒、Bearer 放行（远程客户端配对面）
        status_anon, _, _ = http_get_json(f"{origin}/api/projects")
        assert status_anon == 401
        status_auth, _, _ = http_get_json(
            f"{origin}/api/projects", headers={"Authorization": f"Bearer {token}"}
        )
        assert status_auth == 200
    finally:
        supervisor.shutdown()


def test_role_switch_to_client_stops_engine_serves_shell(
    tmp_path: Path, make_dist: MakeDist
) -> None:
    supervisor, _ = _start(tmp_path, make_dist(), "standalone")
    try:
        engine_origin = supervisor.engine_origin()
        assert engine_origin is not None
        engine_port = int(engine_origin.rsplit(":", 1)[1])
        supervisor.apply_role("client")
        assert supervisor.engine_origin() is None  # 引擎确停
        assert not port_open("127.0.0.1", engine_port)
        shell_origin = supervisor.shell_origin()
        assert shell_origin is not None  # 客户端态=本地静态壳供 UI
        status, body, _ = http_get(f"{shell_origin}/")
        assert status == 200
        assert "wp-test" in body
    finally:
        supervisor.shutdown()


def test_unconfigured_bootstrap_is_shell_only(tmp_path: Path, make_dist: MakeDist) -> None:
    supervisor, _ = _start(tmp_path, make_dist(), "unconfigured")
    try:
        assert supervisor.engine_origin() is None  # 首启引导不起引擎
        assert supervisor.shell_origin() is not None
    finally:
        supervisor.shutdown()


def test_apply_same_role_idempotent(tmp_path: Path, make_dist: MakeDist) -> None:
    supervisor, _ = _start(tmp_path, make_dist(), "standalone")
    try:
        origin_before = supervisor.engine_origin()
        supervisor.apply_role("standalone")  # 同方案幂等（R2 注记路径）
        assert supervisor.engine_origin() == origin_before
    finally:
        supervisor.shutdown()


def test_shutdown_idempotent_and_closes_all(tmp_path: Path, make_dist: MakeDist) -> None:
    supervisor, _ = _start(tmp_path, make_dist(), "client")
    shell_origin = supervisor.shell_origin()
    assert shell_origin is not None
    shell_port = int(shell_origin.rsplit(":", 1)[1])
    supervisor.shutdown()
    supervisor.shutdown()  # 幂等
    assert not port_open("127.0.0.1", shell_port)
    assert supervisor.engine_origin() is None and supervisor.shell_origin() is None


def test_apply_unknown_role_rejected_before_persist(
    tmp_path: Path, make_dist: MakeDist
) -> None:
    supervisor = _supervisor(tmp_path, make_dist(), "unconfigured")
    supervisor.start()
    try:
        with pytest.raises(ValueError, match="未知桌面壳角色"):
            supervisor.apply_role("lan")
        assert supervisor._config_store.load().role == "unconfigured"  # noqa: SLF001——持久层未被污染
    finally:
        supervisor.shutdown()
