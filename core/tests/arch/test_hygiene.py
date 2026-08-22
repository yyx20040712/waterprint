"""架构门禁：占位/裸异常/乱码/UTF-8 合法性 = 0 违规（永续激活）。

输入:  gate_patterns.SCAN_DIRS 源码与文档 + scripts/check_grep_gates.py
输出:  卫生断言结果（违禁特征即失败）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：AGENTS §3——占位实现不写存根、错误不许静默、中文必须可读。
# 与旧系统"乱码断言测试永远通过"（教训 D1）相反：本测试扫描真实
# 特征串，先红后绿成立。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.arch

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_hygiene_gate() -> None:
    """占位/裸 except/乱码门禁脚本全绿。"""
    env = dict(os.environ, PYTHONUTF8="1")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_grep_gates.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_all_text_files_utf8_readable() -> None:
    """仓库文本文件全部可按 UTF-8 解码（教训 C4 的机器验证）。"""
    excluded = {
        ".git", ".venv", "venv", "node_modules", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis",
        "__snapshots__", "dist", "build", "generated", ".mimosa",
    }
    suffixes = {".py", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml", ".toml", ".txt"}
    bad: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if excluded.intersection(path.relative_to(REPO_ROOT).parts):
            continue
        if path.suffix not in suffixes:
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append(path.relative_to(REPO_ROOT).as_posix())
    assert not bad, f"非 UTF-8 文件: {bad}"
