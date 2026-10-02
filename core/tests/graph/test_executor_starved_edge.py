"""executor 检修饥饿边镜像测试（conv-golden 批 2026-10-02——UF-61④ 行为锚批）。

输入:  waterprint.graph.executor.execute_graph +
       executor_assembly.forward_stocks（修复面）
输出:  四面行为锚——①offline 帧缺源股前向边→零股并入 propagate 汇流
       （守恒恢复：Σ边股==在运口全流量+零权股不稀释浓度）②基线帧
       （design/avg）缺源股=装配/单元缺陷，原生 KeyError 裸逃逸
       （GR-08——修复面不吞缺陷，conv-golden 批前行为保留）③对照帧：
       基线双口均分+汇流恢复（q/2+q/2==q 位串级）④对偶封边（回炉轮 1
       R1——判据钳制）：offline 帧**非目标单元**缺源股=装配/单元缺陷，
       仍原生 KeyError 裸逃逸（零股承接仅限缺股源单元==offline 目标
       单元的饥饿边——吞错边界对偶封死）。
       golden 面锚=tests/golden/test_municipal_conveyance_e2e.py
       （municipal_34760_conveyance 案例）；修复前红面实录=批档
       .workflow/conv-golden-20261002/red-first-run.txt（裸 KeyError
       逃逸 run_full_calc）。
"""

from __future__ import annotations

import importlib
import struct

import pytest

import waterprint.registry.dimensions  # R1a 绑定先导（模块级 _stub_manifest load_manifest 前置——dim 校验需要）

_mod = importlib.import_module("waterprint.graph.executor")
execute_graph = getattr(_mod, "execute_graph", None)

pytestmark = pytest.mark.skipif(
    execute_graph is None,
    reason="实现未就绪：waterprint.graph.executor（M1 三单元切片）",
)


def _stub_manifest(
    unit_id: str, ports: tuple[tuple[str, str, str], ...],
    params: list[dict[str, object]] | None = None,
    mappings: list[dict[str, object]] | None = None,
) -> object:
    """最小清单（test_executor.py 同款+mappings 可选——检修降级映射 stub）。"""
    from waterprint.contracts.manifest import load_manifest

    return load_manifest(
        {
            "unit_id": unit_id, "i18n_key": f"stub.{unit_id}", "version": "1.0",
            "business_line": "municipal", "params": params if params is not None else [],
            "ports": [{"port_id": p, "fluid": f, "direction": d} for p, f, d in ports],
            "removal_refs": {}, "norm_refs": ["conv-golden 批 stub（tests/graph 本地图单元）"],
            "condition_mappings": mappings if mappings is not None else [],
            "constraint_refs": [],
        }
    )


class _SplitStub:
    """动态多口分流 stub：WATER in → out_1~out_n（conveyance 配水类形态
    ——ports 声明单 out 口、compute 按参数 n 动态产口；condition_mappings
    =n 降级三元式——DSL 真路径，非 stub 自读 condition）。"""

    manifest = _stub_manifest(
        "stub_split", (("in", "WATER", "IN"), ("out", "WATER", "OUT")),
        params=[{"field_id": "n", "label_zh": "出流口数", "dim": "DIMENSIONLESS",
                 "default": 2.0, "grid": [2.0, 3.0, 4.0]}],
        mappings=[{"target": "n", "rule": "n if pool.all_pools else n - 1"}],
    )

    def compute(self, ctx: object) -> object:
        """每口 q/n 均分+水质透传（一条 BOD5 指标承载 mix 见证）。"""
        from waterprint.contracts.flow import WaterFlow
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.unit_api import UnitResult

        inflow = ctx.inflows[PortRef(ctx.unit_id, "in")]  # type: ignore[attr-defined]
        count = int(ctx.params["n"])  # type: ignore[attr-defined]
        quality = WaterQuality({"BOD5": 200.0})
        outflows = {}
        outqualities = {}
        for index in range(1, count + 1):
            ref = PortRef(ctx.unit_id, f"out_{index}")
            outflows[ref] = WaterFlow(
                q_avg_daily=inflow.q_avg_daily / count, kz=inflow.kz
            )
            outqualities[ref] = quality
        return UnitResult(
            outflows=outflows, outqualities=outqualities,
            dims={"q_each": inflow.q_avg_daily / count, "n_effective": float(count)},
            warnings=(), formula_ids=("stub.split",),
        )


