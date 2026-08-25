"""server 测试系统装配：httpx AsyncClient/TestClient fixtures（薄，禁业务断言）。

输入:  无
输出:  app/client/settings fixtures（供 routers/services/jobs 测试）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【fixtures】
#   test_settings：临时目录版 Settings（projects/exports/data 均
#     指向 tmp_path，隔离真实文件系统）；
#   client：create_app(test_settings) + httpx TestClient
#     （实现期改用 ASGITransport AsyncClient）。
# 【本文件只读锁定范围之外】——server/tests 全目录同样纳入
#   test-lock.manifest.json（scripts/lock_tests.py 统一处理）。
#
# 【实现注记（SERVER 2026-08-26，总授权激活批）】
#   - client 用 ASGITransport AsyncClient（规格头口径）+ lifespan_context
#     显式启停（ASGITransport 不自动走 lifespan）；executor 注入
#     ThreadPoolExecutor（真进程池 spawn 探针另在报告实录——本 fixture
#     语义面等价：同一 run_task/进度桥/取消令牌路径）。
#   - 数据面：coefficients 用仓库真数据包（拷贝至 tmp data_dir 只读面）；
#     模板由 fixture 生成（UF-16：data/templates 0.0.0 无模板文件）。
#   - 异步测试经 anyio 插件（anyio 为 fastapi 传递依赖，零新增依赖）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import shutil
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from openpyxl import Workbook

from waterprint_server.jobs.manager import Manager
from waterprint_server.main import create_app
from waterprint_server.services import ServiceContext
from waterprint_server.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_DATA = REPO_ROOT / "data"


@pytest.fixture
def anyio_backend() -> str:
    """anyio 插件后端选择（asyncio——与生产事件循环一致）。"""
    return "asyncio"


def _cass_project_payload() -> dict[str, object]:
    """CASS 单元项目（枚举/计算测试载体——bench 同源最小图）。"""
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


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """临时目录版 Settings（三目录指向 tmp；coefficients 真包拷贝只读面）。"""
    data_dir = tmp_path / "data"
    (data_dir / "templates").mkdir(parents=True)
    shutil.copytree(REPO_DATA / "coefficients", data_dir / "coefficients")
    workbook = Workbook()
    sheet = workbook.active
    sheet["A1"] = "{{trace[0].unit_id}}"
    sheet["B1"] = "静态文本"
    workbook.save(data_dir / "templates" / "calcbook_unit.xlsx")
    return Settings(
        projects_dir=tmp_path / "projects",
        exports_dir=tmp_path / "exports",
        data_dir=data_dir,
        calc_workers=1,
        log_file=str(tmp_path / "test-server.log"),
    )


@pytest.fixture
async def client(test_settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """ASGITransport AsyncClient（lifespan 显式启停；ThreadPool 注入=spawn 探针外置）。"""
    executor = ThreadPoolExecutor(max_workers=test_settings.calc_workers)
    application = create_app(test_settings, executor=executor)
    async with application.router.lifespan_context(application):
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            yield async_client
    executor.shutdown(wait=True)


@pytest.fixture
async def service_ctx(test_settings: Settings) -> AsyncIterator[ServiceContext]:
    """服务层直测装配束（Manager 真调度 + ThreadPool 执行面）。"""
    from waterprint_server.settings import ensure_directories

    ensure_directories(test_settings)
    (test_settings.exports_dir / "tasks" / "cancel").mkdir(parents=True, exist_ok=True)
    executor = ThreadPoolExecutor(max_workers=1)
    manager = Manager(
        executor,
        cancel_dir=test_settings.exports_dir / "tasks" / "cancel",
        loop=asyncio.get_running_loop(),
        max_concurrent=1,
    )
    manager.start()
    yield ServiceContext(settings=test_settings, manager=manager)
    await manager.shutdown(1.0)
    executor.shutdown(wait=True)


@pytest.fixture
def cass_payload() -> dict[str, object]:
    """CASS 项目 JSON（创建端点载体）。"""
    return _cass_project_payload()
