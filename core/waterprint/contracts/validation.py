"""校验警告码键族契约：PlantWarning 五字段+ValidationReport+kb 码规则单源（1A2）。

输入:  Severity（unit_api 冻结枚举——同层 import 合法，D3 注记先例）+
       kb constraint_key（solution 装载器 source 面）+JSON 字节（serde 面）
输出:  PlantWarning/ValidationReport（1A3 泥量/1A4 参数域后续码族同模块
       登记的契约载体）+KB_CODE_PREFIX/kb_warning_code/is_kb_code（码规则
       单源）+serialize_validation/deserialize_validation（2A1 批 serde
       增档——server calc-val artifact 数据源契约）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（1A2 校验骨架批 1a2-20261004 §3.1 预裁决；镜像测试
#   tests/contracts/test_validation.py）
#
# 【公开接口】
#   class PlantWarning(不可变)：plant 级校验警告五字段——code:str
#       （码键族——kb 派生码经 kb_warning_code 构造）/condition_key:str
#       （影响面：厂级进水面=「plant」常量段，1A3/1A4 工况域族扩展位）/
#       param_key:str（调节方向指向——进水字段 ID）/message:str（人类
#       可读消息：实际值+带域数值+条目键，禁空话禁无出处措辞）/
#       severity:Severity（复用 unit_api 枚举——前向兼容 1A3/1A4 分级；
#       不复用 UF-17 冻结 Warning：其无码位，六字段面禁改）
#   class ValidationReport(不可变)：warnings: tuple[PlantWarning, ...]+
#       codes() -> tuple[str, ...]（去重保序——首现序）+__bool__（零警告
#       =False）
#   KB_CODE_PREFIX: Final[str]（="kb."：kb 派生检查码冻结前缀）
#   kb_warning_code(key) -> str：kb 派生码构造（前缀+constraint_key 单源）
#   is_kb_code(code) -> bool：kb 派生码判别（前缀+非空键段——空键段 False）
#   serialize_validation(report) -> bytes：确定性序列化正门（R4——2A1 批
#       server val artifact 数据源；根单键 {"warnings": [五字段对象…]}）
#   deserialize_validation(data: bytes) -> ValidationReport：严格反序列化
#       正门（R4——缺键拒/未知键拒/类型与枚举域守卫；空 warnings 合法）
#   InvalidValidationError(Exception)：校验报告数据非法（JSON/结构/键集
#       /severity 越界——GR-11 族，deserialize 侧错误载体）
#
# 【行为规格】
#   R1 码规则单源：kb 派生检查码恒为 KB_CODE_PREFIX+constraint_key——
#      键↔码双向可逆（前缀剥离还原），禁在其他模块复刻码拼接。
#   R2 值对象不可变：两 dataclass 均 frozen（T3A-01 快照语义同族）。
#   R3 零警告语义：ValidationReport 布尔假=「无违规」（消费面 if 直判；
#      codes() 空元组同义——码面而非计数面承载）。
#   R4 serde（2A1 批 D1）：serialize 确定性纪律同源（sort_keys+紧凑分隔符
#      +UTF-8+ensure_ascii=False——result_schema/trust_serde 同参）且
#      warnings 数组序=报告序保序（kb 传入序=message 首例语义的载体——
#      数组序不参与 sort）；severity=枚举字符串（.value 面）。deserialize
#      严格键集（trust_serde R4 同精神：根/条目两级缺键拒+未知键拒，消息
#      含键名/路径）；四串叶类型守卫+severity 枚举域拒；空 warnings 合法
#      （空报告可序列化）。PlantWarning 无数值字段——较 trust_serde 免
#      round/非有限守卫面（无数值通路即无数值纪律面）。
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】五字段冻结面/severity 枚举复用/码规则可逆/键族存在断言
#   （input_band 恰 7 条→7 码稳定集）/codes() 去重保序/__bool__/serde
#   七面（2A1：往返无损/双跑字节同/未知键拒/缺键拒/空报告/序保序恒等/
#   严格面三拒）。
#
# 【参照】1a2-20261004 任务书 §3.1；2a1-20261005 任务书 §3 D1；
#   contracts/unit_api.py（Severity）；contracts/trust_serde.py（serde
#   先例——严格键集/确定性参数同源）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Final, final

from waterprint.contracts.unit_api import Severity

KB_CODE_PREFIX: Final[str] = "kb."


@dataclass(frozen=True)
@final
class PlantWarning:
    """plant 级校验警告（1A2 骨架五字段——厂级进水面起步，码族随批扩展）。"""

    code: str
    condition_key: str
    param_key: str
    message: str
    severity: Severity


@dataclass(frozen=True)
@final
class ValidationReport:
    """校验报告（不可变）：PlantWarning 元组——零警告 falsy（R3）。"""

    warnings: tuple[PlantWarning, ...] = ()

    def codes(self) -> tuple[str, ...]:
        """码清单（去重保序——首现序；空报告=空元组）。"""
        seen: list[str] = []
        for warning in self.warnings:
            if warning.code not in seen:
                seen.append(warning.code)
        return tuple(seen)

    def __bool__(self) -> bool:
        """零警告=False（「无违规」直判面——消费方 if report 即越带）。"""
        return bool(self.warnings)


def kb_warning_code(key: str) -> str:
    """kb 派生检查码构造：KB_CODE_PREFIX+constraint_key（码规则单源 R1）。"""
    return KB_CODE_PREFIX + key


def is_kb_code(code: str) -> bool:
    """kb 派生码判别：前缀 KB_CODE_PREFIX+非空键段（键↔码可逆判别面）。"""
    return code.startswith(KB_CODE_PREFIX) and len(code) > len(KB_CODE_PREFIX)


# ── serde 段（2A1 批 D1——server calc-val artifact 数据源契约）──

# 确定性 JSON 参数（result_schema/trust_serde 同源——R4）
_JSON_KWARGS: dict[str, Any] = {
    "sort_keys": True,
    "ensure_ascii": False,
    "separators": (",", ":"),
}
# 严格键集判据（R4——与 PlantWarning 字段一一对应）
_ROOT_KEYS: frozenset[str] = frozenset({"warnings"})
_WARNING_KEYS: frozenset[str] = frozenset(
    {"code", "condition_key", "param_key", "message", "severity"}
)


class InvalidValidationError(Exception):
    """校验报告数据非法（JSON/结构/键集/severity 越界）——GR-11 族（R4）。"""


def serialize_validation(report: ValidationReport) -> bytes:
    """确定性序列化正门（R4）：根单键对象——warnings 数组序=报告序保序
    （kb 传入序=message 首例语义的载体——数组序不参与 sort_keys）。"""
    tree: dict[str, Any] = {
        "warnings": [
            {
                "code": warning.code,
                "condition_key": warning.condition_key,
                "param_key": warning.param_key,
                "message": warning.message,
                "severity": warning.severity.value,
            }
            for warning in report.warnings
        ]
    }
    return json.dumps(tree, **_JSON_KWARGS).encode("utf-8")


def _reject_keys(raw: dict[str, Any], required: frozenset[str], path: str) -> None:
    """结构守卫：缺键拒+未知键拒（R4——消息含键名/路径）。"""
    missing = sorted(key for key in required if key not in raw)
    if missing:
        raise InvalidValidationError(
            f"校验报告结构非法：{path} 缺失必需键 {missing}"
            "（R4——serialize 恒发全键，缺失即数据源缺陷）"
        )
    unknown = sorted(set(raw) - required)
    if unknown:
        raise InvalidValidationError(
            f"校验报告结构非法：{path} 含未知键 {unknown}（合法键 {sorted(required)}）"
            "（R4——未知键拒）"
        )


def _require_str(value: Any, path: str) -> str:
    """结构守卫：字符串叶子（四串叶共用——code/condition_key/param_key/
    message；severity 独走枚举域守卫）。"""
    if not isinstance(value, str):
        raise InvalidValidationError(
            f"校验报告结构非法：{path} 应为字符串，得到 {value!r}"
        )
    return value


def _require_severity(value: Any, path: str) -> Severity:
    """结构守卫：severity 枚举域（serialize 恒发 .value 串——非串前置拒
    〔回炉 d1-N1：Severity(7) 等非串值 ValueError 收编面显式化〕+越界拒）。"""
    if not isinstance(value, str):
        raise InvalidValidationError(
            f"校验报告结构非法：{path} 应为字符串，得到 {value!r}"
        )
    try:
        return Severity(value)
    except ValueError as exc:
        raise InvalidValidationError(
            f"校验报告结构非法：{path} severity 越界：{value!r}"
            f"（合法 {[item.value for item in Severity]}）"
        ) from exc


def deserialize_validation(data: bytes) -> ValidationReport:
    """严格反序列化正门（R4）：UTF-8+JSON+根/条目两级严格键集+类型/
    枚举域守卫；空 warnings 合法（空报告=「无违规」合法态）。"""
    try:
        tree = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidValidationError(f"校验报告非法 JSON（UTF-8）：{exc}") from exc
    if not isinstance(tree, dict):
        raise InvalidValidationError(
            f"校验报告结构非法：$ 应为对象，得到 {type(tree).__name__}"
        )
    _reject_keys(tree, _ROOT_KEYS, "$")
    raw_warnings = tree["warnings"]
    if not isinstance(raw_warnings, list):
        raise InvalidValidationError(
            f"校验报告结构非法：$.warnings 应为数组，得到 {type(raw_warnings).__name__}"
        )
    warnings: list[PlantWarning] = []
    for index, item in enumerate(raw_warnings):
        path = f"$.warnings[{index}]"
        if not isinstance(item, dict):
            raise InvalidValidationError(
                f"校验报告结构非法：{path} 应为对象，得到 {type(item).__name__}"
            )
        _reject_keys(item, _WARNING_KEYS, path)
        warnings.append(
            PlantWarning(
                code=_require_str(item["code"], f"{path}.code"),
                condition_key=_require_str(item["condition_key"], f"{path}.condition_key"),
                param_key=_require_str(item["param_key"], f"{path}.param_key"),
                message=_require_str(item["message"], f"{path}.message"),
                severity=_require_severity(item["severity"], f"{path}.severity"),
            )
        )
    return ValidationReport(warnings=tuple(warnings))
