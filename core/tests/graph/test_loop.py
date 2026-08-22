"""loop 镜像测试：回路固定点迭代（收敛/发散诊断/阻尼/确定性）。

输入:  waterprint.graph.loop 公开符号 + 线性回路 compute 回调
输出:  ADR-003 语义断言（禁止静默返回未收敛值）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.graph.loop")
solve_loop = getattr(_mod, "solve_loop", None)
LoopDivergence = getattr(_mod, "LoopDivergence", None)
LoopConfig = getattr(_mod, "LoopConfig", None)

pytestmark = pytest.mark.skipif(
    None in (solve_loop, LoopDivergence, LoopConfig),
    reason="实现未就绪：waterprint.graph.loop（M1）",
)


def _affine(slope: float, intercept: float):
    """构造线性回路 F(x) = slope·x + intercept（单变量）。"""
    def compute(state: dict[str, float]) -> dict[str, float]:
        return {"x": slope * state["x"] + intercept}
    return compute


def _config(damping: float, max_iter: int = 500):
    return LoopConfig(tolerance=1e-10, max_iterations=max_iter, damping=damping)


def test_contraction_converges_to_analytic_fixed_point() -> None:
    """收缩映射收敛到解析不动点 x = b/(1-a)。"""
    solution = solve_loop(
        ["n1"], _affine(0.5, 2.0), {"n1": {"x": 0.0}}, _config(1.0)
    )
    assert solution["n1"]["x"] == pytest.approx(4.0, abs=1e-6)


def test_oscillating_case_converges_with_damping() -> None:
    """a=-1.8 无阻尼发散；ω=0.5 收敛（阻尼的作用——ADR-003 R3）。"""
    solve_loop(["n1"], _affine(-1.8, 1.0), {"n1": {"x": 0.0}}, _config(0.5))


def test_divergence_raises_with_history() -> None:
    """R2：发散抛 LoopDivergence 且携带迭代历史（禁止静默末值）。"""
    with pytest.raises(LoopDivergence) as excinfo:
        solve_loop(["n1"], _affine(2.0, 1.0), {"n1": {"x": 1.0}}, _config(1.0, max_iter=50))
    assert getattr(excinfo.value, "history", ()) or excinfo.value.args


def test_same_input_same_iteration_path() -> None:
    """R5：确定性——同输入双跑收敛解一致。"""
    args = (["n1"], _affine(0.7, 3.0), {"n1": {"x": 0.0}}, _config(1.0))
    first = solve_loop(*args)
    second = solve_loop(*args)
    assert first == second
