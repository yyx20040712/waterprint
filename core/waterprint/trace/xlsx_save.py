"""xlsx 字节确定性保存共享件：openpyxl 工作簿 → 时钟归一 zip 落盘。

输入:  openpyxl Workbook + 输出路径（calcbook 模板渲染/estimate 直写渲染）
输出:  字节确定性 .xlsx（双渲染字节相同——R4 机制单源，批 14-FIX）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（est-20261001 D2：_deterministic_save 机制自 calcbook.py 抽出
#   ——含 _MODIFIED_RE/_FIXED_MODIFIED，机制单源防双源漂移〔批 14-FIX
#   历史不二犯〕；calcbook.py 改消费共享件〔行为零变——隔秒双渲染字节
#   恒等测试两处在锁〕；estimate_sheet.py 新直写渲染件同源消费）
#
# 【公开接口】
#   deterministic_save(workbook: Workbook, out: Path) -> None
#   fixed_created() -> datetime（新工作簿 created 锚定固定纪元——直写
#       渲染件时钟面归一；模板渲染件 created 保留=模板属性传递仍锚）
#   check_no_formulas(workbook: Workbook, reject: type[Exception]) -> None
#       （回炉轮1 R5：禁公式扫描机制自 calcbook 抽出共享——调用方注入
#       自有域异常类[calcbook=InvalidTemplateError/estimate_sheet=
#       InvalidEstimateRenderError]，消息含工作表名!坐标 GR-09）
#
# 【行为规格】
#   R4 字节确定性（机制原文自 calcbook.py 迁驻——语义逐字保真）：
#       保存经 ZipInfo 缺省时间戳重写 zip 条目（openpyxl save 默认携带
#       落盘时刻，双渲染字节不同——重写后双渲染字节相同）
#       +core.xml dcterms:modified 值归一定值（批 14-FIX 修复：openpyxl
#       save 链路无条件把 modified 刷新为落盘时刻——构造后/加载后显式
#       赋定值均被覆盖[探针 b14-probe/probe_fixface.py 场景 A/C 实证]，
#       赋值归一路不通，落盘后在 zip 条目链内改写该载荷行；modified
#       =渲染时刻属非内容时钟噪声，归一为固定纪元定值）。
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量（ZipInfo 缺省
#   date_time 即 zip 纪元；固定纪元经字符串定值解析，无 int/float 字面量）。
#
# 【测试要求】消费件各自镜像件锁隔秒双渲染字节恒等+modified==定值
#   （tests/trace/test_calcbook.py + tests/trace/test_estimate_sheet.py
#   两处在锁——共享机制双消费面双保险）。
# 【参照】批 14-FIX（ADR-010 快照回归）；est-20261001 任务书 §三 D2
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Final
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from openpyxl import Workbook

__all__ = ["check_no_formulas", "deterministic_save", "fixed_created"]


def check_no_formulas(workbook: Workbook, reject: type[Exception]) -> None:
    """禁公式扫描（回炉轮1 R5——calcbook._check_no_formulas 机制迁驻共享）：
    遍历全部工作表单元格，data_type=='f' 即以调用方域异常拒。

    openpyxl 对 '=' 开头字符串按公式存储是真实注入面（直写渲染件的
    book name/source/fee_key/base DSL 透传串同守——§11 R12 计算单一
    事实源在 Python，输出只做渲染）。"""
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    raise reject(
                        f"含公式单元格：{sheet.title}!{cell.coordinate}"
                        "（§11 R12——计算单一事实源在 Python，输出只做渲染）"
                    )

# R4 modified 归一面（批 14-FIX 原文迁驻）：正则与快照测试层规范化器同式
# （tests/snapshots/test_snapshots.py _MODIFIED_RE——双保险两层同源）。
_MODIFIED_RE: re.Pattern[bytes] = re.compile(
    rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)"
)
# 归一定值=W3CDTF 固定纪元（与快照测试 _FIXED_EPOCH 同源纪元；字符串
# 非数值字面量——AST 魔法数字门禁面外，dxf_writer _DEFAULT_SCALE 同款口径）。
_FIXED_MODIFIED: Final[str] = "2000-01-01T00:00:00Z"


def fixed_created() -> datetime:
    """固定纪元 datetime（新工作簿 created 锚——直写渲染件时钟面归一）。

    解析自 _FIXED_MODIFIED 单源（零数值字面量）；带时区（W3CDTF Z 尾
    ↔ ISO 8601 +00:00 等价形）。
    """
    return datetime.fromisoformat(_FIXED_MODIFIED.replace("Z", "+00:00"))


def deterministic_save(workbook: Workbook, out: Path) -> None:
    """R4 字节确定性保存：入内存→modified 载荷归一→ZipInfo 纪元重写条目。

    归一在条目循环内完成（openpyxl save 无条件刷新 modified——批 14-FIX
    机制注记见规格头 R4；未来 openpyxl 标签形态变致正则不匹配=no-op，
    由隔秒双渲染字节恒等断言兜底响红）。
    """
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    with ZipFile(buffer) as source, ZipFile(out, "w", ZIP_DEFLATED) as target:
        for name in source.namelist():
            payload = source.read(name)
            if name == "docProps/core.xml":
                payload = _MODIFIED_RE.sub(
                    rb"\g<1>" + _FIXED_MODIFIED.encode("utf-8") + rb"\g<2>",
                    payload,
                )
            entry = ZipInfo(name)  # 缺省 date_time=zip 纪元——确定性锚点
            entry.compress_type = source.getinfo(name).compress_type
            target.writestr(entry, payload)
