"""coefficients 镜像测试：系数库加载（数据驱动、版本传播、引用闭环）。

输入:  waterprint.registry.coefficients 公开符号 + 临时 YAML 数据包
输出:  加载/失联拒绝/版本断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.registry.coefficients")
load_coefficients = getattr(_mod, "load_coefficients", None)

pytestmark = pytest.mark.skipif(
    load_coefficients is None,
    reason="实现未就绪：waterprint.registry.coefficients（M1）",
)


def _write_pkg(tmp_path: Path, body: str) -> Path:
    target = tmp_path / "coefficients"
    target.mkdir()
    (target / "manifest.yaml").write_text(
        "data_version: '9.9.9-test'\n", encoding="utf-8"
    )
    (target / "entries.yaml").write_text(body, encoding="utf-8")
    return target


def test_load_and_query(tmp_path: Path) -> None:
    pkg = _write_pkg(tmp_path, "\n".join([
        "- key: test.demo.factor",
        "  value: 0.85",
        "  unit: dimensionless",
        "  source: GB 50014-2021 表 6.x.x",
        "  note: demo",
    ]))
    lib = load_coefficients(pkg)
    assert lib.get("test.demo.factor").value == pytest.approx(0.85)
    assert lib.data_version == "9.9.9-test"


def test_entry_without_source_rejected(tmp_path: Path) -> None:
    """R2：无 source 条目加载失败。"""
    pkg = _write_pkg(tmp_path, "\n".join([
        "- key: test.no.source",
        "  value: 1.0",
        "  unit: dimensionless",
        "  source: ''",
        "  note: x",
    ]))
    with pytest.raises(Exception, match=".+"):
        load_coefficients(pkg)


def test_duplicate_key_rejected(tmp_path: Path) -> None:
    body = "\n".join([
        "- key: test.dup",
        "  value: 1.0",
        "  unit: dimensionless",
        "  source: s",
        "  note: x",
    ] * 2)
    pkg = _write_pkg(tmp_path, body)
    with pytest.raises(Exception, match=".+"):
        load_coefficients(pkg)
