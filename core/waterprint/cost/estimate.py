"""概算汇总：分部分项 + 措施 + 间接 + 预备 + 税（计算全部在 Python，模板只展示）。

输入:  工程量清单（takeoff）+ PriceBook（单价）
输出:  概算表（分级汇总结构，含每一笔的单价×数量可追溯记录）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/cost/test_estimate.py）
#
# 【公开接口】
#   build_estimate(quantities, price_book,
#                  fee_config) -> EstimateSheet
#   class EstimateSheet(不可变)：
#       detail_rows（分部分项：价 = 量 × 单价，逐笔挂 price_key 与
#                    source_field_ids）
#       measure / indirect / reserve / tax：各级费用行（费率出处必填）
#       grand_total
#       repro（design_hash, engine_version, data_version 三元组）
#   class FeeRule：fee_key、rate、base（取费基数表达式 DSL）、source
#
# 【行为规格】
#   R1 费率是数据：措施/间接/预备/税率的取值与取费基数全部来自
#      fee_config（数据包，带出处）；代码零费率常量。
#   R2 计算在 Python 单点完成（§11 R12）：Excel 输出只是渲染——
#      模板禁止 Excel 公式，渲染器见 trace/calcbook.py。
#   R3 汇总可复算：grand_total = f(工程量, 单价, 费率)，确定性；
#      同输入双跑字节级相同；结果挂三元组。
#   R4 工况标注：概算基于哪个 condition_key 的工程量必须显式
#      （默认基线 design 档；检修工况变化量由用户选择后单独出表）。
#
# 【COST2 实装注记】（概算段二，2026-08-28）
#   - 费率数据链：rate 值经 PriceBook.get(fee_key).price 消费
#     auxiliary.yaml rate.* 条目（dimensionless 守卫）；base DSL 与
#     归桶在 field_mapping.yaml fee_rules 节（load_fee_rules 装载，
#     冻结 §二.5 裁决——代码零费率零基数）。
#   - base DSL = contracts.expr 受限表达式；命名基数集（求值环境，
#     固定序 measure→indirect→reserve→tax 渐进可用）：
#       detail_subtotal        分部分项小计（Σ明细）
#       equipment_subtotal     设备费小计（Σ cost_class=equipment 明细）
#       construction_subtotal  建安费（detail+measure，measure 桶后可用）
#       subtotal               小计（construction+indirect，indirect 后）
#       reserve_subtotal       预备费小计（reserve 桶后可用）
#     取费语义（auxiliary note 同源）：安装=设备×15%、管理/设计/监理/
#     前期=建安×率、预备=小计×10%、税=(小计+预备)×9%。
#   - repro：data_version=PriceBook.price_data_version（R2 三元组联动
#     ——单价包升版即旧概算过期）；design_hash/engine_version 经
#     repro 参数注入（app 装配层传递 PlantResult.repro 面）。
#   - 分级自洽（测试要求落点）：grand_total = subtotal +
#     reserve_subtotal + Σtax；subtotal = construction_subtotal +
#     Σindirect；construction = detail_subtotal + Σmeasure。
#
# 【测试要求】分级汇总数字自洽（明细求和=小计、小计+费用=总价）、
#   费率缺出处拒绝、双跑确定性、三元组记录。
#
# 【参照】重写计划 §11 R12/§13.3/§16 A8
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import final

import yaml

from waterprint.contracts.expr import eval_checked, parse_checked
from waterprint.contracts.result_schema import ReproTriple
from waterprint.cost.prices import InvalidPriceError, PriceBook
from waterprint.cost.takeoff import TakeoffItem


class InvalidEstimateError(Exception):
    """概算汇总非法（费率缺出处/基数 DSL 非法/失联键/单位不一致）——领域异常。"""


_FIELD_MAPPING_NAME = "field_mapping.yaml"
_RATE_UNIT = "dimensionless"
_FEE_RULE_KEYS = frozenset({"fee_key", "bucket", "base", "source"})
BUCKETS: tuple[str, ...] = ("measure", "indirect", "reserve", "tax")
_BASE_NAMES = frozenset(
    {
        "detail_subtotal",
        "equipment_subtotal",
        "construction_subtotal",
        "subtotal",
        "reserve_subtotal",
    }
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
        raise InvalidEstimateError(f"{what} {path.name} {reason}") from exc


def _nonempty_str(value: object, what: str) -> str:
    """字符串守卫：非空 str（空串/空白/异类型均拒，消息含字段名）。"""
    if not isinstance(value, str) or not value.strip():
        raise InvalidEstimateError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


@dataclass(frozen=True)
@final
class FeeRule:
    """单条费率规则：键/费率/取费基数 DSL/出处/归桶（R1 全数据面）。"""

    fee_key: str
    rate: float
    base: str
    source: str
    bucket: str

    def __post_init__(self) -> None:
        """守卫：bucket 在册 / rate 有限且为 [0,1] 费率域 / 出处非空白。"""
        if self.bucket not in BUCKETS:
            raise InvalidEstimateError(
                f"费率 {self.fee_key!r} 的 bucket 非法：{self.bucket!r}"
                f"（合法 {list(BUCKETS)}——分级归桶，求值序即此序）"
            )
        rate = self.rate
        if not isinstance(rate, int | float) or isinstance(rate, bool):
            raise InvalidEstimateError(
                f"费率 {self.fee_key!r} 的 rate 必须为数值：得到 {rate!r}"
            )
        if not math.isfinite(float(rate)) or not 0 <= float(rate) <= 1:
            raise InvalidEstimateError(
                f"费率 {self.fee_key!r} 的 rate 越出费率域 [0,1]：{rate!r}"
                "（R1 数据面守卫——费率是数据，数据也要过门槛）"
            )
        if not _nonempty_str(self.source, f"费率 {self.fee_key!r} 的 source").strip():
            raise InvalidEstimateError(
                f"费率 {self.fee_key!r} 的 source 不能为空白串（R1：费率缺出处拒绝）"
            )


@dataclass(frozen=True)
@final
class EstimateRow:
    """单笔分部分项：单价×数量可追溯记录（挂 price_key 与 source_field_ids）。"""

    price_key: str
    unit: str
    quantity: float
    unit_price: float
    amount: float
    source_field_ids: tuple[str, ...]
    source: str


@dataclass(frozen=True)
@final
class FeeLine:
    """单笔费用行：费率×基数=金额（挂费率出处——R1 出处必填落点）。"""

    fee_key: str
    rate: float
    base: str
    base_amount: float
    amount: float
    source: str


@dataclass(frozen=True)
@final
class EstimateSheet:
    """概算表：分级汇总结构（各级小计显式——逐级求和自洽可断言）。"""

    detail_rows: tuple[EstimateRow, ...]
    measure: tuple[FeeLine, ...]
    indirect: tuple[FeeLine, ...]
    reserve: tuple[FeeLine, ...]
    tax: tuple[FeeLine, ...]
    detail_subtotal: float
    equipment_subtotal: float
    construction_subtotal: float
    subtotal: float
    reserve_subtotal: float
    grand_total: float
    repro: ReproTriple
    condition_key: str


def _parse_fee_rule(where: str, raw: object, price_book: PriceBook) -> FeeRule:
    """fee_rules 行 → FeeRule：键集恰四键；rate 经单价包 rate.* 读出（R1）。"""
    if not isinstance(raw, dict):
        raise InvalidEstimateError(
            f"费率行形态非法（{where}）：须为映射，得到 {type(raw).__name__}"
        )
    given = set(raw)
    missing = _FEE_RULE_KEYS - given
    unknown = given - _FEE_RULE_KEYS
    if missing or unknown:
        raise InvalidEstimateError(
            f"费率行键集非法（{where}）：缺 {sorted(missing)}，多 "
            f"{sorted(unknown)}（应恰为 {sorted(_FEE_RULE_KEYS)}）"
        )
    fee_key = _nonempty_str(raw["fee_key"], f"费率行 fee_key（{where}）")
    try:
        rate_item = price_book.get(fee_key)
    except InvalidPriceError as exc:
        raise InvalidEstimateError(
            f"费率键失联：{fee_key!r}（单价包 price_data_version="
            f"{price_book.data_version} 无此 rate.* 条目——费率值必须经"
            "数据包消费，R1 代码零费率）"
        ) from exc
    if rate_item.unit != _RATE_UNIT:
        raise InvalidEstimateError(
            f"费率键 {fee_key!r} 单位须为 {_RATE_UNIT!r}：得到 {rate_item.unit!r}"
            "（rate.* 条目是费率不是单价）"
        )
    return FeeRule(
        fee_key=fee_key,
        rate=rate_item.price,
        base=_nonempty_str(raw["base"], f"费率 {fee_key!r} 的 base"),
        source=_nonempty_str(raw["source"], f"费率 {fee_key!r} 的 source"),
        bucket=_nonempty_str(raw["bucket"], f"费率 {fee_key!r} 的 bucket"),
    )


def load_fee_rules(path: str | Path, price_book: PriceBook) -> tuple[FeeRule, ...]:
    """费率装载正门：field_mapping.yaml fee_rules 节 + 单价包 rate.* 合成。"""
    file = Path(path)
    if not file.is_file():
        raise InvalidEstimateError(
            f"费率 DSL 文件不存在：{file}（estimate R1 数据面，field_mapping.yaml）"
        )
    data = _load_yaml(file, "费率文件")
    if not isinstance(data, dict):
        raise InvalidEstimateError(
            f"费率文件顶层须为映射：得到 {type(data).__name__}"
        )
    unknown_sections = sorted(set(data) - {"mappings", "fee_rules"})
    if unknown_sections:
        raise InvalidEstimateError(
            f"费率文件含未知节：{unknown_sections}（只允许 mappings/fee_rules）"
        )
    rows = data.get("fee_rules")
    if not isinstance(rows, list) or not rows:
        raise InvalidEstimateError(
            "fee_rules 节必须为非空列表（GR-14 空集显式：无费率=装配缺陷）"
        )
    return tuple(
        _parse_fee_rule(f"fee_rules[{index}]", raw, price_book)
        for index, raw in enumerate(rows)
    )


def _detail_rows(
    quantities: Sequence[TakeoffItem], price_book: PriceBook
) -> tuple[tuple[EstimateRow, ...], float, float]:
    """分部分项逐笔：量×单价（失联键/单位不一致拒），返回（行, 小计, 设备小计）。"""
    rows: list[EstimateRow] = []
    detail_subtotal = 0.0
    equipment_subtotal = 0.0
    for item in quantities:
        try:
            price = price_book.get(item.price_key)
        except InvalidPriceError as exc:
            raise InvalidEstimateError(
                f"工程量条目失联定额键：{item.price_key!r}（单价包 "
                f"price_data_version={price_book.data_version}——takeoff R3 "
                "同门槛双保险）"
            ) from exc
        if item.unit != price.unit:
            raise InvalidEstimateError(
                f"工程量单位与单价单位不一致：{item.price_key!r} 量记 "
                f"{item.unit!r}，单价条目为 {price.unit!r}"
                "（R2 量纲门槛——禁静默换算）"
            )
        amount = item.quantity * price.price
        rows.append(
            EstimateRow(
                price_key=item.price_key,
                unit=price.unit,
                quantity=item.quantity,
                unit_price=price.price,
                amount=amount,
                source_field_ids=tuple(item.source_field_ids),
                source=price.source,
            )
        )
        detail_subtotal += amount
        if item.cost_class == "equipment":
            equipment_subtotal += amount
    return tuple(rows), detail_subtotal, equipment_subtotal


def _eval_base(rule: FeeRule, env: Mapping[str, float]) -> float:
    """base DSL 求值：contracts.expr 受限表达式（引用名限命名基数集）。"""
    parsed = parse_checked(rule.base, frozenset(_BASE_NAMES))
    value = eval_checked(parsed, env)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidEstimateError(
            f"费率 {rule.fee_key!r} 的 base 求值结果须为数值：{rule.base!r} → {value!r}"
        )
    number = float(value)
    if not math.isfinite(number):
        raise InvalidEstimateError(
            f"费率 {rule.fee_key!r} 的 base 求值结果非有限：{rule.base!r} → {number!r}"
        )
    return number


def _bucket_lines(
    rules: Iterable[FeeRule], bucket: str, env: Mapping[str, float]
) -> tuple[FeeLine, ...]:
    """单桶逐行：base×rate=金额（费率出处随行——R1 出处必填）。"""
    lines: list[FeeLine] = []
    for rule in rules:
        if rule.bucket != bucket:
            continue
        base_amount = _eval_base(rule, env)
        lines.append(
            FeeLine(
                fee_key=rule.fee_key,
                rate=rule.rate,
                base=rule.base,
                base_amount=base_amount,
                amount=base_amount * rule.rate,
                source=rule.source,
            )
        )
    return tuple(lines)


def build_estimate(
    quantities: Sequence[TakeoffItem],
    price_book: PriceBook,
    fee_rules: Sequence[FeeRule],
    *,
    repro: ReproTriple | None = None,
    condition_key: str = "design",
) -> EstimateSheet:
    """概算汇总正门：明细逐笔 → 四桶费用（固定序）→ grand_total（R2 单点）。

    repro 省略时 data_version 取单价包 price_data_version、design_hash/
    engine_version 记空串占位（app 装配层应传 PlantResult.repro 面）。
    """
    rows, detail_subtotal, equipment_subtotal = _detail_rows(quantities, price_book)
    env: dict[str, float] = {
        "detail_subtotal": detail_subtotal,
        "equipment_subtotal": equipment_subtotal,
    }
    measure = _bucket_lines(fee_rules, "measure", env)
    construction_subtotal = detail_subtotal + sum(
        line.amount for line in measure
    )
    env["construction_subtotal"] = construction_subtotal
    indirect = _bucket_lines(fee_rules, "indirect", env)
    subtotal = construction_subtotal + sum(line.amount for line in indirect)
    env["subtotal"] = subtotal
    reserve = _bucket_lines(fee_rules, "reserve", env)
    reserve_subtotal = sum(line.amount for line in reserve)
    env["reserve_subtotal"] = reserve_subtotal
    tax = _bucket_lines(fee_rules, "tax", env)
    grand_total = subtotal + reserve_subtotal + sum(line.amount for line in tax)
    triple = ReproTriple("", "", price_book.data_version)
    if repro is not None:
        triple = repro
    return EstimateSheet(
        detail_rows=rows,
        measure=measure,
        indirect=indirect,
        reserve=reserve,
        tax=tax,
        detail_subtotal=detail_subtotal,
        equipment_subtotal=equipment_subtotal,
        construction_subtotal=construction_subtotal,
        subtotal=subtotal,
        reserve_subtotal=reserve_subtotal,
        grand_total=grand_total,
        repro=triple,
        condition_key=condition_key,
    )
