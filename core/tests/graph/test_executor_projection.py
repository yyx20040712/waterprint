"""executor_projection 镜像测试：投影域拆分不变量（B3-R11 裁定件）。

输入:  waterprint.graph.executor 再导出面与 executor_projection 定义面
输出:  恒等断言（_dims_of/_snapshot 同一对象——再导出保消费面 from
       waterprint.graph.executor import 零改动；领域异常经 dsl import
       同向无环=修正②钉面）
"""

from __future__ import annotations

from waterprint.graph import executor, executor_projection


def test_reexport_identity() -> None:
    """投影域符号经 executor 再导出=定义面同一对象（B3 笔①拆分不变量钉面）。"""
    assert executor._dims_of is executor_projection._dims_of  # noqa: SLF001  # 私有面钉面（B3-R11 裁定文）
    assert executor._snapshot is executor_projection._snapshot  # noqa: SLF001  # 同上
