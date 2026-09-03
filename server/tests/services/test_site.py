"""site 服务镜像测试：间距校核装配（kb 阈值解析/足迹投影/降级语义）。

输入:  waterprint_server.services.site 公开符号+service_ctx 装配
输出:  服务契约断言（L4b 间距校核的服务面——core spacing_report 装配器）
"""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.services.site")
build_spacing_for_project = getattr(_mod, "build_spacing_for_project")

calculation_mod = importlib.import_module("waterprint_server.services.calculation")
projects_mod = importlib.import_module("waterprint_server.services.projects")

pytestmark = pytest.mark.anyio

# kb 1.3.0 已追认阈值（Ruling 2026-09-03——通用全对 WARN/限定对 ERROR）
_GENERAL_CLEARANCE_M = 6.0
_SCOPED_CLEARANCE_M = 10.0


def _design(site: dict[str, object] | None) -> dict[str, object]:
    """chenshachi+cass 链式双单元 design（足迹双可算——5 万 m³/d 级真算）。"""
    design: dict[str, object] = {
        "nodes": {
            "inlet": {
                "kind": "municipal_input",
                "q_avg_daily": 34760.7 / 86400,
                "kz": 1.4,
                "CODCR": 400.0,
                "BOD5": 200.0,
                "SS": 250.0,
                "NH3N": 26.0,
                "TN": 43.0,
                "TP": 6.5,
            },
            "municipal_chenshachi": {},
            "municipal_cass": {},
        },
        "edges": [
            {
                "src": {"unit_id": "inlet", "port_id": "out"},
                "dst": {"unit_id": "municipal_chenshachi", "port_id": "in"},
            },
            {
                "src": {"unit_id": "municipal_chenshachi", "port_id": "out"},
                "dst": {"unit_id": "municipal_cass", "port_id": "in"},
            },
        ],
    }
    if site is not None:
        design["site"] = site
    return design


def _project_payload(site: dict[str, object] | None) -> dict[str, object]:
    return {
        "project": {
            "format_version": "1.0",
            "design": _design(site),
            "view": {},
            "metadata": {
                "format_version": "1.0",
                "content_hash": "0",
                "engine_version": "0",
                "data_version": "0",
            },
        }
    }


_NEAR_SITE: dict[str, object] = {
    "structures": {
        "municipal_chenshachi": {"x": 0.0, "y": 0.0, "rotation": 0.0},
        "municipal_cass": {"x": 10.0, "y": 0.0, "rotation": 0.0},
    }
}


async def _project_with_result(ctx, site: dict[str, object]) -> str:  # type: ignore[no-untyped-def]
    """建含 site 摆放的项目并跑 calc 至 done（足迹消费前提）。"""
    outcome = projects_mod.create_project(ctx, _project_payload(site))
    project_id = outcome.project_id
    handle = await calculation_mod.submit_calculation(ctx, project_id, [])
    for _ in range(200):
        if ctx.manager.status(handle.task_id).state in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert ctx.manager.status(handle.task_id).state == "done"
    return project_id


