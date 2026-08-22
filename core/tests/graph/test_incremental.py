"""incremental 镜像测试：脏传播与缓存（语义铁律 = 字节级等价全量）。

输入:  waterprint.graph.incremental 公开符号
输出:  脏范围/缓存键三元组失配断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.graph.incremental")
recompute_scope = getattr(_mod, "recompute_scope", None)
CacheKey = getattr(_mod, "CacheKey", None)

pytestmark = pytest.mark.skipif(
    None in (recompute_scope, CacheKey),
    reason="实现未就绪：waterprint.graph.incremental（M1）",
)


def test_cache_key_contains_repro_triple() -> None:
    """R3：缓存键含三元组——engine/data 版本变化自动失配（§16 A8）。"""
    import dataclasses

    names = {f.name for f in dataclasses.fields(CacheKey)}
    assert {"unit_id", "design_hash", "condition_key", "engine_version", "data_version"} <= names


def test_cache_entries_are_immutable() -> None:
    """§17.2：条目不可变（失效=键不再命中，无锁模型的前提）。"""
    import dataclasses

    assert CacheKey.__dataclass_params__.frozen
