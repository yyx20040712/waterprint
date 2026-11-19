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


# ══ E2E-1 扩 R2-P2-1：项目读面禁缓存（[HUMAN-LOCK] 2026-09-26 落地）══


@pytest.mark.anyio
async def test_read_project_response_no_store(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """E2E-1 扩（R2-P2-1）：项目读面禁缓存——apply/保存后同 URL 缓存旧读
    假阴性（round2 d20 实录）。"""
    created = await client.post(
        "/api/projects", json={"project": cass_payload}
    )
    project_id = created.json()["project_id"]
    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"


# ══ F2 并发丢更新批（2026-11-20）：PUT 条件保存（?base_hash 三态+并发序）══


@pytest.mark.anyio
async def test_conditional_put_three_states_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """条件 PUT 三态：基线符 200 / 基线不符 409 带现行标识 / 无基线直写 200。"""
    created = await client.post("/api/projects", json={"name": "并发治理"})
    assert created.status_code == 200, created.text
    project_id = created.json()["project_id"]
    base_hash = created.json()["content_hash"]
    body = (await client.get(f"/api/projects/{project_id}")).json()
    body["design"]["nodes"]["inlet"] = {"kind": "municipal_input"}

    # 态①基线符 → 200
    ok = await client.put(
        f"/api/projects/{project_id}", json=body, params={"base_hash": base_hash}
    )
    assert ok.status_code == 200, ok.text
    current_hash = ok.json()["content_hash"]
    assert current_hash != base_hash  # 版本标识随写更新

    # 态②基线不符（旧基线）→ 409 统一错误体带现行摘要
    body["design"]["nodes"]["inlet"]["q_avg_daily"] = 0.4
    conflict = await client.put(
        f"/api/projects/{project_id}", json=body, params={"base_hash": base_hash}
    )
    assert conflict.status_code == 409, conflict.text
    error = conflict.json()
    assert error["error_type"] == "ProjectConcurrentWriteError"
    assert current_hash[:10] in error["detail"]  # 错误体携带当前版本标识
    assert "q_avg_daily" not in (
        (await client.get(f"/api/projects/{project_id}")).json()["design"]["nodes"].get(
            "inlet", {}
        )
    )  # 零写入

    # 态③无基线（兼容期）→ 200 直写
    direct = await client.put(f"/api/projects/{project_id}", json=body)
    assert direct.status_code == 200, direct.text
    latest = (await client.get(f"/api/projects/{project_id}")).json()
    assert latest["design"]["nodes"]["inlet"].get("q_avg_daily") == 0.4


@pytest.mark.anyio
async def test_conditional_put_concurrent_ab_sequence_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """并发序（审计 F2 HTTP 面）：A/B 双端同基线→A 保存 200→B 保存必 409。"""
    created = await client.post("/api/projects", json={"name": "双上下文"})
    project_id = created.json()["project_id"]
    base_hash = created.json()["content_hash"]
    shared = (await client.get(f"/api/projects/{project_id}")).json()

    body_a = {**shared, "design": {**shared["design"], "nodes": {
        **shared["design"]["nodes"], "municipal_cugeshan": {}}}}
    body_b = {**shared, "design": {**shared["design"], "nodes": {
        **shared["design"]["nodes"], "municipal_aao": {}}}}

    resp_a = await client.put(
        f"/api/projects/{project_id}", json=body_a, params={"base_hash": base_hash}
    )
    assert resp_a.status_code == 200, resp_a.text
    resp_b = await client.put(  # B 无提示覆盖的静默通道就此关闭
        f"/api/projects/{project_id}", json=body_b, params={"base_hash": base_hash}
    )
    assert resp_b.status_code == 409
    assert resp_b.json()["error_type"] == "ProjectConcurrentWriteError"
    final_nodes = set(
        (await client.get(f"/api/projects/{project_id}")).json()["design"]["nodes"]
    )
    assert final_nodes == {"municipal_cugeshan"}  # A 存续、B 未落（显式选择前不覆盖）
