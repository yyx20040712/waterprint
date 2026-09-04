"""check_ruff 门禁脚本镜像直测：四态（双 SKIP/全 OK/单 FAIL/OSError 兜底）。

输入:  scripts/check_ruff.py（脚本 REPO 写死不可注入——sys.path 注入
       import+monkeypatch venv 定位/子进程；真实脚本冒烟一跑走子进程）
输出:  四态断言（输出文案+main() 返回值——SC1 D9③）
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def module():
    """scripts/check_ruff 注入 import（模块级 sys.path 写死禁——fixture 内进出）。"""
    injected = str(REPO_ROOT / "scripts")
    sys.path.insert(0, injected)
    try:
        return importlib.import_module("check_ruff")
    finally:
        sys.path.remove(injected)


@pytest.fixture()
def fake_python(module):  # type: ignore[no-untyped-def]
    """REPO 内假解释器路径（[INFO] 行 relative_to(REPO) 前缀前提）。"""
    return module.REPO / "core" / ".venv" / "Scripts" / "python.exe"


def test_double_skip_returns_zero(module, monkeypatch, capsys) -> None:
    """双 SKIP=0（CI 零依赖 job 预期路径——SKIP 语义红线不破）。"""
    monkeypatch.setattr(module, "locate_venv_python", lambda root: None)
    assert module.main() == 0
    out = capsys.readouterr().out
    assert out.count("[SKIP] check_ruff") == 2
    assert "uv sync" in out  # D9②：SKIP 引导语（本地运行请 uv sync）


def test_all_ok_returns_zero(module, monkeypatch, capsys, fake_python) -> None:
    """全 OK=0（ruff 退出码 0 透传 [OK] 单行）。"""
    monkeypatch.setattr(module, "locate_venv_python", lambda root: fake_python)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
    )
    assert module.main() == 0
    assert capsys.readouterr().out.count("[OK] check_ruff") == 2


def test_single_fail_returns_one(module, monkeypatch, capsys, fake_python) -> None:
    """单 FAIL=1（core 根 ruff 退出码非 0——任一根 FAIL 即退出码 1）。"""
    monkeypatch.setattr(module, "locate_venv_python", lambda root: fake_python)
    runs = iter([
        SimpleNamespace(returncode=1, stdout=b"", stderr=b"lint boom\n"),
        SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
    ])
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: next(runs))
    assert module.main() == 1
    out = capsys.readouterr().out
    assert "[FAIL] check_ruff：core" in out
    assert "lint boom" in out  # ruff 输出透传


def test_oserror_fallback_returns_one(module, monkeypatch, capsys, fake_python) -> None:
    """OSError 兜底=FAIL（D9①：venv 解释器在但不可执行——禁裸抛 traceback）。"""

    def raise_oserror(*args: object, **kwargs: object) -> None:
        raise PermissionError("denied")  # OSError 现实异常族成员

    monkeypatch.setattr(module, "locate_venv_python", lambda root: fake_python)
    monkeypatch.setattr(module.subprocess, "run", raise_oserror)
    assert module.main() == 1
    out = capsys.readouterr().out
    assert "子进程不可用" in out  # 兜底文案（含异常与重建引导）
    assert "uv sync" in out
    assert out.count("[FAIL] check_ruff") == 2  # 双根皆 OSError=双 FAIL 行


def test_real_script_smoke() -> None:
    """冒烟：真实脚本子进程一跑（本机双 [OK]/CI 双 [SKIP] 皆绿——断言=退出码
    0+每根恰一行 [OK]/[SKIP] 且零 [FAIL]；R1-1：无条件 [OK] 断言在 CI
    零依赖 job（双 venv 缺=双 SKIP）必红——预拦；SC1R-01：推导段收紧为
    逐根行计数断言——ok/skip/fail 三计数锁，非存在性推导）。"""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_ruff.py")],
        capture_output=True,
        cwd=REPO_ROOT,
        check=False,
    )
    text = result.stdout.decode("utf-8", errors="replace")
    assert result.returncode == 0, text + result.stderr.decode("utf-8", errors="replace")
    assert "[FAIL]" not in text
    for name, _root in (("core", REPO_ROOT / "core"), ("server", REPO_ROOT / "server")):
        # SC1R-01 逐根行计数（startswith 判定保精确——含 check_ruff：{name}
        # 的非判定行[进度/引导语]不入三计数；脚本现实输出=判定行恒带前缀）。
        lines = [ln for ln in text.splitlines() if f"check_ruff：{name}" in ln]
        ok = sum(1 for ln in lines if ln.startswith("[OK]"))
        skip = sum(1 for ln in lines if ln.startswith("[SKIP]"))
        fail = sum(1 for ln in lines if ln.startswith("[FAIL]"))
        assert ok + skip == 1 and fail == 0, (
            f"{name} 根须恰一行 [OK]/[SKIP] 且零 [FAIL]"
            f"（ok={ok} skip={skip} fail={fail}）：{text}"
        )
