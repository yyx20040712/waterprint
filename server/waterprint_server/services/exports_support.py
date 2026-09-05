"""exports 纯函数与常量支撑（ENG7 P3a 拆分件——命名/摘要/边车/批量载荷）。

输入:  文件名分量与导出请求面（str/Mapping）+ExportMeta（同文件）
输出:  确定性文件名/边车文本/批量 IPC items（纯函数零 IO 零落盘）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（ENG7 D3 P3a；镜像=services/exports 既有用例经透传间接覆盖）
#
# 【公开接口】（经 services/exports.py 顶部透传再导出保公开面）
#   _name_component/_deterministic_name/_unit_id_of/_sidecar_text/
#   _batch_items_payload + ExportMeta + InvalidExportRequestError +
#   常量 _KINDS/_KIND_SUFFIXES/_DIGEST_PREFIX + DOWNLOAD_SUFFIXES
#   （EXPD：services/exports 下载校验直消费，不入透传 __all__）
#
# 【行为规格】
#   R-1 纯度：零 IO/零全局态/不 import main·routers 面；import 仅
#      stdlib+settings.validate_component（层序 services>settings 合法）。
#   R-2 纯搬迁：五函数+ExportMeta+三常量逐字自 exports.py 迁入
#      （ENG7 零行为变化——零新测试，D3 裁）。
#   R-3 异常随迁注记：命名闸两纯函数（_name_component/_deterministic_
#      name）的 raise 面依赖 InvalidExportRequestError——留 exports.py
#      则 exports↔本件循环 import；随迁+透传，main/routers 直 import
#      面零变化。
#
# 【测试要求】create_export 路径既有用例间接覆盖（零特征测试——D3 裁）。
# 【参照】ENG7 简报 D3；AGENTS §3（ruff 预算）/§5（契约头）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from waterprint_server.settings import validate_component

_KINDS: Final[tuple[str, ...]] = ("calcbook", "audit", "dxf", "estimate", "ifc")
_DIGEST_PREFIX: Final[int] = 10  # 文件名摘要长度（白名单字面量；注记区）
# FE9 D4：kind→产物后缀映射（dxf→.dxf、ifc→.ifc；其余 Excel 族恒 .xlsx 零漂移）。
_KIND_SUFFIXES: Final[Mapping[str, str]] = MappingProxyType(
    {"calcbook": ".xlsx", "audit": ".xlsx", "dxf": ".dxf", "estimate": ".xlsx", "ifc": ".ifc"}
)
# EXPD D1：下载面合法后缀集（_KIND_SUFFIXES 值域派生——不新造字面量集，
# kind 增删时下载白名单零漂移；大小写敏感=.DXF 天然拒）。
DOWNLOAD_SUFFIXES: Final[frozenset[str]] = frozenset(_KIND_SUFFIXES.values())


class InvalidExportRequestError(ValueError):
    """导出请求非法（kind 白名单外）——422 面。"""


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


def _name_component(value: str, fallback: str, what: str) -> str:
    """R1-1（AU-1 修复 2026-08-26）：文件名分量白名单（空串→fallback）。

    condition_key/items condition 等用户可写字段过 validate_component
    （与 safe_child 同源字符集）；越界=InvalidExportRequestError（422）
    ——穿越串拒于落盘之前，§18 路径安全。
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
    project_id: str,
    kind: str,
    condition_key: str,
    digest: str,
    *,
    unit_id: str | None = None,
) -> str:
    """R4 确定性命名：项目 id+kind+(unit)+condition+三元组摘要（禁时钟）。

    R1-1：全部分量过白名单（project_id/condition/unit=validate_component、
    kind∈_KINDS、digest=sha256 hex 天然安全）——穿越即拒（422）。
    FE9 D4：后缀按 kind 映射（_KIND_SUFFIXES——dxf→.dxf/ifc→.ifc；历史
    恒 .xlsx 对 dxf 产物名不诚实的缺陷收口，calcbook 零漂移）。
    FE9 R1（DS-01）：unit_id 非 None 时命名序 {project}-{kind}-{unit}-
    {condition}-{digest}{后缀}；None 零漂移（修复锚=同名 os.replace
    覆盖静默丢失——单元键进名后文件名必然互异）。
    """
    if kind not in _KINDS:
        raise InvalidExportRequestError(f"导出 kind {kind!r} 不在合法面 {_KINDS}")
    safe_project = _name_component(project_id, "REQUIRED", "project_id")
    safe_condition = _name_component(condition_key, "all", "condition_key")
    unit_part = (
        f"-{_name_component(unit_id, 'REQUIRED', 'unit_id')}"
        if unit_id is not None
        else ""
    )
    return (
        f"{safe_project}-{kind}{unit_part}-{safe_condition}"
        f"-{digest[:_DIGEST_PREFIX]}{_KIND_SUFFIXES[kind]}"
    )


def _unit_id_of(chosen: Mapping[str, Any]) -> str | None:
    """FE9 R3（DS-08）：仅非空字符串透传（宽转 str() 移除防消息失真）；
    非字符串/空串→None=M5 后全厂总图通道（bare POST 200——直拒面归
    site_design 缺位，core 侧闸）。
    """
    unit = chosen.get("unit_id")
    return unit if isinstance(unit, str) and unit else None


def _sidecar_text(meta: ExportMeta) -> str:
    """边车文本（确定性序列化——R2-C 批量 items 经 IPC 携带，worker 仅落盘）。"""
    return (
        json.dumps(meta.__dict__, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def _batch_items_payload(
    items: Sequence[Mapping[str, Any]], names: Sequence[str], common: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """R2-C+SVRB：export_batch items IPC 面（S2 D6 透传+D1 逐项 unit+边车预构建）。

    dxf 项附 sidecars={dxf,dwg} 文本（ExportMeta 八键单源，worker 仅落盘；
    DWG 乐观预构建真成功才落盘=无幽灵边车）；SVRB D3：ifc 项附 sidecars=
    {ifc}（无 dwg 边车——模型级；诚实元数据+将来下载白名单统一铺路）；
    其余 kind 存量零边车。unit_id 逐项归一已由 create_export 完成（D1
    item 覆盖批级——空串形态落 IPC 面，worker 侧归一 None 对偶口径）。
    """
    batch: list[dict[str, Any]] = []
    for item, name in zip(items, names, strict=True):
        condition_key = str(item.get("condition_key", ""))
        item_kind = str(item.get("kind", ""))
        entry: dict[str, Any] = {
            "kind": item["kind"],
            "result_file": common["result_file"],
            "template": common["template"],
            "out_name": name,
            # SVRB D1：unit_id 逐项真源（归一位于 create_export）+
            # condition_key item 自有。
            "unit_id": str(item.get("unit_id") or ""),
            "condition_key": condition_key,
        }
        if item_kind in {"dxf", "ifc"}:
            meta = ExportMeta(
                project_id=str(common["project_id"]),
                kind=item_kind,
                condition_key=condition_key,
                file_name=name,
                design_digest=str(common["design_digest"]),
                engine_version=str(common["engine_version"]),
                data_version=str(common["data_version"]),
                stale_labeled=bool(common["stale_labeled"]),
            )
            if item_kind == "dxf":
                entry["sidecars"] = {
                    "dxf": _sidecar_text(meta),
                    "dwg": _sidecar_text(
                        replace(meta, file_name=Path(name).with_suffix(".dwg").name)
                    ),
                }
            else:  # SVRB D3：ifc 项边车补齐（仅产物 meta——无 dwg 面）
                entry["sidecars"] = {"ifc": _sidecar_text(meta)}
        batch.append(entry)
    return batch
