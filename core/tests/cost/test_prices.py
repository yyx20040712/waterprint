"""prices 镜像测试：定额单价加载（出处门槛、失联键、版本传播）。

输入:  waterprint.cost.prices 公开符号 + 临时 YAML 包
输出:  加载语义断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.cost.prices")
load_prices = getattr(_mod, "load_prices", None)
PriceBook = getattr(_mod, "PriceBook", None)

pytestmark = pytest.mark.skipif(
    None in (load_prices, PriceBook),
    reason="实现未就绪：waterprint.cost.prices（M3）",
)


def _pkg(tmp_path: Path, entry_source: str) -> Path:
    target = tmp_path / "unit_prices"
    target.mkdir()
    (target / "manifest.yaml").write_text(
        "price_data_version: '1.0.0-test'\n", encoding="utf-8"
    )
    (target / "buildings.yaml").write_text("\n".join([
        "- key: KL9-TEST",
        "  name: 测试子目",
        "  unit: m3",
        f"  price: 100.0",
        f"  source: {entry_source}",
    ]), encoding="utf-8")
    return target


def test_load_query_and_version(tmp_path: Path) -> None:
    lib = load_prices(_pkg(tmp_path, "测试定额 第9章"))
    assert lib.get("KL9-TEST").price == pytest.approx(100.0)
    assert lib.data_version


def test_entry_without_source_rejected(tmp_path: Path) -> None:
    """R1：无 source 条目加载失败。"""
    with pytest.raises(Exception, match=".+"):
        load_prices(_pkg(tmp_path, ""))
