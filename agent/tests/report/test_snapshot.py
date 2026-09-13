"""渲染黄金样例快照测试（__snapshots__/municipal_34760.sample.md——字节级对照）。

样例文件由轨道丙一次性生成入库（只读黄金样例——diagnostics 已接线；
AI1-INTEG-2026-09-13 §3 预裁决①自 report/templates/ 迁入 __snapshots__/
——快照资产归宿，预算门禁排除区）；测试将 golden 实数据管线渲染输出与
其字节级对照（确定性锚）。result.json 或 diag.json 缺失即 skip。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from waterprint.app import load_project
from waterprint.contracts.result_schema import PlantResult
from waterprint.contracts.trust import DiagnosticsReport

from waterprint_agent.report.build import build_report_ast
from waterprint_agent.report.render_md import render_markdown

_SAMPLE = (
    Path(__file__).resolve().parent
    / "__snapshots__"
    / "municipal_34760.sample.md"
)


def test_golden_render_matches_committed_sample(
    golden_project_path: Path,
    golden_plant: PlantResult,
    golden_diag: DiagnosticsReport,
) -> None:
    if not _SAMPLE.is_file():
        pytest.skip(f"渲染黄金样例缺失：{_SAMPLE}")
    project = load_project(golden_project_path)
    ast = build_report_ast(project, golden_plant, diagnostics=golden_diag)
    assert render_markdown(ast) == _SAMPLE.read_text(encoding="utf-8")
