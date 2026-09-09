"""FD 可行域引导（design_map）契约测试：轴声明/预算/产物/双源/对拍（PD5 四类）。

输入:  waterprint.solution.design_map 公开符号 + app.run_design_map 装配面
输出:  先红后绿契约断言（新文件——锁面笔收束）
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

pd = pytest.importorskip("pandas")
numpy = pytest.importorskip("numpy")

_dm = importlib.import_module("waterprint.solution.design_map")
derive_step = getattr(_dm, "derive_step", None)
axis_point_budget = getattr(_dm, "axis_point_budget", None)
resolve_axes = getattr(_dm, "resolve_axes", None)
ensure_budget = getattr(_dm, "ensure_budget", None)
axis_mappings = getattr(_dm, "axis_mappings", None)
build_design_map = getattr(_dm, "build_design_map", None)
feasible_mask = getattr(_dm, "feasible_mask", None)
widest_segment = getattr(_dm, "widest_segment", None)
DesignMapTooLarge = getattr(_dm, "DesignMapTooLarge", None)
InvalidDesignMapError = getattr(_dm, "InvalidDesignMapError", None)
_grid = importlib.import_module("waterprint.solution.grid")
build_grid = getattr(_grid, "build_grid", None)
_constraints = importlib.import_module("waterprint.solution.constraints")
apply_constraints = getattr(_constraints, "apply_constraints", None)

pytestmark = pytest.mark.skipif(
    None in (derive_step, axis_point_budget, resolve_axes, ensure_budget,
             axis_mappings, build_design_map, feasible_mask, widest_segment,
             DesignMapTooLarge, InvalidDesignMapError, build_grid,
             apply_constraints),
    reason="实现未就绪：waterprint.solution.design_map（FD 批）",
)

_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"

# PD8 跨语言黄金值：与 webapp deriveStep node 测试共享同一组期望
# （同一 range→同一 step——防 Python/JS 派生漂移；双向注释引用）。
_GOLDEN_STEPS: tuple[tuple[tuple[float, float], float], ...] = (
    ((0.05, 0.15), 0.009999999999999998),  # aao ns（浮点尾差面——JS 同值）
    ((3500.0, 4500.0), 100.0),  # aao x_mlss（精确面）
    ((7.0, 10.0), 0.3),  # vxinglvchi v_filter（精确面）
)


def _spec(field_id: str, low: float, high: float, label: str | None = "标签") -> Any:
    from waterprint.contracts.manifest import ParamSpec

    return ParamSpec(
        field_id=field_id, dim="DIMENSIONLESS", default=low,
        range=(low, high), label_zh=label,
    )


# ── 一、轴声明与步长（PD1/PD8）──────────────────────────────────────


@pytest.mark.parametrize(("span", "expected"), _GOLDEN_STEPS)
def test_derive_step_golden(span: tuple[float, float], expected: float) -> None:
    """PD8 黄金值互锁：(max-min)/10——与 webapp deriveStep 同式同期望。"""
    assert derive_step(span) == expected  # type: ignore[misc]


def test_axis_point_budget_inclusive_mirror() -> None:
    """P1-5 同式预算：闭区间含首末点（arange 镜像——非整除上界档同型）。"""
    assert axis_point_budget((0.0, 10.0), 1.0) == 11  # type: ignore[misc]
    assert axis_point_budget((0.5, 2.0), 0.5) == 4  # type: ignore[misc]
    assert axis_point_budget((0.0, 1.0), 0.6) == 3  # type: ignore[misc]（钳制前上界预算）


def test_resolve_axes_default_step_and_metadata() -> None:
    """缺省 range=manifest、step=派生、dim/label_zh 透传（grid_fields 同源）。"""
    resolved = resolve_axes([_spec("ns", 0.05, 0.15)], [{"field_id": "ns"}])  # type: ignore[misc]
    assert len(resolved) == 1
    axis = resolved[0]
    assert axis.field_id == "ns"
    assert axis.dim == "DIMENSIONLESS"
    assert axis.label_zh == "标签"
    assert axis.minimum == 0.05
    assert axis.maximum == 0.15
    assert axis.step == derive_step((0.05, 0.15))  # type: ignore[misc]


def test_resolve_axes_two_axes_declaration_order_kept() -> None:
    """声明序保持（产物 axes/mask 序=用户声明序——PD3 消费契约）。"""
    resolved = resolve_axes(  # type: ignore[misc]
        [_spec("x_mlss", 3500.0, 4500.0), _spec("ns", 0.05, 0.15)],
        [{"field_id": "ns"}, {"field_id": "x_mlss", "step": 200.0}],
    )
    assert [axis.field_id for axis in resolved] == ["ns", "x_mlss"]
    assert resolved[1].step == 200.0  # step 覆盖生效


def test_resolve_axes_range_override_containment() -> None:
    """用户 range 覆盖：⊆manifest 合法；越界 fail-closed 拒（PD1）。"""
    resolved = resolve_axes(  # type: ignore[misc]
        [_spec("ns", 0.05, 0.15)], [{"field_id": "ns", "range": {"min": 0.06, "max": 0.1}}]
    )
    assert (resolved[0].minimum, resolved[0].maximum) == (0.06, 0.1)
    with pytest.raises(InvalidDesignMapError, match="越界"):  # type: ignore[misc]
        resolve_axes(  # type: ignore[misc]
            [_spec("ns", 0.05, 0.15)],
            [{"field_id": "ns", "range": {"min": 0.04, "max": 0.1}}],
        )


@pytest.mark.parametrize(
    ("axes", "match"),
    [
        ([], "1~2"),
        ([{"field_id": "a"}, {"field_id": "b"}, {"field_id": "c"}], "1~2"),
        ([{"field_id": "ghost"}], "不在该单元"),
        ([{"field_id": "ns"}, {"field_id": "ns"}], "重复"),
        ([{"field_id": ""}], "field_id"),
        ([{"field_id": "ns", "step": 0.0}], "step 须 > 0"),
        ([{"field_id": "ns", "step": -0.1}], "step 须 > 0"),
        ([{"field_id": "ns", "step": float("inf")}], "非有限"),
        ([{"field_id": "ns", "range": {"min": 0.1, "max": 0.1}}], "min<max"),
        ([{"field_id": "ns", "range": {"min": 0.2, "max": 0.1}}], "min<max"),
        ([{"field_id": "ns", "range": 5.0}], "range 覆盖须为对象"),
    ],
)
def test_resolve_axes_rejects(axes: list[Mapping[str, object]], match: str) -> None:
    """轴声明非法族（GR-11：消息可定位）。"""
    with pytest.raises(InvalidDesignMapError, match=match):  # type: ignore[misc]
        resolve_axes([_spec("ns", 0.05, 0.15)], axes)  # type: ignore[misc]


def test_resolve_axes_requires_manifest_range() -> None:
    """无 range 参数（grid 档/无域声明）不可作轴——无扫描基准 fail-closed。"""
    from waterprint.contracts.manifest import ParamSpec

    spec = ParamSpec(field_id="n", dim="DIMENSIONLESS", default=4.0, grid=(2.0, 3.0))
    with pytest.raises(InvalidDesignMapError, match="无 range 声明可扫描"):  # type: ignore[misc]
        resolve_axes([spec], [{"field_id": "n"}])  # type: ignore[misc]


# ── 二、护栏（PD4/P1-5：解析期拦截）────────────────────────────────


def test_ensure_budget_over_limit_rejected() -> None:
    """超 max_points → DesignMapTooLarge（消息形态照抄 GridTooLarge 泛化口径）。"""
    resolved = resolve_axes(  # type: ignore[misc]
        [_spec("ns", 0.05, 0.15)], [{"field_id": "ns", "step": 0.001}]
    )  # 101 点
    with pytest.raises(DesignMapTooLarge, match="超护栏"):  # type: ignore[misc]
        ensure_budget(resolved, {"solution.design_map.max_points": 100.0})  # type: ignore[misc]


def test_ensure_budget_default_2500_allows_full_scan() -> None:
    """缺省 2500：50×50 满配扫描放行（registry 伴生件注册键生效面）。"""
    resolved = resolve_axes(  # type: ignore[misc]
        [_spec("a", 0.0, 4.9), _spec("b", 0.0, 4.9)],
        [{"field_id": "a", "step": 0.1}, {"field_id": "b", "step": 0.1}],
    )  # 50×50=2500
    ensure_budget(resolved, {})  # type: ignore[misc]


@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_ensure_budget_nonpositive_override_rejected(bad: float) -> None:
    """0/负覆盖值域守卫（挂账硬化裁量本批兑现——全拒陷阱显式化）。"""
    resolved = resolve_axes([_spec("ns", 0.05, 0.15)], [{"field_id": "ns"}])  # type: ignore[misc]
    with pytest.raises(InvalidDesignMapError, match=">= 1"):  # type: ignore[misc]
        ensure_budget(resolved, {"solution.design_map.max_points": bad})  # type: ignore[misc]


# ── 三、双源可行掩码（PD2/P0-2 终裁核心）──────────────────────────


def test_feasible_mask_dual_source() -> None:
    """双源=约束通过 ∧ 行非 NaN：单侧真不构成可行。"""
    frame = pd.DataFrame({"nan_flag": [False, False, True, True]})
    matrix = pd.DataFrame({"c": [True, False, True, False]})
    mask = feasible_mask(frame, matrix)  # type: ignore[misc]
    assert mask.tolist() == [True, False, False, False]


def test_feasible_mask_nan_infeasible_without_constraints() -> None:
    """「全绿」≠「无信息」：空约束集下 NaN 域拒行仍不可行（P0-2 终裁）。"""
    frame = pd.DataFrame({"nan_flag": [False, True, False]})
    matrix = pd.DataFrame(index=[0, 1, 2])  # 零列=全真（GR-14 空集语义）
    mask = feasible_mask(frame, matrix)  # type: ignore[misc]
    assert mask.tolist() == [True, False, True]


# ── 四、产物形态（PD3：全字段+确定性+段/掩码几何）─────────────────


def _one_d_product() -> Any:
    resolved = resolve_axes([_spec("v", 0.0, 10.0)], [{"field_id": "v", "step": 1.0}])  # type: ignore[misc]
    grid = build_grid(axis_mappings(resolved), guard_base=False)  # type: ignore[misc]
    mask = numpy.zeros(grid.total, dtype=bool)
    mask[2:5] = True  # 段 [2,4]
    mask[7:9] = True  # 段 [7,8]
    return build_design_map("u", grid, mask, resolved, "degraded"), mask  # type: ignore[misc]


def test_product_1d_full_fields_and_determinism() -> None:
    """1D 全字段（axes/stats/axis_values/segments/coverage/diagnosis）+双跑字节同。"""
    product, mask = _one_d_product()
    payload = product.payload()
    assert payload["unit_id"] == "u"
    assert payload["axes"] == [{
        "field_id": "v", "dim": "DIMENSIONLESS", "label_zh": "标签",
        "range": {"min": 0.0, "max": 10.0}, "step": 1.0, "points": 11,
    }]
    assert payload["stats"] == {
        "total": 11, "feasible": 5, "infeasible": 6, "feasible_ratio": 5 / 11,
    }
    assert payload["axis_values"] == [[float(i) for i in range(11)]]
    assert payload["segments"] == [{"start": 2.0, "end": 4.0}, {"start": 7.0, "end": 8.0}]
    assert payload["mask"] is None
    assert payload["constraint_coverage"] == "degraded"
    diagnosis = payload["diagnosis"]
    assert diagnosis["feasible_ratio"] == 5 / 11
    assert diagnosis["axes"] == [{
        "field_id": "v", "magnitude": 1.0,
        "widest_segment": {"start": 2.0, "end": 4.0, "centroid": 3.0},
        "recommended_value": 3.0,
    }]
    # R2 双跑字节同（常驻断言口径：sort_keys）
    again, _ = _one_d_product()
    assert json.dumps(payload, sort_keys=True) == json.dumps(again.payload(), sort_keys=True)


def test_product_no_feasible_segment_none_semantics() -> None:
    """R4 不编造：无可行段=逐轴 None + feasible_ratio=0。"""
    resolved = resolve_axes([_spec("v", 0.0, 1.0)], [{"field_id": "v"}])  # type: ignore[misc]
    grid = build_grid(axis_mappings(resolved), guard_base=False)  # type: ignore[misc]
    product = build_design_map(  # type: ignore[misc]
        "u", grid, numpy.zeros(grid.total, dtype=bool), resolved, "full"
    )
    payload = product.payload()
    assert payload["stats"]["feasible"] == 0
    assert payload["segments"] == []
    assert payload["diagnosis"]["feasible_ratio"] == 0.0
    assert payload["diagnosis"]["axes"] == [{
        "field_id": "v", "magnitude": None, "widest_segment": None,
        "recommended_value": None,
    }]


def test_product_2d_declared_order_orientation() -> None:
    """2D：mask=声明序 row-major（grid 字典序≠声明序时转置归位）+诊断投影。"""
    # 声明序 (b, a)；字典序 (a, b)——b 3 值 × a 2 值，shape=(2,3)
    resolved = resolve_axes(  # type: ignore[misc]
        [_spec("a", 10.0, 20.0), _spec("b", 2.0, 4.0)],
        [{"field_id": "b", "step": 1.0}, {"field_id": "a", "step": 10.0}],
    )
    grid = build_grid(axis_mappings(resolved), guard_base=False)  # type: ignore[misc]
    assert grid.fields == ("a", "b")  # build_grid R2 字典序
    rows = [(row["a"], row["b"]) for row in grid.array]
    assert rows == [(10.0, 2.0), (10.0, 3.0), (10.0, 4.0),
                    (20.0, 2.0), (20.0, 3.0), (20.0, 4.0)]
    mask = numpy.array([False, True, False, False, True, False])  # (a10,b3)/(a20,b3)
    product = build_design_map("u", grid, mask, resolved, "full")  # type: ignore[misc]
    payload = product.payload()
    assert payload["axis_values"] == [[2.0, 3.0, 4.0], [10.0, 20.0]]  # 声明序 (b, a)
    assert payload["segments"] is None
    assert payload["mask"] == [[0, 0], [1, 1], [0, 0]]  # 行=b 值、列=a 值
    axes_diagnosis = payload["diagnosis"]["axes"]
    assert axes_diagnosis[0] == {  # b 轴投影（任一 a 补全可行）→ [3,3]
        "field_id": "b", "magnitude": 0.0,
        "widest_segment": {"start": 3.0, "end": 3.0, "centroid": 3.0},
        "recommended_value": 3.0,
    }
    assert axes_diagnosis[1] == {  # a 轴投影 → [10,20]
        "field_id": "a", "magnitude": 5.0,
        "widest_segment": {"start": 10.0, "end": 20.0, "centroid": 15.0},
        "recommended_value": 15.0,
    }


def test_widest_segment_first_on_tie_and_none() -> None:
    """等宽并列取首段（确定性）；空掩码=None。"""
    values = [0.0, 1.0, 2.0, 3.0, 4.0]
    tie = widest_segment(values, numpy.array([True, True, False, True, True]))  # type: ignore[misc]
    assert tie == {"start": 0.0, "end": 1.0, "centroid": 0.5}
    assert widest_segment(values, numpy.zeros(5, dtype=bool)) is None  # type: ignore[misc]


# ── 五、app 正门端到端（PD1~PD3 装配面+对拍）──────────────────────


def _fd_project(unit_id: str) -> Any:
    from waterprint.contracts.project_schema import DesignState, Metadata, ProjectFile

    return ProjectFile(
        format_version="1.0",
        design=DesignState(
            nodes={
                "inlet": {
                    "kind": "municipal_input",
                    "q_avg_daily": 34760.7 / 86400,
                    "kz": 1.4,
                    "CODCR": 400.0, "BOD5": 200.0, "SS": 250.0,
                    "NH3N": 26.0, "TN": 43.0, "TP": 6.5,
                },
                unit_id: {},
            },
            edges=[{
                "src": {"unit_id": "inlet", "port_id": "out"},
                "dst": {"unit_id": unit_id, "port_id": "in"},
            }],
        ),
        metadata=Metadata(
            format_version="1.0", content_hash="",
            engine_version="fd", data_version="fd",
        ),
    )


def _fd_env() -> Any:
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients

    lib = load_coefficients(_DATA)
    return RunEnv(
        engine_version="fd", data_version=f"coefficients@{lib.data_version}",
        assumptions={}, coefficients=lib, price_book={},
        trace_sink=None, engine_params={},
    )


def _conditions() -> Any:
    from waterprint.contracts.condition import build_condition_set

    return build_condition_set([])


def test_run_design_map_1d_degraded_full_scan() -> None:
    """app 正门 1D：缺省步长全距扫描（11 点>7^1 不受枚举基数约束——PD4 独立）。"""
    from waterprint.app import run_design_map
    from waterprint.solution.design_map import DesignMapOptions

    product = run_design_map(
        _fd_project("municipal_aao"), "municipal_aao", _conditions(), _fd_env(),
        DesignMapOptions(axes=[{"field_id": "ns"}], fixed_params={}),
    )
    payload = product.payload()
    assert payload["constraint_coverage"] == "degraded"
    assert payload["stats"]["total"] == 11
    assert payload["axes"][0]["field_id"] == "ns"
    assert payload["axes"][0]["label_zh"] == "BOD5 污泥负荷"
    assert payload["axes"][0]["points"] == 11
    again = run_design_map(
        _fd_project("municipal_aao"), "municipal_aao", _conditions(), _fd_env(),
        DesignMapOptions(axes=[{"field_id": "ns"}], fixed_params={}),
    )
    assert json.dumps(payload, sort_keys=True) == json.dumps(again.payload(), sort_keys=True)


def test_run_design_map_constraint_face_vs_enumeration_pipeline() -> None:
    """对拍（无第二判据证明）：run_design_map 可行面 == 枚举面原语手工装配。

    手工侧=build_grid+enumerate_solutions+apply_constraints（枚举管线
    原语）+ feasible_mask 双源合成；两侧任何判据分叉即红。
    """
    from waterprint.app import assemble, run_design_map, run_full_calc
    from waterprint.app_enumeration import UpstreamSource, upstream_context
    from waterprint.solution.diagnose import diagnose_infeasibility

    constraints = (
        {"key": "vxinglvchi.v_filter_band",
         "expression": "v_filter_act >= 7.0 and v_filter_act <= 10.0",
         "source": "constraint_kb"},
        {"key": "vxinglvchi.v_forced_band",
         "expression": "v_forced_act <= 13.0",
         "source": "constraint_kb"},
    )
    from waterprint.app import Constraint
    from waterprint.solution.design_map import DesignMapOptions

    typed = tuple(Constraint(**item) for item in constraints)
    project = _fd_project("municipal_vxinglvchi")
    env = _fd_env()
    conditions = _conditions()
    product = run_design_map(
        project, "municipal_vxinglvchi", conditions, env,
        DesignMapOptions(axes=[{"field_id": "v_filter"}], fixed_params={}, constraints=typed),
    )
    payload = product.payload()
    assert payload["constraint_coverage"] == "full"

    # 手工装配（枚举面原语）——与 run_design_map 同数据源
    assembled = assemble(project, env)
    unit = assembled.units["municipal_vxinglvchi"]
    resolved = resolve_axes(unit.manifest.params, [{"field_id": "v_filter"}])  # type: ignore[misc]
    grid = build_grid(axis_mappings(resolved), guard_base=False)  # type: ignore[misc]
    plant = run_full_calc(project, conditions, env).plant
    context = upstream_context(
        UpstreamSource(assembled.units, assembled.edges, project.design, plant),
        "municipal_vxinglvchi", next(iter(conditions.iter_all())), env,
    )
    frame = importlib.import_module("waterprint.solution.enumerate").enumerate_solutions(
        grid, context, unit, env
    )
    filtered = apply_constraints(frame, typed)  # type: ignore[misc]
    mask = feasible_mask(frame, filtered.pass_matrix)  # type: ignore[misc]
    # 对拍一：可行数
    assert payload["stats"]["feasible"] == int(mask.sum())
    # 对拍二：逐点掩码（1D 段重建）
    values = payload["axis_values"][0]
    rebuilt = numpy.zeros(len(values), dtype=bool)
    for segment in payload["segments"]:
        start = values.index(segment["start"])
        end = values.index(segment["end"])
        rebuilt[start : end + 1] = True
    assert rebuilt.tolist() == mask.tolist()
    # 对拍三：diagnose 幅度接线（grid 在场）——本例 param_key=v_filter_act
    # ≠轴字段 v_filter → magnitude=None 诚实缺省；expected_effect 带可行率
    report = diagnose_infeasibility(
        filtered.pass_matrix, {c.expression: c for c in typed}, grid=grid
    )
    assert report.suggestions, "失败行在场应产建议"
    assert all(s.magnitude is None for s in report.suggestions)
    assert all("可行率" in s.expected_effect for s in report.suggestions)


def test_run_design_map_guard_fires_before_grid() -> None:
    """P1-5 时序：max_points 拦截先于网格生成（GridTooLarge 不触发——PD4 独立）。"""
    from waterprint.app import run_design_map
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.solution.design_map import DesignMapOptions

    lib = load_coefficients(_DATA)
    env = RunEnv(
        engine_version="fd", data_version="x",
        assumptions={"solution.design_map.max_points": 30.0},
        coefficients=lib, price_book={}, trace_sink=None, engine_params={},
    )
    # 6×6=36 ≤ 7^2=49（枚举护栏放行）但 > 30（FD 护栏拦截）
    with pytest.raises(DesignMapTooLarge, match="max_points"):  # type: ignore[misc]
        run_design_map(
            _fd_project("municipal_aao"), "municipal_aao", _conditions(), env,
            DesignMapOptions(axes=[
                {"field_id": "ns", "range": {"min": 0.05, "max": 0.15}, "step": 0.02},
                {"field_id": "x_mlss", "range": {"min": 3500.0, "max": 4500.0}, "step": 200.0},
            ], fixed_params={}),
        )


def test_run_design_map_fixed_params_authoritative() -> None:
    """PD1 固定参数=显式映射叠加（server 装配面权威）：跨轴参数注入生效。"""
    from waterprint.app import run_design_map
    from waterprint.solution.design_map import DesignMapOptions

    product = run_design_map(
        _fd_project("municipal_aao"), "municipal_aao", _conditions(), _fd_env(),
        DesignMapOptions(axes=[{"field_id": "ns"}],
                         fixed_params={"x_mlss": 4000.0, "t_p": 1.5}),
    )
    assert product.payload()["stats"]["total"] == 11  # 扫描面不受固定参数影响


def test_run_design_map_unit_missing_rejected() -> None:
    """目标单元不在装配图=InvalidAssemblyError（单单元语义同枚举）。"""
    from waterprint.app import InvalidAssemblyError, run_design_map
    from waterprint.solution.design_map import DesignMapOptions

    with pytest.raises(InvalidAssemblyError, match="不在装配图"):  # type: ignore[misc]
        run_design_map(
            _fd_project("municipal_aao"), "municipal_ghost", _conditions(), _fd_env(),
            DesignMapOptions(axes=[{"field_id": "ns"}], fixed_params={}),
        )
