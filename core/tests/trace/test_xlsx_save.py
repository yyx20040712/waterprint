"""xlsx_save 共享件镜像测试：est-20261001（确定性保存机制单源抽取件）。

输入:  waterprint.trace.xlsx_save（deterministic_save/fixed_created）
输出:  机制契约断言（modified 归一定值+zip 条目纪元+双保存字节恒等）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（est-20261001 D2——_deterministic_save 自 calcbook.py 抽出
#   的机制单源件；本件=tests/arch/test_structure.py 镜像规则强制件
#   〔test_<stem>.py 命名铁律〕。机制的行为面由两消费件镜像锁隔秒
#   双渲染字节恒等〔test_calcbook.py+test_estimate_sheet.py 两处在锁
#   ——D2 预裁决原文〕；本件直锁机制本体三断言。）
#
# 【覆盖面】
#   - modified 归一：docProps/core.xml dcterms:modified==固定纪元定值
#     （批 14-FIX——openpyxl save 无条件刷新面收口）；
#   - zip 条目纪元：全部条目 date_time==ZipInfo 缺省纪元（时钟不入条目）；
#   - 双保存字节恒等：同工作簿两次保存字节相同（确定性锚点）；
#   - fixed_created：固定纪元 datetime（新工作簿 created 锚源）。
# 【替身口径】零替身（openpyxl 真链路）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

_mod = importlib.import_module("waterprint.trace.xlsx_save")

_FIXED_MODIFIED = b"2000-01-01T00:00:00Z"
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)  # ZipInfo 缺省 date_time（zip 纪元）


def _tiny_workbook_path_pair(tmp_path: Path) -> tuple[Path, Path]:
    """最小工作簿双保存（同内容两路径——确定性对照载体）。"""
    from openpyxl import Workbook

    first = tmp_path / "a.xlsx"
    second = tmp_path / "b.xlsx"
    for out in (first, second):
        workbook = Workbook()
        workbook.properties.created = _mod.fixed_created()
        workbook.active.append(("机制锚", 1.0))
        _mod.deterministic_save(workbook, out)
    return first, second


def test_deterministic_save_normalises_clock_and_entry_epochs(
    tmp_path: Path,
) -> None:
    """机制契约：modified==定值+全部 zip 条目 date_time==纪元+字节恒等。"""
    first, second = _tiny_workbook_path_pair(tmp_path)
    assert first.read_bytes() == second.read_bytes()  # 双保存字节恒等
    with zipfile.ZipFile(first) as archive:
        core_xml = archive.read("docProps/core.xml")
        for info in archive.infolist():
            assert info.date_time == _ZIP_EPOCH  # 时钟不入条目（纪元锚）
    modified = re.search(rb"<dcterms:modified[^>]*>([^<]*)</dcterms:modified>", core_xml)
    assert modified is not None and modified.group(1) == _FIXED_MODIFIED


def test_fixed_created_is_frozen_epoch() -> None:
    """fixed_created：固定纪元 datetime（UTC 带时区——W3CDTF Z 尾等价形）。"""
    assert _mod.fixed_created() == datetime(2000, 1, 1, tzinfo=UTC)
