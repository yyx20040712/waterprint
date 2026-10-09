"""report_pdf 路由契约测试：POST /api/exports/report_pdf（Typst PDF 计算书）。

输入:  waterprint_server.routers.report_pdf 端点 + services.report_pdf 编排
输出:  HTTP 契约（200 PDF 文件流+kind 面板登记+下载/stale 409 与 force/
       404 两面/unit_id 422）——真编译面 typst 在场承载，缺席=显式 skip

规格说明（B6 计算说明批 2026-10-09 任务书 §二.⑥——端点形态沿 calcbook/
  audit 惯例〔body {project_id, condition_key, options}+?force=1〕；
  产物落 exports/ 确定性命名+.meta.json 边车沿既有；stale 守门 409 同族；
  部署依赖=typst CLI 必在 server 主机——测试面缺席=skip 显式标注禁静默绿）。
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import status

from waterprint_server.routers import report_pdf as report_pdf_router
from waterprint_server.settings import Settings

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REPO_DATA = _REPO_ROOT / "data"

_EXPECTED_REPORT_PDF = {("post", "/api/exports/report_pdf")}


def _typst_binary() -> str | None:
    """测试面 typst 发现（which→env→winget 包目录探查——部署文档同源布局）。"""
    found = shutil.which("typst")
    if found:
        return found
    override = os.environ.get("WATERPRINT_TYPST_PATH", "").strip()
    if override and Path(override).is_file():
        return override
    packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for candidate in packages.glob("Typst.Typst*/typst-*/typst.exe"):
        if candidate.is_file():
            return str(candidate)
    return None


def _cass_project_payload() -> dict[str, object]:
    """inlet→CASS 项目载荷（conftest cass_payload 同源）。"""
    return {
        "project": {
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
                    "municipal_cass": {},
                },
                "edges": [
                    {
                        "src": {"unit_id": "inlet", "port_id": "out"},
                        "dst": {"unit_id": "municipal_cass", "port_id": "in"},
                    }
                ],
            },
            "view": {},
            "metadata": {
                "format_version": "1.0",
                "content_hash": "0",
                "engine_version": "0",
                "data_version": "0",
            },
        }
    }


@pytest.fixture
def pdf_settings(tmp_path: Path) -> Settings:
    """report_pdf 消费面 Settings（conftest.test_settings 同款+typst 路径注入）。

    typst 在场=env WATERPRINT_TYPST_PATH 载入（三级解析①通道——真部署同路）；
    缺席=空串（三级解析走 which，本机无则相关用例 skip）。
    """
    data_dir = tmp_path / "data"
    (data_dir / "templates").mkdir(parents=True)
    shutil.copytree(_REPO_DATA / "coefficients", data_dir / "coefficients")
    shutil.copytree(_REPO_DATA / "constraint_kb", data_dir / "constraint_kb")
    shutil.copytree(_REPO_DATA / "unit_prices", data_dir / "unit_prices")
    binary = _typst_binary()
    if binary:
        os.environ["WATERPRINT_TYPST_PATH"] = binary
    return Settings(
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=data_dir,
        calc_workers=1,
        log_file=str(tmp_path / "test-report-pdf.log"),
    )


@pytest.fixture
async def client(pdf_settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """ASGITransport AsyncClient（conftest.client 同款+typst env 前置）。"""
    from waterprint_server.main import create_app

    executor = ThreadPoolExecutor(max_workers=pdf_settings.calc_workers)
    application = create_app(pdf_settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    executor.shutdown(wait=True)
    os.environ.pop("WATERPRINT_TYPST_PATH", None)


async def _project_with_result(client: httpx.AsyncClient) -> str:
    """创建 CASS 项目并跑一次计算（结果集就绪）。"""
    created = await client.post("/api/projects", json=_cass_project_payload())
    assert created.status_code == status.HTTP_200_OK
    project_id = created.json()["project_id"]
    task_id = (await client.post(
        "/api/calc/run", json={"project_id": project_id, "conditions": []}
    )).json()["task_id"]
    body: dict[str, object] = {}
    for _ in range(300):
        body = (await client.get(f"/api/calc/tasks/{task_id}")).json()
        if body.get("state") in {"done", "failed"}:
            break
        await asyncio.sleep(0.1)
    assert body["state"] == "done"
    return project_id


def _pdf_pages(payload: bytes) -> int:
    """PDF 页数探针（/Count 最大值——字节探针面，无 pypdf 依赖）。"""
    return max(int(m) for m in re.findall(rb"/Count (\d+)", payload))


def test_router_exposes_report_pdf_endpoint_wiring() -> None:
    """report_pdf 路由件端点集恰一件（46→47 增量无漂移——独立路由件：
    exports.router 镜像测试七件冻结断言=人类锁定面，本端点独立挂载零触碰）。"""
    observed = {
        (method.lower(), route.path)
        for route in report_pdf_router.router.routes
        for method in route.methods  # type: ignore[union-attr]
    }
    assert observed == _EXPECTED_REPORT_PDF


@pytest.mark.anyio
async def test_report_pdf_404_faces(client: httpx.AsyncClient) -> None:
    """404 两面（typst 无关——取数先于编译）：未知项目/无结果集。"""
    response = await client.post("/api/exports/report_pdf", json={"project_id": "nosuch"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    created = await client.post("/api/projects", json=_cass_project_payload())
    project_id = created.json()["project_id"]
    response = await client.post(
        "/api/exports/report_pdf", json={"project_id": project_id}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "/api/calc/run" in response.json()["detail"]


@pytest.mark.anyio
async def test_report_pdf_unit_id_rejected_422(client: httpx.AsyncClient) -> None:
    """unit_id 422 拒（全厂整厂产物——audit/estimate 同族预校验）。"""
    response = await client.post(
        "/api/exports/report_pdf",
        json={
            "project_id": "nosuch",
            "options": {"unit_id": "municipal_cass"},
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "unit_id" in response.json()["detail"]


@pytest.mark.anyio
async def test_report_pdf_stale_409_without_typst(client: httpx.AsyncClient) -> None:
    """stale 守门（typst 无关——守门先于编译）：PUT 改参→409；未 force 禁出件。"""
    project_id = await _project_with_result(client)
    saved = (await client.get(f"/api/projects/{project_id}")).json()
    project = dict(saved)
    project["design"]["nodes"]["municipal_cass"]["n"] = 3.0
    put = await client.put(f"/api/projects/{project_id}", json=project)
    assert put.status_code == status.HTTP_200_OK
    response = await client.post(
        "/api/exports/report_pdf", json={"project_id": project_id}
    )
    assert response.status_code == status.HTTP_409_CONFLICT  # §17.1 导出行
    assert "禁止静默导出" in response.json()["detail"]


@pytest.mark.skipif(
    _typst_binary() is None,
    reason="typst CLI 不在本机（PDF 编译部署依赖——B6 §二.⑥ 部署依赖申报："
    "winget 安装 Typst.Typst 或设 WATERPRINT_TYPST_PATH；禁静默绿）",
)
@pytest.mark.anyio
async def test_report_pdf_200_compile_list_download(
    client: httpx.AsyncClient, pdf_settings: Settings
) -> None:
    """200 主线：真编译产 PDF（魔数+页数≥1）+kind 面板登记+下载通道。"""
    project_id = await _project_with_result(client)
    response = await client.post(
        "/api/exports/report_pdf", json={"project_id": project_id}
    )
    assert response.status_code == status.HTTP_200_OK
    payload = response.content
    assert payload[:8] == b"%PDF-1.7"
    assert _pdf_pages(payload) >= 1
    # kind 面板：产物列表含 report_pdf 行+边车在场
    listed = (await client.get("/api/exports", params={"project_id": project_id})).json()
    rows = [row for row in listed if row["kind"] == "report_pdf"]
    assert len(rows) == 1
    file_name = rows[0]["file_name"]
    assert file_name.endswith(".pdf")
    assert (pdf_settings.exports_dir / f"{file_name}.meta.json").is_file()
    # 下载通道（后缀白名单派生含 .pdf——EXPD D1 面）
    download = await client.get(f"/api/exports/{file_name}")
    assert download.status_code == status.HTTP_200_OK
    assert download.content[:8] == b"%PDF-1.7"


@pytest.mark.skipif(
    _typst_binary() is None,
    reason="typst CLI 不在本机（PDF 编译部署依赖——B6 §二.⑥ 部署依赖申报："
    "winget 安装 Typst.Typst 或设 WATERPRINT_TYPST_PATH；禁静默绿）",
)
@pytest.mark.anyio
async def test_report_pdf_force_stale_labeled(client: httpx.AsyncClient) -> None:
    """force=1：stale 结果仍可导出+边车 stale_labeled=True 显式标注。"""
    project_id = await _project_with_result(client)
    saved = (await client.get(f"/api/projects/{project_id}")).json()
    project = dict(saved)
    project["design"]["nodes"]["municipal_cass"]["n"] = 3.0
    await client.put(f"/api/projects/{project_id}", json=project)
    response = await client.post(
        "/api/exports/report_pdf", params={"force": True}, json={"project_id": project_id}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.content[:8] == b"%PDF-1.7"
    listed = (await client.get("/api/exports", params={"project_id": project_id})).json()
    rows = [row for row in listed if row["kind"] == "report_pdf"]
    assert rows[0]["stale_labeled"] is True  # 产物永不冒充（R1）
