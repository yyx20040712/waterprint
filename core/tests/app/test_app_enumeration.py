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


def test_export_artifact_dxf_site_plan_writes_drawing(tmp_path: Path) -> None:
    """M5 D1+M6 案乙：dxf 全厂总图正向——site_layout 出图+文件内嵌目录页实体。

    断：bytes 非空+out 落盘一致+DXF 头魔面 AC1032（R2018）；工况显式
    design 档（condition_key 显式传——UserWarning 零涉）；M6 目录面
    （ezdxf 读回）：表题「图纸目录」+四列表头+总图行图号 01（直承
    _SITE_SHEET_NO）+单元行图号 02..N+1（unit_id 字典序——摆放结构
    列表为真源，悬空单元 municipal_aao 同入列=图之所绘）+比例列恒
    write_dxf 缺省同值 1:100+目录实体位于图框下方（表体顶=包围盒底
    -gap）。
    """
    import ezdxf

    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set as _bcs
    from waterprint.contracts.project_schema import (
        DesignState,
        Metadata,
        ProjectFile,
        SiteDesign,
        StructurePlacement,
    )
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
    assert "design" in plant.conditions  # 显式工况前提
    out = tmp_path / "site.dxf"
    payload = export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out,
        site_design=SiteDesign(
            structures={
                "municipal_cass": StructurePlacement(x=5.0, y=5.0),
                "municipal_aao": StructurePlacement(x=15.0, y=5.0),  # 悬空（快照无）=摆放真源同入目录
            }
        ),
        condition_key="design",
    )
    assert payload  # 禁静默空产物（UF-33）
    assert out.read_bytes() == payload  # write_dxf 落盘与返回字节一致
    assert b"AC1032" in payload[:512]  # DXF R2018 头魔面
    msp = ezdxf.readfile(out).modelspace()
    texts = {e.dxf.text for e in msp.query("TEXT")}
    assert {"图纸目录", "序号", "图号", "图名", "比例"} <= texts  # 表题+四列表头
    assert {"01", "1:100"} <= texts  # 总图行图号+比例列（write_dxf 缺省同值）
    assert {"02", "03", "municipal_cass", "municipal_aao"} <= texts  # 字典序 02..N+1
    border = [e for e in msp.query("LWPOLYLINE")
              if e.dxf.layer == "WP-frame-border"]
    frame = max(border, key=lambda e: max(p[1] for p in e.get_points("xy")))
    frame_bottom = min(p[1] for p in frame.get_points("xy"))
    catalog_title = next(e for e in msp.query("TEXT") if e.dxf.text == "图纸目录")
    assert catalog_title.dxf.insert[1] < frame_bottom  # 目录在图框下方（mm 域读回）

    # R1 行级配对（G1-05 二审 CONFIRMED）：集合包含断言拦不住排序方向
    # 回归——总控变异实证：接线处 sorted→reversed(sorted()) 后旧断言面
    # 仍 15 用例全绿。按列锚 x 分组图号列/图名列文字（各列锚 x=列起点+
    # 0.15 内缩恒同值），y 降序（=目录行序）断言图号↔图名字典序配对映射。
    no_x = next(e.dxf.insert[0] for e in msp.query("TEXT") if e.dxf.text == "01")
    name_x = next(e.dxf.insert[0] for e in msp.query("TEXT")
                  if e.dxf.text == "全厂总图")

    def column(anchor_x: float) -> list:
        headers = {"序号", "图号", "图名", "比例"}  # 表头行与数据列同锚 x——剔出
        return sorted(
            (e for e in msp.query("TEXT")
             if abs(e.dxf.insert[0] - anchor_x) < 1e-6 and e.dxf.text not in headers),
            key=lambda e: -e.dxf.insert[1],
        )

    assert [e.dxf.text for e in column(no_x)] == ["01", "02", "03"]  # 图号列行序
    assert [e.dxf.text for e in column(name_x)] == [
        "全厂总图", "municipal_aao", "municipal_cass",
    ]  # 图名列=总图行+unit_id 字典序（aao<cass↔02/03 配对）


def test_export_artifact_dxf_site_plan_requires_site_design(tmp_path: Path) -> None:
    """M5 D1：全厂总图诚实拒绝——unit_id 缺省且无 site_design→ArtifactKindNotReady。

    直接 core 调用方无 site 通道时显性报（server 单产物通道有透传；批量面
    暂不支持——M5 注记）；最小 PlantResult 沿 SC1 空工况用例构造形态。
    """
    from waterprint.contracts.result_schema import PlantResult, ReproTriple

    plant = PlantResult(
        conditions={}, summary={}, trace=(),
        repro=ReproTriple(design_hash="t" * 16, engine_version="t", data_version="t"),
    )
    with pytest.raises(ArtifactKindNotReady, match="须传 site_design"):  # type: ignore[misc]
        export_artifact(  # type: ignore[misc]
            "dxf", plant, Path("unused"), tmp_path / "site.dxf"
        )
