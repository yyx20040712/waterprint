"""app_enumeration 伴生件镜像测试：类型面守卫 + 上游重建正反两向。

输入:  waterprint.app_enumeration 公开符号（镜像规则：test_<模块名>.py）
输出:  伴生件契约断言（M2-SOL D2：选项默认值/裸 str 拒/导出分发/重建域）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.app_enumeration")
EnumerationOptions = getattr(_mod, "EnumerationOptions", None)
UpstreamSource = getattr(_mod, "UpstreamSource", None)
upstream_context = getattr(_mod, "upstream_context", None)
export_artifact = getattr(_mod, "export_artifact", None)
ArtifactKindNotReady = getattr(_mod, "ArtifactKindNotReady", None)

pytestmark = pytest.mark.skipif(
    None in (EnumerationOptions, UpstreamSource, upstream_context, export_artifact,
             ArtifactKindNotReady),
    reason="实现未就绪：waterprint.app_enumeration（M2-SOL）",
)

_DATA = Path(__file__).resolve().parents[2].parent / "data" / "coefficients"


def test_options_defaults_core_side() -> None:
    """core 侧默认：无约束/裕度宽优先/limit 取全部（分页归服务层）。"""
    options = EnumerationOptions()  # type: ignore[misc]
    assert options.constraints == ()
    assert options.sort_by == "margin_min"
    assert options.ascending is False
    assert options.limit is None


def test_options_bare_str_constraints_rejected() -> None:
    """constraints 裸 str 拒（I-2 同款防线：逐字符拆解为伪键）。"""
    with pytest.raises(TypeError, match="裸 str"):  # type: ignore[misc]
        EnumerationOptions(constraints="kb.demo.len_max")  # type: ignore[misc]


def test_upstream_context_rebuilds_inflow() -> None:
    """上游重建正向：inlet→CASS 经 execute_graph 既有产物重建入流工况。"""
    from waterprint.app import assemble, run_full_calc
    from waterprint.contracts.condition import FlowCase, OperatingCondition
    from waterprint.contracts.condition import build_condition_set as _bcs
    from waterprint.contracts.flow import WaterFlow
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="m2sol",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0,
                    "BOD5": 200.0,
                    "SS": 250.0,
                    "TN": 43.0,
                },
                "municipal_cass": {},
            },
            edges=[
                {
                    "src": {"unit_id": "inlet", "port_id": "out"},
                    "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                }
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="m2sol",
            data_version="m2sol",
        ),
    )
    assembled = assemble(project, env)
    plant = run_full_calc(project, _bcs([]), env).plant
    condition = OperatingCondition(flow_case=FlowCase.DESIGN)
    ctx = upstream_context(  # type: ignore[misc]
        UpstreamSource(assembled.units, assembled.edges, project.design, plant),  # type: ignore[misc]
        "municipal_cass",
        condition,
        env,
    )
    assert set(ctx.inflows) == {next(iter(assembled.edges)).dst}
    flow = ctx.inflows[next(iter(assembled.edges)).dst]
    assert isinstance(flow, WaterFlow)
    assert flow.q_avg_daily == pytest.approx(34760.7 / 86400, rel=1e-9)
    assert flow.kz == pytest.approx(1.4)
    assert ctx.inqualities[next(iter(assembled.edges)).dst].concentrations["TN"] == (
        pytest.approx(43.0)
    )
    assert ctx.params["n_pool"] == pytest.approx(4.0)  # manifest 默认∪design 覆盖面
    assert ctx.condition is condition


def test_upstream_context_unknown_unit_rejected() -> None:
    """上游重建负向：未命中单元=KeyError（装配缺陷口径，程序性失败）。"""
    from waterprint.app import assemble, run_full_calc
    from waterprint.contracts.condition import FlowCase, OperatingCondition
    from waterprint.contracts.condition import build_condition_set as _bcs
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="m2sol",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )
    project = ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={"inlet": {"kind": "municipal_input", "q_avg_daily": 0.5, "kz": 1.4}},
            edges=[],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="m2sol",
            data_version="m2sol",
        ),
    )
    assembled = assemble(project, env)
    plant = run_full_calc(project, _bcs([]), env).plant
    with pytest.raises(KeyError):
        upstream_context(  # type: ignore[misc]
            UpstreamSource(assembled.units, assembled.edges, project.design, plant),  # type: ignore[misc]
            "no_such_unit",
            OperatingCondition(flow_case=FlowCase.DESIGN),
            env,
        )
