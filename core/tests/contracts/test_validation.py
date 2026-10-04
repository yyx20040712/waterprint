"""contracts/validation 镜像测试：警告码键族契约+PlantWarning/ValidationReport 结构。

输入:  waterprint.contracts.validation（KB_CODE_PREFIX/kb_warning_code/
       is_kb_code/PlantWarning/ValidationReport）+kb 真源（仓库 data 面）
输出:  契约断言——码规则单源（前缀+键可逆还原+空键段拒）+键族存在断言
       （kb 装载 151 条总数锚+input_band 恰 7 条→7 码稳定集+mass_balance
       恰 1 条→1 码稳定集+param_band 恰 109 条→109 码稳定集，单源=kb
       数据禁手写码字面量表）
       +PlantWarning 五字段冻结面（severity 复用 unit_api 枚举——不复用
       UF-17 冻结 Warning）+ValidationReport codes() 去重保序/__bool__ 语义
"""

# ══════════════════════════════════════════════════════════════════
# 规格：1A2 校验骨架批（1a2-20261004）§3.1 预裁决——码键族落 contracts
#   新模块；后续批（1A3 泥量/1A4 参数域）在同模块登记各自族。键族存在
#   断言锚=route-design-final §2.1 L46（warning_codes 键族存在）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from waterprint.contracts.unit_api import Severity
from waterprint.contracts.validation import (
    KB_CODE_PREFIX,
    PlantWarning,
    ValidationReport,
    is_kb_code,
    kb_warning_code,
)
from waterprint.solution.constraints import load_kb_constraints

_REPO_ROOT = Path(__file__).resolve().parents[3]
_KB_FILE = _REPO_ROOT / "data" / "constraint_kb" / "constraints.json"
_INPUT_BAND_KIND = "input_band"  # 断言主语（kb 数据面字面量）
_FAMILY_COUNT = 7  # 基线数字（任务书 §5：input_band 7 条全 WARN 起草态）
_TOTAL_COUNT = 151  # 总数锚（k1-N1：kb 2.0.0 全量 151 条——1A3 批 42+1A4 批
# param_band 109；计数漂移即红）
_MASS_BALANCE_KIND = "mass_balance"  # 1A3 批新 kind（kb 数据面字面量）
_MASS_BALANCE_FAMILY_COUNT = 1  # 1A3 批增条计数（mass_balance 恰 1）
_PARAM_BAND_KIND = "param_band"  # 1A4 批新 kind（kb 数据面字面量）
_PARAM_BAND_FAMILY_COUNT = 109  # 1A4 批增条计数（28 单元 _PARAMS_POSITIVE
# 机扫聚合——逐字段一条；实扫单源=.workflow/1a4-20261004/scan_params_positive.py）


def _warn(code: str) -> PlantWarning:
    """最小 PlantWarning 桩（五字段齐——severity 复用 unit_api 枚举）。"""
    return PlantWarning(
        code=code,
        condition_key="plant",
        param_key="kz",
        message="桩消息",
        severity=Severity.WARN,
    )


