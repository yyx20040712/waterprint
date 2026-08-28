"""矿井水 golden 端到端（43,836 m³/d，地表水 III 类；M3 验收）。

输入:  golden_data/mine_43836/{input_project.json, expected_summary.json}
输出:  全流程对照断言（GOLDEN2 段一激活，2026-08-28——原骨架 raise
       "M3 接线断言：run_full_calc 跑通 43,836 案例并逐项对照（含污泥
       线回路收敛）——不得删除或放宽"语义忠实承载：①正门跑
       input_project（2 工况全）②逐工况逐项终水对照（五指标面
       ——BOD5RM：BOD5 不建）③主尺寸逐项对照（8 单元空字典=旧源
       kuangjing.ddesign.json 默认）④summary 真值五指标对照⑤工况集
       2+0 恰等索引⑥serialize 双跑字节同；"含污泥线回路收敛"面随
       v2 升版承载——矿井污泥链手算表未备，README 承诺面 v1 已改写
       记档）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：M3 验收 = 矿井水线 8 单元全流程出全套对照；期望值来源
# docs/norms 手算对照与旧系统结果（差异逐条解释，由领域专家签字后
# 录入 golden_data——实现者不得自编）。v1=主线 8 节点（GOLDEN2 D4：
# 无污泥线/无回流/无 m3_deferred 键）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.golden,
    pytest.mark.skipif(
        not (Path(__file__).parent / "golden_data" / "mine_43836" / "expected_summary.json").is_file(),
        reason="golden 数据未整理（M3：43,836 m³/d 案例由领域专家录入）",
    ),
]

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_TERMINAL = "mine_water_ziwai"
# 五指标面（BOD5RM——Ruling BOD5-不建：矿井水 B/C=0.025 无生化性）
_INDICATORS = frozenset({"SS", "CODCR", "NH3N", "TN", "TP"})


def test_mine_water_golden_end_to_end(golden_data_dir: Path) -> None:
    """端到端：矿井水线 8 单元 run_full_calc 2 工况终水逐项+主尺寸对照（双容差禁放宽）。"""
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

    # ⑤ 工况集 2+0 索引（ADR-007：八包 condition_mappings 全空 → k=0）
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

    # ② 逐工况逐项终水对照（双容差按 expected 内标注——不放宽）
    # 键集钳制：每工况恰等五指标面（BOD5 缺席合法——BOD5RM），防删块静默绿
    assert set(expected["effluent"]) == set(keys)
    for condition_key, fields in expected["effluent"].items():
        assert set(fields) == _INDICATORS, f"五指标面 {condition_key}"
        snapshot = plant.conditions[condition_key][_TERMINAL]
        for indicator, item in fields.items():
            actual = snapshot.outqualities[f"{_TERMINAL}.out.{indicator}"]
            assert actual == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"终水 {condition_key}.{indicator}"

    # ③ design 档主尺寸逐项对照（每 unit 主控项，容差同上）
    # 单元覆盖钳制：design_dims 恰覆盖八节点全图——无 inlet 排除
    # （mine_water_input 是真单元，其 dims ≥1 键收录如 q_design）
    assert set(expected["design_dims"]) == set(project.design.nodes)
    for unit_id, fields in expected["design_dims"].items():
        dims = plant.conditions["design"][unit_id].dims
        for field, item in fields.items():
            assert dims[field] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"主尺寸 {unit_id}.{field}"

    # ④ summary 真值五指标对照（D10 注入口径——与终水同源互证）
    for condition_key, fields in expected["effluent"].items():
        summary_view = plant.summary[condition_key]
        assert set(summary_view) == set(fields), f"summary 键集 {condition_key}"
        for indicator, item in fields.items():
            assert summary_view[indicator] == pytest.approx(
                item["value"], rel=item["rel"], abs=item["abs"]
            ), f"summary {condition_key}.{indicator}"

    # ⑥ serialize 双跑字节同（确定性 R3——generated 实录机器锚定）
    first = serialize(run_full_calc(project, conditions, env).plant)
    second = serialize(run_full_calc(project, conditions, env).plant)
    assert first == second
    assert len(first) == expected["generated"]["serialize_bytes"]
    assert hashlib.sha256(first).hexdigest()[:16] == (
        expected["generated"]["serialize_sha256_head"]
    )
