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

from collections.abc import Mapping

from waterprint.contracts.drawing_projection import (
    PROJECTION_TABLE,
    ElevationProfile,
    ProfileStation,
)
from waterprint.contracts.result_schema import PlantResult, TraceNode
from waterprint.contracts.unit_api import Severity, Warning
from waterprint.elevation.losses import Losses
from waterprint.registry.assumptions import assumption

__all__ = ["InvalidProfileError", "build_profile"]

_INLET_KEYS: tuple[str, ...] = ("water_level", "ground_elev")
_SOURCE_UNIT = "inlet"  # golden/模板主线的内置源节点名（dims 空、不设站）


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
