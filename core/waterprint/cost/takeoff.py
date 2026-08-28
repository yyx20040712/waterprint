"""工程量提取：PlantResult 字段 ID → 分部分项工程量清单（零中文匹配）。

输入:  PlantResult（按 condition_key 索引的维度字段数组）
输出:  工程量清单（条目：定额项键 + 数量 + 单位，来自 dimensions 注册字段）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_takeoff.py）
#
# 【公开接口】
#   class TakeoffItem(不可变)：price_key（定额单价键）、quantity、
#       unit、source_field_ids（量来源于哪些结果字段——可审计）
#   takeoff_quantities(plant_result, condition_key) -> tuple[TakeoffItem, ...]
#
# 【行为规格】
#   R1 取数只按字段 ID：清单条目由"字段 ID → 定额项"映射表（数据，
#      data/unit_prices 侧配套）驱动；出现任何中文字符串匹配逻辑
#      = 评审拒绝（病灶根除点，§3 保证 4）。
#   R2 量纲正确：quantity 单位与 price_key 单价单位一致（混凝土 m3、
#      钢筋 t、土方 m3……）；不一致 = 提取错误即抛领域异常。
#   R3 source_field_ids 必填：每个量可回溯到结果字段与工况——审计链路
#      （M4"任一数字可回溯"）在概算侧的落点。
#   R4 按工况提取：condition_key 必填（检修工况的 n-1 池 → 工程量
#      不变还是变化由字段语义决定，但提取结果标注工况）。
#   R5 挖深联动（M3）：土方量消费 elevation.Profile 的实际埋深
#      （由 L4 app 装配传入，本文件不 import elevation——总线原则 §16 A4）。
#
# 【COST2 实装注记】（概算段二，2026-08-28）
#   - 映射数据面 = data/unit_prices/field_mapping.yaml mappings 节
#     （D3 裁决；loader 见 load_field_mapping）。行结构/首版行集口径
#     见该文件头注。
#   - R2 门槛实装点：每行映射 unit 必须与 PriceBook 同键条目 unit
#     完全一致，不一致 = InvalidTakeoffError（含两单位与键名）；
#     映射 price_key 失联 = 同异常（prices R3 双向闭环）。
#   - R3 溯源形态：source_field_ids 存"unit_id.field_id"全限定名
#     （dims 字段按单元隔离，全限定才可回溯到结果字段与工况）。
#   - R4：condition_key 空白或不在 conditions = 领域异常（禁静默取
#      "任意工况"）；条目挂 condition_key 标注。
#   - R5 挂账：首版土方=池容直取近似（field_mapping 注记）；挖深联动
#     归段三（elevation.Profile 通道由 app 装配传入——本文件零
#     elevation import）。
#   - 默认装载：price_book/field_mapping 省略时经模块相对路径定位
#     仓库 data/unit_prices（结构图谱声明的 cost→data 消费通道）；
#     测试与装配层可注入构造面。
#   - 取数零中文匹配：dims 键查表（dict get），无任何 str.find/in
#     判定逻辑（grep 门禁红线）。
#
# 【测试要求】字段 ID 映射正确、单位不匹配拒绝、source_field_ids 完整、
#   静态断言：源码无中文匹配 API 调用（如 str.find/in 判定）。
#
# 【参照】重写计划 §13.3/§16 A4；数据包 data/unit_prices/README.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import final

import yaml

from waterprint.contracts.result_schema import PlantResult
from waterprint.cost.prices import InvalidPriceError, PriceBook, load_prices


class InvalidTakeoffError(Exception):
    """工程量提取非法（工况缺失/单位不一致/失联键/映射结构）——领域异常。"""


# 仓库 data/unit_prices（cost→data 声明边的运行期定位；.parent 链零
# 数值字面量：takeoff.py → cost → waterprint → core → 仓库根）。
DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "unit_prices"
)
_FIELD_MAPPING_NAME = "field_mapping.yaml"

_MODE_DIRECT = "direct"
_MODE_COUNT_TIMES_VALUE = "count_times_value"
_MODES = frozenset({_MODE_DIRECT, _MODE_COUNT_TIMES_VALUE})
_COST_CLASSES = frozenset({"civil", "equipment"})

_MAPPING_REQUIRED = frozenset(
    {"price_key", "unit", "mode", "source_field_ids", "cost_class", "source"}
)


def _load_yaml(path: Path, what: str) -> object:
    """yaml.safe_load 唯一入口：解析/解码异常 from exc 包装（prices 同 idiom）。"""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        reason = (
            f"解码失败（非 UTF-8）：{exc}"
            if isinstance(exc, UnicodeDecodeError)
            else f"YAML 解析失败：{exc}"
        )
        raise InvalidTakeoffError(f"{what} {path.name} {reason}") from exc


def _nonempty_str(value: object, what: str) -> str:
    """字符串守卫：非空 str（空串/空白/异类型均拒，消息含字段名）。"""
    if not isinstance(value, str) or not value.strip():
        raise InvalidTakeoffError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


@dataclass(frozen=True)
@final
class QuantityRule:
    """单条映射行：定额键+计量单位+取法+字段 ID 集（+限定单元/费用类）。"""

    price_key: str
    unit: str
    mode: str
    source_field_ids: tuple[str, ...]
    cost_class: str
    source: str
    unit_id: str | None = None


@dataclass(frozen=True)
@final
class FieldMapping:
    """不可变映射集（R1 数据驱动的"字段 ID → 定额项"真源快照）。"""

    rules: tuple[QuantityRule, ...]


@dataclass(frozen=True)
@final
class TakeoffItem:
    """单条清单条目：定额键/数量/单位/溯源字段集（+费用类与工况标注）。"""

    price_key: str
    quantity: float
    unit: str
    source_field_ids: tuple[str, ...]
    cost_class: str
    condition_key: str


def _parse_rule(where: str, raw: object) -> QuantityRule:
    """单行守卫：键集恰必填+可选 unit_id；mode/cost_class/字段数逐项校验。"""
    if not isinstance(raw, dict):
        raise InvalidTakeoffError(
            f"映射行形态非法（{where}）：须为映射，得到 {type(raw).__name__}"
        )
    given = set(raw)
    missing = _MAPPING_REQUIRED - given
    unknown = given - _MAPPING_REQUIRED - {"unit_id"}
    if missing or unknown:
        raise InvalidTakeoffError(
            f"映射行键集非法（{where}）：缺 {sorted(missing)}，多 "
            f"{sorted(unknown)}（必填 {sorted(_MAPPING_REQUIRED)}，可选 "
            "['unit_id']——多键少键均拒，防拼写静默）"
        )
    price_key = _nonempty_str(raw["price_key"], f"映射行 price_key（{where}）")
    mode = _nonempty_str(raw["mode"], f"映射 {price_key!r} 的 mode")
    if mode not in _MODES:
        raise InvalidTakeoffError(
            f"映射 {price_key!r} 的 mode 非法：{mode!r}（合法 {sorted(_MODES)}）"
        )
    fields_raw = raw["source_field_ids"]
    if not isinstance(fields_raw, list) or not fields_raw:
        raise InvalidTakeoffError(
            f"映射 {price_key!r} 的 source_field_ids 必须为非空列表"
            f"（R3 溯源必填）：得到 {fields_raw!r}"
        )
    expected = 1 if mode == _MODE_DIRECT else 2
    if len(fields_raw) != expected:
        raise InvalidTakeoffError(
            f"映射 {price_key!r} 的 source_field_ids 应恰 {expected} 个"
            f"（mode={mode}）：得到 {len(fields_raw)} 个"
        )
    cost_class = _nonempty_str(
        raw["cost_class"], f"映射 {price_key!r} 的 cost_class"
    )
    if cost_class not in _COST_CLASSES:
        raise InvalidTakeoffError(
            f"映射 {price_key!r} 的 cost_class 非法：{cost_class!r}"
            f"（合法 {sorted(_COST_CLASSES)}——estimate 设备费基数分拣依据）"
        )
    unit_id_raw = raw.get("unit_id")
    return QuantityRule(
        price_key=price_key,
        unit=_nonempty_str(raw["unit"], f"映射 {price_key!r} 的 unit"),
        mode=mode,
        source_field_ids=tuple(
            _nonempty_str(field, f"映射 {price_key!r} 的 source_field_ids 成员")
            for field in fields_raw
        ),
        cost_class=cost_class,
        source=_nonempty_str(raw["source"], f"映射 {price_key!r} 的 source"),
        unit_id=(
            None
            if unit_id_raw is None
            else _nonempty_str(unit_id_raw, f"映射 {price_key!r} 的 unit_id")
        ),
    )


def load_field_mapping(path: str | Path) -> FieldMapping:
    """映射装载正门：field_mapping.yaml mappings 节严格校验 → FieldMapping。"""
    file = Path(path)
    if not file.is_file():
        raise InvalidTakeoffError(
            f"字段映射文件不存在：{file}（takeoff R1 数据面，D3 最小集）"
        )
    data = _load_yaml(file, "映射文件")
    if not isinstance(data, dict):
        raise InvalidTakeoffError(
            f"映射文件顶层须为映射：得到 {type(data).__name__}"
        )
    unknown_sections = sorted(set(data) - {"mappings", "fee_rules"})
    if unknown_sections:
        raise InvalidTakeoffError(
            f"映射文件含未知节：{unknown_sections}（只允许 mappings/fee_rules）"
        )
    rows = data.get("mappings")
    if not isinstance(rows, list) or not rows:
        raise InvalidTakeoffError(
            "映射文件 mappings 节必须为非空列表"
            "（GR-14 空集显式：无映射=装配缺陷，禁静默空清单）"
        )
    return FieldMapping(
        rules=tuple(_parse_rule(f"mappings[{index}]", raw) for index, raw in enumerate(rows))
    )


def _resolve_quantity(
    dims: Mapping[str, float], rule: QuantityRule
) -> float | None:
    """单规则×单单元取数：字段齐备按 mode 计算；字段缺失=不适用（None）。

    零中文匹配：dims 查表取值（dict 键命中），无任何子串/列表扫描逻辑。
    """
    values: list[float] = []
    for field in rule.source_field_ids:
        if field not in dims:
            return None
        value = dims[field]
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise InvalidTakeoffError(
                f"字段 {field!r} 的值必须为数值：得到 {value!r}"
                f"（类型 {type(value).__name__}）"
            )
        values.append(float(value))
    if rule.mode == _MODE_COUNT_TIMES_VALUE:
        return values[0] * values[1]
    return values[0]


def _check_rule_against_book(rule: QuantityRule, price_book: PriceBook) -> None:
    """R2+R3 前置静态校验：失联键/单位不一致 → 领域异常（消息含键与单位）。"""
    try:
        item = price_book.get(rule.price_key)
    except InvalidPriceError as exc:
        raise InvalidTakeoffError(
            f"映射行失联定额键：{rule.price_key!r}（单价包 "
            f"price_data_version={price_book.data_version} 无法解析——"
            "prices R3 同门槛）"
        ) from exc
    if rule.unit != item.unit:
        raise InvalidTakeoffError(
            f"映射单位与单价单位不一致：{rule.price_key!r} 映射记 "
            f"{rule.unit!r}，单价条目为 {item.unit!r}"
            "（R2 量纲门槛——不一致即提取错误，禁静默换算）"
        )


def takeoff_quantities(
    plant_result: PlantResult,
    condition_key: str,
    *,
    price_book: PriceBook | None = None,
    field_mapping: FieldMapping | None = None,
) -> tuple[TakeoffItem, ...]:
    """工程量提取正门：工况内逐单元×逐规则取数（R1~R4）。

    冻结入口 (plant_result, condition_key) 可单独调用——省略注入时
    经默认数据面装载（结构图谱 cost→data 声明边）。
    """
    if not isinstance(condition_key, str) or not condition_key.strip():
        raise InvalidTakeoffError(
            "condition_key 必填且非空白（R4 按工况提取——禁静默取任意工况）"
        )
    units = plant_result.conditions.get(condition_key)
    if units is None:
        raise InvalidTakeoffError(
            f"工况不存在：{condition_key!r}"
            f"（可用工况 {sorted(plant_result.conditions)}——R4 显式拒绝）"
        )
    book = price_book
    if book is None:
        book = load_prices(DEFAULT_DATA_DIR)
    mapping = field_mapping
    if mapping is None:
        mapping = load_field_mapping(DEFAULT_DATA_DIR / _FIELD_MAPPING_NAME)
    for rule in mapping.rules:
        _check_rule_against_book(rule, book)
    items: list[TakeoffItem] = []
    for unit_id in sorted(units):
        if not isinstance(unit_id, str):
            raise InvalidTakeoffError(
                f"工况 {condition_key!r} 含非字符串单元键：{unit_id!r}"
            )
        snapshot = units[unit_id]
        for rule in mapping.rules:
            if rule.unit_id is not None and rule.unit_id != unit_id:
                continue
            quantity = _resolve_quantity(snapshot.dims, rule)
            if quantity is None:
                continue
            items.append(
                TakeoffItem(
                    price_key=rule.price_key,
                    quantity=quantity,
                    unit=rule.unit,
                    source_field_ids=tuple(
                        f"{unit_id}.{field}" for field in rule.source_field_ids
                    ),
                    cost_class=rule.cost_class,
                    condition_key=condition_key,
                )
            )
    return tuple(items)


def default_field_mapping_path() -> Path:
    """默认映射文件路径（装配层/探针消费）。"""
    return DEFAULT_DATA_DIR / _FIELD_MAPPING_NAME
