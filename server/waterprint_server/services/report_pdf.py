"""report_pdf 导出服务用例：装配 AST→Typst 源→typst CLI 编译 PDF（stale 守门沿既有）。

输入:  ServiceContext + 项目 id + condition_key（缺省 design）+选项+force
输出:  ExportHandle（PDF 落 exports/ 确定性命名+.meta.json 边车沿既有）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 计算说明批 2026-10-09 任务书 §二.⑥；镜像测试
#   server/tests/routers/test_report_pdf.py+tests/services/test_report_pdf.py）
#
# 【公开接口】
#   create_report_pdf_export(ctx, project_id, condition_key, options,
#                            *, force=False) -> ExportHandle
#       （POST /api/exports/report_pdf 编排正门——单产物即时生成，
#       ExportHandle/命名/边车/注册面全沿 exports 既有真源）
#   resolve_typst_path(typst_path) -> str（typst CLI 三级解析纯函数）
#   TypstUnavailableError/TypstCompileError（500 族显式消息——部署
#       依赖缺/编译失败超时，stderr 捕获入消息禁静默）
#
# 【行为规格】
#   R1 stale 守门（§17.1 导出行——create_export 同口径）：最近结果集
#      三元组 vs 当前项目 hash 不一致且未 force → StaleExportError
#      （409）；force 导出产物边车显式标注旧三元组（产物永不冒充）。
#      守门先于装配/编译（重活拒在前）。
#   R2 装配（§二.⑥）：services.report.assemble_report 共享真源（diag/
#      cost/layout 装配+verify_report 全绿——md/PDF 两产物同一闸）→
#      core render_typst（AST→Typst 源——确定性，公式=Typst math 打印机
#      单源）→subprocess typst compile（tmp+os.replace 原子落盘
#      GR-38）→边车登记（_write_meta 沿既有）。
#   R3 typst 路径三级解析：settings 覆盖〔env WATERPRINT_TYPST_PATH〕
#      →PATH shutil.which→显式 TypstUnavailableError（部署依赖缺——
#      winget 路径不入硬编码源码，安装路径面仅落 docs/deployment.md）。
#   R4 编译错误面：非零退出/超时（settings.typst_timeout_s）/可执行缺
#      =TypstCompileError（stderr 尾段入消息——500 族显式）+tmp 零残留。
#   R5 全厂整厂产物：options.unit_id 显式 422 拒（audit/estimate 同族
#      预校验）；condition_key 缺省/空串归一 design。
#   R6 确定性边界：Typst 源字节确定（render_typst 纪律）；PDF 二进制
#      含引擎时间戳=引擎行为不入字节对账面（对账面=core golden）。
#   R7 批量面申报：本 kind 为单产物端点语义（task_id 恒 None）——
#      options.items 混装 report_pdf 走 create_export 通用面（core
#      export_artifact 未知 kind 显式拒绝），worker 批量白名单不含
#      本 kind（二道闸显式拒）——两错误面均显式非静默，记档申报。
#
# 【测试要求】services/test_report_pdf.py（解析三态+kind 登记+编译错误
#   面）+routers/test_report_pdf.py（契约五面：200 真编译+面板+下载/
#   stale 409+force 标注/404 两面/unit_id 422）。
#
# 【参照】B6 任务书 §二.⑥；services/exports.py（守门/命名/边车先例）；
#   services/report.py（装配真源）；jobs/export_render.py（渲染分流派位
#   ——本 kind 经独立服务件承载：jobs 层禁上行 import services 装配面）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from waterprint import app as core
from waterprint.report import render_typst

from waterprint_server.services import ServiceContext
from waterprint_server.services._shared.latest_calc import latest_calc_result
from waterprint_server.services.exports_io import _write_meta
from waterprint_server.services.exports_support import (
    ExportHandle,
    ExportMeta,
    ExportSourceNotFoundError,
    InvalidExportRequestError,
    StaleExportError,
    _deterministic_name,
    _unit_id_of,
)
from waterprint_server.services.projects import read_project
from waterprint_server.services.report import assemble_report

__all__ = [
    "ExportSourceNotFoundError",
    "TypstCompileError",
    "TypstUnavailableError",
    "create_report_pdf_export",
    "resolve_typst_path",
]

_KIND: Final[str] = "report_pdf"
_DEFAULT_CONDITION: Final[str] = "design"
# stderr 入消息长度上限（幂积式 200——worker _FAILURE_TEXT_LIMIT 同款口径）
_STDERR_LIMIT: Final[int] = 2 * 10**2


class TypstUnavailableError(RuntimeError):
    """typst CLI 不在（部署依赖缺）——500 面（安装指引显式）。"""


class TypstCompileError(RuntimeError):
    """Typst 编译失败/超时/可执行缺——500 面（stderr 显式消息禁静默）。"""


def resolve_typst_path(typst_path: str) -> str:
    """typst CLI 三级解析（R3）：settings 覆盖→PATH which→显式错误。

    winget 安装路径不入硬编码源码（部署文档「导出格式」节专责）；本机
    已装而 PATH 未含时由部署侧设 WATERPRINT_TYPST_PATH。
    """
    override = typst_path.strip()
    if override:
        return override
    found = shutil.which("typst")
    if found:
        return found
    raise TypstUnavailableError(
        "typst CLI 不在 PATH 且未配置 WATERPRINT_TYPST_PATH（PDF 计算书"
        "导出的部署依赖——服务主机须安装 typst〔winget 安装 Typst.Typst〕"
        "或设该环境变量指向 typst 可执行件；安装路径面见 docs/deployment.md"
        "「导出格式」节）"
    )


def _typst_compile(typst_bin: str, source: str, out: Path, timeout_s: int) -> None:
    """Typst 编译原语（R4）：tmp 源→typst compile→PDF 原子落盘 out。

    失败/超时=TypstCompileError（stderr 尾段入消息）+tmp 零残留
    （try/finally 清理——成功路径产物 os.replace 后源 tmp 即清）。
    """
    tag = uuid.uuid4().hex
    src_tmp = out.with_name(f"{out.name}.{tag}.typ")
    pdf_tmp = out.with_name(f"{out.name}.{tag}.pdf")
    try:
        src_tmp.write_text(source, encoding="utf-8")
        try:
            compiled = subprocess.run(  # 受控二进制（三级解析面）；参数数组形无 shell
                [typst_bin, "compile", str(src_tmp), str(pdf_tmp)],
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TypstCompileError(
                f"typst 编译超时（>{timeout_s}s——WATERPRINT_TYPST_TIMEOUT_S "
                "可调）：PDF 计算书未产出"
            ) from exc
        except OSError as exc:
            raise TypstCompileError(
                f"typst 可执行不可运行：{typst_bin!r}（{exc!r}——检查 "
                "WATERPRINT_TYPST_PATH 指向）"
            ) from exc
        if compiled.returncode != 0:
            stderr_tail = compiled.stderr.decode("utf-8", "replace").strip()
            raise TypstCompileError(
                "typst 编译失败（returncode "
                f"{compiled.returncode}）：{stderr_tail[-_STDERR_LIMIT:]}"
            )
        if not pdf_tmp.is_file():
            raise TypstCompileError(
                f"typst 编译声称成功但产物缺席：{pdf_tmp.name!r}（引擎行为异常）"
            )
        out.parent.mkdir(parents=True, exist_ok=True)
        os.replace(pdf_tmp, out)  # GR-38 原子落盘
    finally:
        src_tmp.unlink(missing_ok=True)
        pdf_tmp.unlink(missing_ok=True)


def create_report_pdf_export(  # 五参=exports.create_export 同款编排豁免先例（ctx+入口四参）
    ctx: ServiceContext,
    project_id: str,
    condition_key: str = "",
    options: Mapping[str, Any] | None = None,
    *,
    force: bool = False,
) -> ExportHandle:
    """report_pdf 编排正门（R1~R5）：守门 →装配 →render_typst →编译 →边车。"""
    chosen = dict(options or {})
    unit_id = _unit_id_of(chosen)
    if unit_id is not None:
        raise InvalidExportRequestError(
            f"report_pdf 为全厂整厂产物（unit_id {unit_id!r} 不适用——"
            "audit/estimate 同族 422 拒）"
        )
    condition = condition_key.strip() or _DEFAULT_CONDITION
    # R1 stale 守门（先于装配/编译——重活拒在前；§17.1 导出行同口径）
    _, latest = latest_calc_result(ctx, project_id, not_found=ExportSourceNotFoundError)
    result_digest = str(latest.get("design_hash", ""))
    project = read_project(ctx, project_id)  # 项目不存在=ProjectNotFoundError（404）
    current_digest = core.design_hash(project.design)
    stale = result_digest != current_digest
    if stale and not force:
        raise StaleExportError(result_digest, current_digest)
    # R2 装配+渲染+编译（verify 全绿同一闸；工况不在结果集=404 面）
    assembled = assemble_report(ctx, project_id, condition)
    label = project.view.name.strip() or project_id
    source = render_typst(assembled.ast, project_label=label)
    typst_bin = resolve_typst_path(ctx.settings.typst_path)
    name = _deterministic_name(project_id, _KIND, condition, result_digest)
    out = ctx.exports_dir / name
    _typst_compile(typst_bin, source, out, ctx.settings.typst_timeout_s)
    _write_meta(
        ctx,
        ExportMeta(
            project_id=project_id,
            kind=_KIND,
            condition_key=condition,
            file_name=name,
            design_digest=result_digest,
            engine_version=str(latest.get("engine_version", "")),
            data_version=str(latest.get("data_version", "")),
            stale_labeled=stale and force,
        ),
    )
    return ExportHandle(
        project_id=project_id,
        kind=_KIND,
        condition_key=condition,
        path=str(out),
        design_digest=result_digest,
        stale_labeled=stale and force,
        task_id=None,  # R7 单产物端点语义（无批量任务面）
    )
