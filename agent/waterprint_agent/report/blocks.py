"""说明书块类型定义与装配辅助（预算拆分件——自 build.py 纯搬迁）。

路径:   waterprint_agent/report/blocks.py
职责:   ReportAST 的块类型族（TableBlock/NumberLine/NarrativeSlot/
        FigureRef/NoteLine/Section/Chapter）+EstimateRowLike/
        EstimateSheetLike 协议+纯投影辅助（单元显示名/工况标签/锚定
        索引/dims 字段排序/单元展示序）——章节装配（build.py）的消费面。
禁区:   禁 import server／fastmcp／core L1-L3（只许 waterprint.app 正门
        与 waterprint.contracts.*）；禁 IO——纯函数，不读不写文件。
参照:   v2 设计书 D5①/D5④；AI1-INTEG-2026-09-13 §3 预裁决①（拆分
        零行为变化——既有 62 测试不动全绿为验收门）。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final

from waterprint.contracts.manifest import UnitManifest
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.quantity import CANONICAL_UNITS
from waterprint.contracts.result_schema import PlantResult, UnitResultSnapshot

__all__ = [
    "DESIGN_KEY",
    "Chapter",
    "EstimateRowLike",
    "EstimateSheetLike",
    "FigureRef",
    "NarrativeSlot",
    "NoteLine",
    "NumberLine",
    "ReportAST",
    "Section",
    "TableBlock",
    "anchor_index",
    "condition_label",
    "dim_label_unit",
    "indicator_of",
    "ordered_dim_fields",
    "ordered_units",
    "unit_zh",
]

# 设计工况键（主尺寸／负荷一律以 design 档为准——D5① 第 4 章数据源）
DESIGN_KEY = "design"

# 进水／内置节点 id（第 2 章承接，不入第 4 章逐单元）
_INLET_ID = "inlet"

# 污泥线前缀（第 3 章泥线表分组依据）
_SLUDGE_PREFIX = "sludge_"

# v1 市政模板单元中文名（声明面誊录 docs/structure-graph.md §3 总表——与
# server services/units.py 同源；新单元须同步登记，缺席回落 unit_id 原文）
_UNIT_NAMES_ZH: Mapping[str, str] = {
    "municipal_cugeshan": "粗格栅",
    "municipal_xigeshan": "细格栅",
    "municipal_chenshachi": "旋流沉砂池",
    "municipal_chuchenchi": "辐流初沉池",
    "municipal_tiaojiechi": "调节池",
    "municipal_aao": "AAO 生物池",
    "municipal_cass": "CASS 生物池",
    "municipal_gaomidu": "高密沉淀池",
    "municipal_vxinglvchi": "V 型滤池",
    "municipal_ziwai": "紫外消毒",
    "municipal_erchunchi": "辐流二沉池",
    "municipal_bashi_jiliangcao": "巴歇尔计量槽",
    "municipal_wushui_tisheng": "污水提升泵房",
    "sludge_hebing": "污泥合并",
    "sludge_shusong": "污泥输送",
    "sludge_bengzhan": "污泥泵站",
    "sludge_nongsuo": "污泥浓缩",
    "sludge_xiaohua": "污泥消化",
    "sludge_tuoshui": "污泥脱水",
    "sludge_ganhua": "污泥干化",
    "municipal_input": "市政输入",
}


@dataclass(frozen=True)
@final
class TableBlock:
    """程序填表块（N1 计算章主体——单元格为字符串，渲染层零推导）。"""

    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
@final
class NumberLine:
    """数值锚定行：label＋值＋单位＋公式 ID（单位空串=无量纲或未知量纲）。

    formula_id 空串 = 该值无 trace 对应（派生／圆整／回显参数）——渲染层
    不加锚点，禁伪造锚定（数值锚定断言件的等值前提）。
    """

    label: str
    value: float
    unit: str
    formula_id: str = ""


@dataclass(frozen=True)
@final
class NarrativeSlot:
    """N3 叙述槽：AI 撰稿承接位（正文禁数字——anchors 后检守卫）。"""

    slot_id: str
    hint: str


@dataclass(frozen=True)
@final
class FigureRef:
    """附图引用：图名（产物文件名）＋图题。"""

    name: str
    caption: str


@dataclass(frozen=True)
@final
class NoteLine:
    """程序注记段（纯文本段落——撰写面禁数字纪律由装配方自律）。"""

    text: str


@dataclass(frozen=True)
@final
class Section:
    """章内小节（第 4 章逐单元分组）。"""

    title: str
    blocks: tuple[Block, ...]


Block = TableBlock | NumberLine | NarrativeSlot | FigureRef | NoteLine | Section


@dataclass(frozen=True)
@final
class Chapter:
    """章节：id（稳定标识）＋标题＋块序列。"""

    id: str
    title: str
    blocks: tuple[Block, ...]


ReportAST = tuple[Chapter, ...]


class EstimateRowLike(Protocol):
    """概算明细行协议（core cost EstimateRow 的最小消费面）。"""

    price_key: str
    name_zh: str
    unit: str
    quantity: float
    unit_price: float
    amount: float


class EstimateSheetLike(Protocol):
    """概算表协议（core cost EstimateSheet 的最小消费面——集成批接线）。"""

    detail_rows: Sequence[EstimateRowLike]
    subtotal: float
    grand_total: float


def unit_zh(unit_id: str) -> str:
    """单元中文显示名（声明面映射；缺席回落 unit_id——不猜名）。"""
    return _UNIT_NAMES_ZH.get(unit_id, unit_id)


def indicator_of(key: str, unit_id: str) -> str:
    """出水品质键 → 指标名（剥离「{unit}.out.」前缀）。"""
    prefix = f"{unit_id}.out."
    return key.removeprefix(prefix) if key.startswith(prefix) else key


def condition_label(condition_key: str) -> str:
    """工况键 → 工程语义说明（表内文字——程序注入，非 AI 叙述）。"""
    if condition_key == DESIGN_KEY:
        return "最高日最高时设计工况"
    if condition_key == "avg":
        return "平均时工况"
    if condition_key.startswith("design_offline_"):
        offline = condition_key.removeprefix("design_offline_")
        return f"单元 {unit_zh(offline)}（{offline}）检修敏感性工况（n-1 池）"
    return condition_key


def anchor_index(plant: PlantResult) -> dict[str, dict[float, str]]:
    """design 工况 trace 输出 → 公式 ID 索引（值等值锚定——首现优先）。

    round(x,10) 与 result_schema 序列化定点同口径：锚定值与 serialize 值
    逐项相等的断言基础。
    """
    index: dict[str, dict[float, str]] = {}
    for node in plant.trace:
        if node.condition_key != DESIGN_KEY:
            continue
        per_unit = index.setdefault(node.unit_id, {})
        per_unit.setdefault(round(node.output, 10), node.formula_id)
    return index


def ordered_dim_fields(
    dims: Mapping[str, float], manifest: UnitManifest | None
) -> list[str]:
    """dims 字段序：manifest out_dims 声明序优先，余键字典序（确定性）。"""
    declared = [
        spec.field_id
        for spec in (manifest.out_dims if manifest else ())
        if spec.field_id in dims
    ]
    rest = sorted(key for key in dims if key not in set(declared))
    return declared + rest


def dim_label_unit(
    field_id: str, manifest: UnitManifest | None
) -> tuple[str, str]:
    """dims 字段 →（中文标签，规范单位串）：out_dims 声明面直投；缺席
    回落（字段 ID 原文＋空单位——不猜量纲）。"""
    if manifest is not None:
        for spec in manifest.out_dims:
            if spec.field_id == field_id:
                return spec.label_zh or field_id, CANONICAL_UNITS.get(spec.dim, "")
    return field_id, ""


def ordered_units(
    project: ProjectFile, snapshot: Mapping[str, UnitResultSnapshot]
) -> list[str]:
    """单元展示序：自进水节点沿 design.edges 广度优先的工序序（回路边
    防重入），未达单元（污泥线等无显式入边者）按快照原序殿后——确定性。

    edges 为原始 dict 形态（{"src": {"unit_id":…}, "dst": …}——
    project_schema R2 弱类型面），此处只做只读键访问。
    """
    adjacency: dict[str, list[str]] = {}
    for edge in project.design.edges:
        src = edge.get("src")
        dst = edge.get("dst")
        if not isinstance(src, Mapping) or not isinstance(dst, Mapping):
            continue
        src_id = src.get("unit_id")
        dst_id = dst.get("unit_id")
        if isinstance(src_id, str) and isinstance(dst_id, str):
            adjacency.setdefault(src_id, []).append(dst_id)
    ordered: list[str] = []
    seen = {_INLET_ID}
    queue = [_INLET_ID]
    while queue:
        unit_id = queue.pop(0)
        for nxt in adjacency.get(unit_id, ()):
            if nxt in seen or nxt not in snapshot:
                continue
            seen.add(nxt)
            ordered.append(nxt)
            queue.append(nxt)
    ordered.extend(uid for uid in snapshot if uid not in seen)
    return ordered
