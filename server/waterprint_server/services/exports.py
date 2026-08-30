"""导出服务用例：计算书/图纸/概算/审计的产物编排（stale 守门）。

输入:  项目 id + 导出 kind + condition_key + 选项
输出:  产物文件路径与元数据（含三元组摘要）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 server/tests/services/test_exports.py）
#
# 【公开接口】
#   create_export(project_id, kind, condition_key, options,
#                 force=False) -> ExportHandle
#   list_exports(project_id) -> tuple[ExportMeta, ...]
#
# 【行为规格】
#   R1 stale 守门（§17.1 导出行）：最近结果集三元组 vs 当前项目
#      hash 不一致且未 force → 拒绝（上游 409）；force 导出的产物
#      文件名与元数据显式标注旧三元组（产物永不冒充）。本条"消费时
#      实时比对"是全库 stale 守门统一口径（SENS-B 2026-08-23
#      UF-37——calc 侧"完成时对比"仅作 UI 提示性标记）。
#   R2 产物编排：渲染编排经 waterprint.app 对应用例（export_artifact：
#      kind→calcbook/audit/dxf/estimate，SENS-B 2026-08-23 UF-33，
#      不直连 core 各渲染器）产出写入 exports_dir；落盘一律临时文件+
#      同分区 rename 原子写（GR-38，SENS-B 2026-08-23 UF-38）；产物
#      注册表（列表查询）只记元数据不复制数据。
#   R3 批量导出走低优先级队列（§17.1）；单产物即时生成上限（超过
#      阈值转任务，防同步请求超时）。
#   R4 文件名确定性：项目 id + kind + condition + 三元组摘要
#      （禁止当前时钟——同名同输入即同文件，幂等重导出覆盖校验）。
#
# 【实现注记（SERVER 2026-08-26）】
#   - 单产物即时上限=1（>1 项即转 export_batch 任务，R3 v1 阈值）。
#   - 摘要=design digest 前 10 位（白名单字面量）；engine/data 版本
#     进 .meta.json 边车（注册表只记元数据不复制数据，R2）。
#   - 模板缺位=ExportTemplateMissingError（501 面，UF-16 模板录入批
#     挂账：data/templates 0.0.0 无模板文件——诚实未就绪）。
#   - R1-1（AU-1 修复 2026-08-26）：文件名四分量全过白名单
#     （condition/items kind/project_id=validate_component 或 _KINDS；
#     digest=hex 天然安全）——穿越串 422 拒于落盘之前；worker 侧
#     二道闸（kind 白名单+out_name 无分隔符无 ..）随行。
#   - FE1 M4（ENG3 2026-08-28）：即时生成路径 deserialize 结果文件
#     缺失/损坏（OSError/InvalidResultError）归一 ExportSourceNotFound
#     Error 404 面（scene.py 同构——路径安全族裸 500 禁）。
#   - FE9 D2/D3/D4（2026-08-30 drawings 图纸面板批）：
#     D2 模板闸收窄——存在性闸仅对模板消费 kind（calcbook，_TEMPLATE_
#     KINDS）执行；dxf/audit/estimate 返回名义路径不闸（core 链零模板
#     消费：dxf 走 write_dxf 内建 styles.base_styles，audit/estimate 在
#     core owners 表 NotReady 分派前不打开模板）。历史三 kind 死于
#     server 模板闸未达 core 正门 501 语义面（探针实录 2026-08-30）；
#     禁造 dxf_unit.xlsx 占位模板（core 不消费=死资产，违诚实原则）。
#     D3 options 透传（单产物路径）——core 调用附 unit_id/condition_key
#     kwargs（core _EXPORT_OPTIONS 同款键集）；空串归一 None：
#     condition_key None→core 缺省 design 档+UserWarning；unit_id
#     None→core NotReady「全厂总图归 M5 site_plan」诚实 501。批量路径
#     （items>1 转 export_batch 任务）不透传——worker options 透传挂账
#     S2 落盘化批同域（前端 v1 只发单图请求）。
#     D4 kind 后缀映射——_deterministic_name 恒 .xlsx 收敛为按 kind
#     映射（_KIND_SUFFIXES）：dxf→.dxf。既有 calcbook 命名零漂移
#     （dxf 历史从未成功导出——恒 501，无存量文件名面）。
#
# 【测试要求】stale 拒绝与 force 标注、确定性命名、批量转任务。
#
# 【参照】重写计划 §17.1/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from waterprint import app as core
from waterprint.contracts.result_schema import InvalidResultError, deserialize

from waterprint_server.jobs.manager import TaskRequest
from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import design_digest, read_project
from waterprint_server.settings import validate_component

_KINDS: Final[tuple[str, ...]] = ("calcbook", "audit", "dxf", "estimate")
_DIGEST_PREFIX: Final[int] = 10  # 文件名摘要长度（白名单字面量；注记区）
_IMMEDIATE_LIMIT: Final[int] = 1  # 单产物即时上限（R3 v1：超过即转任务）
# FE9 D2：模板消费 kind 面（唯一）——存在性闸只对 calcbook 执行（core
# calcbook 分支真读模板；dxf/audit/estimate core 链零模板消费——注记区）。
_TEMPLATE_KINDS: Final[frozenset[str]] = frozenset({"calcbook"})
# FE9 D4：kind→产物后缀映射（dxf→.dxf；其余 Excel 族恒 .xlsx 零漂移）。
_KIND_SUFFIXES: Final[Mapping[str, str]] = MappingProxyType(
    {"calcbook": ".xlsx", "audit": ".xlsx", "dxf": ".dxf", "estimate": ".xlsx"}
)


class StaleExportError(RuntimeError):
    """结果集三元组过期且未 force（§17.1 导出行）——409 面附输入版本。"""

    def __init__(self, result_digest: str, current_digest: str) -> None:
        super().__init__(
            f"最近结果集基于 design {result_digest[:_DIGEST_PREFIX]}…，当前项目"
            f" design {current_digest[:_DIGEST_PREFIX]}…（输入版本不一致——"
            "禁止静默导出旧结果冒充新结果；?force=1 显式导出旧结果（产物"
            "与元数据将标注旧三元组）或先重算）"
        )
        self.result_digest = result_digest
        self.current_digest = current_digest


class ExportSourceNotFoundError(RuntimeError):
    """无最近完成结果集可消费——404 面（先运行计算）。"""


class ExportTemplateMissingError(RuntimeError):
    """导出模板未就绪（UF-16 data/templates 录入批）——501 面。"""


class InvalidExportRequestError(ValueError):
    """导出请求非法（kind 白名单外）——422 面。"""


@dataclass(frozen=True)
class ExportHandle:
    """导出产物句柄（R4：确定性命名；stale_labeled=force 旧三元组标注）。"""

    project_id: str
    kind: str
    condition_key: str
    path: str
    design_digest: str
    stale_labeled: bool
    task_id: str | None  # 批量转任务时非 None（R3）


@dataclass(frozen=True)
class ExportMeta:
    """产物注册表条目（R2：只记元数据不复制数据；无时钟字段）。"""

    project_id: str
    kind: str
    condition_key: str
    file_name: str
    design_digest: str
    engine_version: str
    data_version: str
    stale_labeled: bool


def _template_for(ctx: ServiceContext, kind: str) -> Path:
    """模板解析（data/templates；缺位=诚实未就绪，UF-16）。

    FE9 D2 收窄：存在性闸仅对 _TEMPLATE_KINDS（calcbook）执行——
    dxf/audit/estimate 返回名义路径不闸（core 链零模板消费，注记区；
    闸在其后的 core 正门：dxf 分派真出图/audit·estimate NotReady）。
    """
    template = ctx.templates_dir / f"{kind}_unit.xlsx"
    if kind in _TEMPLATE_KINDS and not template.is_file():
        raise ExportTemplateMissingError(
            f"导出模板未就绪：{template} 不存在（UF-16——模板归 "
            "data/templates 录入批；禁静默空产物）"
        )
    return template


def _latest_calc_result(
    ctx: ServiceContext, project_id: str
) -> Mapping[str, Any]:
    """最近完成计算结果集（注册序最末 done calc——消费时实时取，UF-37）。

    ENG4 D2（M-8）：原返回 (latest_id, latest) 二元组——首元 task_id 无
    任何消费面（唯一调用方 create_export 弃置），纯重构收敛为单值
    （scene/elevation/cost 三服务同款签名，零行为变化）。
    """
    latest: Mapping[str, Any] | None = None
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(task_id)
        if status.kind == "calc" and status.state == "done" and status.result:
            latest = status.result
    if latest is None:
        raise ExportSourceNotFoundError(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return latest


def _name_component(value: str, fallback: str, what: str) -> str:
    """R1-1（AU-1 修复 2026-08-26）：文件名分量白名单（空串→fallback）。

    condition_key/items condition 等用户可写字段过 validate_component
    （与 safe_child 同源字符集）；越界 raise InvalidExportRequestError
    （422 面）——穿越串（../与分隔符注入）拒于落盘之前，§18 路径安全。
    """
    if not value:
        return fallback
    try:
        return validate_component(value)
    except ValueError as exc:
        raise InvalidExportRequestError(
            f"导出文件名分量 {what} 非法：{value!r}（§18 路径安全——白名单"
            "字符集[ASCII 字母数字-_/]，拒绝 ../与分隔符注入；R1-1）"
        ) from exc


def _deterministic_name(
    project_id: str, kind: str, condition_key: str, digest: str
) -> str:
    """R4 确定性命名：项目 id+kind+condition+三元组摘要（禁当前时钟）。

    R1-1：全部四分量过白名单（project_id/condition=validate_component、
    kind∈_KINDS、digest=sha256 hex 天然安全）——穿越即拒（422）。
    FE9 D4：后缀按 kind 映射（_KIND_SUFFIXES——dxf→.dxf；历史恒 .xlsx
    对 dxf 产物名不诚实的缺陷收口，calcbook 零漂移）。
    """
    if kind not in _KINDS:
        raise InvalidExportRequestError(f"导出 kind {kind!r} 不在合法面 {_KINDS}")
    safe_project = _name_component(project_id, "REQUIRED", "project_id")
    safe_condition = _name_component(condition_key, "all", "condition_key")
    return (
        f"{safe_project}-{kind}-{safe_condition}"
        f"-{digest[:_DIGEST_PREFIX]}{_KIND_SUFFIXES[kind]}"
    )


def _write_meta(ctx: ServiceContext, meta: ExportMeta) -> None:
    """注册表边车（原子写；只记元数据不复制数据，R2）。"""
    sidecar = ctx.exports_dir / f"{meta.file_name}.meta.json"
    tmp = sidecar.with_name(sidecar.name + ".tmp")
    tmp.write_text(
        json.dumps(meta.__dict__, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp, sidecar)


async def create_export(  # noqa: PLR0913  # 规格冻结五参签名（公开接口）+ctx 首参惯例
    ctx: ServiceContext,
    project_id: str,
    kind: str,
    condition_key: str = "",
    options: Mapping[str, Any] | None = None,
    *,
    force: bool = False,
) -> ExportHandle:
    """产物编排正门（R1 守门→R2 渲染→R3 批量转任务→R4 确定性命名）。"""
    if kind not in _KINDS:
        raise InvalidExportRequestError(f"导出 kind {kind!r} 不在合法面 {_KINDS}")
    chosen = dict(options or {})
    items: Sequence[Mapping[str, Any]] = chosen.get("items") or [
        {"kind": kind, "condition_key": condition_key}
    ]
    latest = _latest_calc_result(ctx, project_id)
    result_digest = str(latest.get("design_hash", ""))
    current_digest = design_digest(read_project(ctx, project_id).design)
    stale = result_digest != current_digest
    if stale and not force:
        raise StaleExportError(result_digest, current_digest)
    template = str(_template_for(ctx, kind))
    names = [
        _deterministic_name(
            project_id,
            str(item.get("kind", "")),  # 缺 kind=白名单外→422（禁 KeyError 500）
            str(item.get("condition_key", "")),
            result_digest,
        )
        for item in items
    ]
    if len(items) > _IMMEDIATE_LIMIT:  # R3：超单产物上限转低优先级任务
        handle = await ctx.manager.submit(
            TaskRequest(
                kind="export_batch",
                priority=ctx.settings.task_queue_priorities["export_batch"],
                payload={
                    "kind": "export_batch",
                    "project_id": project_id,
                    "exports_dir": str(ctx.exports_dir),
                    "items": [
                        {
                            "kind": item["kind"],
                            "result_file": latest.get("result_file"),
                            "template": template,
                            "out_name": name,
                        }
                        for item, name in zip(items, names, strict=True)
                    ],
                },
            ),
        )
        return ExportHandle(
            project_id=project_id,
            kind=kind,
            condition_key=condition_key,
            path=str(ctx.exports_dir / names[0]),
            design_digest=result_digest,
            stale_labeled=stale and force,
            task_id=handle.task_id,
        )
    # 单产物即时生成（同步经 app.export_artifact；临时文件+rename 原子写）

    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        # FE1 M4（路径安全族）：结果文件缺失/损坏归一 404 领域面——裸 500
        # 禁（scene.py 同构收口；worker 侧 export_batch 不读盘不在本面）。
        raise ExportSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    out = ctx.exports_dir / names[0]
    tmp = out.with_name(out.name + ".tmp")
    # FE9 D3：options 透传（单产物路径——core _EXPORT_OPTIONS 同款键集；
    # 空串归一 None：unit_id None→core NotReady 全厂总图 501 诚实面、
    # condition_key None→core 缺省 design 档+UserWarning。批量路径不透传
    # ——worker 面挂账 S2 落盘化批，注记区）。
    options_unit = chosen.get("unit_id")
    core.export_artifact(
        kind,
        plant,
        Path(template),
        tmp,
        unit_id=str(options_unit) if options_unit else None,
        condition_key=condition_key or None,
    )
    os.replace(tmp, out)
    meta = ExportMeta(
        project_id=project_id,
        kind=kind,
        condition_key=condition_key,
        file_name=names[0],
        design_digest=result_digest,
        engine_version=str(latest.get("engine_version", "")),
        data_version=str(latest.get("data_version", "")),
        stale_labeled=stale and force,
    )
    _write_meta(ctx, meta)
    return ExportHandle(
        project_id=project_id,
        kind=kind,
        condition_key=condition_key,
        path=str(out),
        design_digest=result_digest,
        stale_labeled=stale and force,
        task_id=None,
    )


def list_exports(ctx: ServiceContext, project_id: str) -> tuple[ExportMeta, ...]:
    """产物列表（注册表=元数据边车扫描；无独立索引库语义同 projects R4）。

    ENG4 D3（I-5）注记：project_id 缺省=空串→raw.get("project_id") == ""
    恒不匹配→恒 []（无「列出全部」语义——前端无消费面，语义裁决挂 UX
    批，禁就地自创语义）。
    """
    metas: list[ExportMeta] = []
    for sidecar in sorted(ctx.exports_dir.glob("*.meta.json")):
        try:
            raw = json.loads(sidecar.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # 损坏边车不阻塞列表
        if raw.get("project_id") == project_id:
            metas.append(ExportMeta(**raw))
    return tuple(metas)
