/**
 * 首帧门测试（FE-4 批 2026-09-30——TDD 先红后绿：纯核直测+SSR 探针）。
 *
 * 输入:  FirstFrameGate（createFirstFrameGate 纯核[闭包状态单元] +
 *        useFirstFrameGate 薄适配[useSyncExternalStore] + FirstFrameOverlay/
 *        FirstFrameSignal 薄壳——渲染行为面薄壳不测沿 ViewerToolbar.test 先例，
 *        overlay 文案/role 属用户可见契约故入断言面）
 * 输出:  断言四组：①纯核 done 初值 false；②signal() 后翻 true；③幂等——
 *        重复 signal 仍 true 且订阅者恰通知一次（首帧回调每帧重入零副作用）；
 *        ④hook 适配 SSR 初值面（消费组件渲染 pending 分支）+overlay
 *        role="status" 文案在场
 *
 * 形态说明（沿 TaskPanel.test.tsx SSR 先例——零 jsdom 红线：状态迁移断言走
 *   纯核闭包（node 直测），React 面仅断言 SSR 初值渲染——renderToString
 *   丢弃 fiber 树，signal 后的重渲染不在本测试可达面（真实链路=Canvas
 *   useFrame 首帧回调→signal→Scene 重渲卸 overlay，门二无头探针实证）。
 */
import { readFileSync } from "node:fs";
import { renderToString } from "react-dom/server";
import { createElement } from "react";
import { describe, expect, it, vi } from "vitest";

import {
  createFirstFrameGate,
  FirstFrameOverlay,
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
