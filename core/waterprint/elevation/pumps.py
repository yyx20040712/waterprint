"""提升判定与扬程计算：跌水/提升分支的显式判定（>1m 跌水提示）。

输入:  ElevationProfile（纵断数据）
输出:  泵参数（扬程/流量/台数建议输入）+ 跌水警告
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/elevation/test_pumps.py）
#
# 【公开接口】
#   evaluate_pumping(profile: ElevationProfile,
#                    assumptions) -> PumpingPlan
#   class PumpingPlan(不可变)：stations（需提升站位列表）、
#       每站 {static_head, total_head, design_flow, condition_key}、
#       drop_warnings（跌水 >1m 的位置与高差）
#
# 【行为规格】
#   R1 判定显式化：水面衔接高差 > 提升阈值（默认来自 assumptions，出处
#      入库；重写计划口径"跌水 >1m 提示"）→ 生成跌水 Warning；
#      需要提升 → 生成泵站站位与扬程（静扬程 + 管路损失，损失经
#      losses.py 公式求值，禁止另抄公式）。
#   R2 台数与选型：本文件只给设计流量与扬程（泵参数输入）；设备选型
#      台数组合属于方案枚举/单元包职责（提升泵房单元），不在此重复。
#   R3 工况关联：扬程按 condition_key 计算（design 档流量）；结果标注
#      所属工况（§14.1"约束校核、三维、图纸、概算都标注所属工况"）。
#   R4 无提升需求（全程自流）→ 空站位列表是合法结果，非异常。
#
# 【测试要求】构造 2m 跌水 → Warning + 高差正确、自流图 → 空计划、
#   total_head >= static_head 不变量、工况标注。
#
# 【参照】重写计划 §14.2 跌水/提升行
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from waterprint.contracts.drawing_projection import ElevationProfile
from waterprint.contracts.unit_api import Severity, Warning
from waterprint.elevation.losses import friction_loss
from waterprint.registry.assumptions import assumption

__all__ = ["PumpStation", "PumpingPlan", "evaluate_pumping"]


@dataclass(frozen=True)
@final
class PumpStation:
    """需提升站位（不可变）：静扬程/总扬程/设计流量/工况标注。"""

    unit_id: str
    static_head: float
    total_head: float
    design_flow: float
    condition_key: str


@dataclass(frozen=True)
@final
class PumpingPlan:
    """提升判定产出（不可变）：站位列表 + 跌水警告（全程自流=双空合法，R4）。"""

    stations: tuple[PumpStation, ...]
    drop_warnings: tuple[Warning, ...]


def evaluate_pumping(
    profile: ElevationProfile, assumptions: Mapping[str, float]
) -> PumpingPlan:
    """提升判定正门：跌水>阈值→Warning；水面需抬升→站位+扬程（R1/R3）。

    扬程损失经 losses.py EL-F1 求值（管路概算几何经 assumptions 键
    elevation.pump.*——设计输入接线前概算占位，出处随 registry 条目）；
    台数/选型归方案枚举与提升泵房单元包（R2 不在此重复）。
    """
    threshold = assumption("elevation.drop_threshold", assumptions)
    stations: list[PumpStation] = []
    drops: list[Warning] = []
    for upstream, downstream in zip(
        profile.stations, profile.stations[1:], strict=False
    ):
        drop = upstream.water_level - downstream.water_level
        if drop > threshold:
            drops.append(
                Warning(
                    severity=Severity.WARN,
                    source="elevation.drop_threshold（重写计划 §14.2 跌水>1m 提示口径）",
                    message=(
                        f"{upstream.unit_id!r}→{downstream.unit_id!r} 水面跌落 "
                        f"{drop:.3f} m 超阈值 {threshold:g} m——消能措施提示"
                    ),
                    condition_key=profile.condition_key,
                    affected_unit_ids=(downstream.unit_id,),
                )
            )
        elif drop < 0.0:  # 下游水面高于上游=需提升（自流图不触发，R4）
            static_head = -drop
            pipe_loss = friction_loss(
                {
                    "length": assumption("elevation.pump.pipe_length", assumptions),
                    "diameter": assumption(
                        "elevation.pump.pipe_diameter", assumptions
                    ),
                },
                downstream.design_flow,
                ctx=(downstream.unit_id, profile.condition_key),
                assumptions=assumptions,
            )
            stations.append(
                PumpStation(
                    unit_id=downstream.unit_id,
                    static_head=static_head,
                    total_head=static_head + pipe_loss,
                    design_flow=downstream.design_flow,
                    condition_key=profile.condition_key,
                )
            )
    return PumpingPlan(stations=tuple(stations), drop_warnings=tuple(drops))
