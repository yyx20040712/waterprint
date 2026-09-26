"""assumptions_joint 镜像测试：B4-3 联合枚举护栏键伴生件（类注入防环形态）。

输入:  waterprint.registry.assumptions_joint 公开符号
输出:  solution.joint.* 键族契约断言（B4-3 定稿件 §二/W7/W8/N2——11 float 键）
"""

from __future__ import annotations

import importlib

_mod = importlib.import_module("waterprint.registry.assumptions_joint")
joint_entries = getattr(_mod, "joint_entries", None)


def test_entries_pass_assumption_guards() -> None:
    """类注入形态：以真 Assumption/TuningImpact 构造通过六守卫（防环落地证明）。"""
    from waterprint.registry.assumptions import Assumption, TuningImpact

    entries = joint_entries(Assumption, TuningImpact)  # type: ignore[misc]
    assert len(entries) == 12  # 批2b +capex 键（11→12）
    for entry in entries:
        assert isinstance(entry, Assumption)


def test_joint_keys_registered_in_default_assumptions() -> None:
    """主件装配闭环：solution.joint.* 全量进 DEFAULT_ASSUMPTIONS（正门可达）。"""
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS, assumption

    keys = DEFAULT_ASSUMPTIONS.keys()
    expected = {
        "solution.joint.max_units": 6.0,
        "solution.joint.beam_width": 5.0,
        "solution.joint.max_total_rows": 500000.0,
        "solution.joint.timeout_s": 120.0,
        "solution.joint.max_full_plant_evals": 25.0,
        "solution.joint.relax_factor": 2.0,
        "solution.joint.stage_proxy_weights": 0.5,
        "solution.joint.objective_weight_opex": 0.25,
        "solution.joint.objective_weight_energy": 0.3,
        "solution.joint.objective_weight_carbon": 0.2,
        "solution.joint.objective_weight_capex": 0.25,
        "solution.joint.validation_conditions": 0.0,
    }
    for key, default in expected.items():
        assert key in keys, f"缺键 {key}"
        assert assumption(key, {}) == default
        assert assumption(key, {key: default + 1.0}) == default + 1.0  # 覆盖优先


def test_joint_key_metadata_provenance() -> None:
    """出处纪律（R2 无出处不入库）：source 含 B4-3 终裁字样+全 DIMENSIONLESS。"""
    from waterprint.registry.assumptions import Assumption, TuningImpact

    entries = joint_entries(Assumption, TuningImpact)  # type: ignore[misc]
    for entry in entries:
        assert entry.key.startswith("solution.joint.")
        assert "B4-3" in entry.source and "追认" in entry.source
        assert entry.dim.value == "DIMENSIONLESS"
        assert entry.tuning_impact is not None


def test_manifest_load_order_unchanged() -> None:
    """装载序零扰动：YAML 包 4 件装载序不变+[0] safety.superheight 锚不动。"""
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    assert DEFAULT_ASSUMPTIONS[0].key == "safety.superheight"
    yaml_keys = [item.key for item in DEFAULT_ASSUMPTIONS]
    joint_keys = [k for k in yaml_keys if k.startswith("solution.joint.")]
    assert len(joint_keys) == 12  # 批2b +capex 键
    # 伴生件尾挂：joint 键全在 YAML 键之后（design_map 伴生先例同制）
    assert yaml_keys.index("solution.design_map.max_points") < yaml_keys.index(
        "solution.joint.max_units"
    )
