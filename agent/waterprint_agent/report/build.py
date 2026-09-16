"""设计说明书 AST 装配（七章节，D5① 映射表为真源——数据驱动生成）。

路径:   waterprint_agent/report/build.py
职责:   ProjectFile+PlantResult（可选 DiagnosticsReport／概算表／布置数据）
        → ReportAST 章节树。NumberLine 在此绑定「数字+单位+公式 ID」——
        锚定值一律取自 plant.trace 同公式的实跑输出（等值绑定，禁造数）。
        块类型族与纯投影辅助自 blocks.py 迁入（预算拆分——零行为变化，
        本文件再导出保既有 import 面不变）。
禁区:   禁 import server／fastmcp／core L1-L3（只许 waterprint.app 正门与
        waterprint.contracts.*）；禁 IO——纯函数装配，不读不写文件。
参照:   v2 设计书 D5①／D5③／D5④；AI1-INTEG-2026-09-13 §3 预裁决①。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from waterprint.app import discover_units
from waterprint.contracts.manifest import UnitManifest
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.result_schema import PlantResult, UnitResultSnapshot
from waterprint.contracts.trust import DiagnosticsReport

from waterprint_agent.report.blocks import (
    DESIGN_KEY,
    Block,
    Chapter,
    EstimateRowLike,
    EstimateSheetLike,
    FigureRef,
    NarrativeSlot,
    NoteLine,
    NumberLine,
    ReportAST,
    Section,
    TableBlock,
    anchor_index,
    condition_label,
    dim_label_unit,
    indicator_of,
    ordered_dim_fields,
    ordered_units,
    unit_zh,
)

__all__ = [
    "Chapter",
    "EstimateRowLike",
    "EstimateSheetLike",
    "FigureRef",
    "InvalidReportError",
    "NarrativeSlot",
    "NoteLine",
    "NumberLine",
    "ReportAST",
    "Section",
    "TableBlock",
    "build_report_ast",
]

# 进水／内置节点 id（第 2 章承接，不入第 4 章逐单元——blocks 同源声明）
_INLET_ID = "inlet"

# 污泥线前缀（第 3 章泥线表分组依据——blocks 同源声明）
_SLUDGE_PREFIX = "sludge_"


class InvalidReportError(Exception):
    """说明书装配非法（缺设计工况结果等）——GR-11 族（领域异常）。"""


def _chapter_design_basis(project: ProjectFile, plant: PlantResult) -> Chapter:
    """第 1 章 设计依据：项目标识表＋规范依据表（trace 条文去重）。"""
    identity_rows = (
        ("设计内容哈希（content_hash）", project.metadata.content_hash),
        ("引擎版本（engine_version）", plant.repro.engine_version),
        ("数据版本（data_version）", plant.repro.data_version),
        ("项目文件格式版本（format_version）", project.format_version),
        ("工艺单元数", str(len(project.design.nodes))),
        ("单元连接数", str(len(project.design.edges))),
    )
    norm_refs = sorted({node.norm_ref for node in plant.trace})
    norm_rows = tuple(
        (f"依据 {index}", ref) for index, ref in enumerate(norm_refs, start=1)
    )
    blocks: tuple[Block, ...] = (
        TableBlock(
            title="项目标识与版本三元组",
            headers=("项目", "值"),
            rows=identity_rows,
        ),
        TableBlock(
            title="规范与条文依据（全部公式出处去重）",
            headers=("序号", "条文出处"),
            rows=norm_rows,
        ),
        NoteLine(
            "本章全部数据由程序自项目 metadata 与计算迹（trace）条文自动"
            "汇编——数值溯源原则下，设计依据与结果数值同源可溯。"
        ),
    )
    return Chapter(id="design_basis", title="设计依据", blocks=blocks)


def _chapter_flow_quality(
    plant: PlantResult, diagnostics: DiagnosticsReport | None
) -> Chapter:
    """第 2 章 设计水量水质：进水流量／水质程序填表＋工况表＋达标校核。"""
    snapshot = plant.conditions[DESIGN_KEY]
    blocks: list[Block] = []
    inlet = snapshot.get(_INLET_ID)
    if inlet is None:
        blocks.append(
            NoteLine("结果中无进水节点快照——水量水质表数据待补（结构缺陷）。")
        )
    else:
        flow_row_list = [
            ("平均日流量 q_avg_daily（m3/s）",
                 str(inlet.outflows.get(f"{_INLET_ID}.out.q_avg_daily", ""))),
                ("总变化系数 kz（无量纲）",
                 str(inlet.outflows.get(f"{_INLET_ID}.out.kz", ""))),
            ("设计流量 q_design（m3/s，最高日最高时）",
             str(inlet.outflows.get(f"{_INLET_ID}.out.q_design", ""))),
        ]
        flow_rows = tuple(flow_row_list)
        quality_rows = tuple(
            (indicator_of(key, _INLET_ID), str(inlet.outqualities[key]))
            for key in sorted(inlet.outqualities)
        )
        blocks.extend(
            (
                TableBlock(title="设计流量", headers=("项目", "值"), rows=flow_rows),
                TableBlock(
                    title="进水水质（design 工况，mg/L）",
                    headers=("指标", "进水值"),
                    rows=quality_rows,
                ),
            )
        )
    condition_rows = tuple(
        (key, condition_label(key)) for key in plant.conditions
    )
    blocks.append(
        TableBlock(
            title="计算工况集（2+k 线性——ADR-007）",
            headers=("工况键", "工程语义"),
            rows=condition_rows,
        )
    )
    if diagnostics is None:
        blocks.append(NoteLine("出水达标校核：数据待接线（诊断随计算批产出）。"))
    else:
        margins = [
            item for item in diagnostics.effluent if item.condition_key == DESIGN_KEY
        ]
        if margins:
            blocks.append(
                TableBlock(
                    title="出水达标校核（design 工况，mg/L）",
                    headers=("指标", "结果值", "限值", "裕度"),
                    rows=tuple(
                        (item.indicator, str(item.value), str(item.limit),
                         str(item.margin))
                        for item in margins
                    ),
                )
            )
        else:
            blocks.append(
                NoteLine("出水达标校核：诊断未含 design 工况裕度（标准未绑定）。")
            )
    return Chapter(id="flow_quality", title="设计水量水质", blocks=tuple(blocks))


def _chapter_process_selection(
    project: ProjectFile, plant: PlantResult
) -> Chapter:
    """第 3 章 工艺流程比选：程序注入主线／泥线结论表＋AI 论证槽（N3）。"""
    snapshot = plant.conditions[DESIGN_KEY]
    ordered = ordered_units(project, snapshot)
    water_line = [
        uid for uid in ordered
        if uid != _INLET_ID and not uid.startswith(_SLUDGE_PREFIX)
    ]
    sludge_line = [uid for uid in ordered if uid.startswith(_SLUDGE_PREFIX)]
    water_rows = tuple(
        (str(no), unit_zh(uid), uid) for no, uid in enumerate(water_line, start=1)
    )
    sludge_rows = tuple(
        (str(no), unit_zh(uid), uid) for no, uid in enumerate(sludge_line, start=1)
    )
    blocks: tuple[Block, ...] = (
        TableBlock(
            title="采用方案——水线主工序（程序注入结论）",
            headers=("序号", "构筑物", "单元标识"),
            rows=water_rows,
        ),
        TableBlock(
            title="采用方案——污泥线工序（程序注入结论）",
            headers=("序号", "构筑物", "单元标识"),
            rows=sludge_rows,
        ),
        NarrativeSlot(
            slot_id="process_selection",
            hint="只承接上表已注入的工序结论展开论证（比选理由／规范依据），"
            "正文禁新增任何数字——支撑数值由程序给，不由叙述写。",
        ),
    )
    return Chapter(id="process_selection", title="工艺流程比选", blocks=blocks)


def _unit_section(
    unit_id: str,
    snap: UnitResultSnapshot,
    manifest: UnitManifest | None,
    anchors: Mapping[str, Mapping[float, str]],
) -> Section:
    """第 4 章单单元小节：dims 锚定行＋出水水质表＋公式集注记。"""
    unit_anchors = anchors.get(unit_id, {})
    lines: list[NumberLine] = []
    for field in ordered_dim_fields(snap.dims, manifest):
        label, unit = dim_label_unit(field, manifest)
        value = snap.dims[field]
        lines.append(
            NumberLine(
                label=label,
                value=value,
                unit=unit,
                formula_id=unit_anchors.get(round(value, 10), ""),
            )
        )
    blocks: list[Block] = [NoteLine(f"设计工况（{DESIGN_KEY}）主要尺寸与负荷：")]
    blocks.extend(lines)
    quality_rows = tuple(
        (indicator_of(key, unit_id), str(snap.outqualities[key]))
        for key in sorted(snap.outqualities)
    )
    if quality_rows:
        blocks.append(
            TableBlock(
                title=f"出水水质（{DESIGN_KEY} 工况，mg/L）",
                headers=("指标", "出水值"),
                rows=quality_rows,
            )
        )
    if snap.formula_ids:
        blocks.append(
            NoteLine(
                f"本单元公式集：{'、'.join(snap.formula_ids)}（详见溯源索引与审计附件）。"
            )
        )
    return Section(title=f"{unit_zh(unit_id)}（{unit_id}）", blocks=tuple(blocks))


def _chapter_unit_calc(
    project: ProjectFile,
    plant: PlantResult,
    manifests: Mapping[str, tuple[UnitManifest, Any]],
) -> Chapter:
    """第 4 章 构筑物逐单元计算：NumberLine 主体（全部可锚者挂公式 ID）。"""
    snapshot = plant.conditions[DESIGN_KEY]
    anchors = anchor_index(plant)
    sections = tuple(
        _unit_section(
            unit_id,
            snapshot[unit_id],
            manifests[unit_id][0] if unit_id in manifests else None,
            anchors,
        )
        for unit_id in ordered_units(project, snapshot)
        if unit_id != _INLET_ID
    )
    return Chapter(id="unit_calc", title="构筑物逐单元计算", blocks=sections)


def _chapter_layout(
    diagnostics: DiagnosticsReport | None, layout: Mapping[str, Any] | None
) -> Chapter:
    """第 5 章 平面与高程布置：AI 叙述槽＋水力闭合校核＋布置数据块。"""
    blocks: list[Block] = [
        NarrativeSlot(
            slot_id="layout_narrative",
            hint="围绕程序注入的高程与闭合结论论述布置原则（流程顺畅／"
            "近远期结合／检修条件），正文禁新增任何数字。",
        )
    ]
    if diagnostics is None:
        blocks.append(NoteLine("水力闭合校核：数据待接线（诊断随计算批产出）。"))
    else:
        closure_rows = tuple(
            (
                closure.condition_key,
                line.fluid,
                str(line.q_sources_total),
                str(line.q_sinks_total),
                str(line.closure_rel),
            )
            for closure in diagnostics.mass_balance
            for line in closure.lines
        )
        blocks.append(
            TableBlock(
                title="水力闭合校核（源汇两侧合计与相对闭合）",
                headers=("工况", "流体", "源侧合计（m3/s）", "汇侧合计（m3/s）", "相对闭合"),
                rows=closure_rows,
            )
        )
        if diagnostics.convergence:
            blocks.append(
                TableBlock(
                    title="回路收敛统计",
                    headers=("工况", "回路单元", "迭代次数", "末步残差"),
                    rows=tuple(
                        (
                            stat.condition_key,
                            "、".join(stat.loop_nodes),
                            str(stat.iterations),
                            str(stat.final_residual),
                        )
                        for stat in diagnostics.convergence
                    ),
                )
            )
        else:
            blocks.append(NoteLine("回路收敛：本图无回路迭代（convergence 空）。"))
    if layout is None:
        blocks.append(
            NoteLine("高程与场景布置数据：数据待接线（wp_get_layout_summary 批）。")
        )
    else:
        blocks.append(
            TableBlock(
                title="布置数据块（layout 聚合投影）",
                headers=("键", "值"),
                rows=tuple((str(key), str(value)) for key, value in layout.items()),
            )
        )
    return Chapter(id="layout", title="平面与高程布置", blocks=tuple(blocks))


def _chapter_estimate(estimate: EstimateSheetLike | None) -> Chapter:
    """第 6 章 工程概算：概算明细＋汇总表（None →「数据待接线」占位）。"""
    if estimate is None:
        blocks: tuple[Block, ...] = (
            TableBlock(
                title="工程概算（数据待接线）",
                headers=("项", "值"),
                rows=(("工程概算", "数据待接线（wp_get_estimate_summary 批）"),),
            ),
        )
    else:
        detail_rows = tuple(
            (
                str(no),
                row.name_zh or row.price_key,
                row.unit,
                str(row.quantity),
                str(row.unit_price),
                str(row.amount),
            )
            for no, row in enumerate(estimate.detail_rows, start=1)
        )
        blocks = (
            TableBlock(
                title="概算明细（分部分项）",
                headers=("序号", "项目", "单位", "数量", "单价", "合价"),
                rows=detail_rows,
            ),
            TableBlock(
                title="概算汇总",
                headers=("项", "值"),
                rows=(
                    ("分部分项小计", str(estimate.subtotal)),
                    ("工程总投资（含预备费与税金）", str(estimate.grand_total)),
                ),
            ),
        )
    return Chapter(id="estimate", title="工程概算", blocks=blocks)


def _chapter_drawings(plant: PlantResult) -> Chapter:
    """第 7 章 附图：DXF 产物引用＋审计附件 A（D5④——同批产出）。"""
    blocks: tuple[Block, ...] = (
        FigureRef(name="plant_layout.dxf", caption="全厂平面布置图"),
        FigureRef(name="hydraulic_profile.dxf", caption="水力高程流程图"),
        FigureRef(
            name=f"audit-{plant.repro.design_hash[:8]}.html",
            caption="附件 A 公式溯源审计报告（逐条公式／条文／输入值）",
        ),
        NoteLine(
            "附图与附件随导出批（wp_export_dxf／wp_export_audit）同批产出，"
            "文件名带设计摘要串（design_digest）——以导出清单为准。"
        ),
    )
    return Chapter(id="drawings", title="附图", blocks=blocks)


def build_report_ast(
    project: ProjectFile,
    plant: PlantResult,
    *,
    diagnostics: DiagnosticsReport | None = None,
    estimate: EstimateSheetLike | None = None,
    layout: Mapping[str, Any] | None = None,
) -> ReportAST:
    """两段式管线第一段：七章节 AST 装配（纯函数，无 IO）。

    章节与数据源映射（D5① 真源）：1 设计依据＝metadata＋trace 条文／
    2 设计水量水质＝进水快照＋工况＋裕度／3 工艺流程比选＝工序结论表
    ＋AI 槽／4 构筑物逐单元计算＝dims 锚定行（NumberLine 主体）／
    5 平面与高程布置＝AI 槽＋水力闭合＋布置块／6 工程概算＝概算表／
    7 附图＝产物引用。diagnostics／estimate／layout 允许 None（集成批
    接线，渲染层留「数据待接线」占位）。
    """
    if DESIGN_KEY not in plant.conditions:
        raise InvalidReportError(
            f"结果缺设计工况快照：{DESIGN_KEY!r}（说明书以 design 档为准——D5①）"
        )
    manifests = discover_units()
    return (
        _chapter_design_basis(project, plant),
        _chapter_flow_quality(plant, diagnostics),
        _chapter_process_selection(project, plant),
        _chapter_unit_calc(project, plant, manifests),
        _chapter_layout(diagnostics, layout),
        _chapter_estimate(estimate),
        _chapter_drawings(plant),
    )
