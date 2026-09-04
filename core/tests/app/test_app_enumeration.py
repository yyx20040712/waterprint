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


def test_export_artifact_ifc_builds_model(tmp_path: Path) -> None:
    """SC1 D6：ifc 正门成功路径——scene→ifc 模型落盘且字节与返回一致。

    核对实录（本文件既有断言面 grep）：无 ifc 抛 NotReady 用例/合法面
    文案断言（export_artifact 面仅符号存在性）——ifc 成功路径为本用例
    新增锚。缺省工况=UserWarning"未指定工况……出模型"（dxf 同构文案，
    出模型口径）。
    """
    from waterprint.app import run_full_calc
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
            nodes={
                "inlet": {"kind": "municipal_input", "q_avg_daily": 34760.7 / 86400,
                          "kz": 1.4, "CODCR": 400.0, "BOD5": 200.0, "SS": 250.0,
                          "TN": 43.0},
                "municipal_cass": {},
            },
            edges=[
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": "municipal_cass", "port_id": "in"}},
            ],
        ),
        metadata=Metadata(
            format_version="1.0",
            content_hash="",
            engine_version="m2sol",
            data_version="m2sol",
        ),
    )
    plant = run_full_calc(project, _bcs([]), env).plant  # type: ignore[misc]
    assert plant.conditions  # 缺省工况取排序首键前提
    out = tmp_path / "model.ifc"
    with pytest.warns(UserWarning, match="未指定工况"):
        payload = export_artifact(  # type: ignore[misc]
            "ifc", plant, Path("unused.ifc"), out
        )
    assert payload != b""  # 禁静默空产物（UF-33）
    assert out.read_bytes() == payload  # write_ifc 落盘与返回字节一致


def test_export_artifact_ifc_empty_conditions_rejected(tmp_path: Path) -> None:
    """SC1 R0：空工况集 ifc 显式拒绝（总控亲验 mypy 红收口）。

    chosen=None 禁裸传 build_scene（None 入「工况不在结果」消息=mypy
    arg-type 红）；空 conditions 沿 UF-33 诚实拒绝（dxf next(iter, "")
    空串兜底先例不适用——build_scene 对空串同样 KeyError 且消息含
    空串字面量）。
    """
    from waterprint.contracts.result_schema import PlantResult, ReproTriple

    plant = PlantResult(
        conditions={}, summary={}, trace=(),
        repro=ReproTriple(design_hash="t" * 16, engine_version="t", data_version="t"),
    )
    with pytest.raises(ArtifactKindNotReady, match="至少一个工况"):
        export_artifact(  # type: ignore[misc]
            "ifc", plant, Path("unused.ifc"), tmp_path / "m.ifc"
        )
