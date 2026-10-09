"""报告服务用例：最近完成结果集 → 计算说明书 Markdown+章节索引（verify 全绿才返）。

输入:  ServiceContext + 项目 id + condition_key（缺省 design）
输出:  ReportResponse（markdown+sections 两级索引+stale/design_hash 回显）
       +assemble_report（exports report_pdf 路共享装配正门——B6 §二.⑥）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 计算说明批 2026-10-09 任务书 §二.④——装配序参照 agent
#   #21 _export_report_impl；镜像测试 server/tests/routers/test_report.py
#   +tests/services/test_report.py）
#
# 【公开接口】
#   build_report(ctx, project_id, condition_key) -> ReportResponse
#       （报告数据通道服务面正门——GET /api/calc/projects/{pid}/report）
#   assemble_report(ctx, project_id, condition_key) -> AssembledReport
#       （装配正门：AST+markdown+verify 全绿——exports report_pdf 路
#       共享消费，两产物同一装配真源）
#   ReportResponse/ReportSectionModel/ReportGeneratedFromModel（响应
#       模型面——routers response_model 直用，unit_detail 先例：禁协议
#       层重复声明漂移面）
#   ReportSourceNotFoundError/ReportEntryNotFoundError（404 两面：源
#       不可得 / 工况不在——文案区分，unit_detail 惯例）
#   ReportVerifyError（500 面——verify 未全绿禁出件，显式消息禁静默）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：latest_calc_result 共享件（unit_detail
#      同制零重算）；项目不存在=ProjectNotFoundError（404）；无结果集/
#      结果文件损坏=ReportSourceNotFoundError（404，消息含 /api/calc/run
#      引导）。
#   R2 装配（agent #21 同序）：diag（latest.diag_file——trust R2 降级面
#      同款：缺失/损坏→None 显式降级禁伪造）→cost（services.cost 同
#      通道：EstimateSheetModel 结构满足 EstimateSheetLike 协议——
#      name_zh 单一真源）→layout（elevation+scene 服务聚合→压缩投影行，
#      agent _report_layout_rows 同源）→core build_report_ast
#      （narrative_fills 缺省 None 占位形态——AI 撰稿回填不在本批）。
#   R3 出件闸：render_markdown+verify_report 全绿才返（§五值锚定纪律
#      ——未全绿=ReportVerifyError 显式消息，md/PDF 两产物同一闸）。
#   R4 sections：AST 章+Section 两级投影（章 level=1/unit_calc 单元
#      小节 level=2——前端导航数据源；id=章 id/「{章 id}-{小节序}」
#      确定性，渲染前置产出零额外取数）。
#   R5 新鲜度：stale=result_is_stale（design_hash≠当前 digest——
#      unit_detail/compare 同口径显式回显禁静默）；design_hash=结果件
#      repro 真源；generated_from.digest10=design_hash 前 10 位
#      （exports _DIGEST_PREFIX 同口径）。
#
# 【测试要求】routers/test_report.py 五用例（契约三面+stale 流转+
#   markdown 数学块）+services/test_report.py（sections 投影纯函数）。
#
# 【参照】B6 任务书 §二.④；services/unit_detail.py（取数母本）；
#   agent tools/exports.py _export_report_impl（装配序形源）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.result_schema import (
    InvalidResultError,
    deserialize,
)
from waterprint.contracts.trust import (
    DiagnosticsReport,
    InvalidDiagnosticsError,
    deserialize_diag,
)
from waterprint.report import (
    CheckReport,
    ReportAST,
    Section,
    build_report_ast,
    render_markdown,
    verify_report,
)

from waterprint_server.services import ServiceContext
from waterprint_server.services import cost as cost_service
from waterprint_server.services import elevation as elevation_service
from waterprint_server.services import scene as scene_service
from waterprint_server.services._shared.latest_calc import latest_calc_result
from waterprint_server.services.projects import read_project, result_is_stale

__all__ = [
    "AssembledReport",
    "ReportEntryNotFoundError",
    "ReportGeneratedFromModel",
    "ReportResponse",
    "ReportSectionModel",
    "ReportSourceNotFoundError",
    "ReportVerifyError",
    "assemble_report",
    "build_report",
]

_DESIGN_KEY = "design"
# 摘要前缀长度（exports_support._DIGEST_PREFIX 同款口径——白名单字面量 10）
_DIGEST_PREFIX = 10
# verify 失败明细入消息条数上限（白名单字面量 2——首两样即诊断面）
_VERIFY_SAMPLE = 2


class ReportSourceNotFoundError(Exception):
    """报告源不可得（项目无结果集/结果文件损坏）——404 面。"""


class ReportEntryNotFoundError(Exception):
    """报告目标不在（工况缺席结果集）——404 面（文案区分）。"""


class ReportVerifyError(RuntimeError):
    """说明书数值锚定断言未全绿（禁出件）——500 面（服务端数据完整性）。"""


class ReportSectionModel(BaseModel):
    """章节索引条目（R4）：id 确定性+两级 level（1=章/2=unit_calc 小节）。"""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    level: int


class ReportGeneratedFromModel(BaseModel):
    """生成来源摘要（R5）：digest10=结果件 design_hash 前 10 位。"""

    model_config = ConfigDict(frozen=True)

    digest10: str


class ReportResponse(BaseModel):
    """计算说明书报告响应（R1~R5——markdown 含 $$ 数学块与公式溯源附录）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    condition_key: str
    stale: bool
    design_hash: str
    markdown: str
    sections: tuple[ReportSectionModel, ...]
    generated_from: ReportGeneratedFromModel


