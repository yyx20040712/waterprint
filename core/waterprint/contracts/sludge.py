"""污泥量契约（SLUDGE 独立通道；DS 干固体守恒的载体）。

输入:  湿泥量、干固体量 DS、含水率（边界带单位，换算到规范单位）
输出:  SludgeFlow（不可变）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/contracts/test_sludge.py +
# 性质测试 properties_sludge.py）
#
# 【公开接口】
#   class SludgeFlow(不可变)：
#       q_wet: float        湿泥体积流量，规范单位 m3/s
#       ds: float           干固体质量流量，规范单位 kg/s
#       moisture: float     含水率，小数（0 <= moisture < 1）
#   make_sludge(q_wet: float, ds: float, moisture: float) -> SludgeFlow
#       构造正门（单位换算+校验集中于此）
#   mix(flows: Sequence[SludgeFlow]) -> SludgeFlow
#       污泥汇流：q_wet、ds 各自求和；含水率由总量反解（非简单平均）
#       （T2 预裁决 P3：签名冻结为单参——规格头原草案 "weights" 参数删除，
#        两处锁定测试均单参、加权语义无规格；规格修正随本任务显式 commit）
#
# 【行为规格】
#   R1 守恒不变量（性质测试常驻）：任何混合/分流前后 Σds 不变
#      （§14.2"DS 守恒断言进性质测试——含水率变化不守恒即失败"）。
#   R2 含水率与 (ds, q_wet) 的相互换算依赖污泥密度假设，该假设只存在于
#      registry/assumptions.py（默认值带出处），本契约不内嵌密度常数。
#   R3 校验：q_wet >= 0、ds >= 0、0 <= moisture < 1；违反抛领域异常。
#   R4 污泥链含水率沿程变化 = 各单元改写 moisture 后产生新 SludgeFlow
#      （不可变值对象，禁止原地修改）。
#
# 【T2 预裁决注记】（总控 2026-08-23）
#   P2 异常类自立 InvalidSludgeError（GR-11 Invalid* 族）。
#   P4 含水率反解公式冻结（干基质量恒等，不内嵌密度常数——R2）：
#      water_i = ds_i·m_i/(1−m_i)，
#      merged.moisture = Σwater/(Σwater+Σds)；
#      边界：空序列或 Σwater+Σds==0（全零股）→ 返回零污泥单位元
#      SludgeFlow(0.0, 0.0, 0.0)（GR-14 单位元选项）。
#   P5 所有数值校验先 isfinite 再域校验（NaN 逃过 `if v < 0`——
#      GR-02 复发路径；±Inf 同拒）。
#   P7 make_sludge 收裸 float（规范单位 m3/s、kg/s、小数含水率）；
#      不造复合单位 DimKey、不扩 quantity 白名单（q_wet/ds 的
#      Quantity 化留给未来规格）。
#   P8 禁做三字段三角一致校验：镜像测试数据本身物理不自洽
#      （q=0.01, ds=2.0, m=0.98），三字段独立校验各自域即可——
#      加三角校验测试必红。
#   P11 异常消息冻结（发布后不改文本，GR-09）：必含参数键 + 实际值
#      （+期望域）。
#   数值纪律：本文件不在魔法数字白名单——数值字面量仅 0/1。
#
# 【测试要求】混合守恒、含水率反解、非法构造拒绝；
#   性质：随机两组混合 Σds 前后相等（hypothesis）。
#
# 【参照】重写计划 §14.2；ADR 语义：SLUDGE 端口类型独立于 WATER（ports.py）；
#   简报 T2 预裁决 P2/P3/P4/P5/P7/P8/P11
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import final


class InvalidSludgeError(Exception):
    """污泥构造非法（q_wet/ds/moisture 域、非有限值）——领域异常（P2，GR-11 族）。"""


@dataclass(frozen=True)
@final
class SludgeFlow:
    """湿泥量 + 干固体量 + 含水率的不可变值对象（R4：改写即新对象）。"""

    q_wet: float
    ds: float
    moisture: float


def make_sludge(q_wet: float, ds: float, moisture: float) -> SludgeFlow:
    """构造正门（P7 裸 float：m3/s、kg/s、小数含水率）；域校验集中于此。"""
    if not isfinite(q_wet):
        raise InvalidSludgeError(f"q_wet 非有限值拒绝（GR-02）：得到 {q_wet!r}")
    if q_wet < 0:
        raise InvalidSludgeError(f"q_wet 必须 >= 0（m3/s）：得到 {q_wet!r}")
    if not isfinite(ds):
        raise InvalidSludgeError(f"ds 非有限值拒绝（GR-02）：得到 {ds!r}")
    if ds < 0:
        raise InvalidSludgeError(f"ds 必须 >= 0（kg/s）：得到 {ds!r}")
    if not isfinite(moisture):
        raise InvalidSludgeError(
            f"moisture 非有限值拒绝（GR-02）：得到 {moisture!r}"
        )
    if not 0 <= moisture < 1:
        raise InvalidSludgeError(
            f"moisture 必须在 [0,1)（小数含水率）：得到 {moisture!r}"
        )
    return SludgeFlow(q_wet=q_wet, ds=ds, moisture=moisture)


def mix(flows: Sequence[SludgeFlow]) -> SludgeFlow:
    """污泥汇流（P3 单参签名）：q_wet/ds 各自求和，含水率按干基质量恒等反解（P4）。

    单位元条款：空序列或 Σwater+Σds==0（全零股）→ 零污泥 SludgeFlow(0,0,0)。
    """
    water_total = 0.0
    ds_total = 0.0
    q_wet_total = 0.0
    for one in flows:
        water_total += one.ds * one.moisture / (1 - one.moisture)
        ds_total += one.ds
        q_wet_total += one.q_wet
    total = water_total + ds_total
    if total == 0:
        return SludgeFlow(q_wet=0.0, ds=0.0, moisture=0.0)
    return make_sludge(q_wet_total, ds_total, water_total / total)