class _MergeWitnessStub:
    """汇流见证 stub：WATER in→out 双透传（q 回显 dims+水质透传——
    test_executor.py _ConsumerStub 空水质不担浓度见证，本 stub 补该面）。"""

    manifest = _stub_manifest(
        "stub_witness", (("in", "WATER", "IN"), ("out", "WATER", "OUT"))
    )

    def compute(self, ctx: object) -> object:
        """入流双量+水质透传（汇流守恒与浓度恒等的断言面）。"""
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.unit_api import UnitResult

        ref = PortRef(ctx.unit_id, "in")
        stock = ctx.inflows[ref]  # type: ignore[attr-defined]
        quality = ctx.inqualities.get(ref, WaterQuality({}))  # type: ignore[attr-defined]
        out = PortRef(ctx.unit_id, "out")
        return UnitResult(
            outflows={out: stock}, outqualities={out: quality},
            dims={"q_in": stock.q_avg_daily}, warnings=(),
            formula_ids=("stub.witness",),
        )


class _SilentStub:
    """哑源 stub：声明 out 口但 compute 产零出流（缺股缺陷注入器——
    非目标单元缺股对偶用例的病灶形态：单元正常返回但未产布线口股）。"""

    manifest = _stub_manifest(
        "stub_silent", (("in", "WATER", "IN"), ("out", "WATER", "OUT"))
    )

    def compute(self, ctx: object) -> object:
        """声明面合法、产出面缺口（装配/单元缺陷载体——无布线口股）。"""
        from waterprint.contracts.unit_api import UnitResult

        return UnitResult(
            outflows={}, outqualities={}, dims={"silent": 1.0},
            warnings=(), formula_ids=("stub.silent",),
        )


def _env() -> object:
    """RunEnv（loop.* 三键经 EngineParam 直投——tests 层无 app 装配）。"""
    from waterprint.contracts.run_env import EngineParam, RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    entries = {item.key: item for item in DEFAULT_ASSUMPTIONS}
    return RunEnv(
        engine_version="graph-test", data_version="graph-test",
        assumptions={key: item.default for key, item in entries.items()},
        coefficients={}, price_book={}, trace_sink=None,
        engine_params={key: EngineParam(value=item.default, source=item.source, note=item.note)
                       for key, item in entries.items() if key.startswith("loop.")},
    )


def _split_graph(
    node_params: dict[str, object], *, ghost: bool = False
) -> tuple[object, dict[str, object]]:
    """共用装配：src→split（双口布线 out_1/out_2 同入一口）→cons 线性图。

    ghost=True 增哑源注入边 ghost.out→cons.in（_SilentStub 产零出流
    ——非目标单元缺股缺陷载体，对偶封边用例专用）。"""
    from waterprint.contracts.project_schema import DesignState
    from waterprint.graph.nodes import builtin_unit

    edges = [
        {"src": {"unit_id": "src", "port_id": "out"},
         "dst": {"unit_id": "split", "port_id": "in"}, "recycle": False},
        {"src": {"unit_id": "split", "port_id": "out_1"},
         "dst": {"unit_id": "cons", "port_id": "in"}, "recycle": False},
        {"src": {"unit_id": "split", "port_id": "out_2"},
         "dst": {"unit_id": "cons", "port_id": "in"}, "recycle": False},
    ]
    nodes: dict[str, dict[str, object]] = {
        "src": {"kind": "municipal_input", "q_avg_daily": 34760.7,
                "kz": 1.4, "BOD5": 200.0},
        "split": dict(node_params),
        "cons": {},
    }
    units: dict[str, object] = {
        "src": builtin_unit(
            "municipal_input", {"q_avg_daily": 34760.7, "kz": 1.4, "BOD5": 200.0}
        ),
        "split": _SplitStub(),
        "cons": _MergeWitnessStub(),
    }
    if ghost:
        nodes["ghost"] = {}
        edges.append(
            {"src": {"unit_id": "ghost", "port_id": "out"},
             "dst": {"unit_id": "cons", "port_id": "in"}, "recycle": False}
        )
        units["ghost"] = _SilentStub()
    design = DesignState(nodes=nodes, edges=edges)  # type: ignore[arg-type]
    return design, units


