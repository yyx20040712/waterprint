"""flows 卫生面镜像测试：exp-hygiene-20260930（H5 tmp 全异常清理+H2 再导出）。

输入:  waterprint.flows（audit_render_flow/result_persist_flow/trace 异常族再导出）
输出:  flows 行为契约断言（异常路径 tmp 零残留/再导出恒等零新边）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（exp-hygiene-20260930 exports 卫生批·core 小笔 server 侧锚）
#
# 【覆盖面】
#   - H5：audit_render_flow/result_persist_flow 半写 tmp 在**任何**异常
#     路径清理后 re-raise（原 except OSError 面——非 OSError 异常残留
#     .tmp 半写文件；任务书 P5 全异常清理）；
#   - H2：trace.audit 异常族（InvalidAuditError/InvalidAuditPathError）
#     经 flows 再导出恒等（server forbidden 面零直连——__all__ 同步）。
# 【替身口径】render_audit_html/discover_units monkeypatch 替身（tmp 半写
#   后 raise——被测面=flows 清理逻辑非渲染本体）；result_persist_flow 面
#   经 os.replace 注入非 OSError（tmp 已由真码 write_bytes 落位）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.flows")

pytestmark = [pytest.mark.anyio]


def test_flows_reexport_trace_audit_exception_family_identity() -> None:
    """H2（exp-hygiene-20260930）：trace.audit 异常族经 flows 再导出——
    类对象恒等（零新边零复制）+__all__ 同步（server 面禁直连 trace，
    经 flows 取用——任务书 P2）。"""
    trace_mod = importlib.import_module("waterprint.trace.audit")
    assert _mod.InvalidAuditError is trace_mod.InvalidAuditError  # 同一类对象
    assert _mod.InvalidAuditPathError is trace_mod.InvalidAuditPathError
    assert "InvalidAuditError" in _mod.__all__  # 公开面同步（无 underscore 私引）
    assert "InvalidAuditPathError" in _mod.__all__


async def test_audit_render_flow_cleans_tmp_on_any_exception(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """H5：audit_render_flow 渲染期非 OSError 异常（半写 tmp 后 raise）
    ——清理半写 .tmp 后 re-raise（异常路径后 tmp 计数=0）。"""
    out = tmp_path / "report.html"

    def _half_write_then_raise(trace, result, target):  # type: ignore[no-untyped-def]
        Path(target).write_text("<html>half", encoding="utf-8")  # 半写 tmp
        raise ValueError("injected non-OSError render failure (H5)")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_mod, "discover_units", lambda: None)  # 注册表装载面外置
        mp.setattr(_mod, "render_audit_html", _half_write_then_raise)
        plant = type("PlantStub", (), {"trace": None})()  # 实参求值面（.trace）
        with pytest.raises(ValueError, match="H5"):
            _mod.audit_render_flow(object(), plant, out)  # type: ignore[arg-type]
    assert not out.exists()  # 终名未落位（异常=re-raise 非吞）
    assert list(tmp_path.glob("*.tmp")) == []  # 半写 tmp 已清理（曾残留）


async def test_result_persist_flow_cleans_tmp_on_any_exception(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """H5（同族两处一致性）：result_persist_flow 落盘期非 OSError 异常
    （tmp 已由真码 write_bytes 落位后 replace 失败）——清理 .tmp 后
    re-raise（P5：两函数对齐，禁单侧残留）。"""
    import os

    out = tmp_path / "calc-result.json"

    def _boom(src, dst):  # type: ignore[no-untyped-def]
        raise RuntimeError("injected non-OSError replace failure (H5)")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_mod, "serialize", lambda plant: b"{}")  # 序列化面外置
        mp.setattr(os, "replace", _boom)
        with pytest.raises(RuntimeError, match="H5"):
            _mod.result_persist_flow(object(), out)  # type: ignore[arg-type]
    assert not out.exists()
    assert list(tmp_path.glob("*.tmp")) == []  # tmp 已清理（曾残留）
