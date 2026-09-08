"""executor_assembly 镜像测试：输入装配域拆分不变量（TD1 裁定件）。

输入:  waterprint.graph.executor 引用面与 executor_assembly 定义面
输出:  恒等断言（缝 A 六符号同一对象——executor 消费面零改动钉面；
       行为零变更纯搬迁的回归钉）
"""

from __future__ import annotations

from waterprint.graph import executor, executor_assembly


def test_assembly_identity() -> None:
    """装配域六符号经 executor 导入=定义面同一对象（TD1 缝 A 拆分不变量钉面）。"""
    assert executor._LOOP_KEYS is executor_assembly._LOOP_KEYS  # noqa: SLF001  # 私有面钉面（恒等断言——test_executor_dsl 先例）
    assert executor._NullSink is executor_assembly._NullSink  # noqa: SLF001
    assert executor._endpoint is executor_assembly._endpoint  # noqa: SLF001
    assert executor._edges_from_design is executor_assembly._edges_from_design  # noqa: SLF001
    assert executor._loop_config is executor_assembly._loop_config  # noqa: SLF001
    assert executor._unit_params is executor_assembly._unit_params  # noqa: SLF001
