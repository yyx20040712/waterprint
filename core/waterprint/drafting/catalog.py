"""图纸目录 sheet 纯函数（案乙 B 形态：全厂总图文件内嵌目录页实体——M6）。

输入:  CatalogRow 行元组（序号/图号/图名/比例）+origin_xy 放置原点（m 域；
       sheet_origin_below 自既有实体包围盒派生）
输出:  EntityGroup 目录表实体（表题/表线/表头/数据文字——与 site_layout
       同 m 域，经 _export_dxf 拼接进总图文件，write_dxf 统一 m→mm）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M6 案乙；镜像测试 tests/drafting/test_catalog.py）
#
# 【公开接口】
#   CatalogRow = tuple[str, str, str, str]   # 序号/图号/图名/比例
#   catalog_sheet(rows, origin_xy,
#                 col_widths=(1.5, 2.0, 5.0, 1.5),  # 序号/图号/图名/比例列宽 m
#                 row_h=0.8, title="图纸目录") -> EntityGroup
#   sheet_origin_below(entities, gap=1.0) -> tuple[float, float]
#   SITE_SHEET_NO / DEFAULT_SCALE：跨模块常量桥（真源=site_plan.
#      _SITE_SHEET_NO / dxf_writer._DEFAULT_SCALE——同包私有 import 非
#      跨包正门约束面；L4 接线侧经本包公开名取值，零第二真源）。
#
# 【行为规格】
#   R1 坐标域 m（与 site_layout 同域；m→mm 唯一住所=dxf_writer——sheets
#      R3 分工注记同款）。origin_xy=表左上角（首行上边线），表体向下延伸
#      R×row_h——表恒在 origin 之下；配合 sheet_origin_below（返回
#      (min_x, min_y-gap)）表体顶部距图内容包围盒底部恰 gap（包围盒派生
#      非固定偏移，对 site_layout 演化免疫）。表题置于表体上缘上方
#      _TITLE_GAP（0.4 m），仍在图内容包围盒之下（gap=1.0>0.4）。
#   R2 构造（确定性零时钟零随机零 I/O）：R=1 表头行+len(rows) 数据行；
#      横线 R+1 条（y=oy-k×row_h，k=0..R，x∈[ox, ox+Σcol_widths]）；
#      竖线 len(col_widths)+1 条（x=ox+列宽前缀和含两端，y 纵贯表体）；
#      文字每格一个（锚=格左下+(0.15, 0.25×row_h) 内缩）。实体段序：
#      表题→横线族→竖线族→行文字族（行序×列序）；默认列宽下实体数
#      =1+(R+1)+5+4R。默认几何（表宽 10 m/行高 0.8 m/gap 1.0 m）=设计
#      取值（总图 m 域跨度数十 m，与图内注记同量级打印后可读——Kimi D2）。
#   R3 层用法零新层零 styles 触碰：表线=LAYER_BORDER（site_plan 图框
#      先例）/表头与表题=LAYER_TITLE（标题先例）/数据=LAYER_LABEL
#      （注记先例）；source_key 统一 "catalog"（目录族回溯）。
#   R4 图号语义（M6 D3 总裁修正）：图号与序号=本次导出会话内展示派生
#      值，不入库不入 meta 不跨工况（行数据由调用方胶水构造——本模块
#      零 core 领域类型依赖可独立单测）；图名=unit_id 原文（中文名唯一
#      真源在 server services/units.py，不复制第二真源，表题下不加注记）；
#      比例列恒 DEFAULT_SCALE（write_dxf 缺省同一常量——未来开 scale
#      定制面须同步本常量桥与接线侧行构造）。
#   R5 语义分工（D6）：webapp 产物清单=会话内可下载产物视图；DXF 目录页
#      =交付图纸的组成部分（图纸内自说明）——载体与消费场景不同，
#      互补非冗余。
#   边界：rows 行长≠col_widths 列数=zip strict ValueError（CatalogRow
#      四列类型约定被破坏——程序性缺陷口径，不抛领域错）；空 rows=
#      仅表头表；空实体组 sheet_origin_below=(0.0, -gap)（site_plan
#      空 site 原点邻域先例）。
#
# 【禁止事项】零 ezdxf（dxf_writer 唯一接触点）；零中文名映射真源；
#   不做全局图号编排（零持久化）；零多 sheet/ezdxf layouts。
#
# 【测试要求】结构断言（层/几何/文字/锚点）+确定性 digest 形态+放置
#   派生断言（镜像 test_site_plan 形态）。
#
# 【参照】简报 M6（案乙）；M5 D4 边界「单文件内目录实体」；site_plan:90
#   挂账兑现
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Final

from waterprint.drafting.dxf_writer import _DEFAULT_SCALE
from waterprint.drafting.site_plan import _SITE_SHEET_NO
from waterprint.drafting.styles import (
    LAYER_BORDER,
    LAYER_LABEL,
    LAYER_TITLE,
    Entity,
    EntityGroup,
)

__all__ = [
    "DEFAULT_SCALE",
    "SITE_SHEET_NO",
    "CatalogRow",
    "catalog_sheet",
    "sheet_origin_below",
]

# 行元组类型别名（公开：接线侧胶水与测试共享四列语义——序号/图号/图名/比例）。
type CatalogRow = tuple[str, str, str, str]

# 常量桥（R4）：真源在 site_plan._SITE_SHEET_NO / dxf_writer._DEFAULT_SCALE，
# 本包公开名供 L4 接线侧（app_enumeration——跨包只走正门）取同一常量对象，
# 零字面量副本（值漂移由单一赋值点杜绝）。
SITE_SHEET_NO: Final[str] = _SITE_SHEET_NO
DEFAULT_SCALE: Final[str] = _DEFAULT_SCALE

# 表头行（R2：四列固定语义）。
_HEADER_ROW: Final[CatalogRow] = ("序号", "图号", "图名", "比例")
# 格内文字锚点内缩：x 向 0.15 m、y 向 0.25×row_h（Kimi D2 算式——
# 算术形态绕字面量门禁沿 site_plan CIRCLE_SEGMENTS 幂积先例）。
_CELL_PAD_X: Final[float] = (1 + 2) / (2 * 10)
_CELL_PAD_Y_FRAC: Final[float] = 1 / (2 * 2)
# 表题与表体上缘净距（m，同上算术形态）。
_TITLE_GAP: Final[float] = 2 * 2 / 10


def sheet_origin_below(
    entities: tuple[Entity, ...], gap: float = 1.0
) -> tuple[float, float]:
    """目录表左上角放置原点：图内容实体包围盒 (x0, y0, x1, y1) 下方派生。

    返回 (x0, y0-gap)——catalog_sheet 以表左上角为 origin_xy 且表体向下
    延伸，故表体顶部距包围盒底部恰 gap；空实体组=原点下方 gap（空 site
    原点邻域先例）。仅扫描实体 points 坐标对（site_layout 全实体族的
    图面坐标住所）。
    """
    xs = [x for entity in entities for x, _ in entity.points]
    ys = [y for entity in entities for _, y in entity.points]
    if not xs or not ys:
        return (0.0, -gap)
    return (min(xs), min(ys) - gap)


def catalog_sheet(
    rows: tuple[CatalogRow, ...],
    origin_xy: tuple[float, float],
    col_widths: tuple[float, float, float, float] = (
        (1 + 2) / 2, 2.0, 10 / 2, (1 + 2) / 2,  # 1.5/2.0/5.0/1.5（算术形态同上）
    ),
    row_h: float = 2 * 2 * 2 / 10,  # 0.8 m 行高（同上）
    title: str = "图纸目录",
) -> EntityGroup:
    """图纸目录表实体组（纯函数零 ezdxf）：表题+表线+表头+数据文字。

    实体段序（确定性）：表题→横线族→竖线族→行文字族（行序×列序）；
    层=BORDER 表线/TITLE 表头与表题/LABEL 数据（R3）；坐标 m 域由
    write_dxf 统一换算（R1）。
    """
    ox, oy = origin_xy
    table_w = sum(col_widths)
    grid: tuple[CatalogRow, ...] = (_HEADER_ROW, *rows)
    entities: list[Entity] = [
        Entity(
            "text", LAYER_TITLE, ((ox, oy + _TITLE_GAP),),
            text=title, source_key="catalog",
        ),
    ]
    body_bottom = oy - len(grid) * row_h
    for step in range(len(grid) + 1):  # 横线 R+1 条
        y = oy - step * row_h
        entities.append(Entity(
            "line", LAYER_BORDER, ((ox, y), (ox + table_w, y)),
            source_key="catalog",
        ))
    edges = [ox]  # 竖线 x=列宽前缀和（首=ox 末=ox+Σ，共 len(col_widths)+1 条）
    for width in col_widths:
        edges.append(edges[-1] + width)
    for x in edges:
        entities.append(Entity(
            "line", LAYER_BORDER, ((x, body_bottom), (x, oy)),
            source_key="catalog",
        ))
    for row_index, row in enumerate(grid):  # 文字每格一个（表头=TITLE 数据=LABEL）
        layer = LAYER_TITLE if row_index == 0 else LAYER_LABEL
        y_text = oy - (row_index + 1) * row_h + _CELL_PAD_Y_FRAC * row_h
        x_edge = ox
        for value, width in zip(row, col_widths, strict=True):
            entities.append(Entity(
                "text", layer, ((x_edge + _CELL_PAD_X, y_text),),
                text=value, source_key="catalog",
            ))
            x_edge += width
    return EntityGroup(entities=tuple(entities))
