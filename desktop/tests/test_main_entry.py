"""main.py bootstrap_origin 纯函数测试（窗口装配薄层不进测试——联机第七批）。"""

from __future__ import annotations

import pytest

from waterprint_desktop.main import bootstrap_origin


class _Origins:
    def __init__(self, engine: str | None, shell: str | None) -> None:
        self._engine = engine
        self._shell = shell

    def engine_origin(self) -> str | None:
        return self._engine

    def shell_origin(self) -> str | None:
        return self._shell


def test_engine_origin_wins_when_present() -> None:
    assert (
        bootstrap_origin(_Origins("http://127.0.0.1:8621", "http://127.0.0.1:8620"))
        == "http://127.0.0.1:8621"
    )


def test_shell_origin_fallback() -> None:
    assert (
        bootstrap_origin(_Origins(None, "http://127.0.0.1:8620"))
        == "http://127.0.0.1:8620"
    )


def test_no_origin_fail_fast() -> None:
    with pytest.raises(RuntimeError, match="无可用 origin"):
        bootstrap_origin(_Origins(None, None))
