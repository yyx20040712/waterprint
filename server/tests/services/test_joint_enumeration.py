"""joint_enumeration 服务镜像测试：静态预检 422+任务提交面（B4-3 TDD 序 4）。

输入:  waterprint_server.services.joint_enumeration 公开符号
输出:  预检护栏（rows 公式/N 上限）与异步 job 同 worker 制式断言
"""

from __future__ import annotations

import importlib

import pytest

_mod = importlib.import_module("waterprint_server.services.joint_enumeration")
submit_joint_enumeration = getattr(_mod, "submit_joint_enumeration", None)
JointEnumerationTooLargeError = getattr(_mod, "JointEnumerationTooLargeError", None)
InvalidJointUnitsError = getattr(_mod, "InvalidJointUnitsError", None)

pytestmark = pytest.mark.skipif(
    None in (submit_joint_enumeration, JointEnumerationTooLargeError,
             InvalidJointUnitsError),
    reason="实现未就绪：services.joint_enumeration（B4-3）",
)


def _payload() -> dict[str, object]:
    """两目标项目载荷（inlet→aao→cass——服务预检载体）。"""
    return {
        "format_version": "1.0",
        "design": {
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
                "municipal_aao": {},
                "municipal_cass": {},
            },
            "edges": [
                {"src": {"unit_id": "inlet", "port_id": "out"},
                 "dst": {"unit_id": "municipal_aao", "port_id": "in"}},
                {"src": {"unit_id": "municipal_aao", "port_id": "out"},
                 "dst": {"unit_id": "municipal_cass", "port_id": "in"}},
            ],
        },
        "view": {},
        "metadata": {
            "format_version": "1.0", "content_hash": "0",
            "engine_version": "0", "data_version": "0",
        },
    }


_GRIDS = {
    "municipal_aao": [{"field_id": "n", "values": [2.0, 3.0]}],
    "municipal_cass": [{"field_id": "n_pool", "values": [2.0, 3.0]}],
}


async def _project_id(ctx, tmp_path, overrides=None) -> str:  # type: ignore[no-untyped-def]
    """落盘项目并注册（read_project 消费面；assumption_overrides 入档）。"""
    import json

    payload = _payload()
    payload["design"]["assumption_overrides"] = dict(overrides or {})
    project_id = "joint-probe"
    path = ctx.projects_dir / f"{project_id}.wp.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return project_id


@pytest.mark.anyio
async def test_submit_returns_task_handle(service_ctx, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """正门 200 面：预检过→异步 job 同 worker 制式（kind=joint_enumerate）。"""
    project_id = await _project_id(service_ctx, tmp_path)
    handle = await submit_joint_enumeration(  # type: ignore[misc]
        service_ctx, project_id, ["municipal_cass", "municipal_aao"],
        {"grids": _GRIDS},
    )
    assert handle.task_id
    status = service_ctx.manager.status(handle.task_id)
    assert status.kind == "joint_enumerate"
    assert status.state in {"queued", "running", "done"}


@pytest.mark.anyio
async def test_precheck_over_budget_rejected(service_ctx, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """W7 静态预检：rows 估计超 max_total_rows → 422 面（事前拒非截断）。"""
    project_id = await _project_id(
        service_ctx, tmp_path, {"solution.joint.max_total_rows": 3.0}
    )
    with pytest.raises(JointEnumerationTooLargeError, match="静态预检"):  # type: ignore[misc]
        await submit_joint_enumeration(  # type: ignore[misc]
            service_ctx, project_id, ["municipal_aao", "municipal_cass"],
            {"grids": _GRIDS},
        )


@pytest.mark.anyio
async def test_precheck_over_max_units_rejected(service_ctx, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """N>max_units（项目覆盖收紧）→ 422 面（名义护栏——N3 口径）。"""
    project_id = await _project_id(
        service_ctx, tmp_path, {"solution.joint.max_units": 1.0}
    )
    with pytest.raises(JointEnumerationTooLargeError, match="max_units"):  # type: ignore[misc]
        await submit_joint_enumeration(  # type: ignore[misc]
            service_ctx, project_id, ["municipal_aao", "municipal_cass"], None,
        )


@pytest.mark.anyio
async def test_invalid_units_rejected(service_ctx, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """空/重复/未知 unit_ids → 422 面（请求形态校验）。"""
    project_id = await _project_id(service_ctx, tmp_path)
    with pytest.raises(InvalidJointUnitsError, match="至少"):  # type: ignore[misc]
        await submit_joint_enumeration(service_ctx, project_id, [], None)  # type: ignore[misc]
    with pytest.raises(InvalidJointUnitsError, match="重复"):  # type: ignore[misc]
        await submit_joint_enumeration(  # type: ignore[misc]
            service_ctx, project_id, ["municipal_aao", "municipal_aao"], None,
        )
    with pytest.raises(InvalidJointUnitsError, match="不在单元目录"):  # type: ignore[misc]
        await submit_joint_enumeration(service_ctx, project_id, ["nope"], None)  # type: ignore[misc]


@pytest.mark.anyio
async def test_precheck_uses_request_grid_sizes(service_ctx, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """预检网格规模=请求覆盖值域（values 计数——非 manifest 全档）。"""
    project_id = await _project_id(
        service_ctx, tmp_path, {"solution.joint.max_total_rows": 12.0}
    )
    # 2·(5²−1)/4=12≤12 过；计数含请求覆盖两单元各 2 档
    handle = await submit_joint_enumeration(  # type: ignore[misc]
        service_ctx, project_id, ["municipal_aao", "municipal_cass"],
        {"grids": _GRIDS},
    )
    assert handle.task_id
