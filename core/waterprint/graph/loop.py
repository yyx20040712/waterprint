"""回路固定点迭代：阻尼/容差/发散诊断（污泥回流、内回流的求解器）。

输入:  回路组（SCC）+ compute 回调（由 executor 提供）+ 迭代参数
输出:  收敛结果或 LoopDivergence 诊断（含迭代历史）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7b 实现 D1 裁决 2026-08-25；镜像测试 tests/graph/test_loop.py）
#
# 【公开接口】
#   class LoopDivergence(Exception)：
#       loop_nodes: tuple[str, ...] / iterations: int / history:
#       tuple[float, ...]（构造三元组；最近 10 步残差——"若干步"
#       口径=T7b 冻结；供 UI 给出"用户拆环"建议，ADR-003）
#   @dataclass(frozen=True) class LoopConfig：tolerance: float /
#       max_iterations: int / damping: float 三字段必填无默认——
#       数值真源在 registry/assumptions 的 loop.* 条目（executor 从
#       env.engine_params 提取构造，GR-15 禁散落字面量）；本文件
#       不重复守卫（EngineParam 已过 GR-02 有限性，装配缺陷走 GR-08）
#   solve_loop(loop_group: list[str],
#              compute: Callable[[dict[str, float]], dict[str, float]],
#              init_guess: dict[str, dict[str, float]],
#              config: LoopConfig) -> dict[str, dict[str, float]]
#       ——四参形态锁定测试锁死，逐字不改
#
# 【行为规格】
#   R1 收敛判据=全部变量相对残差过关：|x_new − x_old| / max(|x_old|,
#      1.0) < tolerance（混合尺度分母下限 1.0 防零除——工程惯例类，
#      规格头注记）；迭代律 x_{n+1} = x_n + ω·(F(x_n) − x_n)（阻尼
#      ADR-003 R3）。
#   R2 发散/不收敛：超过 max_iterations 仍不收敛 → 抛 LoopDivergence
#      （禁止静默返回最后一次迭代值——那是最危险的谎言）；三字段全载：
#      回路组 / 迭代数 / history（每步记全变量相对残差的最大值）。
#   R3 纯函数语义：同输入同收敛路径（R5 确定性，禁随机初始化；
#      init_guess 由调用方确定性地提供）。
#   R4 迭代历史进计算迹：每次迭代记录残差（本文件内载 history 供
#      发散诊断；PlantResult.trace 链路归 M1 collector——T7b 结构
#      就位不伪造，冲突记档 D10）。
#   R5 残差为 NaN（上游溢出等）时 NaN < tolerance 恒 False → 不收敛
#      → 走 R2 发散路径（fail-safe，禁静默通过）。
#   R6 远期：Broyden/Anderson 加速作为可替换策略注入，接口不变。
#
# 【摊平口径】（Explore 缺口 1 裁决，T7b 冻结）
#   solve_loop 把两层 init_guess 摊平为单层 dict 喂 compute（外层
#   节点名剥掉、内层变量名直并），返回解按 init_guess 的节点分桶
#   还原两层；变量名全局唯一性义务在调用方——executor 构造 compute
#   时用 f"{node}.{var}" 键（与 ports._ref 的 GR-09 展示形态
#   unit_id.port_id 同款纪律）。
#
# 【数值纪律】本文件不在魔法数字白名单——字面量仅 0/1/2/10
#   （分母下限 1.0、history 尾长 10）。
#
# 【测试要求】已知线性回路收敛到解析解、发散回路抛 LoopDivergence
#   且 history 非空、阻尼=1 与阻尼<1 的迭代步数对比、
#   确定性（同输入双跑迭代路径相同）。
#
# 【参照】重写计划 §3-3/§8 风险行/§16 A2；ADR-003；简报 T7b D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import final


# N818 豁免理由：LoopDivergence 之名由锁定测试 test_loop.py、本规格头
# 【公开接口】与宪法 §3 领域异常例举（"InvalidUnitConfig / LoopDivergence 等"）
# 三重冻结，改名 = 破坏锁定契约（UF-45 豁免备案同族先例 ExprSyntaxError）。
class LoopDivergence(Exception):  # noqa: N818
    """回路迭代不收敛（禁止静默返回末值）——携带诊断三元组（R2）。"""

    loop_nodes: tuple[str, ...]
    iterations: int
    history: tuple[float, ...]

    def __init__(
        self,
        loop_nodes: tuple[str, ...],
        iterations: int,
        history: tuple[float, ...],
    ) -> None:
        """构造诊断三元组（回路组/迭代数/最近若干步残差）。"""
        self.loop_nodes = tuple(loop_nodes)
        self.iterations = iterations
        self.history = tuple(history)
        tail = ", ".join(f"{value:.3e}" for value in self.history[-2:])
        super().__init__(
            f"回路迭代不收敛：回路组 {list(self.loop_nodes)} 经 "
            f"{self.iterations} 步未达容差（禁止静默返回末值——R2）；"
            f"最近残差 [{tail}]（完整 history 见异常字段，"
            "用户拆环建议见 ADR-003）"
        )


@dataclass(frozen=True)
@final
class LoopConfig:
    """迭代参数三件套（必填无默认；数值真源=registry/assumptions loop.*）。"""

    tolerance: float
    max_iterations: int
    damping: float


def _step(
    state: dict[str, float],
    evaluated: dict[str, float],
    config: LoopConfig,
) -> tuple[dict[str, float], float]:
    """单步阻尼更新：返回（新状态, 全变量相对残差最大值）。"""
    updated: dict[str, float] = {}
    residual_max = 0.0
    for name, old in state.items():
        # compute 输出缺变量名 = 调用方闭包构造缺陷：原生 KeyError
        # （GR-08 禁静默默认——propagate"src 端口不在 upstream"同款口径）。
        fresh = evaluated[name]
        new = old + config.damping * (fresh - old)
        updated[name] = new
        residual = abs(new - old) / max(abs(old), 1.0)
        residual_max = max(residual_max, residual)
    return updated, residual_max


def solve_loop(
    loop_group: list[str],
    compute: Callable[[dict[str, float]], dict[str, float]],
    init_guess: dict[str, dict[str, float]],
    config: LoopConfig,
) -> dict[str, dict[str, float]]:
    """阻尼固定点迭代至全变量相对残差过关；超限抛 LoopDivergence（R1/R2）。

    摊平口径：init_guess 两层（节点→变量→值）摊平为单层喂 compute，
    返回解按 init_guess 的节点分桶还原；变量名全局唯一性义务在调用方
    （executor 以 f"{node}.{var}" 键构造，见本文件规格头【摊平口径】）。
    """
    state = {
        name: value
        for bucket in init_guess.values()
        for name, value in bucket.items()
    }
    history: list[float] = []
    for _ in range(config.max_iterations):
        evaluated = compute(dict(state))
        state, residual = _step(state, evaluated, config)
        history.append(residual)
        if residual < config.tolerance:
            return {
                node: {name: state[name] for name in bucket}
                for node, bucket in init_guess.items()
            }
    raise LoopDivergence(
        loop_nodes=tuple(loop_group),
        iterations=config.max_iterations,
        history=tuple(history[-10:]),
    )
