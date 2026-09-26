"""应用工厂镜像测试：生命周期、异常映射、契约自检。

输入:  waterprint_server.main 公开符号
输出:  工厂契约断言
"""

from __future__ import annotations

import importlib

import pytest
from fastapi import status

_mod = importlib.import_module("waterprint_server.main")
create_app = getattr(_mod, "create_app")

pytestmark = [
    pytest.mark.skipif(
        create_app is None,
        reason="实现未就绪：waterprint_server.main.create_app（服务层 M2）",
    ),
]


def test_factory_repeats_without_global_state_wiring() -> None:
    """R1 接线断言：create_app 两次构建互不污染（可测试工厂）。"""
    from waterprint_server.settings import Settings

    settings = Settings()
    first = create_app(settings)
    second = create_app(settings)
    paths_first = sorted(first.openapi()["paths"])
    paths_second = sorted(second.openapi()["paths"])
    assert paths_first == paths_second and len(paths_first) > 1  # 路由数一致
    handlers_first = {exc.__name__ for exc in first.exception_handlers}
    handlers_second = {exc.__name__ for exc in second.exception_handlers}
    assert handlers_first == handlers_second and len(handlers_first) > 1  # 映射一致
    assert first.state is not second.state  # 独立装配束（无全局可变态）


def test_domain_exception_mapping_complete_wiring() -> None:
    """R2 接线断言：领域异常映射表覆盖核心异常（400/404/422）。

    InvalidUnitConfig→400、NotFound 族→404、LoopDivergence→422（附诊断体）
    ——LoopDivergence 类不可直连导入（D7 forbidden：waterprint.graph），
    经 DOMAIN_ERROR_CODES 名义表承载（worker 诊断消费面，集中一处）。
    """
    from waterprint.contracts.manifest import InvalidUnitConfig

    from waterprint_server.jobs.manager import UnknownTaskError
    from waterprint_server.main import DOMAIN_ERROR_CODES
    from waterprint_server.services.projects import ProjectNotFoundError
    from waterprint_server.settings import Settings

    app = create_app(Settings())
    table = {
        exc.__name__: handler for exc, handler in app.exception_handlers.items()
    }
    handler = table[InvalidUnitConfig.__name__]
    response = handler(None, InvalidUnitConfig("单元配置非法"))  # type: ignore[arg-type]
    assert response.status_code == status.HTTP_400_BAD_REQUEST  # InvalidUnitConfig→400
    response = table[ProjectNotFoundError.__name__](  # type: ignore[arg-type]
        None, ProjectNotFoundError("项目不存在")
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND  # NotFound→404
    response = table[UnknownTaskError.__name__](None, UnknownTaskError("任务不存在"))  # type: ignore[arg-type]
    assert response.status_code == status.HTTP_404_NOT_FOUND  # 任务 NotFound→404
    # LoopDivergence→422 附诊断（名义表——类基映射不可达的 worker 侧领域异常）
    assert DOMAIN_ERROR_CODES["LoopDivergence"] == status.HTTP_422_UNPROCESSABLE_CONTENT
    # 附诊断体：错误响应结构 {detail, error_type}
    body = table[InvalidUnitConfig.__name__](None, InvalidUnitConfig("x"))  # type: ignore[arg-type]
    assert b"error_type" in body.body and b"detail" in body.body


# ══ R4 C-2：no-store 全 GET 读面中间件（[HUMAN-LOCK] 2026-09-26 落地；
#     test_r4_draft.py C-2 节转正——夹具沿本文件既有 conftest client）══


@pytest.mark.anyio
async def test_c2_api_get_list_no_store(client) -> None:  # type: ignore[no-untyped-def]
    """C-2：/api/ GET 列表读面统一 no-store（R2-P2-1 单点外其余读面同病根除）。"""
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"


@pytest.mark.anyio
async def test_c2_static_units_no_store(client) -> None:  # type: ignore[no-untyped-def]
    """C-2：units 静态目录面同禁（本批全禁口径——豁免留后续按需开）。"""
    resp = await client.get("/api/units")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"


@pytest.mark.anyio
async def test_c2_head_no_store(client) -> None:  # type: ignore[no-untyped-def]
    """C-2 回炉（d1 N-5）：HEAD 防御覆盖——FastAPI APIRoute 实测 405 不自动容许 HEAD
    （门一框架论断证伪记录）；405 响应仍过中间件，头在场即证判据面覆盖。"""
    resp = await client.head("/api/projects")
    assert resp.status_code == 405
    assert resp.headers["cache-control"] == "no-store"


@pytest.mark.anyio
async def test_c2_post_not_stamped(client) -> None:  # type: ignore[no-untyped-def]
    """C-2 回炉（d1 N2b）：POST 面不加盖（仅读面判据的负向边界锚）。

    空 body=合法空白新建（CreateProjectRequest.project 可选）→200——POST
    成功面同样不加盖，边界语义一致。
    """
    resp = await client.post("/api/projects", json={})
    assert resp.status_code == 200
    assert "cache-control" not in resp.headers


@pytest.mark.anyio
async def test_c2_non_api_get_exempt(client) -> None:  # type: ignore[no-untyped-def]
    """C-2：非 /api/ 前缀 GET 不加盖（openapi 文档面——豁免边界锚）。"""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert "cache-control" not in resp.headers
