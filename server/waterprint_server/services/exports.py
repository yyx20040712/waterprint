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
#   resolve_export_file(ctx, file_name) -> Path（EXPD——下载校验正门）
#   ExportFileNotFoundError（EXPD——下载不在册 404 面）
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
#   R4 文件名确定性：项目 id + kind + (unit) + condition + 三元组摘要
#      （禁止当前时钟——同名同输入即同文件，幂等重导出覆盖校验；
#      FE9 R1[DS-01]：dxf 附 unit 分量——同结果集同工况多单元导出
#      文件名互异，防同名覆盖静默丢产物；S2 D6 批量面同收口恒传）。
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
#   - FE9 D2/D3/D4（2026-08-30 drawings 图纸面板批）：D2 模板闸收窄——
#     仅 calcbook 执行存在性闸（余 kind core 链零模板消费；历史三 kind
#     死于 server 模板闸未达 core 正门——探针实录；禁造占位模板违诚实）；
#     D3 options 透传（unit_id/condition_key，空串归一 None——调用点注记）；
#     D4 kind 后缀映射 _KIND_SUFFIXES（dxf/ifc 各得其后缀，calcbook 零漂移）。
#     S2 D6（2026-08-30 落盘化批）：批量路径同款收口——items 每项增
#     unit_id（批级共享）+condition_key（item 自有）；worker 逐项透传
#     kwargs（空串归一 None 同单产物口径）；批量命名 unit 分量恒传。
#   - FE9 R 轮（2026-08-30，二审全 CONFIRMED 后裁定）：R1（DS-01
#     Critical）确定性命名附 unit 分量——单产物路径 _deterministic_
#     name(unit_id=options.unit_id)（批量 items 面不传——worker 挂账
#     同前）；修复锚=同名覆盖静默丢产物。R3（DS-08）options.unit_id
#     严格化（_unit_id_of：仅非空字符串透传，宽转 str() 移除→None=
#     core 诚实 501 面维持）。
#   - WP0（ODA-A 2026-09-02）：dxf 落盘后可选子进程转 DWG（开关空=关，
#     转换器不随产品分发）；失败/超时/边车写失败=warning+跳过（DXF 恒
#     交付，core drafting 零触碰；R-1 G1-01/A-01 收口）。
#   - R2-C（2026-09-02 交付2）：DWG 原语下沉 jobs.dwg（本文件留策略壳）
#     ；批量 payload 增 DWG 开关+超时+dxf 项边车文本预构建（ExportMeta
#     八键单源，worker 仅落盘，同步路径双产物登记同构）。
#   - R-1（2026-09-02 K-05）：转换域拆件 jobs/dwg.py——dwg_convert 真源
#     随迁（D-01 落位成功才置旗），本文件 import 改 jobs.dwg 同步。
#   - SC1 D7（2026-09-04）：ifc 分支——_KINDS 五元组+.ifc 后缀+调用点
#     附 assumptions/site_design kwargs（scene 服务 R3/R5 同款口径）；
#     R1-5：批量入口显式拒绝 ifc（单产物端点语义）。
#   - M5（2026-09-04 图纸面批）：dxf 单产物附 site_design kwargs（unit_id
#     缺省=全厂总图——bare POST 200）；批量对偶拒绝（D5）：批级 unit
#     空+dxf 项→422（worker 无 site_design 透传通道）。
#   - ENG7（2026-09-05 工程攒批）：P3a 拆分——五纯函数+ExportMeta+常量
#     _KINDS/_KIND_SUFFIXES/_DIGEST_PREFIX+InvalidExportRequestError（命名闸
#     两纯函数 raise 面依赖，留此则循环 import——随迁）迁 exports_support.py，
#     顶部 import 透传再导出保公开面（main/routers 直 import 与 getattr
#     消费零断链）；P3b——create_export 抽 _reject_conflicting_batch_pairs
#     （批量对偶拒绝闸）与 _build_drawing_kwargs（图纸族 kwargs 组装）两子函数，
#     语句 44→<40 消 PLR0915 行内豁免（PLR0913 五参签名保留）。
#   - SVRB（2026-09-05 服务端批量任务面）：D1 items 逐项 unit_id 归一
#     （item 非空串优先——_unit_id_of 逐项校验；空串/缺省/None 回落批级
#     options.unit_id，「item 覆盖批级」唯一语义）；D2 payload common 层
#     增 project_path（提交时绝对路径——spawn 环境 worker load_project
#     通道，calc 先例形态）+design_digest（提交时快照信任留痕——执行期
#     不重算不拦截）；_build_drawing_kwargs 迁 jobs/export_kwargs.py
#     （worker 批量面共享真源——services→jobs 向下合法，ENG8 终名随迁）；
#     D3 ifc 放行三件（worker _EXPORT_KINDS+_safe_out_name ifc 特判
#     +ifc 项边车补齐）+_reject_conflicting_batch_pairs 改载 ifc 批内
#     unit 一致小闸（原两族拒绝删除——kwargs 通道已与单产物等价）。
#   - EXPD（2026-09-05 甲案下载端点批）：D1 resolve_export_file（后缀闸
#     DOWNLOAD_SUFFIXES〔exports_support 派生〕→stem 闸 validate_component
#     严格拒→产物/边车存在性双闸→绝对路径；422 先于 404 防·存在性泄露
#     D2）+新域异常 ExportFileNotFoundError（404 面，main._EXCEPTION_STATUS
#     注册）；生成/列表面零变化。
#
# 【测试要求】stale 拒绝与 force 标注、确定性命名、批量转任务。
#
# 【参照】重写计划 §17.1/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Final

