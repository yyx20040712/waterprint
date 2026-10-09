"""registry 全量 Typst 真编译门（W-D——B6 R1 回炉 2026-10-09 拨4）。

面：451 条公式 Typst 串（TypstMathPrinter 输出面）经 typst CLI 真编译
零错——快照 golden 只对账字节，语义可编译性（邻接歧义/标识符保留字/
e 记数指数形态）只有真编译能证。覆盖锚：GM-F8/F9/KN-F6 的
``1 times 10^(-06)`` e 记数族（d1-W3 点名面）。

typst CLI 缺席=显式 skip（部署依赖——禁静默绿；三级解析面同
server/tests test_report_pdf 惯例：which→WATERPRINT_TYPST_PATH→winget
包目录探查）。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# registry 装载面子进程脚本（干净面——stdout 出 JSON：count/rows[fid,typst]）
_COMPILE_WORKER = """
import io, json, sys
from contextlib import redirect_stdout
with redirect_stdout(io.StringIO()):
    from waterprint.units_lib import discover_units
    discover_units()
    import waterprint.elevation.losses
    import waterprint.network.manning
from waterprint.registry.formulas.store import _REGISTRY
from waterprint.report.formula_printers import typst_of_expression
rows = []
for fid in sorted(_REGISTRY):
    spec = _REGISTRY[fid].spec
    rows.append([fid, typst_of_expression(spec.expression, spec.symbols)])
print(json.dumps({"count": len(_REGISTRY), "rows": rows}, ensure_ascii=False))
"""


def _typst_binary() -> str | None:
    """typst CLI 发现（which→env→winget 包目录——部署文档同源布局）。"""
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


def _registry_rows() -> list[list[str]]:
    """干净装载面全量 (fid, typst) 行（子进程隔离——快照测试同款纪律）。"""
    result = subprocess.run(
        [sys.executable, "-c", _COMPILE_WORKER],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)["rows"]


@pytest.mark.skipif(
    _typst_binary() is None,
    reason="typst CLI 不在本机（registry 全量真编译门=部署依赖——winget 安装"
    " Typst.Typst 或设 WATERPRINT_TYPST_PATH；禁静默绿）",
)
def test_registry_full_typst_compile_zero_error(tmp_path: Path) -> None:
    """451 条全量真编译零错+e 记数指数形态在编译面承载（W-D 主锚）。"""
    typst_bin = _typst_binary()
    assert typst_bin
    rows = _registry_rows()
    assert len(rows) >= 451  # 装载面基数下限（业务线扩充单增）
    # e 记数指数形态锚（d1-W3 点名：GM-F8/F9/KN-F6 的 10^(-06) 族——
    # 防空文件静默绿：编译载荷必含该族实样）
    body = dict(rows)
    for fid in ("GM-F8", "GM-F9", "KN-F6"):
        assert "10^(-06)" in body[fid], f"{fid} e 记数形态缺席（编译面失锚）"
    lines = ["#set page(width: 10cm, height: auto, margin: 4mm)",
             "#set text(size: 6pt)"]
    lines += [f"$ {text} $" for _, text in rows]
    src = tmp_path / "registry_all.typ"
    pdf = tmp_path / "registry_all.pdf"
    src.write_text("\n".join(lines), encoding="utf-8")
    compiled = subprocess.run(  # 受控二进制（三级解析发现面）；参数数组形
        [typst_bin, "compile", str(src), str(pdf)],
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert compiled.returncode == 0, (
        "registry 全量 Typst 真编译失败：\n"
        f"{compiled.stderr.decode('utf-8', 'replace')[-2000:]}"
    )
    assert pdf.is_file() and pdf.read_bytes()[:5] == b"%PDF-"
