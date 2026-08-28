"""市政回流 golden 端到端（34,760 m³/d+上清液/滤液回流；GOLDEN3 批）。

输入:  golden_data/municipal_34760_recycle/{input_project,expected_summary}.json
输出:  21 节点回流图全流程对照断言（D5~D7：主线 19 节点+rj_sup/rj_filtrate
       两 recycle_junction 转换+4 条跨子图 forward 回流边——v1 前向叠加
       口径 D0；5 工况终水逐项+20 单元主尺寸+水量平衡守恒+rj dims
       投影对照+m3 双锚+serialize 双跑——2026-08-28 GOLDEN3 起草）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：GOLDEN3 D7 断言族照市政先例（test_municipal_e2e）+回流专属三面：
#   ①水量平衡（汇流守恒——business-logic §3）：bashi 出流 q_avg_daily
#     == inlet + nongsuo q_sup/86400 + tuoshui q_filtrate/86400（逐工况）；
#   ②rj dims 投影对照：rj_sup/rj_filtrate 的 q_recycle/ss_recycle 与
#     nongsuo/tuoshui dims 的 q_sup/ds_sup、q_filtrate/ds_filtrate 齐次；
#   ③m3 断言（cost 三正门直调+grand_total 逐级自洽+hebing 双锚）。
#   期望值真源=app 正门一次实跑落盘（禁手打——生成脚本实录见实现报告）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (
            Path(__file__).parent
            / "golden_data"
            / "municipal_34760_recycle"
            / "expected_summary.json"
        ).is_file(),
        reason="golden 数据未整理（GOLDEN3：回流案例由领域专家录入）",
    ),
]

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_REPO_PRICES = Path(__file__).resolve().parents[3] / "data" / "unit_prices"
_TERMINAL = "municipal_bashi_jiliangcao"
_SECS_PER_DAY = 86400.0


def _conditions(expected: dict[str, Any]):
    """工况集正门（checked_units 承载于 expected——市政先例 §2.2）。"""
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set(expected["checked_units"])


def _front_door(case_dir: Path, expected: dict[str, Any]):
    """正门三件：load_project → RunEnv → run_full_calc（env 口径=generated 实录）。"""
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    project = load_project(case_dir / "input_project.json")
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_REPO_DATA),
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    return project, env, run_full_calc(project, _conditions(expected), env)


def _assert_effluent_and_dims(
    plant: Any, project: Any, expected: dict[str, Any], keys: list[str]
) -> None:
    """② 逐工况终水+③ design 主尺寸（键集钳制防删块静默绿）+summary 真值。"""
    assert set(expected["effluent"]) == set(keys)
    for condition_key, fields in expected["effluent"].items():
        snapshot = plant.conditions[condition_key][_TERMINAL]
        for indicator, item in fields.items():
            actual = snapshot.outqualities[f"{_TERMINAL}.out.{indicator}"]
            assert actual == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"终水 {condition_key}.{indicator}"
    assert set(expected["design_dims"]) == set(project.design.nodes) - {"inlet"}
    for unit_id, fields in expected["design_dims"].items():
        dims = plant.conditions["design"][unit_id].dims
        for field, item in fields.items():
            assert dims[field] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"主尺寸 {unit_id}.{field}"
    summary_view = plant.summary["design"]  # app 层注入真值（市政 e2e 同款）
    assert set(summary_view) == set(expected["effluent"]["design"])
    for indicator, item in expected["effluent"]["design"].items():
        assert summary_view[indicator] == pytest.approx(
            item["value"], rel=item["rel"], abs=item["abs"]
        ), f"summary design.{indicator}"


def _assert_water_balance_and_rj(plant: Any, keys: list[str]) -> None:
    """回流专属①②：水量平衡守恒（逐工况）+rj 两节点 dims 投影对照。"""
    design = plant.conditions["design"]
    inlet_q = design["inlet"].outflows["inlet.out.q_avg_daily"]
    q_sup = design["sludge_nongsuo"].dims["q_sup"]
    ds_sup = design["sludge_nongsuo"].dims["ds_sup"]
    q_filtrate = design["sludge_tuoshui"].dims["q_filtrate"]
    ds_filtrate = design["sludge_tuoshui"].dims["ds_filtrate"]
    balanced = inlet_q + q_sup / _SECS_PER_DAY + q_filtrate / _SECS_PER_DAY
    for condition_key in keys:
        q_bashi = plant.conditions[condition_key][_TERMINAL].outflows[
            f"{_TERMINAL}.out.q_avg_daily"
        ]
        assert q_bashi == pytest.approx(
            balanced, rel=1e-12, abs=1e-15
        ), f"水量平衡（汇流守恒）{condition_key}：{q_bashi!r} != {balanced!r}"
    rj_sup = design["rj_sup"].dims
    rj_filtrate = design["rj_filtrate"].dims
    assert rj_sup["q_recycle"] == pytest.approx(q_sup, rel=1e-12)
    assert rj_sup["ss_recycle"] == pytest.approx(
        ds_sup / q_sup * 1000, rel=1e-12
    ), "rj_sup SS 投影=ds_sup/q_sup×1000"
    assert rj_filtrate["q_recycle"] == pytest.approx(q_filtrate, rel=1e-12)
    assert rj_filtrate["ss_recycle"] == pytest.approx(
        ds_filtrate / q_filtrate * 1000, rel=1e-12
    ), "rj_filtrate SS 投影=ds_filtrate/q_filtrate×1000"


def _assert_m3(plant: Any, expected: dict[str, Any]) -> None:
    """回流专属③：m3 断言（cost 三正门直调+逐级自洽+hebing 双锚）。"""
    from waterprint.cost.estimate import build_estimate, load_fee_rules
    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import takeoff_quantities

    book = load_prices(_REPO_PRICES)
    fees = load_fee_rules(_REPO_PRICES / "field_mapping.yaml", book)
    items = takeoff_quantities(plant, "design", price_book=book)
    sheet = build_estimate(items, book, fees)
    assert (
        sheet.subtotal + sheet.reserve_subtotal + sum(line.amount for line in sheet.tax)
        == sheet.grand_total
    )
    m3 = expected["m3_deferred"]
    for key in ("estimate_total", "total_sludge"):
        assert set(m3[key]) == {"value", "source", "abs", "rel"}, key
    estimate = m3["estimate_total"]
    assert sheet.grand_total == pytest.approx(
        estimate["value"], rel=estimate["rel"], abs=estimate["abs"]
    ), "m3_deferred.estimate_total（21 节点回流图 design 档 grand_total）"
    hebing = plant.conditions["design"]["sludge_hebing"].dims
    assert hebing["ds_total"] == pytest.approx(
        m3["total_sludge"]["value"],
        rel=m3["total_sludge"]["rel"],
        abs=m3["total_sludge"]["abs"],
    ), "m3_deferred.total_sludge（hebing ds_total——回流不改泥量主线）"
    wet = expected["design_dims"]["sludge_hebing"]["q_total"]
    assert hebing["q_total"] == pytest.approx(
        wet["value"], rel=wet["rel"], abs=wet["abs"]
    ), "hebing q_total（湿基 m³/d——m3 双断言第二锚）"


def test_municipal_recycle_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：回流图 5 工况终水+20 单元主尺寸+水量平衡+rj 投影+m3+serialize。"""
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet
    from waterprint.contracts.result_schema import serialize

    case_dir = golden_data_dir / "municipal_34760_recycle"
    expected = json.loads(
        (case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )
    keys = [ConditionSet.key(c) for c in _conditions(expected).iter_all()]
    assert keys == expected["condition_keys"]
    assert len(keys) == 2 + len(expected["checked_units"]) == 5  # ⑤ 工况 2+k

    project, env, bundle = _front_door(case_dir, expected)
    plant = bundle.plant
    assert set(plant.conditions) == set(keys)  # ① 正门三断言
    assert plant.repro.design_hash == project.metadata.content_hash
    assert set(plant.summary) == set(keys)

    _assert_effluent_and_dims(plant, project, expected, keys)
    _assert_water_balance_and_rj(plant, keys)
    _assert_m3(plant, expected)

    first = serialize(run_full_calc(project, _conditions(expected), env).plant)
    second = serialize(run_full_calc(project, _conditions(expected), env).plant)
    assert first == second  # ⑥ serialize 双跑字节同（确定性 R3）
    assert len(first) == expected["generated"]["serialize_bytes"]
    assert hashlib.sha256(first).hexdigest()[:16] == (
        expected["generated"]["serialize_sha256_head"]
    )
