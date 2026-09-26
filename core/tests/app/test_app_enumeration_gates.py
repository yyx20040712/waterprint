"""app_enumeration_gates 镜像测试（批5 新增件——[HUMAN-LOCK] 草案转正）。

覆盖：批5 AUD-W5 双源可行口径统一（域拒行剔出可行集）+无解诊断
domain_rejected 拒因维度+联合枚举正门装配注入转发。
落位目标：core/tests/app/test_app_enumeration_gates.py（三连锁同批闭合）。
"""
from __future__ import annotations

from pathlib import Path

import pytest

_mod = __import__("waterprint.app", fromlist=["run_enumeration"])
_gates = __import__(
    "waterprint.app_enumeration_gates", fromlist=["run_enumeration"]
)
run_enumeration = getattr(_mod, "run_enumeration")
run_joint_enumerate = getattr(_mod, "run_joint_enumerate")
EnumerationOptions = getattr(_mod, "EnumerationOptions")
Constraint = getattr(_mod, "Constraint")

pytestmark = pytest.mark.skipif(
    None in (run_enumeration, run_joint_enumerate, EnumerationOptions, Constraint),
    reason="实现未就绪：批5 app_enumeration_gates（AUD-W5）",
)

_DATA = Path(__file__).resolve().parents[2].parent / "data" / "coefficients"
_UNIT = "municipal_cass"  # 15 档网格：5 实算（t_cycle=4）×10 域拒（t_cycle∈{6,8}）


def _project() -> object:
    """inlet→CASS 两节点项目（test_enumeration_usecase 同构载体）。"""
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile

    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,  # 三表流量口径
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "TN": 43.0,
                },
                _UNIT: {},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": _UNIT, "port_id": "in"},
                }
            ],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="", engine_version="b5",
            data_version="b5",
        ),
    )


def _env() -> object:
    """真实数据包 env（coefficients factor.cass.*/removal.cass.* 在册）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    return RunEnv(
        engine_version="b5",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def _conditions() -> object:
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set([])


def test_domain_rejected_rows_excluded_from_feasible() -> None:
    """AUD-W5：域拒行（nan_flag=True）不入可行集/排序/分页面。"""
    outcome = run_enumeration(  # type: ignore[misc]
        _project(), _UNIT, _conditions(), _env()
    )
    assert outcome.total_feasible == 10  # 5 实算档 × 双工况（原 30 含 20 域拒）
    assert outcome.domain_rejected == 20  # 有解路径域拒计数透传（d1 W-2）
    assert int(outcome.rows["nan_flag"].sum()) == 0  # rows 全为实算行
    assert int(outcome.rows["v_plant"].notna().sum()) == 10
    assert outcome.diagnosis is None  # 可行非空=无诊断


def test_infeasible_diagnosis_carries_domain_dimension() -> None:
    """AUD-W5 拒因维度：恒假约束→domain_rejected=20 与约束失败计数分维。"""
    impossible = EnumerationOptions(  # type: ignore[misc]
        constraints=(
            Constraint(  # type: ignore[misc]
                key="demo.impossible", expression="v_plant <= 0", source="test"
            ),
        )
    )
    outcome = run_enumeration(  # type: ignore[misc]
        _project(), _UNIT, _conditions(), _env(), impossible
    )
    assert outcome.total_feasible == 0
    assert outcome.diagnosis is not None
    assert outcome.diagnosis.domain_rejected == 20  # 域拒 20 行独立计数
    assert outcome.diagnosis.fail_counts  # 约束失败计数面仍在
    assert outcome.diagnosis.minimal_conflicts  # 冲突集非空（无解诊断可用）


def test_all_domain_rejected_without_constraints_is_domain_report() -> None:
    """全域拒+空约束=域拒报告（fail_counts 仅 domain_nan_rows——批5）。"""
    import pandas

    from waterprint.app_enumeration_gates import (
        _enumeration_diagnosis,  # 私面直证（镜像件义务）
    )

    frame = pandas.DataFrame(
        {"v": [float("nan")] * 3, "nan_flag": [True] * 3}
    )
    report = _enumeration_diagnosis(frame, (), None, object())
    assert report.domain_rejected == 3
    assert dict(report.fail_counts) == {"domain_nan_rows": 3}
    assert report.minimal_conflicts == () and report.suggestions == ()


def test_joint_gate_injects_assemble_when_absent() -> None:
    """联合枚举正门：assemble=None 时经 app_assembly 注入（转发语义零变）。"""
    from tests.solution.test_beam import (  # 既有夹具单点复用
        _AAO,
        _CASS,
        _conditions,
        _env,
        _options,
        _project,
    )

    outcome = run_joint_enumerate(  # type: ignore[misc]
        _project(), [_AAO, _CASS], _conditions(), _env(), _options()
    )
    assert len(outcome.combos) >= 1  # 全链可跑（详断言归 test_beam 既有面）


def test_outcome_domain_rejected_default_zero() -> None:
    """d1 W-2：domain_rejected 缺省 0——旧构造面（无该参）兼容。"""
    from waterprint.app_enumeration import EnumerationOutcome

    outcome = EnumerationOutcome(
        rows=None, total_feasible=0, truncated=False,
        diagnosis=None, grid=None,
    )
    assert outcome.domain_rejected == 0


def test_gates_module_is_single_definition_face() -> None:
    """app 再导出=伴生件定义面单源（B3 R1 恒等钉面先例）。"""
    assert run_enumeration is _gates.run_enumeration
    assert run_joint_enumerate is _gates.run_joint_enumerate
