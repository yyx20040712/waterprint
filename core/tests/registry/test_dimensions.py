"""dimensions 镜像测试：维度字段注册表（单位元数据层——单位双轨终结点）。

输入:  waterprint.registry.dimensions 公开符号
输出:  登记/查询/dtype 断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.registry.dimensions")
FieldSpec = getattr(_mod, "FieldSpec", None)
register_dimension = getattr(_mod, "register_dimension", None)
dimension_of = getattr(_mod, "dimension_of", None)
dtype_of = getattr(_mod, "dtype_of", None)

pytestmark = pytest.mark.skipif(
    None in (FieldSpec, register_dimension, dimension_of, dtype_of),
    reason="实现未就绪：waterprint.registry.dimensions（M1）",
)


def test_register_and_query_roundtrip() -> None:
    spec = FieldSpec(
        field_id="test_pool_length", dim="LENGTH", unit="m",
        i18n_key="fields.pool_length", category="geometry",
    )
    register_dimension(spec)
    assert dimension_of("test_pool_length") is spec


def test_unit_must_match_dimension() -> None:
    """R2：单位必须等于该量类的规范单位（不一致拒绝）。"""
    with pytest.raises(Exception, match=".+"):
        register_dimension(FieldSpec(
            field_id="test_bad_unit", dim="FLOW", unit="m",
            i18n_key="fields.bad", category="geometry",
        ))


def test_duplicate_field_id_rejected() -> None:
    """R3：字段 ID 唯一（不可改名——序列化与历史迹依赖）。"""
    spec = FieldSpec(
        field_id="test_dup_field", dim="LENGTH", unit="m",
        i18n_key="fields.dup", category="geometry",
    )
    register_dimension(spec)
    with pytest.raises(Exception, match=".+"):
        register_dimension(spec)


def test_unknown_field_query_raises() -> None:
    """未知字段查询抛领域异常（禁止返回 None 假装成功）。"""
    with pytest.raises(Exception, match=".+"):
        dimension_of("no_such_field_anywhere")
