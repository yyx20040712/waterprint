/**
 * 会话历史退避重试测试（F2 B-1——首轮竞态 502 兜底）。
 *
 * 输入:  useHistoryRetry hook（React hooks 桩零渲染器直驱——
 *        useTaskEventSource.test 同款惯例）+nextHistoryRetryDelayMs 纯函数
 * 输出:  退避梯（500/1000/2000ms）+502→200 序列（首轮失败二轮成功——
 *        重试发生且成功即停）+耗尽即停（三梯上限，禁无限静默重试）
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  HISTORY_RETRY_MAX,
  nextHistoryRetryDelayMs,
  useHistoryRetry,
} from "./historyRetry";

// ---- React hooks 桩（零渲染器直驱 effect——useTaskEventSource.test 惯例）----
const reactStub = vi.hoisted(() => ({
  effects: [] as Array<() => void | (() => void)>,
}));
vi.mock("react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react")>();
  return {
    ...actual,
    useEffect: (effect: () => void | (() => void)) => {
      reactStub.effects.push(effect);
    },
  };
});

/** 直驱 hook：单次渲染态调用→立即执行收集到的 effect→返回清理器。 */
function mountRetry(pending: boolean, refetch: () => Promise<unknown>): () => void {
  useHistoryRetry(pending, refetch);
  const effect = reactStub.effects[reactStub.effects.length - 1];
  if (effect === undefined) {
    throw new Error("未收集到 useHistoryRetry effect（hooks 桩失效）");
  }
  reactStub.effects.length = 0;
  const cleanup = effect() as (() => void) | undefined;
  return cleanup ?? (() => {});
}

describe("nextHistoryRetryDelayMs 退避梯（B-1：500ms 起指数）", () => {
  it("三梯延迟 500/1000/2000ms（500ms 起指数 ×3——工单 B-1 口径）", () => {
    expect(nextHistoryRetryDelayMs(0)).toBe(500);
    expect(nextHistoryRetryDelayMs(1)).toBe(1000);
    expect(nextHistoryRetryDelayMs(2)).toBe(2000);
  });
});

describe("useHistoryRetry（B-1 竞态兜底——502→200 序列）", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("502→200：首轮失败（502）二轮成功（200）——重试发生且成功即停", async () => {
    // mock fetch 序列（经 react-query refetch 代理面）：首次 502（reject）
    // /二次 200（resolve）——成功落定后 pending 翻 false（成功渲染态）。
    const outcomes: Array<"502" | "200"> = ["502", "200"];
    const refetch = vi.fn(() => {
      const outcome = outcomes[refetch.mock.calls.length - 1] ?? "200";
      return outcome === "502"
        ? Promise.reject(new Error("502 Bad Gateway"))
        : Promise.resolve({ isError: false });
    });
    const cleanup = mountRetry(true, refetch);
    await vi.advanceTimersByTimeAsync(499);
    expect(refetch).not.toHaveBeenCalled(); // 未到首梯——不重试
    await vi.advanceTimersByTimeAsync(1);
    expect(refetch).toHaveBeenCalledTimes(1); // 500ms 首梯重试（502 落定）
    await vi.advanceTimersByTimeAsync(1000);
    expect(refetch).toHaveBeenCalledTimes(2); // 1000ms 二梯（200 落定）
    cleanup(); // 成功渲染：条件解除（pending=false 装卸新 effect）
    mountRetry(false, refetch);
    await vi.advanceTimersByTimeAsync(60000);
    expect(refetch).toHaveBeenCalledTimes(2); // 成功即停——不再重试
  });

  it("耗尽即停：持续失败三梯后不再重试（耗尽态文案归 ChatPanel 两态渲染）", async () => {
    const refetch = vi.fn(() => Promise.reject(new Error("502 Bad Gateway")));
    mountRetry(true, refetch);
    await vi.advanceTimersByTimeAsync(500);
    expect(refetch).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1000);
    expect(refetch).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(2000);
    expect(refetch).toHaveBeenCalledTimes(3);
    await vi.advanceTimersByTimeAsync(120000);
    expect(refetch).toHaveBeenCalledTimes(HISTORY_RETRY_MAX); // 三梯耗尽——不无限静默
  });

  it("非刚建会话（pending=false）零重试——「中继不可达」态不走退避", async () => {
    const refetch = vi.fn(() => Promise.resolve({ isError: true }));
    mountRetry(false, refetch);
    await vi.advanceTimersByTimeAsync(60000);
    expect(refetch).not.toHaveBeenCalled();
  });
});
