"""产物导出分发伴生件（PROFILE3 2026-09-08 自 app_enumeration 拆分——
522 行超 500 预算红线，export 族整体迁出；行为零变更纯搬迁。批6j 拆件：
解析器族迁 app_export_options〔撞墙 566>500——ADR-024 配方，本件回落
386；522/566=不同时点行数非矛盾，N-7 注记〕）。

输入:  PlantResult（工况快照全集）+ProjectFile 模板/site_design/路由 options
       （路由选项 DSL 解析器族批6j 拆至 app_export_options 兄弟件——
       566>500 预算墙 ADR-024 拆件配方；公开面经本件再导出零改动）
输出:  产物 bytes（calcbook/dxf[单单元/总图/纵断]/ifc——write 落盘+返回）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（UF-33 产物导出面；PROFILE2/3 纵断接线与补全；伴生件形态=
# app_enumeration 同款 L4 并列——pyproject layers 三件套+structure-graph
# §1a/§1b+file-contracts 登记；app_enumeration 经本件再导出消费面零改动；
# 本件零 app 依赖[防环]，app_enumeration→app_export 同层伴生边）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from waterprint.app_export_options import (  # 批6j 拆件（ADR-024 预算墙）
    ArtifactKindNotReady as ArtifactKindNotReady,  # noqa: PLC0414  # 显式再导出（mypy attr-defined 面——ruff 别名检查让位）
)
from waterprint.app_export_options import (
    _check_export_options,
    _inlet_datum_of,
    _scale_denom_of,
    _station_overrides_of,
)
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
from waterprint.drafting.sheets import PROFILE_H_SCALE, PROFILE_V_SCALE
from waterprint.drafting.site_plan import SiteOptions, site_layout
from waterprint.drafting.styles import EntityGroup, base_styles
from waterprint.elevation.losses import head_losses
from waterprint.elevation.profile import build_chainage_axis, build_profile
from waterprint.elevation.pumps import evaluate_pumping
from waterprint.geometry.scene import build_scene
from waterprint.ifc_export import build_ifc, write_ifc
from waterprint.registry.assumptions import DEFAULT_ASSUMPTIONS
from waterprint.trace.calcbook import render_calcbook


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
        water_raw, ground_raw = (
            options.get("water_level"), options.get("ground_elev")
        )
        if sheet != "profile" and (water_raw is not None or ground_raw is not None):
            raise ArtifactKindNotReady(
                "options 'water_level'/'ground_elev' 仅在 sheet='profile'"
                "（纵断绝对标高基准）时可传——单单元图剖面以相对标高米值"
                "直投影（绝对化=剖面与平面图脱节，v1 相对基准维持）、总图"
                "无标高语义（批6j 组合真值表，禁静默忽略）"
            )
        h_scale = _scale_denom_of(h_raw, "h_scale") if h_raw is not None else None
        v_scale = _scale_denom_of(v_raw, "v_scale") if v_raw is not None else None
        station_overrides = _station_overrides_of(overrides_raw)
        inlet, _provided = _inlet_datum_of(water_raw, ground_raw)
        # W-3（d1 回炉）：注记=输入原文回显（strip 后十进制串——与输入零
        # 失真；:g 格式 6 位有效数字+大值科学记数法=载体失真不可用）。
        datum_note = (
            "高程基准：绝对标高（进厂水面 "
            f"{water_raw.strip()} m / 地面 {ground_raw.strip()} m）"
            if water_raw is not None and ground_raw is not None else None
        )
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
            inlet=inlet, datum_note=datum_note,
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


# 批6j（2026-09-29 UF-50 收口）：进厂标高通道=导出选项 DSL
# （water_level/ground_elev 成对，仅 sheet=profile——批6i 案丙先例：
# SiteDesign/design 增键=全量 design_hash 漂移越出授权面）。缺省=相对
# ±0.00 基准（工程惯例）——原 `_REL_DATUM` 模块常量退役，默认基准降格为
# _inlet_datum_of 解析器文档化默认（进厂标高是 design 态输入非假设，
# profile R2 口径，零假设数值面）。

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


def _export_dxf(  # noqa: PLR0913, PLR0917  # 十参=批6i 八参+进厂标高解析对（批6j——inlet/datum_on）；签名扩展沿 export_artifact 行内豁免先例
    plant: PlantResult,
    unit_id: str | None,
    out: Path,
    condition_key: str | None = None,
    site_design: SiteDesign | None = None,
    sheet: str | None = None,
    h_scale: int | None = None,
    v_scale: int | None = None,
    station_overrides: dict[str, float] | None = None,
    inlet: Mapping[str, float] | None = None,
    datum_note: str | None = None,
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
        # 批6j：inlet/datum_note 透传（进厂标高 DSL 解析结果+原文注记——
        # 绝对标高模式唯一消费面；单元分支守卫恒得缺省相对基准）。
        return _export_profile_dxf(
            plant, out, condition_key, h_scale=h_scale, v_scale=v_scale,
            site_design=site_design, station_overrides=station_overrides,
            inlet=inlet, datum_note=datum_note,
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
    # 批6j：单元分支进厂标高=守卫恒得缺省相对基准（sheet≠profile 时
    # water_level/ground_elev 已在上层组合真值表拒——inlet 在本分支恒为
    # _inlet_datum_of 缺省值，单单元图相对基准 v1 口径维持）。
    profile = build_profile(
        plant, losses,
        inlet if inlet is not None else _inlet_datum_of(None, None)[0],
        view, condition_key,
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


def _export_profile_dxf(  # noqa: PLR0913  # 八参=批6i 六参+进厂标高解析对（批6j）；keyword-only 沿 export_artifact 豁免先例
    plant: PlantResult,
    out: Path,
    condition_key: str,
    h_scale: int | None = None,
    v_scale: int | None = None,
    *,
    site_design: SiteDesign | None = None,
    station_overrides: Mapping[str, float] | None = None,
    inlet: Mapping[str, float] | None = None,
    datum_note: str | None = None,
) -> bytes:
    """厂级纵断图编排（PROFILE2）：build_profile→evaluate_pumping→
    build_chainage_axis（批6i）→profile_sheet。

    装配口径（终裁 PD5 沿承+批6i 桩号轴+批6j 绝对标高）：假设视图与
    单元分支同源（DEFAULT_ASSUMPTIONS 默认视图——水力口径跨图纸一致）；
    进厂标高=inlet（批6j DSL 解析结果；缺省=相对 ±0.00 基准）；桩号轴=
    build_chainage_axis(profile, site_design, station_overrides) 单源构造
    （批6i 终裁：站距三态装配唯一路径——site_design None/覆盖缺省同样经
    此构造 fallback 轴，profile_sheet 零自建零双行为）；平台占宽=10 m
    占位沿轴承载（golden 18 站中 12 站无流程向长度字段实测[辐流池
    d=直径/污泥线站无长度语义]，逐站取数规则挂账领域专家——v1
    station_lengths 通道退役〔全仓零消费勘察在案〕，占位宽单源化）；
    meta.title=中文具名常量（DrawingMeta 承载图名，单单元图
    meta.title=unit_id 先例同构——终裁必改 3）。
    批6j 绝对标高模式（datum_note 非 None）：elev_baseline=进厂水面标高
    （图面几何基准平移——案甲，默认 0.0 位级恒等）+图脚高程基准注记行
    （输入原文回显——装配层单点构造，W-3）；标高标注文本=station 绝对
    值（build_profile 已随基准平移）。
    """
    view = {entry.key: entry.default for entry in DEFAULT_ASSUMPTIONS}
    losses = head_losses((), ctx=("", condition_key), assumptions=view)
    datum = inlet if inlet is not None else _inlet_datum_of(None, None)[0]
    profile = build_profile(plant, losses, datum, view, condition_key)
    pumping = evaluate_pumping(profile, view)
    axis = build_chainage_axis(profile, site_design, station_overrides)
    styles = base_styles()
    options = ProfileOptions(
        h_scale=PROFILE_H_SCALE if h_scale is None else h_scale,
        v_scale=PROFILE_V_SCALE if v_scale is None else v_scale,
        axis=axis,
        pumping=pumping,
        elev_baseline=datum["water_level"],
        datum_note=datum_note,
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
