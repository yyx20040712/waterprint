"""执行器投影域件：UF-42 单元结果投影表（三键槽流量+指标键水质+dims 校验）。

输入:  UnitResult + unit_id（dims/外流股/水质面）
输出:  _dims_of（str→float 逐项有限性校验投影）/_snapshot（UnitResult
       Snapshot 装配）——executor.py 同名再导出（消费面零改动）；领域
       异常经 executor_dsl import（B3 R2 修正②——同向无环）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3 R2 2026-09-05：UF-42 投影域自 executor.py 拆出；
#   搬运零行为变化（签名/语义/报文零变，docstring 随迁）——投影口径
#   全文见 executor.py 规格说明【UF-42 投影表】节）
#
# 【迁移面】_dims_of（GR-02 dims 有限性守卫）/_snapshot（三键槽流量+
#   指标键水质+dims 校验的快照装配）；InvalidExecutionError 消费经
#   from waterprint.graph.executor_dsl import（定义面在 dsl——修正②）
#
# 【行为规格】与 executor.py 原文逐字同构；测试经 executor 再导出面
#   由 test_executor 覆盖，B3-R11 增 test_executor_projection 恒等钉面。
#
# 【参照】B3 简报 R2；重写计划 §14.1；简报 T7b D3（缺口 6 裁决）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

from waterprint.contracts.flow import WaterFlow
from waterprint.contracts.result_schema import UnitResultSnapshot
from waterprint.contracts.sludge import SludgeFlow
from waterprint.contracts.unit_api import UnitResult
from waterprint.graph.executor_dsl import InvalidExecutionError


def _dims_of(dims: object, unit_id: str) -> dict[str, float]:
    """UF-42 dims 投影：str→float 逐项有限性校验（GR-02），他形状拒。"""
    if not isinstance(dims, Mapping):
        raise InvalidExecutionError(
            f"单元 {unit_id!r} 的 dims 须为 str→float 映射：得到 {type(dims).__name__}")
    projected: dict[str, float] = {}
    for key, value in dims.items():
        numeric = (
            isinstance(key, str)
            and not isinstance(value, bool)
            and isinstance(value, int | float)
        )
        if not numeric or not isfinite(float(value)):
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 的 dims[{key!r}]={value!r} 非法（GR-02：字符串键→有限数值）")
        projected[key] = float(value)
    return projected


def _snapshot(result: UnitResult, unit_id: str) -> UnitResultSnapshot:
    """UF-42 投影表：三键槽流量+指标键水质+dims 校验（规格头【UF-42 投影表】）。"""
    outflows: dict[str, float] = {}
    for ref, stock in result.outflows.items():
        prefix = f"{unit_id}.{ref.port_id}"
        if isinstance(stock, WaterFlow):
            outflows[f"{prefix}.q_avg_daily"] = stock.q_avg_daily
            outflows[f"{prefix}.kz"] = stock.kz
            outflows[f"{prefix}.q_design"] = stock.q_design
        elif isinstance(stock, SludgeFlow):
            outflows[f"{prefix}.q_wet"] = stock.q_wet
            outflows[f"{prefix}.ds"] = stock.ds
            outflows[f"{prefix}.moisture"] = stock.moisture
        else:
            raise InvalidExecutionError(
                f"单元 {unit_id!r} 输出端口 {prefix} 股类型非法：{type(stock).__name__}")
    outqualities = {
        f"{unit_id}.{ref.port_id}.{indicator}": value
        for ref, quality in result.outqualities.items()
        for indicator, value in quality.concentrations.items()
    }
    return UnitResultSnapshot(
        unit_id=unit_id, outflows=outflows, outqualities=outqualities,
        dims=_dims_of(result.dims, unit_id), warnings=result.warnings,
        formula_ids=result.formula_ids)
