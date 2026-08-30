/**
 * solutions 任务流纯函数测试：SSE 线格式解析/事件归约/快照归一/终态判定
 * （D2/D7 TDD）。
 *
 * 输入:  taskFeed 四纯函数族（node 环境——零 EventSource/DOM 依赖）
 * 输出:  纯函数契约断言（event:/data: 线格式→事件对象/事件序列归约
 *        TaskView/TaskStatus 快照→同形 TaskView 双源归一/终态判定）
 *
 * 规格说明（FE6 批 6b 段四，D2/D7；线格式=routers/events.py:53
 * `event: {type}\ndata: {json}\n\n`；Event 载荷五字段
 * {type,task_id,percent,message,condition_key}（manager.py:121-129））：
 *   - 状态事件 message=state 名（queued/running/cancelled/done/failed）；
 *     进度事件 message=stage（enumerate 面 load/run/rows）；
 *   - 终态任务连接即发一条快照 state 事件后收流（manager.py:296-298）
 *     ——deep-link 直进终态场景同一归约路径；
 *   - SSE 载荷无 error 字段（failed 详情走 TaskStatus 快照源——双源归一）；
 *   - 畸形 data JSON 拒（null——薄壳静默丢弃不崩流）。
 */
import { describe, expect, it } from "vitest";

import {
  isTerminalState,
  parseEventData,
  parseSseBlock,
  reduceTaskEvent,
  taskStatusToView,
  type TaskFeedEvent,
} from "./taskFeed";

/** 构造服务端线格式块（routers/events.py `_stream` 同构）。 */
function sseBlock(payload: Record<string, unknown>): string {
  return `event: ${String(payload["type"])}\ndata: ${JSON.stringify(payload)}\n\n`;
}

describe("parseSseBlock（event:/data: 线格式解析）", () => {
  it("progress 事件块 → 五字段事件对象（camelCase 归一）", () => {
    const event = parseSseBlock(
      sseBlock({
        type: "progress",
        task_id: "t-1",
        percent: 0.5,
        message: "run",
        condition_key: null,
      }),
    );
    expect(event).toEqual({
      type: "progress",
      taskId: "t-1",
      percent: 0.5,
      message: "run",
      conditionKey: null,
    });
  });

  it("state 事件块（终态快照形态）解析", () => {
    const event = parseSseBlock(
      sseBlock({ type: "state", task_id: "t-1", percent: 1, message: "done", condition_key: null }),
    );
    expect(event).toMatchObject({ type: "state", message: "done", percent: 1 });
  });

  it("data JSON 畸形 → null（拒不崩）", () => {
    expect(parseSseBlock("event: state\ndata: {not json}\n\n")).toBeNull();
  });

  it("data 非对象（数组/原始值）→ null", () => {
    expect(parseSseBlock('event: state\ndata: [1,2]\n\n')).toBeNull();
    expect(parseSseBlock('event: state\ndata: "done"\n\n')).toBeNull();
  });

  it("无 data 行 → null（空块/仅 event 行）", () => {
    expect(parseSseBlock("event: state\n\n")).toBeNull();
    expect(parseSseBlock("\n\n")).toBeNull();
  });

  it("载荷字段类型宽容归一（percent 非数→null；message 非 string→null）", () => {
    const event = parseSseBlock(
      'event: progress\ndata: {"type":"progress","task_id":"t-1","percent":"高","message":3}\n\n',
    );
    expect(event).toEqual({
      type: "progress",
      taskId: "t-1",
      percent: null,
      message: null,
      conditionKey: null,
    });
  });
});

describe("parseEventData（data 行直读——薄壳 e.data 面）", () => {
  it("JSON 串 → 事件对象（type 取载荷内 type）", () => {
    const event = parseEventData(
      '{"type":"state","task_id":"t-2","percent":0,"message":"queued","condition_key":null}',
    );
    expect(event).toEqual({
      type: "state",
      taskId: "t-2",
      percent: 0,
      message: "queued",
      conditionKey: null,
    });
  });

  it("畸形 JSON/非对象 → null", () => {
    expect(parseEventData("oops{")).toBeNull();
    expect(parseEventData("null")).toBeNull();
    expect(parseEventData("")).toBeNull();
  });
});