def test_plant_warning_five_frozen_fields() -> None:
    """PlantWarning 五字段冻结面：字段集恰五（code/condition_key/param_key/
    message/severity）；frozen dataclass 赋值拒。"""
    warning = _warn("kb.inlet.kz_band")
    assert {f.name for f in dataclasses.fields(warning)} == {
        "code", "condition_key", "param_key", "message", "severity"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        warning.code = "kb.other"  # type: ignore[misc]


def test_plant_warning_reuses_unit_api_severity() -> None:
    """severity 复用 contracts.unit_api Severity 枚举（1A3/1A4 分级前向
    兼容面——不复用 UF-17 冻结 Warning：其无码位）。"""
    assert _warn("kb.x").severity is Severity.WARN
    error_level = PlantWarning(
        code="kb.x", condition_key="plant", param_key="kz",
        message="桩消息", severity=Severity.ERROR,
    )
    assert error_level.severity is Severity.ERROR  # 三级枚举值随行承载


def test_kb_code_rule_single_source_roundtrip() -> None:
    """码规则单源：KB_CODE_PREFIX 冻结前缀+kb_warning_code 构造+
    is_kb_code 判别+前缀剥离可逆还原（键↔码双向单源）。"""
    assert KB_CODE_PREFIX == "kb."
    assert kb_warning_code("inlet.kz_band") == KB_CODE_PREFIX + "inlet.kz_band"
    assert is_kb_code(kb_warning_code("inlet.kz_band"))
    assert not is_kb_code(KB_CODE_PREFIX)  # 空键段拒（d1-N2："kb." 非码——键↔码可逆）
    assert not is_kb_code("maint.x.kb.any_fail")  # 码位在尾非前缀——非 kb 派生码
    code = kb_warning_code("inlet.quality_upper.cod")
    assert code[len(KB_CODE_PREFIX):] == "inlet.quality_upper.cod"  # 剥离可逆


def test_validation_report_codes_dedupe_preserve_order() -> None:
    """ValidationReport：codes() 去重保序（首现序）；__bool__ 零警告=False；
    warnings 元组冻结（frozen dataclass）。"""
    report = ValidationReport(warnings=(
        _warn("kb.a"), _warn("kb.b"), _warn("kb.a")))
    assert report.codes() == ("kb.a", "kb.b")
    assert bool(report)  # 非零警告 truthy
    empty = ValidationReport(warnings=())
    assert not empty  # 零警告 falsy（§3.1 预裁决语义）
    assert empty.codes() == ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.warnings = ()  # type: ignore[misc]


def test_kb_input_band_family_exists_seven_codes() -> None:
    """键族存在断言：装载 kb 中 kind=input_band 恰 7 条→7 码稳定集。

    单源=kb 数据（码经 kb_warning_code 派生，禁手写码字面量表制造双源
    ——route-design-final §2.1 L46 警告码键族锚）。
    """
    loaded = load_kb_constraints(_KB_FILE)
    assert len(loaded) == _TOTAL_COUNT  # 总数锚（42——装载面全集漂移即红）
    family = tuple(kb for kb in loaded if kb.kind == _INPUT_BAND_KIND)
    assert len(family) == _FAMILY_COUNT  # 恰 7 条（基线数字——数据面冻结）
    codes = tuple(sorted(kb_warning_code(kb.constraint.key) for kb in family))
    assert len(set(codes)) == _FAMILY_COUNT  # 键唯一→码唯一（7 码稳定集）
    assert all(is_kb_code(code) for code in codes)
    assert all(
        code[len(KB_CODE_PREFIX):] == kb.constraint.key
        for code, kb in zip(
            codes,
            sorted(family, key=lambda kb: kb.constraint.key),
            strict=True,
        )
    )  # 码=前缀+键 单源还原（kb 数据面单源）


def test_kb_mass_balance_family_exists_one_code() -> None:
    """键族存在断言（1A3 批）：kind=mass_balance 恰 1 条→1 码稳定集。

    单源=kb 数据（kb_warning_code 派生——input_band 七码集同款形态；
    1A3 泥量互校族锚=route-design-final §2.1 L47 警告码触发验收）。
    """
    loaded = load_kb_constraints(_KB_FILE)
    assert len(loaded) == _TOTAL_COUNT  # 总数锚（42——两族断言共用装载）
    family = tuple(kb for kb in loaded if kb.kind == _MASS_BALANCE_KIND)
    assert len(family) == _MASS_BALANCE_FAMILY_COUNT  # 恰 1 条（1A3 增条）
    codes = tuple(kb_warning_code(kb.constraint.key) for kb in family)
    assert codes == ("kb.sludge.primary_load_band",)  # 1 码稳定集（单源派生）
    assert all(is_kb_code(code) for code in codes)
    assert all(
        code[len(KB_CODE_PREFIX):] == kb.constraint.key
        for code, kb in zip(codes, family, strict=True)
    )  # 码=前缀+键 单源还原（键↔码双向可逆）


def test_kb_param_band_family_exists_109_codes() -> None:
    """键族存在断言（1A4 批）：kind=param_band 恰 109 条→109 码稳定集。

    单源=kb 数据（kb_warning_code 派生——input_band 七码集/mass_balance
    单码集同款形态；1A4 单元参数正性域族锚=route-design-final §2.1 行
    1A4「域外注入断言拒绝/降级警告」）。键面=`param.<field>.positive`
    逐字段一条（28 单元 _PARAMS_POSITIVE 机扫聚合单源——计数=109 与
    扫描脚本实扫/主控预扫三方一致）。
    """
    loaded = load_kb_constraints(_KB_FILE)
    assert len(loaded) == _TOTAL_COUNT  # 总数锚（151——三族断言共用装载）
    family = tuple(kb for kb in loaded if kb.kind == _PARAM_BAND_KIND)
    assert len(family) == _PARAM_BAND_FAMILY_COUNT  # 恰 109 条（1A4 增条）
    keys = tuple(kb.constraint.key for kb in family)
    assert all(
        key.startswith("param.") and key.endswith(".positive") for key in keys
    )  # 键面契约：param.<field>.positive（逐字段一条）
    assert len(set(keys)) == len(keys)  # 键唯一→码唯一（109 码稳定集）
    codes = tuple(sorted(kb_warning_code(kb.constraint.key) for kb in family))
    assert len(codes) == _PARAM_BAND_FAMILY_COUNT
    assert all(is_kb_code(code) for code in codes)
    sorted_family = sorted(family, key=lambda kb: kb.constraint.key)
    assert all(
        code[len(KB_CODE_PREFIX):] == kb.constraint.key
        for code, kb in zip(codes, sorted_family, strict=True)
    )  # 码=前缀+键 单源还原（键↔码双向可逆）
