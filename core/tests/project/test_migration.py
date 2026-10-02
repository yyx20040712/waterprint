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
    # 链序=注册序（L4a 起；inlet-m3d 批 2026-10-02 增 "4.0"——进水参数面 m³/d）
    assert SUPPORTED_VERSIONS == ("1.0", "2.0", "3.0", "4.0")
    assert SUPPORTED_VERSIONS[-1] == "4.0"


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


def test_unicode_digit_version_rejected_wiring() -> None:
    """REWORK 审查 G1-01（2026-09-09）：Unicode 数字（"②" isdigit 真而
    int 炸）不得裸 ValueError 逃逸——isdecimal 前置归 None =「未知历史
    版本」拒绝族（InvalidProjectError 4xx 语义；crafted 输入鲁棒性）。"""
    with pytest.raises(InvalidProjectError, match="未知历史版本"):
        migrate({"format_version": "1.②", "design": {}, "view": {}})


def test_overlong_version_rejected_wiring() -> None:
    """REWORK 审查 G1-01 同型：超长数字段（≥3.11 int() 4300 位上限抛
    ValueError）经 try/except 收编归拒绝族——CI 矩阵 3.12/3.13 与本地
    3.14 全量 ≥3.11，int() 必炸分支确定性覆盖。"""
    with pytest.raises(InvalidProjectError, match="未知历史版本"):
        migrate({"format_version": f"1.{'9' * 5000}", "design": {}, "view": {}})


_MIGRATION_SAMPLES = (
    Path(__file__).resolve().parents[1] / "golden" / "golden_data" / "migrations"
)


