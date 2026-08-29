"""units 服务镜像测试：目录/假设投影、D1 键集钳制、builtin 面、缓存单例。

输入:  waterprint_server.services.units 公开符号
输出:  服务契约断言（META1 D1~D7 端点形态的服务面）
"""

from __future__ import annotations

import importlib
import json

_mod = importlib.import_module("waterprint_server.services.units")
list_units = getattr(_mod, "list_units")
list_assumptions = getattr(_mod, "list_assumptions")
_unit_names: dict[str, str] = getattr(_mod, "_UNIT_NAMES")

_core = importlib.import_module("waterprint.app")

# 内置四 kind 序（GOLDEN3 D1 后冻结序——services 投影与 core nodes 同源声明面）
_BUILTIN_KINDS = ("municipal_input", "junction", "quality_edit", "recycle_junction")


def test_units_catalog_shape_order_and_ports() -> None:
    """R1：36 条=32 包（unit_id 序）+4 内置（kind 序排末）；端口表真源逐字投影。"""
    catalog = list_units()
    entries = catalog.units
    assert len(entries) == 36
    packaged = [entry for entry in entries if entry.kind == "unit"]
    builtin = [entry for entry in entries if entry.kind == "builtin"]
    assert len(packaged) == 32 and len(builtin) == 4
    assert [entry.unit_id for entry in packaged] == sorted(
        entry.unit_id for entry in packaged
    )  # 注册表单元按 unit_id 排序
    assert [entry.unit_id for entry in builtin] == list(_BUILTIN_KINDS)  # 内置排末 kind 序
    assert all(entry.name_zh and entry.business_line for entry in entries)  # 中文名/业务线全量在册
    aao = next(entry for entry in entries if entry.unit_id == "municipal_aao")
    assert [(p.port_id, p.fluid, p.direction) for p in aao.ports] == [
        ("in", "WATER", "IN"),
        ("out", "WATER", "OUT"),
        ("sludge_out", "SLUDGE", "OUT"),
    ]  # 冻结 §三：aao 三口
    hebing = next(entry for entry in entries if entry.unit_id == "sludge_hebing")
    assert [(p.port_id, p.fluid, p.direction) for p in hebing.ports] == [
        ("in_primary", "SLUDGE", "IN"),
        ("in_bio", "SLUDGE", "IN"),
        ("in_chem", "SLUDGE", "IN"),
        ("out", "SLUDGE", "OUT"),
    ]  # 冻结 §三：hebing 三入一口
    recycle = sorted(
        (entry.unit_id, p.port_id) for entry in entries for p in entry.ports if p.recycle
    )
    assert recycle == [("sludge_nongsuo", "sup"), ("sludge_tuoshui", "filtrate")]  # 全库恰两回流口


def test_unit_names_keys_clamp_discovered_union_builtin() -> None:
    """D1 钳制：_UNIT_NAMES 键集恰等 discover_units 键集∪四 kind（缺名/多影即红）。"""
    discovered = set(_core.discover_units())
    assert len(discovered) == 32
    assert set(_unit_names) == discovered | set(_BUILTIN_KINDS)


def test_param_depth_five_fields_from_manifest() -> None:
    """D3：参数五字段全出（dim=DimKey 枚举名；default/range/grid manifest 原样）。"""
    catalog = list_units()
    aao = next(entry for entry in catalog.units if entry.unit_id == "municipal_aao")
    n = next(p for p in aao.params if p.field_id == "n")
    assert (n.dim, n.default) == ("DIMENSIONLESS", 2.0)
    assert n.grid == (2.0, 3.0, 4.0, 5.0, 6.0)
    assert n.range is None
    ns = next(p for p in aao.params if p.field_id == "ns")
    assert ns.grid is None
    assert ns.range is not None and (ns.range.min, ns.range.max) == (0.05, 0.15)


def test_builtin_projection_params_and_ports() -> None:
    """D7：builtin 参数面/端口表投影（default/range/grid=null 诚实缺省）。"""
    catalog = list_units()
    by_id = {entry.unit_id: entry for entry in catalog.units if entry.kind == "builtin"}
    municipal = by_id["municipal_input"]
    assert [(p.field_id, p.dim) for p in municipal.params] == [
        ("q_avg_daily", "FLOW"),
        ("kz", "DIMENSIONLESS"),
        ("BOD5", "CONCENTRATION"),
        ("CODCR", "CONCENTRATION"),
        ("NH3N", "CONCENTRATION"),
        ("SS", "CONCENTRATION"),
        ("TN", "CONCENTRATION"),
        ("TP", "CONCENTRATION"),
    ]  # 必需两键+INDICATORS 六键（sorted 序确定性）
    assert all(
        p.default is None and p.range is None and p.grid is None for p in municipal.params
    )  # 无声明面=诚实缺省
    assert [(p.port_id, p.fluid, p.direction) for p in municipal.ports] == [("out", "WATER", "OUT")]
    quality = by_id["quality_edit"]
    assert [p.field_id for p in quality.params] == [
        "BOD5", "CODCR", "NH3N", "SS", "TN", "TP"
    ]
    assert by_id["junction"].params == () and by_id["recycle_junction"].params == ()
    assert [(p.port_id, p.fluid, p.direction) for p in by_id["junction"].ports] == [
        ("in_1", "WATER", "IN"),
        ("in_2", "WATER", "IN"),
        ("out", "WATER", "OUT"),
    ]
    assert [(p.port_id, p.fluid, p.direction) for p in by_id["recycle_junction"].ports] == [
        ("in", "SLUDGE", "IN"),
        ("out", "WATER", "OUT"),
    ]  # 泥进水出=转换节点（冻结 §二）


def test_assumptions_projection_twenty_one_entries() -> None:
    """R3：21 条六字段取五（tuning_direction 在场；首条 safety.superheight）。"""
    catalog = list_assumptions()
    entries = catalog.assumptions
    assert len(entries) == 21
    assert entries[0].key == "safety.superheight"  # registry 声明序（[0] 锚）
    assert (entries[0].dim, entries[0].default) == ("LENGTH", 0.3)
    assert all(entry.source and entry.note and entry.tuning_direction for entry in entries)
    keys = [entry.key for entry in entries]
    assert len(set(keys)) == len(keys)  # 键唯一（AssumptionSet 构造期保证的镜像）


def test_cache_singleton_and_double_run_deterministic() -> None:
    """R4/D5：lru_cache 单例（同一冻结实例）+双跑 sort_keys 字节同。"""
    assert list_units() is list_units()
    assert list_assumptions() is list_assumptions()
    first = json.dumps(list_units().model_dump(), sort_keys=True, ensure_ascii=False)
    second = json.dumps(list_units().model_dump(), sort_keys=True, ensure_ascii=False)
    assert first == second
