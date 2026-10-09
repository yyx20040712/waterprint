/**
 * 失焦连跳提交节流测试（B2 P3 V10——任务书 §二.⑦.5：ParamForm 失焦自动
 * 提交多任务连发代价——连发合并裁量〔leading 即发+trailing 合并尾发〕；
 * M1 缺省路径零消费=零行为变；node 直测 fake timers）。
 *
 * 输入:  createCommitThrottle（注入窗口 1500ms 缺省——vi fake timers 驱动
 *        Date.now/setTimeout）
 * 输出:  断言族：①静默窗首调即发（leading——零延迟提交）②窗内连发合并
 *        为一次尾发（trailing——最新 fire 载荷）③窗过再调=新 leading
 *        ④cancel=尾发消解 ⑤fire 后窗口重计（连续两轮各 1+1 发）
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createCommitThrottle } from "./commitThrottle";

beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
});

describe("createCommitThrottle（V10 连发合并）", () => {
  it("静默窗首调即发（leading——零延迟提交）", () => {
    const fire = vi.fn();
    const throttle = createCommitThrottle({ windowMs: 1500 });
    throttle.schedule(fire);
    expect(fire).toHaveBeenCalledTimes(1);
    throttle.cancel();
  });

  it("窗内连发合并为一次尾发（trailing——最新 fire 载荷）", () => {
    const first = vi.fn();
    const second = vi.fn();
    const third = vi.fn();
    const throttle = createCommitThrottle({ windowMs: 1500 });
    throttle.schedule(first); // leading 即发
    vi.advanceTimersByTime(300);
    throttle.schedule(second); // 窗内→挂尾
    vi.advanceTimersByTime(300);
    throttle.schedule(third); // 窗内再挂尾→覆盖（最新合并）
    expect(second).not.toHaveBeenCalled();
    expect(third).not.toHaveBeenCalled();
    vi.advanceTimersByTime(900); // 尾窗到点（距 leading 1500ms）
    expect(first).toHaveBeenCalledTimes(1);
    expect(second).toHaveBeenCalledTimes(0); // 被最新合并（丢弃中间载荷）
    expect(third).toHaveBeenCalledTimes(1);
    throttle.cancel();
  });

  it("窗过再调=新 leading（每窗至多 leading+trailing 两发）", () => {
    const fire = vi.fn();
    const throttle = createCommitThrottle({ windowMs: 1500 });
    throttle.schedule(fire);
    vi.advanceTimersByTime(1600); // 窗过
    throttle.schedule(fire);
    expect(fire).toHaveBeenCalledTimes(2);
    throttle.cancel();
  });

  it("cancel=尾发消解（挂尾未发即取消→零尾发）", () => {
    const fire = vi.fn();
    const throttle = createCommitThrottle({ windowMs: 1500 });
    throttle.schedule(fire);
    vi.advanceTimersByTime(100);
    throttle.schedule(fire); // 挂尾
    throttle.cancel();
    vi.advanceTimersByTime(2000);
    expect(fire).toHaveBeenCalledTimes(1); // 仅 leading
  });

  it("fire 后窗口重计（尾发后满窗再调=新 leading；新窗尾发如常）", () => {
    const fire = vi.fn();
    const throttle = createCommitThrottle({ windowMs: 1500 });
    throttle.schedule(fire); // t=0 第一轮 leading（call 1）
    vi.advanceTimersByTime(500);
    throttle.schedule(fire); // t=500 挂尾
    vi.advanceTimersByTime(1000); // t=1500 第一轮尾发（call 2）——窗口自尾发重计
    expect(fire).toHaveBeenCalledTimes(2);
    vi.advanceTimersByTime(1600); // t=3100（距尾发 1600≥窗——静默）
    throttle.schedule(fire); // 第二轮 leading（call 3）
    vi.advanceTimersByTime(700);
    throttle.schedule(fire); // t=3800 窗内挂尾（3800−3100=700<1500）
    vi.advanceTimersByTime(800); // t=4600 第二轮尾发（call 4）
    expect(fire).toHaveBeenCalledTimes(4);
    throttle.cancel();
  });
});
