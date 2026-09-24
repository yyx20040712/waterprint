/**
 * 聊天任务事件解读测试（B4-4b 门二 P0——字段协议断言：message 承载 state/stage）。
 *
 * 输入:  SSE data 样本（state 终态/progress 阶段/畸形行）
 * 输出:  三态解读+stageSink 副作用断言（门二复算 8 的回归锚——禁再读 state/stage 键）
 */

import { describe, expect, it, vi } from "vitest";

import { interpretChatEvent } from "./chatEvent";

describe("interpretChatEvent（B4-4b 门二 P0 回归锚）", () => {
  it("state 终态：message 字段承载状态名→terminal（禁读 parsed.state）", () => {
    expect(interpretChatEvent('{"type":"state","task_id":"t1","percent":1,"message":"done","condition_key":null}', vi.fn())).toEqual({
      kind: "terminal",
      state: "done",
    });
    expect(interpretChatEvent('{"type":"state","percent":1,"message":"failed"}', vi.fn())).toEqual({
      kind: "terminal",
      state: "failed",
    });
  });

  it("progress 阶段：message 字段承载阶段文案→sink 副作用（禁读 parsed.stage）", () => {
    const sink = vi.fn();
    const reading = interpretChatEvent(
      '{"type":"progress","task_id":"t1","percent":0.5,"message":"调用工具 wp_run_calc","condition_key":null}',
      sink,
    );
    expect(reading).toEqual({ kind: "event" });
    expect(sink).toHaveBeenCalledWith("调用工具 wp_run_calc");
  });

  it("非终态 state（running）与 stale：event 态不触发 terminal", () => {
    expect(interpretChatEvent('{"type":"state","message":"running"}', vi.fn())).toEqual({ kind: "event" });
    expect(interpretChatEvent('{"type":"stale","message":"stale"}', vi.fn())).toEqual({ kind: "event" });
  });

  it("畸形行：drop（不计链路健康）", () => {
    expect(interpretChatEvent("not-json", vi.fn())).toEqual({ kind: "drop" });
  });

  it("旧字段形态（state/stage 键——门二 P0 缺陷形态）恒不命中 terminal：回归防倒退", () => {
    const sink = vi.fn();
    // 即使上游某日改发 stage 键，本解读也不得静默挂死——保持 event 态
    expect(interpretChatEvent('{"type":"state","stage":"done"}', sink)).toEqual({ kind: "event" });
    expect(sink).not.toHaveBeenCalled();
  });
});
