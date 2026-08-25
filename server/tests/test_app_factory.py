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
