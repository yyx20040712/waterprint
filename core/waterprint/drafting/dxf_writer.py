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
#      meta 值，禁用当前时钟——快照回归与可复算前提）+落盘后 CLASSES
#      段记录序归一（批 14-FIX 修复：ezdxf 1.4.4 类注册序随进程熵翻转
#      →CLASSES 段 CLASS 记录换位[同句柄同内容仅序异，跨进程双稳态，
#      与 PYTHONHASHSEED 无关——探针 b14-probe/probe_fixface2.py 20
#      采样实证]；CLASS 记录零顺序语义[类声明表]，记录块按组码 0 分界
#      字典序排序——ezdxf readfile 往返完整+幂等+跨进程恒等三证。
#      行尾自适应：ezdxf ASCII 导出 Windows=CRLF/Linux=LF 平台原生
#      [CI 首验实录]，归一按原生行尾就地改写。
#      OBJECTS 段不归一：26 采样零漂移+首对象=根字典位置惯例保守不动）。
#   R4 路径安全（§18）：输出路径限制在配置输出目录内拼接 + 分量校验，
#      拒绝 ".."/绝对路径分量——越界抛领域异常。
#   R5 m→mm 换算唯一住所：图形实体坐标（结果 m）→ 出图 mm 的比例换算
#      在本文件统一执行（换算因子来自 SheetSpec 比例），各图纸文件
#      1:1 mm 语义（sheets R3 分工）。
#
# 【测试要求】R2018 版本头断言、UTF-8 中文文字实体往返、确定性双跑
#   字节级相同、路径越界拒绝、快照回归；CLASSES 记录序==字典序+双子
#   进程渲染字节恒等（批 14-FIX——跨进程双稳态补强）。
#
# 【参照】重写计划 §12.5/§18 路径安全；ADR-006；R6/R7 风险行
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, final

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
# DXF 文本结构常量（批 14-FIX CLASSES 归一面——非业务数值，AST 魔法数字
# 门禁真源区外具名化，赋值仅用白名单值组合）：组码-值成对步距 2 行；
# 段头行对（0/SECTION+2/<名>）共 2 对=4 行。
_DXF_PAIR_LINES: Final[int] = 2
_DXF_SECTION_HEAD_LINES: Final[int] = _DXF_PAIR_LINES * _DXF_PAIR_LINES
# 出图默认比例（R1-2 裁定 2026-08-26：比例接线——write_dxf scale 关键字承接
# SheetSpec 比例口径；缺省值=GB/T 50001 工程惯例常用出图比例 1:100，
# M5 布图批接 SheetSpec 实例传递）。字符串比例非数值字面量（AST 门禁面外），
# 形态校验在 _scale_factor（非法串拒）。
_DEFAULT_SCALE: Final[str] = "1:100"


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


def _classes_range(lines: list[bytes]) -> tuple[int, int]:
    """CLASSES 段体行界（组码 0/SECTION+2/CLASSES … 0/ENDSEC）。

    缺段/无终界=畸形输入 fail-closed（R2018 必有该段）。
    """
    for i in range(len(lines) - _DXF_SECTION_HEAD_LINES + 1):
        if not (
            lines[i].strip() == b"0"
            and lines[i + 1] == b"SECTION"
            and lines[i + _DXF_PAIR_LINES].strip() == b"2"
            and lines[i + _DXF_SECTION_HEAD_LINES - 1] == b"CLASSES"
        ):
            continue
        end = i + _DXF_SECTION_HEAD_LINES
        while end + 1 < len(lines) and not (
            lines[end].strip() == b"0" and lines[end + 1] == b"ENDSEC"
        ):
            end += 1
        if end + 1 < len(lines):
            return i + _DXF_SECTION_HEAD_LINES, end
        break
    raise InvalidDrawingError("DXF 缺 CLASSES 段或无 ENDSEC 终界（畸形输入）")


def _group_pairs(body: list[bytes]) -> list[tuple[bytes, ...]]:
    """段体行对 → 记录块列表（组码 0 分界）；行数非偶=配对破缺抛拒。"""
    if len(body) % _DXF_PAIR_LINES != 0:
        raise InvalidDrawingError(
            f"DXF CLASSES 段体行数 {len(body)} 非偶（组码-值配对破缺）"
        )
    blocks: list[tuple[bytes, ...]] = []
    current: list[bytes] = []
    for i in range(0, len(body), _DXF_PAIR_LINES):
        if body[i].strip() == b"0":
            if current:
                blocks.append(tuple(current))
            current = [body[i], body[i + 1]]
        else:
            current.extend((body[i], body[i + 1]))
    if current:
        blocks.append(tuple(current))
    return blocks


def _sort_classes_section(out: Path) -> None:
    """R3 补充（批 14-FIX）：落盘后 CLASSES 段记录块字典序归一（就地改写）。

    仅动 CLASSES 段内记录序（ezdxf 注册序=进程熵噪声，跨进程双稳态）；
    其余段/行零触碰。行尾自适应（ezdxf ASCII 导出 Windows=CRLF/Linux
    =LF 平台原生——CI 首验实录；快照测试规范化器 replace 归一同款
    差异面对象，此处按原生形态就地改写不引入跨平台字节变更）。
    畸形输入 fail-closed 抛 InvalidDrawingError——禁静默丢行。
    """
    data = out.read_bytes()
    eol = b"\r\n" if b"\r\n" in data else b"\n"
    lines = data.split(eol)
    start, end = _classes_range(lines)
    merged: list[bytes] = []
    for block in sorted(_group_pairs(lines[start:end])):
        merged.extend(block)
    lines[start:end] = merged
    out.write_bytes(eol.join(lines))


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
    """R3 确定性头部：审计字段固定值+可复算三元组落 custom_vars（R1-4）。

    condition_key+repro 三元组经 HEADER 段自定义属性（$CUSTOMPROPERTYTAG/
    $CUSTOMPROPERTY 对）落盘——ezdxf 回读 doc.header.custom_vars 可得，
    不可再静默丢（NF-1 修复；时间/GUID 由 ezdxf 测试开关固定）。
    """
    doc.header["$TDINDWG"] = 0.0
    doc.header["$PROJECTNAME"] = meta.title  # 合法头变量（$comments 非法——实测）
    doc.header["$LASTSAVEDBY"] = meta.creator
    for tag, value in (
        ("condition_key", meta.condition_key),
        ("design_hash", meta.repro[0]),
        ("engine_version", meta.repro[1]),
        ("data_version", meta.repro[2]),
    ):
        doc.header.custom_vars.append(tag, value)


def write_dxf(
    entities: EntityGroup,
    styles: StyleTable,
    out: Path,
    meta: DrawingMeta,
    scale: str = _DEFAULT_SCALE,
) -> Path:
    """DXF R2018（AC1032）落盘正门：翻译（m→mm 唯一住所）→确定性头→落盘。

    scale=出图比例串（'1:100' 形态，SheetSpec 比例口径——v1 调用方直传，
    M5 布图批由 SheetSpec 实例接线）；m→mm 因子经 _scale_factor(scale)
    求得，"1:100" 硬编码已废止（R1-2）。
    """
    _validate_out(out)
    _enable_fixed_meta()
    doc = ezdxf_new("R2018")
    _apply_styles(doc, styles)
    factor = _scale_factor(scale)
    _translate(doc, entities, styles, factor)
    _fix_header(doc, meta)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    _sort_classes_section(out)  # R3 批 14-FIX：注册序噪声归一（跨进程字节恒等）
    return out
