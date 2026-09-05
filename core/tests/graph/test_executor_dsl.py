"""executor_dsl 镜像测试：DSL 域拆分不变量（B3-R11 裁定件）。

输入:  waterprint.graph.executor 再导出面与 executor_dsl 定义面
输出:  恒等断言（_apply_mappings/InvalidExecutionError 同一对象——再导出
       保消费面 from waterprint.graph.executor import 零改动；dsl→executor
       反向环根除=修正①钉面）
"""

from __future__ import annotations

from waterprint.graph import executor, executor_dsl


def test_reexport_identity() -> None:
    """DSL 域符号经 executor 再导出=定义面同一对象（B3 笔①拆分不变量钉面）。"""
    assert executor._apply_mappings is executor_dsl._apply_mappings  # noqa: SLF001  # 私有面钉面（实名 _apply_mappings——B3-R11 裁定文）
    assert executor.InvalidExecutionError is executor_dsl.InvalidExecutionError
