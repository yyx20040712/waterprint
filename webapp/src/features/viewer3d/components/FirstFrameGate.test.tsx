/**
 * 首帧门测试（FE-4 批 2026-09-30——TDD 先红后绿：纯核直测+SSR 探针；
 * 2A4 批 2026-10-05 UF-56 增超时降级组）。
 *
 * 输入:  FirstFrameGate（createFirstFrameGate 纯核[闭包状态单元，UF-56 增
 *        isTimedOut/armTimeout/disarmTimeout 三键] + useFirstFrameGate 薄适配
 *        [useSyncExternalStore——返回 [done, timedOut, signal] 三元] +
 *        FirstFrameOverlay/FirstFrameTimeoutPanel/FirstFrameSignal 薄壳——
 *        渲染行为面薄壳不测沿 ViewerToolbar.test 先例，overlay/timeout 面
 *        文案与 role 属用户可见契约故入断言面）
 * 输出:  断言两组：①FE-4 既有面——纯核 done 初值/signal 翻转/幂等恰通知
 *        一次+hook 适配 SSR 初值+overlay role="status" 文案+resetKey 复位
 *        三例；②UF-56 超时降级组（fake timers 轨——vi.useFakeTimers 纯核
 *        域逐 describe 还原）——超时恰通知一次幂等/signal 先到清窗/
 *        timedOut 后 signal 状态诚实/disarm+重 arm 窗重起/done 后 arm
 *        no-op+超时面板 SSR 文案+Scene 消费源文断言
 *
 * 形态说明（沿 TaskPanel.test.tsx SSR 先例——零 jsdom 红线：状态迁移断言走
 *   纯核闭包（node 直测），React 面仅断言 SSR 初值渲染——renderToString
 *   丢弃 fiber 树，signal 后的重渲染不在本测试可达面（真实链路=Canvas
 *   useFrame 首帧回调→signal→Scene 重渲卸 overlay，门二无头探针实证））。
 */
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { createElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createFirstFrameGate,
  FirstFrameOverlay,
  FirstFrameTimeoutPanel,
  FIRST_FRAME_TIMEOUT_MS,
  useFirstFrameGate,
} from "./FirstFrameGate";

/** hook 消费探针（SSR 初值面——done 文案二态直读）。 */
function GateProbe() {
  const [done] = useFirstFrameGate();
  return createElement("div", null, done ? "gate-done" : "gate-pending");
}

/** resetKey 探针（R1 F1——带 key 渲染初值面：新签名接线运行面）。 */
function GateResetProbe({ resetKey }: { resetKey: string }) {
  const [done] = useFirstFrameGate(resetKey);
  return createElement("div", null, done ? "gate-done" : "gate-pending");
}