describe("reduceTaskEvent（事件序列归约 TaskView）", () => {
  it("无先前视图+state queued → 初始视图", () => {
    const view = reduceTaskEvent(null, {
      type: "state",
      taskId: "t-1",
      percent: 0,
      message: "queued",
      conditionKey: null,
    });
    expect(view).toEqual({ state: "queued", percent: 0, stage: "queued", error: null, stale: false });
  });

  it("progress 事件只推 percent/stage（state 不动）", () => {
    const base = reduceTaskEvent(null, {
      type: "state", taskId: "t", percent: 0, message: "running", conditionKey: null,
    });
    const view = reduceTaskEvent(base, {
      type: "progress", taskId: "t", percent: 0.5, message: "run", conditionKey: null,
    });
    expect(view).toEqual({ state: "running", percent: 0.5, stage: "run", error: null, stale: false });
  });

  it("state 事件更新 state+stage（快照 percent 保序）", () => {
    const base = reduceTaskEvent(null, {
      type: "progress", taskId: "t", percent: 0.5, message: "run", conditionKey: null,
    });
    const view = reduceTaskEvent(base, {
      type: "state", taskId: "t", percent: 0.75, message: "running", conditionKey: null,
    });
    expect(view).toEqual({ state: "running", percent: 0.75, stage: "running", error: null, stale: false });
  });

  it("stale 事件置 stale 标记（其余保留）", () => {
    const base = reduceTaskEvent(null, {
      type: "state", taskId: "t", percent: 1, message: "done", conditionKey: null,
    });
    const view = reduceTaskEvent(base, {
      type: "stale", taskId: "t", percent: 1, message: "stale", conditionKey: null,
    });
    expect(view).toEqual({ state: "done", percent: 1, stage: "done", error: null, stale: true });
  });

  it("终态 state 事件收口（done 后视图定格）", () => {
    const running = reduceTaskEvent(null, {
      type: "state", taskId: "t", percent: 0.5, message: "running", conditionKey: null,
    });
    const done = reduceTaskEvent(running, {
      type: "state", taskId: "t", percent: 1, message: "done", conditionKey: null,
    });
    expect(done).toEqual({ state: "done", percent: 1, stage: "done", error: null, stale: false });
  });

  it("未知事件类型 no-op（前视兼容）", () => {
    const base = reduceTaskEvent(null, {
      type: "state", taskId: "t", percent: 0, message: "running", conditionKey: null,
    });
    const unknown: TaskFeedEvent = {
      type: "future-kind", taskId: "t", percent: 9, message: "?", conditionKey: null,
    };
    expect(reduceTaskEvent(base, unknown)).toEqual(base);
    expect(reduceTaskEvent(null, unknown)).toBeNull();
  });

  it("SSE 载荷无 error 字段——failed 事件 error 仍 null（详情走快照源）", () => {
    const view = reduceTaskEvent(null, {
      type: "state", taskId: "t", percent: 0.5, message: "failed", conditionKey: null,
    });
    expect(view).toMatchObject({ state: "failed", error: null });
  });
});

describe("isTerminalState（终态判定）", () => {
  it("done/cancelled/failed 终态；queued/running/未知非终态", () => {
    expect(isTerminalState("done")).toBe(true);
    expect(isTerminalState("cancelled")).toBe(true);
    expect(isTerminalState("failed")).toBe(true);
    expect(isTerminalState("queued")).toBe(false);
    expect(isTerminalState("running")).toBe(false);
    expect(isTerminalState("pending")).toBe(false);
  });
});

describe("taskStatusToView（TaskStatus 快照→TaskView 双源归一）", () => {
  it("failed 快照：error 组合 error_type+error+error_code", () => {
    const view = taskStatusToView({
      task_id: "t-1",
      kind: "calc",
      state: "failed",
      progress: 0.5,
      stage: "run",
      condition_key: null,
      stale: false,
      error: "LoopDivergence: 迭代发散",
      error_type: "LoopDivergence",
      error_code: 422,
      result: null,
    });
    expect(view.state).toBe("failed");
    expect(view.percent).toBe(0.5);
    expect(view.stage).toBe("run");
    expect(view.error).toContain("LoopDivergence");
    expect(view.error).toContain("迭代发散");
    expect(view.error).toContain("422");
    expect(view.stale).toBe(false);
  });

  it("done 快照：error=null；progress/stage 直通", () => {
    const view = taskStatusToView({
      task_id: "t-2",
      kind: "enumerate",
      state: "done",
      progress: 1,
      stage: "rows",
      condition_key: null,
      stale: false,
      error: null,
      error_type: null,
      result: { feasible_count: 5 },
    });
    expect(view).toEqual({ state: "done", percent: 1, stage: "rows", error: null, stale: false });
  });

  it("弱字段宽容：state 非字符串→unknown；progress 非数→null", () => {
    const view = taskStatusToView({ state: 3, progress: "半", stage: null, stale: "yes" });
    expect(view.state).toBe("unknown");
    expect(view.percent).toBeNull();
    expect(view.stage).toBe("");
    expect(view.stale).toBe(false);
  });

  it("stale 快照面：stale=true 保留（提示性标记）", () => {
    const view = taskStatusToView({ state: "done", progress: 1, stage: "serialize", stale: true });
    expect(view.stale).toBe(true);
  });
});


// ═══ AUDIT2 FIX2 I-8：未测分支入册（容式门→null；探针 2026-08-30 已证） ═══
describe("AUDIT2 I-8 taskFeed 未测分支", () => {
  it("载荷缺 type → null", () => {
    expect(parseEventData('{"percent": 10}')).toBeNull();
  });
  it("percent=NaN → null（isFinite 面——字符串外补数形）", () => {
    expect(parseEventData('{"type":"progress","percent":NaN}')).toBeNull();
  });
});
