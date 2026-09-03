"""migration 镜像测试：版本迁移链（链式到达/未来版拒绝/不可迁移拒绝）。

输入:  waterprint.project.migration 公开符号 + golden_data/migrations 样本对
       （L4a 起 v2→v3 样本入链——R4 每迁移器配 golden 用例）
输出:  迁移链契约断言
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.project.migration")
migrate = getattr(_mod, "migrate", None)
SUPPORTED_VERSIONS = getattr(_mod, "SUPPORTED_VERSIONS", None)
_io = importlib.import_module("waterprint.project.io")
InvalidProjectError = getattr(_io, "InvalidProjectError", None)

pytestmark = pytest.mark.skipif(
    None in (migrate, SUPPORTED_VERSIONS),
    reason="实现未就绪：waterprint.project.migration（M1）",
)


def test_supported_versions_form_a_chain_from_current() -> None:
    """R1：版本序列非空且含当前版（链式结构前提）。"""
    assert SUPPORTED_VERSIONS
    assert SUPPORTED_VERSIONS == ("1.0", "2.0", "3.0")  # 链序=注册序（L4a 起）
    assert SUPPORTED_VERSIONS[-1] == "3.0"


def test_future_version_rejected_wiring() -> None:
    """R3 接线断言：format_version > 当前 → 拒绝（不降级打开）。"""
    with pytest.raises(InvalidProjectError, match="999.0"):
        migrate({"format_version": "999.0", "design": {}, "view": {},
                 "metadata": {"content_hash": "0" * 64,
                              "engine_version": "0.1.0",
                              "data_version": "coefficients@0.1.0"}})


def test_unmappable_field_rejected_wiring() -> None:
    """R2 接线断言：语义不明字段 → 领域异常指明路径（禁止猜测性默认）。"""
    # v1 产品首发无历史迁移链：含未知旧字段的样本以"未知历史版本"拒
    # 语义落（T7a D8 裁决——0.9 不在合法序列，无从映射）。
    with pytest.raises(InvalidProjectError, match="未知历史版本"):
        migrate({"format_version": "0.9", "legacy_field": "旧字段样本"})


_MIGRATION_SAMPLES = (
    Path(__file__).resolve().parents[1] / "golden" / "golden_data" / "migrations"
)


def test_golden_migration_sample_v2_to_v3() -> None:
    """R4 golden 样本对（L4a 起接线）：v2→v3 input 经链后逐键 == expected。

    样本=人类维护件（golden_data/migrations/README 纪律——实现不自编）；
    比对面=model_dump(mode="json") 与 expected JSON 逐键相等（含
    metadata.migrated_from="2.0" 与 design.site.boundary 默认补键）。
    """
    source = json.loads(
        (_MIGRATION_SAMPLES / "v2_0_to_3_0_input.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (_MIGRATION_SAMPLES / "v2_0_to_3_0_expected.json").read_text(encoding="utf-8")
    )
    migrated = migrate(source)
    assert migrated.model_dump(mode="json") == expected
