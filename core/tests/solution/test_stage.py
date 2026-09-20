"""joint_enumeration 部件镜像测试：stage/ranking/diagnose（B4-3 TDD 序 2）。

输入:  waterprint.solution.joint_enumeration 三部件公开符号
输出:  冻结前缀传播/降权标记排序/除零权重重分配/网格放宽契约断言
       （定稿件 W10/W12/N6/W8——终裁定稿口径）
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas
import pytest

_stage = importlib.import_module("waterprint.solution.joint_enumeration.stage")
_ranking = importlib.import_module("waterprint.solution.joint_enumeration.ranking")
_diagnose = importlib.import_module("waterprint.solution.joint_enumeration.diagnose")

stage_proxies = getattr(_stage, "stage_proxies", None)
energy_estimate = getattr(_stage, "energy_estimate", None)
plant_objective = getattr(_ranking, "plant_objective", None)
degraded_aware_order = getattr(_ranking, "degraded_aware_order", None)
relax_grid_specs = getattr(_diagnose, "relax_grid_specs", None)
stage_conflicts = getattr(_diagnose, "stage_conflicts", None)

pytestmark = pytest.mark.skipif(
    None in (stage_proxies, energy_estimate, plant_objective, degraded_aware_order,
             relax_grid_specs, stage_conflicts),
    reason="实现未就绪：solution.joint_enumeration 部件（B4-3）",
)


class _Sink:
    """空迹收集器（结构满足 TraceSink 协议）。"""

    def record(self, node: Any) -> None:
        """丢弃记录。"""


# ── stage：阶段代理分（裕度/能耗双分量归一+份额）────────────────────


def _frame(rows: list[dict[str, float]]) -> pandas.DataFrame:
    return pandas.DataFrame(rows)


def test_stage_proxy_margin_only_full_share() -> None:
    """share=1：代理分=裕度归一（margin_min 越大越好，min-max 归一到 0~1）。"""
    frame = _frame([
        {"margin_min": 1.0, "e_pump": 30.0},
        {"margin_min": 2.0, "e_pump": 20.0},
        {"margin_min": 3.0, "e_pump": 10.0},
    ])
    proxies = stage_proxies(frame, (0, 1, 2), 1.0, 0.0)  # type: ignore[misc]
    assert proxies[0] == pytest.approx(0.0)
    assert proxies[1] == pytest.approx(1 / 2)
    assert proxies[2] == pytest.approx(1.0)


def test_stage_proxy_energy_component_low_is_better() -> None:
    """share=0：代理分=能耗归一（估计值越小越好——e_* 三键求和含冻结基线）。"""
    frame = _frame([
        {"margin_min": 1.0, "e_aeration": 10.0, "e_pump": 5.0},
        {"margin_min": 1.0, "e_aeration": 0.0, "e_pump": 0.0},
    ])
    proxies = stage_proxies(frame, (0, 1), 0.0, 5.0)  # type: ignore[misc]
    # 行0 估计=10+5+5=20（最差→0），行1 估计=0+0+5=5（最好→1）
    assert proxies[0] == pytest.approx(0.0)
    assert proxies[1] == pytest.approx(1.0)


def test_stage_proxy_degenerate_spread_is_midpoint() -> None:
    """无区分度（全同行）：分量取中位 1/2（禁编造区分度——确定性口径）。"""
    frame = _frame([{"margin_min": 2.0, "e_pump": 1.0}] * 2)
    proxies = stage_proxies(frame, (0, 1), 1.0, 0.0)  # type: ignore[misc]
    assert proxies[0] == pytest.approx(1 / 2)
    assert proxies[1] == pytest.approx(1 / 2)


def test_energy_estimate_sums_b4_2a_keys() -> None:
    """能耗估计=e_aeration/e_pump/e_stir 三键和+冻结前缀基线贡献（B1 口径）。"""
    assert energy_estimate({"e_aeration": 1.0, "e_pump": 2.0, "e_stir": 3.0, "x": 9.0}, 4.0) == pytest.approx(10.0)  # type: ignore[misc]


def test_stage_context_prefix_frozen() -> None:
    """StageContext 冻结前缀：不可变 dataclass（frozen 防中途改值）。"""
    from waterprint.contracts.condition import FlowCase, OperatingCondition

    ctx = _stage.StageContext(
        unit_id="u2",
        prefix={"u1": {"n": 2.0}},
        condition=OperatingCondition(flow_case=FlowCase.DESIGN, offline_unit=None),
        baseline_energy=0.0,
    )
    with pytest.raises(Exception):
        ctx.unit_id = "u3"  # type: ignore[misc]
    assert ctx.prefix["u1"]["n"] == 2.0


# ── ranking：目标函数（归一化+除零权重重分配 N6）───────────────────


def test_objective_lower_cost_better() -> None:
    """基线归一：value/base 加权和，越小越好（opex/energy/carbon 同向）。"""
    baseline = {"opex": 100.0, "energy": 50.0, "carbon": 2.0}
    weights = {"opex": 0.5, "energy": 0.3, "carbon": 0.2}
    metrics = [
        {"opex": 100.0, "energy": 50.0, "carbon": 2.0},
        {"opex": 50.0, "energy": 50.0, "carbon": 2.0},
    ]
    scores = plant_objective(metrics, baseline, weights)  # type: ignore[misc]
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == pytest.approx(1.0 - 0.5 * 1 / 2)


def test_objective_zero_baseline_redistributes_weight() -> None:
    """N6：基准值 0/缺失 → 该键权重重分配至其余键（不除零不编造）。"""
    baseline = {"opex": 0.0, "energy": 50.0, "carbon": 2.0}
    weights = {"opex": 0.5, "energy": 0.3, "carbon": 0.2}
    metrics = [{"opex": 123.0, "energy": 25.0, "carbon": 2.0}]
    scores = plant_objective(metrics, baseline, weights)  # type: ignore[misc]
    # 活跃键 energy/carbon 权重 0.3/0.2 → 归一化分母 0.5；energy 减半
    assert scores[0] == pytest.approx((0.3 * 1 / 2 + 0.2 * 1.0) / 0.5)


def test_objective_missing_metric_value_redistributes() -> None:
    """N6 组合面：单组合缺指标值（sparse）→ 该键权重当场重分配。"""
    baseline = {"opex": 100.0, "energy": 50.0, "carbon": 2.0}
    weights = {"opex": 0.5, "energy": 0.3, "carbon": 0.2}
    metrics = [{"opex": 100.0, "energy": 50.0}]  # carbon 缺席
    scores = plant_objective(metrics, baseline, weights)  # type: ignore[misc]
    assert scores[0] == pytest.approx(1.0)  # 活跃键全等基线→1.0


def test_objective_all_missing_is_zero() -> None:
    """全键缺席：score=0 恒等（无区分度，排序落次序键——诚实降级）。"""
    scores = plant_objective([{}], {"opex": 0.0}, {"opex": 1.0})  # type: ignore[misc]
    assert scores[0] == 0.0


def test_degraded_aware_order_pure_before_degraded() -> None:
    """W10：同分 sensitivity_degraded 排纯可行之后（不剔除）。"""
    scored = [
        (1.0, True, ("b",)),   # 同分但 degraded → 排后
        (1.0, False, ("z",)),  # 纯可行
        (0.5, True, ("a",)),   # 分更低 → 最前（分数优先于降权标记）
    ]
    order = degraded_aware_order(scored)  # type: ignore[misc]
    assert order == (2, 1, 0)


def test_degraded_aware_order_deterministic_tie_break() -> None:
    """同分同标记：参数键字典序稳定（确定性全序——UI 不抖动）。"""
    scored = [
        (1.0, False, ("b", 2.0)),
        (1.0, False, ("a", 9.0)),
    ]
    order = degraded_aware_order(scored)  # type: ignore[misc]
    assert order == (1, 0)


# ── diagnose：分层最小冲突集（首空级既有 diagnose+末空级放宽）──────


def test_stage_conflicts_wraps_existing_diagnose_with_prefix() -> None:
    """首空级：以冻结前缀为上下文调既有 diagnose_infeasibility（前缀注记在载荷）。"""
    matrix = pandas.DataFrame(
        {"c1": [False, False], "c2": [True, False]},
    )
    constraints = {"c1": {"expression": "x >= 1", "source": "kb:c1"},
                   "c2": {"expression": "y <= 2", "source": "kb:c2"}}
    grid = _simple_grid()
    payload = stage_conflicts(matrix, constraints, grid, {"u1": {"n": 2.0}})  # type: ignore[misc]
    assert payload["frozen_prefix"] == {"u1": {"n": 2.0}}
    assert payload["minimal_conflicts"]  # 非空冲突集（c1 单独即冲突：全行 False）
    assert any(set(conflict) == {"c1"} for conflict in payload["minimal_conflicts"])
    assert payload["fail_counts"]["c1"] == 2


def test_relax_grid_specs_widens_range_only() -> None:
    """末空级放宽：range 域两侧各扩 (factor−1)/2 比例（f=2 → 域宽翻倍）；
    values 离散档（manifest 网格形态）无法连续放宽=原样保留+诚实注记。"""
    specs = [
        {"field_id": "n", "range": {"min": 2.0, "max": 6.0}, "step": 1.0},
        {"field_id": "t", "values": [4.0, 6.0, 8.0]},
    ]
    relaxed = relax_grid_specs(specs, 2.0)  # type: ignore[misc]
    assert relaxed[0]["range"] == {"min": 0.0, "max": 8.0}  # 2−2=0 / 6+2=8
    assert relaxed[0]["step"] == 1.0
    assert relaxed[1] == specs[1]  # 离散档原样


def _simple_grid() -> Any:
    """两行一维网格（诊断统计源——grid 形面）。"""
    from waterprint.solution.grid import build_grid

    return build_grid([{"field_id": "n", "values": [2.0, 3.0]}], guard_base=False)
