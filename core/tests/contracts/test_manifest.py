"""manifest 镜像测试：清单 schema 四类静态校验与合法清单往返。

输入:  waterprint.contracts.manifest 公开符号
输出:  静态校验拒绝路径断言（非法清单 = 启动失败）
"""

from __future__ import annotations

import copy
import importlib
from pathlib import Path

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


def test_label_zh_roundtrip_and_default_none() -> None:
    """B2 PD1/PD3：label_zh 声明值透传 + 可选键缺省 None。"""
    with_label = copy.deepcopy(VALID_MINIMAL)
    with_label["params"][0]["label_zh"] = "池长"
    manifest = load_manifest(with_label)
    assert manifest.params[0].label_zh == "池长"
    # 可选键：不声明 label_zh 的既有清单零改动可加载（VALID_MINIMAL 夹具绿）
    default_manifest = load_manifest(copy.deepcopy(VALID_MINIMAL))
    assert default_manifest.params[0].label_zh is None


# B2 PD3 完备性巡检：32 个单元数据件（units_lib/<line>/<unit>/manifest.py
# 两层深度）。_template/manifest.py 是纯规格头样例件（无 params 条目零数据），
# 不在 glob 两层命中面内——33 件口径中的它不计入 233 条统计（简报 PD3 注记）。
_CORE_ROOT = Path(__file__).resolve().parents[2]
_UNITS_ROOT = _CORE_ROOT / "waterprint" / "units_lib"
_UNIT_DIRS = sorted(path.parent for path in _UNITS_ROOT.glob("*/*/manifest.py"))


@pytest.mark.parametrize(
    "unit_dir", _UNIT_DIRS, ids=lambda d: f"{d.parent.name}_{d.name}"
)
def test_unit_params_label_zh_complete(unit_dir: Path) -> None:
    """B2 PD3 巡检：每单元全参数 label_zh 非空 str（233 条无开天窗拦截）。"""
    parts = unit_dir.relative_to(_CORE_ROOT).parts
    module = importlib.import_module(".".join(parts) + ".manifest")
    params = module.manifest.params
    assert params, f"{unit_dir} 无参数条目（异常数据件）"
    for spec in params:
        assert isinstance(spec.label_zh, str) and spec.label_zh, (
            f"{unit_dir} 参数 {spec.field_id} label_zh 缺失或空（B2 全量填充开天窗）"
        )


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
