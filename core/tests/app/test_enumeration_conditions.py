"""ADR-018 D2 枚举全工况化镜像测试：run_enumeration 多工况行面契约。

输入:  waterprint.app 公开符号（run_enumeration/EnumerationOptions/load_
       project）+ golden municipal_34760 案例（19 节点；checked_units=
       [chuchenchi/aao/erchunchi] → 2+3=5 工况；expected_summary 同源）
输出:  多工况行数/键分组/行序/约束跨工况一致/全工况无解诊断/空集守卫/
       condition_fields 标签族——ADR-018 D2 行为规格镜像

【锁面纪律】本件为 ADR-018 新增测试面（2026-09-12），271 键锁面只增
  不改；D6 记档的既有两件翻案（test_enumeration_usecase 十五行/排序
  截断）归既有件维护，本件不重复承载——只断「多工况新增语义」。
  载体选 golden 全厂（非 CASS 两节点）=工况轴真源（AAO 已声明
  out_dims 21 条，condition_fields 标签族断真源面）。
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.app")
run_enumeration = getattr(_mod, "run_enumeration", None)
load_project = getattr(_mod, "load_project", None)
EnumerationOptions = getattr(_mod, "EnumerationOptions", None)
Constraint = getattr(_mod, "Constraint", None)
InvalidAssemblyError = getattr(_mod, "InvalidAssemblyError", None)

pytestmark = pytest.mark.skipif(
    None
    in (run_enumeration, load_project, EnumerationOptions, Constraint,
        InvalidAssemblyError),
    reason="实现未就绪：waterprint.app 枚举全工况化（ADR-018）",
)

_GOLDEN = (
    Path(__file__).resolve().parents[1]
    / "golden" / "golden_data" / "municipal_34760"
)
_AAO_OUT_DIMS_ZH = (  # AAO manifest out_dims 前四条 label_zh 真源抽样（全 21 条归 AAO 测试面）
    "好氧区容积",
    "好氧区 HRT",
    "厌氧区容积",
    "缺氧区容积",
)


def _project() -> object:
    """golden municipal_34760 项目（19 节点全厂——工况轴真源载体）。"""
    return load_project(_GOLDEN / "input_project.json")  # type: ignore[misc]


def _checked_units() -> list[str]:
    """expected_summary 同源受检集（chuchenchi/aao/erchunchi → 2+3=5 工况）。"""
    expected = json.loads((_GOLDEN / "expected_summary.json").read_text(encoding="utf-8"))
    return [str(u) for u in expected["checked_units"]]


def _env() -> object:
    """golden e2e 同口径 env（coefficients + 默认假设视图）。"""
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    data = Path(__file__).resolve().parents[3] / "data" / "coefficients"
    lib = load_coefficients(data)
    return RunEnv(
        engine_version="adr018",
        data_version=f"coefficients@{lib.data_version}",
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib,
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def test_rows_scale_with_condition_count(golden_data_dir: Path) -> None:
    """D2 行数=grid.total×(2+k)：golden 3 受检=5 工况 × AAO 网格档数。"""
    from waterprint.app import assemble
    from waterprint.contracts.condition import build_condition_set
    from waterprint.solution.grid import build_grid

    project = _project()
    env = _env()
    conditions = build_condition_set(_checked_units())
    assembled = assemble(project, env)
    unit = assembled.units["municipal_aao"]
    grid = build_grid(
        [spec for spec in unit.manifest.params if spec.grid is not None],
        overrides=env.assumptions,
    )
    outcome = run_enumeration(project, "municipal_aao", conditions, env)  # type: ignore[misc]
    assert len(outcome.rows) == grid.total * 5  # R1：2+k 线性（3 受检=5 工况）
    assert outcome.rows["condition_key"].value_counts().to_dict() == {
        "design": grid.total,
        "avg": grid.total,
        "design_offline_municipal_chuchenchi": grid.total,
        "design_offline_municipal_aao": grid.total,
        "design_offline_municipal_erchunchi": grid.total,
    }


def test_row_order_is_condition_then_grid(golden_data_dir: Path) -> None:
    """D2 行序语义（ADR-018 D2 记档）：margin_min 全 NaN（AAO 无 margin_*
    字段）时 rank 稳定排序 tie_break=grid 轴升序 → 呈现序=网格行主序、
    工况内序交错（同方案档各工况相邻）——较工况块序更利同档跨工况比。
    """
    from waterprint.contracts.condition import build_condition_set

    outcome = run_enumeration(  # type: ignore[misc]
        _project(), "municipal_aao", build_condition_set(_checked_units()), _env()  # type: ignore[misc]
    )
    keys = outcome.rows["condition_key"].tolist()
    total = len(keys) // 5  # 5 工况均分（网格档数）
    # 交错序：每个网格档内 5 工况按 build_condition_set 序相邻
    first_row_block = keys[:5]
    assert first_row_block == [
        "design",
        "avg",
        "design_offline_municipal_chuchenchi",
        "design_offline_municipal_aao",
        "design_offline_municipal_erchunchi",
    ]
    # 首 grid 轴单调非降（网格行主序——tie_break 升序生效）
    first_axis = outcome.rows.columns[0]
    axis_values = outcome.rows[first_axis].tolist()
    assert axis_values == sorted(axis_values, key=float)
    # 工况覆盖完整性：5 工况各 total 行
    assert outcome.rows["condition_key"].value_counts().to_dict() == {
        "design": total,
        "avg": total,
        "design_offline_municipal_chuchenchi": total,
        "design_offline_municipal_aao": total,
        "design_offline_municipal_erchunchi": total,
    }


def test_constraints_apply_across_conditions_consistently(
    golden_data_dir: Path,
) -> None:
    """D2 约束整帧一次过滤：全部在场行满足表达式（跨工况一致性可观测面）。"""
    from waterprint.contracts.condition import build_condition_set

    options = EnumerationOptions(  # type: ignore[misc]
        constraints=(
            Constraint(  # type: ignore[misc]
                key="demo.v_max",
                expression="v_total <= 100000",
                source="test",
            ),
        )
    )
    outcome = run_enumeration(  # type: ignore[misc]
        _project(), "municipal_aao", build_condition_set([]), _env(), options  # type: ignore[misc]
    )
    feasible = outcome.rows[outcome.rows["v_total"].notna()]
    assert bool((feasible["v_total"] <= 100000).all())  # 约束对全部工况行生效
    assert outcome.diagnosis is None  # 有可行解 → 不出诊断


def test_diagnosis_only_when_all_conditions_infeasible(
    golden_data_dir: Path,
) -> None:
    """D2 诊断口径=全工况无可行解才触发（分工况无解诊断挂账 ADR-018）。"""
    from waterprint.contracts.condition import build_condition_set

    impossible = EnumerationOptions(  # type: ignore[misc]
        constraints=(
            Constraint(  # type: ignore[misc]
                key="demo.impossible",
                expression="v_total <= 0",  # 恒假（容积恒正）
                source="test",
            ),
        )
    )
    outcome = run_enumeration(  # type: ignore[misc]
        _project(), "municipal_aao", build_condition_set([]), _env(), impossible  # type: ignore[misc]
    )
    assert outcome.total_feasible == 0
    assert outcome.diagnosis is not None  # 全工况无解 → 诊断在非 None


def test_empty_condition_set_guard(golden_data_dir: Path) -> None:
    """D2 空集守卫：直构空 ConditionSet=InvalidAssemblyError（GR-11 收口）。"""
    from waterprint.contracts.condition import ConditionSet

    with pytest.raises(InvalidAssemblyError, match="conditions 为空集"):  # type: ignore[misc]
        run_enumeration(  # type: ignore[misc]
            _project(),
            "municipal_aao",
            ConditionSet(baseline=(), sensitivity=()),  # type: ignore[misc]
            _env(),  # type: ignore[misc]
        )


def test_condition_fields_from_out_dims_label_zh(golden_data_dir: Path) -> None:
    """D2 condition_fields=按 manifest.out_dims 声明序取 label_zh 真源（AAO 23 条）。"""
    from waterprint.contracts.condition import build_condition_set

    outcome = run_enumeration(  # type: ignore[misc]
        _project(), "municipal_aao", build_condition_set([]), _env()  # type: ignore[misc]
    )
    assert outcome.condition_fields[:4] == _AAO_OUT_DIMS_ZH  # 声明序前四条中文名
    assert len(outcome.condition_fields) == 23  # AAO 21→23 条（V2 批+曝气头数据面批两键）
