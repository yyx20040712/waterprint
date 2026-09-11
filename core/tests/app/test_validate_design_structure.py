"""validate_design_structure 用例（P0-3 呈裁④甲——四族+汇总面）。

输入:  waterprint.app.validate_design_structure（DesignState→错误元组）
输出:  合法图零错误/悬空边/端口不在册/方向错/流体错/未知单元六族断言
"""

from __future__ import annotations

from waterprint.app import validate_design_structure
from waterprint.contracts.project_schema import DesignState
from waterprint.graph.nodes import InvalidNodeError, builtin_ports


def _design(nodes: dict[str, dict[str, object]],
            edges: list[dict[str, object]]) -> DesignState:
    """最小构造（nodes/edges 两面——其余键缺省）。"""
    return DesignState(nodes=nodes, edges=edges)  # type: ignore[arg-type]


def test_valid_graph_zero_errors() -> None:
    """合法图（内置 inlet OUT→包单元 IN 水-水匹配）零错误。"""
    design = _design(
        {
            "inlet": {"kind": "municipal_input", "q_avg_daily": 0.4, "kz": 1.4},
            "municipal_aao": {},
        },
        [{"src": {"unit_id": "inlet", "port_id": "out"},
          "dst": {"unit_id": "municipal_aao", "port_id": "in"}}],
    )
    assert validate_design_structure(design) == ()


def test_dangling_edge_endpoint() -> None:
    """悬空边：端点 unit_id 不在 design.nodes → 错误带定位（呈裁④查①）。"""
    design = _design(
        {"inlet": {"kind": "municipal_input", "q_avg_daily": 0.4, "kz": 1.4}},
        [{"src": {"unit_id": "inlet", "port_id": "out"},
          "dst": {"unit_id": "ghost", "port_id": "in"}}],
    )
    errors = validate_design_structure(design)
    assert len(errors) == 1
    assert "design.edges[0].dst 悬空 unit_id：ghost" in errors[0]


def test_port_not_declared() -> None:
    """端口不在册：端点 port_id 不在 manifest 端口表 → 错误（呈裁④查②）。"""
    design = _design(
        {"inlet": {"kind": "municipal_input", "q_avg_daily": 0.4, "kz": 1.4},
         "municipal_aao": {}},
        [{"src": {"unit_id": "inlet", "port_id": "nope"},
          "dst": {"unit_id": "municipal_aao", "port_id": "in"}}],
    )
    errors = validate_design_structure(design)
    assert len(errors) == 1
    assert "端口未声明：inlet.nope" in errors[0]


def test_direction_mismatch() -> None:
    """方向错：OUT→OUT 违 R2（须 OUT→IN）→ 错误（呈裁④查③）。"""
    design = _design(
        {"inlet": {"kind": "municipal_input", "q_avg_daily": 0.4, "kz": 1.4},
         "municipal_aao": {}},
        [{"src": {"unit_id": "inlet", "port_id": "out"},
          "dst": {"unit_id": "municipal_aao", "port_id": "out"}}],
    )
    errors = validate_design_structure(design)
    assert len(errors) == 1
    assert "边方向非法" in errors[0]


def test_fluid_mismatch() -> None:
    """流体错：泥 OUT→水 IN 违 R1（validate_edge 唯一裁判复用面）。"""
    design = _design(
        {"sludge_ganhua": {}, "municipal_aao": {}},
        [{"src": {"unit_id": "sludge_ganhua", "port_id": "out"},
          "dst": {"unit_id": "municipal_aao", "port_id": "in"}}],
    )
    errors = validate_design_structure(design)
    assert len(errors) == 1
    assert "流体类型不匹配" in errors[0]


def test_unknown_unit_and_kind_accumulate() -> None:
    """未知单元/未知内置 kind 汇总为错误（非拒式——⑦甲中间态呈报）。"""
    design = _design({"nope_unit": {}, "x": {"kind": "bad_kind"}}, [])
    errors = validate_design_structure(design)
    assert len(errors) == 2
    assert "nope_unit" in errors[0]
    assert "未知内置节点 kind" in errors[1]


def test_malformed_edge_shape_accumulates() -> None:
    """边形状非法（缺端点双 string）汇总为错误（_endpoint 同款窄化）。"""
    design = _design(
        {"municipal_aao": {}},
        [{"src": {"unit_id": "municipal_aao"}, "dst": None}],
    )
    errors = validate_design_structure(design)
    assert len(errors) >= 1
    assert any("design.edges[0]" in item for item in errors)


def test_builtin_ports_readonly_face() -> None:
    """builtin_ports 只读面：四 kind 端口表可取+未知 kind=InvalidNodeError
    （构造分面——municipal_input 零构造不触发必填参数校验）。"""
    decls = builtin_ports("municipal_input")
    assert [(p.port_id, p.direction.value) for p in decls] == [("out", "OUT")]
    try:
        builtin_ports("nope")
    except InvalidNodeError:
        pass
    else:
        raise AssertionError("未知 kind 须 InvalidNodeError")