import structlog
from waterprint import app as core
from waterprint.contracts.result_schema import InvalidResultError, deserialize

from waterprint_server.jobs.dwg import dwg_convert
from waterprint_server.jobs.export_kwargs import _build_drawing_kwargs
from waterprint_server.jobs.manager import TaskRequest
from waterprint_server.services import ServiceContext
from waterprint_server.services.exports_support import (
    _DIGEST_PREFIX,
    _KINDS,
    DOWNLOAD_SUFFIXES,
    ExportMeta,
    InvalidExportRequestError,
    _batch_items_payload,
    _deterministic_name,
    _sidecar_text,
    _unit_id_of,
)
from waterprint_server.services.projects import design_digest, read_project
from waterprint_server.settings import validate_component

# ENG7：拆分后公开面显式声明（jobs/records.py __all__ 再导出先例——mypy
# no-implicit-reexport 下透传名 ExportMeta/InvalidExportRequestError 需入册；
# importlib+getattr 消费面运行时不受影响）。
__all__ = [
    "ExportFileNotFoundError",
    "ExportHandle",
    "ExportMeta",
    "ExportSourceNotFoundError",
    "ExportTemplateMissingError",
    "InvalidExportRequestError",
    "StaleExportError",
    "create_export",
    "list_exports",
    "resolve_export_file",
]

_IMMEDIATE_LIMIT: Final[int] = 1  # 单产物即时上限（R3 v1：超过即转任务）
# FE9 D2：模板消费 kind 面（唯一）——存在性闸只对 calcbook 执行（core
# calcbook 分支真读模板；dxf/audit/estimate/ifc core 链零模板消费——注记区）。
_TEMPLATE_KINDS: Final[frozenset[str]] = frozenset({"calcbook"})
_LOGGER = structlog.get_logger(__name__)


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


class ExportFileNotFoundError(RuntimeError):
    """下载产物不在册（产物缺/边车缺——注册口径双闸）——404 面（EXPD D2）。"""


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


