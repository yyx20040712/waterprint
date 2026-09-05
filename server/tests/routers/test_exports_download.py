"""exports 下载端点镜像测试（EXPD 甲案：GET /api/exports/{file_name}）。

输入:  waterprint_server.routers.exports 下载面 + client 真装配
输出:  下载正向全链 + 穿越 DoD 六例契约断言（SERVER AU-1 条款 4）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（EXPD 甲案下载端点批 2026-09-05·简报 §2.5 D6）
#
# 【覆盖面】
#   - 正向：真导出 dxf（_project_with_result 先例）→列表取 file_name→
#     GET 下载 200+响应字节与落盘逐字节一致+Content-Disposition 含
#     原文件名；
#   - 穿越 DoD 六例（条款 4——客户端可控路径参数）：例1/2 浅 ../x 与
#     深 ../../.. 族（同族合一函数）；例3 URL 编码 ..%2f..；例4 绝对
#     路径（win 盘符 C:\\evil+posix /etc/passwd）；例5 合法形态名不在册；
#     例6 产物在而边车缺（先真导出再删 .meta.json）——每例请求前后
#     os.listdir(exports_dir) 快照恒等断言（test_exports.py:273 先例）；
#   - 两态断言（简报 D6）：例1-4 ∈{404,422} 且响应体非文件流
#     （application/json 统一错误体）；例5/6 恰 404 且 error_type
#     实值断言（条款 4——名义等值断言不合格）。
# 【落位注记】EXPD 拆件（宪法 §2 行预算 ≤500——routers/test_exports.py
#   489 行满载；services/test_exports_dwg.py 按面拆件先例），
#   _project_with_result 内嵌同款（跨测试件 import 无门禁面）。
# 【参照】EXPD 简报 §2.1/§2.5；AGENTS §18 路径安全
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
]


async def _project_with_result(client, extra_units=()):  # type: ignore[no-untyped-def]
    """建项目并跑 calc 至 done（test_exports.py 同款——下载正向前置）。"""
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
    for unit_id in extra_units:
        nodes[unit_id] = {}
    chain = ["inlet", *extra_units, "municipal_cass"]
    edges = [
        {
            "src": {"unit_id": chain[i], "port_id": "out"},
            "dst": {"unit_id": chain[i + 1], "port_id": "in"},
        }
        for i in range(len(chain) - 1)
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
    return project_id  # type: ignore[no-any-return]


async def _export_one_dxf(client, project_id: str) -> str:  # type: ignore[no-untyped-def]
    """真导出一张全厂总图 dxf→列表取 file_name（正向/例6 共用前置）。"""
    exported = await client.post(
        "/api/exports/dxf",
        json={"project_id": project_id, "condition_key": "design"},
    )
    assert exported.status_code == status.HTTP_200_OK
    metas = await client.get("/api/exports", params={"project_id": project_id})
    return str(next(meta["file_name"] for meta in metas.json() if meta["kind"] == "dxf"))


@pytest.mark.anyio
async def test_download_positive_flow_wiring(client, test_settings) -> None:  # type: ignore[no-untyped-def]
    """EXPD 正向：GET 下载 200+响应字节与落盘逐字节一致+Content-Disposition 原文件名。"""
    project_id = await _project_with_result(client)
    file_name = await _export_one_dxf(client, project_id)
    downloaded = await client.get(f"/api/exports/{file_name}")
    assert downloaded.status_code == status.HTTP_200_OK
    assert downloaded.content == (test_settings.exports_dir / file_name).read_bytes()  # 逐字节一致
    disposition = str(downloaded.headers.get("content-disposition", ""))
    assert file_name in disposition  # 原文件名（FileResponse filename 面）


@pytest.mark.anyio
async def test_download_traversal_dot_segments_rejected_wiring(
    client, test_settings
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 穿越 DoD 例1/2：浅 ../x 与深 ../../.. 族——4xx 两态+目录快照恒等。"""
    _project_id = await _project_with_result(client)
    exports_dir = test_settings.exports_dir
    before_listing = sorted(os.listdir(exports_dir))
    for evil in ("../x", "../" * 3 + "deep"):
        response = await client.get(f"/api/exports/{evil}")
        assert response.status_code in {404, 422}, (
            f"{evil!r} 期望 4xx（路径参含 /→路由 404；框架解码入闸→422），"
            f"得到 {response.status_code}"
        )
        assert response.headers.get("content-type", "").startswith("application/json")  # 非文件流
        assert "detail" in response.json()  # 统一错误体（非产物字节）
        assert sorted(os.listdir(exports_dir)) == before_listing  # 目录零新增


