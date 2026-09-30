"""exports 选项预校验闸域：路由/audit 选项整批原子 422（纯 raise 面）。

输入:  导出请求面（批级 options + items Mapping 序列）+端点级 condition_key
输出:  合法即静默返回；任一畸形/audit 违禁携带即 InvalidExportRequestError
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（R2 回炉拆件 2026-09-30：exp-audit 收口批门一双审后——
#   exports_support.py 513 行顶 AGENTS §2 预算墙，预校验闸族四件+
#   两常量迁本件〔ADR-024 拆件配方精神——services 兄弟件先例=
#   exports_registry/exports_io〕；行为零变更纯搬迁〔ENG7 P3a/D3
#   口径〕+audit 闸 R2 扩面随迁落位）。
#
# 【公开接口】
#   reject_bad_route_options(chosen, items, *, condition_key="") -> None
#       （services/exports.py create_export 唯一调用方——import 随迁；
#        含 PROFILE3 h/v 形态闸+sheet×unit 互斥+批6i 站距/批6j 标高
#        形态闸+exp-audit audit 选项闸）
#
# 【行为规格】
#   R-1 纯度：零 IO/零全局态/不 import main·routers 面；import 仅
#      stdlib（re/typing）+同包 exports_support（提取件与
#      InvalidExportRequestError——services 节点内兄弟件先例）。
#   R-2 整批原子：任一项畸形即拒（422 含 item 索引定位）；域上限留
#      core 终闸（双闸分工零重叠——PROFILE3 定案）。
#   R-3 audit 闸（exp-audit-20260930+R2 回炉 k2-W1/d1-N1）：audit 项
#      item 级 unit_id/非空 condition_key/六路由键任一携带即拒；纯
#      audit 批批级同款+端点 condition_key；携带判据类型收死（键在场
#      非 None 非空串即拒——非字符串形态不静默归 None）。
#
# 【测试要求】routers/test_exports_audit.py（audit 族）+services/
#   routers 既有 PROFILE2/3/批6i/6j 用例经 create_export 间接覆盖。
# 【参照】briefs exp-audit-20260930 §三.3+回炉 R2；AGENTS §2/§3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Final

from waterprint_server.services.exports_support import (
    InvalidExportRequestError,
    _sheet_of,
    _unit_id_of,
)

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


# R2 回炉（k2-W1+d1-N1）：audit 禁携路由键族（sheet/比例/站距/标高=图纸
# 路由语义——audit 全厂单份零消费；键集与 exports._route_keys_of 归一层
# face 同族但件间独立声明——support/gates 件不可 import services 主件
# [防环]，双处漂移由预校验用例族锁定）。
_AUDIT_BANNED_ROUTE_KEYS: Final[tuple[str, ...]] = (
    "sheet", "h_scale", "v_scale", "station_overrides", "water_level", "ground_elev",
)


def _audit_carries(source: Mapping[str, Any], key: str) -> bool:
    """R2 回炉③：携带判据类型收死——键在场且非 None 且非空串即拒。

    任意非空值（含非字符串形态如 unit_id=123——_unit_id_of 仅透传非空
    str 会将其静默归 None）都算显式携带意图，禁静默吞（批6j 非字符串
    显式拒先例）；仅缺省/None/空串=未携带。"""
    value = source.get(key)
    return value is not None and value != ""


def _reject_bad_audit_options(
    chosen: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    condition_key: str,
) -> None:
    """exp-audit-20260930：audit 选项闸（整批原子 422——禁静默忽略任一意图）。

    audit=全厂单份 HTML（flows.audit_render_flow 零路由选项消费面）：
    ①item 级显式 unit_id/非空 condition_key/六路由键任一携带即拒（单产物
    缺省 item 携端点 condition_key 即此面）；②纯 audit 批（全部 items 为
    audit）批级 options.unit_id/六路由键/端点 condition_key 同拒（批级将
    逐项继承/代表批意图）；混装批 audit 项不继承批级路由键（归一层置空）
    且批级键为非 audit 项合法消费面，故不拒。"""
    for index, item in enumerate(items):
        if str(item.get("kind", "")) != "audit":
            continue
        label = f"options.items[{index}]"
        if _audit_carries(item, "unit_id"):
            raise InvalidExportRequestError(
                f"导出 {label} 的 kind 'audit' 不接受 'unit_id'（审计报告为"
                "全厂单份不分单元——请移除 unit_id，或改用分单元 kind 如"
                " dxf；exp-audit 整批原子拒绝）"
            )
        if _audit_carries(item, "condition_key"):
            raise InvalidExportRequestError(
                f"导出 {label} 的 kind 'audit' 不接受非空 'condition_key'"
                "（审计报告为全厂单份跨工况文档——condition_key 请留空；"
                "exp-audit 整批原子拒绝）"
            )
        for key in _AUDIT_BANNED_ROUTE_KEYS:
            if _audit_carries(item, key):
                raise InvalidExportRequestError(
                    f"导出 {label} 的 kind 'audit' 不接受路由选项 {key!r}"
                    "（审计报告为全厂单份 HTML——sheet/比例/站距/标高均为"
                    "图纸路由语义，请移除该选项或改用 dxf；R2 回炉整批"
                    "原子拒绝）"
                )
    if not items or not all(
        str(item.get("kind", "")) == "audit" for item in items
    ):
        return  # 非纯 audit 批：批级路由键对 audit 项归一层置空（不拒）
    if _audit_carries(chosen, "unit_id"):
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
    for key in _AUDIT_BANNED_ROUTE_KEYS:
        if _audit_carries(chosen, key):
            raise InvalidExportRequestError(
                f"导出 options 的 kind 'audit' 不接受路由选项 {key!r}"
                "（审计报告为全厂单份 HTML——sheet/比例/站距/标高均为图纸"
                "路由语义，请移除该选项或改用 dxf；R2 回炉整批原子拒绝）"
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
    keyword 参入闸）；R2 回炉（k2-W1+d1-N1）扩：audit 六路由键（sheet/
    h/v/station/标高）item 级与纯 audit 批批级任一携带即拒+unit_id 判据
    类型收死（键在场非 None 非空串即拒——非字符串形态不再静默归 None）；
    域上限留 core 终闸（双闸分工零重叠）。"""
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