async def create_export(  # noqa: PLR0913  # 规格冻结五参签名+ctx 首参惯例（PLR0915 已消——ENG7 P3b 抽批量对偶拒绝闸与 dxf kwargs 组装两子函数）
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
    # R2/G1-02（SC1 延伸修复）：per-item kind 缺省/空串归一端点 kind（命名闸/两检查/边车同源）。
    items: Sequence[Mapping[str, Any]] = [
        {**item, "kind": str(item.get("kind") or kind)}
        for item in (chosen.get("items") or [{"kind": kind, "condition_key": condition_key}])
    ]
    latest = _latest_calc_result(ctx, project_id)
    result_digest = str(latest.get("design_hash", ""))
    project = read_project(ctx, project_id)
    current_digest = design_digest(project.design)
    stale = result_digest != current_digest
    if stale and not force:
        raise StaleExportError(result_digest, current_digest)
    template = str(_template_for(ctx, kind))
    # FE9 R1（DS-01）+S2 D6 命名收口：文件名恒附 unit 分量（unit 键进名
    # 防同名覆盖；批量面同收口——worker 透传同批落地，命名面随兑现）。
    unit_option = _unit_id_of(chosen)
    # SVRB D1：items 逐项 unit_id 归一——item 非空串优先（_unit_id_of 逐项
    # 校验），空串/缺省/None 回落批级（「item 覆盖批级」唯一语义；归一位
    # 在本载荷构造处——worker 面逐项读 item.unit_id 天然兼容）。
    items = [{**item, "unit_id": _unit_id_of(item) or unit_option or ""} for item in items]
    names = [
        _deterministic_name(
            project_id,
            (item_kind := str(item.get("kind", ""))),  # G1-02：kind 已归一——白名单外仍 422
            str(item.get("condition_key", "")),
            result_digest,
            # R1-3（G1-04）：ifc=全厂模型——unit 分量置 None（core 不消费
            # unit_id；同工况同结果字节相同文件名应相同）；SVRB：余 kind
            # 逐项 unit（D1 归一——批内 unit 一致小闸保 ifc 命名唯一）。
            unit_id=None if item_kind == "ifc" else (str(item.get("unit_id") or "") or None),
        )
        for item in items
    ]
    if len(items) > _IMMEDIATE_LIMIT:  # R3：超单产物上限转低优先级任务
        # SVRB D3：ifc 批内 unit 一致小闸（原 R1-5/M5 D5 两族拒绝删除——
        # worker kwargs 通道已与单产物等价；小闸定义见上方）。
        _reject_conflicting_batch_pairs(items)
        handle = await ctx.manager.submit(
            TaskRequest(
                kind="export_batch",
                priority=ctx.settings.task_queue_priorities["export_batch"],
                payload={
                    "kind": "export_batch",
                    "project_id": project_id,
                    "exports_dir": str(ctx.exports_dir),
                    # SVRB D2：project_path 提交时绝对路径（spawn 环境 worker
                    # cwd 无关——load_project 通道，calc 先例）+design_digest
                    # 提交时快照信任留痕（执行期不重算不拦截——项目执行期
                    # 被编辑是常态非异常）。
                    "project_path": str(
                        (ctx.projects_dir / f"{project_id}.wp.json").resolve()
                    ),
                    "design_digest": result_digest,
                    # R2-C：DWG 开关+超时（worker dwg_convert 消费；默认空=关）
                    "dwg_converter_path": ctx.settings.dwg_converter_path.strip(),
                    "dwg_converter_timeout_s": ctx.settings.dwg_converter_timeout_s,
                    # R2-C+SVRB：items IPC 面=S2 D6 透传+D1 逐项 unit 归一
                    # +dxf/ifc 项边车文本（dxf={dxf,dwg}/ifc={ifc}——
                    # _batch_items_payload）。
                    "items": _batch_items_payload(items, names, {
                        "project_id": project_id,
                        "design_digest": result_digest,
                        "engine_version": str(latest.get("engine_version", "")),
                        "data_version": str(latest.get("data_version", "")),
                        "stale_labeled": stale and force,
                        "result_file": latest.get("result_file"),
                        "template": template,
                    }),
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
    tmp = out.with_name(f"{out.name}.{uuid.uuid4().hex}.tmp")  # M8-A/W3 唯一化
    # FE9 D3/R3：options 透传（空串归一 None；unit_id 严格化 _unit_id_of）。
    # SC1 D7/M5：ifc·dxf 族 kwargs 组装（assumptions/site_design——SVRB
    # 迁 jobs/export_kwargs.py，worker 批量面共享真源）。
    extra = _build_drawing_kwargs(kind, project)
    core.export_artifact(
        kind,
        plant,
        Path(template),
        tmp,
        # SVRB D1：unit 归一后逐项真源（items 恒 1 项——item 覆盖批级同语义）。
        unit_id=str(items[0].get("unit_id") or "") or None,
        condition_key=condition_key or None,
        **extra,
    )
    os.replace(tmp, out)
    # WP0 挂点（落盘后/边车前）：dxf 可选转 DWG，失败=跳过（DXF 不可破）。
    dwg_name = _post_export_dwg(ctx, kind, out)
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
    if dwg_name is not None:  # 双产物登记；R-1/G1-01 边车写失败=跳过登记（DWG 永不阻塞 DXF）
        try:
            _write_meta(ctx, replace(meta, file_name=dwg_name))
        except OSError as exc:
            _LOGGER.warning(
                "dwg_convert_skipped", source=dwg_name, reason=f"sidecar write failed: {exc!r}"
            )
    return ExportHandle(
        project_id=project_id,
        kind=kind,
        condition_key=condition_key,
        path=str(out),
        design_digest=result_digest,
        stale_labeled=stale and force,
        task_id=None,
    )


def resolve_export_file(ctx: ServiceContext, file_name: str) -> Path:
    """EXPD 下载校验正门（D1：后缀闸→stem 闸→存在性双闸→绝对路径）。

    422 先于 404（D2——格式错先判防存在性泄露）；stem 闸走 settings 真源
    validate_component 严格拒（非 _name_component——其 fallback 属生成面
    语义）；存在性=产物与 .meta.json 边车双闸（注册口径——仅产物在盘而
    边车缺=不可下载）。边车内容不解析（下载面与列表扫描解析面奇态漂移
    显式接受记档——Kimi D10②）。
    """
    if Path(file_name).suffix not in DOWNLOAD_SUFFIXES:
        raise InvalidExportRequestError(
            f"下载文件名 {file_name!r} 后缀不在合法面 {sorted(DOWNLOAD_SUFFIXES)}"
            "（EXPD §18 路径安全——后缀白名单拒边车名/无后缀/大小写后缀）"
        )
    try:
        validate_component(Path(file_name).stem)
    except ValueError as exc:
        raise InvalidExportRequestError(
            f"下载文件名 {file_name!r} stem 非法（EXPD §18 路径安全——"
            "白名单字符集拒 ../分隔符/盘符/多点）"
        ) from exc
    product = ctx.exports_dir / file_name
    if not product.is_file():
        raise ExportFileNotFoundError(
            f"导出产物不存在：{file_name!r}（不在册——先 POST /api/exports/* 生成）"
        )
    if not (ctx.exports_dir / f"{file_name}.meta.json").is_file():
        raise ExportFileNotFoundError(
            f"导出产物 {file_name!r} 注册边车缺失（下载在册口径——产物与边车双闸）"
        )
    return product.resolve()


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
            if isinstance(raw, dict) and raw.get("project_id") == project_id:
                metas.append(ExportMeta(**raw))
        except (json.JSONDecodeError, TypeError):
            continue  # 损坏/非对象/键面不符边车不阻塞列表（WP4 修2+R-1 R2——跳过不 500）
    return tuple(metas)
