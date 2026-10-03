"""calc 命令域：flows 全链编排+kb 宽容装载注入（退出码 0/3/4）。

输入:  CLI calc 参数（project/--conditions/--data-dir/--out）+数据包
       constraint_kb（kb 执法面数据源）
输出:  进程退出码+stdout 六指标摘要+result.json 确定性落盘（flows 通道）
"""

# ══════════════════════════════════════════════════════════════════
# 规格（kbwire-20261003 拆件：_run_calc/_CALC_* 自 cli.py 原文整迁
#   +kb 装载段——cli.py 500/500 贴墙，命令域伴生件；镜像测试
#   tests/app/test_cli_calc.py ①②③。）
#
# 【公开接口】
#   run_calc_command(project_path, conditions, data_dir, out) -> int
#       = cli._run_calc 原文（R6 flows 全链→摘要+落盘；退出码 0/3/4）；
#       cli.py 分发表经别名 import 消费（表零改动）。
#   _CALC_VALIDATIONS/_CALC_FAILURES: Final[tuple[type[BaseException], ...]]
#       自 cli.py 迁入+InvalidConstraintError 并入 VALIDATIONS（kb 坏档
#       →退出码 3 读入校验族——kbwire 接线）。
#
# 【kb 装载语义（宽容面）】kb 文件缺失→warnings.warn+()（不注入——
#   build_standards_flow 同款 is_file 前置）；文件在场→load_kb_constraints
#   fail-fast（坏档经 _CALC_VALIDATIONS→3）。路径经 flows._CONSTRAINT_KB/
#   _CONSTRAINTS_FILE 私有引用（executor_dsl 跨件私有引用先例——禁路径
#   字面量双源）。装载入 try 段（kb 装载异常收编 3 族）。
#
# 【禁止事项】不持有其余子命令（归 cli.py）；零数值字面量。
# 【参照】cli_common.py（共享底座）；flows（用例流层）
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Final

from waterprint import flows
from waterprint.app import InvalidAssemblyError, InvalidProjectError, load_project
from waterprint.cli_common import (
    _EXIT_CALCULATION,
    _EXIT_OK,
    _EXIT_VALIDATION,
    _data_dir,
    _user_out,
)
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import InvalidConnection
from waterprint.graph import LoopDivergence
from waterprint.graph.executor_dsl import InvalidExecutionError
from waterprint.graph.nodes import InvalidNodeError
from waterprint.registry.coefficients import InvalidCoefficientError
from waterprint.solution.constraints import (
    InvalidConstraintError,
    KbConstraint,
    load_kb_constraints,
)

# calc 面 3 族（读入/守护/装配校验+kb 坏档）与 4 族（执行期领域异常）——R6。
_CALC_VALIDATIONS: Final[tuple[type[BaseException], ...]] = (
    InvalidProjectError, InvalidAssemblyError, InvalidCoefficientError,
    InvalidConstraintError, flows.InvalidFlowError, OSError,
)
_CALC_FAILURES: Final[tuple[type[BaseException], ...]] = (
    LoopDivergence, InvalidNodeError, InvalidConnection,
    InvalidUnitConfig, InvalidExecutionError,
)


def run_calc_command(project_path: str, conditions: str | None,
                     data_dir: str | None, out: str | None) -> int:
    """calc：flows 全链（+kb 宽容装载注入）→摘要+warnings 计数（0/3/4）。"""
    source = Path(project_path).resolve()
    target = _user_out(out, source.with_suffix(".result.json"))
    if target is None:
        return _EXIT_VALIDATION
    keys = None if conditions is None else [k for k in conditions.split(",") if k]
    pack = _data_dir(data_dir)
    try:
        project = load_project(source)
        env = flows.build_env_flow(pack, project)
        cond = flows.build_condition_flow(project, keys)
        standards = flows.build_standards_flow(pack)
        # 跨件私有引用（executor_dsl 先例——禁路径字面量双源，规格节记档）
        kb_path = pack / flows._CONSTRAINT_KB / flows._CONSTRAINTS_FILE  # noqa: SLF001
        constraints: tuple[KbConstraint, ...] = ()
        if kb_path.is_file():
            constraints = load_kb_constraints(kb_path)
        else:
            warnings.warn(
                f"约束知识库缺失：{kb_path}（kb 执法面不注入——宽容面，"
                "build_standards_flow 同款）", stacklevel=2)
        result = flows.run_calc_flow(
            project, cond, env, standards, constraints=constraints, result_out=target)
    except _CALC_VALIDATIONS as exc:
        print(f"[校验失败] 读入/装配/守护：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    except _CALC_FAILURES as exc:
        print(f"[计算失败] 执行期：{exc}", file=sys.stderr)
        return _EXIT_CALCULATION
    warns = sum(
        len(unit.warnings)
        for snapshot in result.plant.conditions.values()
        for unit in snapshot.values()
    )
    print(
        f"计算完成：{len(result.plant.conditions)} 工况 / warnings {warns} 条 / "
        f"design_digest {result.design_digest}"
    )
    for condition_key in result.plant.conditions:
        summary = result.plant.summary.get(condition_key, {})
        line = "  ".join(f"{k}={v:.6g}" for k, v in summary.items())
        print(f"  [{condition_key}] {line or '（无水质键——非市政终水口径）'}")
    print(f"  结果已写入 {result.result_path}（serialize 确定性——GR-38 原子落盘）")
    return _EXIT_OK
