"""内部构件布局：曝气头/搅拌器/填料的数量与摆放（实例数来自计算结果）。

输入:  单元结果（设备台数/个数/间距类字段 ID）+ assumptions
输出:  实例化图元组（instance_count + 阵列变换，GPU InstancedMesh 数据源）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/geometry/test_internals.py）
#
# 【公开接口】
#   internal_instances(unit_result, assumptions) -> tuple[InstanceGroup, ...]
#   class InstanceGroup：semantic（aerator/paddle/media/gate/pipe）、
#       prototype（Primitive）、count（实例数）、placements
#       （阵列参数：origin/step/rows/cols——展开由渲染层或显式列表）
#
# 【行为规格】
#   R1 数量唯一真源 = 计算结果字段（曝气头个数、搅拌器台数、填料体积
#      换算个数等已在单元 compute 完成）；几何层只摆放不计数
#      （双源漂移根除，§10.5）。
#   R2 布局规则（曝气头均布行列、填料支架层高、搅拌器安装位）来自
#      assumptions/coefficients（出处入库），节点标注来源键。
#   R3 阵列表达优先于逐实例列表：千级构件用 (origin, step, rows, cols)
#      参数化（数据量 O(1)）；不规则摆放才允许显式坐标列表。
#   R4 语义标签稳定集合：aerator/paddle/media/gate/opening/pipe…
#      新增语义先登记 scene.py 规格（前端材质映射依赖）。
#   R5 开口/穿孔（CSG 场景）：kind=opening 的实例组显式声明，
#      供前端 three-bvh-csg 定点使用（§12.6 CSG 仅限开口）。
#
# 【测试要求】count == 结果字段值、阵列参数展开数 == count、
#   语义标签 ∈ 稳定集合、来源键标注。
#
# 【参照】重写计划 §10.5/§12.6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from waterprint.contracts.drawing_projection import PROJECTION_TABLE
from waterprint.contracts.result_schema import UnitResultSnapshot
from waterprint.geometry.pools import Primitive
from waterprint.registry.assumptions import assumption

__all__ = ["InstanceGroup", "internal_instances"]

_SPACING_KEY = "geometry.pool.spacing"


@dataclass(frozen=True)
@final
class InstanceGroup:
    """实例组（不可变）：语义+原型+数量+阵列参数（O(1) 数据量，R3）。

    placements 键集：origin（原点二元组）/step（行列步距二元组）/rows
    （行数单元组）/cols（列数单元组）/source_key（取数 dims 键字符串型
    装载）——阵列展开 rows×cols ≥ count（末行缺额 < cols），显式坐标
    列表保留给不规则摆放（本 v1 全阵列）。
    """

    semantic: str
    prototype: Primitive
    count: int
    placements: Mapping[str, object]

    def __post_init__(self) -> None:
        """placements 只读快照 + count 非负校验（GR-02 精神）。"""
        if self.count < 0:
            raise ValueError(
                f"实例数非负不变量破坏：{self.semantic}={self.count}"
            )
        object.__setattr__(
            self, "placements", MappingProxyType(dict(self.placements))
        )


def internal_instances(
    unit_result: UnitResultSnapshot, assumptions: Mapping[str, float]
) -> tuple[InstanceGroup, ...]:
    """内部构件实例组（R1 数量唯一真源=对照表 instance_counts→dims 值）。

    阵列参数（origin/step/rows/cols）按 geometry.pool.spacing（assumptions
    出处入库）近方阵推导——rows×cols ≥ count、缺额 < cols；step 尺寸
    同源 spacing（原型盒以步距为界——摆放不计数，计数唯一在结果字段）。
    """
    projection = PROJECTION_TABLE.get(unit_result.unit_id)
    if projection is None or not projection.instance_counts:
        return ()  # 无实例计数键单元（显式空组——数量真源在结果字段）
    dims = unit_result.dims
    spacing = assumption(_SPACING_KEY, assumptions)
    groups: list[InstanceGroup] = []
    for semantic, count_key in sorted(projection.instance_counts.items()):
        if count_key not in dims:
            continue  # 对账测试守卫覆盖（表键必在 dims）；防御位
        count = max(int(float(dims[count_key])), 0)
        if count == 0:
            continue
        cols = max(math.ceil(math.sqrt(count)), 1)
        rows = max(math.ceil(count / cols), 1)
        groups.append(
            InstanceGroup(
                semantic=semantic,
                prototype=Primitive(
                    "box",
                    {"length": spacing, "width": spacing, "depth": spacing},
                    semantic,
                ),
                count=count,
                placements={
                    "origin": (0.0, 0.0),
                    "step": (spacing, spacing),
                    "rows": rows,
                    "cols": cols,
                    "source_key": count_key,
                },
            )
        )
    return tuple(groups)
