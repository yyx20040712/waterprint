"""formulas 镜像测试：公式注册表（登记/量纲静态校验/溯源门槛/apply 产迹）。

输入:  waterprint.registry.formulas 公开符号
输出:  注册表契约断言（溯源基石——§3 保证 5、§16 A1 防线）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.registry.formulas")
FormulaSpec = getattr(_mod, "FormulaSpec", None)
register = getattr(_mod, "register", None)
by_id = getattr(_mod, "by_id", None)
validate_all = getattr(_mod, "validate_all", None)

pytestmark = pytest.mark.skipif(
    None in (FormulaSpec, register, by_id, validate_all),
    reason="实现未就绪：waterprint.registry.formulas（M1）",
)


def _spec(**overrides) -> object:
    data = {
        "formula_id": "test-demo-formula",
        "expression": "V = Q * t",
        "symbols": {"Q": ("FLOW", "设计流量"), "t": ("TIME", "水力停留时间")},
        "output_dim": "VOLUME",
        "norm_ref": "GB 50014-2021 §x.x.x",
    }
    data.update(overrides)
    return FormulaSpec(**data)


def test_register_then_query_roundtrip() -> None:
    """登记 → 按 ID 查询往返一致。"""
    spec = _spec()
    register(spec)
    assert by_id("test-demo-formula") is spec


def test_missing_norm_ref_rejected() -> None:
    """R2：无条文出处的公式禁止登记。"""
    with pytest.raises(Exception, match=".+"):
        register(_spec(norm_ref=""))


def test_dimension_mismatch_rejected_at_load() -> None:
    """R1：量纲不匹配在登记/加载期拒绝（不是运行时警告）。"""
    bad = FormulaSpec(
        formula_id="test-bad-dim",
        expression="Q = C",
        symbols={"C": ("CONCENTRATION", "浓度")},
        output_dim="FLOW",
        norm_ref="GB 50014-2021 §x.x.x",
    )
    with pytest.raises(Exception, match=".+"):
        register(bad)


def test_duplicate_id_rejected() -> None:
    """formula_id 全库唯一（改名 = 破坏可复算，只能新增）。"""
    register(_spec())
    with pytest.raises(Exception, match=".+"):
        register(_spec())
