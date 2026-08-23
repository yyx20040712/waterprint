"""水质契约 + 出水标准库（标准是数据不是分支，一级A/III类各一条数据）。

输入:  6 项常规指标值（规范单位 mg/L）+ 标准名（如 "GB18918-2002-1A"）
输出:  WaterQuality、EffluentStandard、达标裕度 margin
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_quality.py）
#
# 【公开接口】
#   INDICATORS: 常规六指标字段 ID（冻结）：BOD5 / CODCR / SS / NH3N / TN / TP
#   class WaterQuality(不可变)：按字段 ID 存浓度（mg/L 裸值），
#       支持缺项（None）——缺项在传播中按"不参与混合"处理并记录警告
#   class EffluentStandard(不可变)：standard_id、名称、限值 dict[字段ID→float]
#   STANDARDS: 出水标准库（数据驱动加载自 data/coefficients，构造时注入）
#       ——装载机制见 UF-39，挂起（P1）：T2 只交付类型 + margin + WaterQuality，
#       禁止内联任何标准限值数值（魔法数字门禁 + golden"不内联限值"）
#   margin(value: float, standard: EffluentStandard, indicator: str) -> float
#       裕度 = (限值 − 计算值) / 限值；>=0 达标，负值即超限幅度
#
# 【行为规格】
#   R1 双水线标准差异 = 库里两条数据（市政一级A / 矿井水 III类），
#      代码中禁止出现 if 标准名 的分支（§14.2，病灶"标准硬编码分支"）。
#   R2 浓度非负；负值构造抛 InvalidQualityError。
#   R3 标准库加载失败/标准 ID 未知 → 领域异常，禁止回退默认标准。
#   R4 指标集合开放：六指标为最小冻结集，新增指标走 dimensions 注册表 +
#      标准库数据同步，不改本契约代码。
#
# 【T2 预裁决注记】（总控 2026-08-23）
#   P1 STANDARDS 挂起（UF-39）：装载者/注入形态/与 GR-36"L0 禁 I/O"的
#      调和待数据工作包或 T4 定义；本文件零标准数值、零 I/O。
#   P6 WaterQuality 形态：构造收 dict[字段ID→float]（键 ⊆ INDICATORS，
#      未知键 → InvalidQualityError，消息注明扩展路径走 dimensions 注册）；
#      按字段 ID 属性访问（缺项返回 None 非 0）；未知属性正常 AttributeError。
#      内部快照为 MappingProxyType（真不可变）；标准条目的限值域守卫
#      集中在 margin（值与限值 isfinite、限值 > 0——P5 先有限后域）。
#   P10 INDICATORS 冻结为 frozenset({"BOD5","CODCR","SS","NH3N","TN","TP"})
#      （大写形态，CODCR 非 CODCr）。
#   P11 异常消息冻结（发布后不改文本，GR-09）：必含参数键 + 实际值
#      （+期望域）。
#   数值纪律：本文件不在魔法数字白名单——数值字面量仅 0/1；margin
#      公式无字面量。
#
# 【测试要求】裕度符号语义、数据驱动（同库不同标准结果不同而代码路径相同）、
#   负浓度拒绝、缺项语义。
#
# 【参照】重写计划 §3-4/§14.2；数据包 data/coefficients/README.md；
#   简报 T2 预裁决 P1/P6/P10/P11；UF-39
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Final, final


class InvalidQualityError(Exception):
    """水质构造/求值非法（未知指标、负浓度、非有限值、限值域）——领域异常（GR-11 族）。"""


INDICATORS: Final[frozenset[str]] = frozenset(
    {"BOD5", "CODCR", "SS", "NH3N", "TN", "TP"}
)


@dataclass(frozen=True)
@final
class WaterQuality:
    """按字段 ID 存六指标浓度（mg/L 裸值）的不可变值对象；缺项为 None（P6）。"""

    concentrations: Mapping[str, float]

    def __post_init__(self) -> None:
        """构造校验（P5 先有限后域）+ 只读快照冻结（R2/P6）。"""
        unknown = set(self.concentrations) - INDICATORS
        if unknown:
            raise InvalidQualityError(
                f"未知指标键 {sorted(unknown)!r}：合法键 ⊆ {sorted(INDICATORS)}"
                "（指标扩展走 dimensions 注册表，R4）"
            )
        for key, value in self.concentrations.items():
            if not isfinite(value):
                raise InvalidQualityError(
                    f"{key} 浓度非有限值拒绝（GR-02）：得到 {value!r}"
                )
            if value < 0:
                raise InvalidQualityError(
                    f"{key} 浓度必须 >= 0（mg/L）：得到 {value!r}"
                )
        object.__setattr__(
            self, "concentrations", MappingProxyType(dict(self.concentrations))
        )

    def __getattr__(self, name: str) -> float | None:
        """字段 ID 属性访问：缺项 None 非 0；未知属性 AttributeError（P6）。"""
        if name not in INDICATORS:
            raise AttributeError(
                f"WaterQuality 无字段 {name!r}（合法字段 ID：{sorted(INDICATORS)}）"
            )
        return self.concentrations.get(name)


@dataclass(frozen=True)
@final
class EffluentStandard:
    """出水标准（一条数据，非代码分支，R1）：ID + 名称 + 指标限值表。"""

    standard_id: str
    name_i18n: str
    limits: Mapping[str, float]

    def __post_init__(self) -> None:
        """只读快照冻结（标准是数据：限值域守卫集中在 margin，R3/P5）。"""
        object.__setattr__(self, "limits", MappingProxyType(dict(self.limits)))


def margin(value: float, standard: EffluentStandard, indicator: str) -> float:
    """达标裕度 = (限值 − 值)/限值；>=0 达标，负值即超限幅度（值/限值守卫集中于此）。"""
    if not isfinite(value):
        raise InvalidQualityError(
            f"margin 的 value 非有限值拒绝（GR-02）：得到 {value!r}"
        )
    if indicator not in INDICATORS:
        raise InvalidQualityError(
            f"未知指标 {indicator!r}：合法指标 ⊆ {sorted(INDICATORS)}"
            "（指标扩展走 dimensions 注册表，R4）"
        )
    if indicator not in standard.limits:
        raise InvalidQualityError(
            f"标准 {standard.standard_id!r} 未覆盖指标 {indicator}"
            "（标准条目来自数据包，禁止回退默认标准，R3）"
        )
    limit = standard.limits[indicator]
    if not isfinite(limit) or limit <= 0:
        raise InvalidQualityError(
            f"标准 {standard.standard_id!r} 的 {indicator} 限值必须为有限且 > 0"
            f"（mg/L）：得到 {limit!r}"
        )
    return (limit - value) / limit
