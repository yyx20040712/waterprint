"""report 服务面单测：sections 两级投影纯函数+模型形状。

输入:  waterprint_server.services.report（_sections_of 纯投影+响应模型）
输出:  章/小节两级索引形状断言（id 确定性/level 语义/附录章投影）

规格说明（B6 计算说明批 2026-10-09 任务书 §二.④ R4——服务面纯函数
  直测；契约三面归 tests/routers/test_report.py）。
"""

from __future__ import annotations

from waterprint.report import (
    Chapter,
    NarrativeSlot,
    NoteLine,
    NumberLine,
    Section,
    TableBlock,
)

from waterprint_server.services.report import (
    ReportGeneratedFromModel,
    ReportResponse,
    ReportSectionModel,
    _sections_of,
)


def _sample_ast() -> tuple[Chapter, ...]:
    """两章样例 AST：unit_calc 含两小节+附录不编号章（Section 仅第 4 章族）。"""
    return (
        Chapter(
            id="design_basis",
            title="设计依据",
            blocks=(TableBlock(title="t", headers=("a",), rows=(("b",)),),
                    NoteLine(text="n")),
        ),
        Chapter(
            id="unit_calc",
            title="构筑物逐单元计算",
            blocks=(
                Section(title="AAO 生物池（municipal_aao）",
                        blocks=(NumberLine(label="L", value=1.0, unit="m"),)),
                Section(title="CASS 生物池（municipal_cass）",
                        blocks=(NarrativeSlot(slot_id="s", hint="h"),)),
                NoteLine(text="尾注"),
            ),
        ),
        Chapter(id="formula_appendix", title="公式溯源", blocks=(), numbered=False),
    )


def test_sections_of_two_level_projection() -> None:
    """两级投影：章 level=1（附录章在内）；Section level=2 且 id 序确定性。"""
    sections = _sections_of(_sample_ast())
    assert [(s.id, s.level) for s in sections] == [
        ("design_basis", 1),
        ("unit_calc", 1),
        ("unit_calc-1", 2),
        ("unit_calc-2", 2),
        ("formula_appendix", 1),
    ]
    by_id = {s.id: s for s in sections}
    assert by_id["unit_calc-1"].title.startswith("AAO 生物池")
    assert by_id["unit_calc-2"].title.startswith("CASS 生物池")


def test_sections_of_deterministic_double_run() -> None:
    """确定性：同 AST 双投影逐项相等（无时钟/无随机——render_md 同纪律）。"""
    first = _sections_of(_sample_ast())
    second = _sections_of(_sample_ast())
    assert first == second


def test_report_response_model_frozen_shape() -> None:
    """响应模型形状冻结（frozen 模型+generated_from 嵌套摘要面）。"""
    model = ReportResponse(
        project_id="p",
        condition_key="design",
        stale=False,
        design_hash="a" * 64,
        markdown="# m",
        sections=(ReportSectionModel(id="design_basis", title="设计依据", level=1),),
        generated_from=ReportGeneratedFromModel(digest10="a" * 10),
    )
    assert model.generated_from.digest10 == model.design_hash[:10]
    assert model.model_config.get("frozen") is True
