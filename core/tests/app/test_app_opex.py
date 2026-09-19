"""app_opex 镜像测试：运行成本全厂投影（B4-2b，终裁定案 master-ruling-r2）。

输入:  base summary 合并面（power_*/dose_* 平键）+ CoefficientsView 桩
       （factor.opex.* 单价五键——单元测试注入值，不与 factors.yaml 数据耦合）
输出:  opex_summary_of/_with_opex 行为断言（sparse 键族/分项合成/合计律/
       factor 缺席容错/纯函数双跑恒等/合并语义）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：B4-2b 终裁 §三 S3——F1 电费=power_total×电价×年化天数；
# F2 药剂=Σ在场 dose×单价×年化天数（元/kg 口径）；F3 合计=Σ在场分项
# （无分项不立）；sparse=单价键前缀列举判在场（单键缺席跳分项/全
# 缺席无 cost 键）；年化因子缺失→F1/F2 均不立（无年化不立年键）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from waterprint.app_opex import _with_opex, opex_summary_of


class _StubCoefficients:
    """CoefficientsView 协议桩：注入单价表，keys 前缀列举/get 失联抛错同真源。"""

    def __init__(self, prices: dict[str, float]) -> None:
        self._prices = prices

    @property
    def data_version(self) -> str:
        return "stub"

    def get(self, key: str) -> Any:
        if key not in self._prices:
            raise KeyError(f"失联键（领域异常语义）: {key}")
        return SimpleNamespace(
            value=self._prices[key], unit="", source="", note="")

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(sorted(k for k in self._prices if k.startswith(prefix)))


def _lib(**prices: float) -> _StubCoefficients:
    return _StubCoefficients({f"factor.opex.{k}": v for k, v in prices.items()})


_FULL_LIB = _lib(electricity=0.5, pac=2.0, pam=4.0, magnetic_seed=1.0,
                 days_per_year=10.0)


def test_sparse_full_chain_and_total() -> None:
    """R1/F1~F3 全链：源键齐→三键全出；无源键工况→空映射（sparse）。"""
    base = {
        "design": {
            "power_total_kwh_d": 100.0, "dose_pac_kg_d": 3.0,
            "dose_pam_kg_d": 2.0, "dose_seed_kg_d": 1.5,
        },
        "sludge_line": {"ds_out": 3.0},  # 无 opex 源键
    }
    view = opex_summary_of(base, _FULL_LIB)
    assert view["design"] == {
        "cost_electricity_yuan_a": 500.0,   # 100×0.5×10
        "cost_chemicals_yuan_a": 155.0,     # (3×2+2×4+1.5×1)×10
        "cost_opex_yuan_a": 655.0,          # 500+155（合计律）
    }
    assert view["sludge_line"] == {}


def test_partial_sources_no_total_without_parts() -> None:
    """分项缺席合成：只 dose→chemicals+合计；只 power→electricity+合计；
    两者皆无→空（无分项不立合计）。"""
    only_dose = opex_summary_of(
        {"design": {"dose_pac_kg_d": 3.0, "dose_pam_kg_d": 2.0}}, _FULL_LIB)
    assert only_dose["design"] == {
        "cost_chemicals_yuan_a": 140.0, "cost_opex_yuan_a": 140.0}
    only_power = opex_summary_of(
        {"design": {"power_total_kwh_d": 100.0}}, _FULL_LIB)
    assert only_power["design"] == {
        "cost_electricity_yuan_a": 500.0, "cost_opex_yuan_a": 500.0}


def test_factor_absence_tolerated() -> None:
    """R1 factor 缺席容错：全缺席→无 cost 键；单键缺席→该分项跳过；
    年化键缺席→F1/F2 均不立。"""
    empty = opex_summary_of(
        {"design": {"power_total_kwh_d": 100.0, "dose_pac_kg_d": 3.0}},
        _StubCoefficients({}))
    assert empty["design"] == {}
    no_pac = opex_summary_of(
        {"design": {"power_total_kwh_d": 100.0, "dose_pac_kg_d": 3.0,
                     "dose_pam_kg_d": 2.0}},
        _lib(electricity=0.5, pam=4.0, days_per_year=10.0))
    assert no_pac["design"] == {
        "cost_electricity_yuan_a": 500.0,
        "cost_chemicals_yuan_a": 80.0,      # 仅 PAM 分项 (2×4)×10
        "cost_opex_yuan_a": 580.0}
    no_days = opex_summary_of(
        {"design": {"power_total_kwh_d": 100.0, "dose_pac_kg_d": 3.0}},
        _lib(electricity=0.5, pac=2.0))
    assert no_days["design"] == {}          # 年化缺席→年键不立


def test_pure_function_double_run_identical() -> None:
    """R2 纯投影：同输入双跑恒等。"""
    base = {"avg": {"power_total_kwh_d": 100.0, "dose_pam_kg_d": 2.0}}
    first: Any = opex_summary_of(base, _FULL_LIB)
    second = opex_summary_of(base, _FULL_LIB)
    assert first == second
    assert first["avg"]["cost_opex_yuan_a"] == 580.0  # 500+(2×4×10)


def test_with_opex_merge_semantics() -> None:
    """_with_opex 合并语义：同工况字典 update、base 键族优先、
    extra 独有工况不注入（_with_energy 同款）。"""
    base = {"design": {"BOD5": 8.0}, "avg": {"BOD5": 6.0}}
    extra = {"design": {"cost_opex_yuan_a": 655.0}, "other": {"cost_opex_yuan_a": 1.0}}
    merged = _with_opex(base, extra)
    assert merged["design"] == {"BOD5": 8.0, "cost_opex_yuan_a": 655.0}
    assert merged["avg"] == {"BOD5": 6.0}
    assert "other" not in merged
