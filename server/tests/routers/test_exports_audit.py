"""exports audit 端点镜像测试：exp-audit-20260930 收口批（501→200）。

输入:  waterprint_server.routers.exports /audit 端点（service 全链）
输出:  audit 导出行为契约断言（200 HTML/幂等命名/stale 409+force/
       422 两闸/混装批零继承+批量 worker 分流）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（exp-audit-20260930 audit 501 收口批·server 通道笔）
#
# 【覆盖面】
#   - 单产物正向：POST /api/exports/audit → 200 text/html+锚点内容
#     （标题/三元组版本串——非全字节断言）+产物落 exports_dir+.html
#     后缀+幂等命名（同输入同名，注册表单行）；
#   - stale 守门维持：design 漂移未 force → 409 StaleExportError；
#     force=1 → 200+stale_labeled 元数据标注（既有链零回归）；
#   - 选项闸（禁静默忽略任一意图）：audit+unit_id（批级/item 级/纯
#     audit 批批级）→ 422；audit+非空 condition_key（端点级/item 级）→
#     422；拒绝即零落盘（exports_dir 快照前后对比）；
#   - 混装批零继承+批量路径：dxf+audit 混装 items（批级 unit_id）→
#     dxf 项继承 unit 分量、audit 项全路由键置空（命名无 unit 段）；
#     任务终态 done 双产物（dxf 魔面+HTML 锚点——worker 分流实证）。
# 【替身口径】零替身——audit 渲染走真 flows.audit_render_flow（本批
#   被测接线面即分流正门；dxf 魔面断言沿 test_exports.py 先例）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import importlib
import os

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.routers.exports")
router = getattr(_mod, "router")

pytestmark = [
    pytest.mark.skipif(
        router is None,
        reason="实现未就绪：waterprint_server.routers.exports（服务层 M2/M3）",
    ),
    pytest.mark.anyio,
]


async def _project_with_result(client):  # type: ignore[no-untyped-def]
    """建项目并跑 calc 至 done（test_exports.py 同款前置——audit 消费前提）。"""
    nodes: dict[str, object] = {
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
        "municipal_cass": {},
    }
    edges = [
        {
            "src": {"unit_id": "inlet", "port_id": "out"},
            "dst": {"unit_id": "municipal_cass", "port_id": "in"},
        }
    ]
    payload = {
        "project": {
            "format_version": "1.0",
            "design": {"nodes": nodes, "edges": edges},
            "view": {},
            "metadata": {
                "format_version": "1.0",
                "content_hash": "0",
                "engine_version": "0",
                "data_version": "0",
            },
        }
    }
    created = await client.post("/api/projects", json=payload)
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": []}
    )).json()["task_id"]
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id, task_id  # type: ignore[no-any-return]


async def _wait_task_terminal(client, task_id: str) -> dict:  # type: ignore[no-untyped-def]
    """轮询任务至终态（test_exports.py 同款——批量 E2E 消费面）。"""
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "cancelled", "failed"}:
            return body  # type: ignore[no-any-return]
        await asyncio.sleep(0.1)
    pytest.fail(f"任务 {task_id} 300 轮询内未到终态（exp-audit 批量 E2E）")


def _disposition_name(response) -> str:  # type: ignore[no-untyped-def]
    """Content-Disposition 文件名解析（test_exports.py 同款——尾锁后缀边界）。"""
    disposition = str(response.headers.get("content-disposition", ""))
    return disposition.rsplit('filename="', maxsplit=1)[-1].rstrip('"')


@pytest.mark.anyio
async def test_audit_single_product_html_flow_wiring(  # type: ignore[no-untyped-def]
    client, test_settings
) -> None:
    """单产物正向：200 text/html+锚点（标题/三元组 engine 版本串）+.html
    后缀+落盘真件+幂等命名（同输入同名——注册表单行，禁时钟）。"""
    project_id, task_id = await _project_with_result(client)
    engine_version = (await client.get(f"/api/calc/tasks/{task_id}")).json()[
        "result"
    ]["engine_version"]
    fresh = await client.post("/api/exports/audit", json={"project_id": project_id})
    assert fresh.status_code == status.HTTP_200_OK
    assert fresh.headers["content-type"].startswith("text/html")  # DoD：HTML 流
    text = fresh.content.decode("utf-8")
    assert "公式溯源审计报告" in text  # 标题锚点（非全字节断言）
    assert str(engine_version) in text  # 三元组版本串在场（R4 头部自证）
    assert _disposition_name(fresh).endswith(".html")  # kind 后缀映射
    metas = await client.get("/api/exports", params={"project_id": project_id})
    rows = [meta for meta in metas.json() if meta["kind"] == "audit"]
    assert len(rows) == 1 and rows[0]["file_name"].endswith(".html")
    assert (test_settings.exports_dir / rows[0]["file_name"]).is_file()  # 落盘真件
    again = await client.post("/api/exports/audit", json={"project_id": project_id})
    assert again.status_code == status.HTTP_200_OK
    assert _disposition_name(again) == rows[0]["file_name"]  # 幂等命名（同输入同名）
    metas = await client.get("/api/exports", params={"project_id": project_id})
    rows = [meta for meta in metas.json() if meta["kind"] == "audit"]
    assert len(rows) == 1  # 幂等重导出覆盖（注册表不重复登记）


@pytest.mark.anyio
async def test_audit_stale_409_and_force_labeled_wiring(client) -> None:  # type: ignore[no-untyped-def]
    """stale 守门维持：design 漂移未 force → 409 StaleExportError 附摘要；
    force=1 → 200 text/html+元数据 stale_labeled=true（旧三元组显式标注）。"""
    project_id, task_id = await _project_with_result(client)
    result_digest = (await client.get(f"/api/calc/tasks/{task_id}")).json()[
        "result"
    ]["design_hash"]
    project = (await client.get(f"/api/projects/{project_id}")).json()
    project["design"]["assumption_overrides"] = {"safety.superheight": 0.3}
    saved = await client.put(f"/api/projects/{project_id}", json=project)
    assert saved.status_code == status.HTTP_200_OK and saved.json()["design_changed"]
    stale = await client.post("/api/exports/audit", json={"project_id": project_id})
    assert stale.status_code == status.HTTP_409_CONFLICT
    assert stale.json()["error_type"] == "StaleExportError"
    assert result_digest[:6] in str(stale.json()["detail"])  # 摘要值锁定
    forced = await client.post(
        "/api/exports/audit",
        json={"project_id": project_id},
        params={"force": "true"},
    )
    assert forced.status_code == status.HTTP_200_OK
    assert forced.headers["content-type"].startswith("text/html")  # force 照常真产物
    metas = await client.get("/api/exports", params={"project_id": project_id})
    rows = [meta for meta in metas.json() if meta["kind"] == "audit"]
    assert len(rows) == 1 and rows[0]["stale_labeled"] is True  # 旧三元组标注
    assert rows[0]["design_digest"] == result_digest


@pytest.mark.anyio
async def test_audit_unit_id_option_rejected_422_wiring(  # type: ignore[no-untyped-def]
    client, test_settings
) -> None:
    """选项闸①：audit+unit_id（批级/item 级/纯 audit 批批级）→ 422 且零落盘
    （禁静默忽略——audit 为全厂单份不分单元）。"""
    project_id, _task_id = await _project_with_result(client)
    exports_dir = test_settings.exports_dir
    before = sorted(os.listdir(exports_dir))
    batch_level = await client.post(
        "/api/exports/audit",
        json={"project_id": project_id, "options": {"unit_id": "municipal_cass"}},
    )
    assert batch_level.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert batch_level.json()["error_type"] == "InvalidExportRequestError"
    assert "unit_id" in str(batch_level.json()["detail"])  # 中文指路文案
    item_level = await client.post(
        "/api/exports/audit",
        json={
            "project_id": project_id,
            "options": {"items": [
                {"kind": "audit", "unit_id": "municipal_cass"},
            ]},
        },
    )
    assert item_level.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    mixed_item = await client.post(
        "/api/exports/audit",
        json={
            "project_id": project_id,
            "options": {"items": [
                {"kind": "calcbook", "condition_key": "design"},
                {"kind": "audit", "unit_id": "municipal_cass"},
            ]},
        },
    )
    assert mixed_item.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT  # 整批原子拒
    assert sorted(os.listdir(exports_dir)) == before  # 拒绝即零落盘


@pytest.mark.anyio
async def test_audit_condition_key_rejected_422_wiring(  # type: ignore[no-untyped-def]
    client, test_settings
) -> None:
    """选项闸②：audit+非空 condition_key（端点级/item 级/纯 audit 批端点级）→
    422 且零落盘（audit 为全厂单份跨工况文档——condition_key 请留空）。"""
    project_id, _task_id = await _project_with_result(client)
    exports_dir = test_settings.exports_dir
    before = sorted(os.listdir(exports_dir))
    endpoint_level = await client.post(
        "/api/exports/audit",
        json={"project_id": project_id, "condition_key": "design"},
    )
    assert endpoint_level.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert endpoint_level.json()["error_type"] == "InvalidExportRequestError"
    assert "condition_key" in str(endpoint_level.json()["detail"])
    item_level = await client.post(
        "/api/exports/audit",
        json={
            "project_id": project_id,
            "options": {"items": [{"kind": "audit", "condition_key": "design"}]},
        },
    )
    assert item_level.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    pure_batch_endpoint = await client.post(
        "/api/exports/audit",
        json={
            "project_id": project_id,
            "condition_key": "design",
            "options": {"items": [{"kind": "audit"}, {"kind": "audit"}]},
        },
    )
    assert pure_batch_endpoint.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert sorted(os.listdir(exports_dir)) == before  # 拒绝即零落盘


@pytest.mark.anyio
async def test_audit_mixed_batch_no_inherit_and_worker_branch_wiring(  # type: ignore[no-untyped-def]
    client, test_settings
) -> None:
    """混装批零继承+批量路径：dxf+audit items（批级 unit_id）→dxf 项继承
    unit 分量、audit 项全路由键置空（命名无 unit 段+.html）；任务终态
    done 双产物（dxf 魔面+HTML 标题锚点——worker 分流 flows 实证）。"""
    project_id, _task_id = await _project_with_result(client)
    batch = await client.post(
        "/api/exports/dxf",
        json={
            "project_id": project_id,
            "options": {
                "unit_id": "municipal_cass",  # 批级——dxf 项继承/audit 项置空
                "items": [
                    {"kind": "dxf", "condition_key": "design"},
                    {"kind": "audit"},
                ],
            },
        },
    )
    assert batch.status_code == status.HTTP_200_OK  # 批量转任务句柄 JSON
    done = await _wait_task_terminal(client, str(batch.json()["task_id"]))
    assert done["state"] == "done" and len(done["result"]["files"]) == 2
    html_names = [
        name for name in sorted(os.listdir(test_settings.exports_dir))
        if name.endswith(".html")
    ]
    dxf_names = [
        name for name in sorted(os.listdir(test_settings.exports_dir))
        if name.endswith(".dxf")
    ]
    assert len(html_names) == 1 and len(dxf_names) == 1  # 双产物各一
    assert "-dxf-municipal_cass-design-" in dxf_names[0]  # dxf 项继承批级 unit
    assert "-audit-all-" in html_names[0]  # audit 命名（condition 缺省段=all）
    assert "municipal_cass" not in html_names[0]  # audit 项零路由键继承（无 unit 段）
    assert "全厂总图".encode() not in (  # audit 非 dxf 总图通道（内容互不串道）
        test_settings.exports_dir / html_names[0]
    ).read_bytes()
    assert "公式溯源审计报告" in (  # HTML 标题锚点（真 flows 渲染）
        test_settings.exports_dir / html_names[0]
    ).read_text(encoding="utf-8")
    assert b"AC1032" in (test_settings.exports_dir / dxf_names[0]).read_bytes()[:512]
