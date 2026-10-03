"""trust_serde 镜像测试：拆件引用连续恒等钉（kbflag-20261003 拆件笔）。

输入:  waterprint.contracts.trust（正门）+trust_serde（serde 内核定义面）
输出:  恒等断言——同名再导出两函数 is 同一对象+__all__ 在场（消费方
       import 面零变化的机器锚；序列化行为面测试归 test_trust.py）。
"""

from __future__ import annotations

from waterprint.contracts import trust, trust_serde


def test_reexport_identity_pins() -> None:
    """恒等钉：trust 两正门函数与 trust_serde 同名定义 is 同一对象
    （定义面迁移、正门面恒等——拆件纯搬迁零行为的机器锚）。"""
    assert trust.serialize_diag is trust_serde.serialize_diag
    assert trust.deserialize_diag is trust_serde.deserialize_diag
    assert "serialize_diag" in trust.__all__
    assert "deserialize_diag" in trust.__all__
