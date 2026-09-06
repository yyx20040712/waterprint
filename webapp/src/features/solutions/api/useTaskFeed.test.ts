/**
 * 任务流重连治理测试（B6 D3：退避梯/封顶/停连慢探测纯函数直测；B7 D3/D5
 * 增补：onConnection 三态回调通道+常量单源断言）。
 *
 * 输入:  useTaskFeed 导出的 nextReconnectDelayMs/planRecovery（时间逻辑
 *        纯函数面）+useTaskFeed hook 本体（B7 新面：React hooks 桩直驱
 *        ——useState/useRef/useEffect 经 vi.mock 替换为无渲染器可调形态，
 *        node 零 jsdom 红线内直调；EventSource 桩注入可控触发面）+
 *        shared/api/sseConstants 单源常量（B7 D5）
 * 输出:  指数梯 1s→30s 封顶+达限切 60s 慢探测断言+onConnection 三态
 *        （断连→reconnecting/达限→probing/重建 onopen→ok；首连接 open
 *        零噪音）+SSE_FAILURE_LIMIT=5 单源断言
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SSE_FAILURE_LIMIT } from "../../../shared/api/sseConstants";
import {
  nextReconnectDelayMs,
  planRecovery,
  useTaskFeed,
} from "./useTaskFeed";

// ---- B7 D3 三态回调通道：React hooks 桩（零渲染器直驱 effect）----
// useEffect 只收集待执行（挂载语义=测试内手动调用）；useState 写面 no-op
// （本用例不消费 view 态）；useRef 透真（onTerminal/onConnection ref 通道
// ——hook 渲染体赋 .current 即达）。
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
    useRef: <T>(initial: T) => ({ current: initial }),
    useState: <T>(initial: T | (() => T)) => [
      typeof initial === "function" ? (initial as () => T)() : initial,
      () => {}, // setState 写面 no-op（onConnection 用例不消费 view）
    ] as [T, (next: T) => void],
  };
});

/** EventSource 桩：实例登记+可控触发（triggerError/triggerOpen——B7 新惯例）。 */
class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  url: string;
  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }
  addEventListener() {} // 命名事件面（state/progress/stale）本用例不触发
  close() {
    this.closed = true;
  }
  triggerError() {
    this.onerror?.();
  }
  triggerOpen() {
    this.onopen?.();
  }
}

/** 当前（最新）连接实例（退避重建后取新桩直驱）。 */
function latestSource(): FakeEventSource {
  const latest = FakeEventSource.instances[FakeEventSource.instances.length - 1];
  if (latest === undefined) {
    throw new Error("无 EventSource 桩实例（连接未建立）");
  }
  return latest;
}

/** 直驱 hook：单次渲染态调用（hooks 桩）→立即执行收集到的 effect（挂载
 * 语义模拟）→返回 effect 清理器（卸载语义备用）。 */
function mountTaskFeed(
  onConnection?: (state: "reconnecting" | "probing" | "ok") => void,
): () => void {
  useTaskFeed("task-b7", undefined, onConnection);
  const effect = reactStub.effects[reactStub.effects.length - 1];
  if (effect === undefined) {
    throw new Error("未收集到 useTaskFeed effect（hooks 桩失效）");
  }
  reactStub.effects.length = 0;
  const cleanup = effect() as (() => void) | undefined;
  return cleanup ?? (() => {});
}

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

describe("SSE_FAILURE_LIMIT 单源（B7 D5 收敛）", () => {
  it("shared/api/sseConstants 值=5（useTaskFeed/useExportBatch 双源同值防漂移）", () => {
    expect(SSE_FAILURE_LIMIT).toBe(5);
  });
});

describe("useTaskFeed onConnection 三态回调（B7 D3——EventSource 桩直驱）", () => {
  beforeEach(() => {
    vi.useFakeTimers(); // 退避/慢探测 setTimeout 可控推进
    vi.stubGlobal("EventSource", FakeEventSource);
    FakeEventSource.instances = [];
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("断连→reconnecting（onerror 计数后退避重建）", () => {
    const onConnection = vi.fn();
    mountTaskFeed(onConnection);
    latestSource().triggerError();
    expect(onConnection).toHaveBeenCalledTimes(1);
    expect(onConnection).toHaveBeenCalledWith("reconnecting");
    // 退避 1s 后重建新连接（桩实例数 1→2）
    vi.advanceTimersByTime(1000);
    expect(FakeEventSource.instances).toHaveLength(2);
  });

  it("连续 5 次 error→probing（达上限切 60s 慢探测）", () => {
    const onConnection = vi.fn();
    mountTaskFeed(onConnection);
    for (const delayMs of [1000, 2000, 4000, 8000, 60000]) {
      latestSource().triggerError();
      vi.advanceTimersByTime(delayMs);
    }
    expect(onConnection).toHaveBeenCalledTimes(5);
    expect(onConnection).toHaveBeenNthCalledWith(1, "reconnecting");
    expect(onConnection).toHaveBeenNthCalledWith(4, "reconnecting");
    expect(onConnection).toHaveBeenNthCalledWith(5, "probing");
  });

  it("降级后重建 onopen→ok（failures>0 才发；首连接 open 零噪音）", () => {
    const onConnection = vi.fn();
    mountTaskFeed(onConnection);
    // 首连接 open：failures=0 不发回调（零噪音——ok=重建连接且此前降级）
    latestSource().triggerOpen();
    expect(onConnection).not.toHaveBeenCalled();
    // 4 连错（reconnecting 期）→第 5 错达限降级（probing）
    for (const delayMs of [1000, 2000, 4000, 8000]) {
      latestSource().triggerError();
      vi.advanceTimersByTime(delayMs);
    }
    latestSource().triggerError();
    expect(onConnection).toHaveBeenLastCalledWith("probing");
    // 60s 慢探测重建→onopen=ok（transport 级真信号——failures=5>0 达发）
    vi.advanceTimersByTime(60000);
    latestSource().triggerOpen();
    expect(onConnection).toHaveBeenLastCalledWith("ok");
    // failures 不因 ok 复位（归零仅事件到达——B7 D3 状态机零变更）：
    // 恢复后再断连仍按达限计数走 probing
    latestSource().triggerError();
    expect(onConnection).toHaveBeenLastCalledWith("probing");
  });
});
