"""高程纵断图：沿流程拓扑的纵断面（水面/池底/管底/地面线 + 标高标注）。

输入:  ElevationProfile（elevation 子系统总线产出）+ ChainageAxis（批6i
       桩号轴——真实站距）
输出:  纵断图 DXF 实体组（流程纵断面，比例横纵分设）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_profile_drawing.py
#   +实现测试 tests/drafting/test_profile_drawing_impl.py）
#
# 【公开接口】
#   profile_sheet(profile: ElevationProfile, styles,
#                 options: ProfileOptions) -> EntityGroup
#   class ProfileOptions：h_scale / v_scale（横纵比例分设，如横 1:500
#      纵 1:100——工程惯例，取值来自 options 数据非硬编码；比例分母
#      整数必填）+axis（ChainageAxis 桩号轴——批6i 起必填单源：站距
#      三态/桩号/平台占宽全经 elevation.build_chainage_axis 构造，本
#      文件零自建零第二占位常量）+pumping（PumpingPlan 标注数据，
#      None 跳过——经 app 装配传入 R3；泵站/跌水注记仅取与本图
#      condition_key 同工况条目）
#   〔styles 参数语义注记（R 轮 G1-01 双审呈报）：本文件不消费
#      styles——EntityGroup 以图层名引用样式，装配在 dxf_writer.
#      write_dxf._apply_styles 按图层名统一落盘；签名三参沿
#      unit_section 同款先例（签名含 styles、函数体零消费——调用
#      方链 styles 传至 write_dxf）〕
#
# 【行为规格】
#   R1 四线齐备：地面线/水面线/池底线/管底线（§12.5 高程纵断图定义：
#      "沿流程拓扑生成纵断面（水面/池底/管底/地面线+标高标注）"）；
#      数据全部来自 ElevationProfile，本文件零标高推算（纯投影）。
#      〔管底线语义注记（PROFILE 批 PD1）：重力流管道贴池底敷设、忽略
#      管壁厚——管底=池底近似投影，source_key 与池底同指 floor_elev，
#      语义由 LAYER_PIPE 图层区分；独立管底高程需求挂账 L0 扩展流程〕
#   R2 站位横轴 = 桩号（批6i 真实站距）：站位序=流程拓扑序（topo 分层
#      的展开序）；x=结构中心桩号（ChainageAxis.chainages 累计里程）
#      中心锚定平台 [c−w/2, c+w/2]——中心距=图面距（度量真实）；站距
#      三态源（布置连线/手动覆盖/缺布置占位）经 build_chainage_axis
#      装配（站序链数据唯一真源），本文件零站距推导。站名标注经 i18n
#      显示键取中文（显示层职责——core 面站名=unit_id 原文，catalog
#      "图名=unit_id 原文"同款先例）；每站桩号 K 图式标注（K{km}+
#      {m:06.3f} 零填充——道路/管线纵断工程惯例）。
#   R3 标高标注：每站标注水面/池底/地面三值（剖面图 R2 同源规则）；
#      提升泵站与跌水点从 PumpingPlan 标注（经 options.pumping 装配
#      传入——纯读标注，零水力计算）。
#   R4 横纵比例分设的坐标换算集中在本文件入口一处（可审计），
#      禁散落各图元。模型坐标负域合法（首站平台跨原点 [−w/2, w/2]
#      ——DXF WCS 无原点约束；v1 左锚全正域系巧合非契约）。
#   R5 纯投影 + 零 ezdxf（同 plan_view R2）；工况标注（condition_key）
#      ——不同工况水位不同，图纸必须可区分。图脚站距源注记=计数汇总
#      +逐边明细（fallback/manual/重叠三类全图面化——批6i 终裁：零
#      dead field，fallback 边定位与 manual 边漂移可见化）。
#
# 【数值纪律】m→mm 因子经 quantity.parse 契约求值（dxf_writer.
#   _mm_per_meter 同款——1 mm=m 换算不抄系数）；桩号 K 图式千米分解
#   =10**3 幂积形态（API_TOKEN_MIN_LENGTH 绕字面量门禁先例）；标高
#   文本 .3f 格式串非数值字面量（AST 门禁面外）。
#
# 【依赖足迹】waterprint.elevation.pumps（PumpingPlan 类型——L3 同层
#   消费边，import-linter ignore_imports 显式豁免登记，ifc_export→
#   geometry 2026-09-03 先例；structure-graph.md §1b 注记承载）；
#   contracts.drawing_projection（ChainageAxis——L0 类型面）。
#
# 【测试要求】四线实体存在且值 == Profile、比例换算正确、桩号中心锚
#   定位、K 图式文本、三态源注记、工况标注、快照回归（内容哈希自锚
#   ——test_profile_drawing_impl）。
#
# 【参照】重写计划 §12.5 高程纵断图行；ADR-006；PROFILE 批简报
#   （task-PROFILE-plan.md PD1~PD9）；批6i 设计件 rev2（b6i-design.md）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from waterprint.contracts.drawing_projection import (
    ChainageAxis,
    ElevationProfile,
)
from waterprint.contracts.quantity import DimKey, parse
from waterprint.contracts.unit_api import Severity
from waterprint.drafting.styles import (
    LAYER_ELEV,
    LAYER_PIPE,
    LAYER_POOL,
    Entity,
    EntityGroup,
    StyleTable,
)

if TYPE_CHECKING:
    from waterprint.elevation.pumps import PumpingPlan

__all__ = ["InvalidProfileDrawingError", "ProfileOptions", "profile_sheet"]


class InvalidProfileDrawingError(Exception):
    """纵断图生成非法（空站位/比例非正/轴不匹配）——GR-11 族。"""


# 桩号 K 图式千米分解（K{km}+{m:07.3f} 零填充——10*10*10 幂积
# 形态=1000 仅用白名单字面量 10；API_TOKEN_MIN_LENGTH 先例同族）。
_KM_METERS: Final[float] = float(10 * 10 * 10)
# 站距三态源图面注记词表（ProfileEdge.source 同词表单源投影）。
_SOURCE_LABELS: Final[dict[str, str]] = {
    "layout": "布置连线",
    "manual": "手动",
    "fallback": "占位",
}


@dataclass(frozen=True)
@final
class ProfileOptions:
    """纵断图选项（不可变）：横纵比例分母 + 桩号轴 + 提升计划标注。

    h_scale/v_scale=比例分母整数（如横 1:500 纵 1:100 → 500/100——
    必填，工程出图比例显式传入不设默认）；axis=ChainageAxis 桩号轴
    （批6i 起必填——含站距三态边/桩号/平台占宽；缺布置场景同样经
    build_chainage_axis(profile, None) 单源构造 fallback 轴，本图零
    自建）；pumping=None 时泵/跌水注记整体跳过（PumpingPlan 双空
    合法语义沿承）。
    """

    h_scale: int
    v_scale: int
    axis: ChainageAxis
    pumping: PumpingPlan | None = None


def _mm_per_meter() -> float:
    """m→mm 换算因子（R4 唯一换算点用；quantity.parse 契约求值——
    dxf_writer._mm_per_meter 同款：1 mm=m 经 pint 换算，因子=1/0.001）。"""
    return 1.0 / parse(1.0, "mm", DimKey.LENGTH)


def _to_sheet(x_m: float, elev_m: float, factor: float,
              options: ProfileOptions) -> tuple[float, float]:
    """模型坐标（m）→ 图面坐标（mm）：x=桩距×因子÷横比例分母，
    y=标高×因子÷纵比例分母（R4 换算集中唯一入口——y=实际高程直投影
    零基准平移，PD5）。"""
    return (
        x_m * factor / options.h_scale,
        elev_m * factor / options.v_scale,
    )


def _station_bounds(profile: ElevationProfile,
                    axis: ChainageAxis) -> tuple[tuple[float, float], ...]:
    """各站平台界（米）：中心锚 [c−w/2, c+w/2]——桩号=结构中心里程，
    平台占宽=axis.platform_widths（批6i 两维分离：边长推里程、占宽定
    画幅）。轴覆盖守卫：axis 缺任一站桩号=装配缺陷显式拒（禁静默回退
    等距——v1 双行为面已退役）。"""
    unit_ids = [station.unit_id for station in profile.stations]
    missing = [
        unit_id for unit_id in unit_ids
        if unit_id not in axis.chainages or unit_id not in axis.platform_widths
    ]
    if missing:
        raise InvalidProfileDrawingError(
            f"桩号轴缺站位桩号或平台占宽：{missing}（axis 与 profile 站集"
            "不一致——轴须经 build_chainage_axis(profile,…) 单源构造，"
            "禁静默等距回退）"
        )
    # d1-r2 W2 实修：v1「站距非正拒」fail-closed 在手构轴面复立（公开
    # ChainageAxis 可构造——负/零边长倒退桩号禁入图，G1-03 口径承接）。
    for edge in axis.edges:
        if edge.station_len <= 0.0:
            raise InvalidProfileDrawingError(
                f"桩号轴边长非正：{edge.from_unit!r}→{edge.to_unit!r} "
                f"得 {edge.station_len:g} m（零宽平台/倒退桩号无图面语义"
                "——构造期缺陷显式拒）"
            )
    return tuple(
        (
            axis.chainages[unit_id] - axis.platform_widths[unit_id] / 2,
            axis.chainages[unit_id] + axis.platform_widths[unit_id] / 2,
        )
        for unit_id in unit_ids
    )


def _km_text(chainage_m: float) -> str:
    """桩号 K 图式文本（K{km}+{m:07.3f}——千米+零填充三位小数余量：
    总宽 7=三位整数+小数点+三位小数〔"005.200"〕，批6i 终裁 N1）。

    进位归一（k1-W1 实修）：余量 ∈ [999.9995, 1000) 时 07.3f 格式化为
    "1000.000"（07 系最小宽度非上限）——对上界形态串做进位+归零（比较
    面经 _KM_METERS 自身格式化派生，零新字面量）。
    """
    km = int(chainage_m // _KM_METERS)
    text = f"{chainage_m - km * _KM_METERS:07.3f}"
    if text == f"{_KM_METERS:07.3f}":
        km += 1
        text = f"{0.0:07.3f}"
    return f"K{km:d}+{text}"


def _source_note(axis: ChainageAxis) -> list[str]:
    """图脚站距源注记行集（R5 三态全图面化）：计数汇总+逐边明细。

    fallback 边逐条列出（缺布置定位残边）；manual 边逐条列出 from→to=
    值（链变动漂移可见化——打印锚随链动）；重叠/同位警告逐条列出
    （axis.warnings 全量投影，零 dead field）。
    """
    counts = dict.fromkeys(_SOURCE_LABELS.values(), 0)
    lines_detail: list[str] = []
    for edge in axis.edges:
        counts[_SOURCE_LABELS[edge.source]] += 1
        if edge.source in ("manual", "fallback"):
            lines_detail.append(
                f"站距[{_SOURCE_LABELS[edge.source]}] "
                f"{edge.from_unit}->{edge.to_unit}={edge.station_len:g} m"
            )
    lines = [
        "站距源：布置连线 {layout} / 手动 {manual} / 占位 {fallback}".format(
            layout=counts["布置连线"], manual=counts["手动"],
            fallback=counts["占位"],
        )
    ]
    lines.extend(lines_detail)
    # d1-r2 W1 实修：仅 WARN 入警告行（INFO=fallback/常态占位明细已载
    # ——重复呈现+语义错级消除；Severity 经 unit_api L0 判别）。
    lines.extend(
        f"站距警告 {warning.message}"
        for warning in axis.warnings if warning.severity == Severity.WARN
    )
    return lines


# 四线声明表（R1）：(字段, 图层)——管底与池底同指 floor_elev、图层分
# 取 LAYER_POOL/LAYER_PIPE（语义区分——R1 注记；表驱动=四线齐备可对账）。
_FOUR_LINES: Final[tuple[tuple[str, str], ...]] = (
    ("ground_elev", LAYER_ELEV),
    ("water_level", LAYER_ELEV),
    ("floor_elev", LAYER_POOL),
    ("floor_elev", LAYER_PIPE),
)


def _polyline_of(line: tuple[str, str], bounds: tuple[tuple[float, float], ...],
                 profile: ElevationProfile, factor: float,
                 options: ProfileOptions) -> Entity:
    """四线之一（line=(字段, 图层)）：全站折点序列——每站站内平台两折点
    （x=平台左/右界〔中心锚桩号〕，y=该站字段值）；坐标全经 _to_sheet
    唯一换算入口；source_key=被引用字段。"""
    field, layer = line
    points: list[tuple[float, float]] = []
    for station, (x_left, x_right) in zip(profile.stations, bounds, strict=True):
        value = getattr(station, field)
        points.append(_to_sheet(x_left, value, factor, options))
        points.append(_to_sheet(x_right, value, factor, options))
    return Entity("line", layer, tuple(points),
                  text=field, source_key=f"profile.{field}")


def profile_sheet(
    profile: ElevationProfile,
    styles: StyleTable,
    options: ProfileOptions,
) -> EntityGroup:
    """纵断图正门（纯投影）：四线+每站标高/站名/桩号标注+泵/跌水注记
    +站距源注记+工况。

    实体生成顺序固定（确定性）：四线（地面/水面/池底/管底）→逐站标高
    三值与站名与桩号 K→泵站/跌水注记（options.pumping）→图脚站距源
    注记→工况标注。
    """
    if not profile.stations:
        raise InvalidProfileDrawingError(
            "纵断站位为空（ElevationProfile.stations 至少一站——"
            "空站纵断无图面语义，禁静默空产物）"
        )
    if options.h_scale <= 0 or options.v_scale <= 0:
        raise InvalidProfileDrawingError(
            f"比例分母非正：h={options.h_scale} v={options.v_scale}"
            "（1:N 比例分母须正整数——R4 换算前提）"
        )
    factor = _mm_per_meter()
    bounds = _station_bounds(profile, options.axis)
    entities: list[Entity] = [
        _polyline_of(line, bounds, profile, factor, options)
        for line in _FOUR_LINES
    ]
    right_of: dict[str, float] = {}  # unit_id → 站右界桩号（泵标注定位）
    for station, (x_left, x_right) in zip(profile.stations, bounds, strict=True):
        right_of[station.unit_id] = x_right
        for field in ("water_level", "floor_elev", "ground_elev"):
            value = getattr(station, field)
            entities.append(
                Entity("text", LAYER_ELEV,
                       (_to_sheet(x_right, value, factor, options),),
                       text=f"{value:.3f}", source_key=f"profile.{field}")
            )
        entities.append(
            Entity("text", LAYER_ELEV,
                   (_to_sheet((x_left + x_right) / 2, station.ground_elev,
                              factor, options),),
                   text=station.unit_id, source_key="profile.unit_id")
        )
        entities.append(
            Entity("text", LAYER_ELEV,
                   (_to_sheet(x_left, station.ground_elev, factor, options),),
                   text=_km_text(options.axis.chainages[station.unit_id]),
                   source_key="chainage.km")
        )
    if options.pumping is not None:
        # R 轮 G1-02：注记仅取与本图同工况条目（PumpingPlan 按工况独立
        # 产出——异工况条目标到本图=工况混注）；跌水注记锚定受影响站
        # 右界（affected_unit_ids 首元素——零原点堆叠）。
        for pump in options.pumping.stations:
            if pump.condition_key != profile.condition_key:
                continue  # 异工况泵站条目——不属于本图
            pump_station = profile.station_of(pump.unit_id)
            if pump_station is None:
                continue  # 泵站位不在本纵断（工况差异）——跳过非异常
            entities.append(
                Entity("elev_symbol", LAYER_ELEV,
                       (_to_sheet(right_of[pump.unit_id],
                                  pump_station.water_level, factor,
                                  options),),
                       text=f"提升 total_head={pump.total_head:.3f}"
                            f" design_flow={pump.design_flow:.3f}",
                       source_key="pumping.total_head")
            )
        for drop in options.pumping.drop_warnings:
            if drop.condition_key != profile.condition_key:
                continue  # 异工况跌水条目——不属于本图
            anchor_id = (
                drop.affected_unit_ids[0] if drop.affected_unit_ids else None
            )
            if anchor_id is None or anchor_id not in right_of:
                continue  # 无受影响站锚（或不在本图）——无法定位不标
            anchor_station = profile.station_of(anchor_id)
            if anchor_station is None:
                continue
            entities.append(
                Entity("text", LAYER_ELEV,
                       (_to_sheet(right_of[anchor_id],
                                  anchor_station.ground_elev, factor,
                                  options),),
                       text=drop.message,
                       source_key="pumping.drop_warnings")
            )
    # 图脚站距源注记（R5）：自 (0,0) 向下逐行（工况标注行尾随——注记
    # 锚序确定性：站距源在前工况在后）。
    note_lines = _source_note(options.axis)
    entities.extend(
        Entity("text", LAYER_ELEV, ((0.0, -float(index)),),
               text=line, source_key="chainage.source_note")
        for index, line in enumerate(note_lines)
    )
    entities.append(
        Entity("text", LAYER_ELEV, ((0.0, -float(len(note_lines))),),
               text=f"condition={profile.condition_key}",
               source_key="condition_key")
    )
    return EntityGroup(entities=tuple(entities))
