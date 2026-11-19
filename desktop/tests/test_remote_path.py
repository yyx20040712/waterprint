"""远程通路联调：双实例（客户端态壳→服务端态引擎）握手+token 门禁+CORS
（联机第七批 ADR-028——b6 webapp remoteHandshake 三步的 Python 侧镜像）。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tests.conftest import MakeDist, http_get_json
from waterprint_desktop.config import ConfigStore, DesktopConfig
from waterprint_desktop.runtime import RuntimeSupervisor
from waterprint_desktop.static_shell import serve_static


@pytest.fixture
def server_instance(
    tmp_path: Path, make_dist: MakeDist, monkeypatch: pytest.MonkeyPatch
) -> tuple[RuntimeSupervisor, str]:
    """实例 A：服务端态引擎（远程服务器角色）。

    CORS 白名单经既有 WATERPRINT_ALLOWED_ORIGINS 通道注入实例 B（客户端
    壳）的实际 origin——临时端口形态下不落 8620 缺省，走部署配置通道
    （生产=缺省 8620 已在 server 缺省白名单，无需配置）。
    """
    shell = serve_static(make_dist(), port=0)
    client_origin = f"http://127.0.0.1:{shell.actual_port}"
    monkeypatch.setenv("WATERPRINT_ALLOWED_ORIGINS", client_origin)
    store = ConfigStore(tmp_path / "desktop.json")
    store.save(DesktopConfig(role="server"))
    supervisor = RuntimeSupervisor(
        store,
        tmp_path / "unused-dist",  # 远程服务器窗口面不在本联调域（UI 走客户端本地壳）
        engine_port=0,
        shell_port=0,
        data_root=tmp_path / "data",
        executor_factory=lambda: ThreadPoolExecutor(max_workers=1),
    )
    supervisor.start()
    engine_origin = supervisor.engine_origin()
    assert engine_origin is not None
    try:
        yield supervisor, client_origin
    finally:
        supervisor.shutdown()
        shell.stop()


def test_remote_handshake_meta_reachable_with_cors(
    server_instance: tuple[RuntimeSupervisor, str],
) -> None:
    """第一步（meta 豁免面）：客户端 origin 跨域可达+版本三槽在场。"""
    supervisor, client_origin = server_instance
    origin = supervisor.engine_origin()
    assert origin is not None
    status, meta, headers = http_get_json(
        f"{origin}/api/meta", headers={"Origin": client_origin}
    )
    assert status == 200
    for slot in ("app_version", "data_version", "api_version"):
        assert meta[slot] != ""  # 握手比对面材料在场（b6 clientProtocol 消费）
    assert headers.get("access-control-allow-origin") == client_origin  # CORS 通道真通


def test_remote_token_probe_then_bearer_pass(
    server_instance: tuple[RuntimeSupervisor, str],
) -> None:
    """第二/三步（token 探针→Bearer 放行）：受保面匿名拒+凭据行。"""
    supervisor, _ = server_instance
    origin = supervisor.engine_origin()
    assert origin is not None
    token = supervisor._config_store.load().api_token  # 联调取配对 token（构造注入面回读）
    assert token != ""
    status_anon, _, _ = http_get_json(f"{origin}/api/projects")
    assert status_anon == 401
    status_auth, projects, _ = http_get_json(
        f"{origin}/api/projects", headers={"Authorization": f"Bearer {token}"}
    )
    assert status_auth == 200
    assert isinstance(projects, list)  # 远程项目列表（客户端模式项目面板数据源）


def test_remote_runtime_reports_server_role(
    server_instance: tuple[RuntimeSupervisor, str],
) -> None:
    """配对面：远程服务器 role=server（客户端状态栏「远程@主机」面材料）。"""
    supervisor, _ = server_instance
    origin = supervisor.engine_origin()
    assert origin is not None
    status, runtime, _ = http_get_json(f"{origin}/api/runtime")
    assert status == 200
    assert runtime["role"] == "server"
