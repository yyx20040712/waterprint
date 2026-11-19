"""engine.py 镜像测试：角色化 Settings+UI 挂载+端口决策（联机第七批 ADR-028）。"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.conftest import MakeDist
from waterprint_desktop.engine import (
    build_engine_app,
    build_engine_settings,
    resolve_engine_port,
)
from waterprint_desktop.roles import DEFAULT_ENGINE_PORT, plan_for


def test_resolve_engine_port_default_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WATERPRINT_PORT", raising=False)
    assert resolve_engine_port() == DEFAULT_ENGINE_PORT
    monkeypatch.setenv("WATERPRINT_PORT", "9000")
    assert resolve_engine_port() == 9000


def test_build_settings_standalone(tmp_path: Path) -> None:
    settings = build_engine_settings(
        plan_for("standalone"), api_token="t" * 32, port=8621, data_root=tmp_path
    )
    assert settings.host == "127.0.0.1"
    assert settings.port == 8621
    assert settings.api_token == ""  # 回环角色不消费 token（鉴权关）
    assert settings.projects_dir == tmp_path / "projects"
    assert settings.exports_dir == tmp_path / "exports"


def test_build_settings_server_carries_token(tmp_path: Path) -> None:
    settings = build_engine_settings(
        plan_for("server"), api_token="t" * 32, port=8621, data_root=tmp_path
    )
    assert settings.host == "0.0.0.0"
    assert settings.api_token == "t" * 32


def test_build_settings_server_empty_token_rejected_by_server_redline(
    tmp_path: Path,
) -> None:
    # server R-6 红线复用：0.0.0.0+空 token=Settings 构造即拒（非本包重实现）
    with pytest.raises(ValidationError, match="api_token"):
        build_engine_settings(plan_for("server"), api_token="", port=8621, data_root=tmp_path)


def test_build_settings_engineless_role_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="不起引擎"):
        build_engine_settings(plan_for("client"), api_token="", port=8621, data_root=tmp_path)


def _mounted_ui_names(app: object) -> list[str]:
    return [getattr(route, "name", "") for route in app.routes]


def test_build_engine_app_mounts_ui_when_dist_present(
    tmp_path: Path, make_dist: MakeDist
) -> None:
    dist = make_dist()
    settings = build_engine_settings(
        plan_for("standalone"), api_token="", port=8621, data_root=tmp_path
    )
    app = build_engine_app(settings, dist)
    assert "desktop-ui" in _mounted_ui_names(app)


def test_build_engine_app_skips_ui_when_dist_missing(tmp_path: Path) -> None:
    settings = build_engine_settings(
        plan_for("standalone"), api_token="", port=8621, data_root=tmp_path
    )
    app = build_engine_app(settings, tmp_path / "no-dist")
    assert "desktop-ui" not in _mounted_ui_names(app)
