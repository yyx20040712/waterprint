"""drawing_projection 对账测试：UF-32 对照表 13 单元 dims 键全覆盖（Ruling ①）。

输入:  waterprint.contracts.drawing_projection.PROJECTION_TABLE + golden 项目
       （municipal_34760，11 单元）+ 逐单元单点图（tiaojiechi→cass 补齐 13）
输出:  表覆盖对账断言（五类并集∪non_drawn==compute 实跑键集——13 单元全）
"""

# ══════════════════════════════════════════════════════════════════
# 规格：DRAFT 批 D1（Ruling ① UF-32 方案②）。表是冻结声明面，测试以
# golden 实跑为证逐单元对账——表漏键/多键即红（禁静默遗漏的机器强制）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from pathlib import Path

import pytest

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.quantity import DimKey

pytestmark = [pytest.mark.golden]

_THIRTEEN_UNITS: frozenset[str] = frozenset({
    "municipal_aao", "municipal_bashi_jiliangcao", "municipal_cass",
    "municipal_chenshachi", "municipal_chuchenchi", "municipal_cugeshan",
    "municipal_erchunchi", "municipal_gaomidu", "municipal_tiaojiechi",
    "municipal_vxinglvchi", "municipal_wushui_tisheng",
    "municipal_xigeshan", "municipal_ziwai",
})


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
    """13 单元实跑键集（模块级一次）：golden 11 + 单点图补 tiaojiechi/cass。"""
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
    return live


def test_table_covers_exactly_thirteen_municipal_units() -> None:
    """表键集==13 市政单元（cugeshan/xigeshan 同构不合并）。"""
    assert frozenset(PROJECTION_TABLE) == _THIRTEEN_UNITS


@pytest.mark.parametrize("unit_id", sorted(_THIRTEEN_UNITS))
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


@pytest.mark.parametrize("unit_id", sorted(_THIRTEEN_UNITS))
def test_dim_of_covers_all_keys_with_valid_dims(unit_id: str) -> None:
    """R3：dim_of 逐键覆盖全量且量纲 ∈ DimKey 枚举。"""
    projection = PROJECTION_TABLE[unit_id]
    declared = projection.drawn_keys() | frozenset(projection.non_drawn)
    assert frozenset(projection.dim_of) == declared
    members = set(DimKey)
    for key, dim in projection.dim_of.items():
        assert dim in members, f"{unit_id}.{key} 量纲 {dim!r} 不在 DimKey 枚举内"


@pytest.mark.parametrize("unit_id", sorted(_THIRTEEN_UNITS))
def test_non_drawn_disjoint_from_drawn_keys(unit_id: str) -> None:
    """R1 附：校核量不上图——non_drawn 与四类取数键不相交。"""
    projection = PROJECTION_TABLE[unit_id]
    overlap = frozenset(projection.non_drawn) & projection.drawn_keys()
    assert not overlap, f"{unit_id} 校核量 {sorted(overlap)} 同时入取数类"