async def test_spacing_assembles_violation_from_kb_threshold(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """装配正路：近摆→violations（kb 通用 WARN 阈值+重叠 0 净距）+uncalculated 空。"""
    project_id = await _project_with_result(service_ctx, _NEAR_SITE)
    report = build_spacing_for_project(service_ctx, project_id)
    assert report.uncalculated == ()
    assert len(report.violations) == 1
    row = report.violations[0]
    assert (row.a, row.b) == ("municipal_cass", "municipal_chenshachi")
    assert row.clearance_m == 0.0
    assert row.threshold_m == _GENERAL_CLEARANCE_M
    assert row.severity == "WARN"


async def test_spacing_scoped_threshold_needs_both_kind_members(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """限定对解析：ERROR 阈值成员=kb 两 kind 的本项目单元——无该类单元=不判。"""
    project_id = await _project_with_result(service_ctx, _NEAR_SITE)
    report = build_spacing_for_project(service_ctx, project_id)
    # chenshachi/cass 不在 nongsuo/xiaohua 限定对——恰一条通用 WARN，无 ERROR 行
    assert [row.severity for row in report.violations] == ["WARN"]
    thresholds = _mod._thresholds_from_kb(service_ctx, project_id)  # noqa: SLF001  # 装配面私有直测
    scoped = [t for t in thresholds if t.min_clearance_m == _SCOPED_CLEARANCE_M]
    assert len(scoped) == 1 and scoped[0].unit_kinds == frozenset()
    universal = [t for t in thresholds if t.min_clearance_m == _GENERAL_CLEARANCE_M]
    assert universal[0].unit_kinds is None and universal[0].severity == "WARN"


async def test_spacing_without_result_degrades_full_uncalculated(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """降级语义：无完成计算=violations 空+uncalculated 全量 sorted（不 404/409）。"""
    outcome = projects_mod.create_project(service_ctx, _project_payload(_NEAR_SITE))
    report = build_spacing_for_project(service_ctx, outcome.project_id)
    assert report.violations == ()
    assert list(report.uncalculated) == ["municipal_cass", "municipal_chenshachi"]


async def test_spacing_result_file_unreadable_degrades(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """结果文件缺失=同降级（校核是可降级辅助——scene 404 语义差异记档面）。"""
    import os

    project_id = await _project_with_result(service_ctx, _NEAR_SITE)
    status_row = service_ctx.manager.status(
        service_ctx.manager.task_ids_for_project(project_id)[-1]
    )
    os.remove(str(status_row.result["result_file"]))  # type: ignore[index]
    report = build_spacing_for_project(service_ctx, project_id)
    assert report.violations == ()
    assert list(report.uncalculated) == ["municipal_cass", "municipal_chenshachi"]


async def test_spacing_invalid_condition_raises_422_face(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """工况非法=InvalidSpacingRequestError（422 面消息含合法工况集）。"""
    project_id = await _project_with_result(service_ctx, _NEAR_SITE)
    with pytest.raises(_mod.InvalidSpacingRequestError, match="合法"):
        build_spacing_for_project(service_ctx, project_id, "no_such_condition")


async def test_spacing_unknown_project_raises_not_found(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """项目不存在=ProjectNotFoundError（read_project 先于取数——既有 404 面）。"""
    with pytest.raises(projects_mod.ProjectNotFoundError):
        build_spacing_for_project(service_ctx, "nosuchproject0000")


async def test_spacing_deterministic_double_run(service_ctx) -> None:  # type: ignore[no-untyped-def]
    """确定性：同项目双跑 JSON(sort_keys) 字节同。"""
    project_id = await _project_with_result(service_ctx, _NEAR_SITE)
    first = build_spacing_for_project(service_ctx, project_id)
    second = build_spacing_for_project(service_ctx, project_id)
    dump1 = json.dumps(first.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    dump2 = json.dumps(second.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    assert dump1 == dump2


async def test_spacing_bad_kb_expression_fails_visible(
    service_ctx, tmp_path: Path
) -> None:  # type: ignore[no-untyped-def]
    """fail-visible：spacing_check 表达式非 min_clearance_m >= <float> 形=显式拒。"""
    import shutil

    from waterprint_server.services import ServiceContext
    from waterprint_server.settings import Settings

    data_dir = tmp_path / "crafted-data"  # tmp_path 已被 test_settings 占用 data/
    shutil.copytree(service_ctx.settings.data_dir, data_dir)
    kb_path = data_dir / "constraint_kb" / "constraints.json"
    doc = json.loads(kb_path.read_text(encoding="utf-8"))
    for entry in doc["entries"]:
        if entry["kind"] == "spacing_check":
            entry["expression"] = "clearance > 6"  # 契约外形态
    kb_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    crafted = Settings(
        projects_dir=service_ctx.settings.projects_dir,
        exports_dir=service_ctx.settings.exports_dir,
        data_dir=data_dir,
        calc_workers=1,
        log_file=str(tmp_path / "crafted-server.log"),
    )
    crafted_ctx = ServiceContext(
        settings=crafted, manager=service_ctx.manager, domain_error_codes={}
    )
    project_id = await _project_with_result(service_ctx, _NEAR_SITE)
    with pytest.raises(RuntimeError, match="min_clearance_m"):
        build_spacing_for_project(crafted_ctx, project_id)
