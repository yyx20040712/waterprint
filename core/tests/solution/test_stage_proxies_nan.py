"""阶段代理分 NaN 防护回归草案（AUD-B1 缓解面+AUD-B3）——core/tests 转正候选件。

输入:  waterprint.solution.joint_enumeration.stage.stage_proxies（构造 frame）
输出:  margin_min 全 NaN/部分 NaN → 裕度分量降级中位 1/2（能耗分量保留
       区分度，代理分恒有限）；margins 恒值无区分度行为不变断言；空可行集
       → 空代理分早退（不触 min([]) 裸 ValueError）
"""

from __future__ import annotations

import importlib
from math import isfinite

import pandas
import pytest

stage_proxies = importlib.import_module(
    "waterprint.solution.joint_enumeration.stage"
).stage_proxies


def _frame(rows: list[dict[str, float]]) -> pandas.DataFrame:
    return pandas.DataFrame(rows)


def test_nan_margins_degrade_to_midpoint_energy_kept() -> None:
    """AUD-B1 缓解面：margin_min 全 NaN（当前全库单元无 margin_ 键产出形）
    → 裕度分量=中位 1/2，能耗分量保留区分度（旧行为：min-max 对 NaN
    恒 False → 归一全 NaN → 代理分 NaN，beam 排序退化）。"""
    frame = _frame([
        {"margin_min": float("nan"), "e_pump": 30.0},
        {"margin_min": float("nan"), "e_pump": 10.0},
    ])
    proxies = stage_proxies(frame, (0, 1), 0.5, 0.0)
    assert all(isfinite(value) for value in proxies.values())  # NaN 防护主断言
    # 行0：0.5×1/2+0.5×能耗归一倒置(30→最差=0)=0.25；行1：0.5×1/2+0.5×1=0.75
    assert proxies[0] == pytest.approx(0.25)
    assert proxies[1] == pytest.approx(0.75)


def test_partial_nan_margins_degrade_whole_component() -> None:
    """部分 NaN：分量级降级（含任一 NaN 即整分量取中位——与无区分度
    high<=low 分支同语义，禁编造区分度）。"""
    frame = _frame([
        {"margin_min": 1.0, "e_pump": 30.0},
        {"margin_min": float("nan"), "e_pump": 10.0},
    ])
    proxies = stage_proxies(frame, (0, 1), 1.0, 0.0)  # share=1：纯裕度分量
    assert all(isfinite(value) for value in proxies.values())
    assert proxies[0] == pytest.approx(0.5)
    assert proxies[1] == pytest.approx(0.5)


def test_constant_margins_behavior_unchanged() -> None:
    """恒值 margins（无区分度，无 NaN）：既有行为不变——裕度分量中位
    1/2+能耗分量正常区分。"""
    frame = _frame([
        {"margin_min": 2.0, "e_pump": 30.0},
        {"margin_min": 2.0, "e_pump": 10.0},
    ])
    proxies = stage_proxies(frame, (0, 1), 0.5, 0.0)
    assert proxies[0] == pytest.approx(0.25)
    assert proxies[1] == pytest.approx(0.75)


def test_empty_feasible_returns_empty_proxies() -> None:
    """AUD-B3：空可行集早退——feasible=() → {}（全行域拒级无候选无代理分；
    旧行为：_normalized([]) 的 min([]) 裸 ValueError 上浮 500 面）。"""
    frame = _frame([
        {"margin_min": float("nan"), "e_pump": 30.0},
        {"margin_min": float("nan"), "e_pump": 10.0},
    ])
    assert stage_proxies(frame, (), 0.5, 0.0) == {}
