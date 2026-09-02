"""site 子树 schema 镜像测试：L1 厂区布置（默认态/严格面/约束面/悬空校验/哈希参与）。

输入:  project_schema site 族模型 + parse_project + project.io 确定性序列化
输出:  DesignState 第八键 site 的契约断言（M5 L1 批）
"""

from __future__ import annotations

import pytest

from waterprint.contracts.project_schema import (
    DesignState,
    ProjectFile,
    SiteDesign,
    parse_project,
)
from waterprint.project.io import dumps, dumps_design, loads

# 本地 MINIMAL 副本（v2 形——本目录既有 MINIMAL 为 "1.0" 形，本件钉
# site 批后的当前版装载面；design={} 必过——D7 最小态向 site 键延伸）。
MINIMAL_V2: dict = {
    "format_version": "2.0",
    "design": {},
    "view": {},
    "metadata": {
        "content_hash": "0" * 64,
        "engine_version": "0.1.0",
        "data_version": "0.1.0",
    },
}

# 全子键样例（确定性序列化与哈希参与面载体；浮点含尾差档
# 1.00000000001/1e-12——round(x,10) 归一实证，对照 test_io 双跑形态）。
_SITE_FULL: dict = {
    "structures": {
        "u1": {
            "x": 1.00000000001,  # 尾差档：round(·,10) → 1.0
            "y": 2.0,
            "rotation": 90.0,
            "ground_elevation": 105.5,
        },
        "u2": {"x": 3.0, "y": 1e-12},  # 尾差档：round(·,10) → 0.0
    },
    "roads": [
        {"centerline": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}], "width_m": 6.0}
    ],
    "corridors": [
        {
            "centerline": [{"x": 0.0, "y": 1.0}, {"x": 0.0, "y": 20.0}],
            "width_m": 2.0,
            "kind": "water",
        }
    ],
    "options": {"coord_grid": 10.0, "wind_rose": {"N": 12.5}},
}


def _site_project(site: dict) -> ProjectFile:
    """全 site 样例项目（nodes 覆盖 structures 键——悬空校验前提满足）。"""
    data = dict(MINIMAL_V2)
    data["design"] = {
        "nodes": {"u1": {"pool_length": 10.5}, "u2": {"n": 1}},
        "site": site,
    }
    return parse_project(data)


def test_site_defaults_and_minimal_parse() -> None:
    """默认态：DesignState().site 全默认空容器+options 默认；design={} 过装载且 site 同构。"""
    site = DesignState().site
    assert site.structures == {}
    assert site.roads == []
    assert site.corridors == []
    assert site.options.coord_grid == 10.0
    assert site.options.wind_rose is None
    assert parse_project(dict(MINIMAL_V2)).design.site == site  # 最小态 site=默认


def test_site_unknown_fields_and_non_dict_rejected() -> None:
    """严格面：site 子树未知字段拒（extra=forbid）；SitePoint/摆放非 dict 拒（strict）。"""
    rejects = (
        {"mystery": 1},  # site 未知键
        {"options": {"mystery": 1}},  # options 未知键
        {"structures": {"u1": 42}},  # 摆放非 dict
        {"roads": [{"centerline": [42, {"x": 0.0, "y": 0.0}], "width_m": 1.0}]},  # 点非 dict
    )
    for bad in rejects:
        data = dict(MINIMAL_V2)
        data["design"] = {"nodes": {"u1": {}}, "site": bad}
        with pytest.raises(Exception, match=".+"):  # 行为=拒绝（消息面随 pydantic 版本）
            parse_project(data)


def test_site_constraint_faces() -> None:
    """约束面：centerline<2 点拒；width_m≤0 拒；kind 空串拒；rotation 缺省=0.0、
    ground_elevation=None 合法（§三定稿：rotation 为 strict float——显式 None 拒）。"""
    line2 = [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}]
    rejects = (
        {"roads": [{"centerline": [{"x": 0.0, "y": 0.0}], "width_m": 6.0}]},
        {"corridors": [{"centerline": [line2[0]], "width_m": 2.0, "kind": "w"}]},
        {"roads": [{"centerline": line2, "width_m": 0.0}]},
        {"roads": [{"centerline": line2, "width_m": -1.0}]},
        {"corridors": [{"centerline": line2, "width_m": 0.0, "kind": "w"}]},
        {"corridors": [{"centerline": line2, "width_m": 2.0, "kind": ""}]},
    )
    for bad in rejects:
        data = dict(MINIMAL_V2)
        data["design"] = {"site": bad}
        with pytest.raises(Exception, match=".+"):
            parse_project(data)
    legal = dict(MINIMAL_V2)
    legal["design"] = {
        "nodes": {"u1": {}},
        "site": {"structures": {"u1": {"x": 1.0, "y": 2.0, "ground_elevation": None}}},
    }
    placement = parse_project(legal).design.site.structures["u1"]
    assert placement.rotation == 0.0  # 缺省合法（编辑器自由角零姿态）
    assert placement.ground_elevation is None  # 可选标高显式 None 合法
    explicit = dict(MINIMAL_V2)
    explicit["design"] = {
        "nodes": {"u1": {}},
        "site": {"structures": {"u1": {"x": 1.0, "y": 2.0, "rotation": None}}},
    }
    with pytest.raises(Exception, match=".+"):  # rotation: float 非 Optional——严格拒
        parse_project(explicit)


def test_site_structures_keys_must_exist_in_nodes() -> None:
    """悬空校验：structures 键∉design.nodes 拒（match 悬空）；nodes 有而 site 无=合法未布置态。"""
    dangling = dict(MINIMAL_V2)
    dangling["design"] = {
        "nodes": {"u1": {}},
        "site": {"structures": {"ghost": {"x": 1.0, "y": 1.0}}},
    }
    with pytest.raises(Exception, match="悬空"):
        parse_project(dangling)
    unbuilt = dict(MINIMAL_V2)
    unbuilt["design"] = {"nodes": {"u1": {}}}  # 反向：有节点无摆放——零反向校验
    assert parse_project(unbuilt).design.site.structures == {}


def test_site_serialization_deterministic_roundtrip() -> None:
    """确定性：全子键样例双跑字节同+往返无损；尾差浮点 round(x,10) 归一进输出。"""
    first = dumps(_site_project(_SITE_FULL))
    assert dumps(_site_project(_SITE_FULL)) == first  # 双跑字节同（test_io 同款形态）
    assert dumps(loads(first)) == first  # 往返无损（round 幂等前提）
    assert first.endswith("\n") and "\r" not in first  # 尾换行统一 \n
    assert '"x":1.0' in first  # 1.00000000001 → 1.0（归一实证）
    assert '"y":0.0' in first  # 1e-12 → 0.0（归一实证）
    assert '"kind":"water"' in first  # 开放 kind 字面进序列化面


def test_site_participates_in_design_digest() -> None:
    """哈希参与：同 project 仅 site 差异 → dumps_design 输出不同（site 进 content_hash 面）。"""
    without = _site_project({})  # site 缺省（等价全默认）
    with_site = _site_project(_SITE_FULL)  # 同 nodes——唯一差异=site
    text_without = dumps_design(without.design)
    text_with = dumps_design(with_site.design)
    assert text_without != text_with  # site 差异必变（第八键参与哈希面）
    assert '"site"' in text_with  # site 键确在序列化树内（非空壳对照）
