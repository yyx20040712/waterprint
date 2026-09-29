"""水面/池底/埋深/超高沿程推算：从进厂标高沿流程拓扑生成纵断数据。

输入:  PlantResult（各单元几何结果）+ Losses + 进厂水面标高配置 + assumptions（超高）
输出:  纵断数据（每单元：水面/池底/埋深/地面标高序列，按 condition_key）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/elevation/test_profile.py）
#
# 【公开接口】
#   build_profile(plant_result, losses, inlet_config, assumptions,
#                 condition_key) -> ElevationProfile
#   class ElevationProfile(不可变)：stations（沿流程有序的单元序列）、
#       每站 {water_level, floor_elev, ground_elev, bury_depth, freeboard}、
#       condition_key、trace（公式迹）
#   build_chainage_axis(profile, site_design, overrides) -> ChainageAxis
#       （批6i 桩号轴）：站距三态装配——布置连线长度（siteplan 坐标系
#       欧氏距离逐段累计）默认+手动逐边覆盖例外+缺布置占位（INFO 记档）；
#       桩号=首站 0 起逐边累计；平台占宽=10 m 占位（结构实长扩键挂账）。
#
# 【行为规格】
#   R1 推算方向：自进厂水面标高起，沿流程拓扑逐单元扣损失、定水面、
#      由水深定池底、由超高假设定埋深——顺序与中间量显式进计算迹。
#   R2 超高等默认值只经 assumptions 取得（带出处）；进厂标高是设计输入
#      （design 态），不是假设（§14.3"折叠为配置"）。
#   R3 按工况索引：design/avg 两档与检修敏感性工况各自成 Profile
#      （水位不同），condition_key 贯穿标注。
#   R4 埋深越界（过深/出地面）产生 Warning（非异常——留给用户决策），
#      Warning 进结果供 UI/图纸标注。
#   R5 纵断数据是 drafting/profile_drawing（高程纵断图）与
#      cost（土方按实际挖深，M3 高程-概算联动）的唯一数据源——
#      两处消费同一 Profile，不存在第二份推导。
#
# 【测试要求】线性三单元纵断连续性（下游水面 <= 上游水面 − 损失）、
#   工况档差异、超高来源断言、越界 Warning 触发。
#
# 【参照】重写计划 §13.3/§14.3 折叠行/§16 A4 总线消费
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Final

from waterprint.contracts.drawing_projection import (
    PROJECTION_TABLE,
    ChainageAxis,
    ElevationProfile,
    ProfileEdge,
    ProfileStation,
)
from waterprint.contracts.project_schema import (
    SiteDesign,
    StructurePlacement,
)
from waterprint.contracts.quantity import DimKey, parse
from waterprint.contracts.result_schema import PlantResult, TraceNode
from waterprint.contracts.unit_api import Severity, Warning
from waterprint.elevation.losses import Losses
from waterprint.registry.assumptions import assumption

__all__ = ["InvalidProfileError", "build_chainage_axis", "build_profile"]

_INLET_KEYS: tuple[str, ...] = ("water_level", "ground_elev")
_SOURCE_UNIT = "inlet"  # golden/模板主线的内置源节点名（dims 空、不设站）
# 站距三态源标签（ChainageAxis.ProfileEdge.source——图脚注记分类同词表）。
_SOURCE_LAYOUT: str = "layout"
_SOURCE_MANUAL: str = "manual"
_SOURCE_FALLBACK: str = "fallback"
# 站距缺布置占位=10 m（工程占位单源：ChainageAxis.platform_widths 同值
# 同源——drafting 侧零第二占位常量，对拍用例钉一致性）。
_SPAN_PLACEHOLDER: float = 10.0
# 同位判定容差=1 mm（quantity 契约派生零字面量——k1-W3 实修：布置位移
# 亚毫米=坐标噪声非真实站距，归同位降级 fallback；防「近同位」绕过同位
# 闸后以 1e-12 级边长触发重叠 WARN 的告警语义错位）。
_COINCIDENT_TOL: Final[float] = parse(1.0, "mm", DimKey.LENGTH)


class InvalidProfileError(Exception):
    """纵断推算非法（进厂配置缺键/工况未索引/损失标签越界）——GR-11 族。"""


def _inlet_value(inlet_config: Mapping[str, float], key: str) -> float:
    """进厂设计输入取值（design 态非假设——R2：缺键即拒，禁默认）。"""
    raw = inlet_config.get(key)
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise InvalidProfileError(
            f"进厂配置缺设计输入键或非数值：{key!r}（得到 {raw!r}——"
            "进厂水面标高/地面标高是 design 态输入，禁静默默认，R2）"
        )
    return float(raw)


def build_profile(
    plant_result: PlantResult,
    losses: Losses,
    inlet_config: Mapping[str, float],
    assumptions: Mapping[str, float],
    condition_key: str,
) -> ElevationProfile:
    """沿程推算正门：自进厂水面标高沿拓扑序逐站扣损失定水面/池底/埋深。

    站序=executor 执行序（PlantResult.conditions[condition_key] 映射序，
    即流程拓扑分层展开序）；水深取数经 UF-32 对照表 section_keys.water_depth
    （缺水深键单元以 0 水深入站并出 INFO Warning——显式不静默）；
    中间量（损失/水位/池底/埋深链）经 LossItem→TraceNode 显式进迹。
    """
    for key in _INLET_KEYS:
        _inlet_value(inlet_config, key)
    if condition_key not in plant_result.conditions:
        raise InvalidProfileError(
            f"工况 {condition_key!r} 不在结果（合法 {sorted(plant_result.conditions)}"
            "——R3 按工况索引，禁静默取首档）"
        )
    snapshots = plant_result.conditions[condition_key]
    inlet_level = _inlet_value(inlet_config, "water_level")
    ground = _inlet_value(inlet_config, "ground_elev")
    freeboard = assumption("safety.superheight", assumptions)
    bury_max = assumption("elevation.bury_depth.max", assumptions)
    stations: list[ProfileStation] = []
    warnings: list[Warning] = []
    level = inlet_level
    for unit_id, snapshot in snapshots.items():
        if unit_id == _SOURCE_UNIT or (
            not snapshot.dims and unit_id not in PROJECTION_TABLE
        ):
            continue  # 内置源节点/空 dims 非工艺单元不设站
        loss = losses.by_label(unit_id)
        level -= loss
        projection = PROJECTION_TABLE.get(unit_id)
        depth_key = (
            projection.section_keys.get("water_depth")
            if projection is not None else None
        )
        water_depth = float(snapshot.dims.get(depth_key, 0.0)) if depth_key else 0.0
        if depth_key is None:
            warnings.append(
                Warning(
                    severity=Severity.INFO,
                    source="UF-32 drawing_projection（该单元 dims 无水深键）",
                    message=(
                        f"单元 {unit_id!r} 无有效水深 dims 键——纵断以 0 水深"
                        "入站（池底=水面）；水深取数随单元尺寸键扩展补录"
                    ),
                    condition_key=condition_key,
                    affected_unit_ids=(unit_id,),
                )
            )
        floor = level - water_depth
        bury = ground - floor
        if bury > bury_max:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source="elevation.bury_depth.max（给水排水手册埋深上限起草）",
                    message=(
                        f"单元 {unit_id!r} 池底埋深 {bury:.3f} m 超上限 "
                        f"{bury_max:g} m——过深开挖/支护成本警示（留用户决策，R5）"
                    ),
                    condition_key=condition_key,
                    affected_unit_ids=(unit_id,),
                )
            )
        elif bury < 0.0:
            warnings.append(
                Warning(
                    severity=Severity.WARN,
                    source="elevation.bury_depth.max（出地面校核）",
                    message=(
                        f"单元 {unit_id!r} 池底高于地面 {abs(bury):.3f} m"
                        "——出地面构筑物（抬高或跌水复核，R5）"
                    ),
                    condition_key=condition_key,
                    affected_unit_ids=(unit_id,),
                )
            )
        flow_key = f"{unit_id}.out.q_avg_daily"
        stations.append(
            ProfileStation(
                unit_id=unit_id,
                water_level=level,
                floor_elev=floor,
                ground_elev=ground,
                bury_depth=bury,
                freeboard=freeboard,
                water_depth=water_depth,
                loss_in=loss,
                design_flow=float(snapshot.outflows.get(flow_key, 0.0)),
            )
        )
    trace = tuple(
        TraceNode(
            formula_id=item.formula_id,
            inputs=dict(item.inputs),
            output=item.value,
            norm_ref=item.norm_ref,
            unit_id=item.label,
            condition_key=condition_key,
        )
        for item in losses.items
    )
    return ElevationProfile(
        stations=tuple(stations),
        condition_key=condition_key,
        trace=trace,
        warnings=tuple(warnings),
    )


def _chainage_warning(
    severity: Severity, source: str, message: str, unit_ids: tuple[str, ...],
    condition_key: str,
) -> Warning:
    """站距轴 Warning 构造（三态记档族——severity/message 双参注入）。"""
    return Warning(
        severity=severity,
        source=source,
        message=message,
        condition_key=condition_key,
        affected_unit_ids=unit_ids,
    )


class _EdgeContext:
    """单边解析上下文（参数预算收载体：覆盖表/摆放索引/记档袋/工况键）。"""

    __slots__ = ("condition_key", "manual", "placements", "warnings")

    def __init__(
        self,
        manual: Mapping[str, float],
        placements: Mapping[str, StructurePlacement],
        warnings: list[Warning],
        condition_key: str,
    ) -> None:
        self.manual = manual
        self.placements = placements
        self.warnings = warnings
        self.condition_key = condition_key


def _resolve_edge(
    prev: ProfileStation, cur: ProfileStation, ctx: _EdgeContext,
) -> ProfileEdge:
    """单边三态解析（manual>layout>fallback）——降级警告就地记档。

    manual=覆盖命中（正有限已由入口闸保证）；layout=两端均有摆放的
    布置连线欧氏距离（距离 0 同位=出图面非校核域降级 fallback+WARN，
    spacing 校核域主责）；fallback=10 m 占位+INFO（缺一端即 fallback）。
    """
    override = ctx.manual.get(cur.unit_id)
    if override is not None:
        # 手动覆盖优先（两源不互斥——例外通道胜默认源）
        return ProfileEdge(
            from_unit=prev.unit_id, to_unit=cur.unit_id,
            station_len=float(override), source=_SOURCE_MANUAL,
        )
    placement_prev = ctx.placements.get(prev.unit_id)
    placement_cur = ctx.placements.get(cur.unit_id)
    if placement_prev is not None and placement_cur is not None:
        distance = math.hypot(
            placement_cur.x - placement_prev.x,
            placement_cur.y - placement_prev.y,
        )
        if distance > _COINCIDENT_TOL:
            return ProfileEdge(
                from_unit=prev.unit_id, to_unit=cur.unit_id,
                station_len=distance, source=_SOURCE_LAYOUT,
            )
        ctx.warnings.append(_chainage_warning(
            Severity.WARN, "chainage.layout（同位布置降级）",
            f"布置连线 {prev.unit_id!r}→{cur.unit_id!r} 两点同位"
            f"（距离 {distance:g} m ≤{_COINCIDENT_TOL:g} m 容差）——出图面非校核域，"
            "按占位站距降级；布置奇态归 spacing 校核域处置",
            (prev.unit_id, cur.unit_id), ctx.condition_key,
        ))
    else:
        missing = cur.unit_id if placement_cur is None else prev.unit_id
        if placement_cur is None and placement_prev is None:
            missing = f"{prev.unit_id!r}与{cur.unit_id!r}"
        ctx.warnings.append(_chainage_warning(
            Severity.INFO, "chainage.fallback（缺布置占位）",
            f"站边 {prev.unit_id!r}→{cur.unit_id!r} 缺布置摆放"
            f"（{missing} 无 structures 条目）——按 {_SPAN_PLACEHOLDER:g} m"
            "占位站距入轴（布置连线长度默认源不可达，显式记档非静默）",
            (prev.unit_id, cur.unit_id), ctx.condition_key,
        ))
    return ProfileEdge(
        from_unit=prev.unit_id, to_unit=cur.unit_id,
        station_len=_SPAN_PLACEHOLDER, source=_SOURCE_FALLBACK,
    )


def build_chainage_axis(
    profile: ElevationProfile,
    site_design: SiteDesign | None,
    overrides: Mapping[str, float] | None = None,
) -> ChainageAxis:
    """桩号轴正门（批6i）：站序链逐边三态装配——真实站距数据唯一真源。

    三态边（终裁案丙）：manual=overrides[to_unit]（手动逐边覆盖例外通道
    ——键=下游站 unit_id〔有入边站集 stations[1:]〕，非正/非有限拒）；
    layout=两端均有摆放的布置连线长度（hypot 欧氏距离——siteplan 坐标系
    两点；距离 0 同位奇态=出图面非校核域降级 fallback+WARN，spacing 校核
    域主责）；fallback=10 m 占位+INFO（缺布置站/缺 site_design 整表）。
    负间隙闸：边长−邻接平台半宽和 ≤0 → WARN（占位宽 10 m 非结构实长的
    占位假象不误伤真布置——结构实长扩键后自然消解；记档不拒）。
    平台占宽=10 m 占位全表（结构沿流程向长度 dims 12/18 站无键——扩键
    挂账领域专家；本通道单源，drafting 零第二占位常量）。
    """
    unit_ids = [station.unit_id for station in profile.stations]
    if len(set(unit_ids)) != len(unit_ids):
        duplicates = sorted(
            {unit_id for unit_id in unit_ids if unit_ids.count(unit_id) > 1}
        )
        raise InvalidProfileError(
            f"纵断站位 unit_id 重复：{duplicates}（桩号映射按 unit_id 定址"
            "——重复键静默塌缩，禁；executor 序应无重复，出现即上游缺陷）"
        )
    manual = dict(overrides) if overrides else {}
    legal = set(unit_ids[1:])  # 有入边站集（首站无入边——覆盖键对其永不消费）
    unknown = sorted(set(manual) - legal)
    if unknown:
        raise InvalidProfileError(
            f"station_overrides 含无入边站或未知键：{unknown}"
            f"（合法集=首站外站位 {sorted(legal)}——首站无入边不可覆盖；"
            "图改后残键须清理，禁静默吞意图）"
        )
    for key, value in manual.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise InvalidProfileError(
                f"station_overrides[{key!r}] 须为数值：得到 {value!r}"
                "（手动站距米值——布尔/非数值拒，GR-02）"
            )
        if not math.isfinite(value) or value <= 0.0:
            raise InvalidProfileError(
                f"station_overrides[{key!r}] 须为正有限数：得到 {value!r}"
                "（站距非正/非有限无里程语义——手动值错误须显式修）"
            )
    placements: Mapping[str, StructurePlacement] = (
        dict(site_design.structures) if site_design is not None else {}
    )
    edges: list[ProfileEdge] = []
    warnings: list[Warning] = []
    widths = dict.fromkeys(unit_ids, _SPAN_PLACEHOLDER)
    ctx = _EdgeContext(manual, placements, warnings, profile.condition_key)
    # pairwise 切片恒短一（strict=False 显式声明——B905 面零歧义）
    for prev, cur in zip(profile.stations, profile.stations[1:], strict=False):
        edges.append(_resolve_edge(prev, cur, ctx))
    chainages: dict[str, float] = {}
    accumulated = 0.0
    for index, station in enumerate(profile.stations):
        if index > 0:
            edge = edges[index - 1]
            accumulated += edge.station_len
            gap = (
                edge.station_len
                - (widths[edge.from_unit] + widths[edge.to_unit]) / 2
            )
            if gap < 0.0:
                # 严格重叠才警（gap==0 贴接=合法邻接形态零管段跨距，v1
                # 邻接等价——批6i 实施收窄：占位宽假象下整表 fallback
                # 边恒 gap==0，误警面消除）。
                warnings.append(_chainage_warning(
                    Severity.WARN, "chainage.platform_overlap（平台重叠）",
                    f"站边 {edge.from_unit!r}→{edge.to_unit!r} 边长 "
                    f"{edge.station_len:g} m 小于邻接平台半宽和"
                    f"（{_SPAN_PLACEHOLDER:g} m 占位宽）——平台图面重叠、"
                    "管段间隙无正值；占位宽非结构实长的假象为主因"
                    "（结构实长扩键后自然消解），如实记档",
                    (edge.from_unit, edge.to_unit), ctx.condition_key,
                ))
        chainages[station.unit_id] = accumulated
    return ChainageAxis(
        chainages=chainages,
        edges=tuple(edges),
        platform_widths=widths,
        warnings=tuple(warnings),
    )
