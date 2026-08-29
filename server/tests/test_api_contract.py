"""API 契约测试：路由存在性/方法/响应骨架（OpenAPI 单一事实源的测试侧守卫）。

输入:  create_app 产出的 OpenAPI schema（实现后）
输出:  契约结构断言（端点集与 §13.4 四路由器规格一致）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；休眠测试——app 实现后激活）
#
# 覆盖用例（实现后必须全部转绿，skip 数归零）：
#   A1 OpenAPI 生成成功且端点集 == 七路由器规格的并集
#      （projects 5 + calc 6 + exports 5 + events 2 + scene 1——FE1
#       + units 2——META1 + elevation 1——FE7）；
#   A2 每端点有请求/响应 schema（无 Any 泄漏）；
#   A3 错误响应模型统一（领域异常映射表齐全）；
#   A4 /api/projects/{id} 越界 id（../、绝对路径）→ 4xx 非 500。
#
# 休眠机制：与 core 测试同款 getattr 守卫（waterprint_server.main
#   的 create_app 缺失即 skip 并注明原因）。
# ══════════════════════════════════════════════════════════════════

import asyncio
import importlib

import pytest
from fastapi import status

_main = importlib.import_module("waterprint_server.main")
_CREATE_APP = getattr(_main, "create_app", None)

pytestmark = pytest.mark.skipif(
    _CREATE_APP is None,
    reason="实现未就绪：waterprint_server.main.create_app（服务层 M2 起实现）",
)

# 八路由器端点集（v1 冻结——A1 锁定面：路径×方法 恰 23 条；FE1 +scene1；
# META1 +units2；FE7 +elevation1；FE8 +cost1）。
EXPECTED_ENDPOINTS: dict[str, set[str]] = {
    "/api/projects": {"post", "get"},
    "/api/projects/{project_id}": {"get", "put"},
    "/api/projects/{project_id}/validate": {"post"},
    "/api/calc/run": {"post"},
    "/api/calc/enumerate": {"post"},
    "/api/calc/tasks/{task_id}": {"get"},
    "/api/calc/tasks/{task_id}/cancel": {"post"},
    "/api/calc/tasks/{task_id}/solutions": {"get"},
    "/api/calc/solutions/apply": {"post"},
    "/api/exports": {"get"},
    "/api/exports/calcbook": {"post"},
    "/api/exports/audit": {"post"},
    "/api/exports/dxf": {"post"},
    "/api/exports/estimate": {"post"},
    "/api/events/tasks/{task_id}": {"get"},
    "/api/events/projects/{project_id}": {"get"},
    "/api/scene/{project_id}": {"get"},
    "/api/elevation/{project_id}": {"get"},
    "/api/cost/{project_id}": {"get"},
    "/api/units": {"get"},
    "/api/assumptions": {"get"},
}


@pytest.mark.anyio
async def test_openapi_endpoint_set(client) -> None:  # type: ignore[no-untyped-def]
    """A1：端点集与八路由器规格一致（防止端点漂移无测试感知）。"""
    schema = _main.app.openapi()  # 模块级实例同款 schema（契约自检面）
    observed = {
        path: {m for m in methods if m in {"get", "post", "put", "delete"}}
        for path, methods in schema["paths"].items()
    }
    assert observed == EXPECTED_ENDPOINTS
    assert sum(len(methods) for methods in observed.values()) == 23  # 5+6+5+2+1+1+2+1


@pytest.mark.anyio
async def test_openapi_schema_no_any_leak(client) -> None:  # type: ignore[no-untyped-def]
    """A2：请求/响应 schema 完整，无 Any 类型字段。"""
    schema = _main.app.openapi()
    components = schema.get("components", {}).get("schemas", {})
    assert components, "组件面为空（响应/请求模型未注册）"
    framework_errors = {"ValidationError", "HTTPValidationError", "RequestValidationError"}
    for name, model in components.items():
        if name in framework_errors:
            continue  # 框架自建错误模型（input: Any 是 pydantic 语义，非本面泄漏）
        assert model != {}, f"组件 {name} 为空 schema（Any 泄漏面）"
        for field, spec in model.get("properties", {}).items():
            assert spec != {}, f"{name}.{field} 无类型面（Any 泄漏）"
            assert "type" in spec or "$ref" in spec or "items" in spec or "anyOf" in spec, (
                f"{name}.{field} 缺类型声明"
            )


@pytest.mark.anyio
async def test_error_model_complete(client) -> None:  # type: ignore[no-untyped-def]
    """A3：领域异常 → HTTP 映射表完整（真实端点触发面：404/422）。"""
    missing = {"project_id": "nosuchproject0000", "conditions": []}
    r = await client.post("/api/calc/run", json=missing)
    assert r.status_code == status.HTTP_404_NOT_FOUND  # NotFound 族→404
    assert "error_type" in r.json()  # 统一错误体 {detail, error_type}
    created = await client.post("/api/projects", json={})
    assert created.status_code == status.HTTP_200_OK
    project_id = created.json()["project_id"]
    r = await client.post(
        "/api/calc/enumerate", json={"project_id": project_id, "unit_ids": ["a", "b"]}
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT  # ADR-005 多单元
    r = await client.post(
        "/api/calc/enumerate", json={"project_id": project_id, "unit_ids": []}
    )
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT  # pydantic 参数面
    r = await client.post("/api/exports/audit", json={"project_id": project_id})
    assert r.status_code == status.HTTP_404_NOT_FOUND  # R1-3：无结果集=恰 404（先重算）


@pytest.mark.anyio
async def test_not_ready_kinds_return_501_wiring(client, cass_payload) -> None:  # type: ignore[no-untyped-def]
    """R1-3（AU-3）：有结果集时 audit/dxf/estimate=恰 501（未就绪族确定性）。"""
    created = await client.post("/api/projects", json={"project": cass_payload})
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": []}
    )).json()["task_id"]
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"  # 结果集就绪（501 前提）
    for kind in ("audit", "dxf", "estimate"):
        response = await client.post(f"/api/exports/{kind}", json={"project_id": project_id})
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED, (
            f"{kind} 期望恰 501（ArtifactKindNotReady/模板缺位透传），"
            f"得到 {response.status_code}"
        )
        assert "error_type" in response.json()


@pytest.mark.anyio
async def test_project_id_path_traversal_rejected(client) -> None:  # type: ignore[no-untyped-def]
    """A4：路径穿越 id 拒绝（安全门——4xx 非 500）。"""
    for evil in ("%2e%2e%2fevil", "..%2Fevil", "%2Fabs"):
        response = await client.get(f"/api/projects/{evil}")
        assert 400 <= response.status_code < 500, f"{evil} 期望 4xx，得到 {response.status_code}"
