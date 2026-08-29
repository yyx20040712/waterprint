"""cost 服务用例：最近完成结果集 → 概算表+指标校核（core cost 四模块装配）。

输入:  项目 id + condition_key（可选——缺省="design"基线档，显式回显）
输出:  CostResponse（server 侧 pydantic 冻结模型——routers 直用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（FE8 D1~D4 2026-08-29；镜像测试 server/tests/test_cost.py）
#
# 【公开接口】
#   build_cost_for_project(ctx, project_id, condition_key=None)
#       -> CostResponse（cost 数据通道服务面正门）
#   CostResponse/EstimateSheetModel/EstimateRowModel/FeeLineModel/
#   ReproModel/IndicatorReportModel/IndicatorReadingModel/BandModel
#       （响应模型面——routers response_model 直用，elevation 服务层
#       pydantic 冻结模型先例：禁协议层重复声明漂移面）
#   CostSourceNotFoundError（404 面）/InvalidCostRequestError（422 面）
#
# 【行为规格】
#   R1 取数（最近完成结果集）：_latest_calc_result 复制 services/scene
#      同款取数模式（遍历 task_ids_for_project 取最末 done calc 的
#      status.result——消费时实时取，UF-37 统一口径；不 import scene
#      私有名，FE1 简报条款）；无结果集=CostSourceNotFoundError（404，
#      消息含"先 POST /api/calc/run"）；结果文件缺失/损坏（OSError/
#      InvalidResultError）同归 404 面（FE1 M4 路径安全族——裸 500 禁）。
#   R2 工况缺省="design"（D2——cost 规格头 R4 默认基线档，优先于
#      elevation 排序首键先例；显式回显于响应 condition_key 与
#      sheet.condition_key 双面）；工况不在结果=core.takeoff 的
#      InvalidTakeoffError 转 InvalidCostRequestError（422 面，消息
#      透传含可用工况集）。
#   R3 装配口径（D1——golden test_municipal_e2e._m3_real_values 同款
#      四模块链，服务端单点）：load_prices(data_dir/unit_prices)→
#      load_fee_rules(field_mapping.yaml)→takeoff_quantities→
#      build_estimate（repro=plant.repro 三元组注入——estimate 头注
#      "app 装配层应传 PlantResult.repro 面"落点）→check_indicators。
#      计算在 Python 单点（estimate R2 §11 R12）——前端零算价。
#   R4 design_scale 服务面注入（D3；R1 修复轮 2026-08-29 改快照侧）：
#      结果集快照 conditions[chosen] 各单元 outflows 的
#      *.out.q_avg_daily（m3/s，golden 口径——inlet=0.4023229167）×86400
#      换算经 contracts.quantity pint 正门（禁手写换算系数——quantity
#      禁止面；indicators 头注"换算属显示层/装配层口径"=本层合规）；
#      outflows 键域=单元实跑输出面，天然限定输入单元（zM-1 收窄）；
#      无该键=InvalidCostRequestError（422——规模无定义显式拒绝）。
#      快照侧消除"表=旧快照+规模=新活档"混搭（二审 yI-2 构造实证：
#      活档侧 PUT 改档不重算→scale 漂移 17280/indicator 689.15——
#      编辑未重算时 scale 随表冻结，与表同源）。
#      IndicatorReport WARN 如实下发（诚实读数——前端橙警非绿）；
#      bands 空→checked:False 显式未校核（core R4）。
#   R5 name_zh 中文列名（D4）：detail_rows 各行附 PriceBook.get(
#      price_key).name——服务端下单数表直投，单一真源（禁前端 i18n
#      双源）。
#   R6 确定性：同结果集同响应（core 纯装配+服务层零随机面——双跑
#      sort_keys 字节同，端点测试常驻断言）。
#
# 【测试要求】缺省工况=design、直调对拍 grand_total、自洽分级、
#   name_zh 中文、WARN 语义、checked 面、422/404 异常面、
#   AU-1 穿越 4xx+目录快照零新增。
#
# 【参照】FE8 简报 D1~D4/D9；scene.py/elevation.py 服务先例；
#   golden core/tests/golden/test_municipal_e2e.py 三正门直调先例；
#   UF-33（waterprint.cost 直连边经 docs/structure-graph.md §1b
#   补登，FE8 D9 总控裁决 2026-08-29）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, ConfigDict
from waterprint.contracts.quantity import DimKey, parse
from waterprint.contracts.result_schema import (
    InvalidResultError,
    PlantResult,
    deserialize,
)
from waterprint.cost.estimate import (
    EstimateSheet,
    FeeLine,
    build_estimate,
    load_fee_rules,
)
from waterprint.cost.indicators import (
    IndicatorReport,
    InvalidIndicatorError,
    check_indicators,
    load_indicator_bands,
)
from waterprint.cost.prices import PriceBook, load_prices
from waterprint.cost.takeoff import (
    InvalidTakeoffError,
    load_field_mapping,
    takeoff_quantities,
)

from waterprint_server.services import ServiceContext
from waterprint_server.services.projects import read_project

__all__ = [
    "CostResponse",
    "CostSourceNotFoundError",
    "EstimateRowModel",
    "EstimateSheetModel",
    "FeeLineModel",
    "IndicatorReadingModel",
    "IndicatorReportModel",
    "InvalidCostRequestError",
    "ReproModel",
    "build_cost_for_project",
]

_FIELD_MAPPING_NAME: Final[str] = "field_mapping.yaml"
# m3/d→m3/s 换算因子经 pint 正门求取（quantity R2"换算必须经 pint 完成，
# 禁止手写换算系数"——服务面 ×86400 口径的唯一合法实现面）。
_M3D_TO_M3S: Final[float] = parse(1.0, "m3/d", DimKey.FLOW)
_DEFAULT_CONDITION: Final[str] = "design"  # D2 缺省基线档（estimate R4）


class CostSourceNotFoundError(RuntimeError):
    """无最近完成结果集可消费——404 面（先运行计算）。"""


class InvalidCostRequestError(ValueError):
    """cost 请求非法（工况不在结果/规模不可推导）——422 面。"""


class ReproModel(BaseModel):
    """可复算三元组（core ReproTriple 序列化形状）。"""

    model_config = ConfigDict(frozen=True)

    design_hash: str
    engine_version: str
    data_version: str


class EstimateRowModel(BaseModel):
    """单笔分部分项（core EstimateRow 八字段+name_zh 中文列名=D4）。"""

    model_config = ConfigDict(frozen=True)

    price_key: str
    name_zh: str
    unit: str
    quantity: float
    unit_price: float
    amount: float
    source_field_ids: tuple[str, ...]
    source: str


class FeeLineModel(BaseModel):
    """单笔费用行（core FeeLine 六字段直投影）。"""

    model_config = ConfigDict(frozen=True)

    fee_key: str
    rate: float
    base: str
    base_amount: float
    amount: float
    source: str


class EstimateSheetModel(BaseModel):
    """概算表（D4 契约面：明细+四费桶+小计族+总价+三元组+工况）。"""

    model_config = ConfigDict(frozen=True)

    detail_rows: tuple[EstimateRowModel, ...]
    measure: tuple[FeeLineModel, ...]
    indirect: tuple[FeeLineModel, ...]
    reserve: tuple[FeeLineModel, ...]
    tax: tuple[FeeLineModel, ...]
    detail_subtotal: float
    equipment_subtotal: float
    construction_subtotal: float
    subtotal: float
    reserve_subtotal: float
    grand_total: float
    repro: ReproModel
    condition_key: str


class BandModel(BaseModel):
    """指标经验带（min/max 成对——D4 嵌套形状）。"""

    model_config = ConfigDict(frozen=True)

    min: float
    max: float


class IndicatorReadingModel(BaseModel):
    """单项指标对照（core IndicatorReading 直投影+band 嵌套）。"""

    model_config = ConfigDict(frozen=True)

    indicator_key: str
    value: float
    band: BandModel
    status: str
    reason: str


class IndicatorReportModel(BaseModel):
    """指标校核报告（readings+checked——空带 checked=False 显式未校核）。"""

    model_config = ConfigDict(frozen=True)

    readings: tuple[IndicatorReadingModel, ...]
    checked: bool


class CostResponse(BaseModel):
    """cost 数据通道响应（D1~D4 契约面：工况索引+版本+规模+表+指标）。"""

    model_config = ConfigDict(frozen=True)

    project_id: str
    condition_key: str
    conditions: tuple[str, ...]
    price_data_version: str
    design_scale: float
    sheet: EstimateSheetModel
    indicators: IndicatorReportModel


def _latest_calc_result(ctx: ServiceContext, project_id: str) -> Mapping[str, Any]:
    """最近完成计算结果集（scene._latest_calc_result 同款取数模式复制）。"""
    latest: Mapping[str, Any] | None = None
    for task_id in ctx.manager.task_ids_for_project(project_id):
        status = ctx.manager.status(task_id)
        if status.kind == "calc" and status.state == "done" and status.result:
            latest = status.result
    if latest is None:
        raise CostSourceNotFoundError(
            f"项目 {project_id!r} 无最近完成结果集（先 POST /api/calc/run）"
        )
    return latest


def _fee_lines(lines: tuple[FeeLine, ...]) -> tuple[FeeLineModel, ...]:
    """费桶行投影（FeeLine 六字段直投影——R3 无推导）。"""
    return tuple(
        FeeLineModel(
            fee_key=line.fee_key,
            rate=line.rate,
            base=line.base,
            base_amount=line.base_amount,
            amount=line.amount,
            source=line.source,
        )
        for line in lines
    )


def _sheet_model(sheet: EstimateSheet, book: PriceBook) -> EstimateSheetModel:
    """EstimateSheet → 响应模型（name_zh 经单价包直投=D4/R5）。"""
    return EstimateSheetModel(
        detail_rows=tuple(
            EstimateRowModel(
                price_key=row.price_key,
                name_zh=book.get(row.price_key).name,
                unit=row.unit,
                quantity=row.quantity,
                unit_price=row.unit_price,
                amount=row.amount,
                source_field_ids=tuple(row.source_field_ids),
                source=row.source,
            )
            for row in sheet.detail_rows
        ),
        measure=_fee_lines(sheet.measure),
        indirect=_fee_lines(sheet.indirect),
        reserve=_fee_lines(sheet.reserve),
        tax=_fee_lines(sheet.tax),
        detail_subtotal=sheet.detail_subtotal,
        equipment_subtotal=sheet.equipment_subtotal,
        construction_subtotal=sheet.construction_subtotal,
        subtotal=sheet.subtotal,
        reserve_subtotal=sheet.reserve_subtotal,
        grand_total=sheet.grand_total,
        repro=ReproModel(
            design_hash=sheet.repro.design_hash,
            engine_version=sheet.repro.engine_version,
            data_version=sheet.repro.data_version,
        ),
        condition_key=sheet.condition_key,
    )


def _report_model(report: IndicatorReport) -> IndicatorReportModel:
    """IndicatorReport → 响应模型（band 嵌套 {min,max}——D4 形状）。"""
    return IndicatorReportModel(
        readings=tuple(
            IndicatorReadingModel(
                indicator_key=reading.indicator_key,
                value=reading.value,
                band=BandModel(min=reading.band[0], max=reading.band[1]),
                status=reading.status,
                reason=reading.reason,
            )
            for reading in report.readings
        ),
        checked=report.checked,
    )


def _design_scale_of(plant: PlantResult, condition_key: str) -> float:
    """设计规模（m3/d）：结果集快照 outflows 取数（D3/R4——R1 快照侧）。

    golden 口径照抄（inlet.out.q_avg_daily=0.4023229167→34760.7 m3/d
    ——二审 §四实测形状：outflows 是结果集唯一合法流量快照面[dims 空/
    summary 仅六水质指标]）；sorted 遍历=确定性取数；outflows 键域=
    单元实跑输出面天然限定输入单元（zM-1 收窄——非输入节点不携
    *.out.q_avg_daily）；换算经 pint 因子（_M3D_TO_M3S）——禁手写
    86400。快照侧与表同源：编辑未重算时 scale 随表冻结（yI-2）。
    """
    units = plant.conditions.get(condition_key, {})
    for unit_id in sorted(units):
        value = units[unit_id].outflows.get(f"{unit_id}.out.q_avg_daily")
        if isinstance(value, bool) or not isinstance(value, int | float):
            continue
        return float(value) / _M3D_TO_M3S
    raise InvalidCostRequestError(
        "结果集快照无 *.out.q_avg_daily 输入节点流量（指标设计规模无定义"
        f"——D3 规模取数面；工况 {condition_key!r} sorted 单元集 "
        f"{sorted(units)}）"
    )


def build_cost_for_project(
    ctx: ServiceContext, project_id: str, condition_key: str | None = None
) -> CostResponse:
    """概算正门：项目校验 → 结果集取数 → 四模块装配 → 指标校核 → 投影。"""
    # 项目存在性校验（不存在=ProjectNotFoundError 404）；R1 后装配数据
    # 全部取自结果集快照（design_scale 同源），项目档本体零消费。
    read_project(ctx, project_id)
    latest = _latest_calc_result(ctx, project_id)
    try:
        plant = deserialize(Path(str(latest["result_file"])).read_bytes())
    except (OSError, InvalidResultError) as exc:
        # FE1 M4（路径安全族）：结果文件缺失/损坏归一 404 领域面——裸 500 禁。
        raise CostSourceNotFoundError(
            f"项目 {project_id!r} 最近结果集不可读（文件缺失/损坏——先重算）：{exc}"
        ) from exc
    chosen = condition_key if condition_key is not None else _DEFAULT_CONDITION
    unit_prices = ctx.settings.data_dir / "unit_prices"
    book = load_prices(unit_prices)
    fees = load_fee_rules(unit_prices / _FIELD_MAPPING_NAME, book)
    mapping = load_field_mapping(unit_prices / _FIELD_MAPPING_NAME)
    try:
        items = takeoff_quantities(
            plant, chosen, price_book=book, field_mapping=mapping
        )
    except InvalidTakeoffError as exc:
        raise InvalidCostRequestError(str(exc)) from exc  # 透传可用工况集
    sheet = build_estimate(
        items, book, fees, repro=plant.repro, condition_key=chosen
    )
    design_scale = _design_scale_of(plant, chosen)  # R1 快照侧（与表同源）
    try:
        report = check_indicators(
            sheet, load_indicator_bands(book), design_scale=design_scale
        )
    except InvalidIndicatorError as exc:
        raise InvalidCostRequestError(str(exc)) from exc
    return CostResponse(
        project_id=project_id,
        condition_key=sheet.condition_key,
        conditions=tuple(sorted(plant.conditions)),
        price_data_version=book.data_version,
        design_scale=design_scale,
        sheet=_sheet_model(sheet, book),
        indicators=_report_model(report),
    )
