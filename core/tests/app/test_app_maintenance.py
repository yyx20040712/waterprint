"""app_maintenance 镜像测试：检修观测与校核三面纯投影（UF-61 余轴批）。

输入:  waterprint.app_maintenance（maintenance_summary_of/_with_maintenance）
       + stub 双帧 PlantResult/ConditionSet/kb 桩 + golden municipal_34760
       实跑（aao 锚——probe_master 2026-10-02 分化四键实证）
输出:  三面行为断言——ratio 分化键集（全等/非有限/零基跳过）+kb 适用判据
       三态与单行 DSL 求值双档+fixgeom.min 负值超载语义+golden 三面值锚
       +双跑 serialize 字节同+空 sensitivity 零键+run_full_calc 接线
       （constraints 传入 kb 键在场/缺省 () 零 kb 键/baseline 帧零 maint 键）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：uf61-axes-20261002 简报 §4.1/§4.5——ratio 面=分化键集（两帧同键、
#   design 有限非零、offline 有限、exact != 才发）；kb 面=solution.
#   apply_constraints 单行 DataFrame 求值（禁手写求值——DSL 单源）；
#   fixgeom 面=kb 覆盖字段 ∩ ratio 可算域上 min(1−off/des)；对比基线=
#   conditions.baseline[0]（禁字符串字面量 "design"）；kb.any_fail 汇总键
#   =1.0（任一适用越门）/0.0（全过）——applicable 非空才发（kbwire 批）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from waterprint.app_maintenance import _with_maintenance, maintenance_summary_of
from waterprint.contracts.condition import build_condition_set
from waterprint.contracts.result_schema import PlantResult, ReproTriple, UnitResultSnapshot
from waterprint.solution.constraints import Constraint, KbConstraint

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REPO_DATA = _REPO_ROOT / "data"


def _snap(dims: dict[str, float]) -> UnitResultSnapshot:
    """最小单元快照（face 只读 dims——其余字段空载）。"""
    return UnitResultSnapshot(
        unit_id="stub", outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _plant(frames: dict[str, dict[str, dict[str, float]]]) -> PlantResult:
    """stub PlantResult：conditions 三帧（design/avg/offline——face 读前两者与 offline）。"""
    return PlantResult(
        conditions={
            key: {node: _snap(dims) for node, dims in frame.items()}
            for key, frame in frames.items()
        },
        summary={}, trace=(),
        repro=ReproTriple(design_hash="", engine_version="t", data_version="t"),
    )


def _units(kind: str) -> dict[str, Any]:
    """单元注册表桩：manifest.unit_id=kind（适用判据的 kind 口径）。"""
    return {"stub_unit": SimpleNamespace(manifest=SimpleNamespace(unit_id=kind))}


def _kb(
    key: str, expression: str, unit_kinds: tuple[str, ...], kind: str = "geometry_guard"
) -> KbConstraint:
    """kb 桩（source=kb 键语义——装载器同口径；kind 缺省 geometry_guard）。"""
    return KbConstraint(
        constraint=Constraint(key=key, expression=expression, source=key),
        unit_kinds=unit_kinds,
        kind=kind,
    )


def _double_frame(
    design: dict[str, float], offline: dict[str, float]
) -> PlantResult:
    """目标单元双帧载体（avg 帧面与 face 无关——空帧在场）。"""
    return _plant({
        "design": {"stub_unit": design},
        "avg": {},
        "design_offline_stub_unit": {"stub_unit": offline},
    })


def test_ratio_face_emits_only_differentiated_keys() -> None:
    """ratio 面=分化键集：exact != 才发键；全等键不发（对比面=差异面）。"""
    plant = _double_frame(
        {"a": 2.0, "b": 6.0, "c": 1.0}, {"a": 1.0, "b": 6.0, "c": 2.0})
    view = maintenance_summary_of(
        plant, build_condition_set(["stub_unit"]), _units("stub_kind"), ())
    face = view["design_offline_stub_unit"]
    assert face == {
        "maint.stub_unit.ratio.a": 0.5,
        "maint.stub_unit.ratio.c": 2.0,
    }  # b 全等（ratio 1.0）不发键——分化键集口径


def test_ratio_face_skips_nonfinite_and_zero_design() -> None:
    """ratio 可算域守卫：design 零/非有限、offline 非有限均跳过。"""
    plant = _double_frame(
        {"zero": 0.0, "inf_des": float("inf"), "finite": 4.0, "nan_des": float("nan")},
        {"zero": 1.0, "inf_des": 2.0, "finite": float("inf"), "nan_des": 1.0},
    )
    view = maintenance_summary_of(
        plant, build_condition_set(["stub_unit"]), _units("stub_kind"), ())
    assert view["design_offline_stub_unit"] == {}  # 四守卫各吞一键


def test_kb_face_applicability_three_modes() -> None:
    """kb 适用判据三态：kind 命中+字段在场=适用；kind 缺席/字段缺席=不发键；
    kb 空集=零 kb 键（kb 面整体不入场）。"""
    plant = _double_frame({"v": 10.0}, {"v": 10.0})
    conditions = build_condition_set(["stub_unit"])
    units = _units("stub_kind")
    view = maintenance_summary_of(plant, conditions, units, (
        _kb("kb.stub.hit", "v <= 100", ("stub_kind",)),
        _kb("kb.stub.other_kind", "v <= 100", ("other_kind",)),
        _kb("kb.stub.absent_field", "absent <= 1", ("stub_kind",)),
    ))
    face = view["design_offline_stub_unit"]
    assert set(face) == {  # 恰 kind 命中且字段在场一条（ratio 无分化零键）
        "maint.stub_unit.kb.kb.stub.hit",
        "maint.stub_unit.kb.any_fail",  # kbwire 汇总键（applicable 非空同域）
        "maint.stub_unit.fixgeom.min",  # v 全等→裕度 0.0（可算域含全等字段）
    }
    assert face["maint.stub_unit.kb.any_fail"] == 0.0  # 单条适用且过→0.0
    assert face["maint.stub_unit.fixgeom.min"] == 0.0
    empty = maintenance_summary_of(plant, conditions, units, ())
    assert empty["design_offline_stub_unit"] == {}  # kb 空集=零键（ratio 面无分化同零）


def test_kb_face_pass_both_levels() -> None:
    """kb pass 双档：门内 1.0/越门 0.0（apply_constraints 单行求值——stub 构造越门值）。"""
    plant = _double_frame({"v": 80.0, "w": 40.0}, {"v": 120.0, "w": 40.0})
    view = maintenance_summary_of(
        plant, build_condition_set(["stub_unit"]), _units("stub_kind"), (
            _kb("kb.stub.pass", "w <= 50", ("stub_kind",)),
            _kb("kb.stub.fail", "v <= 100", ("stub_kind",)),
        ))
    face = view["design_offline_stub_unit"]
    assert face["maint.stub_unit.kb.kb.stub.pass"] == 1.0  # 门内
    assert face["maint.stub_unit.kb.kb.stub.fail"] == 0.0  # 越门（标注不阻断）


def test_kb_any_fail_three_modes() -> None:
    """any_fail 汇总键三态（kbwire）：任一适用越门=1.0/全过=0.0/
    无适用条目=不发键（与 kb 键同域——applicable 非空才发）。"""
    plant = _double_frame({"v": 80.0, "w": 40.0}, {"v": 120.0, "w": 40.0})
    conditions = build_condition_set(["stub_unit"])
    units = _units("stub_kind")
    failing = maintenance_summary_of(plant, conditions, units, (
        _kb("kb.stub.pass", "w <= 50", ("stub_kind",)),
        _kb("kb.stub.fail", "v <= 100", ("stub_kind",)),
    ))["design_offline_stub_unit"]
    assert failing["maint.stub_unit.kb.kb.stub.fail"] == 0.0  # 越门单键
    assert failing["maint.stub_unit.kb.any_fail"] == 1.0  # 任一越门→1.0
    passing = maintenance_summary_of(plant, conditions, units, (
        _kb("kb.stub.pass", "w <= 50", ("stub_kind",)),
    ))["design_offline_stub_unit"]
    assert passing["maint.stub_unit.kb.any_fail"] == 0.0  # 全过→0.0
    for constraints in ((), (_kb("kb.stub.other", "v <= 100", ("other_kind",)),)):
        nonapplicable = maintenance_summary_of(
            plant, conditions, units, constraints)["design_offline_stub_unit"]
        assert "maint.stub_unit.kb.any_fail" not in nonapplicable  # 无适用不发键


def test_fixgeom_min_negative_overload_semantics() -> None:
    """fixgeom.min 负值语义：×2 超载=−1.0（固定几何检修负荷裕度——探针 aao 锚）。"""
    plant = _double_frame(
        {"n_aerator": 4.0, "l_pool": 50.0}, {"n_aerator": 8.0, "l_pool": 50.0})
    view = maintenance_summary_of(
        plant, build_condition_set(["stub_unit"]), _units("stub_kind"), (
            _kb("kb.stub.aerator", "n_aerator <= 10000", ("stub_kind",)),
            _kb("kb.stub.pool", "l_pool <= 300", ("stub_kind",)),
        ))
    face = view["design_offline_stub_unit"]
    assert face["maint.stub_unit.fixgeom.min"] == pytest.approx(-1.0)  # min(1−2, 1−1)


def test_fixgeom_absent_when_kb_field_outside_ratio_domain() -> None:
    """fixgeom F∩可算域空=不发键：kb 字段在场（kb 键发）但 design 值为零（ratio 不可算）。"""
    plant = _double_frame({"b": 0.0}, {"b": 0.0})
    view = maintenance_summary_of(
        plant, build_condition_set(["stub_unit"]), _units("stub_kind"), (
            _kb("kb.stub.zero_base", "b <= 1", ("stub_kind",)),
        ))
    face = view["design_offline_stub_unit"]
    assert face == {  # kb 面在场、fixgeom 不发（any_fail 同 kb 域随发）
        "maint.stub_unit.kb.kb.stub.zero_base": 1.0,
        "maint.stub_unit.kb.any_fail": 0.0,
    }


def test_target_snapshot_sparse_skip_and_empty_sensitivity() -> None:
    """目标单元快照双方在场才发键（sparse）；sensitivity 空集=零键（baseline 帧零发）。"""
    missing = _plant({"design": {}, "avg": {}})  # 目标单元两帧均缺席
    assert maintenance_summary_of(
        missing, build_condition_set(["stub_unit"]), _units("stub_kind"), ()
    ) == {"design_offline_stub_unit": {}}  # 稀疏跳过=空面（不造键）
    assert maintenance_summary_of(
        _plant({"design": {"stub_unit": {"a": 1.0}}}), build_condition_set([]),
        _units("stub_kind"), (),
    ) == {}  # 空 sensitivity=零工况投影


def test_with_maintenance_merge_base_priority() -> None:
    """_with_maintenance 合并语义（_with_carbon 同款）：同工况字典 update、
    base 无的工况不并入；两族键集无交集由 maint.* 命名域保证。"""
    base = {"design": {"BOD5": 1.0}, "design_offline_stub_unit": {"BOD5": 2.0}}
    extra = {
        "unrelated_condition": {"maint.x.ratio.n": 0.5},  # base 无的工况=不并入
        "design_offline_stub_unit": {"maint.stub_unit.ratio.n": 0.5},
    }
    merged = _with_maintenance(base, extra)
    assert set(merged) == set(base)  # 工况集不扩（面只发 offline 工况）
    assert merged["design"] == {"BOD5": 1.0}  # 未触达工况零并入
    assert merged["design_offline_stub_unit"] == {
        "BOD5": 2.0, "maint.stub_unit.ratio.n": 0.5}  # maint 键增量并入


def test_pure_function_double_run_stub() -> None:
    """纯函数双跑：同输入两跑全等（kb 迭代=传入序/dims 迭代=插入序的确定性）。"""
    plant = _double_frame({"a": 2.0, "v": 80.0}, {"a": 3.0, "v": 120.0})
    constraints = (
        _kb("kb.stub.one", "v <= 100", ("stub_kind",)),
        _kb("kb.stub.two", "a >= 1", ("stub_kind",)),
    )
    args = (plant, build_condition_set(["stub_unit"]), _units("stub_kind"), constraints)
    assert maintenance_summary_of(*args) == maintenance_summary_of(*args)


# ── 回炉轮 1 补锚（R1 空 baseline 通透/R2 boundary_check 消费面豁免）──────


def test_empty_baseline_returns_empty_not_crash() -> None:
    """R1 锚：空 baseline=无对比基线即无观测面（不炸不造键）——face 直调
    返回 {}+run_full_calc 全链（ConditionSet 直构 baseline=()）通透不崩。"""
    from waterprint.contracts.condition import (
        ConditionSet,
        FlowCase,
        OperatingCondition,
    )

    offline_only = ConditionSet(
        baseline=(),
        sensitivity=(OperatingCondition(
            flow_case=FlowCase.DESIGN, offline_unit="stub_unit"),),
    )
    plant = _double_frame({"a": 2.0}, {"a": 1.0})
    assert maintenance_summary_of(plant, offline_only, _units("stub_kind"), ()) == {}
    # 全链通透：golden 案 offline-only 工况集经 run_full_calc 不崩+零 maint 键
    from waterprint.app import load_project, load_run_env, run_full_calc

    project = load_project(
        Path(__file__).resolve().parents[1] / "golden" / "golden_data"
        / "municipal_34760" / "input_project.json"
    )
    aao_only = ConditionSet(
        baseline=(),
        sensitivity=(OperatingCondition(
            flow_case=FlowCase.DESIGN, offline_unit="municipal_aao"),),
    )
    bundle = run_full_calc(
        project, aao_only, load_run_env(_REPO_DATA, project))
    assert set(bundle.plant.summary) == {"design_offline_municipal_aao"}
    assert not any(
        key.startswith("maint.")
        for key in bundle.plant.summary["design_offline_municipal_aao"]
    )


def test_boundary_check_kind_excluded_from_kb_face() -> None:
    """R2 锚：kind=boundary_check 条目即使 unit_kinds 命中也被面排除
    （装载器 _BOUNDARY_CHECK_KIND 同款豁免镜像——符号式 expression 零
    求值不崩；d1 点名的消费面缺口封堵）。"""
    plant = _double_frame({"containment": 1.0}, {"containment": 1.0})
    view = maintenance_summary_of(
        plant, build_condition_set(["stub_unit"]), _units("stub_kind"), (
            _kb("site.stub.containment", "containment == inside",
                ("stub_kind",), kind="boundary_check"),
            _kb("kb.stub.normal", "containment <= 100", ("stub_kind",)),
        ))
    face = view["design_offline_stub_unit"]
    assert set(face) == {  # boundary_check 排除（符号式未触达 DSL 求值）
        "maint.stub_unit.kb.kb.stub.normal",
        "maint.stub_unit.kb.any_fail",  # kbwire 汇总键（normal 过→0.0）
        "maint.stub_unit.fixgeom.min",
    }
    assert face["maint.stub_unit.fixgeom.min"] == 0.0  # 全等字段裕度基准 _FULL


# ── golden 实跑面（aao 锚——probe_master.py 2026-10-02 分化四键实证）──────


def _golden_bundle(constraints: tuple[KbConstraint, ...]) -> Any:
    """municipal_34760 checked=[aao] 实跑（golden e2e 同径 env 装配）。"""
    from waterprint.app import load_project, load_run_env, run_full_calc

    project = load_project(
        Path(__file__).resolve().parents[1] / "golden" / "golden_data"
        / "municipal_34760" / "input_project.json"
    )
    env = load_run_env(_REPO_DATA, project)
    return run_full_calc(
        project, build_condition_set(["municipal_aao"]), env,
        constraints=constraints,
    )


def _loaded_kb() -> tuple[KbConstraint, ...]:
    """kb 真源装载（34 条全量——kb 面消费面非数据批）。"""
    from waterprint.solution.constraints import load_kb_constraints

    return load_kb_constraints(_REPO_DATA / "constraint_kb" / "constraints.json")


def test_golden_aao_three_faces() -> None:
    """golden aao 实跑锚：ratio 恰分化四键+kb 12 条全 1.0+fixgeom.min=−1.0。

    kb 适用=unit_kinds∋aao 且表达式字段在场（在场即适用——零硬编码名单
    口径）：geometry_guard 8 条+aao 带 2 条（t_n/theta_c 字段在场）+1A4 批
    param_band 2 条（param.n/h2——参数名与离线 dims 同名经字段准入合法
    选中；其余 param_band 条目字段不在 dims 面不选中）=12。"""
    from waterprint.solution.constraints import expression_fields

    bundle = _golden_bundle(_loaded_kb())
    offline = bundle.plant.summary["design_offline_municipal_aao"]
    ratio = {k: v for k, v in offline.items() if ".ratio." in k}
    assert set(ratio) == {  # 探针锚：35 dims 键中恰 4 键漂移（几何四键全等不发）
        "maint.municipal_aao.ratio.n",
        "maint.municipal_aao.ratio.n_aerator",
        "maint.municipal_aao.ratio.n_aerator_raw",
        "maint.municipal_aao.ratio.v_o_series",
    }
    assert ratio["maint.municipal_aao.ratio.n"] == pytest.approx(0.5)  # n 2→1
    assert ratio["maint.municipal_aao.ratio.n_aerator"] == pytest.approx(2.0)  # ×2 升负荷
    kb = {k: v for k, v in offline.items()
          if ".kb." in k and k != "maint.municipal_aao.kb.any_fail"}
    assert set(kb.values()) == {1.0}  # kb 全 1.0（越门 0.0 缺席=门内全通过）
    assert len(kb) == 12  # geometry 8+aao 带 2+param_band 2（param.n/h2——
    # 1A4 批：aao 离线 dims 含同名参数键经 _maint_face 字段准入合法选中，
    # 全 PASS；实跑清点——简报「实现期逐条核」口径）
    aao_dims = dict(
        dict(bundle.plant.conditions["design_offline_municipal_aao"])
        ["municipal_aao"].dims)
    assert {k.removeprefix("maint.municipal_aao.kb.") for k in kb} == {
        # 键集=unit_kinds∋aao 且字段⊆离线 dims 全量（防静默缺席——kb 键
        # 自带点分前缀；_maint_face L121 字段准入门同款镜像——1A4 批
        # param_band 面 param.n/h2 在场、sec_per_hour 等不在 dims 不选中）
        c.constraint.key for c in _loaded_kb()
        if "municipal_aao" in c.unit_kinds
        and set(expression_fields(c.constraint.expression)) <= aao_dims.keys()
    }
    assert offline["maint.municipal_aao.kb.any_fail"] == 0.0  # 全过→汇总键 0.0（kbwire 锚）
    assert offline["maint.municipal_aao.fixgeom.min"] == pytest.approx(-1.0)  # 风机台数 ×2 超载


def test_run_full_calc_wiring_default_and_baseline_faces() -> None:
    """run_full_calc 接线：constraints 缺省 ()=零 kb/fixgeom 键（ratio 仍在）；
    baseline 帧（design/avg）零 maint 键。"""
    bundle = _golden_bundle(())
    plant = bundle.plant
    offline = plant.summary["design_offline_municipal_aao"]
    assert offline["maint.municipal_aao.ratio.n"] == pytest.approx(0.5)  # ratio 面无条件
    assert not any(".kb." in k or ".fixgeom." in k for k in offline)  # 缺省 ()=kb 面不入场
    for base_key in ("design", "avg"):
        assert not any(k.startswith("maint.") for k in plant.summary[base_key]), base_key
    with_kb = _golden_bundle(_loaded_kb()).plant.summary
    assert any(".kb." in k for k in with_kb["design_offline_municipal_aao"])  # 注入后在场


def test_double_run_serialize_byte_identical_with_maintenance() -> None:
    """双跑 serialize 字节同（face 确定性——含 maint 三面键后常驻锚）。"""
    from waterprint.contracts.result_schema import serialize

    first = serialize(_golden_bundle(_loaded_kb()).plant)
    second = serialize(_golden_bundle(_loaded_kb()).plant)
    assert first == second
