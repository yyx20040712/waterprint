"""架构门禁：镜像规则 + 职责表双向同步 + 单元包固定结构（永续激活）。

输入:  core/waterprint 源码树 + docs/file-contracts.md + scripts/check_structure.py
输出:  结构契约断言结果（违反即失败，骨架期即运行）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：§13.2 镜像规则 / §13.6 单元包固定结构 / §13.7 职责表同步。
# 门禁脚本以子进程同口径复用（scripts 与本测试双保险）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.arch

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_gate(script: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )


def test_file_contracts_sync_gate() -> None:
    """职责表双向同步（源码未列/列了不存在/单元包缺件 = 失败）。"""
    result = _run_gate("check_structure.py")
    assert result.returncode == 0, result.stdout + result.stderr


def test_mirror_rule() -> None:
    """每个非 __init__ 源文件必有同名镜像测试（units_lib 固定结构例外）。"""
    src_root = REPO_ROOT / "core" / "waterprint"
    tests_root = REPO_ROOT / "core" / "tests"
    existing = {p.name for p in tests_root.rglob("*.py")}
    missing: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        rel = path.relative_to(src_root)
        if path.name == "__init__.py":
            continue
        if "units_lib" in rel.parts:
            continue  # 单元包固定结构由 check_structure 按 §13.6 校验
        if f"test_{path.stem}.py" not in existing and f"properties_{path.stem}.py" not in existing:
            missing.append(f"{rel} 缺镜像测试 test_{path.stem}.py / properties_{path.stem}.py")
    assert not missing, "\n".join(missing)


def test_unit_template_structure() -> None:
    """_template 必须具备 §13.6 全部固定件（新单元结构一致性的源头）。"""
    template = REPO_ROOT / "core" / "waterprint" / "units_lib" / "_template"
    required = (
        "__init__.py", "manifest.py", "compute.py", "constraints.py",
        "README.md", "tests/test_compute.py", "tests/properties.py",
    )
    missing = [name for name in required if not (template / name).is_file()]
    assert not missing, f"_template 缺固定件: {missing}"
