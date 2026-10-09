"""report_pdf 服务面单测：typst 路径三级解析+kind 登记+编译错误面。

输入:  waterprint_server.services.report_pdf（resolve_typst_path/_typst_compile）
       +exports_support kind 登记面
输出:  解析三态断言+命名/下载后缀登记+编译失败显式错误面（stderr 捕获+tmp 清理）

规格说明（B6 计算说明批 2026-10-09 任务书 §二.⑥——部署依赖三级解析：
  settings 覆盖〔env WATERPRINT_TYPST_PATH〕→PATH which→显式
  TypstUnavailableError；winget 路径不入硬编码源码仅落部署文档；
  编译失败/超时=TypstCompileError 500 族显式消息禁静默）。
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from waterprint_server.services.exports_support import (
    _KIND_SUFFIXES,
    _KINDS,
    DOWNLOAD_SUFFIXES,
)
from waterprint_server.services.report_pdf import (
    TypstCompileError,
    TypstUnavailableError,
    _typst_compile,
    resolve_typst_path,
)


def _typst_binary() -> str | None:
    """测试面 typst 发现（which→env→winget 包目录探查——部署文档同源布局）。"""
    found = shutil.which("typst")
    if found:
        return found
    override = os.environ.get("WATERPRINT_TYPST_PATH", "").strip()
    if override and Path(override).is_file():
        return override
    packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    for candidate in packages.glob("Typst.Typst*/typst-*/typst.exe"):
        if candidate.is_file():
            return str(candidate)
    return None


def test_resolve_typst_path_override_wins() -> None:
    """三级解析①：settings 覆盖值（env 载入面）非空即直用（which 不参与）。"""
    assert resolve_typst_path("  C:/tools/typst.exe ") == "C:/tools/typst.exe"


def test_resolve_typst_path_from_which(monkeypatch: pytest.MonkeyPatch) -> None:
    """三级解析②：覆盖空→PATH 发现（shutil.which）。"""
    monkeypatch.setattr(
        shutil, "which", lambda name: "C:/bin/typst.exe" if name == "typst" else None
    )
    assert resolve_typst_path("") == "C:/bin/typst.exe"


def test_resolve_typst_path_unavailable_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """三级解析③：覆盖空+which 空=显式 TypstUnavailableError（部署依赖缺，
    消息含 WATERPRINT_TYPST_PATH 指引——禁静默 None 穿透）。"""
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    with pytest.raises(TypstUnavailableError, match="WATERPRINT_TYPST_PATH"):
        resolve_typst_path("")


def test_report_pdf_kind_registered_in_exports_faces() -> None:
    """kind 登记面：_KINDS 入册（命名闸放行）+后缀 .pdf（下载白名单派生含）。"""
    assert "report_pdf" in _KINDS
    assert _KIND_SUFFIXES["report_pdf"] == ".pdf"
    assert ".pdf" in DOWNLOAD_SUFFIXES  # EXPD 下载面派生自动覆盖


@pytest.mark.skipif(
    _typst_binary() is None,
    reason="typst CLI 不在本机（PDF 编译部署依赖——B6 §二.⑥ 部署依赖申报："
    "winget 安装 Typst.Typst 或设 WATERPRINT_TYPST_PATH；禁静默绿）",
)
def test_typst_compile_error_face_and_tmp_cleanup(tmp_path: Path) -> None:
    """编译错误面：非法源=TypstCompileError（stderr 捕获进消息）+tmp 零残留。"""
    binary = _typst_binary()
    assert binary is not None
    out = tmp_path / "x-report.pdf"
    with pytest.raises(TypstCompileError, match="typst"):
        _typst_compile(binary, '= #("标题"\n$ 未闭合', out, 2 * 10)
    leftovers = list(tmp_path.iterdir())
    assert leftovers == [], f"编译失败须清 tmp（实测残留：{leftovers}）"
