"""批量方案计算：网格 × 上游上下文 → 结果 DataFrame（枚举管线主体）。

输入:  Grid + 上游 UnitContext 快照（固定）+ 单元 compute（唯一计算源）+ RunEnv
输出:  结果 DataFrame（每行一个方案：参数列 + 结果维度字段列 + 标注列）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_enumerate.py）
#
# 【公开接口】
#   enumerate_solutions(grid: Grid, upstream: UnitContext,
#                       unit: Unit, env: RunEnv) -> pandas.DataFrame
#       （env: RunEnv 类型定义于 contracts/run_env.py——L0 契约，
#        SENS-B 2026-08-23 UF-31 注记）
#
# 【行为规格】
#   R1 单实现双用（§3 保证 1；M2-SOL 现实口径修订 2026-08-26）：枚举与
#      单点计算走**同一个 unit.compute**（逐网格行驱动：dataclasses.
#      replace 换 params、trace 换空 sink）——防双轨的实质=唯一计算源
#      （N=1 网格行结果==单点 compute 的锁定断言由此成立）。原规格头
#      "向量化批量喂入"与现状不符（formulas.apply 标量强类型+13 单元
#      标量守卫是已锁定架构，改造=重写 13 单元超 M2 范围）——apply
#      向量化增强挂账 UF（并入 UF-36 注记）；万级 <5s 预算探针实测
#      （§18.1，超限挂账非阻塞）。行迹用空 sink：枚举结果表本身即
#      审计面，万级落迹会爆炸。
#   R2 物理不变性（性质测试常驻）：结果维度字段非负；有效容积类字段
#      随池数/尺寸参数单调（在网格有序维上断言）。
#   R3 上游上下文冻结：枚举期间上游量不变（快照传入）；工况取当前
#      选定档（枚举结果标注 condition_key 列）。
#   R4 输出形态：DataFrame 列 = grid 参数列（fields 序）+ dims 结果列
#      （首见序）+ margin_min 预备列（margin_* 达标裕度字段行最小值，
#      无裕度字段=NaN）+ nan_flag 标注列 + condition_key 列；行序=grid
#      序，排序/分页在 ranking/服务层做，本文件不做截断（§12.2 分页
#      默认 200 条在服务层）。
#   R5 NaN 政策：约束外推导致的 NaN 不允许静默通过——nan_flag 显式
#      标注列，下游过滤时计数报告。口径分界（GR-37，SENS-B
#      2026-08-23 UF-36）：GR-02 管量与守恒路径零 NaN/Inf；本结果表
#      NaN 标注列是终态数据非中间量，不违 GR-02。
#      【行级域拒口径（M2-SOL 实装注记）】行 compute 抛领域异常
#      （_ROW_DOMAIN_EXCEPTIONS 在册族，与 executor._DOMAIN_EXCEPTIONS
#      同源同步义务——B4 双胞胎禁私有 import）= 探索到非法档（如 CASS
#      时段和≠周期档）：该行 dims 全 NaN + nan_flag=True 进表（枚举=
#      设计空间探索，域拒是正常探索结果，交 constraints/diagnose 管
#      线；单点路径 executor 仍整工况失败——两路径分歧为语义性设计）。
#      行级拒绝原因消息不进表（列面挂账 server 批：reject_reason 列）。
#
# 【测试要求】N=1 网格结果 == 单点 compute（防双轨）、结果行数 == total、
#   非负性/单调性性质、condition_key 标注。
#
# 【参照】重写计划 §3-1/§12.4/§18.1；ADR-005
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import replace
from math import isnan, nan
from typing import Any, final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.flow import InvalidFlowError
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.quality import InvalidQualityError
from waterprint.contracts.run_env import RunEnv
from waterprint.contracts.sludge import InvalidSludgeError
from waterprint.contracts.trace_api import TraceNodeSpec
from waterprint.contracts.unit_api import Unit, UnitContext
from waterprint.registry.formulas import InvalidFormulaError
from waterprint.solution.grid import Grid

_MARGIN_PREFIX = "margin_"
# 行级域拒族（R5 注记）：新增领域异常族须同步本元组（executor 的
# _DOMAIN_EXCEPTIONS 同源同步义务——双胞胎禁私有 import，记档）。
_ROW_DOMAIN_EXCEPTIONS = (
    InvalidUnitConfig,
    InvalidFlowError,
    InvalidQualityError,
    InvalidSludgeError,
    InvalidFormulaError,
)


@final
class _NullSink:
    """空迹收集器（行迹专用：枚举表即审计面，万级落迹会爆炸——R1 注记）。"""

    def record(self, node: TraceNodeSpec) -> None:
        """丢弃记录（结构满足 TraceSink 协议）。"""


_NULL_SINK: _NullSink = _NullSink()


def _dims_of(dims: object) -> dict[str, float]:
    """UnitResult.dims 收窄为 dict[str, float]（13 单元 compute 契约形状）。"""
    if not isinstance(dims, dict):
        raise TypeError(
            f"unit.compute 的 dims 须为 str→float 映射：得到 {type(dims).__name__}"
            "（13 单元契约形状——GR-08 程序缺陷口径）"
        )
    return {str(key): float(value) for key, value in dims.items()}


def _margin_min(dims: dict[str, float], margin_fields: tuple[str, ...]) -> float:
    """R2 预备列：全部达标裕度字段的最小值（最紧指标优先；无裕度字段=NaN）。"""
    values = [dims[key] for key in margin_fields if not isnan(dims.get(key, nan))]
    return min(values) if values else nan


def enumerate_solutions(
    grid: Grid, upstream: UnitContext, unit: Unit, env: RunEnv
) -> pandas.DataFrame:
    """枚举正门：逐网格行驱动同一 unit.compute（R1 防双轨实质），行序=grid 序。

    env 为执行环境透传（签名冻结，UF-31）；行 ctx 的上游量/工况/假设
    沿用 upstream 冻结快照（R3），params=快照参数 ∪ 行参数（行值优先）。
    """
    dims_rows: list[dict[str, float]] = []
    for row in grid.array:
        params = dict(upstream.params)
        params.update({field: float(row[field]) for field in grid.fields})
        try:
            result = unit.compute(replace(upstream, params=params, trace=_NULL_SINK))
            dims_rows.append(_dims_of(result.dims))
        except _ROW_DOMAIN_EXCEPTIONS:
            dims_rows.append({})  # 行级域拒：dims 全 NaN+nan_flag=True（R5 注记）
    dim_fields: list[str] = []
    seen: set[str] = set()
    for dims in dims_rows:
        for key in dims:
            if key not in seen:
                seen.add(key)
                dim_fields.append(key)
    margin_fields = tuple(k for k in dim_fields if k.startswith(_MARGIN_PREFIX))
    data: dict[str, list[Any]] = {
        field: [float(row[field]) for row in grid.array] for field in grid.fields
    }
    for key in dim_fields:
        data[key] = [dims.get(key, nan) for dims in dims_rows]
    data["margin_min"] = [_margin_min(dims, margin_fields) for dims in dims_rows]
    data["nan_flag"] = [
        not dims or any(isnan(value) for value in dims.values())
        for dims in dims_rows  # 空 dims=行级域拒（R5 注记）——一并标注
    ]
    data["condition_key"] = [ConditionSet.key(upstream.condition)] * grid.total
    return pandas.DataFrame(data)
