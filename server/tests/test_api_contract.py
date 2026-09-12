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

# 九路由器端点集（v1 冻结——A1 锁定面：路径×方法 恰 29 条路径/32 操作；FE1 +scene1；
# META1 +units2；FE7 +elevation1；FE8 +cost1；CP1 +constraints1；
# L4b +site/spacing1；SC1 +exports/ifc1——BIM 模型导出，openapi 25→26
# 破面已授权；EXPD +exports/{file_name}1——产物下载端点，openapi 26→27
# 破面已授权 [Ruling 2026-09-05 ②]；P2 生命周期治理批 +copy/rename/
# delete3——openapi 28→31 破面[常设指令推荐序沿册 2026-09-12]）。
EXPECTED_ENDPOINTS: dict[str, set[str]] = {
    "/api/projects": {"post", "get"},
    "/api/projects/{project_id}": {"get", "put", "delete"},
    "/api/projects/{project_id}/validate": {"post"},
    "/api/projects/{project_id}/copy": {"post"},  # P2 生命周期（2026-09-12）
    "/api/projects/{project_id}/rename": {"post"},  # P2 生命周期（2026-09-12）
    "/api/calc/run": {"post"},
    "/api/calc/enumerate": {"post"},
    "/api/calc/tasks/{task_id}": {"get"},
    "/api/calc/tasks/{task_id}/cancel": {"post"},
    "/api/calc/tasks/{task_id}/solutions": {"get"},
    "/api/calc/solutions/apply": {"post"},
    "/api/calc/design-map": {"post"},  # FD PD6（2026-09-09）：可行域同步求值
    "/api/calc/trust/{project_id}": {"get"},  # P2 次批（2026-09-12）：可信度报告 ADR-012 D8
    "/api/exports": {"get"},
    "/api/exports/calcbook": {"post"},
    "/api/exports/audit": {"post"},
    "/api/exports/dxf": {"post"},
    "/api/exports/estimate": {"post"},
    "/api/exports/ifc": {"post"},  # SC1 D7——BIM 模型（ifc_export 正门）
    "/api/exports/{file_name}": {"get"},  # EXPD D3——产物下载（resolve 闸在 service）
    "/api/events/tasks/{task_id}": {"get"},
    "/api/events/projects/{project_id}": {"get"},
    "/api/scene/{project_id}": {"get"},
    "/api/elevation/{project_id}": {"get"},
    "/api/cost/{project_id}": {"get"},
    "/api/units": {"get"},
    "/api/assumptions": {"get"},
    "/api/constraints": {"get"},  # CP1 D5——kb 装载投影（META1 静态目录族）
    "/api/site/spacing": {"get"},  # L4b——间距校核（scene 同构取数端点族）
}


@pytest.mark.anyio
async def test_openapi_endpoint_set(client) -> None:  # type: ignore[no-untyped-def]
    """A1：端点集与九路由器规格一致（防止端点漂移无测试感知）。"""
    schema = _main.app.openapi()  # 模块级实例同款 schema（契约自检面）
    observed = {
        path: {m for m in methods if m in {"get", "post", "put", "delete"}}
        for path, methods in schema["paths"].items()
    }
    assert observed == EXPECTED_ENDPOINTS
    assert sum(len(methods) for methods in observed.values()) == 32  # 5+7+7+2+1+1+2+1+1+1（projects8[P2 +copy/rename/delete——2026-09-12 生命周期治理批]/calc8[P2 次批 +trust 2026-09-12——ADR-012 D8]/exports7/events2/scene1/elevation1/units2/cost1/constraints1/site1——EXPD +exports/{file_name} GET）


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


# PL-03 契约枚举（GOV5 治理余账批 2026-09-12）：声明面锚——端点实际
# 404/409（_EXCEPTION_STATUS 映射）须在 openapi responses 有对应声明
# （行为与文档一致）。首批点名面=lifecycle 三端点（n+41 挂账）+trust
# （n+42 增量——404 行为已测 test_trust.py）；其余端点统一枚举挂账。
_PL03_DECLARED: dict[str, dict[str, set[str]]] = {
    "/api/calc/trust/{project_id}": {
        "get": {"200", "404", "422"},
    },
    "/api/projects/{project_id}/copy": {"post": {"200", "404", "409", "422"}},
    "/api/projects/{project_id}/rename": {"post": {"200", "404", "409", "422"}},
    "/api/projects/{project_id}": {"delete": {"200", "404", "409", "422"}},
}


@pytest.mark.anyio
async def test_pl03_error_responses_declared(client) -> None:  # type: ignore[no-untyped-def]
    """PL-03：点名端点的 404/409 错误响应已声明+统一错误体模型引用。"""
    schema = _main.app.openapi()
    for path, per_method in _PL03_DECLARED.items():
        for method, expected_keys in per_method.items():
            op = schema["paths"][path][method]
            assert set(op["responses"]) == expected_keys, (
                f"{method.upper()} {path} responses={sorted(op['responses'])}"
                f" != {sorted(expected_keys)}（PL-03 声明面漂移）"
            )
            for code in expected_keys - {"200", "422"}:  # 404/409=统一错误体
                schema_ref = op["responses"][code]["content"]["application/json"]["schema"]
                assert schema_ref == {"$ref": "#/components/schemas/ErrorResponse"}, (
                    f"{method.upper()} {path} {code} 非 ErrorResponse 统一体"
                )
    # 统一错误体组件在场（detail/error_type 双字段——R2 冻结形态）
    error_model = schema["components"]["schemas"]["ErrorResponse"]["properties"]
    assert set(error_model) == {"detail", "error_type"}


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
    """R1-3（AU-3）：有结果集时 audit/estimate=恰 501（未就绪族确定性）。

    dxf 移出=M5 全厂总图接线后 bare POST 即 200（R0.5 总控裁定 2026-09-04
    ——SC1 端点集断言 26 同类行为变更连带同步先例；dxf 正向/总图面归
    tests/routers/test_exports.py M5 用例族）。
    """
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
    for kind in ("audit", "estimate"):
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
