"""水量契约与构造校验（消除 Q_design/Q_avg 双轨的病灶根除点）。

输入:  带单位的日平均流量、总变化系数 Kz（来自边界层，规范单位由 quantity 保证）
输出:  WaterFlow（规范单位：Q_avg_daily 与派生 Q_design，m3/s）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_flow.py）
#
# 【公开接口】
#   class WaterFlow(不可变)：
#       q_avg_daily: float        平均日流量，规范单位 m3/s（唯一输入源）
#       kz: float                 总变化系数（最高日最高时 / 平均日平均时）
#       q_design: float           派生属性 = q_avg_daily * kz，禁止独立赋值
#   make_flow(q_avg_daily: Quantity, kz: float) -> WaterFlow
#       唯一构造正门（经 quantity.parse 完成单位换算与量纲校验）
#
# 【行为规格】
#   R1 q_design 是派生量：属性而非输入字段——同对象上双轨不可能存在（病灶
#      "Q_design/Q_avg 双轨"的架构级根除，§3 保证 2）。
#   R2 构造校验：q_avg_daily > 0、kz >= 1；违反抛 InvalidFlowError（领域异常）。
#   R3 Kz 的行业上下限校验属于 constraint_kb 数据（约束），不属于本契约；
#      契约只守数学不变量。
#   R4 m3/d 等外部单位输入必须在 make_flow 内经 quantity.parse 换算，
#      WaterFlow 内部永远是规范单位 m3/s 裸值。
#   R5 工况关联：flow_case=design 用 q_design、avg 用 q_avg_daily
#      （ADR-007；分支发生在图引擎/单元映射，不在本契约）。
#
# 【T2 预裁决注记】（总控 2026-08-23）
#   P5 数值校验先 isfinite 再域校验（`if v < 0` 会放过 NaN——GR-02 复发
#      路径）：kz 为裸 float，make_flow 内先 isfinite 再 kz >= 1；
#      q_avg_daily 的有限性由 quantity.parse 的 GR-02 守卫承担
#      （InvalidQuantityError，P5 同族防线）。
#   P11 异常消息冻结（发布后不改文本，GR-09）：必含参数键 + 实际值
#      （+期望域），冻结口径：
#      "q_avg_daily 必须大于 0（厂界口径 flow.py R2/UF-03）：得到 0.0"、
#      "kz 必须 >= 1：得到 nan（非有限值拒绝，GR-02）"。
#   数值纪律：本文件不在魔法数字白名单——数值字面量仅 0/1；换算一律
#      经 quantity.parse，本文件零换算系数。
#
# 【测试要求】双轨消除断言（q_design 派生只读）、非法构造拒绝、
#   34760 m3/d == 34760/86400 m3/s 换算、kz=1 合法。
#
# 【参照】重写计划 §3-2/§14.1；ADR-002/ADR-007；简报 T2 预裁决 P5/P11
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import final

from waterprint.contracts.quantity import DimKey, Quantity, parse


class InvalidFlowError(Exception):
    """水量构造非法（q_avg_daily 域 / kz 域 / 非有限值）——领域异常（GR-11 族）。"""


@dataclass(frozen=True)
@final
class WaterFlow:
    """平均日流量 + 总变化系数的不可变值对象（q_design 只读派生，R1）。"""

    q_avg_daily: float
    kz: float

    @property
    def q_design(self) -> float:
        """设计流量 = q_avg_daily × kz（派生量：同对象上双轨不可能存在）。"""
        return self.q_avg_daily * self.kz


def make_flow(q_avg_daily: Quantity, kz: float) -> WaterFlow:
    """唯一构造正门：parse 换算到规范单位 m3/s + 数学域校验（R2/R4/P5）。"""
    if not isfinite(kz):
        raise InvalidFlowError(f"kz 必须 >= 1：得到 {kz!r}（非有限值拒绝，GR-02）")
    q_avg = parse(q_avg_daily.magnitude, q_avg_daily.unit, DimKey.FLOW)
    if q_avg <= 0:
        raise InvalidFlowError(
            f"q_avg_daily 必须大于 0（厂界口径 flow.py R2/UF-03）：得到 {q_avg!r}"
        )
    if kz < 1:
        raise InvalidFlowError(f"kz 必须 >= 1：得到 {kz!r}")
    return WaterFlow(q_avg_daily=q_avg, kz=kz)
