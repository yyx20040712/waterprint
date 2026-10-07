/**
 * @vitest-environment jsdom
 *
 * AI 席位容器测试（M7 批 2026-10-07——三分页 对话｜任务｜回执：受控
 * Segmented+mount-on-first-activation+display 保持+席位初值解析+连接徽标
 * +ChatSeat 承袭烟囱）。
 *
 * 输入:  AiSeat/ChatSeat（URL 经 history.replaceState 摆位——真
 *        seatInitialPage 消费；vi.mock 边界沿 paneDomainGate 纪律=feature
 *        api 模块面〔aiconnect/ai_chat api/useTaskFeed/useOpsChainQuery〕+
 *        generated 面无害空数据，禁 mock react-query 内部/antd；
 *        QueryClientProvider 每用例新 client retry:false）
 * 输出:  断言组：①三页签在场+头行标题；②缺省初始页 chat；③?task=/?
 *        enum= 深链→task；④?tab=opsdebug→task（兼容层一次性切席位任务
 *        分页）；⑤?tab=canvas→chat（非 opsdebug 不误切）；⑥双深链并存
 *        同归 task；⑦mount-on-first-activation+display 切换保持；⑧
 *        TASK_EVENT 运行期不自动切页（边缘 a「席位不自动切」）；⑨连接
 *        徽标两态+onOpenAiConnect 透传；⑩ChatSeat 直渲烟囱（ChatPanel
 *        零改挂载——mock 边界=useAiChat api 模块面）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AiSeat } from "./aiSeat";
import { ChatSeat } from "../features/ai_chat/components/ChatSeat";
import { TASK_EVENT } from "../shared/events";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面）：
// antd 浮层（Select 下拉等）挂载期消费 ResizeObserver；ChatPanel 底部锚
// 滚动 effect 消费 Element.scrollIntoView（jsdom 两 API 均缺席）。
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
if (typeof Element.prototype.scrollIntoView !== "function") {
  Element.prototype.scrollIntoView = () => {};
}

/** 受控态位（vi.hoisted——各 mock 工厂闭包同源读写；react-query v5 常读
 *  字段族沿 paneDomainGate D4 口径补齐：pending 语义=data undefined）。 */
const gate = vi.hoisted(() => {
  const idle = () => ({
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
    isPending: true,
    isLoading: true,
    isFetching: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  });
  return {
    conn: { data: undefined as { ready: boolean } | undefined },
    sessions: idle(),
    history: idle(),
    send: { mutate: vi.fn(), isPending: false, isLoading: false },
    taskFeedTaskIds: [] as (string | null)[],
    opsChain: idle(),
  };
});

vi.mock("../features/aiconnect/api/useAiConnection", () => ({
  useAiConnection: (_enabled: boolean) => ({
    statusQuery: { data: gate.conn.data, isError: false, error: null },
  }),
}));
vi.mock("../features/ai_chat/api/useAiChat", () => ({
  CHAT_HISTORY_KEY: (id: string) => ["/api/ai/sessions", id, "messages"],
  useChatSessions: () => gate.sessions,
  useChatHistory: () => gate.history,
  useSendChatMessage: () => gate.send,
}));
vi.mock("../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: (taskId: string | null) => {
    gate.taskFeedTaskIds.push(taskId);
    return null;
  },
}));
vi.mock("../features/opsdebug/api/useOpsChainQuery", () => ({
  useOpsChainQuery: () => gate.opsChain,
}));
vi.mock("../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => ({
    data: undefined,
    isError: false,
    error: null,
    isPending: true,
    isLoading: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  }),
  useCancelTaskApiCalcTasksTaskIdCancelPost: () => ({
    mutate: () => {},
    isPending: false,
  }),
}));
vi.mock("../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({
    data: undefined,
    isError: false,
    error: null,
    isPending: true,
    isLoading: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  }),
}));

/** URL 摆位+每用例新 QueryClient（retry:false——paneDomainGate 同款）。 */
function renderSeat(search: string, onOpenAiConnect: () => void = () => {}) {
  window.history.replaceState(null, "", search === "" ? "/" : `/?${search}`);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<AiSeat onOpenAiConnect={onOpenAiConnect} />, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  });
}

beforeEach(() => {
  gate.conn.data = undefined;
  gate.taskFeedTaskIds.length = 0;
  window.history.replaceState(null, "", "/");
});
afterEach(cleanup);

