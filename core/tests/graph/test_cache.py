"""cache 镜像测试：结果缓存件（命中=跳过 compute+trace 重放——冷/暖等价）。

输入:  waterprint.graph.cache 公开符号（ResultCache/CachedUnitRun/CaptureSink/
       design_fingerprint/default_cache）+ executor 接入面
输出:  LRU 逐出/get 位次刷新（N14 G1-02）/容量非整数拒（N14 G1-01）/
       键五分量逐项失配/指纹 design 全字段覆盖/命中跳过+trace 重放/
       R4 自然过期（整 design 失配+旧键保留）/回路组旁路/单例隔离断言
"""

from __future__ import annotations

import pytest

# ── 本地图单元（tests/graph 不引 units_lib——本文件铁律同源 test_executor）──


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
            "norm_refs": ["B12 cache stub（tests/graph 本地图单元）"],
            "condition_mappings": [],
            "constraint_refs": [],
        }
    )


class _CountingPass:
    """水线透传 stub（计数+trace 记录）：WATER in→out。"""

    def __init__(self, unit_id: str) -> None:
        self.manifest = _stub_manifest(
            unit_id, (("in", "WATER", "IN"), ("out", "WATER", "OUT"))
        )
        self.calls = 0

    def compute(self, ctx: object) -> object:
        """透传+计数+单节点 trace（缓存重放断言材料）。"""
        from waterprint.contracts.condition import ConditionSet
        from waterprint.contracts.flow import WaterFlow
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.trace_api import TraceNodeSpec
        from waterprint.contracts.unit_api import UnitResult

        self.calls += 1
        stock = ctx.inflows[PortRef(ctx.unit_id, "in")]  # type: ignore[attr-defined]
        out = PortRef(ctx.unit_id, "out")
        q = stock.q_avg_daily
        ctx.trace.record(  # type: ignore[attr-defined]
            TraceNodeSpec(
                formula_id=f"stub.{ctx.unit_id}",
                unit_id=ctx.unit_id,
                condition_key=ConditionSet.key(ctx.condition),  # type: ignore[attr-defined]
                bindings={},
                result=q,
            )
        )
        return UnitResult(
            outflows={out: WaterFlow(q_avg_daily=q, kz=stock.kz)},
            outqualities={out: WaterQuality({})},
            dims={"q_in": q},
            warnings=(),
            formula_ids=(f"stub.{ctx.unit_id}",),
        )


class _CountingWrap:
    """单元计数包装（内置节点回路组成员旁路断言面）。"""

    def __init__(self, inner: object) -> None:
        self.inner = inner
        self.manifest = getattr(inner, "manifest")
        self.calls = 0

    def compute(self, ctx: object) -> object:
        """计数后委托内单元。"""
        self.calls += 1
        return self.inner.compute(ctx)  # type: ignore[attr-defined]


class _ListSink:
    """收集 sink（trace 冷/暖对照断言面）。"""

    def __init__(self) -> None:
        self.records: list[object] = []

    def record(self, node: object) -> None:
        """到达序累积。"""
        self.records.append(node)


def _env(sink: object, version: str = "cache-test") -> object:
    """RunEnv（loop.* 三键经 EngineParam 直投——tests 层无 app 装配）。"""
    from waterprint.contracts.run_env import EngineParam, RunEnv
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    entries = [item for item in DEFAULT_ASSUMPTIONS if item.key.startswith("loop.")]
    return RunEnv(
        engine_version=version,
        data_version=version,
        assumptions={item.key: item.default for item in DEFAULT_ASSUMPTIONS},
        coefficients={},
        price_book={},
        trace_sink=sink,
        engine_params={
            item.key: EngineParam(
                value=item.default, source=item.source, note=item.note
            )
            for item in entries
        },
    )


def _conditions() -> object:
    """单元工况集（design 档）。"""
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set([])


def _design(
    nodes: dict[str, dict[str, object]], edges: list[dict[str, object]]
) -> object:
    """DesignState 直构（edges 元素=D3 冻结形态）。"""
    from waterprint.contracts.project_schema import DesignState

    return DesignState(nodes=nodes, edges=edges)  # type: ignore[arg-type]


def _edge(src: str, sp: str, dst: str, dp: str) -> dict[str, object]:
    """边构造。"""
    return {
        "src": {"unit_id": src, "port_id": sp},
        "dst": {"unit_id": dst, "port_id": dp},
    }


