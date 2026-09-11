"""contracts/trust.py 镜像测试：诊断契约序列化/守卫/确定性（P2 次批 ADR-012）。"""

from __future__ import annotations

import json

import pytest

from waterprint.contracts.result_schema import ReproTriple
from waterprint.contracts.trust import (
    ClosureLine,
    DiagnosticsReport,
    FlowClosure,
    IndicatorMargin,
    InvalidDiagnosticsError,
    LoopRunStats,
    UnitImbalance,
    deserialize_diag,
    serialize_diag,
)


def _report() -> DiagnosticsReport:
    """全字段样例（数值手选可读——非真源数值，契约面只验结构/纪律）。"""
    return DiagnosticsReport(
        convergence=(
            LoopRunStats("baseline:design", ("aao", "rj"), 7, 2e-7),
            LoopRunStats("baseline:avg", ("aao", "rj"), 5, 3e-7),
        ),
        loop_params={
            "loop.tolerance": 1e-10, "loop.max_iterations": 200, "loop.damping": 0.8,
        },
        mass_balance=(
            FlowClosure(
                "baseline:design",
                (ClosureLine("WATER", 0.4023229167, 0.4023229167, 0.0),),
                (
                    UnitImbalance("municipal_cugeshan", "WATER", 0.4023229167, 0.4023229167, 0.0),
                    UnitImbalance("municipal_xigeshan", "WATER", 0.4023229167, 0.4023229167, 0.0),
                ),
            ),
        ),
        effluent=(
            IndicatorMargin("baseline:design", "gb18918.level_a", "BOD5", 7.0, 10.0, 0.3),
        ),
        repro=ReproTriple("hash-1", "eng-1", "data-1"),
    )


def test_roundtrip_lossless() -> None:
    """往返无损：deserialize(serialize(x)) 逐字段等价（R2/R4）。"""
    back = deserialize_diag(serialize_diag(_report()))
    assert back == _report()


def test_serialize_deterministic() -> None:
    """确定性：同报告双跑字节级相同（R2）。"""
    assert serialize_diag(_report()) == serialize_diag(_report())


def test_empty_report_legal() -> None:
    """空诊断合法（无回路图 convergence 空；standards 空-effluent 空）。"""
    empty = DiagnosticsReport((), {}, (), (), ReproTriple("h", "e", "d"))
    back = deserialize_diag(serialize_diag(empty))
    assert back.convergence == () and back.effluent == () and back.mass_balance == ()
    assert back.loop_params == {}


def test_iterations_domain_guard() -> None:
    """iterations 域守卫：int>=1；bool/零/负/float 非整值拒；float 整值归一。"""
    with pytest.raises(InvalidDiagnosticsError, match="int>=1"):
        LoopRunStats("ck", ("a",), 0, 1e-9)
    with pytest.raises(InvalidDiagnosticsError, match="int>=1"):
        LoopRunStats("ck", ("a",), -3, 1e-9)
    with pytest.raises(InvalidDiagnosticsError, match="int>=1"):
        LoopRunStats("ck", ("a",), True, 1e-9)  # type: ignore[arg-type]
    # float 整值（serialize int 归一纪律往返前提）经 deserialize 归一 int
    data = json.loads(serialize_diag(_report()))
    data["convergence"][0]["iterations"] = 7.0
    fixed = deserialize_diag(json.dumps(data).encode("utf-8"))
    assert fixed.convergence[0].iterations == 7
    data["convergence"][0]["iterations"] = 7.5
    with pytest.raises(InvalidDiagnosticsError, match="整数值"):
        deserialize_diag(json.dumps(data).encode("utf-8"))


def test_nonfinite_rejected() -> None:
    """非有限值双侧拒：serialize NaN/Inf 拒；deserialize NaN 字面量拒（R3）。"""
    bad = DiagnosticsReport(
        (), {}, (),
        (IndicatorMargin("ck", "s", "BOD5", float("nan"), 10.0, 0.3),),
        ReproTriple("h", "e", "d"),
    )
    with pytest.raises(InvalidDiagnosticsError, match="非有限值"):
        serialize_diag(bad)
    payload = serialize_diag(_report()).decode("utf-8").replace("2e-07", "NaN")
    with pytest.raises(InvalidDiagnosticsError, match="非法 JSON"):
        deserialize_diag(payload.encode("utf-8"))


def test_strict_key_sets() -> None:
    """严格键集：根/节点级未知键拒+缺键拒（R4——消息含键名）。"""
    base = json.loads(serialize_diag(_report()))
    base["extra_key"] = 1
    with pytest.raises(InvalidDiagnosticsError, match="未知键"):
        deserialize_diag(json.dumps(base).encode("utf-8"))
    del base["loop_params"]
    with pytest.raises(InvalidDiagnosticsError, match="缺失必需键"):
        deserialize_diag(json.dumps(base).encode("utf-8"))
    node = json.loads(serialize_diag(_report()))
    node["mass_balance"][0]["lines"][0]["fluid"] = "OIL"
    with pytest.raises(InvalidDiagnosticsError, match="fluid 非法"):
        deserialize_diag(json.dumps(node).encode("utf-8"))


def test_fluid_domain_guard() -> None:
    """fluid 枚举域：WATER/SLUDGE 之外拒（构造面经 deserialize 校验路径）。"""
    data = json.loads(serialize_diag(_report()))
    data["mass_balance"][0]["unit_imbalances"][0]["fluid"] = "GAS"
    with pytest.raises(InvalidDiagnosticsError, match="fluid 非法"):
        deserialize_diag(json.dumps(data).encode("utf-8"))
