"""unit_detail 服务纯函数测试（B2 R2 回炉 R2d——_finite_mapping 四态直测）。

输入:  services.unit_detail._finite_mapping（端口段有限性闸——纯函数层）
输出:  断言族：①正常有限值直通（排序键序）②NaN/Inf 剔除（rows 面
        _finite_or_none 同口径）③不可转值（None/字符串/bool）剔除
        ④空映射=空映射
"""

from __future__ import annotations

import math

from waterprint_server.services.unit_detail import _finite_mapping


def test_finite_values_pass_through_sorted() -> None:
    """正常有限值直通（键序 sorted 确定性——R3 随手②：dict == 忽略键序，
    list(keys) 显式锚定）。"""
    out = _finite_mapping({"b": 2.0, "a": 1.5, "c": 0})
    assert out == {"a": 1.5, "b": 2.0, "c": 0.0}
    assert list(out.keys()) == ["a", "b", "c"]


def test_non_finite_values_dropped() -> None:
    """NaN/±Inf 剔除（JSON 面 NaN 非法/Inf 溢出——防 500 纵深闸）。"""
    raw = {
        "ok": 1.0,
        "nan": float("nan"),
        "inf": math.inf,
        "ninf": -math.inf,
    }
    assert _finite_mapping(raw) == {"ok": 1.0}


def test_non_convertible_values_dropped() -> None:
    """不可转值剔除（None/字符串/bool——bool 经 float() 得 0/1 须拒：
    类型面与 _finite_or_none 同判）。"""
    raw = {"ok": 3.5, "none": None, "text": "1.5", "flag": True}
    assert _finite_mapping(raw) == {"ok": 3.5}


def test_empty_mapping_is_empty() -> None:
    """空映射=空映射（无端口数据面）。"""
    assert _finite_mapping({}) == {}