def _linear_design() -> object:
    """线性两单元链（src 内置输入→c1→c2）。"""
    return _design(
        nodes={
            "src": {"kind": "municipal_input", "q_avg_daily": 0.1, "kz": 1.4},
            "c1": {},
            "c2": {},
        },
        edges=[_edge("src", "out", "c1", "in"), _edge("c1", "out", "c2", "in")],
    )


def _linear_units() -> dict[str, object]:
    """线性链注册表（c1/c2 计数 stub）。"""
    from waterprint.graph.nodes import builtin_unit

    return {
        "src": builtin_unit("municipal_input", {"q_avg_daily": 0.1, "kz": 1.4}),
        "c1": _CountingPass("c1"),
        "c2": _CountingPass("c2"),
    }


# ── 缓存件单元面 ──────────────────────────────────────────────────


def test_result_cache_lru_evicts_oldest() -> None:
    """容量逐出最旧（缩参实例——512 默认不可测逐出）。"""
    from waterprint.graph.cache import ResultCache
    from waterprint.graph.incremental import CacheKey

    cache = ResultCache(capacity=2)
    value = object()
    for index in range(3):
        cache.put(CacheKey(f"u{index}", "h", "c", "e", "d"), value)  # type: ignore[arg-type]
    assert len(cache) == 2
    assert cache.get(CacheKey("u0", "h", "c", "e", "d")) is None  # type: ignore[arg-type]
    assert cache.get(CacheKey("u1", "h", "c", "e", "d")) is not None  # type: ignore[arg-type]


def test_cache_key_five_components_each_mismatch() -> None:
    """五分量逐项失配（unit_id/design_hash/condition_key/engine/data）。"""
    from waterprint.graph.cache import ResultCache
    from waterprint.graph.incremental import CacheKey

    cache = ResultCache()
    base = CacheKey("u", "h", "c", "e", "d")
    cache.put(base, object())  # type: ignore[arg-type]
    for variant in (
        CacheKey("u2", "h", "c", "e", "d"),
        CacheKey("u", "h2", "c", "e", "d"),
        CacheKey("u", "h", "c2", "e", "d"),
        CacheKey("u", "h", "c", "e2", "d"),
        CacheKey("u", "h", "c", "e", "d2"),
    ):
        assert cache.get(variant) is None
    assert cache.get(base) is not None


def test_result_cache_rejects_non_positive_capacity() -> None:
    """capacity<1 拒（ValueError——配置面防御）；非整数/bool 同拒（N14 G1-01）。"""
    from waterprint.graph.cache import ResultCache

    with pytest.raises(ValueError):
        ResultCache(capacity=0)
    with pytest.raises(ValueError):
        ResultCache(capacity=2.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ResultCache(capacity=True)  # type: ignore[arg-type]


def test_result_cache_get_refreshes_recency() -> None:
    """get 刷新 LRU 位次（N14 G1-02——纯 FIFO 实现此测试必红）。"""
    from waterprint.graph.cache import ResultCache
    from waterprint.graph.incremental import CacheKey

    cache = ResultCache(capacity=2)
    value = object()
    key_a = CacheKey("a", "h", "c", "e", "d")
    key_b = CacheKey("b", "h", "c", "e", "d")
    key_c = CacheKey("c", "h", "c", "e", "d")
    cache.put(key_a, value)  # type: ignore[arg-type]
    cache.put(key_b, value)  # type: ignore[arg-type]
    assert cache.get(key_a) is value  # type: ignore[arg-type]
    cache.put(key_c, value)  # type: ignore[arg-type]
    assert cache.get(key_a) is value  # type: ignore[arg-type]
    assert cache.get(key_b) is None  # type: ignore[arg-type]


def test_get_returns_identical_entry_object() -> None:
    """get 返回条目原引用（同对象同字段——消费面禁改写契约的固化面）。"""
    from waterprint.graph.cache import ResultCache
    from waterprint.graph.incremental import CacheKey

    cache = ResultCache()
    key = CacheKey("u", "h", "c", "e", "d")
    entry = object()
    cache.put(key, entry)  # type: ignore[arg-type]
    assert cache.get(key) is entry  # type: ignore[arg-type]
    assert cache.get(key) is cache.get(key)  # type: ignore[arg-type]


def test_capture_sink_forwards_and_collects() -> None:
    """捕获腔：转发真实 sink 并累积节点（重放材料）。"""
    from waterprint.contracts.trace_api import TraceNodeSpec
    from waterprint.graph.cache import CaptureSink

    inner = _ListSink()
    capture = CaptureSink(inner)  # type: ignore[arg-type]
    first = TraceNodeSpec(formula_id="f", unit_id="u", condition_key="c",
                          bindings={}, result=1.0)
    second = TraceNodeSpec(formula_id="g", unit_id="u", condition_key="c",
                           bindings={}, result=2.0)
    capture.record(first)
    capture.record(second)
    assert inner.records == [first, second]
    assert list(capture.nodes) == [first, second]


# ── 指纹面 ────────────────────────────────────────────────────────


def test_design_fingerprint_covers_all_design_fields() -> None:
    """指纹覆盖 DesignState 全八字段（漏字段=不同 design 错误共享缓存）。"""
    from waterprint.graph.cache import design_fingerprint

    base = _design({}, [])
    variants = (
        _design({"u": {"a": 1.0}}, []),
        _design({}, [{"src": {"unit_id": "a", "port_id": "out"},
                      "dst": {"unit_id": "b", "port_id": "in"}}]),
        _design_constraint("constraint_choices", {"c": "x"}),
        _design_constraint("checked_units", ["u"]),
        _design_constraint("assumption_overrides", {"k": 1.0}),
        _design_constraint("influent", {"q": 1.0}),
        _design_constraint("standard_binding", {"s": "std"}),
        _design_constraint(
            "site",
            {"boundary": [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 2.0},
                          {"x": 3.0, "y": 4.0}]},
        ),
    )
    baseline = design_fingerprint(base)  # type: ignore[arg-type]
    for variant in variants:
        assert design_fingerprint(variant) != baseline  # type: ignore[arg-type]
    assert design_fingerprint(_design({}, [])) == baseline  # 同态同指纹


