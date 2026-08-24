"""manifest_validation 镜像测试：装配槽 bind-once 守卫与被拒重绑后槽完好性。

输入:  waterprint.contracts.manifest_validation 公开符号（经 manifest 再导出）
输出:  装配槽重复绑定拒绝 + 被拒重绑后 R1a 查询槽保持原绑定实证
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.manifest_validation")
bind_dimension_lookup = getattr(_mod, "bind_dimension_lookup", None)

_manifest_mod = importlib.import_module("waterprint.contracts.manifest")
load_manifest = getattr(_manifest_mod, "load_manifest", None)

# 装配前置（R1a）：dimensions 注册表导入即经 bind_dimension_lookup 绑定查询
# 钩子（sys.modules 缓存保证进程内仅绑定一次——bind-once 的"已绑定"前提；
# 全量运行时若已被他文件导入则此处直接命中缓存，同样只绑一次）。
importlib.import_module("waterprint.registry.dimensions")

pytestmark = pytest.mark.skipif(
    bind_dimension_lookup is None or load_manifest is None,
    reason="实现未就绪：waterprint.contracts.manifest_validation（M1）",
)

# 最小合法清单（test_manifest.py VALID_MINIMAL 同款结构；unit_id 独立，
# 防与其他镜像用例的语义纠缠）
_MINIMAL: dict = {
    "unit_id": "mirror_validation_unit",
    "i18n_key": "units.mirror",
    "version": "1.0.0",
    "business_line": "municipal",
    "params": [
        {"field_id": "pool_length", "dim": "LENGTH", "default": 10.0},
    ],
    "ports": [
        {"port_id": "in", "fluid": "WATER", "direction": "IN"},
        {"port_id": "out", "fluid": "WATER", "direction": "OUT"},
    ],
    "removal_refs": {},
    "norm_refs": ["GB 50014-2021 §6.2.4"],
    "condition_mappings": [
        {"target": "n_active", "rule": "n if pool.all_pools else n - 1"},
    ],
    "constraint_refs": [],
}


def test_rebind_rejected() -> None:
    """D2/GR-36 记档豁免：装配槽一次性注入，重复绑定 = RuntimeError。"""
    with pytest.raises(RuntimeError, match="装配槽重复绑定"):
        bind_dimension_lookup(lambda field_id: None)


def test_slot_keeps_binding_after_rejected_rebind() -> None:
    """被拒重绑不改槽状态：R1a 查询槽完好，最小清单仍正常构造。"""
    manifest = load_manifest(_MINIMAL)
    assert manifest.unit_id == "mirror_validation_unit"
    assert manifest.params[0].field_id == "pool_length"
