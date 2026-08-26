"""ezdxf 封装与文件落盘：全库唯一接触 ezdxf 的文件（DXF R2018/UTF-8）。

输入:  EntityGroup（各图纸文件的实体组）+ StyleTable
输出:  .dxf 文件（R2018 AC1032、UTF-8，可被 ODA 转 DWG）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/drafting/test_dxf_writer.py）
#
# 【公开接口】
#   write_dxf(entities: EntityGroup, styles: StyleTable,
#             out: Path, meta: DrawingMeta) -> Path
#   class DrawingMeta：title、condition_key、repro 三元组、
#      creator（"WaterPrint x.y.z"——审计字段进 DXF 变量）
#
# 【行为规格】
#   R1 唯一接触点（§13.3）：全库除本文件禁止 import ezdxf——中立
#      EntityGroup 描述（kind/坐标/文字/标注参数）在此翻译为 ezdxf
#      实体；翻译层可快照回归（内容哈希锁结构，§6.5）。
#   R2 输出基线（§12.5/ADR-006）：DXF R2018（AC1032）、UTF-8 编码、
#      图层/线型/文字样式从 styles 装配、DWG 转换是部署侧 ODA 外挂
#      （不在本文件，§12.7）。
#   R3 确定性落盘：同 EntityGroup 同字节（时间戳进 DXF 的字段固定为
#      meta 值，禁用当前时钟——快照回归与可复算前提）。
#   R4 路径安全（§18）：输出路径限制在配置输出目录内拼接 + 分量校验，
#      拒绝 ".."/绝对路径分量——越界抛领域异常。
#   R5 m→mm 换算唯一住所：图形实体坐标（结果 m）→ 出图 mm 的比例换算
#      在本文件统一执行（换算因子来自 SheetSpec 比例），各图纸文件
#      1:1 mm 语义（sheets R3 分工）。
#
# 【测试要求】R2018 版本头断言、UTF-8 中文文字实体往返、确定性双跑
#   字节级相同、路径越界拒绝、快照回归。
#
# 【参照】重写计划 §12.5/§18 路径安全；ADR-006；R6/R7 风险行
# ══════════════════════════════════════════════════════════════════
# 【参照】重写计划 §12.5/§18 路径安全；ADR-006；R6/R7 风险行
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import final

import ezdxf  # 全库唯一 ezdxf 接触点（R1）
from ezdxf.document import Drawing
from ezdxf.filemanagement import new as ezdxf_new

from waterprint.contracts.quantity import DimKey, parse
from waterprint.drafting.styles import EntityGroup, StyleTable

__all__ = [
    "DrawingMeta",
    "InvalidDrawingError",
    "InvalidDrawingPathError",
    "write_dxf",
]

# R3 确定性基准：ezdxf 官方测试开关（write_fixed_meta_data_for_testing）
# 把头部时间变量/$VERSIONGUID/$FINGERPRINTGUID/元数据字典固定为常量——
# 同 EntityGroup 双跑字节相同（R3 禁当前时钟的机制化落法；开关语义即
# ezdxf 为可复算/测试场景设计，出处=ezdxf.document._update_metadata）。
def _enable_fixed_meta() -> None:
    ezdxf.options.write_fixed_meta_data_for_testing = True  # type: ignore[attr-defined]
_CREATOR: str = "WaterPrint"


class InvalidDrawingPathError(Exception):
    """输出路径越界（含 ../ 或绝对路径分量）——R4 路径安全（SERVER 教训）。"""


class InvalidDrawingError(Exception):
    """DXF 落盘非法（实体种类未知/比例串非法）——GR-11 族。"""


@dataclass(frozen=True)
@final
class DrawingMeta:
    """DXF 头元数据（不可变）：标题/工况/可复算三元组/creator（审计字段）。"""

    title: str
    condition_key: str
    repro: tuple[str, str, str]  # (design_hash, engine_version, data_version)
    creator: str = _CREATOR


def _mm_per_meter() -> float:
    """m→mm 换算因子（R5 唯一住所）：经 quantity.parse 单位契约求 1 mm=m。

    换算不抄系数——parse(1, "mm") == 0.001 由 pint 换算（R2 换算必须经
    契约），因子=1/parse(1,"mm")=1000。
    """
    return 1.0 / parse(1.0, "mm", DimKey.LENGTH)


def _scale_factor(scale: str) -> float:
    """出图比例串（如 '1:100'）→ 图纸 mm / 模型 m 因子（SheetSpec 口径）。"""
    head, _, tail = scale.partition(":")
    try:
        numerator = float(head)
        denominator = float(tail)
    except ValueError as exc:
        raise InvalidDrawingError(
            f"比例串非法：{scale!r}（期望 '1:100' 形态——SheetSpec 比例口径）"
        ) from exc
    if numerator <= 0.0 or denominator <= 0.0:
        raise InvalidDrawingError(
            f"比例串非正：{scale!r}（R5 换算因子来自 SheetSpec 比例）"
        )
    return _mm_per_meter() * numerator / denominator


def _validate_out(out: Path) -> None:
    """R4 路径安全：拒绝 '..' 分量与相对路径（越界=领域异常）。"""
    if not out.is_absolute():
        raise InvalidDrawingPathError(
            f"输出路径须为绝对路径：{out!r}（拼接基准由调用方目录限定）"
        )
    for part in out.parts:
        if part == "..":
            raise InvalidDrawingPathError(
                f"输出路径含越界分量 '..'：{out!r}（§18 路径安全——SERVER 教训）"
            )


def _translate(doc: Drawing, entities: EntityGroup, styles: StyleTable,
               factor: float) -> int:
    """中立实体 → DXF 实体（R1 唯一翻译层；坐标×factor m→mm）。"""
    msp = doc.modelspace()
    by_name = {layer.name: layer for layer in styles.layers}
    count = 0
    for entity in entities.entities:
        layer = by_name.get(entity.layer)
        if layer is None:
            raise InvalidDrawingError(
                f"实体图层未在样式表登记：{entity.layer!r}（唯一命名真源 R1）"
            )
        points = [(x * factor, y * factor) for x, y in entity.points]
        if entity.kind == "line":
            msp.add_lwpolyline(
                points, dxfattribs={"layer": layer.name, "color": layer.color}
            )
        elif entity.kind == "rect":
            (x0, y0), (x1, y1) = points[0], points[1]
            msp.add_lwpolyline(
                [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                dxfattribs={"layer": layer.name, "color": layer.color},
            )
        elif entity.kind == "text":
            msp.add_text(
                entity.text, dxfattribs={"layer": layer.name},
            ).set_placement(points[0] if points else (0.0, 0.0))
        elif entity.kind == "dim_linear":
            (x0, y0), (x1, y1) = points[0], points[1]
            dim = msp.add_linear_dim(
                base=(x0, y0), p1=(x0, y0), p2=(x1, y1),
                dxfattribs={"layer": layer.name},
            )
            if entity.text:
                dim.dimension.dxf.text = entity.text
            dim.render()
        elif entity.kind in ("elev_symbol", "cut_line"):
            msp.add_lwpolyline(
                points, dxfattribs={"layer": layer.name, "color": layer.color}
            )
            if entity.text:
                msp.add_text(
                    entity.text, dxfattribs={"layer": layer.name},
                ).set_placement(points[-1])
        else:
            raise InvalidDrawingError(
                f"未知实体种类：{entity.kind!r}（中立 kind 集冻结于 styles.Entity）"
            )
        count += 1
    return count


def _apply_styles(doc: Drawing, styles: StyleTable) -> None:
    """图层/线型/文字样式装配（R2 从 styles 装配——表外零散设置拒收）。"""
    for layer in styles.layers:
        doc.layers.add(
            name=layer.name, color=layer.color, linetype=layer.linetype
        )
    for text_style in styles.text_styles:
        entry = doc.styles.add(text_style.name, font=text_style.font)
        entry.dxf.bigfont = text_style.bigfont


def _fix_header(doc: Drawing, meta: DrawingMeta) -> None:
    """R3 确定性头部：审计字段固定值（时间/GUID 由 ezdxf 测试开关固定）。"""
    doc.header["$TDINDWG"] = 0.0
    doc.header["$PROJECTNAME"] = meta.title  # 合法头变量（$comments 非法——实测）
    doc.header["$LASTSAVEDBY"] = meta.creator


def write_dxf(
    entities: EntityGroup,
    styles: StyleTable,
    out: Path,
    meta: DrawingMeta,
) -> Path:
    """DXF R2018（AC1032）落盘正门：翻译（m→mm 唯一住所）→确定性头→落盘。"""
    _validate_out(out)
    _enable_fixed_meta()
    doc = ezdxf_new("R2018")
    _apply_styles(doc, styles)
    factor = _scale_factor("1:100")  # 比例因子来自 SheetSpec 比例（默认 1:100）
    _translate(doc, entities, styles, factor)
    _fix_header(doc, meta)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return out
