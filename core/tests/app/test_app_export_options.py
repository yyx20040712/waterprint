"""app_export_options 镜像测试（批6j 拆件）：路由选项 DSL 解析器族单元面。

输入:  _check_export_options/_station_overrides_of/_inlet_datum_of/
       _scale_denom_of（伴生件公开解析器族——从 app_export 真源随段迁）
输出:  白名单/形态/域/成对闸断言（路由级组合真值表归 test_export_profile
       族——本件钉解析器单元语义与再导出恒等）。
"""

from __future__ import annotations

import pytest

from waterprint.app_export import ArtifactKindNotReady as ReExported
from waterprint.app_export_options import (
    ArtifactKindNotReady,
    _check_export_options,
    _inlet_datum_of,
    _scale_denom_of,
    _station_overrides_of,
)


def test_reexport_identity() -> None:
    """拆件公开面恒等：app_export 再导出的异常基类=本件真源（beam→search
    先例同款——公开 import 路径零改动实证）。"""
    assert ReExported is ArtifactKindNotReady


def test_check_export_options_whitelist_and_kind_gates() -> None:
    """未知键拒（GR-09 词表纪律）+非 dxf kind 零消费面四键族拒。"""
    with pytest.raises(ArtifactKindNotReady, match="未知选项"):
        _check_export_options({"typo_key": "x"}, "dxf")
    for key in ("h_scale", "v_scale", "station_overrides", "water_level"):
        with pytest.raises(ArtifactKindNotReady, match="仅 kind='dxf'"):
            _check_export_options({key: "1"}, "calcbook")


def test_scale_denom_domain() -> None:
    """比例分母：isdecimal+域 [1, SCALE_DENOM_MAX]——Unicode 数字/超长/
    越界三拒+正常解析。"""
    from waterprint.drafting.sheets import SCALE_DENOM_MAX

    assert _scale_denom_of("2000", "h_scale") == 2000
    assert _scale_denom_of(" 2000 ", "h_scale") == 2000  # strip 先行（PD3 文档化行为）
    for bad in ("②", "0", "-1", "1e3", ""):
        with pytest.raises(ArtifactKindNotReady, match="比例分母"):
            _scale_denom_of(bad, "h_scale")
    with pytest.raises(ArtifactKindNotReady, match="比例分母"):
        _scale_denom_of(str(SCALE_DENOM_MAX + 1), "h_scale")


def test_station_overrides_forms() -> None:
    """站距覆盖 DSL：None/空串→None；缺=/键值空/形态/非正/重复五拒。"""
    assert _station_overrides_of(None) is None
    assert _station_overrides_of("  ") is None
    assert _station_overrides_of("unit_b=30.5") == {"unit_b": 30.5}
    for raw, match in (
        ("unit_b", "缺 '='"), ("unit_b=", "键或值空"), ("=30", "键或值空"),
        ("unit_b=1e3", "非十进制小数形态"), ("unit_b=0", "须为正有限站距米值"),
        ("unit_b=nan", "非十进制小数形态"),
        ("unit_b=30,unit_b=44", "重复"),
    ):
        with pytest.raises(ArtifactKindNotReady, match=match):
            _station_overrides_of(raw)


def test_inlet_datum_default_pair_and_forms() -> None:
    """批6j 进厂标高解析：双 None→(相对 ±0.00 默认, False)；成对必传；
    带符号十进制+有限域；负值合法（海平面下场景）。"""
    datum, provided = _inlet_datum_of(None, None)
    assert provided is False
    assert dict(datum) == {"water_level": 0.0, "ground_elev": 0.0}
    datum, provided = _inlet_datum_of("1053.2", "1051.0")
    assert provided is True
    assert dict(datum) == {"water_level": 1053.2, "ground_elev": 1051.0}
    datum, _ = _inlet_datum_of("-3.5", "-5.0")
    assert datum["water_level"] == -3.5 and datum["ground_elev"] == -5.0
    with pytest.raises(ArtifactKindNotReady, match="成对必传"):
        _inlet_datum_of("1053.2", None)
    with pytest.raises(ArtifactKindNotReady, match="成对必传"):
        _inlet_datum_of(None, "1051.0")
    for bad in ("1e3", "1_000", "１０", "abc", "", "  ", ".", "-.5", "3."):
        with pytest.raises(ArtifactKindNotReady, match="非带符号十进制形态"):
            _inlet_datum_of(bad, "10")
    # 有限域（float 可解析但 NaN/Inf 无高程语义——regex 先拦 'nan'/'inf'
    # 字面量；巨大有限值按工程裁量放行=design 态 GIGO，与站距同口径）。
    datum, provided = _inlet_datum_of("99999.5", "99999.0")
    assert provided and datum["water_level"] == 99999.5