def test_offline_starved_edge_zero_stock_conserves() -> None:
    """饥饿边镜像锚①：offline 帧缺源股边→零股并入汇流——守恒恢复。

    split offline n 2→1（DSL 三元式真路径）只产 out_1（q 全量）；布线
    out_2 边饥饿→零股；cons 入流==src 出流位串级（q+0.0==q）；
    cons 水质==src 浓度（零权股不稀释——mix 零权股 GR-04 合法语义）。
    """
    from waterprint.contracts.condition import build_condition_set

    design, units = _split_graph({})
    plant = execute_graph(  # type: ignore[misc]
        design, units, build_condition_set(["split"]), _env()
    )
    snapshot = plant.conditions["design_offline_split"]  # type: ignore[index]
    q_src = snapshot["src"].outflows["src.out.q_avg_daily"]
    split = snapshot["split"]
    assert split.dims["n_effective"] == 1.0  # DSL 降级 n−1 生效
    assert split.dims["q_each"] == q_src  # 在运口承载全流量
    assert set(split.outflows) == {
        "split.out_1.q_avg_daily", "split.out_1.kz", "split.out_1.q_design",
    }  # UF-42 三键槽（q_design 派生）——offline 帧只产 out_1 口
    cons = snapshot["cons"]
    assert struct.pack("<d", cons.dims["q_in"]) == struct.pack("<d", q_src)  # 饥饿边零股：q+0.0==q 守恒（位串级）
    assert cons.outqualities["cons.out.BOD5"] == 200.0  # 水质不被零股稀释


def test_baseline_missing_stock_still_native_keyerror() -> None:
    """饥饿边镜像锚②：基线帧（design/avg）缺源股=原生 KeyError 裸逃逸。

    节点参数 n=1（直投绕开 grid——装配档位执法归 app.assemble 面）使
    split 基线帧即缺 out_2 股：无 offline 语境=装配/单元缺陷，GR-08
    禁静默默认——修复面不吞缺陷（conv-golden 批前行为保留）。
    """
    from waterprint.contracts.condition import build_condition_set

    design, units = _split_graph({"n": 1.0})
    with pytest.raises(KeyError):
        execute_graph(  # type: ignore[misc]
            design, units, build_condition_set([]), _env()
        )


def test_baseline_split_even_and_merge_restores() -> None:
    """饥饿边镜像锚③（对照帧）：基线双口均分+汇流恢复——q/2+q/2==q
    位串级（半除精确）+水质恒等透传（穿流语义前提锚）。"""
    from waterprint.contracts.condition import build_condition_set

    design, units = _split_graph({})
    plant = execute_graph(  # type: ignore[misc]
        design, units, build_condition_set([]), _env()
    )
    snapshot = plant.conditions["design"]  # type: ignore[index]
    q_src = snapshot["src"].outflows["src.out.q_avg_daily"]
    split = snapshot["split"]
    assert split.dims["n_effective"] == 2.0
    q1 = split.outflows["split.out_1.q_avg_daily"]
    q2 = split.outflows["split.out_2.q_avg_daily"]
    bits = struct.pack("<d", q_src / 2)
    assert struct.pack("<d", q1) == struct.pack("<d", q2) == bits  # 均分（位串级）
    assert struct.pack("<d", q1 + q2) == struct.pack("<d", q_src)  # 汇流恢复（q/2+q/2==q 精确）
    assert struct.pack("<d", snapshot["cons"].dims["q_in"]) == struct.pack("<d", q_src)  # 汇流后守恒
    assert snapshot["cons"].outqualities["cons.out.BOD5"] == 200.0


def test_offline_nontarget_missing_stock_still_native_keyerror() -> None:
    """饥饿边镜像锚④（对偶封边——回炉轮 1 R1 判据钳制）：offline 帧
    **非目标单元**缺源股=装配/单元缺陷，仍原生 KeyError 裸逃逸。

    offline 目标=split（其饥饿边正常零股承接）；哑源 ghost（声明 out
    口但产零出流——非目标单元）布线 ghost.out→cons.in：判据钳制后
    不被静默零股吞错（吞错边界=仅缺股源单元==offline 目标单元），
    GR-08 对偶面封死。"""
    from waterprint.contracts.condition import build_condition_set

    design, units = _split_graph({}, ghost=True)
    with pytest.raises(KeyError):
        execute_graph(  # type: ignore[misc]
            design, units, build_condition_set(["split"]), _env()
        )
