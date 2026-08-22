"""sludge 镜像测试：污泥量契约（DS 守恒、含水率反解、校验）。

输入:  waterprint.contracts.sludge 公开符号
输出:  混合守恒/构造校验断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.sludge")
make_sludge = getattr(_mod, "make_sludge", None)
mix = getattr(_mod, "mix", None)

pytestmark = pytest.mark.skipif(
    None in (make_sludge, mix),
    reason="实现未就绪：waterprint.contracts.sludge 公开符号缺失（M1）",
)


def _sludge(q_wet: float, ds: float, moisture: float):
    return make_sludge(q_wet=q_wet, ds=ds, moisture=moisture)


def test_mix_conserves_dry_solids() -> None:
    """R1：混合 DS 守恒（Σds 前后相等）——§14.2 铁律。"""
    f1 = _sludge(0.01, 2.0, 0.98)
    f2 = _sludge(0.02, 3.0, 0.96)
    merged = mix([f1, f2])
    assert merged.ds == pytest.approx(5.0)
    assert merged.q_wet == pytest.approx(0.03)


def test_mix_moisture_is_derived_not_averaged() -> None:
    """R1：含水率由总量反解，非简单平均（混合后唯一确定）。"""
    f1 = _sludge(0.01, 2.0, 0.98)
    f2 = _sludge(0.01, 2.0, 0.90)
    merged = mix([f1, f2])
    assert merged.moisture != pytest.approx(0.94)  # 非平均
    assert 0.90 < merged.moisture < 0.98  # 介于两股之间


def test_invalid_moisture_rejected() -> None:
    """R3：含水率域 [0,1) 之外拒绝。"""
    with pytest.raises(Exception):
        _sludge(0.01, 1.0, 1.0)
    with pytest.raises(Exception):
        _sludge(0.01, 1.0, -0.1)


def test_negative_quantities_rejected() -> None:
    """R3：q_wet/ds 非负。"""
    with pytest.raises(Exception):
        _sludge(-0.01, 1.0, 0.98)
    with pytest.raises(Exception):
        _sludge(0.01, -1.0, 0.98)
