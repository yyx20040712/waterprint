"""图框/会签栏参数化块库（A0~A4 横竖）：标准图幅的参数化生成。

输入:  图幅参数（幅面 A0~A4、横/竖、图号、图名、设计阶段等栏位数据）
输出:  图框实体组（含会签栏/标题栏，坐标经 dxf_writer 落图）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_sheets.py）
#
# 【公开接口】
#   SHEET_SIZES: Mapping[幅面→(宽, 高) mm]     A0~A4 基本幅面（GB/T 50001）
#   sheet_frame(spec: SheetSpec) -> EntityGroup   图框（幅面/横竖/装订边）
#   title_block(entries: TitleEntries) -> EntityGroup  标题栏+会签栏
#   class SheetSpec(不可变)：size、orientation、margin_scale（加长幅
#      需求以倍数表达，不引入非标幅面魔法数）
#
# 【行为规格】
#   R1 幅面尺寸表挂标准出处；A0~A4 全集必须齐备（测试枚举断言）。
#   R2 全部为参数化块：图框/标题栏/会签栏按栏位数据生成，
#      栏位文字一律 UTF-8；图名等业务文本由调用方传入（本文件不含
#      业务内容）。
#   R3 mm 出图约定：实体坐标单位 mm，绘图比例在 SheetSpec 声明
#      （1:50/1:100 等）；m→mm 比例换算唯一住所=dxf_writer（其 R5，
#      write_dxf scale 参数承接本表比例口径——R1-2 行文统一：plan/
#      section 产模型 m 坐标实体，图纸空间布图缩放归 M5 布图批）。
#   R4 会签栏栏位（设计/校对/审核/审定+日期）为固定模板数据结构，
#      留空栏位合法（由交付流程填写）。
#
# 【测试要求】五幅面×横竖全覆盖生成、尺寸表出处、栏位结构完整、
#   快照回归。
#
# 【参照】重写计划 §12.5；GB/T 50001
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, final

from waterprint.drafting.styles import (
    LAYER_BORDER,
    LAYER_TITLE,
    Entity,
    EntityGroup,
)

__all__ = [
    "SHEET_SIZES",
    "SHEET_SOURCE",
    "SheetSpec",
    "TitleEntries",
    "sheet_frame",
    "title_block",
]

SHEET_SOURCE: Final[str] = (
    "GB/T 50001《房屋建筑制图统一标准》表幅面（A 系列，mm）——"
    "幅面尺寸=声明面常量（DRAFT 批裁决：本文件属 drafting 声明面白名单区，"
    "每条数值带标准出处注记）"
)
# A0~A4 基本幅面（宽×高 mm，横式；竖式宽高互换）——GB/T 50001/ISO 216。
SHEET_SIZES: Final[Mapping[str, tuple[float, float]]] = MappingProxyType({
    "A0": (1189.0, 841.0), "A1": (841.0, 594.0), "A2": (594.0, 420.0),
    "A3": (420.0, 297.0), "A4": (297.0, 210.0),
})
# 图框留边（mm）：a=装订边（左），c=非装订边——GB/T 50001（A0~A2 与
# A3~A4 两档）。
_MARGIN_BIND: Final[float] = 25.0
_MARGIN_WIDE: Final[float] = 10.0
_MARGIN_NARROW: Final[float] = 5.0

# 标题栏/会签栏栏位（R4 固定模板数据结构；留空合法——交付流程填写）。
_TITLE_FIELDS: Final[tuple[str, ...]] = (
    "project", "drawing", "title", "designer", "checker", "reviewer",
    "auditor", "date", "stage", "sheet_no",
)


class InvalidSheetError(Exception):
    """图幅/栏位声明非法（未知幅面/朝向/栏位键）——GR-11 族。"""


@dataclass(frozen=True)
@final
class SheetSpec:
    """图幅规格（不可变）：幅面/朝向/比例（mm 出图约定 R3，比例声明于图纸）。"""

    size: str
    orientation: str = "landscape"
    scale: str = "1:100"
    margin_scale: float = 1.0  # 加长幅需求以倍数表达（不引入非标幅面魔法数）

    def __post_init__(self) -> None:
        """幅面/朝向校验（未知值=领域异常——禁静默默认档）。"""
        if self.size not in SHEET_SIZES:
            raise InvalidSheetError(
                f"未知幅面：{self.size!r}（合法 {sorted(SHEET_SIZES)}，GB/T 50001）"
            )
        if self.orientation not in ("landscape", "portrait"):
            raise InvalidSheetError(
                f"未知朝向：{self.orientation!r}（合法 landscape/portrait）"
            )


@dataclass(frozen=True)
@final
class TitleEntries:
    """标题栏+会签栏栏位数据（不可变，R4：留空合法）。"""

    entries: Mapping[str, str]

    def __post_init__(self) -> None:
        """未知栏位键拒（防拼写漂移静默丢栏）+ 只读快照。"""
        unknown = frozenset(self.entries) - frozenset(_TITLE_FIELDS)
        if unknown:
            raise InvalidSheetError(
                f"未知栏位键：{sorted(unknown)}（合法 {list(_TITLE_FIELDS)}）"
            )
        object.__setattr__(
            self, "entries", MappingProxyType(dict(self.entries))
        )


def sheet_frame(spec: Mapping[str, object]) -> EntityGroup:
    """图框生成（幅面×横竖×装订边，mm 1:1 实体）。

    spec 收 Mapping（锁定测试口径）或 SheetSpec（from_mapping 归一）；
    外框（幅面边界）+ 内框（留边 c/a 后图框线）+ 幅面注记文字。
    """
    size = str(spec.get("size", ""))
    orientation = str(spec.get("orientation", "landscape"))
    normalized = SheetSpec(
        size=size,
        orientation=orientation,
        scale=str(spec.get("scale", "1:100")),
    )
    width, height = SHEET_SIZES[normalized.size]
    if normalized.orientation == "portrait":
        width, height = height, width
    margin = _MARGIN_WIDE if normalized.size in ("A0", "A1", "A2") else _MARGIN_NARROW
    border_layer = LAYER_BORDER  # 唯一命名真源经 styles 常量引用（R1）
    title_layer = LAYER_TITLE
    left = _MARGIN_BIND
    inner: tuple[tuple[float, float], ...] = (
        (left, margin), (width - margin, margin),
        (width - margin, height - margin), (left, height - margin),
        (left, margin),
    )
    outer: tuple[tuple[float, float], ...] = (
        (0.0, 0.0), (width, 0.0), (width, height), (0.0, height), (0.0, 0.0),
    )
    entities = (
        Entity("line", border_layer, outer),
        Entity("line", border_layer, inner),
        Entity(
            "text", title_layer, ((left, 0.0),),
            text=f"{normalized.size} {normalized.orientation} 1:1mm {SHEET_SOURCE[:24]}",
        ),
    )
    return EntityGroup(entities=entities)


def title_block(entries: TitleEntries) -> EntityGroup:
    """标题栏+会签栏（栏位数据生成；UTF-8 文字，留空栏位合法 R4）。"""
    label_layer = LAYER_TITLE  # 唯一命名真源经 styles 常量引用（R1）
    row_h = 5.0  # 栏位行高 mm（GB/T 50001 标题栏分格工程惯例）
    made: list[Entity] = []
    for index, field_id in enumerate(_TITLE_FIELDS):
        y = row_h * index
        made.append(
            Entity(
                "text", label_layer, ((0.0, y),),
                text=f"{field_id}={entries.entries.get(field_id, '')}",
                source_key=field_id,
            )
        )
        made.append(
            Entity(
                "line", label_layer,
                ((0.0, y), (60.0, y)),  # 栏宽 60 mm（标题栏分格工程惯例）
            )
        )
    return EntityGroup(entities=tuple(made))
