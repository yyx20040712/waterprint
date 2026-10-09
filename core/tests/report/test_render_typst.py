"""render_typst 渲染测试（B6 PDF 路——golden 快照+确定性+结构锚+真编译冒烟）。

输入:  waterprint.report.render_typst + golden 三件套（result/diag/项目）
输出:  Typst 源 golden 字节对账+双渲染恒等+结构锚（A4/页眉/页码/字体/
       数学块/表格引用面）+真编译冒烟（typst 在场；缺席=显式 skip）

规格说明（B6 计算说明批 2026-10-09 任务书 §二.⑥——确定性边界：Typst
  **源**字节=对账面（golden 同 render_md 纪律）；PDF 二进制含引擎时间戳
  不入字节对账面（测试断言面=源字节+编译冒烟魔数/页数探针）。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from waterprint.app import load_project
from waterprint.contracts.result_schema import PlantResult, deserialize
from waterprint.contracts.trust import DiagnosticsReport, deserialize_diag
from waterprint.report import build_report_ast, render_typst

_SAMPLE = (
    Path(__file__).resolve().parent / "__snapshots__" / "municipal_34760.sample.typst"
)
_GOLDEN_CASE = (
    Path(__file__).resolve().parents[2] / "golden" / "golden_data" / "municipal_34760"
)
_PDF_MAGIC = b"%PDF-"


def _typst_binary() -> str | None:
    """测试面 typst 发现（which→env→winget 包目录探查——部署文档同源布局）。

    部署依赖申报（§二.⑥）：typst CLI 必在 server 主机——本探查=测试便利面
    （winget 安装布局目录扫描，非产品代码路径解析真源——产品面三级解析在
    server services/report_pdf.resolve_typst_path）。
    """
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


def _golden_source(
    golden_project_path: Path, golden_plant: PlantResult, golden_diag: DiagnosticsReport
) -> str:
    """golden 三件套 → Typst 源（golden 渲染真源——三用例共享）。"""
    ast = build_report_ast(
        load_project(golden_project_path), golden_plant, diagnostics=golden_diag
    )
    return render_typst(ast, project_label="municipal_34760")


def test_golden_typst_source_matches_committed_sample(
    golden_project_path: Path, golden_plant: PlantResult, golden_diag: DiagnosticsReport
) -> None:
    """golden 快照字节对账：渲染输出 == 入库 sample.typst（确定性锚）。"""
    if not _SAMPLE.is_file():
        pytest.skip(f"Typst 黄金样例缺失：{_SAMPLE}")
    assert _golden_source(golden_project_path, golden_plant, golden_diag) == (
        _SAMPLE.read_text(encoding="utf-8")
    )


def test_render_typst_deterministic_double_run(
    golden_project_path: Path, golden_plant: PlantResult, golden_diag: DiagnosticsReport
) -> None:
    """确定性：同 AST 双渲染逐字节相同（无时钟/无随机——render_md 同纪律）。"""
    first = _golden_source(golden_project_path, golden_plant, golden_diag)
    second = _golden_source(golden_project_path, golden_plant, golden_diag)
    assert first == second


def test_typst_source_structure_anchors(
    golden_project_path: Path, golden_plant: PlantResult, golden_diag: DiagnosticsReport
) -> None:
    """结构锚：A4/页码 numbering/页眉项目名+计算书/字体声明/数学块/表格。"""
    source = _golden_source(golden_project_path, golden_plant, golden_diag)
    assert 'paper: "a4"' in source
    assert 'numbering: "1"' in source  # 页脚页码 counter
    assert 'municipal_34760 · 计算书' in source  # 页眉（项目名+计算书）
    assert '"Times New Roman", "SimSun"' in source  # 字体声明
    assert "$" in source and source.count("$ ") >= 2  # display math 展示块
    assert "#table(" in source
    assert '= #"附录 公式溯源"' in source  # 附录章（不占章号）


def test_typst_source_table_header_quoting_regression(
    golden_project_path: Path, golden_plant: PlantResult, golden_diag: DiagnosticsReport
) -> None:
    """表格头引用面回归锚：table.header 实参必须为字符串字面量。

    历史红面：裸标识符头（工况, 流体——中文非法标识符）真编译即错；
    一切实参首字符须为引号（含附录 catalog 表同面）。
    """
    source = _golden_source(golden_project_path, golden_plant, golden_diag)
    assert re.search(r"table\.header\([^\"']", source) is None


@pytest.mark.skipif(
    _typst_binary() is None,
    reason="typst CLI 不在本机（PDF 编译部署依赖——B6 §二.⑥ 部署依赖申报："
    "winget 安装 Typst.Typst 或设 WATERPRINT_TYPST_PATH；禁静默绿）",
)
def test_real_compile_smoke(
    golden_project_path: Path,
    golden_plant: PlantResult,
    golden_diag: DiagnosticsReport,
    tmp_path: Path,
) -> None:
    """真编译冒烟：golden 全文 Typst 源经 typst CLI 产 PDF（魔数+页数≥1）。"""
    binary = _typst_binary()
    assert binary is not None
    src = tmp_path / "sample.typ"
    src.write_text(
        _golden_source(golden_project_path, golden_plant, golden_diag),
        encoding="utf-8",
    )
    pdf = tmp_path / "sample.pdf"
    compiled = subprocess.run(  # 测试面子进程（binary=受控发现面）
        [binary, "compile", str(src), str(pdf)],
        capture_output=True,
        timeout=10**2,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr.decode("utf-8", "replace")[:2000]
    data = pdf.read_bytes()
    assert data[:5] == _PDF_MAGIC and data
    # 页数探针（字节面 /Count 最大值——无 pypdf 依赖，任务书允许探针口径）
    assert max(int(m) for m in re.findall(rb"/Count (\d+)", data)) >= 1
