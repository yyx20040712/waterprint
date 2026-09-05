/**
 * 任务流重连治理纯函数测试（B6 D3：退避梯/封顶/停连慢探测——node 直测）。
 *
 * 输入:  useTaskFeed 导出的 nextReconnectDelayMs/planRecovery（时间逻辑
 *        纯函数面——壳内 EventSource 生命周期薄壳不测先例维持）
 * 输出:  指数梯 1s→30s 封顶+达限切 60s 慢探测（错误态）断言
 */
import { describe, expect, it } from "vitest";

import {
  nextReconnectDelayMs,
  planRecovery,
  SSE_FAILURE_LIMIT,
} from "./useTaskFeed";

describe("nextReconnectDelayMs（指数退避梯——B6 D3）", () => {
  it("1s/2s/4s/8s/16s 指数梯，封顶 30s", () => {
    expect(nextReconnectDelayMs(1)).toBe(1000);
    expect(nextReconnectDelayMs(2)).toBe(2000);
    expect(nextReconnectDelayMs(3)).toBe(4000);
    expect(nextReconnectDelayMs(4)).toBe(8000);
    expect(nextReconnectDelayMs(5)).toBe(16000);
    expect(nextReconnectDelayMs(6)).toBe(30000); // 封顶
    expect(nextReconnectDelayMs(100)).toBe(30000); // 远超封顶不增长
  });
});

describe("planRecovery（停连+慢探测恢复——B6 D3 必改4）", () => {
  it("未达上限=指数退避；达上限=60s 慢探测（错误态停激进重连）", () => {
    expect(planRecovery(1)).toEqual({ mode: "backoff", delayMs: 1000 });
    expect(planRecovery(SSE_FAILURE_LIMIT - 1)).toEqual({
      mode: "backoff",
      delayMs: 8000,
    });
    expect(planRecovery(SSE_FAILURE_LIMIT)).toEqual({
      mode: "probe",
      delayMs: 60000,
    });
    expect(planRecovery(SSE_FAILURE_LIMIT + 1).mode).toBe("probe"); // 持续错误态
  });
});
