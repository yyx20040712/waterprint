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
#   常量 _KINDS/_KIND_SUFFIXES/_DIGEST_PREFIX + DOWNLOAD_SUFFIXES +
#   _DOWNLOAD_STEM_PATTERN（EXPD/R2：services/exports 下载校验直消费，
#   不入透传 __all__）+ StaleExportError/ExportSourceNotFoundError/
#   ExportTemplateMissingError/ExportFileNotFoundError/ExportHandle
#   （B7 笔①迁入五名——经 services/exports 透传再导出口径；异常四类
#   另经 exports_registry raise 消费）
#
# 【行为规格】
#   R-1 纯度：零 IO/零全局态/不 import main·routers 面；import 仅
#      stdlib+settings.validate_component（层序 services>settings 合法）。
#   R-2 纯搬迁：五函数+ExportMeta+三常量逐字自 exports.py 迁入
#      （ENG7 零行为变化——零新测试，D3 裁）；B7 批增迁异常族四类+
#      ExportHandle（同口径逐字迁入零行为变化）。
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
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from waterprint_server.settings import validate_component

_KINDS: Final[tuple[str, ...]] = ("calcbook", "audit", "dxf", "estimate", "ifc")
_DIGEST_PREFIX: Final[int] = 10  # 文件名摘要长度（白名单字面量；注记区）
# FE9 D4：kind→产物后缀映射（dxf→.dxf、ifc→.ifc；其余 Excel 族恒 .xlsx 零漂移）。
# exp-audit-20260930：audit 后缀勘正 .xlsx→.html（501 占位期的名义后缀收口
# ——真产物为自包含 HTML；下载白名单 DOWNLOAD_SUFFIXES 派生面自动含 .html）。
_KIND_SUFFIXES: Final[Mapping[str, str]] = MappingProxyType(
    {"calcbook": ".xlsx", "audit": ".html", "dxf": ".dxf", "estimate": ".xlsx", "ifc": ".ifc"}
)
# EXPD D1：下载面合法后缀集（_KIND_SUFFIXES 值域派生——不新造字面量集，
# kind 增删时下载白名单零漂移；大小写敏感=.DXF 天然拒）。
DOWNLOAD_SUFFIXES: Final[frozenset[str]] = frozenset(_KIND_SUFFIXES.values())
# EXPD R2：下载 stem 闸字符集——与 settings._COMPONENT_PATTERN 同源（首字符
# 字母数字+体字符 [A-Za-z0-9_-]），但**不设 {0,63} 全长上界**：composite
# 下载名=多分量拼接（uuid 项目 id 32+kind+unit+工况+摘要——实测 73 字符
# 在册），settings 上界属单分量语义不适用拼接全名（municipal_vxinglvchi
# 全厂 stem 72 字符在册而 422 缺陷收口）；分隔符逃逸由 R1 恒等闸
# （Path.name≠全名）+本字符集双拦（\ 与 : 不在集内），长度非安全边界。
_DOWNLOAD_STEM_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")


class InvalidExportRequestError(ValueError):
    """导出请求非法（kind 白名单外）——422 面。"""


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


