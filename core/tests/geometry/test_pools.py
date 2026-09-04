"""pools 镜像测试：池体图元（尺寸同源/水面高程/n_active 排布接线）。

输入:  waterprint.geometry.pools 公开符号
输出:  池体图元契约断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.geometry.pools")
pool_primitives = getattr(_mod, "pool_primitives", None)

pytestmark = pytest.mark.skipif(
    pool_primitives is None,
    reason="实现未就绪：waterprint.geometry.pools（M2）",
)


def _snap(uid: str, dims: dict[str, float]):
    from waterprint.contracts.result_schema import UnitResultSnapshot

    return UnitResultSnapshot(
        unit_id=uid, outflows={}, outqualities={}, dims=dims,
        warnings=(), formula_ids=(),
    )


def _assumptions() -> dict[str, float]:
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    return {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}


def test_entrypoint_frozen() -> None:
    """入口冻结：pool_primitives(unit_result, assumptions)。"""
    assert callable(pool_primitives)


def test_no_recomputation_wiring() -> None:
    """R1 接线断言（M2 实质化）：图元尺寸 == 结果字段值（几何层零业务公式）。

    占位实质化（DRAFT 批总授权先例）：矩形池（cugeshan L/B/H）盒体
    dims 逐项相等 + 圆形池（chuchenchi d/h_total）圆柱 dims 逐项相等——
    取数键=对照表 primitive_dims 槽位（UF-32 表驱动）。
    """
    nodes = pool_primitives(
        _snap("municipal_cugeshan",
              {"L": 1.8, "B": 0.7, "H": 1.0, "h1": 0.05}), _assumptions()
    )
    assert len(nodes) == 1 and nodes[0].primitive.kind == "box"
    assert nodes[0].primitive.dims == {"length": 1.8, "width": 0.7, "depth": 1.0}
    assert nodes[0].semantic == "pool_wall"
    assert nodes[0].source_assumption_keys == ("safety.superheight",)  # R2 来源键

    circular = pool_primitives(
        _snap("municipal_chuchenchi",
              {"d": 9.0, "d_center": 1.4, "h_total": 4.0, "h2": 3.0}),
        _assumptions(),
    )
    assert len(circular) == 1 and circular[0].primitive.kind == "cylinder"
    assert circular[0].primitive.dims == {"diameter": 9.0, "depth": 4.0}


def test_water_surface_level_is_floor_plus_depth() -> None:
    """R3：水面高程 = 池底 + 水深（几何投影唯一允许的加法运算）。"""
    from waterprint.geometry.pools import water_surface_node

    node = water_surface_node(
        _snap("municipal_chenshachi",
              {"h2": 1.25, "h_total": 3.0, "d": 3.0, "l_straight": 4.5}),
        _assumptions(),
    )
    assert node.position[2] == pytest.approx(0.0 + 1.25)  # 池底 0 + 水深 h2
    assert node.primitive.semantic == "water_surface"
    # L5R A-S1：水面足迹=池面投影——box 池取 length/width 同源键
    assert node.primitive.dims["length"] == pytest.approx(4.5)
    assert node.primitive.dims["width"] == pytest.approx(3.0)


def test_water_surface_footprint_cylinder_circumscribed_square() -> None:
    """L5R-A01 真圆：cylinder 池水面足迹=diameter 直读（真圆足迹）。"""
    from waterprint.geometry.pools import water_surface_node

    node = water_surface_node(
        _snap("municipal_chuchenchi",
              {"h2": 3.0, "h_total": 4.0, "d": 9.0, "d_center": 1.4}),
        _assumptions(),
    )
    assert node.primitive.dims["diameter"] == pytest.approx(9.0)
    assert "length" not in node.primitive.dims
    assert "width" not in node.primitive.dims


def test_volume_units_without_pool_slots_yield_explicit_empty() -> None:
    """无池体槽位单元（sludge_hebing 衡算类）= 显式空组（非异常，表声明缺位注记）。

    L7 反转改写：原对象 municipal_aao 已声明 primitive_dims 三槽产 box 组
    （见下用例）——空组断言换仍空单元 sludge_hebing（衡算节点无池体语义，
    D9 测试矩阵裁定）。
    """
    nodes = pool_primitives(
        _snap("sludge_hebing", {"ds_total": 100.0, "q_total": 50.0}),
        _assumptions(),
    )
    assert nodes == ()


def test_aao_volume_unit_pool_box_wired() -> None:
    """L7：AAO 容积法池体图元——表声明三槽后产 box 池壁（几何键直取零推导）。

    构造性 fixture（R-1 更正口径）：非 golden 锚——断言面为三槽透传，
    公式真源=aao 包内测试+golden e2e；数值与 golden 实值的差异无语义
    （本用例只证表行声明→box 取数链，不锚计算结果）。
    """
    nodes = pool_primitives(
        _snap("municipal_aao",
              {"v_total": 17862.22, "h2": 5.0, "a_pool": 3572.444,
               "l_pool_raw": 94.4647, "b_pool_raw": 37.7859,
               "l_pool": 94.5, "b_pool": 38.0, "h_pool": 5.3,
               "v_pool": 17955.0}),
        _assumptions(),
    )
    assert len(nodes) == 1 and nodes[0].primitive.kind == "box"
    assert nodes[0].node_id == "municipal_aao::pool_wall"
    assert nodes[0].primitive.dims == {"length": 94.5, "width": 38.0, "depth": 5.3}
    assert nodes[0].semantic == "pool_wall"
    assert nodes[0].source_assumption_keys == ("safety.superheight",)  # R2 来源键
