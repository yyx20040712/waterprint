"""ai_connection 服务镜像测试：状态四项/merge 原子写/uv 缺失 400 面（AI2）＋回炉补测。

输入:  waterprint_server.services.ai_connection 公开符号+tmp 伪工作区
      （data_dir 指向 <tmp>/ws/waterprint/data——仓库根/父目录上溯推导面）
输出:  服务契约断言（四项检查聚合/两份配置 merge 保留/原子写/uv 缺失拒/
      锚点校验拒/agent 缺失前置拒写/第二份写失败回滚/结构性损坏重建/
      .tmp 失败清理）
"""

from __future__ import annotations

import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.services.ai_connection")

_HAS_PUBLIC = all(
    hasattr(_mod, name)
    for name in ("connection_status", "setup_connection", "UvNotFoundError")
)

pytestmark = [
    pytest.mark.skipif(
        not _HAS_PUBLIC,
        reason="实现未就绪：waterprint_server.services.ai_connection（AI2 批）",
    ),
    pytest.mark.anyio,
]


@pytest.fixture
def manager_stub() -> ThreadPoolExecutor:
    """Manager 占位执行器（FIX-5②：yield 后 shutdown——测试面零泄漏）。"""
    executor = ThreadPoolExecutor(max_workers=1)
    yield executor
    executor.shutdown(wait=True)


def _workspace(tmp_path: Path) -> Path:
    """伪工作区：建 <tmp>/ws/waterprint/{data,agent/waterprint_agent} 并返回仓库根。

    data_dir=仓库根/data（生产口径——data_dir.parent 上溯=仓库根）；
    agent 面以最小 waterprint_agent 包形态在场（锚点校验+importable 探针真源）。
    """
    repo_root = tmp_path / "ws" / "waterprint"
    (repo_root / "data").mkdir(parents=True)
    package = repo_root / "agent" / "waterprint_agent"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    return repo_root


def _config_paths(repo_root: Path) -> tuple[Path, Path]:
    """两份工作区配置路径（仓库根+父目录——预裁决固定推导面）。"""
    return (
        repo_root / ".zcode" / "config.json",
        repo_root.parent / ".zcode" / "config.json",
    )


def _ctx(tmp_path: Path, data_dir: Path, manager: ThreadPoolExecutor) -> object:
    """装配束工厂（伪工作区 Settings——多测试共用样板收口）。"""
    from waterprint_server.services import ServiceContext
    from waterprint_server.settings import Settings

    return ServiceContext(
        settings=Settings(
            projects_dir=tmp_path / "projects",
            exports_dir=tmp_path / "exports",
            data_dir=data_dir,
            calc_workers=1,
            log_file=str(tmp_path / "ai-connection.log"),
        ),
        manager=manager,
    )


