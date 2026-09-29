"""导出选项 DSL 解析器族（批6j 拆件——ADR-024 预算墙配方）。

输入:  export_artifact **options（路由选项原始字符串）
输出:  解析后强类型值（比例分母 int/站距覆盖 Mapping/进厂标高 Mapping+成对旗）
       +未知键/形态/域诚实拒绝（ArtifactKindNotReady——基类随段迁本件，
       app_export 再导出保公开 import 路径，beam→search 先例第三例同族）。
拆件动机: app_export 566>500 预算墙（批6j 绝对标高通道扩入解析器族后
       破墙——AGENTS §11 撞墙拆法：解析域整体迁兄弟件，编排域留守）。
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（UF-33 产物导出面·路由选项子域；PROFILE3+批6i/6j 通道族；
# 伴生件形态=app_export 同款 L4 并列——app_export→本件同层伴生边，
# 零 app 依赖[防环]；镜像测试 tests/app/test_app_export_options.py）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from collections.abc import Mapping
from math import isfinite
from types import MappingProxyType
from typing import Final

from waterprint.drafting.sheets import SCALE_DENOM_MAX

__all__ = ["ArtifactKindNotReady"]

class ArtifactKindNotReady(Exception):  # noqa: N818  # 名载归属批次（D2 冻结），LoopDivergence 先例
    """产物 kind 未就绪（audit=M4/dxf=M2 出图批/estimate=M3）——GR-11 族。"""


# 站距覆盖值十进制白名单（批6i k1-W2：整数位必在、小数位可选——
# `30`/`30.5` 合法；前导符/科学记数/分组符/非 ASCII 全拒）。
_STATION_VALUE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+(?:\.[0-9]+)?$"
)

# 进厂标高值带符号十进制白名单（批6j：站距白名单+符号位——绝对标高可为
# 负〔海平面下场景〕，相对 ±0.00 记法本身含符号语义；科学记数/下划线/
# 全角全拒，批6i k1-W2 同族）。
_DATUM_VALUE_RE: Final[re.Pattern[str]] = re.compile(
    r"^-?[0-9]+(?:\.[0-9]+)?$"
)

_EXPORT_OPTIONS: Final[frozenset[str]] = frozenset(
    {"unit_id", "condition_key", "sheet", "h_scale", "v_scale",
     "station_overrides", "water_level", "ground_elev"}
)


def _station_overrides_of(
    raw: str | None,
) -> dict[str, float] | None:
    """站距覆盖 DSL 解析（批6i core 终闸）：None/空串→None（未传）；
    形态 "unit=30.5,unit2=44"（逗号分隔、键=下游站 unit_id、值=米）。
    逐项校验：非空键/数值域（float+ValueError 收编+有限性——isdecimal
    判域不适用小数形态，try/except 收编面=AGENTS §魔法数字段同款 sanctioned
    路径）/重复键拒（同键双值静默取后者=吞意图）；键位合法性（首站/
    未知站）归 build_chainage_axis 闸（合法集=首站外站位——站集在装配
    期才可知，双层闸与 h/v 域闸+路由闸同构）。"""
    text = (raw or "").strip()
    if not text:
        return None
    overrides: dict[str, float] = {}
    for part in text.split(","):
        entry = part.strip()
        if "=" not in entry:
            raise ArtifactKindNotReady(
                f"station_overrides 项 {entry!r} 缺 '='（形态 "
                "'unit=米值' 逗号分隔——批6i 手动逐边覆盖例外通道）："
                f"收到 {raw!r}"
            )
        key, _, value_text = entry.partition("=")
        key = key.strip()
        value_text = value_text.strip()
        if not key or not value_text:
            raise ArtifactKindNotReady(
                f"station_overrides 项 {entry!r} 键或值空（形态 "
                f"'unit=米值'）：收到 {raw!r}"
            )
        # 数值白名单（k1-W2 实修）：十进制小数形态 ASCII 位数——拒科学
        # 记数法（1e3）/下划线分组（1_000）/全角数字（１２３）等 float
        # 静默收编面（h/v isdecimal 判域同族纪律，消息含合法形态示例）。
        if not _STATION_VALUE_RE.match(value_text):
            raise ArtifactKindNotReady(
                f"station_overrides[{key!r}] 值非十进制小数形态："
                f"{value_text!r}（合法如 '30.5'——科学记数法/下划线/非"
                f"ASCII 数字拒）：收到 {raw!r}"
            )
        try:
            value = float(value_text)
        except ValueError as exc:
            raise ArtifactKindNotReady(
                f"station_overrides[{key!r}] 值非数值：{value_text!r}"
                f"（站距米值，如 'unit_b=30.5'）：收到 {raw!r}"
            ) from exc
        if not isfinite(value) or value <= 0.0:
            # d1-r2 W3 实修：非正/非有限在 DSL 终闸层拒（错误族与 h/v
            # 同序——非正本层拦、键位归轴构造层；NaN/Inf 无里程语义）
            raise ArtifactKindNotReady(
                f"station_overrides[{key!r}] 须为正有限站距米值："
                f"得到 {value_text!r}（如 '30.5'）"
            )
        if key in overrides:
            raise ArtifactKindNotReady(
                f"station_overrides 键 {key!r} 重复（后值静默覆盖前值"
                "=吞意图，禁）：收到 {raw!r}"
            )
        overrides[key] = value
    return overrides


def _inlet_datum_of(
    water_raw: str | None, ground_raw: str | None
) -> tuple[Mapping[str, float], bool]:
    """进厂标高 DSL 解析（批6j core 终闸——UF-50 通道收口）。

    双 None → (相对 ±0.00 默认基准, False)：工程相对标高惯例默认——
    原 `_REL_DATUM`「无通道」常量退役（UF-50：收口后退役），0/0 字面量
    降格为本解析器文档化默认值（非假设数值面——进厂标高是 design 态
    输入，profile R2）。
    成对必传：单键=半相对半绝对错配基准（水面 1053/地面 0 → 埋深失真），
    吞意图禁。值=带符号十进制+有限（NaN/Inf 无高程语义）。
    """
    if water_raw is None and ground_raw is None:
        return (
            MappingProxyType({"water_level": 0.0, "ground_elev": 0.0}), False
        )
    if (water_raw is None) != (ground_raw is None):
        raise ArtifactKindNotReady(
            "options 'water_level'/'ground_elev' 成对必传（单键=半相对半"
            "绝对的错配基准——吞意图禁）：仅收到 "
            f"water_level={water_raw!r} ground_elev={ground_raw!r}"
            "（批6j 绝对标高通道，如 water_level='1053.2' "
            "ground_elev='1051.0'）"
        )
    values: dict[str, float] = {}
    for key, raw in (("water_level", water_raw), ("ground_elev", ground_raw)):
        text = (raw or "").strip()
        # 数值白名单（批6i k1-W2 同族+符号位）：拒科学记数法（1e3）/
        # 下划线分组（1_000）/全角数字（１２３）等 float 静默收编面。
        if not _DATUM_VALUE_RE.match(text):
            raise ArtifactKindNotReady(
                f"进厂标高 {key!r} 值非带符号十进制形态：{raw!r}"
                "（合法如 '1053.2'/'-3.5'——科学记数法/下划线/非 ASCII"
                " 数字拒；批6j 绝对标高通道）"
            )
        try:
            value = float(text)
        except ValueError as exc:
            raise ArtifactKindNotReady(
                f"进厂标高 {key!r} 值非数值：{raw!r}（绝对标高米值，"
                "如 '1053.2'——批6j）"
            ) from exc
        if not isfinite(value):
            raise ArtifactKindNotReady(
                f"进厂标高 {key!r} 须为有限米值：得到 {raw!r}"
                "（NaN/Inf 无高程语义——批6j）"
            )
        values[key] = value
    return MappingProxyType(values), True


def _scale_denom_of(raw: str | None, what: str) -> int:
    """比例分母解析（PROFILE3 PD3 core 终闸）：strip 后全数字+域校验
    （1≤值≤SCALE_DENOM_MAX）——判定语义与 server 422 预校验显式同一
    （双闸同构，防 422/501 边界漂移）；非法=诚实拒。"""
    text = (raw or "").strip()
    # R 轮（双审 D1-G1-01/A2-G1-01）：isdecimal 挡 Unicode 数字（"②"等
    # isdigit 真而 int 炸）+长度短路挡超长串（≥3.11 int 4300 位上限
    # ValueError 逃逸）——双闸判定域显式同一（server 预校验同式）。
    if not (text.isdecimal() and len(text) <= len(str(SCALE_DENOM_MAX))
            and 1 <= int(text) <= SCALE_DENOM_MAX):
        raise ArtifactKindNotReady(
            f"export_artifact 选项 {what} 须为正整数比例分母字符串"
            f"（1~{SCALE_DENOM_MAX}，如 '2000'）：收到 {raw!r}（PROFILE3）"
        )
    return int(text)


def _check_export_options(
    options: Mapping[str, str | None], kind: str
) -> None:
    """导出选项键白名单（未知键拒——GR-09 精神，防拼写漂移静默忽略）；
    R 轮（D1-G1-04）：h/v 仅 kind=dxf 可传——calcbook/ifc 分支零消费
    选项，传=意图错配诚实拒（禁静默吞）。"""
    unknown = frozenset(options) - _EXPORT_OPTIONS
    if unknown:
        raise ArtifactKindNotReady(
            f"export_artifact 未知选项：{sorted(unknown)}"
            f"（合法 {sorted(_EXPORT_OPTIONS)}）"
        )
    # 判非 None 值而非键存在（调用方归一层可传 None 占位——None=未传）。
    if kind != "dxf" and (
        options.get("h_scale") is not None or options.get("v_scale") is not None
    ):
        raise ArtifactKindNotReady(
            "options 'h_scale'/'v_scale' 仅 kind='dxf'（纵断双比例）可传——"
            f"kind={kind!r} 零消费选项面（PROFILE3 R 轮，禁静默吞意图）"
        )
    if kind != "dxf" and options.get("station_overrides") is not None:
        raise ArtifactKindNotReady(
            "options 'station_overrides' 仅 kind='dxf'（纵断站距覆盖）可传——"
            f"kind={kind!r} 零消费选项面（批6i，禁静默吞意图）"
        )
    if kind != "dxf" and (
        options.get("water_level") is not None
        or options.get("ground_elev") is not None
    ):
        raise ArtifactKindNotReady(
            "options 'water_level'/'ground_elev' 仅 kind='dxf'（纵断绝对"
            f"标高）可传——kind={kind!r} 零消费选项面（批6j，禁静默吞意图）"
        )
