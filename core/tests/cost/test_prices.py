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
    """批6d 对拍：真包全条目单位入契约（装载即证）+万元族倍率 1e4+版本 1.2.0
    （批6o 词表标准化升版——1.1.0 批6d/1.2.0 批6o）。

    d1 W-2 补强：万元（非台）族 common.* 合计项单独点名对拍（8 条在册——
    循环面覆盖之外再留显式锚）。"""
    lib = load_prices(_REPO_UNIT_PRICES)
    assert lib.data_version == "1.2.0"  # 批6o 升版（词面 minor=台/套词表标准化）
    for key in lib.keys(""):  # 前缀空串=全键列举（PriceBook 非映射——keys() 正门）
        item = lib.get(key)
        if item.unit in ("万元/台", "万元/套", "万元"):
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


# ══ 批6o 词表标准化（台/套裁量——用户裁决 2026-09-28 增补五十六 H+增补
#     六十二③：单体设备类=台、散件布设类〔管路/分布式系统〕=套，逐条裁量；
#     逐条审计表单源=.workflow/backend-calc-complete/b6o-wording-audit.md §二
#     +数据包 README.md 词表面；[HUMAN-LOCK] 2026-09-29 预授权①随批落地）══

# 设备族 42 条台/套逐键冻结表（12 套+30 台——改任一条单位/增删设备条目即红，
# 词表变更=显式数据批事件）：
_EQUIP_UNIT_BY_KEY = {
    # 套=散件布设类（管路/分布式组件/成套系统/批量散件）——12 条：
    "aao.microporous_aerator_piping": "万元/套",
    "cass.microporous_aerator_piping": "万元/套",
    "cass.blower_station": "万元/套",
    "chuchenchi.sludge_valve_piping": "万元/套",
    "gaomidu.inclined_tube_media": "万元/套",
    "gaomidu.pac_dosing_system": "万元/套",
    "gaomidu.pam_dosing_system": "万元/套",
    "kw_ningjiao.pac_dosing_system": "万元/套",
    "kw_ningjiao.pam_dosing_system": "万元/套",
    "vxinglvchi.long_stem_filter_nozzle": "万元/套",
    "vxinglvchi.water_air_distribution": "万元/套",
    "vxinglvchi.pneumatic_valves": "万元/套",
    # 台=单体设备类——30 条：
    "cugeshan.screen_rotary": "万元/台",
    "cugeshan.screw_conveyor_press": "万元/台",
    "xigeshan.drum_screen": "万元/台",
    "xigeshan.screw_conveyor_press": "万元/台",
    "chenshachi.vortex_grit_separator": "万元/台",
    "chenshachi.grit_water_separator": "万元/台",
    "chenshachi.roots_blower": "万元/台",
    "chuchenchi.center_drive_sludge_scraper": "万元/台",
    "cass.rotary_decanter": "万元/台",
    "cass.sludge_return_pump": "万元/台",
    "cass.excess_sludge_pump": "万元/台",
    "cass.online_do_mlss_meter": "万元/台",
    "gaomidu.flash_mixer": "万元/台",
    "gaomidu.flocculation_mixer": "万元/台",
    "gaomidu.sludge_scraper": "万元/台",
    "vxinglvchi.backwash_blower": "万元/台",
    "vxinglvchi.backwash_pump": "万元/台",
    "ziwai.uv_disinfection_module": "万元/台",
    "ziwai.automatic_water_level_weir": "万元/台",
    "ziwai.power_distribution_cabinet": "万元/台",
    "tiaojiechi.submersible_mixer": "万元/台",
    "kw_tiaojiechi.submersible_mixer_exproof": "万元/台",
    "kw_tiaojiechi.coal_slurry_pump": "万元/台",
    "kw_chenshachi.traveling_sand_suction": "万元/台",
    "kw_chenshachi.grit_water_separator": "万元/台",
    "kw_ningjiao.flash_mixer": "万元/台",
    "kw_ningjiao.flocculation_mixer": "万元/台",
    "kw_cifenli.magnetic_disk_separator": "万元/台",
    "kw_cifenli.magnetic_seed_recovery": "万元/台",
    "kw_cifenli.backwash_pump": "万元/台",
}


def test_unit_vocabulary_freeze() -> None:
    """批6o 台/套词表逐键冻结：42 条设备条目单位全表对拍+设备族键集双向恒等
    +套族倍率与台族同 1e4（值零变语义——词面变更非数值变更）。"""
    lib = load_prices(_REPO_UNIT_PRICES)
    assert lib.data_version == "1.2.0"  # 批6o 词表标准化升版（词面 minor）
    equipment = sorted(
        key for key in lib.keys("")
        if lib.get(key).unit in ("万元/台", "万元/套"))
    assert equipment == sorted(_EQUIP_UNIT_BY_KEY), (
        "设备族键集漂移（增删条目须随批改本冻结表）")
    for key, unit in _EQUIP_UNIT_BY_KEY.items():
        item = lib.get(key)
        assert item.unit == unit, key
        assert item.quantity is not None, key  # 设备族台/套条目携参考 quantity 列
    suite_keys = [k for k, u in _EQUIP_UNIT_BY_KEY.items() if u == "万元/套"]
    assert len(suite_keys) == 12 and len(_EQUIP_UNIT_BY_KEY) == 42  # 裁量定版计数锚
    for key in suite_keys:
        assert lib.get(key).scale == pytest.approx(1e4), key  # 套=台同倍率（值零变）


def test_field_mapping_unit_consistency() -> None:
    """批6o 回炉补强（d1-B2/k1-W3 钉死）：field_mapping 全映射行 unit 与
    PriceBook 同键条目逐行恒等——cass.microporous_aerator_piping 等未消费键
    无映射行（映射行集恰 7 行），未来扩行而词面失配即红（R2 量纲一致永久锚）。"""
    from waterprint.cost.takeoff import load_field_mapping

    mapping = load_field_mapping(
        _REPO_UNIT_PRICES / "field_mapping.yaml")
    lib = load_prices(_REPO_UNIT_PRICES)
    equip_rows = 0
    for row in mapping.rules:
        assert row.unit == lib.get(row.price_key).unit, row.price_key
        if lib.get(row.price_key).unit in ("万元/台", "万元/套"):
            equip_rows += 1
    # 设备计数类映射行恰 3：cass.rotary_decanter（台）/ziwai.uv_disinfection_
    # module（台）/aao.microporous_aerator_piping（套）——cass 曝气管路无映射行
    assert equip_rows == 3
