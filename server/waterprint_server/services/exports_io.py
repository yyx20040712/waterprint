"""exports IO 支撑：模板解析/最近结果集取数/批量校验闸/边车写/DWG 转换挂点。

输入:  ServiceContext（templates_dir/manager/settings/exports_dir）+导出请求面
输出:  模板路径/最近结果集/边车落盘/DWG 挂点（services/exports.py 消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（TD1 技术债小批 2026-09-09；PD4-bis 改裁件——E 冻结/设计腿原案
#   迁 exports_support 因其 R-1 纯度声明〔零 IO/零全局态〕不可承载本
#   域五件（四件带 IO/ctx 状态），改立本件承接；与 support 纯函数岛
#   分工=IO/状态承载 vs 纯函数。）
#
# 【公开接口】（services/exports.py 顶部 import 消费——跨件私有引用，
#   非 __all__ 契约面）
#   _template_for/_latest_calc_result/_reject_conflicting_batch_pairs/
#   _write_meta/_post_export_dwg + 常量 _TEMPLATE_KINDS
#
# 【搬迁注记】行为零变更纯搬迁（B7 D1「_write_meta 留守」裁定随 TD1
#   预算减压改裁——内聚让位预算，搬迁非删除；R2-C 策略壳在 services
#   层内换件不违 jobs/services 分层语义）。
#
# 【测试要求】services/exports 既有用例经 import 间接覆盖（纯搬迁零
#   行为变化——ENG7 D3 同口径）。
# 【参照】briefs/task-TD1-plan.md PD4-bis；exports.py 规格头 TD1 注记
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from waterprint_server.jobs.dwg import dwg_convert
from waterprint_server.services import ServiceContext
from waterprint_server.services.exports_support import (
    ExportMeta,
    ExportSourceNotFoundError,
    ExportTemplateMissingError,
    InvalidExportRequestError,
    _sidecar_text,
)

# FE9 D2：模板消费 kind 面（唯一）——存在性闸只对 calcbook 执行（core
# calcbook 分支真读模板；dxf/audit/estimate/ifc core 链零模板消费——注记区）。
_TEMPLATE_KINDS: Final[frozenset[str]] = frozenset({"calcbook"})


def _template_for(ctx: ServiceContext, kind: str) -> Path:
    """模板解析（data/templates；缺位=诚实未就绪，UF-16）。

    FE9 D2 收窄：存在性闸仅对 _TEMPLATE_KINDS（calcbook）执行——其余
    kind 名义路径不闸（core 链零模板消费，闸在 core 正门，注记区）。
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
    """最近完成计算结果集（注册序最末 done calc——消费时实时取，UF-37；
    ENG4 D2：原二元组收敛单值——scene/elevation/cost 三服务同款签名）。"""
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


def _reject_conflicting_batch_pairs(
    items: Sequence[Mapping[str, Any]],
) -> None:
    """ifc 批内 unit 一致小闸（SVRB D3 第三族 422；函数沿承载原闸名）。

    SVRB 起 worker 经 project_path 通道透传 assumptions/site_design——原
    两族拒绝（ifc 项任何/批级 unit 空+dxf 项，根因「worker 无透传通道」）
    删除；本闸改载：items 归一后 ifc 项 unit_id 须全相同（含全缺省）——
    ifc 为模型级产物不分单元（命名 unit 分量置 None：混合单元=同名覆盖
    或 N 份冗余两态皆错）；同 unit 多工况由 condition 分量保证唯一。
    """
    units = {
        str(item.get("unit_id") or "")
        for item in items
        if str(item.get("kind", "")) == "ifc"
    }
    if len(units) > 1:
        raise InvalidExportRequestError(
            "ifc 批量项 unit_id 须全一致（ifc 为模型级产物不分单元——"
            "混合单元即拒；同单元多工况请保持 unit 一致或全缺省）"
        )


def _write_meta(ctx: ServiceContext, meta: ExportMeta) -> None:
    """注册表边车（原子写；只记元数据，R2；M8-A/W3 tmp 唯一化——worker 同族）。"""
    sidecar = ctx.exports_dir / f"{meta.file_name}.meta.json"
    tmp = sidecar.with_name(f"{sidecar.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(_sidecar_text(meta), encoding="utf-8", newline="\n")
    os.replace(tmp, sidecar)


def _post_export_dwg(ctx: ServiceContext, kind: str, artifact: Path) -> str | None:
    """WP0（ODA-A）挂点：dxf 且开关非空→子进程转 DWG 同名并排（原语
    jobs.dwg.dwg_convert）；失败/超时=warning 跳过，成功返回名供边车登记。
    """
    if kind != "dxf":
        return None
    converter = ctx.settings.dwg_converter_path.strip()
    if not converter:  # 默认空=关（容器内无转换器，零行为漂移）
        return None
    dwg = dwg_convert(converter, artifact, ctx.settings.dwg_converter_timeout_s)
    return dwg.name if dwg is not None else None