describe("FirstFrameGate（三维首帧门）", () => {
  it("纯核：done 初值 false（挂载即 pending——overlay 在场前提）", () => {
    expect(createFirstFrameGate().isDone()).toBe(false);
  });

  it("纯核：signal() 后翻 true（首帧回调收口）", () => {
    const cell = createFirstFrameGate();
    cell.signal();
    expect(cell.isDone()).toBe(true);
  });

  it("幂等：重复 signal 仍 true 且订阅者恰通知一次（useFrame 每帧重入安全）", () => {
    const cell = createFirstFrameGate();
    const listener = vi.fn();
    cell.subscribe(listener);
    cell.signal();
    cell.signal();
    cell.signal();
    expect(cell.isDone()).toBe(true);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("hook 适配：SSR 初值渲染 pending 分支（useFirstFrameGate 消费面）", () => {
    expect(renderToString(createElement(GateProbe))).toContain("gate-pending");
  });

  it("overlay：role=status 与「正在构建三维场景…」文案在场（用户可见契约）", () => {
    const html = renderToString(createElement(FirstFrameOverlay));
    expect(html).toContain("正在构建三维场景");
    expect(html).toContain('role="status"');
  });

  it("复位面（R1 F1）：resetKey 接线在场——useMemo deps=[resetKey]（源文断言沿 domainColorAxis.test 读源先例：切 key 重建 cell、done 归 false）", () => {
    const source = readFileSync(new URL("./FirstFrameGate.tsx", import.meta.url), "utf-8");
    expect(source).toContain("useMemo(createFirstFrameGate, [resetKey])");
  });

  it("复位面（R1 F1）：纯核双实例独立——A 首帧收口不串 B（resetKey 重建语义的纯核面）", () => {
    const a = createFirstFrameGate();
    const b = createFirstFrameGate();
    const listenerA = vi.fn();
    a.subscribe(listenerA);
    a.signal();
    expect(b.isDone()).toBe(false); // B 独立未翻
    expect(listenerA).toHaveBeenCalledTimes(1);
  });

  it("复位面（R1 F1）：hook 带 resetKey 渲染 pending（新签名接线运行面）", () => {
    expect(
      renderToString(createElement(GateResetProbe, { resetKey: "proj-a" })),
    ).toContain("gate-pending");
  });

  it("复位面（R2 F1'/B1）：Scene 消费处 FirstFrameSignal 挂 key={projectId}——缓存命中路径 Canvas 不重挂时 fired ref 随重挂归零（源文断言——行为级覆盖归门二探针 D 项硬断言）", () => {
    const scene = readFileSync(new URL("./Scene.tsx", import.meta.url), "utf-8");
    expect(scene).toContain("<FirstFrameSignal onFirstFrame={firstFrameSignal} key={projectId} />");
  });
});

describe("首帧门超时降级（UF-56——2A4 批 2026-10-05）", () => {
  // fake timers 轨：窗口语义纯核域直测（逐 describe 还原——零真实计时器泄漏）
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("常量锚：FIRST_FRAME_TIMEOUT_MS=10_000（探针基线 overlay 寿命 363~439ms——20×+ 余量，值单点可调）", () => {
    expect(FIRST_FRAME_TIMEOUT_MS).toBe(10_000);
  });

  it("纯核：armTimeout 到点翻 timedOut 且订阅者恰通知一次；再 advance 零再通知（幂等——signal 对偶结构）", () => {
    const cell = createFirstFrameGate();
    const listener = vi.fn();
    cell.subscribe(listener);
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    expect(cell.isTimedOut()).toBe(true);
    expect(listener).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    expect(listener).toHaveBeenCalledTimes(1); // 幂等旗标——恰通知一次
  });

  it("纯核：signal 先到=清窗——advance 满程 timedOut 不翻（首帧先到=取消降级）", () => {
    const cell = createFirstFrameGate();
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    cell.signal();
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    expect(cell.isDone()).toBe(true);
    expect(cell.isTimedOut()).toBe(false);
  });

  it("纯核：timedOut 后 signal 到达=done 仍翻 true（cell 状态诚实独立——消费面 Scene timedOut 先判属优先级分工非 cell 抑制）", () => {
    const cell = createFirstFrameGate();
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    cell.signal();
    expect(cell.isDone()).toBe(true);
    expect(cell.isTimedOut()).toBe(true);
  });

  it("纯核：disarmTimeout 清窗不翻；重 arm=窗重起（半程+重 arm+半程→未翻，再半程→翻——重挂/StrictMode 双 effect 幂等安全）", () => {
    const cell = createFirstFrameGate();
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    cell.disarmTimeout();
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    expect(cell.isTimedOut()).toBe(false); // disarm 后清窗不翻
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS / 2);
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS); // 重挂窗=clearTimeout+set 新窗
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS / 2);
    expect(cell.isTimedOut()).toBe(false); // 新窗仅过半程
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS / 2);
    expect(cell.isTimedOut()).toBe(true); // 新窗满程翻
  });

  it("纯核：done=true 后 armTimeout=no-op（advance 不翻——首帧已收口零降级面）", () => {
    const cell = createFirstFrameGate();
    cell.signal();
    cell.armTimeout(FIRST_FRAME_TIMEOUT_MS);
    vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    expect(cell.isTimedOut()).toBe(false);
  });

  it("超时面板：role=alert 与「三维渲染初始化未在 10 秒内完成」文案+重试钮在场（SSR 面——用户可见契约）", () => {
    const html = renderToString(
      createElement(FirstFrameTimeoutPanel, { onRetry: () => {} }),
    );
    expect(html).toContain("三维渲染初始化未在 10 秒内完成");
    expect(html).toContain("设备可能不支持 WebGL 或资源紧张");
    expect(html).toContain('role="alert"');
    expect(html).toContain("重试");
  });

  it("源文断言：Scene 消费 firstFrameTimedOut 先判（面板替代 Canvas 块）+复合 resetKey `${projectId}#${attempt}`（attempt 尾段=重试复位链）", () => {
    const scene = readFileSync(new URL("./Scene.tsx", import.meta.url), "utf-8");
    expect(scene).toContain("firstFrameTimedOut");
    expect(scene).toContain("<FirstFrameTimeoutPanel onRetry={() => setAttempt((a) => a + 1)} />");
    expect(scene).toContain("`${projectId}#${attempt}`");
  });
});
