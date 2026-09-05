"""SSE 连接限流器：四维计数+建连令牌桶（app 内内存权威，零新依赖）。

输入:  Settings 四旋钮（sse_max_connections / sse_max_subscribers_per_task /
       sse_max_subscribers_per_project / sse_connect_rate_per_second）
       + events 两端点建连/订阅/断开时点调用
输出:  RateLimitedError（429+Retry-After）+ SseLimiter（check_connect /
       reserve_task / reserve_project / release_task / release_project）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 批 2026-09-06，简报 D1~D7；镜像测试
# server/tests/routers/test_sse_limits.py）
#
# 【公开接口】
#   RateLimitedError  超限领域异常（Error 后缀沿族——main 统一 handler
#                     派生 error_type=类名；429+冻结错误体 {detail,
#                     error_type}+Retry-After 建议性头）
#   SseLimiter        四维限流器（每 app 一份——main lifespan 构造挂
#                     ServiceContext.sse_limiter；零 fastapi 依赖，
#                     services 层可安全 import）
#
# 【行为规格】
#   R1 四维（D4）：全局并发连接数 / 每任务订阅数 / 每项目订阅数 /
#      建连速率（令牌桶，突发=2×rate 固定不增旋钮）；per-token 不设
#      （单静态 token 退化）；计数器=进程内存态（重启清零，
#      replicas=1 部署契约 main R6）。
#   R2 check+add 同一同步临界区（D4 建议）：全部方法零 await——单事件
#      循环下原子；断开释放经 events._stream finally 回调（连接关闭=
#      计数回收，无泄漏）。
#   R3 建连闸 check_connect 在 include 级依赖序先于 verify_token_sse
#      （D3 必改1：401 风暴的建连消耗被 429 前置压制——只消费速率令牌
#      +全局阈探测，不改计数：认证失败无连接产生即无占位可泄）。
#   R4 鉴权关（匿名）四维全额生效（D2：维度身份无关）；旋钮 None=
#      该维不启用（沿 WP4 task_registry_cap 先例）。
#
# 【错误与边界】超限 raise RateLimitedError；retry_after 建议值：速率维=
#   桶内补一枚令牌所需秒数（向上取整），容量维=1 秒（槽位释放时刻
#   不可预知——建议性语义，D5：EventSource 遵从度不一，不依赖）。
#   【禁止事项】不引第三方限流库（uv.lock 零新依赖）；不做 per-IP/
#   per-token 维度（D4）；不声明 responses（429 不入 openapi——零字节
#   破面）；本模块禁 import fastapi/starlette（services 消费面 §13.4）。
#
# 【测试要求】test_sse_limits.py 八例（低阈值旋钮验证逻辑不真实挂满
#   100 连接；配置值生效单列；断开释放回收；鉴权关全额生效；None 回退）。
# 【参照】.workflow/briefs/task-B6-brief.md D2~D5；重写计划 §16 A5/§17.3
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import math
import time

from waterprint_server.settings import Settings

# 容量维 Retry-After 建议秒数（槽位释放时刻不可预知——白名单字面量 1）。
_CAPACITY_RETRY_S = 1


class RateLimitedError(Exception):
    """SSE 建连/订阅超限（429 面——main 统一翻译+Retry-After 建议头）。"""

    def __init__(self, detail: str, retry_after: int = _CAPACITY_RETRY_S) -> None:
        super().__init__(detail)
        self.retry_after = retry_after


class SseLimiter:
    """四维 SSE 限流器（方法内零 await——单事件循环同步临界区原子）。"""

    def __init__(
        self,
        *,
        max_connections: int | None,
        max_subscribers_per_task: int | None,
        max_subscribers_per_project: int | None,
        connect_rate_per_second: int | None,
    ) -> None:
        self._max_connections = max_connections
        self._max_per_task = max_subscribers_per_task
        self._max_per_project = max_subscribers_per_project
        self._rate = connect_rate_per_second
        self._global = 0
        self._task_counts: dict[str, int] = {}
        self._project_counts: dict[str, int] = {}
        # 令牌桶满态起步（突发=2×rate 固定，D4）；rate None=该维关。
        self._tokens = float(2 * connect_rate_per_second) if connect_rate_per_second else 0.0
        self._last_refill = time.monotonic()

    @classmethod
    def from_settings(cls, settings: Settings) -> SseLimiter:
        """装配（main lifespan——旋钮真源 Settings 五联动免散落）。"""
        return cls(
            max_connections=settings.sse_max_connections,
            max_subscribers_per_task=settings.sse_max_subscribers_per_task,
            max_subscribers_per_project=settings.sse_max_subscribers_per_project,
            connect_rate_per_second=settings.sse_connect_rate_per_second,
        )

    def check_connect(self) -> None:
        """建连检查：速率令牌消费+全局阈探测（不改计数——失败连接无占位）。"""
        self._consume_rate_token()
        if self._max_connections is not None and self._global >= self._max_connections:
            raise RateLimitedError(
                f"SSE 全局连接数已达上限 {self._max_connections}（断开即释放；"
                "权威判定在订阅占位 reserve_*，此处仅前置探测）"
            )

    def reserve_task(self, task_id: str) -> None:
        """任务流占位：全局+每任务两维 check+add（events.py 端点体调用）。"""
        self._reserve(self._max_per_task, self._task_counts, "任务", task_id)

    def reserve_project(self, project_id: str) -> None:
        """项目流占位：全局+每项目两维 check+add（同上）。"""
        self._reserve(self._max_per_project, self._project_counts, "项目", project_id)

    def release_task(self, task_id: str) -> None:
        """任务流计数回收（events._stream finally——连接关闭时点）。"""
        self._release(self._task_counts, task_id)

    def release_project(self, project_id: str) -> None:
        """项目流计数回收（同上）。"""
        self._release(self._project_counts, project_id)

    def _reserve(
        self, cap: int | None, counts: dict[str, int], label: str, key: str
    ) -> None:
        """三维联合占位（同步块原子：两检查与两自增之间零 await）。"""
        if self._max_connections is not None and self._global >= self._max_connections:
            raise RateLimitedError(
                f"SSE 全局连接数已达上限 {self._max_connections}（断开即释放）"
            )
        if cap is not None and counts.get(key, 0) >= cap:
            raise RateLimitedError(f"SSE 每{label}订阅数已达上限 {cap}（key={key}）")
        self._global += 1
        counts[key] = counts.get(key, 0) + 1

    def _release(self, counts: dict[str, int], key: str) -> None:
        """计数回收（全局+单维两处；幂等下限 0；键清零即删不膨胀）。"""
        if self._global > 0:
            self._global -= 1
        if counts.get(key, 0) > 1:
            counts[key] -= 1
        else:
            counts.pop(key, None)

    def _consume_rate_token(self) -> None:
        """令牌桶（突发=2×rate 固定）：不足即 429（retry_after=补 1 枚秒数）。"""
        if self._rate is None:
            return
        now = time.monotonic()
        burst = 2 * self._rate
        self._tokens = min(float(burst), self._tokens + (now - self._last_refill) * self._rate)
        self._last_refill = now
        if self._tokens >= 1:
            self._tokens -= 1
            return
        wait_s = max(1, math.ceil((1 - self._tokens) / self._rate))
        raise RateLimitedError(
            f"SSE 建连速率超限（{self._rate}/s，突发 {burst}）", retry_after=wait_s
        )
