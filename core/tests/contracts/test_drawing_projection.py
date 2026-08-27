"""drawing_projection 对账测试：UF-32 对照表 21 单元 dims 键全覆盖（Ruling ①）。

输入:  waterprint.contracts.drawing_projection.PROJECTION_TABLE + golden 项目
       （municipal_34760，11 单元）+ 逐单元单点图（tiaojiechi→cass 补齐
       13 市政）+ 矿井链单点图（input→…→ziwai 补齐 8 矿井，M3D1）
输出:  表覆盖对账断言（五类并集∪non_drawn==compute 实跑键集——21 单元全）
       + 分线键集 disjoint（聚合无静默覆盖的机器守卫）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：DRAFT 批 D1（Ruling ① UF-32 方案②）；M3D1 扩矿井 8 单元
# （分线表 drawing_projection_mine——聚合正门消费）。表是冻结声明面，
# 测试以 golden/链式单点图实跑为证逐单元对账——表漏键/多键即红
# （禁静默遗漏的机器强制）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from pathlib import Path

import pytest

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.drawing_projection_mine import MINE_PROJECTIONS
from waterprint.contracts.drawing_projection_municipal import (
    MUNICIPAL_PROJECTIONS,
)
from waterprint.contracts.quantity import DimKey

pytestmark = [pytest.mark.golden]

_EXPECTED_UNITS: frozenset[str] = frozenset({
    "mine_water_chenshachi", "mine_water_cifenli", "mine_water_gaomidu",
    "mine_water_input", "mine_water_ningjiao", "mine_water_tiaojiechi",
    "mine_water_vxinglvchi", "mine_water_ziwai",
    "municipal_aao", "municipal_bashi_jiliangcao", "municipal_cass",
    "municipal_chenshachi", "municipal_chuchenchi", "municipal_cugeshan",
    "municipal_erchunchi", "municipal_gaomidu", "municipal_tiaojiechi",
    "municipal_vxinglvchi", "municipal_wushui_tisheng",
    "municipal_xigeshan", "municipal_ziwai",
})

# 矿井水线链序（input 为图源注入点——不接收入边；其余七单元链式相连。
# 端口 in/out 按 8 包 manifest 端口声明实读：全包两口 WATER in/out）
_MINE_CHAIN: tuple[str, ...] = (
    "mine_water_input", "mine_water_tiaojiechi", "mine_water_chenshachi",
    "mine_water_ningjiao", "mine_water_cifenli", "mine_water_gaomidu",
    "mine_water_vxinglvchi", "mine_water_ziwai",
)


def _run_design_dims(payload: dict[str, object], expected: dict[str, object],
                     data_dir: Path) -> dict[str, frozenset[str]]:
    """正门实跑（design 工况）→ unit_id → dims 键集（app 正门口径）。"""
    from waterprint.app import run_full_calc
    from waterprint.contracts.condition import build_condition_set
    from waterprint.contracts.project_schema import ProjectFile
    from waterprint.contracts.run_env import RunEnv
    from waterprint.registry import load_coefficients
    from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS

    project = ProjectFile.model_validate(payload)
    conditions = build_condition_set(expected["checked_units"])  # type: ignore[index]
    lib = load_coefficients(data_dir)
    env = RunEnv(
        engine_version=expected["generated"]["engine_version"],  # type: ignore[index]
        data_version=expected["generated"]["data_version"],  # type: ignore[index]
        assumptions={entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS},
        coefficients=lib, price_book={}, trace_sink=None, engine_params={},
    )
    plant = run_full_calc(project, conditions, env).plant
    return {
        unit_id: frozenset(snapshot.dims)
        for unit_id, snapshot in plant.conditions["design"].items()
    }


@pytest.fixture(scope="module")
def live_dims(golden_data_dir: Path) -> dict[str, frozenset[str]]:
    """21 单元实跑键集（模块级一次）：golden 11 + 市政单点图补 2 + 矿井链 8。"""
    case = golden_data_dir / "municipal_34760"
    payload = json.loads((case / "input_project.json").read_text(encoding="utf-8"))
    expected = json.loads(
        (case / "expected_summary.json").read_text(encoding="utf-8")
    )
    data_dir = case.parents[4] / "data" / "coefficients"
    live = _run_design_dims(payload, expected, data_dir)
    # 单点图：inlet → tiaojiechi → cass（golden 主线未含的两单元逐单元单点）
    design = payload["design"]
    assert isinstance(design, dict)
    nodes = design["nodes"]
    assert isinstance(nodes, dict)
    design["nodes"] = {
        "inlet": nodes["inlet"],
        "municipal_tiaojiechi": {},
        "municipal_cass": {},
    }
    design["edges"] = [
        {"src": {"unit_id": "inlet", "port_id": "out"},
         "dst": {"unit_id": "municipal_tiaojiechi", "port_id": "in"}},
        {"src": {"unit_id": "municipal_tiaojiechi", "port_id": "out"},
         "dst": {"unit_id": "municipal_cass", "port_id": "in"}},
    ]
    live.update(_run_design_dims(payload, expected, data_dir))
    # 矿井链单点图：mine_water_input 图源（无入边）→ … → ziwai——节点
    # 空 dict=默认参数（M3D1 实跑零校验失败零警告，无需参数注入）
    design["nodes"] = {unit: {} for unit in _MINE_CHAIN}
    design["edges"] = [
        {"src": {"unit_id": _MINE_CHAIN[i], "port_id": "out"},
         "dst": {"unit_id": _MINE_CHAIN[i + 1], "port_id": "in"}}
        for i in range(len(_MINE_CHAIN) - 1)
    ]
    live.update(_run_design_dims(payload, expected, data_dir))
    return live


def test_table_covers_exactly_expected_units() -> None:
    """表键集==21 单元（市政 13+矿井 8；cugeshan/xigeshan 同构不合并）。"""
    assert frozenset(PROJECTION_TABLE) == _EXPECTED_UNITS


def test_line_sets_disjoint() -> None:
    """聚合无静默覆盖：分线键集两两不相交 + 并集==PROJECTION_TABLE 键集。"""
    municipal = frozenset(MUNICIPAL_PROJECTIONS)
    mine = frozenset(MINE_PROJECTIONS)
    assert not municipal & mine, (
        f"分线键集重叠 {sorted(municipal & mine)}——聚合将静默覆盖"
        f"（后批扩线越线即红）"
    )
    assert municipal | mine == frozenset(PROJECTION_TABLE)


@pytest.mark.parametrize("unit_id", sorted(_EXPECTED_UNITS))
def test_projection_table_reconciles_with_live_dims(
    unit_id: str, live_dims: dict[str, frozenset[str]]
) -> None:
    """R1：五类并集∪non_drawn == compute 实跑 dims 键集（逐单元对账）。"""
    projection = PROJECTION_TABLE[unit_id]
    live = live_dims[unit_id]
    declared = projection.drawn_keys() | frozenset(projection.non_drawn)
    assert declared == live, (
        f"{unit_id} 表缺键 {sorted(live - declared)} / 表多键 "
        f"{sorted(declared - live)}（禁静默遗漏——逐键归入五类之一）"
    )


@pytest.mark.parametrize("unit_id", sorted(_EXPECTED_UNITS))
def test_dim_of_covers_all_keys_with_valid_dims(unit_id: str) -> None:
    """R3：dim_of 逐键覆盖全量且量纲 ∈ DimKey 枚举。"""
    projection = PROJECTION_TABLE[unit_id]
    declared = projection.drawn_keys() | frozenset(projection.non_drawn)
    assert frozenset(projection.dim_of) == declared
    members = set(DimKey)
    for key, dim in projection.dim_of.items():
        assert dim in members, f"{unit_id}.{key} 量纲 {dim!r} 不在 DimKey 枚举内"


@pytest.mark.parametrize("unit_id", sorted(_EXPECTED_UNITS))
def test_non_drawn_disjoint_from_drawn_keys(unit_id: str) -> None:
    """R1 附：校核量不上图——non_drawn 与四类取数键不相交。"""
    projection = PROJECTION_TABLE[unit_id]
    overlap = frozenset(projection.non_drawn) & projection.drawn_keys()
    assert not overlap, f"{unit_id} 校核量 {sorted(overlap)} 同时入取数类"
