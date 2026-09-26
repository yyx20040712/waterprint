"""app_carbon 镜像测试：碳排放三范围全厂投影（B4-2c，终裁定案 master-ruling D4~D8）。

输入:  base summary 合并面（power_*/dose_*/influent_*/effluent_tn_load 平键）
       + CoefficientsView 桩（factor.carbon.* 键——单元测试注入值，不与
       factors.yaml 数据耦合）
输出:  carbon_summary_of/_with_carbon 行为断言（T1~T7：sparse 三态容错/
       分项合成/合计律/纯函数双跑/N2O 换算数值锚/量级带断言/total 双在场律）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：B4-2c 终裁 D4~D8——C-F1~F9 全集（电/药/N2O 厂内+出水/CH4/
# direct+indirect 合计/total 双在场律/intensity 吨水强度）；sparse=
# 数据键或因子键缺席跳式；磁种键缺席恒跳（R-B42c-3⑤）；数值字面量
# 零（44/28 与 1e-3 键化）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from waterprint.app_carbon import _with_carbon, carbon_summary_of


class _StubCoefficients:
    """CoefficientsView 协议桩：注入因子表，keys 前缀列举/get 失联抛错同真源。"""

    def __init__(self, values: dict[str, float]) -> None:
        self._values = values

    @property
    def data_version(self) -> str:
        return "stub"

    def get(self, key: str) -> Any:
        if key not in self._values:
            raise KeyError(f"失联键（领域异常语义）: {key}")
        return SimpleNamespace(
            value=self._values[key], unit="", source="", note="")

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(sorted(k for k in self._values if k.startswith(prefix)))


# 磁种键刻意缺席（本批不立——R-B42c-3⑤ 的恒跳实证向量）
_FULL_LIB = _StubCoefficients({
    "factor.carbon.grid_co2": 0.5,
    "factor.carbon.n2o_ef_plant": 0.016,
    "factor.carbon.n2o_ef_effluent": 0.005,
    "factor.carbon.ch4_b0": 0.6,
    "factor.carbon.ch4_mcf": 0.03,
    "factor.carbon.gwp_ch4": 25.0,
    "factor.carbon.gwp_n2o": 250.0,
    "factor.carbon.pac": 2.0,
    "factor.carbon.pam": 4.0,
    "factor.carbon.molar_n2o_n": 1.5,
})

_BASE_FULL = {
    "power_total_kwh_d": 100.0,
    "dose_pac_kg_d": 3.0, "dose_pam_kg_d": 2.0, "dose_seed_kg_d": 1.0,
    "influent_flow_m3_d": 200.0,
    "influent_tn_load_kg_d": 10.0, "effluent_tn_load_kg_d": 4.0,
    "influent_bod5_load_kg_d": 40.0,
}


def test_t1_sparse_three_modes() -> None:
    """T1 sparse 三态：①数据键缺席工况→空映射；②因子键缺席→分项跳；
    ③全缺席（空系数包）→全工况空映射无 carbon 键。"""
    view = carbon_summary_of(
        {"design": _BASE_FULL, "sludge_line": {"ds_out": 3.0}}, _FULL_LIB)
    assert view["sludge_line"] == {}
    only_grid = _StubCoefficients({"factor.carbon.grid_co2": 0.5})
    partial = carbon_summary_of({"design": _BASE_FULL}, only_grid)
    assert set(partial["design"]) == {
        "carbon_indirect_electricity_kgco2e_d", "carbon_indirect_kgco2e_d"}
    empty = carbon_summary_of({"design": _BASE_FULL}, _StubCoefficients({}))
    assert empty == {"design": {}}


def test_t2_chemical_parts_synthesis() -> None:
    """T2 分项合成：三 dose 在场但磁种因子缺席→pac+pam 两项和（恒跳实证）。"""
    view = carbon_summary_of({"design": _BASE_FULL}, _FULL_LIB)
    assert view["design"]["carbon_indirect_chemicals_kgco2e_d"] == 14.0  # 3×2+2×4


def test_t3_totals_composition() -> None:
    """T3 合计律：indirect=electricity+chemicals；direct=n2o_plant+n2o_effluent+ch4；
    total=direct+indirect；intensity=total÷Q（双在场全满足）。"""
    out = carbon_summary_of({"design": _BASE_FULL}, _FULL_LIB)["design"]
    assert out["carbon_indirect_electricity_kgco2e_d"] == 50.0  # 100×0.5
    assert out["carbon_indirect_kgco2e_d"] == 64.0  # 50+14
    assert out["carbon_direct_n2o_plant_kgco2e_d"] == 60.0   # 10×0.016×1.5×250
    assert out["carbon_direct_n2o_effluent_kgco2e_d"] == 7.5  # 4×0.005×1.5×250
    assert out["carbon_direct_ch4_kgco2e_d"] == 18.0          # 40×0.6×0.03×25
    assert out["carbon_direct_kgco2e_d"] == 85.5
    assert out["carbon_total_kgco2e_d"] == 149.5
    assert out["carbon_intensity_kgco2e_m3"] == 0.7475  # 149.5/200


def test_t4_pure_function_double_run() -> None:
    """T4 纯函数双跑：同输入两跑全等；不 mutate base（_with_carbon 按
    先例 update 注入——投影件本身只读）。"""
    base = {"design": dict(_BASE_FULL)}
    frozen = {"design": dict(_BASE_FULL)}
    assert (carbon_summary_of(base, _FULL_LIB)
            == carbon_summary_of(base, _FULL_LIB))
    assert base == frozen
    merged = _with_carbon(dict(base), carbon_summary_of(base, _FULL_LIB))
    assert merged["design"]["TN" if "TN" in merged["design"]
                            else "carbon_total_kgco2e_d"] is not None
    assert "carbon_total_kgco2e_d" in merged["design"]


def test_t5_n2o_conversion_anchor() -> None:
    """T5 数值锚（N2O 链）：tn_load×EF×molar×GWP 用真因子位数值复算——
    1494.71 kgN/d × 0.016 × 1.5714286 × 273 ≈ 10259.7（golden design 实测锚
    10259.69——相对容差 1e-4）。"""
    real_lib = _StubCoefficients({
        "factor.carbon.n2o_ef_plant": 0.016,
        "factor.carbon.molar_n2o_n": 1.5714286,
        "factor.carbon.gwp_n2o": 273.0,
    })
    base = {"design": {"influent_tn_load_kg_d": 1494.71}}
    out = carbon_summary_of(base, real_lib)["design"]
    assert out["carbon_direct_n2o_plant_kgco2e_d"] == pytest.approx(
        10259.69, rel=1e-4)


def test_t6_magnitude_band_anchor() -> None:
    """T6 量级带断言：golden municipal design 实数桩（power 7239.75/dose
    1042.82+48.28/Q 34760.7/负荷 1494.71+373.68+6952.14）→电 3885 落
    [1e3,1e4]、药 2069 落 [1e3,1e4]、total 20419 落 [1e4,1e5] 量级带。
    gwp_ch4 桩值=factors.yaml 数据面镜像——带断言不敏感，数据面值变须同步本桩（批2c 注记）。"""
    lib = _StubCoefficients({
        "factor.carbon.grid_co2": 0.5366, "factor.carbon.pac": 1.764,
        "factor.carbon.pam": 4.76,
        "factor.carbon.n2o_ef_plant": 0.016,
        "factor.carbon.n2o_ef_effluent": 0.005,
        "factor.carbon.molar_n2o_n": 1.5714286,
        "factor.carbon.ch4_b0": 0.6, "factor.carbon.ch4_mcf": 0.03,
        "factor.carbon.gwp_ch4": 27.0, "factor.carbon.gwp_n2o": 273.0,
    })
    base = {"design": {
        "power_total_kwh_d": 7239.75,
        "dose_pac_kg_d": 1042.82, "dose_pam_kg_d": 48.28,
        "influent_flow_m3_d": 34760.7,
        "influent_tn_load_kg_d": 1494.71, "effluent_tn_load_kg_d": 373.68,
        "influent_bod5_load_kg_d": 6952.14,
    }}
    out = carbon_summary_of(base, lib)["design"]
    assert 1e3 < out["carbon_indirect_electricity_kgco2e_d"] < 1e4
    assert 1e3 < out["carbon_indirect_chemicals_kgco2e_d"] < 1e4
    assert 1e4 < out["carbon_total_kgco2e_d"] < 1e5
    assert 0.5 < out["carbon_intensity_kgco2e_m3"] < 0.7  # 全国典型带内


def test_t7_total_dual_presence_rule() -> None:
    """T7 双在场律（终裁 D4）：indirect 在+direct 缺→无 total/intensity；
    direct 在+indirect 缺→同；total 在+Q 缺→仅无 intensity。"""
    only_indirect = carbon_summary_of(
        {"design": {"power_total_kwh_d": 100.0, "influent_flow_m3_d": 200.0}},
        _FULL_LIB)["design"]
    assert "carbon_total_kgco2e_d" not in only_indirect
    assert "carbon_intensity_kgco2e_m3" not in only_indirect
    only_direct = carbon_summary_of(
        {"design": {"influent_tn_load_kg_d": 10.0, "influent_flow_m3_d": 200.0}},
        _FULL_LIB)["design"]
    assert "carbon_total_kgco2e_d" not in only_direct
    no_flow = carbon_summary_of(
        {"design": dict(_BASE_FULL, influent_flow_m3_d=0.0)}, _FULL_LIB)["design"]
    assert "carbon_total_kgco2e_d" in no_flow  # total 双在场律满足
    assert "carbon_intensity_kgco2e_m3" not in no_flow  # 零流量退化面不落强度
