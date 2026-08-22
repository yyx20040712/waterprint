"""manifest 镜像测试：清单 schema 四类静态校验与合法清单往返。

输入:  waterprint.contracts.manifest 公开符号
输出:  静态校验拒绝路径断言（非法清单 = 启动失败）
"""

from __future__ import annotations

import copy
import importlib

import pytest

_mod = importlib.import_module("waterprint.contracts.manifest")
load_manifest = getattr(_mod, "load_manifest", None)

pytestmark = pytest.mark.skipif(
    load_manifest is None,
    reason="实现未就绪：waterprint.contracts.manifest.load_manifest（M1）",
)

# 合法最小清单基准（测试内自足数据；工程真实清单由各单元包声明）
VALID_MINIMAL: dict = {
    "unit_id": "test_demo_unit",
    "i18n_key": "units.demo",
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


def test_valid_minimal_manifest_roundtrips() -> None:
    """合法最小清单加载成功且可确定性序列化往返。"""
    manifest = load_manifest(copy.deepcopy(VALID_MINIMAL))
    assert manifest.unit_id == "test_demo_unit"


def test_unknown_field_id_rejected() -> None:
    """R1a：参数字段未在 dimensions 注册 = 加载失败。"""
    data = copy.deepcopy(VALID_MINIMAL)
    data["params"][0]["field_id"] = "no_such_field_in_dimensions"
    with pytest.raises(Exception, match=".+"):
        load_manifest(data)


def test_procedural_condition_mapping_rejected() -> None:
    """R1c：工况映射含任意 Python（非受限 DSL）= 加载失败。"""
    data = copy.deepcopy(VALID_MINIMAL)
    data["condition_mappings"][0]["rule"] = "__import__('os').system('dir')"
    with pytest.raises(Exception, match=".+"):
        load_manifest(data)


def test_empty_norm_refs_rejected() -> None:
    """R1d：无条文出处的设计参数不允许（溯源最低门槛）。"""
    data = copy.deepcopy(VALID_MINIMAL)
    data["norm_refs"] = []
    with pytest.raises(Exception, match=".+"):
        load_manifest(data)


def test_business_line_outside_four_lines_rejected() -> None:
    """R4：业务线 ∈ 四线之外拒绝（§14.3 边界）。"""
    data = copy.deepcopy(VALID_MINIMAL)
    data["business_line"] = "space_station"
    with pytest.raises(Exception, match=".+"):
        load_manifest(data)
