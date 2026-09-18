/**
 * 任务 SSE 生命周期内核测试（B3-b：useTaskFeed/useExportBatch 双实现
 * 收敛至 shared 单源后的内核面——命令面协议直测+长订阅 hook 经 React
 * 桩直驱；重连纯函数族经 useTaskFeed.test 再导出面覆盖，此处不重复）。
 *
 * 输入:  subscribeTaskEvents（EventSource 桩注入可控触发——命名事件
 *        data 递送/终态 close/onOpen·onError 透传/close 句柄幂等）+
 *        useTaskEventSource hook 本体（React hooks 桩零渲染器直驱——
 *        useTaskFeed.test 同款惯例）
 * 输出:  命令面五断言（三命名事件 data 直递 interpret/畸形丢弃归消费方
 *        /terminal 即 close+onTerminal/onerror 不自动 close/close 幂等）
 *        +hook 两断言（taskId null 零建连/解读协议 drop 不计健康——
 *        drop 后 onerror 计数含此前 drop 期）
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  type TaskEventReading,
  subscribeTaskEvents,
  useTaskEventSource,
} from "./useTaskEventSource";

// ---- 命令面：EventSource 桩（实例登记+命名事件可控触发）----
class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  url: string;
  listeners = new Map<string, EventListener[]>();
  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }
  addEventListener(name: string, listener: EventListener) {
    const list = this.listeners.get(name) ?? [];
    list.push(listener);
    this.listeners.set(name, list);
  }
  close() {
    this.closed = true;
  }
  /** 命名事件触发（data 递送——state/progress/stale 三面）。 */
  emit(name: string, data: string) {
    for (const listener of this.listeners.get(name) ?? []) {
      listener({ data } as MessageEvent);
    }
  }
  triggerOpen() {
    this.onopen?.();
  }
  triggerError() {
    this.onerror?.();
  }
}

function latestSource(): FakeEventSource {
  const latest = FakeEventSource.instances[FakeEventSource.instances.length - 1];
  if (latest === undefined) {
    throw new Error("无 EventSource 桩实例（连接未建立）");
  }
  return latest;
}

// ---- hook 面：React hooks 桩（零渲染器直驱 effect——useTaskFeed.test 惯例）----
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
  };
});

/** 直驱 hook：单次渲染态调用→立即执行收集到的 effect→返回清理器。 */
function mountSource(
  taskId: string | null,
  interpret: (data: string) => TaskEventReading,
  onConnection?: (state: "reconnecting" | "probing" | "ok") => void,
): () => void {
  useTaskEventSource(taskId, interpret, undefined, onConnection);
  const effect = reactStub.effects[reactStub.effects.length - 1];
  if (effect === undefined) {
    throw new Error("未收集到 useTaskEventSource effect（hooks 桩失效）");
  }
  reactStub.effects.length = 0;
  const cleanup = effect() as (() => void) | undefined;
  return cleanup ?? (() => {});
}

describe("subscribeTaskEvents 命令面（B3-b 内核——awaitTerminal 消费形态）", () => {
  beforeEach(() => {
    vi.stubGlobal("EventSource", FakeEventSource);
    FakeEventSource.instances = [];
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("三命名事件（state/progress/stale）data 直递 interpret——解析归消费方", () => {
    const seen: string[] = [];
    subscribeTaskEvents("task-k", { interpret: (data) => {
      seen.push(data);
      return { kind: "event" };
    } });
    const source = latestSource();
    source.emit("state", "{\"type\":\"state\"}");
    source.emit("progress", "{\"type\":\"progress\"}");
    source.emit("stale", "{}");
    expect(seen).toEqual(["{\"type\":\"state\"}", "{\"type\":\"progress\"}", "{}"]);
    expect(source.closed).toBe(false); // 非终态不 close（浏览器自动重连保留）
  });

  it("terminal 即 close 本流+转 onTerminal（阻断服务端终态关流自动重连）", () => {
    const onTerminal = vi.fn();
    subscribeTaskEvents("task-k", {
      interpret: (data) => ({ kind: "terminal", state: data }),
      onTerminal,
    });
    const source = latestSource();
    source.emit("state", "done");
    expect(source.closed).toBe(true);
    expect(onTerminal).toHaveBeenCalledTimes(1);
    expect(onTerminal).toHaveBeenCalledWith("done");
  });

  it("onerror 不自动 close（一次性等待语义——治理归消费方经句柄表达）", () => {
    const onError = vi.fn();
    const sub = subscribeTaskEvents("task-k", {
      interpret: () => ({ kind: "event" }),
      onError,
    });
    latestSource().triggerError();
    expect(onError).toHaveBeenCalledTimes(1);
    expect(latestSource().closed).toBe(false);
    sub.close(); // 消费方达限自收束
    expect(latestSource().closed).toBe(true);
  });

  it("onopen 透传（transport 级信号——降级恢复口径归消费方）", () => {
    const onOpen = vi.fn();
    subscribeTaskEvents("task-k", {
      interpret: () => ({ kind: "event" }),
      onOpen,
    });
    latestSource().triggerOpen();
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("close 句柄幂等（重复收束无害——取代守卫/超时双触发面）", () => {
    const sub = subscribeTaskEvents("task-k", { interpret: () => ({ kind: "event" }) });
    sub.close();
    sub.close();
    expect(latestSource().closed).toBe(true);
  });
});

describe("useTaskEventSource 长订阅 hook（B3-b 内核——useTaskFeed 消费形态）", () => {
  beforeEach(() => {
    vi.stubGlobal("EventSource", FakeEventSource);
    FakeEventSource.instances = [];
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("taskId=null 零建连（URL ?task= 消费——null 不建连）", () => {
    mountSource(null, () => ({ kind: "event" }));
    expect(FakeEventSource.instances).toHaveLength(0);
  });

  it("drop 不计链路健康（畸形不证恢复——B6 D3 长订阅口径）", () => {
    vi.useFakeTimers();
    const onConnection = vi.fn();
    mountSource("task-k", () => ({ kind: "drop" }), onConnection);
    const source = latestSource();
    source.emit("progress", "not-json");
    source.triggerError(); // drop 后计数仍 1——reconnecting（非 ok）
    expect(onConnection).toHaveBeenCalledTimes(1);
    expect(onConnection).toHaveBeenCalledWith("reconnecting");
    vi.advanceTimersByTime(1000); // 退避 1s 重建
    expect(FakeEventSource.instances).toHaveLength(2);
    // 重建后健康事件到达→计数归零（下轮 open 降级恢复才发 ok）
    latestSource().emit("state", "{\"type\":\"state\"}");
    latestSource().triggerError();
    expect(onConnection).toHaveBeenLastCalledWith("reconnecting");
    vi.advanceTimersByTime(2000);
    latestSource().triggerOpen(); // failures>0 → ok
    expect(onConnection).toHaveBeenLastCalledWith("ok");
  });

  it("卸载清理：连接+退避定时器双收口（disposed 守卫不复活）", () => {
    vi.useFakeTimers();
    const cleanup = mountSource("task-k", () => ({ kind: "event" }));
    const source = latestSource();
    source.triggerError(); // 退避排程
    cleanup(); // 卸载
    expect(source.closed).toBe(true);
    vi.advanceTimersByTime(60000); // 任意推进——不复活
    expect(FakeEventSource.instances).toHaveLength(1);
  });
});
