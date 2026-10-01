"""概算表 xlsx 直写渲染件（案乙）：EstimateFlowResult → 汇总+指标校核两表。

输入:  flows.estimate_summary_flow 产物 EstimateFlowResult（sheet/report/book）
输出:  单文件 .xlsx（零公式——全部数值 Python 投递；字节确定性=共享件）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（est-20261001 §三 D1/D3——主控终裁案乙 openpyxl 直写，非案甲
#   calcbook 模板机制：概算表=动态行数分级汇总表，calcbook 占位符语法
#   无行展开语义；代码直写先例=render_audit_html（HTML）/drafting 全族
#   （DXF）；模板机制归 UF-16 录入批。镜像测试 tests/trace/test_estimate_
#   sheet.py）
#
# 【公开接口】
#   render_estimate_xlsx(outcome, out: Path) -> Path
#   class InvalidEstimateRenderError(Exception)（回炉轮1 R7——GR-11 族）
#       outcome=flows.EstimateFlowResult 值（D2 签名；静态注解=结构化
#       Protocol _EstimateOutcome——trace→flows 上行边禁 import，含
#       TYPE_CHECKING 面；audit.py 代码直写同域先例，渲染件零业务计算
#       ——全部数值投递自 EstimateSheet/FeeLine/IndicatorReading 字段）
#
# 【行为规格】
#   R1 内容契约（D3 最小列契约，版式细节执行者自裁）：
#       ①概算汇总表——抬头（工况 condition_key+三元组 design_hash/
#       engine_version/data_version——HTML 审计报告头部自证同款口径）
#       +金额单位=元（批6d 折元口径，表头注明）；分部分项逐行=序号/
#       名称（book.get(price_key).name——渲染名称列单一真源=单价包
#       name 直投，services/cost.py R5 同源口径）/单位/数量/单价/合价/
#       出处（price source）；措施/间接/预备/税各桶 FeeLine 行=名称
#       （fee_key）/费率/基数（base DSL 文本）/基数金额/金额/出处；
#       各级小计（detail/construction/subtotal/reserve）+工程概算总计
#       grand_total 显式行。
#       ②指标校核表——逐 IndicatorReading=指标键/值/带（下限/上限两列
#       ——版式自裁）/状态（OK|WARN）/原因；checked=False 时显式
#       「未校核」行（indicators R4 禁静默通过）。
#   R2 零公式：全部单元格 Python 值投递（计算单一事实源在 cost——
#       本件零业务计算零 Excel 公式）；回炉轮1 R5 起落盘前经共享
#       check_no_formulas 防御（'=' 前缀透传串拒——InvalidEstimateRenderError）。
#   R2b 渲染域异常族（回炉轮1 R7）：失联单价键/不可达报告态显式
#       InvalidEstimateRenderError（GR-11 族——flow 面包装 InvalidFlowError）。
#   R3 字节确定性：保存经 xlsx_save 共享件（modified 归一+ZipInfo 纪元）
#       +新工作簿 created 锚定固定纪元（fixed_created——模板属性面
#       无传递源，渲染时钟不入产物）；同 outcome 双渲染字节相同。
#
# 【数值纪律】零魔法数字（仅序号种子 enumerate start=1 白名单值；
#   固定纪元经 xlsx_save 单源解析——无其余数值字面量）。〔回炉轮1 R9
#   改述：原「零数值字面量」与 enumerate(start=1) 自相矛盾。〕
#
# 【禁止事项】禁 import flows（L4 层序上行边——import-linter 对
#   TYPE_CHECKING 导入同样计边，注解走结构化 Protocol）；禁业务计算
#   （R2）；禁中文字符串匹配取数（cost 族铁律）。
#
# 【测试要求】tests/trace/test_estimate_sheet.py（内容契约/零公式/
#   隔秒双渲染字节恒等+modified==定值/未校核显式行）。
# 【参照】est-20261001 任务书 §三 D1~D3；estimate.py R2/R4；audit.py
#   直写先例；xlsx_save.py R4 机制单源
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from waterprint.cost.estimate import EstimateSheet, FeeLine
from waterprint.cost.indicators import IndicatorReport
from waterprint.cost.prices import InvalidPriceError, PriceBook
from waterprint.trace.xlsx_save import (
    check_no_formulas,
    deterministic_save,
    fixed_created,
)

__all__ = ["InvalidEstimateRenderError", "render_estimate_xlsx"]


class InvalidEstimateRenderError(Exception):
    """概算渲染非法（失联单价键/公式注入/不可达报告态）——GR-11 族
    （回炉轮1 R7；flow 面包装 InvalidFlowError，server 禁直连本件）。"""

# 行值域（Worksheet.append 消费面：int 序号/str 文本/float 数值）
type _Row = tuple[int | float | str, ...]


class _EstimateOutcome(Protocol):
    """flows.EstimateFlowResult 结构面（sheet/report/book 三属性）。

    层序墙内注解法（自裁申报项）：D2 签名消费 EstimateFlowResult 值，
    但 trace→flows 为 L4 上行边（import-linter 对 TYPE_CHECKING 导入
    同样计边——lint-imports 实证红）；结构化 Protocol 保持值契约与
    mypy strict 双全（runtime duck 型，EstimateFlowResult 天然满足）。"""

    @property
    def sheet(self) -> EstimateSheet: ...

    @property
    def report(self) -> IndicatorReport: ...

    @property
    def book(self) -> PriceBook: ...


_SHEET_SUMMARY = "概算汇总表"
_SHEET_INDICATORS = "指标校核表"
# 汇总表七列（分部分项与费用桶共用列宽形态：合价/金额同列位——小计行锚）
_DETAIL_HEADER: tuple[str, ...] = (
    "序号", "名称", "单位", "数量", "单价", "合价", "出处",
)
_FEE_HEADER: tuple[str, ...] = (
    "序号", "名称", "费率", "基数", "基数金额", "金额", "出处",
)


def _subtotal_row(label: str, value: float) -> _Row:
    """小计行（标签住名称列、数值住合价/金额列位——两桶共用锚）。"""
    return ("", label, "", "", "", value, "")


def _detail_rows(outcome: _EstimateOutcome) -> list[_Row]:
    """分部分项逐行：名称列=book.get(price_key).name（单一真源直投）。

    回炉轮1 R7：失联键显式拒（InvalidEstimateRenderError from
    InvalidPriceError——零静默跳行/零裸族逃逸）。"""
    rows: list[_Row] = []
    for index, row in enumerate(outcome.sheet.detail_rows, start=1):
        try:
            name = outcome.book.get(row.price_key).name
        except InvalidPriceError as exc:
            raise InvalidEstimateRenderError(
                f"概算明细行失联单价键：{row.price_key!r}（渲染名称列单一"
                "真源=book.get(price_key).name——book 无此键，禁静默跳行）"
            ) from exc
        rows.append(
            (index, name, row.unit, row.quantity, row.unit_price, row.amount,
             row.source)
        )
    return rows


def _fee_rows(lines: tuple[FeeLine, ...]) -> list[_Row]:
    """单桶费用逐行：名称=fee_key/费率/基数 DSL/基数金额/金额/出处。"""
    return [
        (
            index, line.fee_key, line.rate,
            line.base, line.base_amount, line.amount, line.source,
        )
        for index, line in enumerate(lines, start=1)
    ]


def _section(
    worksheet: Worksheet, title: str, header: tuple[str, ...],
    rows: list[_Row],
) -> None:
    """段块：段题+列表头+数据行（append 序=行序确定性）。"""
    worksheet.append((title,))
    worksheet.append(header)
    for row in rows:
        worksheet.append(row)


def _summary_sheet(workbook: Workbook, outcome: _EstimateOutcome) -> None:
    """①概算汇总表：抬头（工况+三元组+金额单位）→分部分项→四桶→总计。"""
    worksheet = workbook.active
    assert worksheet is not None  # 新建工作簿缺省表恒在（mypy strict 收窄）
    worksheet.title = _SHEET_SUMMARY
    sheet = outcome.sheet
    repro = sheet.repro
    for label, value in (
        ("工况（condition_key）", sheet.condition_key),
        ("design_hash", repro.design_hash),
        ("engine_version", repro.engine_version),
        ("data_version", repro.data_version),
        ("金额单位", "元（批6d 折元口径——单价面值×unit_scales 倍率）"),
    ):
        worksheet.append((label, value))
    _section(
        worksheet, "分部分项工程", _DETAIL_HEADER, _detail_rows(outcome)
    )
    worksheet.append(_subtotal_row("分部分项小计", sheet.detail_subtotal))
    for title, lines, label, subtotal in (
        ("措施费", sheet.measure, "建安费小计（分部分项+措施）",
         sheet.construction_subtotal),
        ("间接费", sheet.indirect, "小计（建安费+间接费）", sheet.subtotal),
        ("预备费", sheet.reserve, "预备费小计", sheet.reserve_subtotal),
    ):
        _section(worksheet, title, _FEE_HEADER, _fee_rows(lines))
        worksheet.append(_subtotal_row(label, subtotal))
    _section(worksheet, "税金", _FEE_HEADER, _fee_rows(sheet.tax))
    worksheet.append(_subtotal_row("工程概算总计", sheet.grand_total))


def _indicator_sheet(workbook: Workbook, report: IndicatorReport) -> None:
    """②指标校核表：逐 IndicatorReading；checked=False 显式未校核行。"""
    worksheet = workbook.create_sheet(_SHEET_INDICATORS)
    worksheet.append((_SHEET_INDICATORS,))
    worksheet.append(("指标键", "值", "带下限", "带上限", "状态", "原因"))
    if report.checked and not report.readings:
        # 回炉轮1 R7（d1-F6）：checked=True 空 readings=装载面守卫应排除的
        # 不可达态——显式拒（禁静默空校核表冒充已校核）。
        raise InvalidEstimateRenderError(
            "指标报告不可达态：checked=True 而 readings 为空"
            "（check_indicators 装载面应保证 checked⇒逐带一行）"
        )
    if not report.checked:
        worksheet.append((
            "未校核", "", "", "", "",
            "数据包无该工程类型指标带（indicators R4——显式未校核，禁静默通过）",
        ))
        return
    for reading in report.readings:
        lower, upper = reading.band
        worksheet.append((
            reading.indicator_key, reading.value, lower, upper,
            reading.status, reading.reason,
        ))


def render_estimate_xlsx(outcome: _EstimateOutcome, out: Path) -> Path:
    """概算表渲染正门：两表直写 → 确定性保存（R2 零公式；返回 out）。"""
    workbook = Workbook()
    workbook.properties.created = fixed_created()  # R3：created 锚定固定纪元
    _summary_sheet(workbook, outcome)
    _indicator_sheet(workbook, outcome.report)
    # 回炉轮1 R5：落盘前禁公式扫描（共享机制——'=' 前缀透传串是真实注入面）。
    check_no_formulas(workbook, InvalidEstimateRenderError)
    out.parent.mkdir(parents=True, exist_ok=True)
    deterministic_save(workbook, out)
    return out
