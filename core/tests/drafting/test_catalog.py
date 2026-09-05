"""catalog 镜像测试：图纸目录 sheet（表题/表线/表头/数据文字+包围盒下方派生放置）。

输入:  waterprint.drafting.catalog 公开符号
输出:  目录表契约断言（结构断言+确定性 digest 形态+放置派生，简报 M6 D5；
       案乙 B 形态=总图文件内嵌目录页实体——接线面断言在
       tests/app/test_app_enumeration.py 总图用例）
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
from typing import get_args

import pytest

from waterprint.drafting.styles import (
    LAYER_BORDER,
    LAYER_LABEL,
    LAYER_TITLE,
    Entity,
    EntityGroup,
    base_styles,
)

_mod = importlib.import_module("waterprint.drafting.catalog")
catalog_sheet = getattr(_mod, "catalog_sheet", None)
sheet_origin_below = getattr(_mod, "sheet_origin_below", None)
CatalogRow = getattr(_mod, "CatalogRow", None)

pytestmark = pytest.mark.skipif(
    None in (catalog_sheet, sheet_origin_below, CatalogRow),
    reason="实现未就绪：waterprint.drafting.catalog（M6 案乙）",
)

_ROWS = (
    ("1", "01", "全厂总图", "1:100"),
    ("2", "02", "municipal_cass", "1:100"),
)
_ORIGIN = (3.0, -12.0)


def _sheet() -> EntityGroup:
    return catalog_sheet(_ROWS, _ORIGIN)


def test_entrypoint_frozen() -> None:
    """D2 入口冻结：catalog_sheet 五参（默认列宽/行高/表题）+sheet_origin_below 两参+CatalogRow 四 str。"""
    assert callable(catalog_sheet) and callable(sheet_origin_below)
    signature = inspect.signature(catalog_sheet)
    assert list(signature.parameters) == [
        "rows", "origin_xy", "col_widths", "row_h", "title",
    ]
    assert signature.parameters["col_widths"].default == (1.5, 2.0, 5.0, 1.5)
    assert signature.parameters["row_h"].default == 0.8
    assert signature.parameters["title"].default == "图纸目录"
    origin_signature = inspect.signature(sheet_origin_below)
    assert list(origin_signature.parameters) == ["entities", "gap"]
    assert origin_signature.parameters["gap"].default == 1.0
    target = getattr(CatalogRow, "__value__", CatalogRow)  # PEP 695 type 别名取 value
    assert get_args(target) == (str, str, str, str)  # 序号/图号/图名/比例


def test_layers_subset_no_new_layers() -> None:
    """R3 层用法：实体层 ⊆ base_styles 八层真源（零新层零 styles 触碰——镜像 test_site_plan 层守卫）。"""
    group = _sheet()
    known = {layer.name for layer in base_styles().layers}
    assert {e.layer for e in group.entities} <= known
    assert {e.layer for e in group.entities} == {LAYER_BORDER, LAYER_LABEL, LAYER_TITLE}


def test_table_geometry() -> None:
    """R2 几何：横线 R+1 条（y=oy-k×row_h）/竖线 5 条（x=列宽前缀和含两端）/实体总数算式。"""
    group = _sheet()
    border_lines = [e for e in group.entities
                    if e.layer == LAYER_BORDER and e.kind == "line"]
    horizontal = sorted(
        (e.points[0][1] for e in border_lines
         if e.points[0][1] == e.points[1][1]),
        reverse=True,
    )
    assert horizontal == pytest.approx([-12.0, -12.8, -13.6, -14.4])  # R=3 行→4 横线
    for e in border_lines:  # 横线两端 x=表宽 Σcol_widths=10
        if e.points[0][1] == e.points[1][1]:
            assert sorted(p[0] for p in e.points) == pytest.approx([3.0, 13.0])
    vertical_xs = sorted({e.points[0][0] for e in border_lines
                          if e.points[0][0] == e.points[1][0]})
    assert vertical_xs == pytest.approx([3.0, 4.5, 6.5, 11.5, 13.0])  # 前缀和含两端
    for e in border_lines:  # 竖线纵贯表体 [oy-R×row_h, oy]
        if e.points[0][0] == e.points[1][0]:
            assert sorted(p[1] for p in e.points) == pytest.approx([-14.4, -12.0])
    assert len(group.entities) == 1 + 4 + 5 + 4 * 3  # 表题 1+横线 R+1+竖线 5+文字 4R


def test_header_and_cell_texts() -> None:
    """表头四格=序号/图号/图名/比例（TITLE 层）；数据格=行值原文（LABEL 层）；锚=格左下内缩。"""
    group = _sheet()
    texts = [e for e in group.entities if e.kind == "text"]
    header = [e for e in texts if e.layer == LAYER_TITLE and e.text != "图纸目录"]
    assert [e.text for e in header] == ["序号", "图号", "图名", "比例"]
    data = [e for e in texts if e.layer == LAYER_LABEL]
    assert [e.text for e in data] == [value for row in _ROWS for value in row]
    assert data[0].points[0] == pytest.approx(
        (3.0 + 0.15, -12.0 - 2 * 0.8 + 0.25 * 0.8)
    )  # 首格=首数据行左列（表头下一行，row_index=1→(1+1)×row_h）
    assert data[-1].points[0] == pytest.approx(
        (11.5 + 0.15, -12.0 - 3 * 0.8 + 0.25 * 0.8)
    )  # 末格=末行末列（比例列，图名列前缀和 6.5+5.0）


def test_title_annotation() -> None:
    """R1 表题：title 透传（默认『图纸目录』），层=TITLE，锚=表体上缘上方 0.4；空 rows=仅表头表不抛。"""
    group = _sheet()
    titles = [e for e in group.entities if e.text == "图纸目录"]
    assert len(titles) == 1
    assert titles[0].layer == LAYER_TITLE and titles[0].source_key == "catalog"
    assert titles[0].points[0] == pytest.approx((3.0, -12.0 + 0.4))
    custom = catalog_sheet((), (0.0, 0.0), title="DRAWING LIST")
    assert [e.text for e in custom.entities if e.kind == "text"] == [
        "DRAWING LIST", "序号", "图号", "图名", "比例",
    ]
    assert len(custom.entities) == 1 + 2 + 5 + 4  # R=1（仅表头）→表题+2 横线+5 竖线+4 格


def _canonical(group: EntityGroup) -> str:
    """sorted entities 归一字符串（kind/层/文字/键/坐标 round10/参数）——防漂移基。"""

    def one(entity: object) -> str:
        pts = ";".join(
            f"{round(x, 10)!r},{round(y, 10)!r}" for x, y in entity.points
        )
        params = ";".join(
            f"{key}={round(value, 10)!r}"
            for key, value in sorted(entity.params.items())
        )
        return "|".join(
            (entity.kind, entity.layer, entity.text, entity.source_key, pts, params)
        )

    return "\n".join(sorted(one(e) for e in group.entities))


def _digest(group: EntityGroup) -> str:
    return hashlib.sha256(_canonical(group).encode("utf-8")).hexdigest()[:16]


def test_determinism_and_digest_shape() -> None:
    """确定性：双调实体逐元组全等+digest 同（形态锚沿 test_site_plan _digest 先例——首末实体+总数稳定）。"""
    first = _sheet()
    second = _sheet()
    assert first.entities == second.entities  # frozen dataclass 逐元组全等
    assert _digest(first) == _digest(second)
    assert first.entities[0].text == "图纸目录"  # 段序首=表题
    assert first.entities[-1].text == "1:100"  # 段序末=末行末格（比例列）
    assert len(first.entities) == 1 + 4 + 5 + 4 * (1 + len(_ROWS))  # 文字 4R（R 含表头行）


def test_sheet_origin_below_placement() -> None:
    """R1 放置派生：返回 (min_x, min_y-gap)=目录表左上角（表体向下延伸→表恒在包围盒下方）；空实体组=原点邻域。"""
    entities = (
        Entity("line", LAYER_BORDER, ((2.0, -5.0), (8.0, -5.0))),
        Entity("text", LAYER_LABEL, ((9.0, 3.0),), text="note"),
    )
    assert sheet_origin_below(entities) == (2.0, -6.0)  # gap 默认 1.0
    assert sheet_origin_below(entities, gap=2.5) == (2.0, -7.5)
    assert sheet_origin_below(()) == (0.0, -1.0)  # 空=原点下方 gap（空 site 先例）
    origin = sheet_origin_below(entities)
    group = catalog_sheet(_ROWS, origin)
    body_top = max(
        y for e in group.entities if e.layer == LAYER_BORDER for _, y in e.points
    )
    assert body_top == pytest.approx(-6.0)  # 表体顶=包围盒底-gap
    assert body_top < min(p[1] for p in entities[0].points)  # 恒在图内容之下
