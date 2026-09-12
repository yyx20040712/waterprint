"""枚举结果载荷组装件：diagnosis 序列化 + grid/dim 列族投影 + result 装配。

输入:  枚举产出（EnumerationOutcome）+ 行文件句柄 + 任务 payload +
       项目与工况集（worker _run_enumerate 尾段整迁）
输出:  enumeration_payload（worker result dict 正门——worker 500 行
       预算减压拆件，datapack.py/dwg.py 先例同制）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（ADR-018 D5 拆分 2026-09-12：枚举载荷组装段自 worker.py
#   _run_enumerate 尾段整迁——worker 行数预算正解[沿册工序：增功能
#   优先抽 jobs/ 拆件]；搬运零行为变化，消费面=worker 唯一）
#
# 【公开接口】
#   enumeration_payload(outcome, rows_file, payload, project, conditions)
#       -> dict[str, Any]（done 态 result 载荷正门）
#
# 【行为规格】
#   R-1 diagnosis 序列化（无解交付面）：minimal_conflicts 逐集 sorted +
#      fail_counts 直转 + suggestions dataclasses.asdict（worker 原段
#      逐字随迁——done+feasible_count=0 合法终态语义归 worker R4）。
#   R-2 grid_fields 载荷（B2② PD4/PD6）：[{key,dim,label_zh}]——自该单元
#      manifest.params 按 field_id 查（discover_units 注册表=装配同源；
#      label_zh 真源缺=None 直传，禁 field_id 降级填充——兜底归 webapp）。
#   R-3 dim_fields 载荷（V2 GOV5 批尾）：同形——自 manifest.out_dims 查
#      （计算派生输出量；未声明键 label_zh=None 直传，key 兜底归 webapp）；
#      列族=rows.columns 减 grid 轴减保留三列（margin_min/nan_flag/
#      condition_key）。
#   R-4 溯源与工况面：unit_id（P0-2 深链回填源）/design_hash（枚举时点
#      摘要——FE 漂移闸③源）/condition_keys（ADR-018 D5——多工况行族
#      键清单，calc 面同制，FE 工况列筛选真源）。
#
# 【参照】ADR-018；jobs/datapack.py（拆件先例）；jobs/worker.py（消费面）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from waterprint import app as core
from waterprint.contracts.condition import ConditionSet
from waterprint.contracts.project_schema import ProjectFile

__all__ = ["enumeration_payload"]


def _diagnosis_of(outcome: core.EnumerationOutcome) -> dict[str, Any] | None:
    """诊断序列化（R-1）：None 透传（有解面）；无解=三键直转。"""
    if outcome.diagnosis is None:
        return None
    return {
        "minimal_conflicts": [
            sorted(conflict) for conflict in outcome.diagnosis.minimal_conflicts
        ],
        "fail_counts": dict(outcome.diagnosis.fail_counts),
        "suggestions": [dataclasses.asdict(s) for s in outcome.diagnosis.suggestions],
    }


def enumeration_payload(
    outcome: core.EnumerationOutcome,
    rows_file: Path,
    payload: Mapping[str, Any],
    project: ProjectFile,
    conditions: ConditionSet,
) -> dict[str, Any]:
    """枚举 done 态 result 载荷正门（R-1~R-4——worker _run_enumerate 尾段）。"""
    unit_manifest = core.discover_units()[str(payload["unit_id"])][0]
    spec_by_field = {s.field_id: s for s in unit_manifest.params}
    out_dim_by_field = {s.field_id: s for s in unit_manifest.out_dims}
    dim_field_names = [
        k for k in outcome.rows.columns
        if k not in {*outcome.grid.fields, "margin_min", "nan_flag", "condition_key"}
    ]
    return {
        "state": "done",
        "rows_file": str(rows_file),
        "total_feasible": int(outcome.total_feasible),
        "feasible_count": int(outcome.total_feasible),
        "truncated": bool(outcome.truncated),
        "diagnosis": _diagnosis_of(outcome),
        "columns": [str(column) for column in outcome.rows.columns],
        "grid_fields": [
            {"key": f, "dim": str(spec_by_field[f].dim), "label_zh": spec_by_field[f].label_zh}
            for f in outcome.grid.fields
        ],
        "dim_fields": [
            {"key": k, "dim": str(spec.dim), "label_zh": spec.label_zh}
            if (spec := out_dim_by_field.get(k)) is not None
            else {"key": k, "dim": "", "label_zh": None}
            for k in dim_field_names
        ],
        "project_id": payload.get("project_id", ""),
        "unit_id": str(payload["unit_id"]),
        "design_hash": core.design_hash(project.design),
        "condition_keys": [ConditionSet.key(c) for c in conditions.iter_all()],
    }
