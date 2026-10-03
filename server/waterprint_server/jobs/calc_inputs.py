"""calc 任务数据装配件：出水标准+约束知识库双装载（fail-fast）。

输入:  data_dir 数据包根（server settings 绝对路径）+constraint_kb
输出:  calc_inputs——(standards, constraints) 双元组（worker calc job
       唯一消费面；worker 500 行预算减压拆件，datapack.py/dwg.py 先例同制）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（kbwire-20261003 拆件：ADR-018 D5 拆分先例同制——增功能
#   优先抽 jobs/ 拆件；worker._run_calc standards 段零变迁入+kb 装载
#   注入新增；镜像测试 server/tests/jobs/test_calc_inputs.py）
#
# 【公开接口】
#   calc_inputs(data_dir: Path) -> tuple[tuple[EffluentStandard, ...],
#                                        tuple[KbConstraint, ...]]
#       standards=app.load_effluent_standards（现 worker 段零变迁——
#       ADR-012 D4/D6 数据装配注入）+constraints=app.load_kb_constraints
#       （kb fail-fast：缺文件/坏档=数据装配缺陷，standards D6 同口径）。
#
# 【行为规格】
#   R1 fail-fast 双装载：两装载器均不静默空表；kb 先装载（缺文件=
#       InvalidConstraintError——kbwire 接线批口径），standards 随后
#       （同路径同文件两视图：effluent 12 条/kb 全量 34 条）。
#   R2 零筛选注入：kb 全量条目返回（face 自筛 kind/unit_kinds/字段
#       ——app_maintenance 适用判据单源，本件不预筛）。
#
# 【禁止事项】不持有 job 编排（归 worker）；路径字面量与 worker 旧段
#   同源单份（迁移非双源）。
# 【参照】ADR-018 D5；jobs/enum_payload.py（拆件先例）；jobs/worker.py
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from pathlib import Path

from waterprint import app as core
from waterprint.contracts.quality import EffluentStandard

__all__ = ["calc_inputs"]


def calc_inputs(
    data_dir: Path,
) -> tuple[tuple[EffluentStandard, ...], tuple[core.KbConstraint, ...]]:
    """standards+kb 双装载正门（R1 fail-fast——kb 先、standards 后）。"""
    kb_path = data_dir / "constraint_kb" / "constraints.json"
    constraints = core.load_kb_constraints(kb_path)
    standards = core.load_effluent_standards(kb_path)
    return standards, constraints
