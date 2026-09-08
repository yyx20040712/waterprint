"""app_export 伴生件镜像测试（PROFILE3 2026-09-08 拆分回归钉）。

输入:  inlet→cass 夹具（test_export_profile 同源）
输出:  ①拆分再导出恒等（app_enumeration 再导出面与 app_export 正门同
       对象——消费面零改动承诺的机器锚）；②导出正门路由烟测（纵断
       sheet 通道经新正门可达）。
"""

from __future__ import annotations

from pathlib import Path

import waterprint.app_enumeration as _enum
import waterprint.app_export as _export
from tests.app.test_export_profile import _plant


def test_split_reexport_identity() -> None:
    """拆分回归钉：app_enumeration 再导出=app_export 正门同一对象。"""
    assert _enum.export_artifact is _export.export_artifact
    assert _enum.ArtifactKindNotReady is _export.ArtifactKindNotReady


def test_export_entry_via_new_module(tmp_path: Path) -> None:
    """经新正门的纵断导出烟测（sheet 通道可达+落盘一致）。"""
    plant = _plant()
    out = tmp_path / "p.dxf"
    payload = _export.export_artifact(  # type: ignore[misc]
        "dxf", plant, Path("unused"), out,
        condition_key="design", sheet="profile",
    )
    assert payload and out.read_bytes() == payload
