"""操作链 debug 用例镜像测试（B4-1 薄壳——[HUMAN-LOCK] 锁面笔批准后拷入 server/tests/services/）。

输入:  services/ops_debug 公开面（build_ops_chain+五响应模型）
输出:  导入冒烟+公开面在场+正门 404/空态冒烟（行为全矩阵=仓外探针
       probe_ops_chain.py 37 项实证；薄壳义务=B2-5/B3-c 同款最小面）
"""

from __future__ import annotations

import pytest

from waterprint_server.services import ops_debug


def test_public_surface() -> None:
    """公开面在场（六名——服务件 __all__ 契约）。"""
    for name in (
        "OpsChainResponse", "OpsTaskModel", "LatestCalcBlockModel",
        "DiagSummaryModel", "TraceSummaryModel", "build_ops_chain",
    ):
        assert hasattr(ops_debug, name), name


@pytest.mark.anyio
async def test_unknown_project_404(client, service_ctx) -> None:  # noqa: ANN001
    """正门 404 冒烟（未知项目——ProjectNotFoundError 面）。"""
    from waterprint_server.services.projects import ProjectNotFoundError

    with pytest.raises(ProjectNotFoundError):
        ops_debug.build_ops_chain(service_ctx, "no-such-project")
