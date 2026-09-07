"""32 包 N=1 退化断言电池（批 13-D 收口件——task-13A §七沿承）。

输入:  units_lib 全 32 包包内 test_compute 权威夹具（_params/_ctx——
       golden 主算例）+ registry apply/apply_batch 双正门
输出:  位级断言全绿（golden trace 逐行「标量 apply vs N=1 数组
       apply_batch」IEEE 位恒等+形状合约消费面断言）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批 13-D；task-13-design §三、task-13D-batch-plan §一/§二）
#
# 【电池面】task-13A §七「32 包 N=1 退化断言电池=批 D 收口件」兑现：
#   ①退化面——32 包 golden 主算例 trace 逐行（录音 sink 捕获绑定），
#   标量正门 apply vs 批量正门 apply_batch（N=1 装箱）struct pack 逐位
#   比对恒等（n1_scalars 快路径汇合 _apply_scalar 同一私核的机器锚，
#   探针 P3 模式全库泛化——12 已重写包为双正门消费实证，20 标量包为
#   将来向量化等价性前置证据）；②形状合约面——apply_batch 返回形状
#   （N=1→(1,)/N>1→(N,)）+非等长/零长/二维/非数值 dtype 拒绝面
#   （A2-03/G1-03 接口合约的消费侧断言）。
# 【KZ/NS/ST 覆盖】mine_water/ziwai[KZ-F10]/sludge/nongsuo[NS-F3]/
#   sludge/shusong[ST-F7] 三处非重写面 max 式在本电池 golden 行内
#   位级对拍（±0 平局域外详注见 formulas_kernel R5——引擎正门统一
#   承接的机器层）。
# 【夹具纪律】包内 tests 无包语义——importlib 路径加载（生成器
#   baseline_gen.load_pkg_tests 同款口径），零跨测试件 import；
#   _template 为规格说明件零样板不入电池。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib.util
import struct
from pathlib import Path

import numpy
import pytest

from waterprint.registry import formulas
from waterprint.units_lib import discover_units
from waterprint.units_lib._unit_compute import _vec

_PACKAGES: tuple[str, ...] = (
    "conveyance/jipeishuijing",
    "conveyance/jishuijing",
    "conveyance/peishuijing",
    "conveyance/peishuiqu",
    "mine_water/chenshachi",
    "mine_water/cifenli",
    "mine_water/gaomidu",
    "mine_water/input",
    "mine_water/ningjiao",
    "mine_water/tiaojiechi",
    "mine_water/vxinglvchi",
    "mine_water/ziwai",
    "municipal/aao",
    "municipal/bashi_jiliangcao",
    "municipal/cass",
    "municipal/chenshachi",
    "municipal/chuchenchi",
    "municipal/cugeshan",
    "municipal/erchunchi",
    "municipal/gaomidu",
    "municipal/tiaojiechi",
    "municipal/vxinglvchi",
    "municipal/wushui_tisheng",
    "municipal/xigeshan",
    "municipal/ziwai",
    "sludge/bengzhan",
    "sludge/ganhua",
    "sludge/hebing",
    "sludge/nongsuo",
    "sludge/shusong",
    "sludge/tuoshui",
    "sludge/xiaohua",
)
_CORE = Path(__file__).resolve().parents[2] / "waterprint"


class _Recorder:
    """录音 sink：TraceNodeSpec 快照按序收存（golden 路径绑定源）。"""

    def __init__(self) -> None:
        self.nodes: list[object] = []

    def record(self, node: object) -> None:
        self.nodes.append(node)


def _golden_trace(package: str) -> list[object]:
    """单包 golden 主算例 trace 行（包内 _params/_ctx 权威夹具驱动）。"""
    path = _CORE / "units_lib" / package / "tests" / "test_compute.py"
    spec = importlib.util.spec_from_file_location(f"_b13d_{package.replace('/', '_')}", path)
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recorder = _Recorder()
    ctx = module._ctx(module._params())  # noqa: SLF001  # 包内权威夹具私有面（生成器 load_pkg_tests 同款口径）
    replaced = type(ctx)(
        unit_id=ctx.unit_id,
        inflows=ctx.inflows,
        inqualities=ctx.inqualities,
        params=ctx.params,
        condition=ctx.condition,
        assumptions=ctx.assumptions,
        trace=recorder,
    )
    module.make_unit().compute(replaced)
    assert recorder.nodes, f"{package}: golden 路径零公式行"
    return recorder.nodes


@pytest.mark.parametrize("package", _PACKAGES)
def test_n1_degenerate_golden_rows(package: str) -> None:
    """退化面：golden trace 逐行标量 apply vs N=1 apply_batch 位级恒等。"""
    for node in _golden_trace(package):
        bindings = {k: float(v) for k, v in node.bindings.items()}
        ctx_pair = (node.unit_id, node.condition_key)
        scalar = formulas.apply(node.formula_id, dict(bindings), ctx_pair)
        batched = formulas.apply_batch(node.formula_id, {k: _vec(v) for k, v in bindings.items()}, ctx_pair)
        assert batched.shape == (1,)  # G1-03 形状合约（N=1）
        assert struct.pack("=d", float(batched[0])) == struct.pack("=d", scalar), (
            f"{package}/{node.formula_id}: {scalar!r} vs {float(batched[0])!r}"
        )


def test_n1_battery_corpus_shape() -> None:
    """电池覆盖面：32 包全列（KZ/NS/ST 三 max 包在列——机器层承接锚）。"""
    assert len(_PACKAGES) == 32
    for required in ("mine_water/ziwai", "sludge/nongsuo", "sludge/shusong"):
        assert required in _PACKAGES


def test_shape_contract_n_greater_than_one() -> None:
    """形状合约（A2-03）：N>1 等长绑定 → shape (N,)。"""
    discover_units()
    count = 3
    bindings = {
        symbol: numpy.linspace(0.2, 0.9, count)
        for symbol in ("q_avg_daily", "bod5_in", "ns", "x_mlss")
    }
    outcome = formulas.apply_batch("AO-F1", bindings, ("b13d_battery", "design"))
    assert outcome.shape == (count,)
    assert bool(numpy.isfinite(outcome).all())


def test_shape_contract_n1_returns_singleton() -> None:
    """形状合约（G1-03）：N=1 绑定 → shape (1,)（快路径单点装箱）。"""
    discover_units()
    bindings = {
        "q_avg_daily": numpy.asarray([0.4]),
        "bod5_in": numpy.asarray([200.0]),
        "ns": numpy.asarray([0.1]),
        "x_mlss": numpy.asarray([4000.0]),
    }
    outcome = formulas.apply_batch("AO-F1", bindings, ("b13d_battery", "design"))
    assert outcome.shape == (1,)
    assert formulas.apply(
        "AO-F1",
        {"q_avg_daily": 0.4, "bod5_in": 200.0, "ns": 0.1, "x_mlss": 4000.0},
        ("b13d_battery", "design"),
    ) == float(outcome[0])


def test_shape_contract_reject_faces() -> None:
    """形状合约拒绝面：非等长/零长/二维/非数值 dtype → InvalidFormulaError。"""
    discover_units()
    good = {
        "q_avg_daily": numpy.asarray([0.4]),
        "bod5_in": numpy.asarray([200.0]),
        "ns": numpy.asarray([0.1]),
        "x_mlss": numpy.asarray([4000.0]),
    }
    mismatched = {**good, "ns": numpy.asarray([0.1, 0.2])}
    empty = {**good, "ns": numpy.asarray([], dtype=numpy.float64)}
    two_dim = {**good, "ns": numpy.asarray([[0.1]], dtype=numpy.float64)}
    object_dtype = {**good, "ns": numpy.asarray(["x"], dtype=object)}
    for bindings in (mismatched, empty, two_dim, object_dtype):
        with pytest.raises(formulas.InvalidFormulaError, match="批量"):
            formulas.apply_batch("AO-F1", bindings, ("b13d_battery", "design"))
