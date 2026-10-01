"""市政线检修降级映射声明面与引擎行为测试（cond 批 2026-10-01）。

输入:  units_lib 声明面（discover_units 注册表 13 市政包 manifest）+
       golden municipal_34760 案例（19 节点全厂——引擎行为面载体）
输出:  四组断言——①声明面清点（11 有并行槽数参数单元恰 1 条正典三元式
       且 target/rule 字面恒等；bashi_jiliangcao/wushui_tisheng 两单元
       空映射锁定=不合格面明示）②mapped 单元（aao）design.checked_units
       承载路径 → 3 工况+offline dims 逐键分化（n 降一/单系列量翻倍）
       ③unmapped 单元（bashi）D4 拒检=InvalidAssemblyError（消息含
       「须声明检修降级映射」——诚实行为）④基线零漂移（同一项目无
       checked 与有 checked 两跑 design/avg 两档 summary 逐键相等——
       基线档 pool.all_pools=True 真支原值透传，ADR-007 冻结语义）。

【范围界】mine_water/sludge/conveyance 线不在断言面（cond 批范围=
市政线，他线后续批）；tiaojiechi 仅 n（格数）映射——n_pump_duty 泵
台数非池数语义不映射（映射表出处=cond 批简报 §4.1，ADR-007）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

_REPO_DATA = Path(__file__).resolve().parents[3] / "data" / "coefficients"
_GOLDEN_CASE = Path("municipal_34760")

# 11 单元正典三元式表（unit_id → (target, rule)；简报 §4.1 逐字——
# target 键名与各包 manifest params 声明面逐一核对）。
_CANONICAL: dict[str, tuple[str, str]] = {
    "municipal_cugeshan": ("n", "n if pool.all_pools else n - 1"),
    "municipal_xigeshan": ("n", "n if pool.all_pools else n - 1"),
    "municipal_chenshachi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_chuchenchi": ("n", "n if pool.all_pools else n - 1"),
    # 格数映射；n_pump_duty（泵台数）不映射——非池数降级语义。
    "municipal_tiaojiechi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_aao": ("n", "n if pool.all_pools else n - 1"),
    "municipal_cass": ("n_pool", "n_pool if pool.all_pools else n_pool - 1"),
    "municipal_gaomidu": ("n", "n if pool.all_pools else n - 1"),
    "municipal_vxinglvchi": ("n", "n if pool.all_pools else n - 1"),
    "municipal_ziwai": (
        "n_channel",
        "n_channel if pool.all_pools else n_channel - 1",
    ),
    "municipal_erchunchi": ("n", "n if pool.all_pools else n - 1"),
}

# 两单元不合格明示不映射（D4 拒检=诚实行为——测试锁定空声明面）。
_UNMAPPED: tuple[str, ...] = (
    "municipal_bashi_jiliangcao",  # 单槽构筑物，无并行槽数参数
    "municipal_wushui_tisheng",  # n_pump_duty=ceil 计算值非参数；n_standby 纯计数回显
)


def _registry() -> Any:
    """单元注册表（discover_units——32 包 manifest 装载即静态校验）。"""
    from waterprint.units_lib import discover_units

    return discover_units()


# ══ ① 声明面清点 ══════════════════════════════════════════════════


@pytest.mark.parametrize(
    ("unit_id", "expected"),
    sorted(_CANONICAL.items()),
)
def test_mapped_units_declare_canonical_triple(
    unit_id: str, expected: tuple[str, str]
) -> None:
    """11 单元各恰 1 条三元式：target/rule 字面与正典表恒等+target 在 params。"""
    manifest = _registry()[unit_id][0]
    mappings = manifest.condition_mappings
    assert len(mappings) == 1, f"{unit_id} condition_mappings 恰 1 条：得到 {len(mappings)}"
    target, rule = expected
    assert mappings[0].target == target
    assert mappings[0].rule == rule
    param_ids = {spec.field_id for spec in manifest.params}
    assert target in param_ids, f"{unit_id} 映射 target {target!r} 不在 params 声明面"


def test_mapped_unit_count_is_eleven() -> None:
    """市政线映射单元总数=11（清点面防静默漏报——恰等正典表键集）。"""
    registry = _registry()
    municipal = {
        unit_id
        for unit_id in registry
        if unit_id.startswith("municipal_")
    }
    mapped = {
        unit_id
        for unit_id in municipal
        if registry[unit_id][0].condition_mappings
    }
    assert mapped == set(_CANONICAL)


@pytest.mark.parametrize("unit_id", _UNMAPPED)
def test_unmapped_units_declare_no_mappings(unit_id: str) -> None:
    """两单元 condition_mappings 为空（不合格面锁定——D4 拒检语义承载）。"""
    assert _registry()[unit_id][0].condition_mappings == ()


# ══ ②③④ 引擎行为面（golden municipal_34760 实跑）═════════════════

_golden_ready = (
    Path(__file__).resolve().parents[1] / "golden" / "golden_data" / _GOLDEN_CASE
    / "input_project.json"
).is_file()


def _golden_project(golden_data_dir: Path) -> Any:
    """golden municipal_34760 项目（19 节点全厂装载正门）。"""
    from waterprint.app import load_project

    return load_project(golden_data_dir / _GOLDEN_CASE / "input_project.json")


def _run_env(golden_data_dir: Path) -> Any:
    """RunEnv（口径=golden expected.generated 实录：server 版本串+数据版本）。"""
    import json

    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    generated = json.loads(
        (golden_data_dir / _GOLDEN_CASE / "expected_summary.json").read_text(
            encoding="utf-8"
        )
    )["generated"]
    return RunEnv(
        engine_version=generated["engine_version"],
        data_version=generated["data_version"],
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=load_coefficients(_REPO_DATA),
        price_book={},
        trace_sink=None,
        engine_params={},
    )


def _with_checked(project: Any, *unit_ids: str) -> Any:
    """design.checked_units 承载改写（D4 资格校验路径的输入面）。"""
    return project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"checked_units": list(unit_ids)}
            )
        }
    )


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_mapped_checked_unit_offline_dims_differentiate(
    golden_data_dir: Path,
) -> None:
    """mapped 单元（aao）checked 路径：3 工况+offline dims 逐键分化。

    aao n=2（golden 默认档）：offline 档 n 2→1（n−1 冻结语义）；
    v_o_series/n_aerator 随单系列承载全流量翻倍（主控冒烟口径复证）。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import ConditionSet, build_condition_set

    conditions = build_condition_set(["municipal_aao"])
    keys = [ConditionSet.key(c) for c in conditions.iter_all()]
    assert keys == ["design", "avg", "design_offline_municipal_aao"]  # 2+k=3 工况
    plant = run_full_calc(
        _with_checked(_golden_project(golden_data_dir), "municipal_aao"),
        conditions,
        _run_env(golden_data_dir),
    ).plant
    assert set(plant.conditions) == set(keys)  # 全 3 工况各出整图结果
    design = plant.conditions["design"]["municipal_aao"].dims
    offline = plant.conditions["design_offline_municipal_aao"]["municipal_aao"].dims
    assert design["n"] == 2.0  # golden 案例默认池数档（anchors 非手造）
    assert offline["n"] == design["n"] - 1 == 1.0  # n−1 降级
    assert offline["v_o_series"] == pytest.approx(2 * design["v_o_series"])
    assert offline["n_aerator"] == pytest.approx(2 * design["n_aerator"])


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_unmapped_checked_unit_rejected(golden_data_dir: Path) -> None:
    """unmapped 单元（bashi）勾选受检=InvalidAssemblyError（D4 拒检）。"""
    from waterprint.app import InvalidAssemblyError, assemble

    with pytest.raises(InvalidAssemblyError, match="须声明检修降级映射"):
        assemble(
            _with_checked(
                _golden_project(golden_data_dir), "municipal_bashi_jiliangcao"
            ),
            _run_env(golden_data_dir),
        )


@pytest.mark.golden
@pytest.mark.skipif(not _golden_ready, reason="golden 数据未整理（市政案例在册才跑）")
def test_baseline_summary_zero_drift_with_checked(golden_data_dir: Path) -> None:
    """基线零漂移：同一项目无 checked 与有 checked 两跑 design/avg 逐键相等。

    基线档 pool.all_pools=True → 三元真支=原值浮点透传（构造性零漂移）；
    summary 含 B4-2a 能耗药耗聚合键族——n-不变在 35 键全量上实证。
    """
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set

    project = _golden_project(golden_data_dir)
    env = _run_env(golden_data_dir)
    baseline = run_full_calc(project, build_condition_set([]), env).plant
    checked = run_full_calc(
        project, build_condition_set(["municipal_aao"]), env
    ).plant
    for key in ("design", "avg"):
        assert checked.summary[key] == baseline.summary[key], f"summary.{key} 漂移"