def _design_constraint(field: str, value: object) -> object:
    """单字段变体构造（pydantic 关键字直投）。"""
    from waterprint.contracts.project_schema import DesignState

    return DesignState(**{field: value})  # type: ignore[arg-type]


def test_design_fingerprint_ignores_dict_insertion_order() -> None:
    """键序噪声消除（nodes 插入序不同同指纹——canonical JSON sort_keys）。"""
    from waterprint.graph.cache import design_fingerprint

    first = _design({"a": {}, "b": {}}, [])
    second = _design({"b": {}, "a": {}}, [])
    assert design_fingerprint(first) == design_fingerprint(second)  # type: ignore[arg-type]


# ── executor 接入面 ───────────────────────────────────────────────


def test_hit_skips_compute_and_replays_trace() -> None:
    """命中=跳过 compute+trace 重放（冷/暖 serialize 字节同——R3 承载）。"""
    from waterprint.contracts.result_schema import serialize
    from waterprint.graph.cache import default_cache
    from waterprint.graph.executor import execute_graph

    default_cache().clear()  # 单例隔离纪律（裁定7）
    design = _linear_design()
    units = _linear_units()
    cold_sink, warm_sink = _ListSink(), _ListSink()
    cold = execute_graph(design, units, _conditions(), _env(cold_sink))  # type: ignore[arg-type]
    warm = execute_graph(design, units, _conditions(), _env(warm_sink))  # type: ignore[arg-type]
    # build_condition_set([])=design+avg 两工况——冷跑各一次，暖跑全命中
    assert units["c1"].calls == 2 and units["c2"].calls == 2  # type: ignore[attr-defined]
    assert serialize(cold) == serialize(warm)  # 含快照/repro 字节同
    assert cold_sink.records == warm_sink.records  # trace 重放（冷采集=暖重放）


def test_r4_design_change_misses_and_preserves_old_entries() -> None:
    """R4：换 design 整体失配全 miss+旧键保留永不改写（§17.2 无锁模型）。"""
    from waterprint.graph.cache import default_cache
    from waterprint.graph.executor import execute_graph

    default_cache().clear()
    units_a = _linear_units()
    design_a = _linear_design()
    execute_graph(design_a, units_a, _conditions(), _env(_ListSink()))  # type: ignore[arg-type]
    design_b = _design(
        {
            "src": {"kind": "municipal_input", "q_avg_daily": 0.2, "kz": 1.4},
            "c1": {},
            "c2": {},
        },
        [_edge("src", "out", "c1", "in"), _edge("c1", "out", "c2", "in")],
    )
    execute_graph(design_b, units_a, _conditions(), _env(_ListSink()))  # type: ignore[arg-type]
    assert units_a["c1"].calls == 4  # type: ignore[attr-defined]
    # 两 design×两工况×三单元独立键（旧键未被覆盖）
    assert len(default_cache()) == 12
    execute_graph(design_a, units_a, _conditions(), _env(_ListSink()))  # type: ignore[arg-type]
    assert units_a["c1"].calls == 4  # type: ignore[attr-defined]
    assert len(default_cache()) == 12  # 旧键仍命中（条目零改写）


