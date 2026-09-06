"""单元包共享计算 helper：_factor/_inflow/_apply/_inflow_sludge 单源
（B8 R3 样板收敛；B10 笔①增泥线变体）。

输入:  params 投影（dict[str, float]）/UnitContext（入流+工况+迹语境）/公式绑定
输出:  系数取值 float、入流装配 (PortRef, WaterFlow)/SludgeFlow、公式求值 float
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B8 R3 样板收敛；参照 .workflow/briefs/task-B8-brief.md
# D1/D5 终裁）
#
# 【R-1 逐字迁移】三 helper 自 municipal/cass/compute.py 原文逐字迁移
#   （B8 笔①试点；计算与消息运行时输出恒等——签名允许语境参数最小
#   扩展[D5]：_factor 增 unit_id 入参、_inflow 增 edge_note 尾注入参，
#   消息文案仅消费入参；_apply 签名零扩展——ctx 自带 unit_id/
#   condition_key 语境）；泥线变体 _inflow_sludge 逐字迁移自 sludge/
#   bengzhan/compute.py（B10 笔①——AST 普查 6 泥线包 _inflow 本体
#   同构实证；edge_note 尾注入同款最小扩展）。
# 【R-2 消费面】32 包 compute.py 中实有同构面 22 包（B8 两笔 19 包+
#   B10 笔①族2 三包 municipal/chenshachi、cugeshan、xigeshan 即换；
#   余 10 包两变体族剔出——conveyance 股族 4 包/sludge 泥线族 6 包
#   （B10 笔②收口）；泥线族 6 包（sludge/bengzhan、ganhua、nongsuo、
#   shusong、tuoshui、xiaohua）经 _inflow_sludge 收口（B10 笔①扩载
#   ——笔②消费），hebing _inflow_stocks 为异语义件维持不收敛（注记
#   防后续批误判漏收敛）；_template 为纯规格说明件零样板（30 行——
#   无需消费，B8 R1 实证）；测试要求=golden 全量+双跑 diff=0 常驻测试
#   间接覆盖，零新测试（B3/ENG7/B7 纯搬迁先例三连）；共享件不
#   import 任何包件（无环——D1）；import 面=contracts（L0）+registry
#   （L1）向下合法（InvalidUnitConfig/UnitContext/PortRef/WaterFlow/
#   SludgeFlow/ConditionSet/formulas——L2→L1/L0）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import PortRef
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import UnitContext
from waterprint.registry import formulas


def _factor(params: dict[str, float], key: str, unit_id: str) -> float:
    """系数投影取值：缺键=InvalidUnitConfig（消息含键名，GR-09）。"""
    value = params.get(key)
    if value is None:
        raise InvalidUnitConfig(
            f"单元 {unit_id!r} 缺系数键 {key!r}（应经 app._unit_params 从"
            " coefficients 数据包投影合入 params——M1a D4 装配裁决同款）"
        )
    return float(value)


def _inflow(ctx: UnitContext, edge_note: str) -> tuple[PortRef, WaterFlow]:
    """入流装配：恰一入边且为 WATER（多入/缺入/泥线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], WaterFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 WATER 入边：得到 {len(refs)} 条（{edge_note}）"
        )
    flow = ctx.inflows[refs[0]]
    assert isinstance(flow, WaterFlow)  # 上行守卫已收窄，窄化供类型面
    return refs[0], flow


def _inflow_sludge(ctx: UnitContext, edge_note: str) -> SludgeFlow:
    """入流装配：恰一入边且为 SLUDGE（多入/缺入/水线=领域异常）。"""
    refs = sorted(ctx.inflows, key=lambda ref: (ref.unit_id, ref.port_id))
    if len(refs) != 1 or not isinstance(ctx.inflows[refs[0]], SludgeFlow):
        raise InvalidUnitConfig(
            f"单元 {ctx.unit_id!r} 须恰一条 SLUDGE 入边：得到 {len(refs)} 条（{edge_note}）"
        )
    flow = ctx.inflows[refs[0]]
    assert isinstance(flow, SludgeFlow)  # 上行守卫已收窄，窄化供类型面
    return flow


def _apply(ctx: UnitContext, formula_id: str, bindings: dict[str, float]) -> float:
    """apply 薄封装：统一携带 (unit_id, condition_key) 与 trace sink。"""
    return formulas.apply(
        formula_id,
        bindings,
        (ctx.unit_id, ConditionSet.key(ctx.condition)),
        sink=ctx.trace,
    )
