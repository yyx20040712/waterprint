"""量纲与规范单位定义、pint 边界包装（全库唯一接触 pint 的文件）。

输入:  外部边界的带单位数值与单位字符串（UI/API/项目文件/Excel 读取）
输出:  规范单位裸值（float）、Quantity 包装、InvalidUnitError /
       InvalidQuantityError（ADR-002 §12.1）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T1 冻结；实现必须逐条满足，镜像测试 tests/contracts/test_quantity.py
#   + tests/contracts/properties_quantity.py；白名单锁定测试挂人类解锁批 U-C2）
#
# 【公开接口】
#   class DimKey(StrEnum)        量类枚举（10 成员，值=成员名 ASCII；
#                                签名基型 (str, Enum) 按 ruff UP042 升格为
#                                其 3.12 规范形态 StrEnum，语义等价）：
#                                FLOW/CONCENTRATION/LENGTH/AREA/VOLUME/MASS/
#                                TIME/VELOCITY/POWER/DIMENSIONLESS
#   class Quantity               (magnitude: float, unit: str) 不可变哑值对象：
#                                构造不校验单位、不换算（校验/换算只发生在 parse）
#   class InvalidUnitError(Exception)
#       单位非法：白名单外写法 / 量纲不匹配（领域异常，禁止静默、无默认单位）
#   class InvalidQuantityError(Exception)
#       值非法：非有限实数（NaN / ±Inf，GR-02 输入即拒绝）
#   CANONICAL_UNITS: dict[DimKey, str]
#       量类 → 规范单位串，唯一真源（内核热路径的裸值单位语义）
#   ACCEPTED_INPUT_UNITS: dict[DimKey, frozenset[str]]
#       输入单位白名单真源（UF-20 冻结，见【单位别名白名单】节）
#   parse(value, unit, expect: DimKey) -> float
#       边界入口：白名单内写法经 pint 换算为规范单位裸值并校验量纲
#   attach(value: float, dim: DimKey) -> Quantity
#       出口：规范单位裸值 → 带单位 Quantity（供显示/序列化层）
#
# 【单位别名白名单】（UF-20 冻结：每个 DimKey 一组显式接受写法，
#   白名单外一切写法默认拒绝——含上标 m³/d、大写 M3/d 等 pint 默认
#   接受面；pint 永不接触未审字符串。增补 = 规格变更，走显式 commit
#   + 人类解锁批补锁定测试，不允许实现期顺手扩）
#     FLOW          {"m3/s", "m3/d"}
#     CONCENTRATION {"mg/L", "g/m3"}
#     LENGTH        {"m", "mm"}
#     AREA          {"m2"}            VOLUME {"m3"}       MASS {"kg"}
#     TIME          {"s"}             VELOCITY {"m/s"}    POWER {"W"}
#     DIMENSIONLESS {""}
#   规范串本身天然合法（均为接受集成员）。
#
# 【行为规格】
#   R1 规范单位表（锁定三项 + 评审补充七项，与 registry/dimensions.py 一致）：
#      FLOW→"m3/s"，CONCENTRATION→"mg/L"，LENGTH→"m"（重写计划 §12.1 明示三项）；
#      AREA→"m2"，VOLUME→"m3"，MASS→"kg"，TIME→"s"，VELOCITY→"m/s"，
#      POWER→"W"（SI 口径，kW 属显示层），DIMENSIONLESS→""。
#   R2 换算必须经 pint 完成，禁止手写换算系数；1 m3/d == 1/86400 m3/s、
#      1 mg/L == 1 g/m3 等换算正确性由性质测试覆盖（往返/结合律）。
#      换算因子按 (unit, canonical) 维度 lru_cache——parse 只在边界，
#      内核热路径拿到的是 float 裸值，不碰 pint。
#   R3 非法单位字符串、量纲不匹配（expect=FLOW 却给 "mg/L"）→ InvalidUnitError，
#      禁止默认单位、禁止静默 None。
#   R4 落盘序列化一律"规范单位数值 + 显式 unit 字段"，读取方零换算（§12.1 R15）。
#   R5 值有限性（GR-02）：parse 与 attach 拒绝 NaN / ±Inf → InvalidQuantityError；
#      非数值类型（str 等）不做拦截——程序缺陷按 GR-08 自然 TypeError。
#      parse 不做符号（负值）校验：符号语义归各构造器（flow.py 等），
#      DIMENSIONLESS/温差类量会被负值拒绝误伤（GR-04 分界）。
#   R6 白名单收窄（UF-20）：unit ∈ ACCEPTED_INPUT_UNITS[expect] ∪
#      {CANONICAL_UNITS[expect]}，白名单外一律 InvalidUnitError。
#   R7 异常消息（GR-09，进发布即冻结）：InvalidUnitError 必含「单位串 + 期望
#      DimKey」；InvalidQuantityError 必含「值 repr + 原因」；转换 pint 异常时
#      raise ... from exc（GR-12）。白名单展示中空串写法渲染为 "<空串>"
#      （GLM-01：可读且确定性；判定用原串，行为不变）。
#   R8 parse 路径：值有限性 → 白名单（白名单外→InvalidUnitError，pint 永不
#      接触未审字符串）→ 量纲校验 → pint 换算。本文件是魔法数字门禁真源区，
#      豁免仅覆盖单位定义字符串，不豁免换算系数。
#
# 【实现口径】pint 默认 registry 不解析 "m3"/"m2" 串式（实测 0.25.3），
#   以 ureg.define 别名（"m3 = m**3"、"m2 = m**2"——单位定义字符串，
#   非换算系数）解决；锁定三项规范串 "m3/s"/"mg/L"/"m" 保持原串不变。
#   换算因子缓存用 functools.cache（= lru_cache(maxsize=None)，ruff UP033）。
#
# 【禁止】
#   - 出现任何手写换算系数（0.001、86400 等魔法数只能出现在测试的期望值里）
#   - pint 泄漏到返回值：内核热路径拿到的是 float 裸值
#   - import 内部其他模块（L0 零内部依赖，仅标准库 + pint）
#
# 【测试要求】tests/contracts/test_quantity.py + properties_quantity.py
#   （换算正确性、非法拒绝、往返恒等；性质：attach(parse(x)) == x）；
#   白名单外写法拒 / NaN / Inf 拒的锁定测试挂人类解锁批 U-C2，
#   当期证据以实现报告负例命令输出承担。
#
# 【参照】重写计划 §2/§12.1；ADR-002；UF-20；简报 T1 预裁决 R1~R8；
#   病灶 Q_design/Q_avg 双轨、P_sludge 标 kW
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from math import isfinite
from typing import Final, final

import pint


class DimKey(StrEnum):
    """量类枚举：规范单位表的键，全库单位语义的维度锚点。"""

    FLOW = "FLOW"
    CONCENTRATION = "CONCENTRATION"
    LENGTH = "LENGTH"
    AREA = "AREA"
    VOLUME = "VOLUME"
    MASS = "MASS"
    TIME = "TIME"
    VELOCITY = "VELOCITY"
    POWER = "POWER"
    DIMENSIONLESS = "DIMENSIONLESS"


class InvalidUnitError(Exception):
    """单位非法：白名单外写法或量纲不匹配（禁止默认单位、禁止静默）。"""


class InvalidQuantityError(Exception):
    """值非法：非有限实数（NaN / ±Inf，GR-02 输入即拒绝）。"""


CANONICAL_UNITS: dict[DimKey, str] = {
    DimKey.FLOW: "m3/s",
    DimKey.CONCENTRATION: "mg/L",
    DimKey.LENGTH: "m",
    DimKey.AREA: "m2",
    DimKey.VOLUME: "m3",
    DimKey.MASS: "kg",
    DimKey.TIME: "s",
    DimKey.VELOCITY: "m/s",
    DimKey.POWER: "W",
    DimKey.DIMENSIONLESS: "",
}

ACCEPTED_INPUT_UNITS: dict[DimKey, frozenset[str]] = {
    DimKey.FLOW: frozenset({"m3/s", "m3/d"}),
    DimKey.CONCENTRATION: frozenset({"mg/L", "g/m3"}),
    DimKey.LENGTH: frozenset({"m", "mm"}),
    DimKey.AREA: frozenset({"m2"}),
    DimKey.VOLUME: frozenset({"m3"}),
    DimKey.MASS: frozenset({"kg"}),
    DimKey.TIME: frozenset({"s"}),
    DimKey.VELOCITY: frozenset({"m/s"}),
    DimKey.POWER: frozenset({"W"}),
    DimKey.DIMENSIONLESS: frozenset({""}),
}


@dataclass(frozen=True)
@final
class Quantity:
    """带单位数值的不可变哑包装：只做携带，不校验、不换算（R2 分界）。"""

    magnitude: float
    unit: str


# 模块级私有 registry：别名 "m3"/"m2" 为单位定义字符串（R8 真源区豁免范畴），
# 不引入任何换算系数；pint 对象不越过本模块边界。
_UREG: Final[pint.UnitRegistry[float]] = pint.UnitRegistry()
_UREG.define("m3 = m**3")
_UREG.define("m2 = m**2")


def _require_finite(value: float) -> None:
    """值有限性守卫：NaN / ±Inf 一律 InvalidQuantityError（GR-02）。"""
    if not isfinite(value):
        raise InvalidQuantityError(
            f"值 {value!r} 非有限实数：parse/attach 拒绝 NaN 与 ±Inf（GR-02 输入即拒绝）"
        )


@cache
def _conversion_factor(unit: str, canonical: str, expect: DimKey) -> float:
    """经 pint 求 unit→canonical 的换算因子（按单位对缓存；白名单内串才可达）。"""
    try:
        src = _UREG.parse_units(unit)
        dst = _UREG.parse_units(canonical)
        if src.dimensionality != dst.dimensionality:
            raise InvalidUnitError(
                f"单位 {unit!r} 的量纲与 DimKey.{expect.value}"
                f"（规范单位 {canonical!r}）不符"
            )
        return float((1.0 * src).to(dst).magnitude)
    except pint.PintError as exc:
        raise InvalidUnitError(
            f"单位 {unit!r} 经 pint 解析失败"
            f"（期望 DimKey.{expect.value}，规范单位 {canonical!r}）"
        ) from exc


def _accepted_writing(dim: DimKey) -> str:
    """白名单写法的确定性展示串（排序冻结，供异常消息 GR-09）。

    空串写法以 "<空串>" 形态可读展示（GLM-01：DIMENSIONLESS 的合法空输入
    不得渲染为空白残缺消息）；仅展示层换形，白名单判定仍用原串，行为不变。
    """
    return "/".join(w or "<空串>" for w in sorted(ACCEPTED_INPUT_UNITS[dim]))


def parse(value: float, unit: str, expect: DimKey) -> float:
    """边界入口：白名单内单位经 pint 换算为规范单位裸 float（R8 路径）。"""
    _require_finite(value)
    canonical = CANONICAL_UNITS[expect]
    if unit not in ACCEPTED_INPUT_UNITS[expect] and unit != canonical:
        raise InvalidUnitError(
            f"单位 {unit!r} 不在 DimKey.{expect.value} 的接受写法内"
            f"（白名单：{_accepted_writing(expect)}；UF-20 冻结，默认拒绝白名单外写法）"
        )
    return value * _conversion_factor(unit, canonical, expect)


def attach(value: float, dim: DimKey) -> Quantity:
    """出口包装：规范单位裸值 → Quantity（数值不变，单位=规范单位）。"""
    _require_finite(value)
    return Quantity(magnitude=value, unit=CANONICAL_UNITS[dim])
