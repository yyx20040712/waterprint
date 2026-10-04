"""jobs calc_inputs 镜像测试：standards+kb 双装载（kbwire-20261003）。

输入:  waterprint_server.jobs.calc_inputs（worker calc job 数据装配件）
输出:  三面行为断言——双装载计数锚（standards 12+kb 42）/kb 路径缺失
       InvalidConstraintError fail-fast/返回型冻结（双 tuple+元素型）。
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.jobs.calc_inputs")
calc_inputs = getattr(_mod, "calc_inputs")


def test_calc_inputs_double_load_counts(test_settings) -> None:  # type: ignore[no-untyped-def]
    """双装载计数锚：standards=gb18918 双级 2 档 12 限值（effluent 条目）+
    kb 42（1.9.0 全量——1A1 批 +input_band 7/1A3 批 +mass_balance 1）。"""
    standards, constraints = calc_inputs(Path(str(test_settings.data_dir)))
    assert len(standards) == 2  # level_a/level_b 两档（EffluentStandard 按标准分组）
    assert sum(len(item.limits) for item in standards) == 12  # 双级×六项限值
    assert len(constraints) == 42  # kb 1.9.0（input_band 7+mass_balance 1 零筛全量）
    keys = {item.constraint.key for item in constraints}
    assert "site.boundary_containment" in keys  # boundary_check 亦全量（face 自筛）
    assert "inlet.kz_band" in keys  # input_band 亦全量（R2 零筛选注入）
    assert "sludge.primary_load_band" in keys  # mass_balance 亦全量（1A3 批）


def test_calc_inputs_missing_kb_fails_fast(tmp_path: Path) -> None:
    """kb 路径缺失=数据装配缺陷 fail-fast（InvalidConstraintError——D6 同口径）。"""
    from waterprint.solution.constraints import InvalidConstraintError

    with pytest.raises(InvalidConstraintError, match="constraint_kb 文件缺失"):
        calc_inputs(tmp_path)


def test_calc_inputs_return_type_frozen(test_settings) -> None:  # type: ignore[no-untyped-def]
    """返回型冻结：tuple[tuple[EffluentStandard, ...], tuple[KbConstraint, ...]]。"""
    from waterprint import app as core
    from waterprint.contracts.quality import EffluentStandard

    standards, constraints = calc_inputs(Path(str(test_settings.data_dir)))
    assert isinstance(standards, tuple) and isinstance(constraints, tuple)
    assert all(isinstance(item, EffluentStandard) for item in standards)
    assert all(isinstance(item, core.KbConstraint) for item in constraints)