def test_loop_group_members_bypass_cache() -> None:
    """回路组旁路：组内成员每跑必重算（迭代中间值入缓存=假收敛）；组外命中。"""
    from waterprint.graph.cache import default_cache
    from waterprint.graph.executor import execute_graph
    from waterprint.graph.nodes import builtin_unit

    default_cache().clear()
    design = _design(
        nodes={
            "src": {"kind": "municipal_input", "q_avg_daily": 0.4023229167,
                    "kz": 1.4},
            "producer": {},
            "consumer": {},
            "rj": {"kind": "recycle_junction"},
        },
        edges=[
            _edge("src", "out", "producer", "in"),
            _edge("producer", "out", "consumer", "in"),
            {"src": {"unit_id": "producer", "port_id": "sludge_out"},
             "dst": {"unit_id": "rj", "port_id": "in"}, "recycle": True},
            _edge("rj", "out", "producer", "in_r"),
        ],
    )
    producer = _BypassProducer()
    consumer = _CountingPass("consumer")
    wrapped_rj = _CountingWrap(builtin_unit("recycle_junction", {}))
    units = {
        "src": builtin_unit("municipal_input",
                            {"q_avg_daily": 0.4023229167, "kz": 1.4}),
        "producer": producer,
        "consumer": consumer,
        "rj": wrapped_rj,
    }
    first = execute_graph(design, units, _conditions(), _env(_ListSink()))  # type: ignore[arg-type]
    producer_calls, rj_calls = producer.calls, wrapped_rj.calls
    consumer_calls = consumer.calls
    second = execute_graph(design, units, _conditions(), _env(_ListSink()))  # type: ignore[arg-type]
    from waterprint.contracts.result_schema import serialize

    assert producer.calls > producer_calls  # 组员重算（旁路——迭代多轮）
    assert wrapped_rj.calls > rj_calls  # 组员重算
    assert consumer.calls == consumer_calls  # 组外下游命中（跳过）
    assert serialize(second) == serialize(first)  # 双跑同果（字节级——R1 口径）


class _BypassProducer:
    """产泥 stub（计数）：WATER in+in_r→out+sludge_out（增益<1 保收敛）。"""

    def __init__(self) -> None:
        self.manifest = _stub_manifest(
            "producer",
            (
                ("in", "WATER", "IN"),
                ("in_r", "WATER", "IN"),
                ("out", "WATER", "OUT"),
                ("sludge_out", "SLUDGE", "OUT"),
            ),
        )
        self.calls = 0

    def compute(self, ctx: object) -> object:
        """q=主入流+回流；产泥=线性投影。"""
        from waterprint.contracts.flow import WaterFlow
        from waterprint.contracts.ports import PortRef
        from waterprint.contracts.quality import WaterQuality
        from waterprint.contracts.sludge import SludgeFlow
        from waterprint.contracts.unit_api import UnitResult

        self.calls += 1
        main = ctx.inflows.get(PortRef(ctx.unit_id, "in"))  # type: ignore[attr-defined]
        recycle = ctx.inflows.get(PortRef(ctx.unit_id, "in_r"))  # type: ignore[attr-defined]
        q_main = main.q_avg_daily if main is not None else 0.0
        q_recycle = recycle.q_avg_daily if recycle is not None else 0.0
        q = q_main + q_recycle
        out, sludge = PortRef(ctx.unit_id, "out"), PortRef(ctx.unit_id, "sludge_out")
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


def test_default_cache_singleton_and_clear() -> None:
    """进程级单例恒同对象；clear 清空（测试隔离与批 11 oracle 冷跑纪律）。"""
    from waterprint.graph.cache import default_cache

    first = default_cache()
    second = default_cache()
    assert first is second
    first.clear()
    assert len(first) == 0
