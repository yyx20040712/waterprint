"""executor 镜像测试：图执行编排（工况 2+k 全索引、异常隔离、装配边界）。

输入:  waterprint.graph.execute_graph 公开符号
输出:  编排语义断言（细粒度端到端归 M1 三单元切片与 golden）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.graph.executor")
execute_graph = getattr(_mod, "execute_graph", None)

pytestmark = pytest.mark.skipif(
    execute_graph is None,
    reason="实现未就绪：waterprint.graph.executor（M1 三单元切片）",
)


def test_executor_exposes_protocol_only_entry() -> None:
    """装配边界：执行器入口存在且可调用（具体单元由 app.py 注入）。

    深度行为断言（三单元线性图/回路/双跑 diff=0）随 M1 切片实现激活，
    数值对照由 golden 端到端承载（tests/golden/）。
    """
    assert callable(execute_graph)


def test_executor_does_not_import_units_lib() -> None:
    """铁律：executor 模块禁止 import units_lib（import-linter 同款断言）。"""
    import sys

    assert not any(
        name.startswith("waterprint.units_lib")
        for name in sys.modules
        if name.startswith("waterprint.graph")
    ), "graph 执行链不得加载具体单元（装配点唯一）"


# ── GOLDEN4b R1（总控裁决 2026-08-28）：真环机制两修复的行为锁定。
#    ①跨层消费回归：SCC 组占最浅成员层（max→min）——修复前非组成员在
#    组求解层之前消费组输出=读空池裸 KeyError（真环图水线尾消费产泥组
#    成员的结构性墙），修复后组尽早整组联立、组外消费者恒在更晚层就绪；
#    ②SLUDGE 回路首迭代合法：回路初值 q_wet=1e-6 微流量（修复前 0.0 触
#    dst 侧域守卫族[q_wet>0，recycle_junction GR-14 先例]首迭代即拒）。
#    图单元全用本地 stub+内置节点（tests/graph 不引 units_lib——本文件
#    铁律同源）；数值容差宽（机制行为锁定非数值 golden）。


def _stub_manifest(
    unit_id: str, ports: tuple[tuple[str, str, str], ...]
) -> object:
    """最小清单（ports 三元组）——tests 层本地图单元声明面。"""
    from waterprint.contracts.manifest import load_manifest

    return load_manifest(
        {
            "unit_id": unit_id,
            "i18n_key": f"stub.{unit_id}",
            "version": "1.0",
            "business_line": "municipal",
            "params": [],
            "ports": [
                {"port_id": port, "fluid": fluid, "direction": direction}
                for port, fluid, direction in ports
            ],
            "removal_refs": {},
            "norm_refs": ["GOLDEN4b R1 stub（tests/graph 本地图单元）"],
            "condition_mappings": [],
            "constraint_refs": [],
        }
    )


class _ProducerStub:
    """产泥 stub：WATER in+in_r → out(WATER)+sludge_out(SLUDGE)。"""

    manifest = _stub_manifest(
        "stub_producer",
        (
            ("in", "WATER", "IN"),
            ("in_r", "WATER", "IN"),
            ("out", "WATER", "OUT"),
            ("sludge_out", "SLUDGE", "OUT"),
        ),
    )

    def compute(self, ctx: object) -> object:
        """q=主入流+回流入口；产泥股=水量线性投影（增益<1 保收敛）。"""
        from waterprint.contracts.flow import WaterFlow
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.sludge import SludgeFlow
        from waterprint.contracts.unit_api import UnitResult

        main = ctx.inflows.get(PortRef(ctx.unit_id, "in"))  # type: ignore[attr-defined]
        recycle = ctx.inflows.get(PortRef(ctx.unit_id, "in_r"))  # type: ignore[attr-defined]
        q_main = main.q_avg_daily if main is not None else 0.0
        q_recycle = recycle.q_avg_daily if recycle is not None else 0.0
        q = q_main + q_recycle
        out = PortRef(ctx.unit_id, "out")
        sludge = PortRef(ctx.unit_id, "sludge_out")
        return UnitResult(
            outflows={
                out: WaterFlow(q_avg_daily=q, kz=1.4),
                sludge: SludgeFlow(q_wet=q * 0.01, ds=q * 0.002, moisture=0.9),
            },
            outqualities={out: WaterQuality({}), sludge: WaterQuality({})},
            dims={"q_out": q},
            warnings=(),
            formula_ids=("stub.producer",),
        )


class _PassStub:
    """污泥双出口 stub：SLUDGE in → out+sup（nongsuo sup 形状）。"""

    manifest = _stub_manifest(
        "stub_pass",
        (
            ("in", "SLUDGE", "IN"),
            ("out", "SLUDGE", "OUT"),
            ("sup", "SLUDGE", "OUT"),
        ),
    )

    def compute(self, ctx: object) -> object:
        """底流/上清液双产股（截留+分流——ds 守恒近似）。"""
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.sludge import SludgeFlow
        from waterprint.contracts.unit_api import UnitResult

        stock = ctx.inflows[PortRef(ctx.unit_id, "in")]  # type: ignore[attr-defined]
        out = PortRef(ctx.unit_id, "out")
        sup = PortRef(ctx.unit_id, "sup")
        return UnitResult(
            outflows={
                out: SludgeFlow(
                    q_wet=stock.q_wet * 0.5, ds=stock.ds * 0.95, moisture=0.95
                ),
                sup: SludgeFlow(
                    q_wet=stock.q_wet * 0.4, ds=stock.ds * 0.04, moisture=0.99
                ),
            },
            outqualities={out: WaterQuality({}), sup: WaterQuality({})},
            dims={"q_sup": stock.q_wet * 0.4 * 86400.0},
            warnings=(),
            formula_ids=("stub.pass",),
        )


class _ConsumerStub:
    """水线尾 stub：WATER in→out 透传（跨层消费见证者）。"""

    manifest = _stub_manifest(
        "stub_consumer", (("in", "WATER", "IN"), ("out", "WATER", "OUT"))
    )

    def compute(self, ctx: object) -> object:
        """透传（dims 回显 q_in——跨层读组输出的断言面）。"""
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.unit_api import UnitResult

        stock = ctx.inflows[PortRef(ctx.unit_id, "in")]  # type: ignore[attr-defined]
        out = PortRef(ctx.unit_id, "out")
        return UnitResult(
            outflows={out: stock},
            outqualities={out: WaterQuality({})},
            dims={"q_in": stock.q_avg_daily},
            warnings=(),
            formula_ids=("stub.consumer",),
        )


def _env() -> object:
    """RunEnv（loop.* 三键经 EngineParam 直投——tests 层无 app 装配）。"""
    from waterprint.contracts.run_env import EngineParam, RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    entries = {item.key: item for item in DEFAULT_ASSUMPTIONS}
    return RunEnv(
        engine_version="graph-test",
        data_version="graph-test",
        assumptions={key: item.default for key, item in entries.items()},
        coefficients={},
        price_book={},
        trace_sink=None,
        engine_params={
            key: EngineParam(value=item.default, source=item.source, note=item.note)
            for key, item in entries.items()
            if key.startswith("loop.")
        },
    )


def _conditions() -> object:
    """单元工况集（design 档——机制行为锁定非工况面）。"""
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set([])


def _design(
    nodes: dict[str, dict[str, object]], edges: list[dict[str, object]]
) -> object:
    """DesignState 直构（edges 元素=D3 冻结形态）。"""
    from waterprint.contracts.project_schema import DesignState

    return DesignState(nodes=nodes, edges=edges)  # type: ignore[arg-type]


def _edge(
    src: str, sp: str, dst: str, dp: str, recycle: bool = False
) -> dict[str, object]:
    """边构造（recycle 键恒显式——可读性）。"""
    return {
        "src": {"unit_id": src, "port_id": sp},
        "dst": {"unit_id": dst, "port_id": dp},
        "recycle": recycle,
    }


def _run(design: object, units: dict[str, object]) -> object:
    """execute_graph 正门直调。"""
    assert execute_graph is not None
    return execute_graph(design, units, _conditions(), _env())  # type: ignore[arg-type]


def test_loop_group_scheduled_at_earliest_member_layer() -> None:
    """①跨层消费回归：非组成员在组求解前消费组输出——最浅成员层调度。"""
    from waterprint.graph.nodes import builtin_unit

    design = _design(
        nodes={
            "src": {
                "kind": "municipal_input",
                "q_avg_daily": 0.4023229167,
                "kz": 1.4,
            },
            "producer": {},
            "pass1": {},
            "pass2": {},
            "consumer": {},
            "rj": {"kind": "recycle_junction"},
        },
        edges=[
            _edge("src", "out", "producer", "in"),
            _edge("producer", "out", "consumer", "in"),
            _edge("producer", "sludge_out", "pass1", "in"),
            _edge("pass1", "out", "pass2", "in"),
            _edge("pass2", "sup", "rj", "in", recycle=True),
            _edge("rj", "out", "producer", "in_r"),
        ],
    )
    units = {
        "src": builtin_unit(
            "municipal_input",
            {"q_avg_daily": 0.4023229167, "kz": 1.4},
        ),
        "producer": _ProducerStub(),
        "pass1": _PassStub(),
        "pass2": _PassStub(),
        "consumer": _ConsumerStub(),
        "rj": builtin_unit("recycle_junction", {}),
    }
    plant = _run(design, units)
    # 组={producer,pass1,pass2,rj}（SCC 经 sup 回边闭合）；consumer 非组成员
    # ——修复前组占最深成员层（pass2 层 3），consumer（层 2）先跑读空池。
    snapshot = plant.conditions["design"]  # type: ignore[index]
    q_src = snapshot["src"].outflows["src.out.q_avg_daily"]
    q_rj = snapshot["rj"].outflows["rj.out.q_avg_daily"]
    q_consumer = snapshot["consumer"].dims["q_in"]
    assert q_consumer == pytest.approx(q_src + q_rj, rel=1e-9), "跨层消费读到组解"
    sup = snapshot["pass2"].dims["q_sup"] / 86400.0
    assert q_rj == pytest.approx(sup, rel=1e-9), "rj 出流=sup 股直投（回路闭合）"
    # 确定性 R3：同 (design, conditions, env) 双跑快照逐值同
    again = _run(design, units)
    assert str(again.conditions) == str(plant.conditions)  # type: ignore[arg-type]


def test_sludge_loop_first_iteration_legal() -> None:
    """②SLUDGE 回路首迭代合法：零初值墙（q_wet=1e-6 微估计——R1 墙 B）。"""
    from waterprint.graph.nodes import builtin_unit

    design = _design(
        nodes={"producer": {}, "rj": {"kind": "recycle_junction"}},
        edges=[
            _edge("producer", "sludge_out", "rj", "in", recycle=True),
            _edge("rj", "out", "producer", "in_r", recycle=True),
        ],
    )
    units = {
        "producer": _ProducerStub(),
        "rj": builtin_unit("recycle_junction", {}),
    }
    plant = _run(design, units)  # 修复前：InvalidExecutionError（q_wet=0.0 拒）
    snapshot = plant.conditions["design"]  # type: ignore[index]
    # 收敛解：无源图回路收敛至微正流量——M-2 收紧断言（isfinite+>0 有齿：
    # 实录 q_out≈7.1e-15/q_recycle≈6.2e-11，阻尼序列单调向零不达零）
    from math import isfinite

    q_out = snapshot["producer"].outflows["producer.out.q_avg_daily"]
    assert isfinite(q_out) and q_out > 0.0, f"q_out={q_out!r}"
    q_recycle = snapshot["rj"].dims["q_recycle"]
    assert isfinite(q_recycle) and q_recycle > 0.0, f"q_recycle={q_recycle!r}"


def test_scheduling_gap_rejected_fail_closed() -> None:
    """③C-1 前置守卫：组外提供者层>组执行层=凝聚图调度缺口 fail-closed 拒。

    一审反例形态（R2 裁决 2026-08-28）：src(0)→x1(1)→x2(2)→producer(3)
    外链入组 {producer(3), rj(0)}（sludge_out 回边闭合）——组执行层=最浅
    成员层 0 < 组外 forward 提供者 x2 层 2：组求解时 x2 未就绪。修复前=
    组内 compute 读 x2 空池裸 KeyError（一审 C-1）；守卫后=执行前
    InvalidExecutionError 显式拒（凝聚图完整调度挂账机制批——此形态暂拒）。"""
    from waterprint.graph.executor import InvalidExecutionError
    from waterprint.graph.nodes import builtin_unit

    design = _design(
        nodes={
            "src": {"kind": "municipal_input", "q_avg_daily": 0.4023229167, "kz": 1.4},
            "x1": {},
            "x2": {},
            "producer": {},
            "rj": {"kind": "recycle_junction"},
        },
        edges=[
            _edge("src", "out", "x1", "in"),
            _edge("x1", "out", "x2", "in"),
            _edge("x2", "out", "producer", "in"),
            _edge("producer", "sludge_out", "rj", "in", recycle=True),
            _edge("rj", "out", "producer", "in_r"),
        ],
    )
    units = {
        "src": builtin_unit(
            "municipal_input", {"q_avg_daily": 0.4023229167, "kz": 1.4}
        ),
        "x1": _ConsumerStub(),
        "x2": _ConsumerStub(),
        "producer": _ProducerStub(),
        "rj": builtin_unit("recycle_junction", {}),
    }
    with pytest.raises(InvalidExecutionError, match="层-组调度缺口形态") as excinfo:
        _run(design, units)
    message = str(excinfo.value)
    assert "凝聚图调度挂账" in message, message
    assert "x2" in message, "消息含组外提供者（GR-09）"
    assert "组执行层 0" in message, "消息含组执行层号（GR-09）"
