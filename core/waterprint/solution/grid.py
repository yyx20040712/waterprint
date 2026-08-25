"""自由参数离散网格：manifest 离散配置 → 参数矩阵（向量化枚举的输入形态）。

输入:  单元 manifest 的 ParamSpec 离散网格声明（值域/步长/枚举值）
输出:  参数矩阵（numpy 结构化数组，dtype 由 dimensions 注册表生成）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_grid.py）
#
# 【公开接口】
#   build_grid(param_specs: Sequence[ParamSpec]) -> Grid
#   class Grid：fields（字段序）、array（结构化数组：笛卡尔积展平）、
#       shape（各维取值数）、total（总组合数 = 各维乘积）
#   class GridTooLarge(Exception)：组合数超护栏（领域异常）
#   class InvalidGridError(Exception)：声明非法（空声明/空值域/缺值域/
#       重复字段/非有限值——GR-11 族，本文件定义）
#
# 【行为规格】
#   R1 组合数护栏：total > 4^k 上限（默认上限来自 assumptions，出处入库）
#      → 抛 GridTooLarge（附建议：缩小某维步长/范围）——§12.4
#      "自由参数网格 ≤4^k" 的机器强制。
#   R2 网格确定性：同 manifest 同 Grid（字段序按 field_id 字典序稳定）。
#   R3 网格值只来自 manifest 声明（枚举值或起止步长生成）；
#      代码不注入任何隐含取值。
#   R4 结构化数组 dtype 经 dimensions.dtype_of 生成——单位作为元数据
#      在注册表，数组内是规范单位裸值（§11 R1，pint 不进热路径）。
#      【实现注记】未登记 dimensions 的字段（调用方临时值域声明，如
#      服务层 UI 网格/测试声明）按 dtype_of 同款形态（"<f8" 槽×
#      field_id 槽名）就地构造——R4 实质=结构化 dtype 形态统一，字段
#      槽名恒等（numpy 静默改名防线在 dimensions 登记期）。
#
# 【声明面】每维一条声明，两种形态：ParamSpec（grid 档消费；range 归
#   约束层不在此生成——起止步长生成走 Mapping 声明携带 step）或
#   Mapping（field_id + values 显式值域，或 range{min,max}+step 起止
#   步长生成，闭区间 GR-06）——R3 两种生成路径均零代码注入。
#
# 【测试要求】笛卡尔积正确、字典序稳定性、超限抛 GridTooLarge、
#   dtype 字段与 manifest 一致。
#
# 【参照】重写计划 §12.4；ADR-005
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import isfinite, prod
from typing import Any, Final, final

import numpy

from waterprint.contracts.manifest import ParamSpec
from waterprint.registry.assumptions import assumption
from waterprint.registry.dimensions import InvalidDimensionError, dtype_of

_BASE_KEY: Final[str] = "solution.grid.base_per_dim"


class GridTooLarge(Exception):  # noqa: N818  # 名冻结自规格头/锁定测试，LoopDivergence 先例
    """网格组合数超护栏（total > base**k，§12.4 机器强制）——领域异常。"""


class InvalidGridError(Exception):
    """网格声明非法（空声明/空值域/缺值域/重复字段/非有限值）——GR-11 族。"""


@dataclass(frozen=True)
@final
class Grid:
    """离散参数网格（不可变）：字段序 + 笛卡尔积展平结构化数组 + 形状。"""

    fields: tuple[str, ...]
    array: numpy.ndarray[tuple[int], numpy.dtype[numpy.void]]
    shape: tuple[int, ...]
    total: int


def _number(value: object, where: str) -> float:
    """数值守卫（GR-02）：bool 拒/非数值拒/非有限拒，归一 float。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidGridError(f"{where} 必须为数值（int|float，bool 拒）：得到 {value!r}")
    number = float(value)
    if not isfinite(number):
        raise InvalidGridError(f"{where} 非有限：{number!r}（GR-02 输入即拒）")
    return number