def test_golden_migration_sample_v2_to_v4() -> None:
    """R4 golden 样本对（L4a 起接线）：v2 input 经链后逐键 == expected。

    样本=人类维护件（golden_data/migrations/README 纪律——实现不自编）；
    比对面=model_dump(mode="json") 与 expected JSON 逐键相等（含
    metadata.migrated_from="2.0" 与 design.site.boundary 默认补键）。
    【inlet-m3d 注记 2026-10-02】期望面=链尾到达态：v4 起当前版=4.0，
    v2 样本无 municipal_input 节点（v4 步零触碰）→ expected 版本头随批
    推进至 4.0（migrated_from 仍="2.0"——多级跳步保留最早来源）。
    【conv-golden 注记 2026-10-02】样本对更名 v2_0_to_3_0_*→v2_0_to_4_0_*
    （UF-62⑧）：expected 实为 4.0 到达态——读路径链式迁移 v2→v3→v4，
    命名随到达版；迁移面与期望值零变更（纯更名）。
    """
    source = json.loads(
        (_MIGRATION_SAMPLES / "v2_0_to_4_0_input.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (_MIGRATION_SAMPLES / "v2_0_to_4_0_expected.json").read_text(encoding="utf-8")
    )
    migrated = migrate(source)
    assert migrated.model_dump(mode="json") == expected


def test_golden_migration_sample_v3_to_v4() -> None:
    """R4 golden 样本对（inlet-m3d 批 2026-10-02 接线）：v3→v4 经链逐键==expected。

    v3→v4=进水参数面 m³/s→m³/d 换轴：municipal_input kind 节点
    q_avg_daily ×86400（round 6 定版——迁移舍入口径测试锚）；hebing 形
    单元节点（无 kind、q_avg_daily 本就 m³/d 面）零触碰=负锚；junction/
    recycle_junction 零携带（勘察冻结）样本内如实呈现。
    """
    source = json.loads(
        (_MIGRATION_SAMPLES / "v3_0_to_4_0_input.json").read_text(encoding="utf-8")
    )
    expected = json.loads(
        (_MIGRATION_SAMPLES / "v3_0_to_4_0_expected.json").read_text(encoding="utf-8")
    )
    migrated = migrate(source)
    assert migrated.model_dump(mode="json") == expected


def test_v3_to_v4_rounding_policy_anchored() -> None:
    """inlet-m3d 批迁移舍入口径定版锚：×86400 后 round(x,6)（非全精度）。

    注册表存量 v3 值 0.4023229167（=round(34760.7/86400,10) 的历史定点）
    → 34760.700003（机械迁移面）；golden 手定工程值=34760.7（人类录入
    非迁移产物——两数 3e-6 m³/d（=3 mL/d）差如实记档）。6 位定点=工程
    口径整洁面（1e-6 m³/d≈1 mL/d——千分位换算 1 m³=1000 L，1e-6 m³=
    1e-3 L=1 mL，远低于工程意义；门一回炉 k2-W2/d1-W3 勘正「≈1 L/d」
    1000× 失实句）+ io round-10 幂等前提内稳定。
    """
    migrated = migrate(
        {
            "format_version": "3.0",
            "design": {
                "nodes": {
                    "inlet": {
                        "kind": "municipal_input",
                        "q_avg_daily": 0.4023229167,
                        "kz": 1.4,
                    }
                },
                "edges": [],
            },
            "view": {},
            "metadata": {
                "format_version": "3.0",
                "content_hash": "0" * 64,
                "engine_version": "0",
                "data_version": "coefficients@0.0.0",
            },
        }
    )
    assert migrated.format_version == "4.0"
    assert migrated.design.nodes["inlet"]["q_avg_daily"] == 34760.700003


def _v3_inlet_project(q_avg_daily: float) -> dict:
    """v3 单 municipal_input inlet 项目构造（d1-W2 回炉用例共用底座）。"""
    return {
        "format_version": "3.0",
        "design": {
            "nodes": {
                "inlet": {"kind": "municipal_input", "q_avg_daily": q_avg_daily, "kz": 1.4}
            },
            "edges": [],
        },
        "view": {},
        "metadata": {
            "format_version": "3.0",
            "content_hash": "0" * 64,
            "engine_version": "0",
            "data_version": "coefficients@0.0.0",
        },
    }


def test_v3_to_v4_non_finite_inlet_rejected() -> None:
    """门一回炉 d1-W2（2026-10-02）：换算积非有限（NaN/±inf）fail-loud 拒。

    主控实证旧实现 NaN 静默穿透（round(nan,6)=nan 直写 v4 面）——乘换算
    后 isfinite 闸收编三类：原值 NaN（乘换算仍 NaN）、原值 ±inf、有限
    原值 ×86400 溢出 inf（1e308）。消息含节点 id 与原值（拒因可定位）。
    """
    for bad in (float("nan"), float("inf"), float("-inf"), 1e308):
        with pytest.raises(InvalidProjectError, match="非有限") as excinfo:
            migrate(_v3_inlet_project(bad))
        assert "inlet" in str(excinfo.value)  # 节点 id 进消息
        assert repr(bad) in str(excinfo.value)  # 原值进消息


def test_v3_to_v4_tiny_inlet_rejected() -> None:
    """门一回炉 d1-W2：正值极小被 round6 归零 → fail-loud 拒（禁 0 静默入 v4）。

    1e-13 m³/s ×86400=8.64e-09 m³/d，round 6 位后=0.0——迁移积非正值
    不可承载 v4 面（消息含原值/迁移积/「v3 值过小」）。
    """
    with pytest.raises(InvalidProjectError, match="v3 值过小") as excinfo:
        migrate(_v3_inlet_project(1e-13))
    assert repr(1e-13) in str(excinfo.value)  # 原值进消息
    assert repr(1e-13 * 86400.0) in str(excinfo.value)  # 迁移积进消息


def test_v3_to_v4_small_inlet_passes_with_round6() -> None:
    """门一回炉 d1-W2 恰小可过锚：1e-4 m³/s ×86400=8.64 m³/d（round6 存活）。

    拒收闸=round 后 ≤0.0（非「小即拒」）——8.64 m³/d 为正有效值放行
    （与 1e-13 拒收面互为边界实证）。
    """
    migrated = migrate(_v3_inlet_project(1e-4))
    assert migrated.format_version == "4.0"
    assert migrated.design.nodes["inlet"]["q_avg_daily"] == 8.64


def test_v3_to_v4_non_positive_inlet_rejected() -> None:
    """门一回炉轮 2（k2-W1 2026-10-02）：v3 值非正（0/负）拒收文案分模板。

    0/负原值=非法进水流量（0 非「小」），拒因文案「v3 值非正（0/负——
    非法进水流量）」——与正值极小被 round6 归零的「v3 值过小」面
    （test_v3_to_v4_tiny_inlet_rejected）分模板。0.0/-5.0 两锚各 match
    拒因关键词+节点 id/原值进消息。
    """
    for bad in (0.0, -5.0):
        with pytest.raises(InvalidProjectError, match="v3 值非正") as excinfo:
            migrate(_v3_inlet_project(bad))
        assert "inlet" in str(excinfo.value)  # 节点 id 进消息
        assert repr(bad) in str(excinfo.value)  # 原值进消息
        assert "非法进水流量" in str(excinfo.value)  # 0/负模板关键词


def test_skip_chain_1_0_to_4_0_wiring() -> None:
    """R1 跳级=链式复合（禁快捷迁移）：v1.0 直达 v4.0——site/boundary 补键
    +进水换轴同链达成，migrated_from 保留最早非空来源 "1.0"（R2 审计面）。

    inlet-m3d 批新增用例（§4.5）：链尾自 3.0 延至 4.0 后跳级面复锚。
    """
    migrated = migrate(
        {
            "format_version": "1.0",
            "design": {
                "nodes": {
                    "inlet": {
                        "kind": "municipal_input",
                        "q_avg_daily": 34760.7 / 86400,
                        "kz": 1.4,
                    }
                },
                "edges": [],
            },
            "view": {},
            "metadata": {
                "format_version": "1.0",
                "content_hash": "0" * 64,
                "engine_version": "0",
                "data_version": "coefficients@0.0.0",
            },
        }
    )
    assert migrated.format_version == "4.0"
    assert migrated.metadata.migrated_from == "1.0"  # 多级跳步保留最早来源
    assert migrated.design.nodes["inlet"]["q_avg_daily"] == 34760.7  # round6 恰回工程值
    assert migrated.design.site.boundary == []  # v1→v2→v3 两步补键复合到达


def test_v4_current_passes_through_without_migration() -> None:
    """v4=当前版直通（零迁移）：migrated_from 不动+q 值面零触碰——幂等键。"""
    data = {
        "format_version": "4.0",
        "design": {
            "nodes": {
                "inlet": {"kind": "municipal_input", "q_avg_daily": 34760.7, "kz": 1.4}
            },
            "edges": [],
        },
        "view": {},
        "metadata": {
            "format_version": "4.0",
            "content_hash": "0" * 64,
            "engine_version": "0",
            "data_version": "coefficients@0.0.0",
        },
    }
    migrated = migrate(data)
    assert migrated.format_version == "4.0"
    assert migrated.metadata.migrated_from is None  # 直通不写来源
    assert migrated.design.nodes["inlet"]["q_avg_daily"] == 34760.7  # 不再 ×86400
