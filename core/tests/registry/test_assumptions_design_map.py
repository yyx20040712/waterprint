"""assumptions_design_map 镜像测试：FD 护栏键伴生件（类注入防环形态）。

输入:  waterprint.registry.assumptions_design_map 公开符号
输出:  FD 键声明契约断言（镜像规则——结构门禁 test_mirror_rule 要求件）
"""

from __future__ import annotations

import importlib

_mod = importlib.import_module("waterprint.registry.assumptions_design_map")
design_map_entries = getattr(_mod, "design_map_entries", None)


def test_entries_pass_assumption_guards() -> None:
    """类注入形态：以真 Assumption/TuningImpact 构造通过六守卫（防环落地证明）。"""
    from waterprint.registry.assumptions import Assumption, TuningImpact

    entries = design_map_entries(Assumption, TuningImpact)  # type: ignore[misc]
    assert len(entries) >= 1
    for entry in entries:
        assert isinstance(entry, Assumption)


def test_fd_key_registered_in_default_assumptions() -> None:
    """主件装配闭环：FD 键进 DEFAULT_ASSUMPTIONS（assumption() 正门可达）。"""
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS, assumption

    keys = DEFAULT_ASSUMPTIONS.keys()
    assert "solution.design_map.max_points" in keys
    assert assumption("solution.design_map.max_points", {}) == 2500.0
    assert assumption("solution.design_map.max_points", {"solution.design_map.max_points": 64.0}) == 64.0


def test_fd_key_metadata_provenance() -> None:
    """出处纪律（R2 无出处不入库）：source 含 PD4 终裁+待追认字样。"""
    from waterprint.registry.assumptions import Assumption, TuningImpact

    entry = design_map_entries(Assumption, TuningImpact)[0]  # type: ignore[misc]
    assert entry.key == "solution.design_map.max_points"
    assert "PD4" in entry.source and "追认" in entry.source
    assert entry.dim.value == "DIMENSIONLESS"
    assert entry.tuning_impact is not None and entry.tuning_impact.constraint_keys == ()
