"""grid 镜像测试：离散网格（笛卡尔积/护栏/确定性/dtype）。

输入:  waterprint.solution.grid 公开符号 + manifest 参数声明
输出:  网格构建断言（≤4^k 护栏是 ADR-005 的机器强制）
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint.solution.grid")
build_grid = getattr(_mod, "build_grid", None)
GridTooLarge = getattr(_mod, "GridTooLarge", None)

pytestmark = pytest.mark.skipif(
    None in (build_grid, GridTooLarge),
    reason="实现未就绪：waterprint.solution.grid（M1）",
)


def _param(field_id: str, values: list[float]) -> dict:
    return {"field_id": field_id, "dim": "DIMENSIONLESS", "values": values}


def test_cartesian_product_shape() -> None:
    """R1：3×2 网格 total = 6 且展平行数 = 6。"""
    grid = build_grid([_param("a", [1.0, 2.0, 3.0]), _param("b", [0.5, 1.5])])
    assert grid.total == 6
    assert len(grid.array) == 6


def test_too_many_dimensions_rejected() -> None:
    """R1：总组合数超过护栏（默认上限）→ GridTooLarge。

    B2 A1 重锚：护栏基数 4→7 后 5^10 不再拒——重锚为 8 档（8^10 > 7^10）。
    """
    big = [
        _param(f"f{i}", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        for i in range(10)
    ]  # 8^10 超缺省护栏 7^10
    with pytest.raises(GridTooLarge):
        build_grid(big)


def test_grid_is_deterministic() -> None:
    """R2：同声明同网格（字段按 field_id 字典序稳定）。"""
    params = [_param("b", [1.0, 2.0]), _param("a", [3.0])]
    first = build_grid(params)
    second = build_grid(list(reversed(params)))
    assert first.fields == second.fields
    assert str(first.array) == str(second.array)


def test_guardrail_overrides_tighten() -> None:
    """B2 PD13 A2：overrides 收紧护栏——5 档单维在 base=4 覆盖下拒（5 > 4^1）。"""
    with pytest.raises(GridTooLarge):
        build_grid(
            [_param("n", [2.0, 3.0, 4.0, 5.0, 6.0])],
            overrides={"solution.grid.base_per_dim": 4.0},
        )


def test_guardrail_overrides_raise() -> None:
    """B2 PD13 A2：overrides 抬升护栏——8 档单维（默认 base 拒）在 base=8 覆盖下过。"""
    grid = build_grid(
        [_param("n", [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])],
        overrides={"solution.grid.base_per_dim": 8.0},
    )
    assert grid.total == 8
