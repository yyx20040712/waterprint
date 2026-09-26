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
        "price_data_version: '1.0.0-test'\nunit_scales:\n  m3: 1\n",
        encoding="utf-8",
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


# ══ 批6d unit_scales 金额倍率契约（万元族消费面 10⁴ 归一——
#     b6d-design §二案甲；[HUMAN-LOCK] 2026-09-26 预授权①随批落地）══

_REPO_UNIT_PRICES = (
    Path(__file__).resolve().parents[3] / "data" / "unit_prices"
)


def test_real_pack_unit_scales_contract() -> None:
    """批6d 对拍：真包全条目单位入契约（装载即证）+万元族倍率 1e4+版本 1.1.0。

    d1 W-2 补强：万元（非台）族 common.* 合计项单独点名对拍（8 条在册——
    循环面覆盖之外再留显式锚）。"""
    lib = load_prices(_REPO_UNIT_PRICES)
    assert lib.data_version == "1.1.0"  # 批6d 升版（minor=行为性声明新增）
    for key in lib.keys(""):  # 前缀空串=全键列举（PriceBook 非映射——keys() 正门）
        item = lib.get(key)
        if item.unit in ("万元/台", "万元"):
            assert item.scale == pytest.approx(1e4), key
        else:
            assert item.scale == pytest.approx(1.0), key
    assert lib.get("common.plc_scada").scale == pytest.approx(1e4)  # 万元族显式锚
    assert lib.get("common.sludge_thickening_dewatering").price == pytest.approx(65.0)


def test_unit_scales_section_missing_rejected(tmp_path: Path) -> None:
    """批6d 硬契约：manifest 缺 unit_scales 节=装载拒绝（无遗留分叉）。"""
    target = tmp_path / "unit_prices"
    target.mkdir()
    (target / "manifest.yaml").write_text(
        "price_data_version: '1.0.0-test'\n", encoding="utf-8"
    )
    (target / "buildings.yaml").write_text(
        "- key: KL9-TEST\n  name: 测试子目\n  unit: m3\n  price: 100.0\n"
        "  source: 测试定额\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="unit_scales"):
        load_prices(target)


def test_entry_unit_outside_scales_rejected(tmp_path: Path) -> None:
    """批6d 硬契约：条目单位未声明倍率=装载拒绝（缺列即拒）。"""
    target = tmp_path / "unit_prices"
    target.mkdir()
    (target / "manifest.yaml").write_text(
        "price_data_version: '1.0.0-test'\nunit_scales:\n  m3: 1\n",
        encoding="utf-8",
    )
    (target / "buildings.yaml").write_text(
        "- key: EQ-TEST\n  name: 测试设备\n  unit: 万元/台\n  price: 10.0\n"
        "  source: 测试询价\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="unit_scales"):
        load_prices(target)