describe("席位三分页结构（D1——受控 Segmented+mount-on-first-activation）", () => {
  it("三页签在场+头行标题「AI 席位」+根 wp-seat 在场", () => {
    renderSeat("");
    expect(screen.getByTestId("wp-seat")).toBeTruthy();
    expect(screen.getByText("AI 席位")).toBeTruthy();
    for (const label of ["对话", "任务", "回执"]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
  });

  it("缺省初始页=chat：ChatPanel 承载在场+任务页未挂载", () => {
    renderSeat("");
    expect(screen.getByTestId("wp-chat-session-select")).toBeTruthy();
    expect(screen.queryByTestId("wp-seat-task")).toBeNull();
    expect(screen.queryByTestId("wp-seat-receipts")).toBeNull();
  });

  it("?task= 深链→初始页 task（边缘 c 席位聚焦——任务页在场/对话页未挂载）", () => {
    renderSeat("task=t1");
    expect(screen.getByTestId("wp-seat-task")).toBeTruthy();
    expect(screen.queryByTestId("wp-chat-session-select")).toBeNull();
  });

  it("?enum= 深链→初始页 task（enum 对称口径）", () => {
    renderSeat("enum=e1");
    expect(screen.getByTestId("wp-seat-task")).toBeTruthy();
  });

  it("?tab=opsdebug→初始页 task（兼容层一次性切席位任务分页——§B 副作用列）", () => {
    renderSeat("tab=opsdebug");
    expect(screen.getByTestId("wp-seat-task")).toBeTruthy();
    expect(screen.queryByTestId("wp-chat-session-select")).toBeNull();
  });

  it("?tab=canvas（非 opsdebug 合法槽）→初始页 chat（缺省分支不误切）", () => {
    renderSeat("tab=canvas");
    expect(screen.getByTestId("wp-chat-session-select")).toBeTruthy();
    expect(screen.queryByTestId("wp-seat-task")).toBeNull();
  });

  it("双条件并存（?task=+?tab=opsdebug）同归 task（优先序①>②）", () => {
    renderSeat("task=t9&tab=opsdebug");
    expect(screen.getByTestId("wp-seat-task")).toBeTruthy();
  });

  it("mount-on-first-activation+display 保持：切任务→挂载；切回对话→已挂载任务页不卸载（display:none）", () => {
    const onOpen = vi.fn();
    const view = renderSeat("", onOpen);
    expect(screen.queryByTestId("wp-seat-task")).toBeNull();
    // 到访任务页→首激活挂载
    fireEvent.click(screen.getByText("任务"));
    expect(screen.getByTestId("wp-seat-task")).toBeTruthy();
    // 切回对话：已挂载任务页 display:none 保持在场（任务轨状态不丢——
    // display 在 aiSeat 页包裹层上，testid 为页体根）
    fireEvent.click(screen.getByText("对话"));
    const taskPane = screen.getByTestId("wp-seat-task");
    expect(taskPane.parentElement?.style.display).toBe("none");
    expect(screen.getByTestId("wp-chat-session-select")).toBeTruthy();
    expect(view.container).toBeTruthy();
  });
});

describe("席位不自动切页（边缘 a 限定语——TASK_EVENT 运行期）", () => {
  it("对话在场→写 ?task=+派发 TASK_EVENT→仍对话（任务页不自动挂载/切换）", () => {
    renderSeat("");
    expect(screen.getByTestId("wp-chat-session-select")).toBeTruthy();
    window.history.replaceState(null, "", "/?task=t-late");
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t-late" }));
    expect(screen.getByTestId("wp-chat-session-select")).toBeTruthy();
    expect(screen.queryByTestId("wp-seat-task")).toBeNull();
  });
});

describe("连接徽标（D1 判据：ready 聚合布尔——诚实降级）", () => {
  it("ready=true→「已接入」；徽标点击→onOpenAiConnect 透传", () => {
    gate.conn.data = { ready: true };
    const onOpen = vi.fn();
    renderSeat("", onOpen);
    expect(screen.getByTestId("wp-seat-conn").textContent).toContain("已接入");
    fireEvent.click(screen.getByTestId("wp-seat-conn"));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("ready 非 true（loading/失败/data 缺席）→「未接入」诚实降级", () => {
    gate.conn.data = undefined;
    renderSeat("");
    expect(screen.getByTestId("wp-seat-conn").textContent).toContain("未接入");
  });

  it("ready=false→「未接入」（显式 false 不猜因）", () => {
    gate.conn.data = { ready: false };
    renderSeat("");
    expect(screen.getByTestId("wp-seat-conn").textContent).toContain("未接入");
  });
});

describe("ChatSeat 承袭烟囱（ChatPanel 零改挂载——Drawer 壳退役后 props 注入成立）", () => {
  it("ChatSeat 直渲：会话选择+消息输入在场（mock 边界=useAiChat api 模块面）", () => {
    window.history.replaceState(null, "", "/");
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(<ChatSeat />, {
      wrapper: ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      ),
    });
    expect(screen.getByTestId("wp-chat-session-select")).toBeTruthy();
    expect(screen.getByTestId("wp-chat-input")).toBeTruthy();
  });
});