@dataclass(frozen=True)
class AssembledReport:
    """装配产物束（md/PDF 两产物共享：AST+markdown+verify 报告+新鲜度面）。"""

    condition_key: str
    stale: bool
    design_hash: str
    ast: ReportAST
    markdown: str
    check: CheckReport


def _load_diagnostics(latest: Mapping[str, Any]) -> DiagnosticsReport | None:
    """诊断件读取（R2——trust._load_diagnostics 同款降级面）。

    缺键/缺文件/损坏 → None 显式降级（说明书第 2/5 章呈现「数据待接线」
    占位——禁伪造空诊断冒充，ADR-012 R1 同口径）。
    """
    diag_file = latest.get("diag_file")
    if not isinstance(diag_file, str) or not diag_file:
        return None
    try:
        return deserialize_diag(Path(diag_file).read_bytes())
    except (OSError, InvalidDiagnosticsError):
        return None


def _layout_rows(elevation: Any, scene: Any) -> dict[str, Any]:
    """布置数据块行（R2——elevation+scene 服务聚合压缩投影，agent #16 同源）。"""
    stations = elevation.stations
    pumps = elevation.pump_stations
    return {
        "高程工况": elevation.condition_key,
        "基准面注记": elevation.datum_note,
        "纵断站位数": len(stations),
        "首站水面标高（m）": stations[0].water_level if stations else None,
        "末站水面标高（m）": stations[-1].water_level if stations else None,
        "最大埋深（m）": max((s.bury_depth for s in stations), default=None),
        "提升泵站": "、".join(p.unit_id for p in pumps) or "全程自流",
        "场景节点数": len(scene.nodes),
    }


def _sections_of(ast: ReportAST) -> tuple[ReportSectionModel, ...]:
    """章节两级投影（R4）：章 level=1（附录章在内）+Section level=2。

    id 确定性：章=chapter.id；小节=「{chapter.id}-{章内小节序}」（渲染
    前置产出——AST 序即投影序，零额外取数零时钟）。
    """
    out: list[ReportSectionModel] = []
    for chapter in ast:
        out.append(ReportSectionModel(id=chapter.id, title=chapter.title, level=1))
        section_no = 0
        for block in chapter.blocks:
            if isinstance(block, Section):
                section_no += 1
                out.append(
                    ReportSectionModel(
                        id=f"{chapter.id}-{section_no}",
                        title=block.title,
                        level=2,
                    )
                )
    return tuple(out)


def assemble_report(
    ctx: ServiceContext, project_id: str, condition_key: str | None
) -> AssembledReport:
    """装配正门（R1~R3）：取数 →diag/cost/layout 装配 →render+verify 全绿。"""
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    _, latest = latest_calc_result(ctx, project_id, not_found=ReportSourceNotFoundError)
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        raise ReportSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    chosen = condition_key if condition_key is not None else _DESIGN_KEY
    if chosen not in plant.conditions:
        raise ReportEntryNotFoundError(
            f"工况 {chosen!r} 不在结果集（合法 {sorted(plant.conditions)}）"
        )
    diagnostics = _load_diagnostics(latest)
    cost = cost_service.build_cost_for_project(ctx, project_id, chosen)
    elevation = elevation_service.build_elevation_for_project(ctx, project_id, chosen)
    scene = scene_service.build_scene_for_project(ctx, project_id, chosen)
    ast = build_report_ast(
        project,
        plant,
        diagnostics=diagnostics,
        estimate=cost.sheet,
        layout=_layout_rows(elevation, scene),
    )
    markdown = render_markdown(ast)  # narrative_fills 缺省 None（占位形态）
    check = verify_report(markdown, plant)
    if not check.ok:
        sample = "；".join(check.failures[:_VERIFY_SAMPLE])
        raise ReportVerifyError(
            f"项目 {project_id!r} 说明书数值锚定断言未全绿（禁出件）："
            f"{len(check.failures)} 项失败——首两样 {sample}"
        )
    return AssembledReport(
        condition_key=chosen,
        stale=result_is_stale(latest, project),
        design_hash=plant.repro.design_hash,
        ast=ast,
        markdown=markdown,
        check=check,
    )


def build_report(
    ctx: ServiceContext, project_id: str, condition_key: str | None
) -> ReportResponse:
    """报告数据通道正门（R1~R5）：装配 →markdown+sections 两级索引投影。"""
    assembled = assemble_report(ctx, project_id, condition_key)
    return ReportResponse(
        project_id=project_id,
        condition_key=assembled.condition_key,
        stale=assembled.stale,
        design_hash=assembled.design_hash,
        markdown=assembled.markdown,
        sections=_sections_of(assembled.ast),
        generated_from=ReportGeneratedFromModel(
            digest10=assembled.design_hash[:_DIGEST_PREFIX]
        ),
    )
