"""app_carbon 镜像测试：碳排放三范围全厂投影（B4-2c，终裁定案 master-ruling D4~D8；批6b 扩）。

输入:  base summary 合并面（power_*/dose_*/influent_*/effluent_tn_load 平键
       +批6b 碳上游供数 fuel_gas_nm3_d/vs_degraded_kg_d/biogas_m3_d 平键）
       + CoefficientsView 桩（factor.carbon.* 键——单元测试注入值，不与
       factors.yaml 数据耦合）
输出:  carbon_summary_of/_with_carbon 行为断言（T1~T7：sparse 三态容错/
       分项合成/合计律/纯函数双跑/N2O 换算数值锚/量级带断言/total 双在场律；
       批6b T8~T10：燃料 CO₂/燃烧次要/消化净 CH₄ 三新式+sparse 新面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：B4-2c 终裁 D4~D8——C-F1~F9 全集（电/药/N2O 厂内+出水/CH4/
# direct+indirect 合计/total 双在场律/intensity 吨水强度）；sparse=
# 数据键或因子键缺席跳式；磁种键缺席恒跳（R-B42c-3⑤）；数值字面量
# 零（44/28 与 1e-3 键化）。批6b（2026-09-26）：C-F10~F12 范围一补全
# （燃料 CO₂+燃烧次要+消化净 CH₄——批3.5 追认已签实装面，direct
# 合计扩容；消化档 MCF 0.8 案 A 独立核算废水线毯式 0.03 维持）。
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


# ── 批6b 碳范围一补全（C-F10~F12——批3.5 追认已签实装面）──
# 真因子位数值桩（factors.yaml 1.7.0 数据面镜像——数据面值变须同步本桩）
_B6B_VALUES = {
    "factor.carbon.ch4_b0": 0.6,
    "factor.carbon.gwp_ch4": 27.0,
    "factor.carbon.gwp_n2o": 273.0,
    "factor.carbon.ganhua_ef_co2": 2.1622,
    "factor.carbon.ganhua_ef_ch4": 3.8931e-05,
    "factor.carbon.ganhua_ef_n2o": 3.8931e-05,
    "factor.carbon.dig_mcf": 0.8,
    "factor.carbon.dig_ch4_frac": 0.6,
    "factor.carbon.dig_gas_recovery": 0.9,
    "factor.carbon.ch4_density_std": 0.716,
}
_B6B_LIB = _StubCoefficients(dict(_B6B_VALUES))


def test_t8_fuel_terms() -> None:
    """T8 燃料双分项（C-F10/C-F11）：CO₂ 主项+CH₄/N₂O 次要项（追认链
    复算——1200 Nm³/d×2.1622=2594.64；×3.8931e-5×(27+273)=14.01516）。"""
    out = carbon_summary_of(
        {"design": {"fuel_gas_nm3_d": 1200.0}}, _B6B_LIB)["design"]
    assert out["carbon_direct_fuel_co2_kgco2e_d"] == pytest.approx(
        2594.64, rel=1e-12)
    assert out["carbon_direct_fuel_minor_kgco2e_d"] == pytest.approx(
        14.01516, rel=1e-12)
    assert out["carbon_direct_kgco2e_d"] == pytest.approx(
        2594.64 + 14.01516, rel=1e-12)


def test_t9_digest_net_ch4() -> None:
    """T9 消化净 CH₄（C-F12 案 A）：gross−回收 R 全因子复算——
    900×0.6×0.8=432；R=810×0.6×0.9×0.716=313.1784；净 118.8216×27=
    3208.1832 kgCO2e/d（带内恒正：R 系数 0.54×0.716=0.38664<0.48）。"""
    out = carbon_summary_of(
        {"design": {"vs_degraded_kg_d": 900.0, "biogas_m3_d": 810.0}},
        _B6B_LIB)["design"]
    assert out["carbon_direct_ch4_digest_kgco2e_d"] == pytest.approx(
        3208.1832, rel=1e-12)


def test_t10_new_terms_sparse_faces() -> None:
    """T10 新分项 sparse 三面：①次要因子缺一只→F11 整式跳（F10 仍在）；
    ②消化双源缺一（biogas 缺）→F12 整式跳；③新分项入 direct 合计链
    （F6 扩容——新分项与既有 F3~F5 同和）。"""
    lib_no_minor = _StubCoefficients({
        k: v for k, v in _B6B_VALUES.items()
        if k != "factor.carbon.ganhua_ef_n2o"})
    out = carbon_summary_of(
        {"design": {"fuel_gas_nm3_d": 1200.0}}, lib_no_minor)["design"]
    assert "carbon_direct_fuel_minor_kgco2e_d" not in out
    assert out["carbon_direct_fuel_co2_kgco2e_d"] == pytest.approx(2594.64)
    out_vs_only = carbon_summary_of(
        {"design": {"vs_degraded_kg_d": 900.0}}, _B6B_LIB)["design"]
    assert out_vs_only == {}  # 双源在场律：biogas 缺→F12 不立亦无 direct
    lib_all = _StubCoefficients({
        **_B6B_VALUES,
        "factor.carbon.grid_co2": 0.5366,
        "factor.carbon.n2o_ef_plant": 0.016,
        "factor.carbon.n2o_ef_effluent": 0.005,
        "factor.carbon.molar_n2o_n": 1.5714286,
        "factor.carbon.ch4_mcf": 0.03,
    })
    base = {
        "power_total_kwh_d": 100.0,
        "influent_tn_load_kg_d": 10.0, "effluent_tn_load_kg_d": 4.0,
        "influent_bod5_load_kg_d": 40.0,
        "fuel_gas_nm3_d": 1200.0,
        "vs_degraded_kg_d": 900.0, "biogas_m3_d": 810.0,
    }
    out_full = carbon_summary_of({"design": base}, lib_all)["design"]
    f3 = 10.0 * 0.016 * 1.5714286 * 273.0
    f4 = 4.0 * 0.005 * 1.5714286 * 273.0
    f5 = 40.0 * 0.6 * 0.03 * 27.0
    assert out_full["carbon_direct_kgco2e_d"] == pytest.approx(
        f3 + f4 + f5 + 2594.64 + 14.01516 + 3208.1832, rel=1e-9)


def test_t11_digest_band_invariant_positive() -> None:
    """T11 带界恒正不变式（门一 k1-W2 处置）：r_biogas 声明带上沿 1.1
    m³/kgVS（xiaohua biogas_rate_band.max）+追认定值——净 CH₄ 严格>0
    （无 clamp 语义的前置不变式锚：0.48−1.1×0.54×0.716=0.0547 kg/kgVS
    最小边际；越带负值=逃逸口径显式呈裁，非静默量）。"""
    band_max_lib = _StubCoefficients({
        **_B6B_VALUES,
        # r_biogas 上沿隐含：v_biogas=w_vs_deg×1.1（带内最不利回收比）
    })
    out = carbon_summary_of(
        {"design": {"vs_degraded_kg_d": 1000.0, "biogas_m3_d": 1100.0}},
        band_max_lib)["design"]
    net = out["carbon_direct_ch4_digest_kgco2e_d"] / 27.0  # 还 kgCH4/d
    assert net == pytest.approx(
        1000.0 * 0.6 * 0.8 - 1100.0 * 0.6 * 0.9 * 0.716, rel=1e-12)
    assert net > 0.0
