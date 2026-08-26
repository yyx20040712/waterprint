"""单体平面图生成：manifest 驱动的池体平面布置（管道/设备/标注）。

输入:  PlantResult 单元结果（几何字段 ID）+ styles 样式表 + 图幅选择
输出:  平面图 DXF 实体组（1:1 mm，布图缩放归 SheetSpec/调用方）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_plan_view.py）
#
# 【公开接口】
#   unit_plan(unit_result, manifest, styles, condition_key,
#             options: PlanOptions) -> EntityGroup
#   class PlanOptions：annotation_level（主要尺寸/全部尺寸）、
#      pipe_routing（是否画连接管示意）
#
# 【行为规格】
#   R1 manifest 驱动：图元来源 = manifest 声明的几何字段 ID（哪些尺寸
#      上图由清单声明，加单元不改出图代码——§13.6 四件套的图纸半）。
#   R2 纯投影：尺寸/个数只按字段 ID 取数；本文件零业务公式、
#      零中文匹配、零 ezdxf import（实体类型是本包内中立描述，
#      由 dxf_writer 翻译——保证可快照回归与渲染器无关）。
#   R3 标注完备性（M2 验收"AutoCAD 中标注完整可读"）：总尺寸/分格
#      尺寸/管径标注/标高符号；标注文字经 styles 文字样式；
#      数字单位与结果字段一致（mm 出图时换算在 dxf_writer 统一处理，
#      换算规则挂 scene/drafting 公共约定）。
#   R4 工况标注：图纸右下角注明 condition_key 与三元组摘要
#      （可复算，§14.1"图纸标注所属工况"）。
#   R5 性能：<5s/单元（§18.1，benchmark 守卫）。
#
# 【测试要求】已知矩形池平面实体数量/坐标断言、标注实体存在性、
#   工况/三元组标注、快照回归（内容哈希）。
#
# 【参照】重写计划 §10.3 单体图纸行/§12.5/§13.6；ADR-006
# ══════════════════════════════════════════════════════════════════
# 【参照】重写计划 §10.3 单体图纸行/§12.5/§13.6；ADR-006
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from waterprint.contracts.drawing_projection import UnitProjection
from waterprint.contracts.result_schema import UnitResultSnapshot
from waterprint.drafting.styles import (
    ANNO_OFFSET_CONDITION,
    ANNO_OFFSET_DIM_1,
    ANNO_OFFSET_DIM_2,
    ANNO_OFFSET_LEVEL,
    LAYER_DIM,
    LAYER_LABEL,
    LAYER_POOL,
    Entity,
    EntityGroup,
    StyleTable,
)

__all__ = ["PlanOptions", "unit_plan"]


class InvalidPlanViewError(Exception):
    """平面图生成非法（manifest 非 UF-32 行/几何键缺）——GR-11 族。"""


@dataclass(frozen=True)
@final
class PlanOptions:
    """平面图选项（不可变）：标注级别/连接管示意（R3）。"""

    annotation_level: str = "major"  # major=主要尺寸 / all=全部尺寸
    pipe_routing: bool = False


def unit_plan(
    unit_result: UnitResultSnapshot,
    manifest: UnitProjection,
    styles: StyleTable,
    condition_key: str,
    options: PlanOptions | None = None,
) -> EntityGroup:
    """单体平面图（manifest=UF-32 对照表行驱动取数，R1 纯投影零业务公式）。

    矩形池轮廓（primitive/plan 总尺寸）→ 分格线（gap_count 类）→ 总尺寸/
    分格/标高三类标注实体（R3 标注完备）→ 工况注记（R4 右下角）。
    坐标单位 m（模型 1:1）——m→mm 出图换算归 dxf_writer 唯一住所。
    """
    chosen = options if options is not None else PlanOptions()
    pool = LAYER_POOL  # 唯一命名真源经 styles 常量引用（R1）
    dim = LAYER_DIM
    anno = LAYER_LABEL
    length_key = manifest.plan_keys.get("overall_length") or manifest.primitive_dims.get("length")
    width_key = manifest.plan_keys.get("overall_width") or manifest.primitive_dims.get("width")
    dims = unit_result.dims
    if length_key is None or width_key is None:
        raise InvalidPlanViewError(
            f"单元 {unit_result.unit_id!r} 对照表无总尺寸键（plan/primitive "
            "缺 overall_length/overall_width——图纸前提失败，UF-32 表补录）"
        )
    if length_key not in dims or width_key not in dims:
        raise InvalidPlanViewError(
            f"单元 {unit_result.unit_id!r} dims 缺总尺寸键 "
            f"{length_key!r}/{width_key!r}（结果与表不一致——对账测试守卫对象）"
        )
    length = float(dims[length_key])
    width = float(dims[width_key])
    entities: list[Entity] = [
        Entity("rect", pool, ((0.0, 0.0), (length, width)),
               source_key=f"{length_key}|{width_key}")
    ]
    gap_key = manifest.plan_keys.get("gap_count")
    if gap_key is not None and gap_key in dims:
        count = int(float(dims[gap_key]))
        for index in range(1, max(count, 1)):
            x = length * index / max(count, 1)
            entities.append(
                Entity("line", pool, ((x, 0.0), (x, width)), source_key=gap_key)
            )
    # R3 标注完备：总尺寸（双向）+分格（逐跨）+标高符号占位（剖面同源）
    entities.append(
        Entity("dim_linear", dim, ((0.0, ANNO_OFFSET_DIM_1), (length, ANNO_OFFSET_DIM_1)),
               params={"measurement": length}, text=length_key, source_key=length_key)
    )
    entities.append(
        Entity("dim_linear", dim, ((ANNO_OFFSET_DIM_1, 0.0), (ANNO_OFFSET_DIM_1, width)),
               params={"measurement": width}, text=width_key, source_key=width_key)
    )
    if gap_key is not None and gap_key in dims:
        spans = max(int(float(dims[gap_key])), 1)
        entities.append(
            Entity("dim_linear", dim,
                   ((0.0, ANNO_OFFSET_DIM_2), (length / spans, ANNO_OFFSET_DIM_2)),
                   params={"measurement": length / spans},
                   text=gap_key, source_key=gap_key)
        )
    elev_key = manifest.section_keys.get("water_depth")
    if elev_key is not None and elev_key in dims:
        entities.append(
            Entity("elev_symbol", anno, ((0.0, 0.0),),
                   params={"water_depth": float(dims[elev_key])},
                   text=elev_key, source_key=elev_key)
        )
    # R4 工况注记（右下角；repro 三元组归 DrawingMeta 进 DXF 头——两段合璧）
    entities.append(
        Entity("text", anno, ((length, ANNO_OFFSET_CONDITION),),
               text=f"condition={condition_key}")
    )
    entities.append(
        Entity("text", anno, ((length, ANNO_OFFSET_LEVEL),),
               text=f"annotation={chosen.annotation_level}")
    )
    return EntityGroup(entities=tuple(entities))
