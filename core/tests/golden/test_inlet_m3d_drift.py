"""inlet-m3d 批零漂移守卫（2026-10-02）：进水参数面 m³/s→m³/d 统一的构造性证明。

输入:  golden_data/municipal_34760{,_loop,_recycle}（v4 形——inlet 34760.7 m³/d）
输出:  三面机器锚——①绑定点单源换算（内部出流==parse(34760.7,"m3/d")，
       零手写 86400；与旧字面量 0.4023229167 尾差上界=ulp 漂幅度）②浓度面
       逐键位串恒等（六指标×全工况×三案 ==expected 期望值——常数去除率
       模型 n-不变性质：参数面单位换轴不触内部 WaterFlow m³/s 契约的
       构造性证明，approx 容差外再钉 == 位串级）③流量比例面 ulp 漂上界
       （批前冻结值表——漂幅度恰=新旧字面量尾差，≤9.02e-11 rel（实录
       极大，上界 1e-10 裕度约 9%），实测录档非零且上界钳制）。

漂移面全景实录（重录前核查）见批档 .workflow/inlet-m3d-20261002/
drift-face-prerecord.txt——401 锚漂清单（405 行含 4 案标题行；恰流量
比例面+serialize）。浓度零漂面=base 案六指标×全工况位串零漂（HEAD
对拍）；loop/recycle 两案 SS×design/avg 两键随批重录——回流混合
（junction 流量权重）ulp 渗透所致，prerecord 实录在档
（drift-face-prerecord.txt loop/recycle 段）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.golden

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_CASES = ("municipal_34760", "municipal_34760_loop", "municipal_34760_recycle")
_TERMINAL = "municipal_bashi_jiliangcao"
# 浓度面六指标（常数去除率模型输出——n-不变族）
_CONCENTRATION_KEYS = ("BOD5", "CODCR", "SS", "NH3N", "TN", "TP")
# 批前冻结值表（inlet-m3d 批前 HEAD 实录——ulp 漂上界锚的对照源；
# 值=drift-face-prerecord.txt 期望面逐键誊录）
_PRE_M3D_FROZEN: dict[tuple[str, str], float] = {
    ("municipal_34760", "summary.design.influent_flow_m3_d"): 34760.700002879996,
    ("municipal_34760", "dims.municipal_aao.v_total"): 17862.22020522992,
    ("municipal_34760", "m3.estimate_total"): 19415730.31428396,
    ("municipal_34760_loop", "dims.rj_sup.q_recycle"): 297.54175314820674,
    ("municipal_34760_loop", "dims.sludge_hebing.q_total"): 427.3594991344455,
    ("municipal_34760_recycle", "dims.municipal_aao.v_total"): 18064.347422268198,
}
# ulp 漂上界（实录极大漂幅度 9.02e-11 rel——prerecord loop 段 power_pump
# 实锚；上界钳 1e-10 裕度约 9%，不放宽至工程意义量级；漂非零=换轴真实
# 发生的实录锚）
_ULP_DRIFT_BOUND = 1e-10


def _run(golden_data_dir: Path, case: str, expected: dict[str, Any]) -> Any:
    """golden 案例正门实跑（golden e2e 同口径装配——单案单跑）。"""
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    generated = expected["generated"]
    env = RunEnv(
        engine_version=generated["engine_version"],
        data_version=generated["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_REPO_DATA),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    project = load_project(golden_data_dir / case / "input_project.json")
    conditions = build_condition_set(expected["checked_units"])
    return run_full_calc(project, conditions, env).plant


def _expected(golden_data_dir: Path, case: str) -> dict[str, Any]:
    return json.loads(
        (golden_data_dir / case / "expected_summary.json").read_text(encoding="utf-8")
    )


def test_binding_single_source_pint_conversion(golden_data_dir: Path) -> None:
    """①绑定点单源换算锚：inlet 出流==parse(34760.7,"m3/d")（pint 唯一真源
    ——零手写 86400 系数）；与旧字面量 0.4023229167 的尾差=ulp 漂幅度
    （3.33e-11 abs 上界锚——勘察实证非零，漂面实录承接）。"""
    from waterprint.contracts.quantity import DimKey, parse

    expected = _expected(golden_data_dir, "municipal_34760")
    plant = _run(golden_data_dir, "municipal_34760", expected)
    q_internal = plant.conditions["design"]["inlet"].outflows[
        "inlet.out.q_avg_daily"
    ]
    assert q_internal == parse(34760.7, "m3/d", DimKey.FLOW)  # 单源换算恒等
    assert abs(q_internal - 0.4023229167) < 4e-11  # ulp 漂幅度上界（实测 3.33e-11）
    assert q_internal != 0.4023229167  # 漂真实发生（有损舍入尾差实录）


def test_concentration_faces_bitwise_stable(golden_data_dir: Path) -> None:
    """②浓度面位串恒等：三案全工况六指标 ==expected 期望值（位串级——
    base 案浓度锚未重录（位串恒等故无需）；loop/recycle 两案 SS 锚已随批
    重录后位串锚定）。"""
    for case in _CASES:
        expected = _expected(golden_data_dir, case)
        plant = _run(golden_data_dir, case, expected)
        for condition_key, fields in expected["effluent"].items():
            snapshot = plant.conditions[condition_key][_TERMINAL]
            for indicator in _CONCENTRATION_KEYS:
                assert indicator in fields, (case, condition_key, indicator)
                quality_key = f"{_TERMINAL}.out.{indicator}"
                assert snapshot.outqualities[quality_key] == fields[indicator]["value"], (
                    case, condition_key, indicator
                )


def test_flow_proportional_faces_ulp_bounded(golden_data_dir: Path) -> None:
    """③流量比例面 ulp 漂上界锚：批前冻结值表对照——漂非零且 ≤1e-10 rel
    （新值更精确：34760.7/86400 全精度经 pint 直算 vs 旧 10 位定点舍入）。"""
    for case in _CASES:
        expected = _expected(golden_data_dir, case)
        plant = _run(golden_data_dir, case, expected)
        dims = plant.conditions["design"]
        for (frozen_case, key), frozen in _PRE_M3D_FROZEN.items():
            if frozen_case != case:
                continue
            if key.startswith("summary."):
                actual = plant.summary["design"][key.split(".", 2)[2]]
            elif key.startswith("dims."):
                _, unit_id, field = key.split(".", 2)
                actual = dims[unit_id].dims[field]
            else:  # m3.estimate_total——概算三正门直调（golden e2e 同款）
                from waterprint.cost.estimate import build_estimate, load_fee_rules
                from waterprint.cost.prices import load_prices
                from waterprint.cost.takeoff import takeoff_quantities

                prices = Path(__file__).resolve().parents[3] / "data/unit_prices"
                book = load_prices(prices)
                fees = load_fee_rules(prices / "field_mapping.yaml", book)
                actual = build_estimate(
                    takeoff_quantities(plant, "design", price_book=book), book, fees
                ).grand_total
            assert actual != frozen, (case, key)  # 漂真实发生（实录锚）
            assert abs(actual - frozen) / abs(frozen) <= _ULP_DRIFT_BOUND, (
                case, key, actual, frozen
            )
