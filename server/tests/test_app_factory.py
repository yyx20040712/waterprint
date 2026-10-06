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
    # KbBlockError→422（kbblock 批 D6——kb 阻断门 worker 侧领域异常同款名义表
    # 承载；openapi 契约零改：TaskStatus error_code=anyOf integer|null 值域
    # 已含 422，ADR-026 论证）
    assert DOMAIN_ERROR_CODES["KbBlockError"] == status.HTTP_422_UNPROCESSABLE_CONTENT
    # 附诊断体：错误响应结构 {detail, error_type}
    body = table[InvalidUnitConfig.__name__](None, InvalidUnitConfig("x"))  # type: ignore[arg-type]
    assert b"error_type" in body.body and b"detail" in body.body


def test_domain_error_codes_real_class_binding_quantified() -> None:
    """errmap E1：名义表四键真类绑定**全量化**（逐键码值+set 全量化锚）。

    双通道：core 类改名→import ImportError 红；表键漂移→下标 KeyError/
    集合不等红（回炉轮 1 d1-W1 断言形态的表级全量化扩展——第五键无真类
    锚/删键均红）。注：InvalidUnitConfig 在 DOMAIN_ERROR_CODES 侧=400
    （HTTP 入参校验面），勿照类基映射 422 抄。
    """
    from fastapi import status as http_status

    # 测试件直 import core=回炉轮 1 已立先例（test_calculation.py L156-160）
    from waterprint.contracts.manifest_validation import InvalidUnitConfig
    from waterprint.graph.executor_dsl import InvalidExecutionError
    from waterprint.graph.loop import LoopDivergence
    from waterprint.solution.constraints import KbBlockError

    from waterprint_server.main import DOMAIN_ERROR_CODES

    real_classes = (
        LoopDivergence, InvalidUnitConfig, InvalidExecutionError, KbBlockError,
    )
    expected_codes = {
        "LoopDivergence": http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        "InvalidUnitConfig": http_status.HTTP_400_BAD_REQUEST,
        "InvalidExecutionError": http_status.HTTP_422_UNPROCESSABLE_CONTENT,
        "KbBlockError": http_status.HTTP_422_UNPROCESSABLE_CONTENT,
    }
    for cls in real_classes:  # 逐键：表[真类实名]==预期码（键漂移→KeyError 红）
        assert DOMAIN_ERROR_CODES[cls.__name__] == expected_codes[cls.__name__]
    # 全量化锚：表键集合==四真类名集合（第五键无真类锚/删键均集合不等红）
    assert set(DOMAIN_ERROR_CODES) == {cls.__name__ for cls in real_classes}


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
    （门一框架论断证伪记录）；405 响应仍过中间件，头在场即证判据面覆盖。

    版本耦合注记（批6h 2026-09-27——wave6 §批6h⑧）：本断言与 fastapi
    （传递 starlette）版本行为耦合——现行 fastapi>=0.115 下 APIRoute
    不自动容许 HEAD 故 405；若上游未来改为自动 HEAD 容许，本用例转红
    =有意识绊线（fail-visible），届时人工确认中间件头判据在新语义下
    仍覆盖（200 响应同过中间件）后再更新期望——禁随手改绿。pyproject
    不设 upper bound（依赖钉扎=用户裁决位，批6h Rulings 呈报）。
    """
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
