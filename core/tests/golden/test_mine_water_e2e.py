"""矿井水 golden 端到端（43,836 m³/d，地表水 III 类；M3 验收）。

输入:  golden_data/mine_43836/{input_project.json, expected_summary.json}
输出:  全流程对照断言（GOLDEN2 段一激活，2026-08-28——原骨架 raise
       "M3 接线断言：run_full_calc 跑通 43,836 案例并逐项对照（含污泥
       线回路收敛）——不得删除或放宽"语义忠实承载：①正门跑
       input_project（2 工况全）②逐工况逐项终水对照（五指标面
       ——BOD5RM：BOD5 不建）③主尺寸逐项对照（8 单元空字典=旧源
       kuangjing.ddesign.json 默认）④summary 真值五指标对照⑤工况集
       2+0 恰等索引⑥serialize 双跑字节同；MSLUDGE2 段二升版 v2
       2026-08-28：污泥线承诺面兑现——hebing→nongsuo→tuoshui 三节点
       参数注入链（SLUDGE 图源链头+两链边，"含污泥线"以矿井三股排泥
       参数注入承载；真边环路归 GOLDEN4）+⑦std.gb3838_iii 实绑五键
       ⑧m3 双锚补录（概算总数 cost 三正门直调+总泥量）⑨DS 守恒链
       （hebing ds_total=三股注入干基之和）——旧 30 锚零扰动）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3 验收 = 矿井水线 8 单元全流程出全套对照；期望值来源
# docs/norms 手算对照与旧系统结果（差异逐条解释，由领域专家签字后
# 录入 golden_data——实现者不得自编）。v1=主线 8 节点（GOLDEN2 D4）；
# v2=+污泥线三节点参数注入+std 实绑+m3 双锚（MSLUDGE2——手算表真源
# docs/norms/mine_water_sludge_line.md，§21-③ 已追认）。
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
        not (Path(__file__).parent / "golden_data" / "mine_43836" / "expected_summary.json").is_file(),
        reason="golden 数据未整理（M3：43,836 m³/d 案例由领域专家录入）",
    ),
]

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_REPO_PRICES = Path(__file__).resolve().parents[3] / "data" / "unit_prices"
_TERMINAL = "mine_water_ziwai"
# 五指标面（BOD5RM——Ruling BOD5-不建：矿井水 B/C=0.025 无生化性）
_INDICATORS = frozenset({"SS", "CODCR", "NH3N", "TN", "TP"})
# std.gb3838_iii 五键限值（GB 3838-2002 表 1 III 类——coefficients 1.1.0
# std 键族，表 1 无 SS 项故五键；I1 从严口径=案例出水目标，绑定面透传
# calc 零消费——断言面=绑定值在 coefficients 键集+五键逐值）
_STD_PREFIX = "std.gb3838_iii"
_STD_LIMITS = {"bod5": 4.0, "cod": 20.0, "nh3n": 1.0, "tn": 1.0, "tp": 0.2}


def _std_binding_anchored(project: Any, lib: Any) -> None:
    """⑦ std 实绑断言（v2）：binding 形态+前缀键集钳制+五键逐值。

    standard_binding 只入 content_hash（design 七字段之一）、calc 零消费
    （透传字段）——消费面断言=绑定键值在 coefficients 库内可解析且五键
    逐值等于 GB 3838 III 类限值（1.1.0 std 键族，GOLDEN3 D3 补建）。"""
    binding = project.design.standard_binding
    assert binding == {"effluent": _STD_PREFIX}, "std 绑定形态（I1 从严）"
    assert lib.keys(_STD_PREFIX) == tuple(
        f"{_STD_PREFIX}.{suffix}" for suffix in sorted(_STD_LIMITS)
    ), "std.gb3838_iii 键集钳制（恰五键——表 1 无 SS 项）"
    for suffix, limit in _STD_LIMITS.items():
        key = f"{_STD_PREFIX}.{suffix}"
        assert lib.get(key).value == pytest.approx(
            limit, rel=1e-12, abs=1e-12
        ), f"std 限值 {key}"


def _m3_deferred_values(plant: Any, expected: dict[str, Any]) -> None:
    """⑧ m3 双锚（v2 补录）：概算总数+全厂总泥量实跑对照。

    estimate_total=全图（11 节点）design 档工程量→概算——app 未接 cost
    属既定架构（result_schema"愿景未落"注记），测试直调 cost 三正门
    （GOLDEN2 市政先例 tests/golden/test_municipal_e2e.py）；grand_total
    逐级自洽（subtotal+reserve_subtotal+Σtax=grand_total）先证后对照。
    total_sludge=hebing ds_total（干基 kg/d 主口径）；湿基 q_total 以
    design_dims["sludge_hebing"]["q_total"] 锚承载双断言。"""
    from waterprint.cost.estimate import build_estimate, load_fee_rules
    from waterprint.cost.prices import load_prices
    from waterprint.cost.takeoff import takeoff_quantities

    book = load_prices(_REPO_PRICES)
    fees = load_fee_rules(_REPO_PRICES / "field_mapping.yaml", book)
    items = takeoff_quantities(plant, "design", price_book=book)
    sheet = build_estimate(items, book, fees)
    assert (sheet.subtotal + sheet.reserve_subtotal
            + sum(line.amount for line in sheet.tax)) == sheet.grand_total
    m3 = expected["m3_deferred"]
    for key in ("estimate_total", "total_sludge"):
        assert set(m3[key]) == {"value", "source", "abs", "rel"}, key
    estimate = m3["estimate_total"]
    assert sheet.grand_total == pytest.approx(
        estimate["value"], rel=estimate["rel"], abs=estimate["abs"]
    ), "m3_deferred.estimate_total（11 节点 design 档 grand_total）"
    sludge = m3["total_sludge"]
    hebing = plant.conditions["design"]["sludge_hebing"].dims
    assert hebing["ds_total"] == pytest.approx(
        sludge["value"], rel=sludge["rel"], abs=sludge["abs"]
    ), "m3_deferred.total_sludge（hebing ds_total 干基 kg/d 主口径）"
    wet = expected["design_dims"]["sludge_hebing"]["q_total"]
    assert hebing["q_total"] == pytest.approx(
        wet["value"], rel=wet["rel"], abs=wet["abs"]
    ), "hebing q_total（湿基 m³/d——m3 双断言第二锚）"


def _effluent_and_summary_anchor(plant: Any, expected: dict[str, Any], keys: list[str]) -> None:
    """②/④ 终水与 summary 真值对照（D10 注入口径——同源互证）。

    键集钳制：每工况恰等五指标面（BOD5 缺席合法——BOD5RM），防删块
    静默绿；双容差按 expected 内标注——不放宽。"""
    for condition_key, fields in expected["effluent"].items():
        assert set(fields) == _INDICATORS, f"五指标面 {condition_key}"
        snapshot = plant.conditions[condition_key][_TERMINAL]
        for indicator, item in fields.items():
            actual = snapshot.outqualities[f"{_TERMINAL}.out.{indicator}"]
            assert actual == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"终水 {condition_key}.{indicator}"
        summary_view = plant.summary[condition_key]
        assert set(summary_view) == set(fields), f"summary 键集 {condition_key}"
        for indicator, item in fields.items():
            assert summary_view[indicator] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"summary {condition_key}.{indicator}"
    assert set(expected["effluent"]) == set(keys)  # 工况块恰等 2+0 键集


def test_mine_water_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：矿井水线 11 节点 run_full_calc 2 工况终水逐项+主尺寸对照（双容差禁放宽）。"""
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set
    from waterprint.contracts.result_schema import serialize
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    case_dir = golden_data_dir / "mine_43836"
    project = load_project(case_dir / "input_project.json")
    expected = json.loads(
        (case_dir / "expected_summary.json").read_text(encoding="utf-8")
    )

    # ⑤ 工况集 2+0 索引（ADR-007：八包 condition_mappings 全空 → k=0；
    # 污泥三包 condition_mappings 亦空——v2 后仍 2+0）
    conditions = build_condition_set(expected["checked_units"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == expected["condition_keys"] == ["design", "avg"]
    assert len(keys) == 2 + len(expected["checked_units"]) == 2

    # ① 正门实跑（env 口径=expected.generated 实录：server 正门版本串）
    lib = load_coefficients(_REPO_DATA)
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],
        data_version=expected["generated"]["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    plant = run_full_calc(project, conditions, env).plant
    assert set(plant.conditions) == set(keys)  # 全 2 工况各出整图结果
    assert plant.repro.design_hash == project.metadata.content_hash  # 结果绑定输入
    assert set(plant.summary) == set(keys)  # D10 全工况注入口径

    # ⑦ std 实绑断言（v2——见 helper 规格；lib 与正门同库）
    _std_binding_anchored(project, lib)

    # ② 逐工况逐项终水对照+④ summary 真值五指标对照（helper——见规格）
    _effluent_and_summary_anchor(plant, expected, keys)

    # ③ design 档主尺寸逐项对照（每 unit 主控项，容差同上）
    # 单元覆盖钳制：design_dims 恰覆盖十一节点全图——无 inlet 排除
    # （mine_water_input 是真单元，其 dims ≥1 键收录如 q_design）；v2
    # 污泥三单元随节点增自动入钳制面（键集=set(nodes) 只增）
    assert set(expected["design_dims"]) == set(project.design.nodes)
    for unit_id, fields in expected["design_dims"].items():
        dims = plant.conditions["design"][unit_id].dims
        for field, item in fields.items():
            assert dims[field] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"主尺寸 {unit_id}.{field}"

    # ⑧ m3 双锚（v2 补录——概算总数 cost 三正门直调+总泥量 hebing ds_total）
    _m3_deferred_values(plant, expected)

    # ⑨ DS 守恒链（v2）：hebing ds_total=三股注入干基之和（HB-F4 镜像
    # ——contracts.sludge.mix R1；注入面值即 MS-F1~F3 链级衔接预计算值）
    injected = project.design.nodes["sludge_hebing"]
    hebing_dims = plant.conditions["design"]["sludge_hebing"].dims
    assert hebing_dims["ds_total"] == pytest.approx(
        injected["ds_primary"] + injected["ds_bio"] + injected["ds_chem"],
        rel=1e-12,
        abs=1e-12,
    ), "DS 守恒链：hebing ds_total=三股 ds 之和"

    # ⑥ serialize 双跑字节同（确定性 R3——generated 实录机器锚定；
    # v2 三元组随 11 节点图重录）
    first = serialize(run_full_calc(project, conditions, env).plant)
    second = serialize(run_full_calc(project, conditions, env).plant)
    assert first == second
    assert len(first) == expected["generated"]["serialize_bytes"]
    assert hashlib.sha256(first).hexdigest()[:16] == (
        expected["generated"]["serialize_sha256_head"]
    )
