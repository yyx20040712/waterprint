"""裕度/成本排序与截断：可行方案 → 有序结果（浏览器千行流畅浏览的后端半）。

输入:  FilterResult + 排序键（裕度/成本/自定义字段 ID）+ 截断上限
输出:  排序后的方案切片与排序元信息
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_ranking.py）
#
# 【公开接口】
#   rank(filter_result, df: DataFrame, key: RankingKey, limit: int)
#       -> RankedSolutions（filter_result 经 FeasibleView 协议鸭子取
#       feasible——constraints/constraints.FilterResult 结构满足，
#       互不 import 约定下经参数传递，D1）
#   class RankingKey(不可变)：sort_by（字段 ID 或 "margin_min"/"cost"）、
#       ascending、tie_break（稳定的次序键列表；裸 str 拒）
#   class RankedSolutions(不可变)：rows（截断后的有序 DataFrame）、
#       total_feasible、truncated（bool）
#   class InvalidRankingError(Exception)：排序键列缺失/limit 非法
#       ——GR-11 族，本文件定义
#
# 【行为规格】
#   R1 排序确定性：tie_break 保证全序稳定（同输入同排序，可复算）；
#      禁止不稳定排序导致的方案行序漂移（UI 抖动与快照漂移源头）。
#   R2 裕度排序键 "margin_min"：全部达标裕度字段的最小值（最紧指标
#      优先）——语义固定并测试锁定；成本键依赖概算子系统注入的成本列
#      （"cost"），列缺失时抛领域异常（禁止静默回退裕度排序）。
#   R3 截断显式：limit 由服务层传入（分页），RankedSolutions 标注
#      truncated 与 total_feasible——前端必须可见"还有 N 条"。
#   R4 排序/过滤在 DataFrame 层完成（pandas 天然支持，§2 选型理由），
#      禁止手写行级循环。
#
# 【测试要求】确定性（乱序输入同输出）、tie_break 稳定、截断标注、
#   成本列缺失抛异常、margin_min 语义。
#
# 【参照】重写计划 §2/§12.2；ADR-005
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）


class InvalidRankingError(Exception):
    """排序非法（排序键列缺失/limit 非法/tie_break 形态）——GR-11 族。"""


class FeasibleView(Protocol):
    """可行索引视图协议（constraints.FilterResult 结构满足；互不 import）。"""

    @property
    def feasible(self) -> Sequence[int]: ...


@dataclass(frozen=True)
@final
class RankingKey:
    """排序键（不可变）：主键 + 方向 + 稳定次序键列表。"""

    sort_by: str
    ascending: bool
    tie_break: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """sort_by 非空 + tie_break 序列归一（裸 str 拒，I-2 同款防线）。"""
        if not isinstance(self.sort_by, str) or not self.sort_by:
            raise InvalidRankingError(
                f"RankingKey.sort_by 必须为非空字符串：得到 {self.sort_by!r}"
            )
        if isinstance(self.tie_break, str):
            raise InvalidRankingError(
                "RankingKey.tie_break 必须为键序列（tuple/list），不接受裸 str"
                f"（逐字符拆解为伪键）：得到 {self.tie_break!r}"
            )
        object.__setattr__(self, "tie_break", tuple(self.tie_break))


@dataclass(frozen=True)
@final
class RankedSolutions:
    """排序产出（不可变）：截断后的有序行 + 可行总数 + 截断标注。"""

    rows: pandas.DataFrame
    total_feasible: int
    truncated: bool


def rank(
    filter_result: FeasibleView,
    df: pandas.DataFrame,
    key: RankingKey,
    limit: int,
) -> RankedSolutions:
    """排序正门：可行子集 → DataFrame 层稳定全序排序 → 显式截断（R3/R4）。"""
    if limit < 1:
        raise InvalidRankingError(
            f"limit 须 ≥1（core 侧取全部由调用方传 total；分页默认 200 在"
            f"服务层，§12.2）：得到 {limit!r}"
        )
    subset = df.iloc[list(filter_result.feasible)]
    by = (key.sort_by, *key.tie_break)
    for column in by:
        if column not in subset.columns:
            role = "排序键" if column == key.sort_by else "次序键"
            raise InvalidRankingError(
                f"{role}列缺失：{column!r}（合法列 {list(subset.columns)}——"
                "R2 成本键缺成本列即此路径，禁静默回退裕度排序）"
            )
    ordered = subset.sort_values(
        list(by), ascending=[key.ascending] + [True] * len(key.tie_break), kind="stable"
    )
    truncated = len(ordered) > limit
    return RankedSolutions(
        rows=ordered.head(limit),
        total_feasible=len(ordered),
        truncated=truncated,
    )