def _ranged_values(rng: Mapping[str, object], step: object, field_id: str) -> tuple[float, ...]:
    """起止步长生成（R3 第二路径）：闭区间 [min,max] 步进展开（GR-06）。"""
    unknown = sorted(set(rng) - {"min", "max"})
    if unknown or "min" not in rng or "max" not in rng:
        raise InvalidGridError(
            f"字段 {field_id!r} 的 range 声明须为恰含 min/max 的对象：得到 {sorted(rng)}"
        )
    low = _number(rng["min"], f"字段 {field_id!r} 的 range.min")
    high = _number(rng["max"], f"字段 {field_id!r} 的 range.max")
    stride = _number(step, f"字段 {field_id!r} 的 step")
    if stride <= 0 or low > high:
        raise InvalidGridError(
            f"字段 {field_id!r} 的 range 生成非法：须 step>0 且 min≤max"
            f"（得到 step={stride!r}, min={low!r}, max={high!r}）"
        )
    generated = numpy.arange(low, high + stride / 2, stride).tolist()
    return tuple(_number(value, f"字段 {field_id!r} 生成值") for value in generated)


def _dimension(entry: object, index: int) -> tuple[str, tuple[float, ...]]:
    """单维声明归一：ParamSpec（grid 档）或 Mapping（values/range+step）→ 值域。"""
    if isinstance(entry, ParamSpec):
        if entry.grid is None:
            raise InvalidGridError(
                f"参数 {entry.field_id!r} 无 grid 声明（range 归约束层消费；"
                "枚举需 grid 档或显式值域/起止步长声明——R3 零代码注入）"
            )
        field_id = entry.field_id
        values = tuple(
            _number(value, f"参数 {entry.field_id!r} 的 grid 档位")
            for value in entry.grid
        )
    elif isinstance(entry, Mapping):
        raw_id = entry.get("field_id")
        if not isinstance(raw_id, str) or not raw_id:
            raise InvalidGridError(
                f"网格声明[{index}] 缺非空字符串 field_id：得到 {raw_id!r}"
            )
        field_id = raw_id
        if "values" in entry:
            values = tuple(
                _number(value, f"字段 {field_id!r} 的 values[{position}]")
                for position, value in enumerate(entry["values"])
            )
        elif "range" in entry:
            rng = entry["range"]
            if not isinstance(rng, Mapping):
                raise InvalidGridError(
                    f"字段 {field_id!r} 的 range 须为对象（min/max）：{type(rng).__name__}"
                )
            values = _ranged_values(rng, entry.get("step"), field_id)
        else:
            raise InvalidGridError(
                f"字段 {field_id!r} 声明缺值域（values 或 range+step 二选一）"
            )
    else:
        raise InvalidGridError(
            f"网格声明[{index}] 须为 ParamSpec 或 Mapping：得到 {type(entry).__name__}"
        )
    if not values:
        raise InvalidGridError(f"字段 {field_id!r} 值域为空（空维网格=装配缺陷，GR-14）")
    return field_id, values


def _dtype(fields: tuple[str, ...]) -> numpy.dtype[numpy.void]:
    """R4：经 dimensions.dtype_of 生成；未登记字段按同款形态就地构造（注记）。"""
    try:
        return dtype_of(fields)
    except InvalidDimensionError:
        return numpy.dtype([(field_id, "<f8") for field_id in fields])


def build_grid(param_specs: Sequence[ParamSpec | Mapping[str, Any]]) -> Grid:
    """构建正门：逐维声明归一（字典序稳定）→ 护栏校验 → 笛卡尔积展平。"""
    if not param_specs:
        raise InvalidGridError(
            "网格声明为空：无自由参数的枚举=装配缺陷（GR-14 空集显式语义）"
        )
    dimensions = [_dimension(entry, index) for index, entry in enumerate(param_specs)]
    dimensions.sort(key=lambda item: item[0])  # R2：field_id 字典序稳定
    seen: set[str] = set()
    for field_id, _ in dimensions:
        if field_id in seen:
            raise InvalidGridError(f"网格字段重复：{field_id!r}（dtype 列名唯一）")
        seen.add(field_id)
    fields = tuple(field_id for field_id, _ in dimensions)
    values = tuple(vals for _, vals in dimensions)
    shape = tuple(len(vals) for vals in values)
    total = prod(shape)
    base = assumption(_BASE_KEY, {})
    limit = base ** len(fields)
    if total > limit:
        raise GridTooLarge(
            f"网格组合数 {total} 超护栏 base**k = {limit:g}"
            f"（base={_BASE_KEY}={base:g}，k={len(fields)}——§12.4 ≤4^k；"
            "建议缩小某维步长/范围或减少枚举维数）"
        )
    array = numpy.empty(total, dtype=_dtype(fields))
    for row, combo in enumerate(product(*values)):
        for field_id, value in zip(fields, combo, strict=True):
            array[row][field_id] = value
    return Grid(fields=fields, array=array, shape=shape, total=total)
