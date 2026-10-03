"""结果可信度诊断契约（数据面：收敛/水量闭合/裕度——独立并列 artifact）。

输入:  executor 回路统计（DiagSink 协议采集）+ app 层纯投影（质量平衡/
       出水裕度——ADR-012 D5/D6）
输出:  LoopRunStats / ClosureLine / UnitImbalance / FlowClosure /
       IndicatorMargin / DiagnosticsReport + serialize_diag /
       deserialize_diag（serde 内核=trust_serde.py 承载，本件同名再
       导出——消费方 import 面零变化；序列化纪律 R2/R3/R4 见该件）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（P2 次批冻结 2026-09-12；ADR-012；镜像测试 tests/contracts/
# test_trust.py；kbflag 批 2026-10-03 serde 拆件——R2/R3/R4 规格随内核
# 迁 trust_serde.py，本件保留数据面条款 R1/R5/R6）
#
# 【公开接口】
#   class InvalidDiagnosticsError(Exception)
#       诊断数据非法（结构/非有限值/JSON 非法）——GR-11 Invalid* 族
#   class DiagSink(Protocol)：record_loop(condition_key, loop_nodes,
#       iterations, final_residual)——executor 回路统计采集协议
#       （trace_sink 同构注入面；app 层 DiagCollector 实现）
#   class LoopRunStats(不可变)：condition_key、loop_nodes:
#       tuple[str,...]、iterations: int（>=1）、final_residual: float
#       （>=0 由复算公式 abs 保证，构造面不重复守卫 R6 分层；_step 同式）
#   class ClosureLine(不可变)：fluid（"WATER"/"SLUDGE"）、
#       q_sources_total / q_sinks_total / closure_rel: float
#       ——单流体线厂级闭合（源=无入边单元Σ出流，汇=无出边单元Σ出流）
#   class UnitImbalance(不可变)：unit_id、fluid、q_in / q_out /
#       delta_rel: float——单元×流体进出闭合（有入边单元；
#       泥线减量单元残差=工艺性事实，判读注记非错误）
#   class FlowClosure(不可变)：condition_key、lines:
#       tuple[ClosureLine,...]、unit_imbalances: tuple[UnitImbalance,...]
#   class IndicatorMargin(不可变)：condition_key、standard_id、
#       indicator、value、limit、margin 全 float——裕度=(限值−值)/
#       限值（quality.margin 语义，>=0 达标）
#   class DiagnosticsReport(不可变)：convergence: tuple[LoopRunStats,...]、
#       loop_params: Mapping[str→float]（loop.* 终值口径）、
#       mass_balance: tuple[FlowClosure,...]、effluent:
#       tuple[IndicatorMargin,...]、repro: ReproTriple
#   serialize_diag(report) -> bytes     确定性序列化正门（trust_serde
#       定义，本件同名再导出）
#   deserialize_diag(data: bytes) -> DiagnosticsReport  严格反序列化
#       正门（trust_serde 定义，本件同名再导出）
#
# 【行为规格】（本件=数据面条款；序列化面 R2/R3/R4 归 trust_serde.py）
#   R1 独立并列 artifact（ADR-012 D1）：诊断走 calc-diag-{task_id}.json，
#      PlantResult 总线零触碰——旧结果缺 diag 文件=消费方降级呈现
#      （diagnostics_available=False），禁止静默伪造空诊断冒充。
#   R5 诊断绑定 repro 三元组：与 calc-{task_id}.json 同源产出
#      （同 worker 同 bundle），消费方按 task_id 命名绑定对账。
#   R6 构造轻守卫仅冻结归一（tuple/MappingProxyType）+iterations 域
#      （int>=1，solve_loop 首步即迭代）；数值有限性集中序列化守卫。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 iterations 域
#   下限 1（solve_loop 首步即迭代口径）。
#
# 【测试要求】往返无损、确定性（双跑字节同）、未知/缺失键拒、
#   非有限值拒、iterations 域守卫、空容器恒发（空 tuple 合法序列化
#   为 []——无回路图 convergence 空合法）。
#
# 【参照】ADR-012；contracts/trust_serde.py（serde 内核拆件承载面）；
#   result_schema.py（确定性纪律母本）；quality.py（margin 语义）；
#   conventions §11 GR-02/GR-11
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol, final

from waterprint.contracts.result_schema import ReproTriple

# 再导出面（kbflag 批 2026-10-03 serde 拆件）：serialize_diag /
# deserialize_diag 定义已拆至 trust_serde.py，此处经 __all__ 显式再
# 导出（mypy no-implicit-reexport 认可形态——manifest.py 先例）——
# 消费方 import 面零变化；装载序契约见文件尾段再导出 import 注记。
__all__ = [
    "ClosureLine",
    "DiagSink",
    "DiagnosticsReport",
    "FlowClosure",
    "IndicatorMargin",
    "InvalidDiagnosticsError",
    "LoopRunStats",
    "UnitImbalance",
    "deserialize_diag",
    "serialize_diag",
]

class InvalidDiagnosticsError(Exception):
    """诊断数据非法（结构/非有限值/JSON 非法）——领域异常（GR-11 族）。"""


class DiagSink(Protocol):
    """回路统计采集协议（executor → app 注入面，trace_sink 同构）。"""

    def record_loop(
        self, condition_key: str, loop_nodes: tuple[str, ...],
        iterations: int, final_residual: float,
    ) -> None:
        """一次成功收敛的回路求解统计（发散路径抛异常不进此面）。"""
        ...


@dataclass(frozen=True)
@final
class LoopRunStats:
    """单回路组收敛统计（iterations>=1；final_residual=末步全变量相对残差）。"""

    condition_key: str
    loop_nodes: tuple[str, ...]
    iterations: int
    final_residual: float

    def __post_init__(self) -> None:
        """iterations 域守卫（int>=1——solve_loop 首步即迭代）+tuple 归一。"""
        if isinstance(self.iterations, bool) or not isinstance(
            self.iterations, int
        ) or self.iterations < 1:
            raise InvalidDiagnosticsError(
                f"LoopRunStats.iterations 必须 int>=1：得到 {self.iterations!r}"
                "（solve_loop 首步即迭代——0 步收敛不存在）"
            )
        object.__setattr__(self, "loop_nodes", tuple(self.loop_nodes))


@dataclass(frozen=True)
@final
class ClosureLine:
    """单流体线厂级闭合（源Σ出流 vs 汇Σ出流；closure_rel=|Δ|/max(两边,1.0)）。"""

    fluid: str
    q_sources_total: float
    q_sinks_total: float
    closure_rel: float


@dataclass(frozen=True)
@final
class UnitImbalance:
    """单元×流体进出闭合（delta_rel=|Σ入−Σ出|/max(|Σ入|,1.0)；泥线减量=工艺事实）。"""

    unit_id: str
    fluid: str
    q_in: float
    q_out: float
    delta_rel: float


@dataclass(frozen=True)
@final
class FlowClosure:
    """单工况水量闭合审计：流体分线闭合 + 单元级偏差清单（|delta| 降序）。"""

    condition_key: str
    lines: tuple[ClosureLine, ...]
    unit_imbalances: tuple[UnitImbalance, ...]

    def __post_init__(self) -> None:
        """tuple 归一。"""
        object.__setattr__(self, "lines", tuple(self.lines))
        object.__setattr__(
            self, "unit_imbalances", tuple(self.unit_imbalances)
        )


@dataclass(frozen=True)
@final
class IndicatorMargin:
    """单工况×标准×指标裕度（margin=(限值−值)/限值，>=0 达标——quality.margin 语义）。"""

    condition_key: str
    standard_id: str
    indicator: str
    value: float
    limit: float
    margin: float


@dataclass(frozen=True)
@final
class DiagnosticsReport:
    """可信度诊断报告（独立并列 artifact 载荷，ADR-012 D1）。"""

    convergence: tuple[LoopRunStats, ...]
    loop_params: Mapping[str, float]
    mass_balance: tuple[FlowClosure, ...]
    effluent: tuple[IndicatorMargin, ...]
    repro: ReproTriple

    def __post_init__(self) -> None:
        """tuple 归一 + loop_params 只读快照冻结。"""
        object.__setattr__(self, "convergence", tuple(self.convergence))
        object.__setattr__(
            self, "loop_params", MappingProxyType(dict(self.loop_params))
        )
        object.__setattr__(self, "mass_balance", tuple(self.mass_balance))
        object.__setattr__(self, "effluent", tuple(self.effluent))


# serde 内核再导出（kbflag 批 2026-10-03 拆件；装载序契约双尾形态：本件
# 数据类定义先于尾段 import，trust_serde 侧同款尾段对向边——两侧任一
# 首导均闭环；消费方正门恒为 waterprint.contracts.trust）。
from waterprint.contracts.trust_serde import (  # noqa: E402
    deserialize_diag,
    serialize_diag,
)
