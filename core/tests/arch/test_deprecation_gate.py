"""架构门禁镜像：GR-21 弃用到期门禁（check_deprecation_gate.py）。

输入:  scripts/check_deprecation_gate.py（子进程）+ 真源 docs/file-contracts.md
       + tmp_path 注入样本（逾期/非法日期两形态）
输出:  门禁行为断言（零登记绿/逾期红/格式防呆红——TD1 D1.4 三用例）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：TD1 技术债小批（2026-09-09）GR-21 退役机制缺位收口件。
# 门禁脚本以子进程同口径复用（test_structure.py 先例形态——_run_gate
# 扩展可选样本参数=镜像测试注入面，PD1 终裁）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

pytestmark = pytest.mark.arch

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_gate(
    sample: Path | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """子进程跑门禁（默认真源；可选样本注入——PD1 镜像测试注入面；
    可选 cwd——R 轮 A2-G1-02：路径锚定区分度用）。"""
    command = [sys.executable, str(REPO_ROOT / "scripts" / "check_deprecation_gate.py")]
    if sample is not None:
        command.append(str(sample))
    env = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd if cwd is not None else REPO_ROOT,
        env=env,
        check=False,
    )


def test_zero_registration_first_run_green(tmp_path: Path) -> None:
    """用例①：真源实跑零登记=首检绿（cwd=临时目录——路径自脚本位置
    锚定与 cwd 无关的区分度验证，R 轮 A2-G1-02 加强：误按 cwd 解析
    即找不到真源而红，实现对错可分）。"""
    result = _run_gate(cwd=tmp_path)
    assert result.returncode == 0
    assert "[OK]" in result.stdout


def test_overdue_registration_fails(tmp_path: Path) -> None:
    """用例②：逾期登记样本=红（样本日期=动态今日+昨日——today>=removal
    到期当日即红边界直接钉住，R 轮 A2-G1-02 加强：误改严格大于则
    今日样本不红即暴露）。"""
    today_text = date.today().isoformat()
    yesterday_text = (date.today() - timedelta(days=1)).isoformat()
    sample = tmp_path / "contracts.md"
    sample.write_text(
        "| `some/file.py` | L0 | 某职责(弃用: old_key -> new_key,"
        f" 移除: {today_text}) | 输入 | 输出 |\n"
        "| `some/file.py` | L0 | 某职责(弃用: another -> b,"
        f" 移除: {yesterday_text}) | 输入 | 输出 |",
        encoding="utf-8",
    )
    result = _run_gate(sample)
    assert result.returncode == 1
    assert "[FAIL]" in result.stdout
    assert "old_key" in result.stdout
    assert "another" in result.stdout


def test_future_registration_green(tmp_path: Path) -> None:
    """用例④：未到期登记=绿（明日日期不红——逾期判定单向性反向钉，
    与用例②构成边界对偶）。"""
    tomorrow_text = (date.today() + timedelta(days=1)).isoformat()
    sample = tmp_path / "contracts.md"
    sample.write_text(
        "| `some/file.py` | L0 | 某职责(弃用: old_key -> new_key,"
        f" 移除: {tomorrow_text}) | 输入 | 输出 |",
        encoding="utf-8",
    )
    result = _run_gate(sample)
    assert result.returncode == 0
    assert "弃用登记 1 项，0 逾期" in result.stdout


def test_invalid_date_registration_fails(tmp_path: Path) -> None:
    """用例③：非法日期=格式错红（防呆——非法登记不得静默通过）。"""
    sample = tmp_path / "contracts.md"
    sample.write_text(
        "| `some/file.py` | L0 | 某职责(弃用: a -> b, 移除: 2025-13-40) |",
        encoding="utf-8",
    )
    result = _run_gate(sample)
    assert result.returncode == 1
    assert "[FAIL]" in result.stdout
