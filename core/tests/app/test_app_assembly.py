"""app_assembly 镜像测试：装配域拆分不变量（B3-R11 裁定件）。

输入:  waterprint.app 再导出面与 waterprint.app_assembly 定义面
输出:  恒等断言（assemble/_unit_params/AssembledGraph 同一对象——再导出
       保消费面 from waterprint.app import 零改动，UF-33 单入口语义）
"""

from __future__ import annotations

from waterprint import app, app_assembly


def test_reexport_identity() -> None:
    """装配域三符号经 app 再导出=定义面同一对象（B3 笔①拆分不变量钉面）。"""
    assert app.assemble is app_assembly.assemble
    assert app._unit_params is app_assembly._unit_params  # noqa: SLF001  # 私有直 import 消费面在册（test_unit_params_projection 同符号）
    assert app.AssembledGraph is app_assembly.AssembledGraph