def _deterministic_name(  # noqa: PLR0913  # 九参=命名四真源+unit/sheet/h/v/station/elev 五 keyword 分量（PROFILE2/3+批6i/6j）；keyword-only 沿 export_artifact 豁免先例
    project_id: str,
    kind: str,
    condition_key: str,
    digest: str,
    *,
    unit_id: str | None = None,
    sheet: str | None = None,
    h_scale: int | None = None,
    v_scale: int | None = None,
    station: str | None = None,
    elev: str | None = None,
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
    # PROFILE2：sheet 分量（sheet=profile 纵断与总图同 kind 同 unit 分量
    # 形态——无分量必同名 os.replace 互覆盖，FE9 R1 同型缺陷防再发）。
    sheet_part = (
        f"-{_name_component(sheet, 'REQUIRED', 'sheet')}" if sheet else ""
    )
    # PROFILE3（PD4）：比例段非 None 即出段（显式透传=定制标记；默认零段
    # 保现名与快照锚恒——默认值判定零跨层常量依赖；h/v 独立出段）。
    scale_part = (
        (f"h{h_scale}" if h_scale is not None else "")
        + (f"v{v_scale}" if v_scale is not None else "")
    )
    scale_seg = f"-{scale_part}" if scale_part else ""
    # 批6i：station_overrides 确定性命名段（异覆盖同名 os.replace 静默
    # 覆盖=FE9 R1 同族缺陷防再发——段值=DSL 串 sha256 前 6 位，调用方
    # 预算；默认零段保现名与快照锚恒——h/v 段同构）。
    station_seg = f"-s{station}" if station else ""
    # 批6j：绝对标高基准命名段（异基准同名 os.replace 静默覆盖=FE9 R1
    # 同族——段值=成对基准串 sha256 前 _DIGEST_PREFIX 位；默认零段保现名恒）。
    elev_seg = f"-e{elev}" if elev else ""
    return (
        f"{safe_project}-{kind}{sheet_part}{scale_seg}{station_seg}{elev_seg}{unit_part}"
        f"-{safe_condition}-{digest[:_DIGEST_PREFIX]}{_KIND_SUFFIXES[kind]}"
    )


def _unit_id_of(chosen: Mapping[str, Any]) -> str | None:
    """FE9 R3（DS-08）：仅非空字符串透传（宽转 str() 移除防消息失真）；
    非字符串/空串→None=M5 后全厂总图通道（bare POST 200——直拒面归
    site_design 缺位，core 侧闸）。
    """
    unit = chosen.get("unit_id")
    return unit if isinstance(unit, str) and unit else None


def _sheet_of(chosen: Mapping[str, Any]) -> str | None:
    """PROFILE2：sheet 选项归一提取（仅非空字符串；值域校验归 core
    白名单——未知值 ArtifactKindNotReady 501 与未知 kind 同语义）。
    """
    sheet = chosen.get("sheet")
    return sheet if isinstance(sheet, str) and sheet else None


def _scale_text_of(chosen: Mapping[str, Any], key: str) -> str | None:
    """PROFILE3：比例选项归一提取（仅非空字符串；域校验在 create_export
    预校验面与 core 终闸——提取面零校验防双处漂移）。
    """
    raw = chosen.get(key)
    return raw if isinstance(raw, str) and raw else None


def _station_text_of(chosen: Mapping[str, Any]) -> str | None:
    """批6i：station_overrides 选项归一提取（仅非空字符串；形态/域校验
    在 reject_bad_route_options 预校验面与 core 终闸——提取面零校验防
    双处漂移，_scale_text_of 同族）。"""
    raw = chosen.get("station_overrides")
    return raw if isinstance(raw, str) and raw else None


def _datum_text_of(chosen: Mapping[str, Any], key: str) -> str | None:
    """批6j：进厂标高选项归一提取（water_level/ground_elev 逐键——仅
    非空字符串；成对/形态/数值域校验在预校验面与 core 终闸，提取面
    零校验防双处漂移，_scale_text_of 同族）。"""
    raw = chosen.get(key)
    return raw if isinstance(raw, str) and raw else None


_DATUM_FORM_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?$")


def _reject_bad_datum_form(source: Mapping[str, Any], label: str) -> None:
    """批6j：进厂标高形态预校验（reject_bad_route_options 子闸——非字符
    串类型显式拒[h/v 同族]+带符号十进制形态+成对必传[单键=半相对半绝
    对错配基准吞意图禁]；数值域[有限性]留 core 终闸——双闸分工零重叠
    先例）。"""
    water = source.get("water_level")
    ground = source.get("ground_elev")
    if water is None and ground is None:
        return
    for key, raw in (("water_level", water), ("ground_elev", ground)):
        if raw is None:
            continue
        if not isinstance(raw, str):  # 非字符串类型=显式拒（h/v 同族）
            raise InvalidExportRequestError(
                f"导出 {label}.{key} 须为字符串（如 '1053.2'）："
                f"收到 {type(raw).__name__}（批6j 整批原子拒绝）"
            )
        if not _DATUM_FORM_RE.match(raw.strip()):
            raise InvalidExportRequestError(
                f"导出 {label}.{key} 值非带符号十进制形态：{raw!r}"
                "（合法如 '1053.2'/'-3.5'——科学记数法/下划线/非 ASCII"
                " 拒；批6j 整批原子拒绝）"
            )
    if (water is None) != (ground is None):
        raise InvalidExportRequestError(
            f"导出 {label} 的 'water_level'/'ground_elev' 成对必传"
            "（单键=半相对半绝对的错配基准——吞意图禁；批6j 整批原子拒绝）："
            f"仅收到 water_level={water!r} ground_elev={ground!r}"
        )


def _reject_bad_station_form(
    source: Mapping[str, Any], label: str
) -> None:
    """批6i：station_overrides 形态预校验（reject_bad_route_options 子闸
    ——非字符串类型显式拒[h/v 同族]+逐项含 '=' 且键值非空；数值域/键位
    [首站/未知站]留 core 终闸——双闸分工零重叠先例）。"""
    raw_station = source.get("station_overrides")
    if raw_station is None:
        return
    if not isinstance(raw_station, str):  # 非字符串类型=显式拒（h/v 同族）
        raise InvalidExportRequestError(
            f"导出 {label}.station_overrides 须为字符串"
            f"（如 'unit_b=30.5,unit_c=44'）：收到 "
            f"{type(raw_station).__name__}（批6i 整批原子拒绝）"
        )
    for part in raw_station.split(","):
        entry = part.strip()
        if not entry or "=" not in entry:
            raise InvalidExportRequestError(
                f"导出 {label}.station_overrides 项 {entry!r} 非法"
                "（形态 'unit=米值' 逗号分隔——批6i 整批原子拒绝）"
            )
        key, _, value = entry.partition("=")
        if not key.strip() or not value.strip():
            raise InvalidExportRequestError(
                f"导出 {label}.station_overrides 项 {entry!r} 键或值空"
                "（批6i 整批原子拒绝）"
            )


def _reject_bad_audit_options(
    chosen: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    condition_key: str,
) -> None:
    """exp-audit-20260930：audit 选项闸（整批原子 422——禁静默忽略任一意图）。

    audit=全厂单份 HTML（flows.audit_render_flow 零路由选项消费面）：
    ①item 级显式 unit_id/非空 condition_key 即拒（单产物缺省 item 携端点
    condition_key 即此面）；②纯 audit 批（全部 items 为 audit）批级
    options.unit_id/端点 condition_key 同拒（批级将逐项继承/代表批意图）；
    混装批 audit 项不继承批级路由键（归一层置空），故不拒。"""
    for index, item in enumerate(items):
        if str(item.get("kind", "")) != "audit":
            continue
        label = f"options.items[{index}]"
        if _unit_id_of(item) is not None:
            raise InvalidExportRequestError(
                f"导出 {label} 的 kind 'audit' 不接受 'unit_id'（审计报告为"
                "全厂单份不分单元——请移除 unit_id，或改用分单元 kind 如"
                " dxf；exp-audit 整批原子拒绝）"
            )
        if str(item.get("condition_key") or ""):
            raise InvalidExportRequestError(
                f"导出 {label} 的 kind 'audit' 不接受非空 'condition_key'"
                "（审计报告为全厂单份跨工况文档——condition_key 请留空；"
                "exp-audit 整批原子拒绝）"
            )
    if not items or not all(
        str(item.get("kind", "")) == "audit" for item in items
    ):
        return  # 非纯 audit 批：批级路由键对 audit 项归一层置空（不拒）
    if _unit_id_of(chosen) is not None:
        raise InvalidExportRequestError(
            "导出 options 的 kind 'audit' 不接受 'unit_id'（审计报告为全厂"
            "单份不分单元——请移除 unit_id，或改用分单元 kind 如 dxf；"
            "exp-audit 整批原子拒绝）"
        )
    if condition_key:
        raise InvalidExportRequestError(
            "导出 kind 'audit' 不接受非空 'condition_key'（审计报告为全厂"
            "单份跨工况文档——condition_key 请留空；exp-audit 整批原子拒绝）"
        )


def reject_bad_route_options(
    chosen: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    *,
    condition_key: str = "",
) -> None:
    """PROFILE3（PD6+R 轮）：路由选项预校验=整批原子拒绝（任一项畸形=
    422 含 item 索引定位）。覆盖面：h/v 形态（isdecimal+长度短路——与
    core 终闸同式，Unicode/超长串双逃逸面闭合 D1-G1-01/A2-G1-01）+非
    字符串类型显式拒（数值承载静默归 None=吞意图 D1-G1-05/A2-G1-03）
    +sheet×unit 互斥（批级或项级共存=收单即拒，不放行到 worker 必败
    项 D1-G1-03/A2-G1-02）；exp-audit-20260930 增 audit 选项闸（kind=
    audit 携 unit_id/非空 condition_key 拒——端点级 condition_key 经
    keyword 参入闸）；域上限留 core 终闸（双闸分工零重叠）。"""
    for label, source in [("options", chosen), *[
        (f"options.items[{i}]", item) for i, item in enumerate(items)
    ]]:
        for key in ("h_scale", "v_scale"):
            if key not in source:
                continue
            raw = source.get(key)
            if raw is None:
                continue
            if not isinstance(raw, str):  # 非字符串类型=显式拒（数值承载等）
                raise InvalidExportRequestError(
                    f"导出 {label}.{key} 须为字符串（如 '2000'）："
                    f"收到 {type(raw).__name__}（PROFILE3 整批原子拒绝）"
                )
            text = raw.strip()
            # R 轮（G1-01 server 侧闭合）：int() 包 try/except——超长串
            # 裸 ValueError 逃逸转本闸 422（A2 建议）；域上限（可转换但
            # 越界）留 core 终闸 501——分层=server 拦不可转换/非正，
            # core 拦域越界，判定零重叠且零常量依赖。
            try:
                value = int(text)
            except ValueError:
                raise InvalidExportRequestError(
                    f"导出 {label}.{key} 数字串超长（与 core 域上限位"
                    "数一致校验）：" f"收到 {len(text)} 位（PROFILE3 整批"
                    "原子拒绝）"
                ) from None
            if not text.isdecimal() or value < 1:
                raise InvalidExportRequestError(
                    f"导出 {label}.{key} 须为正整数比例分母字符串"
                    f"（如 '2000'）：收到 {raw!r}（PROFILE3 整批原子拒绝）"
                )
        _reject_bad_station_form(source, label)
        _reject_bad_datum_form(source, label)
        has_unit = bool(_unit_id_of(source))
        has_sheet = _sheet_of(source) is not None
        if has_unit and has_sheet:
            raise InvalidExportRequestError(
                f"导出 {label} 的 'sheet' 与 'unit_id' 互斥（厂级纵断图与"
                "单单元图不可叠加——收单即拒，不放行到执行必败项；"
                "PROFILE3 R 轮整批原子拒绝）"
            )
    _reject_bad_audit_options(chosen, items, condition_key)


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
        # 批6i 勘误（存量缺陷修复）：路由键 IPC 透传——worker 注记称
        # 「sheet/h/v item 级提取（server 归一进 payload）」而本构造
        # 遗漏该键族，批量 profile 项 worker 侧 _item_route_options 恒
        # 空读=产出总图内容挂纵断名的错配（单产物路径无此缺陷；既有
        # e2e 只验名不验内容故潜伏——本批站距覆盖对拍显形）。键集=
        # create_export 归一恒串面；仅 dxf 项承载（core 白名单非 dxf
        # 零消费，收单闸已拒错配意图）。批6j：进厂标高两键随族扩入。
        if item_kind == "dxf":
            for route_key in ("sheet", "h_scale", "v_scale",
                              "station_overrides",
                              "water_level", "ground_elev"):
                route_value = str(item.get(route_key) or "")
                if route_value:
                    entry[route_key] = route_value
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
