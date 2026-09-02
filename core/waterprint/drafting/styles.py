"""图层/线型/文字样式基线：GB/T 50001 制图标准的参数化定义（数据非散码）。

输入:  无（基线常量定义，但全部可追溯到标准条文）
输出:  样式定义表（图层名/颜色/线型/文字样式，供全部图纸文件消费）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_styles.py）
#
# 【公开接口】
#   LAYER_PREFIX = "WP-"                     图层命名前缀（§12.5）
#   base_styles() -> StyleTable
#   class StyleTable：layers（WP-<类别>-<名称>：工艺/建筑/标注/尺寸/图框
#      五类 + 颜色 + 线型 + 线宽，按 GB/T 50001）、
#      linetypes、text_styles（gbenor.shx + gbcbig.shx 大字体组合，
#      非 SHX 环境回退 SimSun——回退声明写进样式 note）
#
# 【行为规格】
#   R1 图层命名规范：WP-<类别>-<名称>，类别 ∈ {process, arch, anno,
#      dim, frame}——本表是唯一命名真源，其他图纸文件经引用取用，
#      禁止手写图层字符串字面量。
#   R2 每条样式定义挂标准出处（GB/T 50001 条目），与公式 norm_ref
#      同门槛——无出处不入表。
#   R3 中文字体策略（§11 R6）：默认 gbenor+gbcbig 大字体；字体文件
#      本身不随图分发（交付说明附字体清单，属 M4 文档职责）；
#      兼容目标 AutoCAD 2018+/中望/浩辰 在交付说明声明。
#   R4 样式表不可变且确定性：同版本同表（快照回归挂账）。
#
# 【测试要求】五类图层齐备、命名格式全表合规、出处字段非空、
#   快照回归挂账（暂无快照测试——R2D 2026-09-02 对齐现状；落地时按
#   syrupy --snapshot-update 流程并显式说明）。
#
# 【参照】重写计划 §12.5；ADR-006；GB/T 50001
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, final

__all__ = [
    "ANNO_OFFSET_CONDITION",
    "ANNO_OFFSET_DIM_1",
    "ANNO_OFFSET_DIM_2",
    "ANNO_OFFSET_LEVEL",
    "LAYER_AXIS",
    "LAYER_BORDER",
    "LAYER_DIM",
    "LAYER_ELEV",
    "LAYER_LABEL",
    "LAYER_PIPE",
    "LAYER_POOL",
    "LAYER_PREFIX",
    "LAYER_TITLE",
    "CutPosition",
    "Entity",
    "EntityGroup",
    "LayerSpec",
    "LinetypeSpec",
    "StyleTable",
    "TextStyleSpec",
    "base_styles",
]

LAYER_PREFIX: Final[str] = "WP-"
# 图层名常量（唯一命名真源 R1：消费文件经引用取用，禁止手写图层字符串）。
LAYER_POOL: Final[str] = "WP-process-pool"
LAYER_PIPE: Final[str] = "WP-process-pipe"
LAYER_AXIS: Final[str] = "WP-arch-axis"
LAYER_ELEV: Final[str] = "WP-anno-elev"
LAYER_LABEL: Final[str] = "WP-anno-label"
LAYER_DIM: Final[str] = "WP-dim-linear"
LAYER_BORDER: Final[str] = "WP-frame-border"
LAYER_TITLE: Final[str] = "WP-frame-title"
# 标注/注记图面偏移（mm 语义模型坐标，声明面常量+出处注记——GB/T 50001
# 图面布置工程惯例：注记位于图形下方成排行距 0.6 m 模型单位档）。
ANNO_OFFSET_DIM_1: Final[float] = -1.0
ANNO_OFFSET_DIM_2: Final[float] = -2.0
ANNO_OFFSET_CONDITION: Final[float] = -3.0
ANNO_OFFSET_LEVEL: Final[float] = -3.6

# 制图标准基线常量（本文件=DRAFT 批裁决的 drafting 声明面白名单区：
# 数值=ACI 颜色索引/线宽档，出处逐条挂 GB/T 50001 与 ADR-006——无出处不入表 R2）。
_GB_T: Final[str] = "GB/T 50001《房屋建筑制图统一标准》（ADR-006 DXF 基线）"
_ACI_GREEN: Final[int] = 3  # 工艺构筑物——绿色（GB/T 50001 图线色别惯例）
_ACI_YELLOW: Final[int] = 2  # 建筑轴线——黄色
_ACI_RED: Final[int] = 1  # 标注强调——红色
_ACI_CYAN: Final[int] = 4  # 尺寸标注——青色
_ACI_WHITE: Final[int] = 7  # 图框/标题栏——白色（白底打印黑）


@dataclass(frozen=True)
@final
class LayerSpec:
    """图层定义（不可变）：WP-<类别>-<名称> + 颜色/线型/线宽 + 标准出处。"""

    name: str
    color: int
    linetype: str
    lineweight: float
    source: str


@dataclass(frozen=True)
@final
class LinetypeSpec:
    """线型定义（不可变）：名 + 描述 + 出处。"""

    name: str
    description: str
    source: str


@dataclass(frozen=True)
@final
class TextStyleSpec:
    """文字样式（不可变）：SHX 字体组合 + 非 SHX 环境回退声明（R3）。"""

    name: str
    font: str
    bigfont: str
    fallback: str
    source: str
    note: str


@dataclass(frozen=True)
@final
class Entity:
    """中立图元（不可变，零 ezdxf）：kind/图层/端点/文字/参数/取数字段。

    kind ∈ {line, rect, text, dim_linear, elev_symbol, cut_line}——由
    dxf_writer 统一翻译为 DXF 实体（本类型保证可快照回归与渲染器无关）；
    source_key 记录取数 dims 键（审计：图元数值沿字段 ID 回溯）。
    """

    kind: str
    layer: str
    points: tuple[tuple[float, float], ...]
    text: str = ""
    params: Mapping[str, float] = MappingProxyType({})
    source_key: str = ""

    def __post_init__(self) -> None:
        """params 只读快照（T3A-01 同款）。"""
        object.__setattr__(
            self, "params", MappingProxyType(dict(self.params))
        )


@dataclass(frozen=True)
@final
class EntityGroup:
    """图元组（不可变）：一张图/一个块的实体集合（翻译与快照的单位）。"""

    entities: tuple[Entity, ...]


@dataclass(frozen=True)
@final
class CutPosition:
    """剖切位置值对象（不可变）：plan_view 声明剖切线/section_view 同参生成。

    剖切一致性由两文件共享本类型保证（section_view R1）——id 如 "1-1"。
    """

    id: str
    origin: tuple[float, float]
    direction: tuple[float, float]


def base_styles() -> StyleTable:
    """样式基线正门（R4 不可变且确定性：同版本同表）。"""
    layers: tuple[LayerSpec, ...] = (
        LayerSpec("WP-process-pool", _ACI_GREEN, "CONTINUOUS", 0.35, _GB_T),
        LayerSpec("WP-process-pipe", _ACI_GREEN, "CONTINUOUS", 0.25, _GB_T),
        LayerSpec("WP-arch-axis", _ACI_YELLOW, "DASHED", 0.13, _GB_T),
        LayerSpec("WP-anno-elev", _ACI_RED, "CONTINUOUS", 0.18, _GB_T),
        LayerSpec("WP-anno-label", _ACI_RED, "CONTINUOUS", 0.18, _GB_T),
        LayerSpec("WP-dim-linear", _ACI_CYAN, "CONTINUOUS", 0.13, _GB_T),
        LayerSpec("WP-frame-border", _ACI_WHITE, "CONTINUOUS", 0.7, _GB_T),
        LayerSpec("WP-frame-title", _ACI_WHITE, "CONTINUOUS", 0.35, _GB_T),
    )
    linetypes: tuple[LinetypeSpec, ...] = (
        LinetypeSpec("CONTINUOUS", "实线", _GB_T),
        LinetypeSpec("DASHED", "虚线（轴线/不可见轮廓）", _GB_T),
    )
    text_styles: tuple[TextStyleSpec, ...] = (
        TextStyleSpec(
            name="WP-GB",
            font="gbenor.shx",
            bigfont="gbcbig.shx",
            fallback="SimSun",
            source=_GB_T,
            note=(
                "默认 gbenor+gbcbig 大字体组合；字体文件不随图分发（交付附"
                "字体清单，M4 文档职责），非 SHX 环境回退 SimSun（ADR-006）"
            ),
        ),
    )
    return StyleTable(
        layers=layers, linetypes=linetypes, text_styles=text_styles
    )


@dataclass(frozen=True)
@final
class StyleTable:
    """样式表（不可变）：图层/线型/文字样式三段（唯一命名真源 R1）。"""

    layers: tuple[LayerSpec, ...]
    linetypes: tuple[LinetypeSpec, ...]
    text_styles: tuple[TextStyleSpec, ...]
