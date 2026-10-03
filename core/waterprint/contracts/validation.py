"""校验警告码键族契约：PlantWarning 五字段+ValidationReport+kb 码规则单源（1A2）。

输入:  Severity（unit_api 冻结枚举——同层 import 合法，D3 注记先例）+
       kb constraint_key（solution 装载器 source 面）
输出:  PlantWarning/ValidationReport（1A3 泥量/1A4 参数域后续码族同模块
       登记的契约载体）+KB_CODE_PREFIX/kb_warning_code/is_kb_code（码规则单源）
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
#   is_kb_code(code) -> bool：kb 派生码判别（前缀判定）
#
# 【行为规格】
#   R1 码规则单源：kb 派生检查码恒为 KB_CODE_PREFIX+constraint_key——
#      键↔码双向可逆（前缀剥离还原），禁在其他模块复刻码拼接。
#   R2 值对象不可变：两 dataclass 均 frozen（T3A-01 快照语义同族）。
#   R3 零警告语义：ValidationReport 布尔假=「无违规」（消费面 if 直判；
#      codes() 空元组同义——码面而非计数面承载）。
#
# 【数值纪律】本文件不在魔法数字白名单——零数值字面量。
#
# 【测试要求】五字段冻结面/severity 枚举复用/码规则可逆/键族存在断言
#   （input_band 恰 7 条→7 码稳定集）/codes() 去重保序/__bool__。
#
# 【参照】1a2-20261004 任务书 §3.1；contracts/unit_api.py（Severity）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final

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
    """kb 派生码判别：前缀 KB_CODE_PREFIX（键↔码可逆性的判别面）。"""
    return code.startswith(KB_CODE_PREFIX)
