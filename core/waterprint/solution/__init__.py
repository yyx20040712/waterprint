"""L3 方案空间包根：枚举/约束过滤/排序/诊断，每文件一个阶段。

输入:  单元 manifest 离散配置 + 上游结果（固定上下文）
输出:  可行方案集合与诊断（enumerate 正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【导出白名单】（M-6 R1 轮落实际导出语句，2026-08-26 二审追认——
#   此前仅有注释清单无导出，D1 末条欠账补齐）
#   grid:        build_grid, GridTooLarge（B2 A2 2026-09-09 起 build_grid
#                增 keyword-only overrides——护栏基数接入假设覆盖管道，
#                公开导出签名变更注记）
#   enumerate:   enumerate_solutions
#   constraints: apply_constraints
#   ranking:     rank
#   diagnose:    diagnose_infeasibility
#   design_map:  resolve_axes, ensure_budget, axis_mappings,
#                build_design_map, derive_step, axis_point_budget,
#                widest_segment, DesignMap, ResolvedAxis,
#                DesignMapTooLarge, InvalidDesignMapError
#                （FD 批 2026-09-09：可行域引导正门件——app.run_design_map
#                装配消费；导出面与 grid/constraints 同门风格）
# 语义边界（ADR-005）：枚举对象永远是**单个工艺单元**（上游结果为固定
# 上下文）；全厂联合枚举为远期研究项，禁止伪装成本轮功能。
# ══════════════════════════════════════════════════════════════════

from waterprint.solution.constraints import apply_constraints
from waterprint.solution.design_map import (
    DesignMap,
    DesignMapTooLarge,
    InvalidDesignMapError,
    ResolvedAxis,
    axis_mappings,
    axis_point_budget,
    build_design_map,
    derive_step,
    ensure_budget,
    resolve_axes,
    widest_segment,
)
from waterprint.solution.diagnose import diagnose_infeasibility
from waterprint.solution.enumerate import enumerate_solutions
from waterprint.solution.grid import GridTooLarge, build_grid
from waterprint.solution.ranking import rank

__all__ = [
    "DesignMap",
    "DesignMapTooLarge",
    "GridTooLarge",
    "InvalidDesignMapError",
    "ResolvedAxis",
    "apply_constraints",
    "axis_mappings",
    "axis_point_budget",
    "build_design_map",
    "build_grid",
    "derive_step",
    "diagnose_infeasibility",
    "ensure_budget",
    "enumerate_solutions",
    "rank",
    "resolve_axes",
    "widest_segment",
]
