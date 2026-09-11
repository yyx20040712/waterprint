"""projects 路由镜像测试：CRUD 端点（薄层、路径安全、写锁）。

输入:  waterprint_server.routers.projects 公开符号
输出:  路由契约断言
"""

from __future__ import annotations

import importlib

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.projects")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.projects（服务层 M2）",
    ),
]

_EXPECTED = {
    ("post", "/api/projects"),
    ("get", "/api/projects"),
    ("get", "/api/projects/{project_id}"),
    ("put", "/api/projects/{project_id}"),
    ("post", "/api/projects/{project_id}/validate"),
    ("post", "/api/projects/{project_id}/copy"),
    ("post", "/api/projects/{project_id}/rename"),
    ("delete", "/api/projects/{project_id}"),
}


def test_router_exposes_eight_endpoints_wiring() -> None:
    """端点集 == 规格八件（CRUD 五件+P2 生命周期三件 copy/rename/delete）。"""
    observed = {
        (method.lower(), route.path) for route in router.routes for method in route.methods
    }  # type: ignore[union-attr]
    assert observed >= _EXPECTED and len(observed) == len(_EXPECTED)  # 恰八件无漂移


@pytest.mark.anyio
async def test_project_id_traversal_rejected_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """R1 接线断言：{id} 含 ../ 或绝对路径 → 4xx 非 500（§18）。"""
    for evil in ("/api/projects/..%2Fevil", "/api/projects/%2e%2e%2fevil"):
        response = await client.get(evil)
        assert 400 <= response.status_code < 500, f"{evil} → {response.status_code}"
        response = await client.put(evil, json={})
        assert 400 <= response.status_code < 500, f"PUT {evil} → {response.status_code}"


@pytest.mark.anyio
async def test_validate_endpoint_accepts_draft_body_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """P0-3 呈裁④甲：POST validate 可选 body=待存草稿（报告面 200 非 422）。"""
    created = await client.post("/api/projects", json={"name": "草稿校验"})
    assert created.status_code == 200, created.text
    project_id = created.json()["project_id"]
    draft = (await client.get(f"/api/projects/{project_id}")).json()
    draft["design"]["nodes"] = {"inlet": {"kind": "municipal_input",
                                          "q_avg_daily": 0.4, "kz": 1.4}}
    draft["design"]["edges"] = [
        {"src": {"unit_id": "inlet", "port_id": "out"},
         "dst": {"unit_id": "ghost", "port_id": "in"}}
    ]
    with_body = await client.post(f"/api/projects/{project_id}/validate", json=draft)
    assert with_body.status_code == 200, with_body.text
    body = with_body.json()
    assert body["valid"] is False
    assert any("悬空" in item for item in body["errors"])
    # 无 body 面=已存项目（空 design 结构合法）
    without_body = await client.post(f"/api/projects/{project_id}/validate")
    assert without_body.status_code == 200
    assert without_body.json()["valid"] is True


@pytest.mark.anyio
async def test_lifecycle_copy_rename_delete_roundtrip_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """P2 生命周期三端点：copy（副本名）→rename（轻通道）→delete（回显）。"""
    created = await client.post("/api/projects", json={"name": "治理面"})
    assert created.status_code == 200, created.text
    project_id = created.json()["project_id"]

    copied = await client.post(f"/api/projects/{project_id}/copy")
    assert copied.status_code == 200, copied.text
    copy_id = copied.json()["project_id"]
    assert copy_id != project_id
    listing = (await client.get("/api/projects")).json()
    names = {item["project_id"]: item["name"] for item in listing}
    assert names[copy_id] == "治理面 (副本)"

    renamed = await client.post(
        f"/api/projects/{project_id}/rename", json={"name": "治理面·改名"}
    )
    assert renamed.status_code == 200, renamed.text
    body = renamed.json()
    assert body["design_changed"] is False  # view 轻通道
    listing = (await client.get("/api/projects")).json()
    names = {item["project_id"]: item["name"] for item in listing}
    assert names[project_id] == "治理面·改名"

    deleted = await client.delete(f"/api/projects/{copy_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["project_id"] == copy_id
    gone = await client.get(f"/api/projects/{copy_id}")
    assert gone.status_code == 404


@pytest.mark.anyio
async def test_lifecycle_delete_missing_returns_404_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """P2 生命周期守卫①：删除不存在→404（统一错误体 error_type）。"""
    response = await client.delete("/api/projects/absent-project")
    assert response.status_code == 404
    assert response.json()["error_type"] == "ProjectNotFoundError"
