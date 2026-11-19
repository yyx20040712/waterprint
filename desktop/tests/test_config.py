"""config.py 镜像测试：持久化/token/路径解析（联机第七批 ADR-028）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from waterprint_desktop.config import (
    SCHEMA_VERSION,
    TOKEN_BYTES,
    ConfigStore,
    DesktopConfig,
    default_config_path,
    default_data_root,
    generate_api_token,
)


def test_load_missing_file_defaults_unconfigured(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "desktop.json")
    config = store.load()
    assert config.role == "unconfigured"
    assert config.api_token == ""


def test_save_load_roundtrip_and_deterministic_bytes(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "desktop.json"
    store = ConfigStore(path)
    store.save(DesktopConfig(role="server", api_token="a" * TOKEN_BYTES * 2))
    once = path.read_bytes()
    store.save(DesktopConfig(role="server", api_token="a" * TOKEN_BYTES * 2))
    assert path.read_bytes() == once  # 同输入双写字节级一致（确定性形态）
    loaded = store.load()
    assert loaded == DesktopConfig(role="server", api_token="a" * TOKEN_BYTES * 2)


def test_save_file_shape_utf8_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "desktop.json"
    ConfigStore(path).save(DesktopConfig(role="standalone"))
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == {
        "schema_version": SCHEMA_VERSION,
        "role": "standalone",
        "api_token": "",
    }


@pytest.mark.parametrize("payload", [
    "{ 坏 JSON",
    '["not", "object"]',
    '{"schema_version": 1, "role": "lan_host"}',
    '{"schema_version": 99, "role": "standalone"}',
    '{"schema_version": 1, "role": "standalone", "api_token": 123}',
    '{"schema_version": 1, "role": "standalone", "api_token": "short"}',
])
def test_load_invalid_payload_rejected(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "desktop.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="桌面壳配置"):
        ConfigStore(path).load()


def test_ensure_server_token_generates_persists_stable(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "desktop.json")
    token = store.ensure_server_token()
    assert len(token) >= TOKEN_BYTES  # ≥16 红线（生成面=32 hex）
    assert int(token, 16) >= 0  # hex 形态
    # 重启稳定：再次取回同值（配对卡「重启或重新生成前有效」）
    assert store.ensure_server_token() == token
    assert store.load().api_token == token


def test_generate_api_token_fresh_and_hex() -> None:
    first = generate_api_token()
    second = generate_api_token()
    assert len(first) == TOKEN_BYTES * 2
    assert first != second  # 密码学随机（同长度不碰撞非断言域——大空间实证）
    int(first, 16)  # hex 字符集校验（非 hex 抛 ValueError）


def test_default_config_path_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WATERPRINT_DESKTOP_CONFIG", str(tmp_path / "c.json"))
    assert default_config_path() == tmp_path / "c.json"
    monkeypatch.delenv("WATERPRINT_DESKTOP_CONFIG")
    fallback = default_config_path()
    assert fallback.name == "desktop.json"
    assert "waterprint" in fallback.parts


def test_default_data_root_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WATERPRINT_DESKTOP_DATA_DIR", str(tmp_path / "d"))
    assert default_data_root() == tmp_path / "d"
    monkeypatch.delenv("WATERPRINT_DESKTOP_DATA_DIR")
    assert "waterprint" in default_data_root().parts
