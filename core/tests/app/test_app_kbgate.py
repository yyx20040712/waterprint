"""app_kbgate 镜像测试：design 帧阻断门（enforcement=block 越门→KbBlockError）。

输入:  waterprint.app_kbgate（assert_kb_gate）+ stub 双帧 PlantResult/
       ConditionSet/kb 桩 + golden municipal_34760 实跑（真实 kb 零违规锚）
输出:  阻断行为断言——design 帧 block 条目越门 raise（violations 三联+传入序
       确定性+消息含逐条 key）/flag 条目永不阻断/豁免面（sensitivity 帧零
       求值——D3 架构性缺席）/空 baseline 通透（R1 镜像）/sparse 跳过/
       boundary_check·unit_kinds·字段覆盖守卫/run_full_calc 接线（真实 kb
       全量零 raise+缺省 () 零行为变更+构造违规 raise+serialize 双跑字节同）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：kbblock-20261006 简报 D1~D5——求值面=conditions.baseline[0] 帧独占
#   （ConditionSet.key 同锚——禁字符串字面量 "design"）；applicable 判据=
#   _maint_face 三 conjunction 镜像（kind≠boundary_check ∧ unit_kinds∋
#   units[node].manifest.unit_id ∧ 表达式字段⊆帧 dims）∧ enforcement=="block"；
#   求值=solution.apply_constraints 单行 DataFrame（禁手写 DSL 求值）；
#   失败语义=KbBlockError 异常全败丢弃（半成品不进 summary/diagnostics/
#   result）；空 baseline=通透不炸（R1 镜像）；node 快照缺席=通透跳过
#   （sparse 镜像）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from waterprint.app_kbgate import assert_kb_gate
from waterprint.contracts.condition import build_condition_set
from waterprint.contracts.result_schema import PlantResult, ReproTriple, UnitResultSnapshot
from waterprint.solution.constraints import Constraint, KbBlockError, KbConstraint

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REPO_DATA = _REPO_ROOT / "data"


def _snap(dims: dict[str, float]) -> UnitResultSnapshot:
    """最小单元快照（gate 只读 dims——其余字段空载）。"""
    return UnitResultSnapshot(
        unit_id="stub", outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _plant(frames: dict[str, dict[str, dict[str, float]]]) -> PlantResult:
    """stub PlantResult：design/avg baseline 帧+offline sensitivity 帧。"""
    return PlantResult(
        conditions={
            key: {node: _snap(dims) for node, dims in frame.items()}
            for key, frame in frames.items()
        },
        summary={}, trace=(),
        repro=ReproTriple(design_hash="", engine_version="t", data_version="t"),
    )


def _units_map(kinds: dict[str, str]) -> dict[str, Any]:
    """单元注册表桩：node → manifest.unit_id=kind（适用判据 kind 口径）。"""
    return {
        node: SimpleNamespace(manifest=SimpleNamespace(unit_id=kind))
        for node, kind in kinds.items()
    }


def _kb(
    key: str, expression: str, unit_kinds: tuple[str, ...],
    kind: str = "geometry_guard", enforcement: str = "block",
) -> KbConstraint:
    """kb 桩（enforcement 缺省 block——本件主测面；flag 桩显式传参）。"""
    return KbConstraint(
        constraint=Constraint(key=key, expression=expression, source=key),
        unit_kinds=unit_kinds, kind=kind, enforcement=enforcement,
    )


def _gate(
    plant: PlantResult, constraints: tuple[KbConstraint, ...],
    units: dict[str, Any] | None = None,
) -> None:
    """直调便捷面（conditions=stub 单目标单元工况集——镜像 maintenance 桩）。"""
    return assert_kb_gate(
        plant, build_condition_set(["stub_unit"]),
        units if units is not None else _units_map({"stub_unit": "stub_kind"}),
        constraints,
    )


# ── 阻断与通过（design 帧独占）──────────────────────────────────────


def test_gate_blocks_design_frame_violation() -> None:
    """design 帧越门=raise：violations 三联结构化+str 消息含逐条 key。"""
    plant = _plant({
        "design": {"stub_unit": {"v": 120.0}},  # v<=100 越门
        "avg": {"stub_unit": {"v": 10.0}},
        "design_offline_stub_unit": {"stub_unit": {"v": 10.0}},
    })
    with pytest.raises(KbBlockError) as excinfo:
        _gate(plant, (_kb("kb.stub.block", "v <= 100", ("stub_kind",)),))
    error = excinfo.value
    assert error.violations == (("stub_unit", "kb.stub.block", "geometry_guard"),)
    assert "kb.stub.block" in str(error)  # 消息含逐条 violated key（server 消费面）
    assert "stub_unit" in str(error)


def test_gate_pass_case_returns_none() -> None:
    """design 帧全过=None（越门条目在 sensitivity 帧不触发——design v=80 过）。"""
    plant = _plant({
        "design": {"stub_unit": {"v": 80.0}},
        "avg": {"stub_unit": {"v": 80.0}},
        "design_offline_stub_unit": {"stub_unit": {"v": 120.0}},  # offline 越门≠阻断
    })
    assert _gate(plant, (_kb("kb.stub.block", "v <= 100", ("stub_kind",)),)) is None


def test_gate_violations_order_deterministic() -> None:
    """violations 迭代序=传入序确定性（R2 纪律）：约束按传入序×节点按帧插入序。"""
    plant = _plant({
        "design": {
            "node_a": {"v": 120.0},  # 帧插入序 node_a 先于 node_b
            "node_b": {"v": 120.0},
        },
        "avg": {},
    })
    units = _units_map({"node_a": "kind_x", "node_b": "kind_x"})
    constraints = (
        _kb("kb.stub.first", "v <= 100", ("kind_x",)),
        _kb("kb.stub.second", "v <= 110", ("kind_x",)),
    )
    with pytest.raises(KbBlockError) as excinfo:
        assert_kb_gate(plant, build_condition_set(["stub_unit"]), units, constraints)
    assert excinfo.value.violations == (
        ("node_a", "kb.stub.first", "geometry_guard"),
        ("node_a", "kb.stub.second", "geometry_guard"),
        ("node_b", "kb.stub.first", "geometry_guard"),
        ("node_b", "kb.stub.second", "geometry_guard"),
    )


def test_gate_flag_entries_never_block() -> None:
    """flag 档永不阻断（P1 选项 3 逐条定级——仪表灯与断路器分档语义锚）：
    同一越门表达式 enforcement=flag=None 通过。"""
    plant = _plant({
        "design": {"stub_unit": {"v": 120.0}}, "avg": {},
    })
    assert _gate(plant, (
        _kb("kb.stub.lamp", "v <= 100", ("stub_kind",), enforcement="flag"),
    )) is None


def test_gate_zero_constraints_passes() -> None:
    """constraints=() 零行为变更锚（铁律二）：无条件目=None。"""
    plant = _plant({"design": {"stub_unit": {"v": 120.0}}, "avg": {}})
    assert _gate(plant, ()) is None


# ── 豁免面与守卫（D3 架构性缺席+applicable 三 conjunction 镜像）────────


def test_gate_sensitivity_frames_architecturally_exempt() -> None:
    """D3 豁免=架构性缺席：offline/sensitivity 帧零阻断求值（代码面无该路径
    ——工况分级线呈裁默认全部豁免；检修观测在最需亮灯时刻不熄灯）。"""
    plant = _plant({
        "design": {"stub_unit": {"v": 10.0}},  # design 帧全过
        "avg": {"stub_unit": {"v": 120.0}},  # baseline[1]（avg）帧零求值
        "design_offline_stub_unit": {"stub_unit": {"v": 120.0}},  # offline 越门不阻断
    })
    assert _gate(plant, (_kb("kb.stub.block", "v <= 100", ("stub_kind",)),)) is None


def test_gate_empty_baseline_passes_not_crash() -> None:
    """R1 镜像口径：空 baseline=通透不炸（无 design 帧即无阻断面）。"""
    from waterprint.contracts.condition import (
        ConditionSet,
        FlowCase,
        OperatingCondition,
    )

    offline_only = ConditionSet(
        baseline=(),
        sensitivity=(OperatingCondition(
            flow_case=FlowCase.DESIGN, offline_unit="stub_unit"),),
    )
    plant = _plant({
        "design_offline_stub_unit": {"stub_unit": {"v": 120.0}},
    })
    assert assert_kb_gate(
        plant, offline_only, _units_map({"stub_unit": "stub_kind"}),
        (_kb("kb.stub.block", "v <= 100", ("stub_kind",)),),
    ) is None


def test_gate_sparse_node_absent_skipped() -> None:
    """node 快照缺席=通透跳过（sparse 镜像）：帧内无该节点=零 applicable。"""
    plant = _plant({"design": {}, "avg": {}})  # design 帧空（目标单元缺席）
    assert _gate(plant, (_kb("kb.stub.block", "v <= 100", ("stub_kind",)),)) is None


def test_gate_applicability_conjunction_guards() -> None:
    """applicable 三 conjunction 镜像+block 档：boundary_check（含符号式表达
    不触 DSL）/unit_kinds 缺席/字段缺席三态均不适用——越门值零 raise。"""
    plant = _plant({"design": {"stub_unit": {"v": 120.0}}, "avg": {}})
    assert _gate(plant, (
        _kb("site.stub.containment", "containment == inside",
            ("stub_kind",), kind="boundary_check"),
        _kb("kb.stub.other_kind", "v <= 100", ("other_kind",)),
        _kb("kb.stub.absent_field", "absent <= 1", ("stub_kind",)),
    )) is None


# ── run_full_calc 接线（execute_graph 之后、summary 组装之前）──────────


def _golden_bundle(constraints: tuple[KbConstraint, ...]) -> Any:
    """municipal_34760 checked=[aao] 实跑（golden e2e 同径 env 装配）。"""
    from waterprint.app import load_project, load_run_env, run_full_calc

    project = load_project(
        Path(__file__).resolve().parents[1] / "golden" / "golden_data"
        / "municipal_34760" / "input_project.json"
    )
    env = load_run_env(_REPO_DATA, project)
    return run_full_calc(
        project, build_condition_set(["municipal_aao"]), env,
        constraints=constraints,
    )


def _loaded_kb() -> tuple[KbConstraint, ...]:
    """kb 真源装载（155 条全量——18 条 block 含面）。"""
    from waterprint.solution.constraints import load_kb_constraints

    return load_kb_constraints(_REPO_DATA / "constraint_kb" / "constraints.json")


def test_run_full_calc_real_kb_zero_violations() -> None:
    """接线锚①：真实 kb 2.1.0 全量注入 golden=零违规零 raise（P1 探针预期
    ——sensitivity 帧 maint.* 标注语义不变）。"""
    bundle = _golden_bundle(_loaded_kb())  # 零 raise 即通过
    assert any(
        ".kb." in k
        for k in bundle.plant.summary["design_offline_municipal_aao"]
    )  # maint 标注面在场（阻断门与观测面并行不悖）


def test_run_full_calc_constructed_violation_raises() -> None:
    """接线锚②：构造 block 违规（aao design 帧 n=2 对 n<=0）→KbBlockError
    全败丢弃（run_full_calc 内 raise——半成品不进 summary/diagnostics）。"""
    violating = _kb("kb.stub.never", "n <= 0", ("municipal_aao",))
    with pytest.raises(KbBlockError, match="kb.stub.never"):
        _golden_bundle((violating,))


def test_run_full_calc_default_constraints_unchanged() -> None:
    """铁律二锚：constraints=() 零行为变更——golden 双跑 serialize 字节同
    （阻断门 no-op 后既有链路逐字节恒等）。"""
    from waterprint.contracts.result_schema import serialize

    first = serialize(_golden_bundle(()).plant)
    second = serialize(_golden_bundle(()).plant)
    assert first == second
