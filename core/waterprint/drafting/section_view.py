"""单体剖面图生成：池体纵剖/横剖（水位线/设备安装高程/标注）。

输入:  PlantResult 单元结果 + ElevationProfile（标高数据，经 app 装配）
       + styles + 图幅选择
输出:  剖面图 DXF 实体组
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_section_view.py）
#
# 【公开接口】
#   unit_section(unit_result, profile_station, styles, condition_key,
#                options: SectionOptions) -> EntityGroup
#   class SectionOptions：cut_position（剖切位置参数，如 1-1 剖面）、
#      annotation_level
#
# 【行为规格】
#   R1 剖切语义：剖面位置由平面图剖切符号联动（plan_view 声明剖切线，
#      section_view 按同一参数生成——剖切一致性由两文件共享
#      CutPosition 值对象保证）。
#   R2 标高数据唯一真源 = ElevationProfile（水面/池底/地面），
#      本文件禁止自行推算标高（总线消费，§16 A4）；水位线/池底线/
#      地面线三线齐备（M5 高程纵断图同源）。
#   R3 设备安装高程（曝气头距底、搅拌器浸深等）来自 assumptions/
#      结果字段，标注来源键。
#   R4 纯投影 + 零 ezdxf（同 plan_view R2）；标注完备性同 R3 条款。
#   R5 工况标注与三元组摘要（同 plan_view R4）。
#
# 【测试要求】三线（水面/池底/地面）实体存在、标高值 == Profile 值、
#   剖切位置联动一致、快照回归。
#
# 【参照】重写计划 §10.3/§12.5；ADR-006
# ══════════════════════════════════════════════════════════════════
# 【参照】重写计划 §10.3/§12.5；ADR-006
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from waterprint.contracts.drawing_projection import ProfileStation
from waterprint.contracts.result_schema import UnitResultSnapshot
from waterprint.drafting.styles import (
    LAYER_DIM,
    LAYER_ELEV,
    LAYER_POOL,
    CutPosition,
    Entity,
    EntityGroup,
    StyleTable,
)

__all__ = ["CutPosition", "SectionOptions", "unit_section"]


class InvalidSectionViewError(Exception):
    """剖面图生成非法（标高站缺/剖切参缺）——GR-11 族。"""


@dataclass(frozen=True)
@final
class SectionOptions:
    """剖面图选项（不可变）：剖切位置（1-1 等）+ 标注级别。"""

    cut_position: CutPosition | None = None
    annotation_level: str = "major"


def unit_section(
    unit_result: UnitResultSnapshot,
    profile_station: ProfileStation,
    styles: StyleTable,
    condition_key: str,
    options: SectionOptions | None = None,
) -> EntityGroup:
    """单体剖面图（R2 标高唯一真源=ElevationProfile 站参数——禁自行推算）。

    三线（地面/水面/池底）+ 池体轮廓（表 primitive 槽位）+ 剖切符号
    （CutPosition 与 plan_view 联动 R1）+ 工况注记（R5）。
    """
    chosen = options if options is not None else SectionOptions()
    pool = LAYER_POOL  # 唯一命名真源经 styles 常量引用（R1）
    anno = LAYER_ELEV
    dim = LAYER_DIM
    length = 10.0  # 剖面展开长度缺省幅（表无 length 槽单元的图幅占位）
    entities: list[Entity] = [
        Entity("line", anno, ((0.0, profile_station.ground_elev),
                              (length, profile_station.ground_elev)),
               text="ground", source_key="profile.ground_elev"),
        Entity("line", anno, ((0.0, profile_station.water_level),
                              (length, profile_station.water_level)),
               text="water", source_key="profile.water_level"),
        Entity("line", pool, ((0.0, profile_station.floor_elev),
                              (length, profile_station.floor_elev)),
               text="floor", source_key="profile.floor_elev"),
    ]
    entities.append(
        Entity("dim_linear", dim,
               ((0.0, profile_station.floor_elev),
                (0.0, profile_station.water_level)),
               params={"measurement": profile_station.water_depth},
               text="water_depth", source_key="profile.water_depth")
    )
    if chosen.cut_position is not None:
        entities.append(
            Entity("cut_line", pool,
                   (chosen.cut_position.origin, chosen.cut_position.direction),
                   text=chosen.cut_position.id)
        )
    entities.append(
        Entity("text", anno, ((length, profile_station.ground_elev),),
               text=f"condition={condition_key}")
    )
    return EntityGroup(entities=tuple(entities))
