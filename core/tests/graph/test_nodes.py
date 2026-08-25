"""nodes 镜像测试：内置图节点三 kind（构造校验/汇流混合/覆盖透传）。

输入:  waterprint.graph.nodes 公开符号
输出:  §14.3 内置节点语义断言（探针②入锁版；T7b 授权新建）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.graph.nodes")
builtin_unit = getattr(_mod, "builtin_unit", None)
InvalidNodeError = getattr(_mod, "InvalidNodeError", None)

pytestmark = pytest.mark.skipif(
    None in (builtin_unit, InvalidNodeError),
    reason="实现未就绪：waterprint.graph.nodes",
)


def _ctx(unit_id, inflows, inqualities):
    from waterprint.contracts.condition import FlowCase, OperatingCondition
    from waterprint.contracts.unit_api import UnitContext

    return UnitContext(
        unit_id=unit_id,
        inflows=inflows,
        inqualities=inqualities,
        params={},
        condition=OperatingCondition(flow_case=FlowCase.DESIGN),
        assumptions={},
        trace=None,
    )


def test_municipal_input_constructs_flow_and_quality() -> None:
    """市政输入：q_design 派生 + 指标正门构造 + formula_ids 含 kind 标识。"""
    from waterprint.contracts.ports import PortRef

    unit = builtin_unit(
        "municipal_input",
        {"q_avg_daily": 0.4, "kz": 1.3, "CODCR": 260.0, "BOD5": 130.0},
    )
    result = unit.compute(_ctx("inlet", {}, {}))
    out = PortRef("inlet", "out")
    assert result.outflows[out].q_avg_daily == pytest.approx(0.4)
    assert result.outflows[out].kz == pytest.approx(1.3)
    assert result.outflows[out].q_design == pytest.approx(0.4 * 1.3)
    assert result.outqualities[out].concentrations == {"CODCR": 260.0, "BOD5": 130.0}
    assert result.dims == {}
    assert result.warnings == ()
    assert result.formula_ids == ("builtin.municipal_input",)


def test_municipal_input_rejects_missing_and_extra_params() -> None:
    """缺必需参数/多余参数 = InvalidNodeError（消息含键清单，GR-09）。"""
    with pytest.raises(InvalidNodeError, match="缺必需参数"):
        builtin_unit("municipal_input", {"q_avg_daily": 0.4})
    with pytest.raises(InvalidNodeError, match="多余参数"):
        builtin_unit(
            "municipal_input", {"q_avg_daily": 0.4, "kz": 1.3, "foo": 1.0}
        )


def test_junction_mixes_load_weighted() -> None:
    """汇流：q_avg=Σ、kz=max、水质负荷加权（权重=q_avg_daily，R2 保守）。"""
    from waterprint.contracts.flow import WaterFlow
    from waterprint.contracts.ports import PortRef
    from waterprint.contracts.quality import WaterQuality

    unit = builtin_unit("junction", {})
    result = unit.compute(
        _ctx(
            "hub",
            {
                PortRef("a", "out"): WaterFlow(q_avg_daily=0.4, kz=1.3),
                PortRef("b", "out"): WaterFlow(q_avg_daily=0.6, kz=1.1),
            },
            {
                PortRef("a", "out"): WaterQuality({"CODCR": 260.0}),
                PortRef("b", "out"): WaterQuality({"CODCR": 140.0}),
            },
        )
    )
    out = PortRef("hub", "out")
    assert result.outflows[out].q_avg_daily == pytest.approx(1.0)
    assert result.outflows[out].kz == pytest.approx(1.3)
    assert result.outqualities[out].concentrations["CODCR"] == pytest.approx(188.0)


def test_junction_rejects_empty_and_sludge_inflows() -> None:
    """空入边拒（多入单出语义无意义）；SLUDGE 入边拒（v1 只做 WATER）。"""
    from waterprint.contracts.ports import PortRef
    from waterprint.contracts.sludge import SludgeFlow

    unit = builtin_unit("junction", {})
    with pytest.raises(InvalidNodeError, match="无入边"):
        unit.compute(_ctx("hub", {}, {}))
    with pytest.raises(InvalidNodeError, match="SLUDGE"):
        unit.compute(
            _ctx(
                "hub",
                {PortRef("s", "out"): SludgeFlow(q_wet=0.01, ds=2.0, moisture=0.98)},
                {},
            )
        )


def test_quality_edit_overrides_and_passes_through() -> None:
    """水质编辑：流量透传（同对象）+ 指标覆盖 + 其余透传 + 越界键拒。"""
    from waterprint.contracts.flow import WaterFlow
    from waterprint.contracts.ports import PortRef
    from waterprint.contracts.quality import WaterQuality

    flow = WaterFlow(q_avg_daily=0.6, kz=1.1)
    unit = builtin_unit("quality_edit", {"NH3N": 5.0})
    result = unit.compute(
        _ctx(
            "polish",
            {PortRef("hub", "out"): flow},
            {
                PortRef("hub", "out"): WaterQuality(
                    {"CODCR": 188.0, "NH3N": 25.0}
                )
            },
        )
    )
    out = PortRef("polish", "out")
    assert result.outflows[out] is flow
    assert result.outqualities[out].concentrations == {"CODCR": 188.0, "NH3N": 5.0}
    with pytest.raises(InvalidNodeError, match="越界"):
        builtin_unit("quality_edit", {"foo": 1.0})


def test_builtin_unit_rejects_unknown_kind() -> None:
    """未知 kind = InvalidNodeError（合法三 kind 清单入消息）。"""
    with pytest.raises(InvalidNodeError, match="未知内置节点 kind"):
        builtin_unit("bogus", {})
