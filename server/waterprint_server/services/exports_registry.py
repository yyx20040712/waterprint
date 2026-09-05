"""exports 产物注册表读面（B7 笔①预拆件——下载校验+清单扫描）。

输入:  ServiceContext + 下载文件名/项目 id（exports_dir 边车扫描）
输出:  校验后产物绝对路径/ExportMeta 元组（零生成零落盘——读面）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B7 笔① 预拆；镜像=services/exports 既有用例经透传间接覆盖）
#
# 【公开接口】（经 services/exports.py 顶部透传再导出保公开面）
#   resolve_export_file/list_exports（产物注册表读面两函数——routers/
#   exports 经 services/exports 消费零变化）
#
# 【行为规格】
#   R-1 纯搬迁：resolve_export_file/list_exports 逐字自 exports.py 迁入
#      （B7 零行为变更——零新测试，D1 裁）。
#   R-2 依赖注记：消费 exports_support 下载两闸常量（DOWNLOAD_SUFFIXES/
#      _DOWNLOAD_STEM_PATTERN）+ExportMeta+raise 面两异常（InvalidExport
#      RequestError/ExportFileNotFoundError）+ServiceContext（services
#      包根装配束）；import 仅 stdlib+两同域件。
#
# 【测试要求】services/exports 既有用例经透传间接覆盖（零新测试——D1 裁）。
# 【参照】briefs/task-B7-brief.md D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from pathlib import Path

from waterprint_server.services import ServiceContext
from waterprint_server.services.exports_support import (
    _DOWNLOAD_STEM_PATTERN,
    DOWNLOAD_SUFFIXES,
    ExportFileNotFoundError,
    ExportMeta,
    InvalidExportRequestError,
)


def resolve_export_file(ctx: ServiceContext, file_name: str) -> Path:
    """EXPD 下载校验正门（R1 恒等闸→D1 后缀闸→R2 stem 闸→存在性双闸→绝对路径）。

    422 先于 404（D2——格式错先判防存在性泄露）。R1 恒等闸首闸：Path.name
    ≠全名即拒（Windows pathlib 视 \\ 为分隔符——..\\..\\evil.dxf 的 stem 取
    末段过闸+目录拼接逃逸任意读实锤收口；POSIX 反斜杠非分隔符恒等放行，
    由 R2 字符集闸兜——双 OS 闭合）。R2 stem 闸=exports_support.
    _DOWNLOAD_STEM_PATTERN（字符集与 settings._COMPONENT_PATTERN 同源但
    不设 {0,63} 全长上界——上界属单分量语义，composite 拼接名实测 73 字符
    在册；弃 validate_component 即此故，非 _name_component 亦同——其
    fallback 属生成面语义）。存在性=产物与 .meta.json 边车双闸（注册口径
    ——仅产物在盘而边车缺=不可下载）。边车内容不解析（下载面与列表扫描
    解析面奇态漂移显式接受记档——Kimi D10②）。
    """
    if Path(file_name).name != file_name:
        raise InvalidExportRequestError(
            f"下载文件名 {file_name!r} 含路径分量（EXPD R1 §18 路径安全——"
            "恒等闸：Path.name≠全名即反斜杠/盘符/分隔符逃逸，Windows pathlib"
            " 视 \\ 为分隔符，拼接前即拒）"
        )
    if Path(file_name).suffix not in DOWNLOAD_SUFFIXES:
        raise InvalidExportRequestError(
            f"下载文件名 {file_name!r} 后缀不在合法面 {sorted(DOWNLOAD_SUFFIXES)}"
            "（EXPD §18 路径安全——后缀白名单拒边车名/无后缀/大小写后缀）"
        )
    if _DOWNLOAD_STEM_PATTERN.fullmatch(Path(file_name).stem) is None:
        raise InvalidExportRequestError(
            f"下载文件名 {file_name!r} stem 非法（EXPD R2 §18 路径安全——"
            "字符集白名单拒 ../分隔符/盘符/多点；不设长度上界——composite"
            " 多分量拼接名可超单分量 64 上界）"
        )
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