@pytest.mark.anyio
async def test_download_traversal_encoded_separator_rejected_wiring(
    client, test_settings
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 穿越 DoD 例3：URL 编码分隔符 ..%2f..——4xx 两态+目录快照恒等。"""
    _project_id = await _project_with_result(client)
    exports_dir = test_settings.exports_dir
    before_listing = sorted(os.listdir(exports_dir))
    response = await client.get("/api/exports/..%2f..")
    assert response.status_code in {404, 422}, (
        f"..%2f.. 期望 4xx（% 字符集外 422/含 / 路由 404 两态均受），"
        f"得到 {response.status_code}"
    )
    assert response.headers.get("content-type", "").startswith("application/json")  # 非文件流
    assert "detail" in response.json()
    assert sorted(os.listdir(exports_dir)) == before_listing  # 目录零新增


@pytest.mark.anyio
async def test_download_traversal_absolute_paths_rejected_wiring(
    client, test_settings
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 穿越 DoD 例4：绝对路径（win 盘符 C:\\evil+posix /etc/passwd）——4xx+快照恒等。"""
    _project_id = await _project_with_result(client)
    exports_dir = test_settings.exports_dir
    before_listing = sorted(os.listdir(exports_dir))
    for evil in ("C:\\evil", "/etc/passwd"):
        response = await client.get(f"/api/exports/{evil}")
        assert response.status_code in {404, 422}, (
            f"{evil!r} 期望 4xx（反斜杠冒号 stem 拒 422/含 / 路由 404），"
            f"得到 {response.status_code}"
        )
        assert response.headers.get("content-type", "").startswith("application/json")  # 非文件流
        assert sorted(os.listdir(exports_dir)) == before_listing  # 目录零新增


@pytest.mark.anyio
async def test_download_legit_name_not_registered_returns_404_wiring(
    client, test_settings
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 穿越 DoD 例5：合法形态名不在册→恰 404 ExportFileNotFoundError（注册口径）。"""
    exports_dir = test_settings.exports_dir
    before_listing = sorted(os.listdir(exports_dir))
    response = await client.get("/api/exports/p1-dxf-c-0123456789.dxf")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error_type"] == "ExportFileNotFoundError"  # 实值断言（条款 4）
    assert sorted(os.listdir(exports_dir)) == before_listing  # 目录零新增


@pytest.mark.anyio
async def test_download_product_without_sidecar_returns_404_wiring(
    client, test_settings
) -> None:  # type: ignore[no-untyped-def]
    """EXPD 穿越 DoD 例6：产物在而边车缺（真导出后删 .meta.json）→恰 404（双闸注册口径）。"""
    project_id = await _project_with_result(client)
    file_name = await _export_one_dxf(client, project_id)
    (test_settings.exports_dir / f"{file_name}.meta.json").unlink()  # 边车缺探针
    before_listing = sorted(os.listdir(test_settings.exports_dir))
    response = await client.get(f"/api/exports/{file_name}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error_type"] == "ExportFileNotFoundError"  # 实值断言（条款 4）
    assert sorted(os.listdir(test_settings.exports_dir)) == before_listing  # 目录零新增
