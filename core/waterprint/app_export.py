"""产物导出分发伴生件（PROFILE3 2026-09-08 自 app_enumeration 拆分——
522 行超 500 预算红线，export 族整体迁出；行为零变更纯搬迁）。

输入:  PlantResult（工况快照全集）+ProjectFile 模板/site_design/路由 options
输出:  产物 bytes（calcbook/dxf[单单元/总图/纵断]/ifc——write 落盘+返回）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（UF-33 产物导出面；PROFILE2/3 纵断接线与补全；伴生件形态=
# app_enumeration 同款 L4 并列——pyproject layers 三件套+structure-graph
# §1a/§1b+file-contracts 登记；app_enumeration 经本件再导出消费面零改动；
# 本件零 app 依赖[防环]，app_enumeration→app_export 同层伴生边）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
import warnings
from collections.abc import Mapping
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Final

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.project_schema import SiteDesign
from waterprint.contracts.result_schema import PlantResult
from waterprint.drafting.catalog import (
    DEFAULT_SCALE,
    SITE_SHEET_NO,
    CatalogRow,
    catalog_sheet,
    sheet_origin_below,
)
from waterprint.drafting.dxf_writer import DrawingMeta, write_dxf
from waterprint.drafting.plan_view import unit_plan
from waterprint.drafting.profile_drawing import ProfileOptions, profile_sheet
from waterprint.drafting.section_view import unit_section
from waterprint.drafting.sheets import PROFILE_H_SCALE, PROFILE_V_SCALE, SCALE_DENOM_MAX
from waterprint.drafting.site_plan import SiteOptions, site_layout
from waterprint.drafting.styles import EntityGroup, base_styles
from waterprint.elevation.losses import head_losses
from waterprint.elevation.profile import build_chainage_axis, build_profile
from waterprint.elevation.pumps import evaluate_pumping
from waterprint.geometry.scene import build_scene
from waterprint.ifc_export import build_ifc, write_ifc
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
from waterprint.trace.calcbook import render_calcbook


class ArtifactKindNotReady(Exception):  # noqa: N818  # 名载归属批次（D2 冻结），LoopDivergence 先例
    """产物 kind 未就绪（audit=M4/dxf=M2 出图批/estimate=M3）——GR-11 族。"""


# 站距覆盖值十进制白名单（批6i k1-W2：整数位必在、小数位可选——
# `30`/`30.5` 合法；前导符/科学记数/分组符/非 ASCII 全拒）。
_STATION_VALUE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+(?:\.[0-9]+)?$"
)

_EXPORT_OPTIONS: Final[frozenset[str]] = frozenset(
    {"unit_id", "condition_key", "sheet", "h_scale", "v_scale",
     "station_overrides"}
)


def _station_overrides_of(
    raw: str | None,
) -> dict[str, float] | None:
    """站距覆盖 DSL 解析（批6i core 终闸）：None/空串→None（未传）；
    形态 "unit=30.5,unit2=44"（逗号分隔、键=下游站 unit_id、值=米）。
    逐项校验：非空键/数值域（float+ValueError 收编+有限性——isdecimal
    判域不适用小数形态，try/except 收编面=AGENTS §魔法数字段同款 sanctioned
    路径）/重复键拒（同键双值静默取后者=吞意图）；键位合法性（首站/
    未知站）归 build_chainage_axis 闸（合法集=首站外站位——站集在装配
    期才可知，双层闸与 h/v 域闸+路由闸同构）。"""
    text = (raw or "").strip()
    if not text:
        return None
    overrides: dict[str, float] = {}
    for part in text.split(","):
        entry = part.strip()
        if "=" not in entry:
            raise ArtifactKindNotReady(
                f"station_overrides 项 {entry!r} 缺 '='（形态 "
                "'unit=米值' 逗号分隔——批6i 手动逐边覆盖例外通道）："
                f"收到 {raw!r}"
            )
        key, _, value_text = entry.partition("=")
        key = key.strip()
        value_text = value_text.strip()
        if not key or not value_text:
            raise ArtifactKindNotReady(
                f"station_overrides 项 {entry!r} 键或值空（形态 "
                f"'unit=米值'）：收到 {raw!r}"
            )
        # 数值白名单（k1-W2 实修）：十进制小数形态 ASCII 位数——拒科学
        # 记数法（1e3）/下划线分组（1_000）/全角数字（１２３）等 float
        # 静默收编面（h/v isdecimal 判域同族纪律，消息含合法形态示例）。
        if not _STATION_VALUE_RE.match(value_text):
            raise ArtifactKindNotReady(
                f"station_overrides[{key!r}] 值非十进制小数形态："
                f"{value_text!r}（合法如 '30.5'——科学记数法/下划线/非"
                f"ASCII 数字拒）：收到 {raw!r}"
            )
        try:
            value = float(value_text)
        except ValueError as exc:
            raise ArtifactKindNotReady(
                f"station_overrides[{key!r}] 值非数值：{value_text!r}"
                f"（站距米值，如 'unit_b=30.5'）：收到 {raw!r}"
            ) from exc
        if not isfinite(value) or value <= 0.0:
            # d1-r2 W3 实修：非正/非有限在 DSL 终闸层拒（错误族与 h/v
            # 同序——非正本层拦、键位归轴构造层；NaN/Inf 无里程语义）
            raise ArtifactKindNotReady(
                f"station_overrides[{key!r}] 须为正有限站距米值："
                f"得到 {value_text!r}（如 '30.5'）"
            )
        if key in overrides:
            raise ArtifactKindNotReady(
                f"station_overrides 键 {key!r} 重复（后值静默覆盖前值"
                "=吞意图，禁）：收到 {raw!r}"
            )
        overrides[key] = value
    return overrides


def _scale_denom_of(raw: str | None, what: str) -> int:
    """比例分母解析（PROFILE3 PD3 core 终闸）：strip 后全数字+域校验
    （1≤值≤SCALE_DENOM_MAX）——判定语义与 server 422 预校验显式同一
    （双闸同构，防 422/501 边界漂移）；非法=诚实拒。"""
    text = (raw or "").strip()
    # R 轮（双审 D1-G1-01/A2-G1-01）：isdecimal 挡 Unicode 数字（"②"等
    # isdigit 真而 int 炸）+长度短路挡超长串（≥3.11 int 4300 位上限
    # ValueError 逃逸）——双闸判定域显式同一（server 预校验同式）。
    if not (text.isdecimal() and len(text) <= len(str(SCALE_DENOM_MAX))
            and 1 <= int(text) <= SCALE_DENOM_MAX):
        raise ArtifactKindNotReady(
            f"export_artifact 选项 {what} 须为正整数比例分母字符串"
            f"（1~{SCALE_DENOM_MAX}，如 '2000'）：收到 {raw!r}（PROFILE3）"
        )
    return int(text)


def _check_export_options(
    options: Mapping[str, str | None], kind: str
) -> None:
    """导出选项键白名单（未知键拒——GR-09 精神，防拼写漂移静默忽略）；
    R 轮（D1-G1-04）：h/v 仅 kind=dxf 可传——calcbook/ifc 分支零消费
    选项，传=意图错配诚实拒（禁静默吞）。"""
    unknown = frozenset(options) - _EXPORT_OPTIONS
    if unknown:
        raise ArtifactKindNotReady(
            f"export_artifact 未知选项：{sorted(unknown)}"
            f"（合法 {sorted(_EXPORT_OPTIONS)}）"
        )
    # 判非 None 值而非键存在（调用方归一层可传 None 占位——None=未传）。
    if kind != "dxf" and (
        options.get("h_scale") is not None or options.get("v_scale") is not None
    ):
        raise ArtifactKindNotReady(
            "options 'h_scale'/'v_scale' 仅 kind='dxf'（纵断双比例）可传——"
            f"kind={kind!r} 零消费选项面（PROFILE3 R 轮，禁静默吞意图）"
        )
    if kind != "dxf" and options.get("station_overrides") is not None:
        raise ArtifactKindNotReady(
            "options 'station_overrides' 仅 kind='dxf'（纵断站距覆盖）可传——"
            f"kind={kind!r} 零消费选项面（批6i，禁静默吞意图）"
        )


def export_artifact(  # noqa: PLR0913  # SC1 D6 钦定 keyword-only 两参（assumptions/site_design——ifc 分支消费）；5 参预算与签名主授权冲突，行内豁免沿 N818 同款先例
    kind: str,
    plant: PlantResult,
    template: Path,
    out: Path,
    *,
    assumptions: Mapping[str, float] | None = None,
    site_design: SiteDesign | None = None,
    **options: str | None,
) -> bytes:
    """产物导出分发薄壳（UF-33）：calcbook 接 M1b trace 正门；dxf 接 M2 出图批；ifc 接 BIM 模型批。

    D5 扩展：unit_id 关键字参数（默认 None）——kind="dxf" 单单元出图必填；
    缺省+site_design=全厂总图（M5 兑现），缺省且无 site_design=诚实拒绝；
    calcbook 分支签名零变（unit_id 不消费）。
    R1-1 扩展（2026-08-26）：condition_key 关键字参数（默认 None）——
    dxf 工况显式选择；两选项经 **options 透传（签名 5 参预算合规——
    调用形态 export_artifact(kind, plant, template, out, unit_id=…,
    condition_key=…) 与命名参数完全同形）。
    SC1 扩展（2026-09-04）：keyword-only assumptions/site_design 两参
    （默认 None）——kind="ifc" 消费（build_scene 假设视图与 site 装配
    透传，services/scene.py R3/R5 同口径；None assumptions=默认假设表
    兜底）；其余分支零消费。
    M5 扩展（2026-09-04）：site_design 追及 dxf 分支（unit_id 缺省的
    全厂总图编排——site_layout 接线；dxf 链自建假设视图故 assumptions
    零涉）。
    """
    _check_export_options(options, kind)
    if kind == "calcbook":
        return render_calcbook(plant.trace, plant, template, out).read_bytes()
    if kind == "dxf":
        sheet = options.get("sheet")
        if sheet is not None and sheet != "profile":
            raise ArtifactKindNotReady(
                f"export_artifact 未知 sheet 取值 {sheet!r}"
                "（合法面 ['profile']——图纸形态路由，PROFILE2）"
            )
        if sheet == "profile" and options.get("unit_id") is not None:
            raise ArtifactKindNotReady(
                "options 'sheet=profile'（厂级纵断图）与 'unit_id'（单单元"
                "图）互斥——纵断为跨单元厂级图纸，语义不可叠加（PROFILE2 "
                "组合真值表，禁静默忽略任一意图）"
            )
        h_raw, v_raw = options.get("h_scale"), options.get("v_scale")
        if sheet != "profile" and (h_raw is not None or v_raw is not None):
            raise ArtifactKindNotReady(
                "options 'h_scale'/'v_scale' 仅在 sheet='profile'（纵断双"
                "比例）时可传——其他图纸形态为单比例体系（PROFILE3 组合"
                "真值表，禁静默忽略）"
            )
        overrides_raw = options.get("station_overrides")
        if sheet != "profile" and overrides_raw is not None:
            raise ArtifactKindNotReady(
                "options 'station_overrides' 仅在 sheet='profile'（纵断站距"
                "覆盖）时可传——其他图纸形态无站距语义（批6i 组合真值表，"
                "禁静默忽略）"
            )
        h_scale = _scale_denom_of(h_raw, "h_scale") if h_raw is not None else None
        v_scale = _scale_denom_of(v_raw, "v_scale") if v_raw is not None else None
        station_overrides = _station_overrides_of(overrides_raw)
        if options.get("condition_key") is None and plant.conditions:
            warnings.warn(
                "未指定工况，取 design 档出图——多工况请显式传 condition_key",
                stacklevel=2,  # 栈级 2=指向 export_artifact 调用方
            )
        return _export_dxf(
            plant, options.get("unit_id"), out, options.get("condition_key"),
            site_design=site_design, sheet=sheet,
            h_scale=h_scale, v_scale=v_scale,
            station_overrides=station_overrides,
        )
    if kind == "ifc":
        if options.get("condition_key") is None and plant.conditions:
            warnings.warn(
                "未指定工况，取 design 档出模型——多工况请显式传 condition_key",
                stacklevel=2,  # 栈级 2=指向 export_artifact 调用方（dxf 同构）
            )
        merged = assumptions if assumptions is not None else {
            entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS
        }
        chosen = options.get("condition_key")
        if chosen is None and plant.conditions:
            chosen = sorted(plant.conditions)[0]
        if chosen is None:
            # R0（总控亲验收口）：空工况集禁裸传 build_scene（None 入
            # 「工况不在结果」消息=mypy arg-type 红）——UF-33 诚实拒绝。
            raise ArtifactKindNotReady(
                "产物 kind 'ifc' 需至少一个工况（结果集工况为空——"
                "先重算；禁静默空产物，UF-33）"
            )
        graph = build_scene(plant, merged, chosen, site_design=site_design)
        model = build_ifc(graph)
        write_ifc(model, out)
        return out.read_bytes()
    owners = {"audit": "M4", "estimate": "M3"}
    owner = owners.get(kind, "未知 kind（合法面 calcbook/audit/dxf/estimate/ifc）")
    raise ArtifactKindNotReady(
        f"产物 kind {kind!r} 未就绪（归属：{owner}；禁静默空产物，UF-33）"
    )


# DXF 导出 v1 基准面：未传设计标高时以 ±0.00 相对标高出图（工程相对标高
# 惯例；绝对标高设计输入通道随 server 批/M5 接线——进厂标高是 design
# 态输入非假设，profile R2 口径，此处零默认数值面[0/0 字面量]）。
_REL_DATUM: Final[Mapping[str, float]] = MappingProxyType(
    {"water_level": 0.0, "ground_elev": 0.0}
)

# 纵断图装配常量（PROFILE2 2026-09-08 终裁 PD5）：比例分母=GB/T 50106
# 纵断图横纵差一量级工程惯例（本节取值仅纵断装配用，非全项目图例口径；
# 透传定制面挂账）；图号沿 SITE_SHEET_NO（"01"）同型常量；图名=中文
# 具名常量（总图行「全厂总图」sheet_title 先例同构——非单元行 unit_id
# 口径）；目录比例列=横纵双比例复合字符串（CatalogRow str 列合法）。
_PROFILE_SHEET_NO: Final[str] = "02"
# 目录固定行数（总图行+纵断行——单元行序号自其后起：2+1=03，PROFILE2）。
_FIXED_CATALOG_ROWS: Final[int] = 2
_PROFILE_TITLE: Final[str] = "高程纵断图"
# 目录比例文本=常量派生单真源（双审 G1-02/P2A2-3——字面量双源漂移面消）。
_PROFILE_SCALE_TEXT: Final[str] = f"1:{PROFILE_H_SCALE}/1:{PROFILE_V_SCALE}"


def _export_dxf(  # noqa: PLR0913, PLR0917  # 八参=既有五参+sheet 路由+h/v 比例（PROFILE2/3）；签名扩展沿 export_artifact 行内豁免先例
    plant: PlantResult,
    unit_id: str | None,
    out: Path,
    condition_key: str | None = None,
    site_design: SiteDesign | None = None,
    sheet: str | None = None,
    h_scale: int | None = None,
    v_scale: int | None = None,
    station_overrides: dict[str, float] | None = None,
) -> bytes:
    """dxf 内部编排（D5）：elevation→plan+section（经 UF-32 对照表）→write_dxf。

    R1-1 工况显式化：condition_key=None 取首档（当前装配序=design）+
    UserWarning（不再静默——profile R3"禁静默取首档"口径对齐）；显式值
    未知即拒（合法面=plant.conditions 键集）。
    M5（2026-09-04）：unit_id 缺省分支=全厂总图编排——site_design 透传
    时 site_layout（design 态布置+工况快照纯投影）直接出图；无 site_design
    =诚实拒绝（server 单产物通道有透传，批量面暂不支持——M5 注记）。
    unit_id 给定路径原样零改（含不在工况图/无纵断站既有拒绝）。
    site_plan.InvalidSitePlanError 不捕获直上（L3 领域异常——server 侧
    映射归既有 exception handler 链）。
    M6（2026-09-05）：总图分支=总图实体+图纸目录页同文件并置（案乙 B
    形态）——site_layout 后接 catalog_sheet（sheet_origin_below 自
    包围盒下方派生放置），entities 拼接沿单元图 plan+section 先例；
    目录图号=会话内派生零持久化（catalog R4 语义）。
    批6i（2026-09-29）：sheet=profile 分支开始消费 site_design（桩号轴
    布置连线默认源——v1「site_design 零消费」终裁 §一.8 口径按用户
    2026-09-28 裁决〔relay 增补六十二①〕推翻为消费面）。
    """
    if condition_key is None:
        condition_key = next(iter(plant.conditions), "")  # Warning 已在上层发出
    elif condition_key not in plant.conditions:
        raise ArtifactKindNotReady(
            f"工况 {condition_key!r} 不在结果（合法 "
            f"{sorted(plant.conditions)}——dxf 出图工况校验，R1-1）"
        )
    if sheet == "profile":
        # PROFILE2（2026-09-08）：厂级纵断图独立编排——工况校验共享本层
        # 入口（纵断与单元图/总图同 R1-1 口径）。
        # 批6i（2026-09-29）：site_design 消费面开启——布置连线长度=
        # 桩号轴默认站距源（增补六十二①）；station_overrides=手动逐边
        # 覆盖例外通道（DSL 已在上层终闸解析为 Mapping）。
        # PROFILE3：h/v 透传覆盖（None=声明面常量——默认比例产物字节
        # 恒等锚 9b9ea8e1 的结构性路径——批6i 桩号轴随批重录新基线）。
        return _export_profile_dxf(
            plant, out, condition_key, h_scale=h_scale, v_scale=v_scale,
            site_design=site_design, station_overrides=station_overrides,
        )
    if unit_id is None:
        if site_design is None:
            raise ArtifactKindNotReady(
                "产物 kind 'dxf' 全厂总图导出须传 site_design（server 单产物"
                "通道；批量面暂不支持——M5 注记）"
            )
        styles = base_styles()
        layout = site_layout(
            site_design,
            plant,
            styles,
            # 同构直读：schema SitePlanOptions{coord_grid,wind_rose} 与
            # drafting SiteOptions 字段同名同型（M5 总裁实证注——零换算面）。
            SiteOptions(
                coord_grid=site_design.options.coord_grid,
                wind_rose=site_design.options.wind_rose,
            ),
        )
        sheet_title = "全厂总图"
        # M6 案乙目录行集（图之所绘——D3 总裁修正①）：总图行 01（常量桥
        # 直承 site_plan 真源）+摆放单元行（unit_id 字典序 03..N+2——摆放
        # 结构列表为真源，悬空单元同入列；工况 units 含未摆放单元不采）；
        # 图名=unit_id 原文（中文名真源在 server，零第二真源）；比例=
        # DEFAULT_SCALE（write_dxf 缺省同一常量经 catalog 桥取值零副本）。
        # 图号/序号=本次导出会话内展示派生值，不入库不入 meta 不跨工况。
        # PROFILE2（2026-09-08）：纵断行插位 2（图号 02——目录=会话图纸
        # 集索引语义沿单元行先例[单单元 DXF 独立文件亦经目录行索引]；
        # 图名=中文具名常量[总图行「全厂总图」先例同构]、比例=横纵双
        # 比例复合字符串——总控终裁 PD2 改裁入目录）。
        rows: tuple[CatalogRow, ...] = (
            ("1", SITE_SHEET_NO, sheet_title, DEFAULT_SCALE),
            ("2", _PROFILE_SHEET_NO, _PROFILE_TITLE, _PROFILE_SCALE_TEXT),
            *((str(number), f"{number:02d}", unit_id, DEFAULT_SCALE)
              for number, unit_id in enumerate(
                  sorted(site_design.structures), start=_FIXED_CATALOG_ROWS + 1)),
        )
        catalog = catalog_sheet(rows, sheet_origin_below(layout.entities))
        entities = EntityGroup(entities=layout.entities + catalog.entities)
        meta = DrawingMeta(
            title=sheet_title,
            condition_key=condition_key,
            repro=(plant.repro.design_hash,
                   plant.repro.engine_version, plant.repro.data_version),
        )
        return write_dxf(entities, styles, out, meta).read_bytes()
    snapshot = plant.conditions.get(condition_key, {}).get(unit_id)
    projection = PROJECTION_TABLE.get(unit_id)
    if snapshot is None or projection is None:
        raise ArtifactKindNotReady(
            f"dxf 目标单元 {unit_id!r} 不在当前工况图或 UF-32 对照表"
            f"（工况 {condition_key!r}；禁静默空产物）"
        )
    view = {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}
    losses = head_losses((), ctx=(unit_id, condition_key), assumptions=view)
    profile = build_profile(
        plant, losses, _REL_DATUM, view, condition_key
    )
    station = profile.station_of(unit_id)
    if station is None:
        raise ArtifactKindNotReady(
            f"dxf 目标单元 {unit_id!r} 无纵断站（工况 {condition_key!r}）"
        )
    styles = base_styles()
    plan = unit_plan(snapshot, projection, styles, condition_key)
    section = unit_section(snapshot, station, styles, condition_key)
    entities = EntityGroup(entities=plan.entities + section.entities)
    meta = DrawingMeta(
        title=unit_id,
        condition_key=condition_key,
        repro=(plant.repro.design_hash,
               plant.repro.engine_version, plant.repro.data_version),
    )
    write_dxf(entities, styles, out, meta)
    return out.read_bytes()


def _export_profile_dxf(  # noqa: PLR0913  # 六参=既有三参+h/v 比例+site_design+覆盖 Mapping（批6i）；keyword-only 沿 export_artifact 豁免先例
    plant: PlantResult,
    out: Path,
    condition_key: str,
    h_scale: int | None = None,
    v_scale: int | None = None,
    *,
    site_design: SiteDesign | None = None,
    station_overrides: Mapping[str, float] | None = None,
) -> bytes:
    """厂级纵断图编排（PROFILE2）：build_profile→evaluate_pumping→
    build_chainage_axis（批6i）→profile_sheet。

    装配口径（终裁 PD5 沿承+批6i 桩号轴）：假设视图与单元分支同源
    （DEFAULT_ASSUMPTIONS 默认视图+_REL_DATUM 相对标高基准面——水力
    口径跨图纸一致）；桩号轴=build_chainage_axis(profile, site_design,
    station_overrides) 单源构造（批6i 终裁：站距三态装配唯一路径——
    site_design None/覆盖缺省同样经此构造 fallback 轴，profile_sheet
    零自建零双行为）；平台占宽=10 m 占位沿轴承载（golden 18 站中 12
    站无流程向长度字段实测[辐流池 d=直径/污泥线站无长度语义]，逐站
    取数规则挂账领域专家——v1 station_lengths 通道退役〔全仓零消费
    勘察在案〕，占位宽单源化）；meta.title=中文具名常量（DrawingMeta
    承载图名，单单元图 meta.title=unit_id 先例同构——终裁必改 3）。
    """
    view = {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}
    losses = head_losses((), ctx=("", condition_key), assumptions=view)
    profile = build_profile(plant, losses, _REL_DATUM, view, condition_key)
    pumping = evaluate_pumping(profile, view)
    axis = build_chainage_axis(profile, site_design, station_overrides)
    styles = base_styles()
    options = ProfileOptions(
        h_scale=PROFILE_H_SCALE if h_scale is None else h_scale,
        v_scale=PROFILE_V_SCALE if v_scale is None else v_scale,
        axis=axis,
        pumping=pumping,
    )
    entities = profile_sheet(profile, styles, options)
    meta = DrawingMeta(
        title=_PROFILE_TITLE,
        condition_key=condition_key,
        repro=(plant.repro.design_hash,
               plant.repro.engine_version, plant.repro.data_version),
    )
    write_dxf(entities, styles, out, meta)
    return out.read_bytes()