async def test_status_all_green_when_configured(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """四项全真：两份配置任一含 waterprint 条目+agent 包在场+uv 可解析→ready。"""
    repo_root = _workspace(tmp_path)
    repo_config, _parent_config = _config_paths(repo_root)
    repo_config.parent.mkdir(parents=True)
    repo_config.write_text(
        json.dumps({"mcp": {"servers": {"waterprint": {"command": "uv"}}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")
    status = _mod.connection_status(_ctx(tmp_path, repo_root / "data", manager_stub))
    assert status.config_written is True
    assert [str(path) for path in _config_paths(repo_root)] == list(status.config_paths)
    assert status.agent_importable is True
    assert status.uv_path == "/fake/bin/uv.exe"
    assert status.sandbox_root == str(repo_root.parent / "ai-sandbox")
    assert status.ready is True


async def test_status_unconfigured_workspace_all_honest(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """未配置工作区（锚点在场面配置/uv 缺）：配置假+uv 假+ready 假诚实聚合。"""
    repo_root = _workspace(tmp_path)
    monkeypatch.setattr(_mod, "which", lambda _name: None)
    status = _mod.connection_status(_ctx(tmp_path, repo_root / "data", manager_stub))
    assert status.config_written is False
    assert status.agent_importable is True  # 锚点包在场（回炉：裸工作区归锚点拒测）
    assert status.uv_path is None
    assert status.ready is False


async def test_status_config_written_if_either_file_has_entry(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """任一含 waterprint 条目即 config_written（父目录单份亦真——会话开在
    父目录场景是本批战役背景的真源踩坑形态）。"""
    repo_root = _workspace(tmp_path)
    _repo_config, parent_config = _config_paths(repo_root)
    parent_config.parent.mkdir(parents=True)
    parent_config.write_text(
        json.dumps({"mcp": {"servers": {"waterprint": {"command": "uv"}}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "which", lambda _name: None)
    status = _mod.connection_status(_ctx(tmp_path, repo_root / "data", manager_stub))
    assert status.config_written is True
    assert status.ready is False  # uv 面未真（which 打桩 None——ready 聚合诚实）


async def test_status_rejects_unexpected_data_dir_layout(
    tmp_path, manager_stub
) -> None:  # type: ignore[no-untyped-def]
    """FIX-3 锚点校验：data_dir 上溯无 agent/waterprint_agent 锚=WorkspaceLayoutError
    （400 面——错误消息指明部署形态预期 data_dir=<仓库根>/data）。"""
    stray = tmp_path / "elsewhere"
    (stray / "data").mkdir(parents=True)  # 无 agent 包（非仓库根布局）
    ctx = _ctx(tmp_path, stray / "data", manager_stub)
    with pytest.raises(_mod.WorkspaceLayoutError, match=r"data_dir=<仓库根>/data"):
        _mod.connection_status(ctx)


async def test_setup_writes_both_configs_merge_semantics(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """merge 写：两份配置写入 waterprint 条目——他 server 条目与无关顶层键保留。"""
    repo_root = _workspace(tmp_path)
    repo_config, parent_config = _config_paths(repo_root)
    repo_config.parent.mkdir(parents=True)
    repo_config.write_text(
        json.dumps(
            {
                "theme": "dark",
                "mcp": {"servers": {"other_tool": {"command": "other"}}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")
    result = _mod.setup_connection(_ctx(tmp_path, repo_root / "data", manager_stub))
    assert [str(path) for path in (repo_config, parent_config)] == list(
        result.written_paths
    )
    for path in (repo_config, parent_config):
        document = json.loads(path.read_text(encoding="utf-8"))
        entry = document["mcp"]["servers"]["waterprint"]
        assert entry["command"] == "/fake/bin/uv.exe"
        assert entry["args"] == [
            "run",
            "--directory",
            str(repo_root / "agent"),
            "waterprint-mcp",
        ]
        assert entry["env"] == {
            "WATERPRINT_AI_SANDBOX": str(repo_root.parent / "ai-sandbox")
        }
    merged = json.loads(repo_config.read_text(encoding="utf-8"))
    assert merged["theme"] == "dark"  # 无关顶层键保留
    assert merged["mcp"]["servers"]["other_tool"] == {"command": "other"}  # 他 server 保留


async def test_setup_rebuilds_structurally_corrupt_mcp(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """FIX-5① 结构性损坏重建：mcp 非 dict/servers 非 dict 两形态归重建
    （无关顶层键仍保留——R3 结构面）。"""
    repo_root = _workspace(tmp_path)
    repo_config, parent_config = _config_paths(repo_root)
    repo_config.parent.mkdir(parents=True)
    repo_config.write_text(
        json.dumps({"theme": "dark", "mcp": "not-a-mapping"}), encoding="utf-8"
    )
    parent_config.parent.mkdir(parents=True)
    parent_config.write_text(
        json.dumps({"mcp": {"servers": 42}}), encoding="utf-8"
    )
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")
    _mod.setup_connection(_ctx(tmp_path, repo_root / "data", manager_stub))
    rebuilt_repo = json.loads(repo_config.read_text(encoding="utf-8"))
    assert rebuilt_repo["theme"] == "dark"  # 无关键保留
    assert "waterprint" in rebuilt_repo["mcp"]["servers"]  # mcp 串形态重建
    rebuilt_parent = json.loads(parent_config.read_text(encoding="utf-8"))
    assert "waterprint" in rebuilt_parent["mcp"]["servers"]  # servers 非 dict 重建


async def test_setup_rejects_when_agent_not_importable(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """FIX-3 前置拒写：agent 不可导入（status 同款探测面）=400 拒+零文件写入。"""
    repo_root = _workspace(tmp_path)
    repo_config, parent_config = _config_paths(repo_root)
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")
    monkeypatch.setattr(_mod, "_agent_importable", lambda _dir: False)
    ctx = _ctx(tmp_path, repo_root / "data", manager_stub)
    with pytest.raises(_mod.WorkspaceLayoutError, match="agent"):
        _mod.setup_connection(ctx)
    assert not repo_config.exists() and not parent_config.exists()  # 零文件写入


async def test_setup_second_write_failure_restores_first(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """FIX-2 跨文件半写补偿：第二份写抛 OSError→第一份恢复原始字节+异常上抛。"""
    repo_root = _workspace(tmp_path)
    repo_config, parent_config = _config_paths(repo_root)
    original = json.dumps({"theme": "dark"}).encode("utf-8")
    repo_config.parent.mkdir(parents=True)
    repo_config.write_bytes(original)
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")
    # getattr 字符串面取私有名（打桩保留真件——SLF001 私有成员访问面规避）
    real_write = getattr(_mod, "_write_config_atomic")
    calls = {"count": 0}

    def flaky_write(path: Path, config: dict) -> None:  # type: ignore[type-arg]
        calls["count"] += 1
        if calls["count"] == 2:  # 第二份（父目录）写失败面
            raise OSError("模拟磁盘故障")
        real_write(path, config)

    monkeypatch.setattr(_mod, "_write_config_atomic", flaky_write)
    with pytest.raises(OSError, match="模拟磁盘故障"):
        _mod.setup_connection(_ctx(tmp_path, repo_root / "data", manager_stub))
    assert repo_config.read_bytes() == original  # 第一份恢复原始内容
    assert not parent_config.exists()  # 第二份原不存在保持不存在


async def test_setup_atomic_no_tmp_leftovers(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """GR-38 原子写：写后 .zcode 目录零 .tmp 残留（损坏既有件视为 {} 重写）。"""
    repo_root = _workspace(tmp_path)
    repo_config, _parent_config = _config_paths(repo_root)
    repo_config.parent.mkdir(parents=True)
    repo_config.write_text("{ 损坏 JSON", encoding="utf-8")
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")
    _mod.setup_connection(_ctx(tmp_path, repo_root / "data", manager_stub))
    document = json.loads(repo_config.read_text(encoding="utf-8"))
    assert "waterprint" in document["mcp"]["servers"]  # 损坏件={} 语义后重写成功
    leftovers = [
        item.name for item in repo_config.parent.iterdir() if item.name.endswith(".tmp")
    ]
    assert leftovers == []


async def test_write_atomic_cleans_tmp_on_failure(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """FIX-4 .tmp 失败清理：replace 抛 OSError→异常上抛且 .zcode 目录零 .tmp 残留。"""
    repo_root = _workspace(tmp_path)
    repo_config, _parent_config = _config_paths(repo_root)
    monkeypatch.setattr(_mod, "which", lambda _name: "/fake/bin/uv.exe")

    def broken_replace(_src: object, _dst: object) -> None:
        raise OSError("模拟 replace 失败")

    monkeypatch.setattr(_mod.os, "replace", broken_replace)
    with pytest.raises(OSError, match="模拟 replace 失败"):
        _mod.setup_connection(_ctx(tmp_path, repo_root / "data", manager_stub))
    zcode_dir = repo_config.parent
    if zcode_dir.exists():  # 第一份失败即抛（第二份未写）——补偿面零已写件
        leftovers = [item.name for item in zcode_dir.iterdir() if item.name.endswith(".tmp")]
        assert leftovers == []


async def test_setup_uv_missing_raises_domain_error(
    tmp_path, manager_stub, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """uv 不可解析=UvNotFoundError（400 面——预裁决固定错误）；零文件写入。"""
    repo_root = _workspace(tmp_path)
    repo_config, _parent_config = _config_paths(repo_root)
    monkeypatch.setattr(_mod, "which", lambda _name: None)
    ctx = _ctx(tmp_path, repo_root / "data", manager_stub)
    with pytest.raises(_mod.UvNotFoundError):
        _mod.setup_connection(ctx)
    assert not repo_config.exists()  # 失败面零半成品
