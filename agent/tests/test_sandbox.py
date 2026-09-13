"""test_sandbox——init_workspace 幂等建树 + env 覆盖 + data 资产根。

输入:  tmp_path 沙箱根
输出:  目录树/workspace.toml/幂等断言（AI1-TRACK-B §3 预裁决）
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from waterprint_agent import sandbox


def test_init_workspace_builds_tree(tmp_path: Path) -> None:
    """首次建树：五区目录+workspace.toml（记录 data 资产根与创建时间）。"""
    root = tmp_path / "sb"
    returned = sandbox.init_workspace(root)
    assert returned == root
    for area in ("projects", "exports", "results", "sessions", "reports"):
        assert (root / area).is_dir(), f"缺目录 {area}"
    marker = root / "workspace.toml"
    assert marker.is_file()
    data = tomllib.loads(marker.read_text(encoding="utf-8"))
    assert data["data_asset"]["root"] == str(sandbox.data_asset_root())
    assert Path(data["data_asset"]["root"]).is_dir()  # 真实 data 资产根在位
    assert data["created_at"]


def test_init_workspace_idempotent(tmp_path: Path) -> None:
    """幂等：重复调用零异常且不覆写 workspace.toml（created_at 不变）。"""
    root = tmp_path / "sb"
    sandbox.init_workspace(root)
    first = (root / "workspace.toml").read_text(encoding="utf-8")
    sandbox.init_workspace(root)
    sandbox.init_workspace(root)
    assert (root / "workspace.toml").read_text(encoding="utf-8") == first


def test_sandbox_root_env_override(tmp_path: Path, monkeypatch) -> None:
    """env WATERPRINT_AI_SANDBOX 覆盖默认根（绝对化）。"""
    monkeypatch.setenv("WATERPRINT_AI_SANDBOX", str(tmp_path / "env-sb"))
    assert sandbox.sandbox_root() == (tmp_path / "env-sb").resolve()
    monkeypatch.delenv("WATERPRINT_AI_SANDBOX")
    default = sandbox.sandbox_root()
    assert default.is_absolute()
    assert default.name == "ai-sandbox"
    assert default.parent == sandbox.repo_root().parent  # 默认根=仓库上一级/ai-sandbox


def test_data_asset_root_points_at_repo_data() -> None:
    """data 资产根=仓库 data/（constraint_kb/coefficients 在位）。"""
    data = sandbox.data_asset_root()
    assert data.is_dir()
    assert (data / "constraint_kb" / "constraints.json").is_file()
    assert (data / "coefficients" / "manifest.yaml").is_file()
