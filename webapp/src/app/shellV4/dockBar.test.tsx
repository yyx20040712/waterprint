/**
 * @vitest-environment jsdom
 *
 * v4 底栏双区测试（B2 结果与方案批——完成直达〔§一.4 done 任务行→分析表
 * 直达+相关单元选中〕+failed 错误提示面+dock-ai 会话续接〔P3 d1-N7——
 * zone 切换卸载/重挂与刷新两径 sessionId 持久恢复〕）。
 *
 * 输入:  DockBar（任务态/SSE/会话三 hook 模块替身）+done/failed 任务夹具
 * 输出:  断言族：①done 任务行点击→onTaskNavigate({state:"done",unitId})
 *        〔unitId=枚举任务 result.unit_id 透传〕②done 且无 unit_id=null
 *        透传 ③failed=错误提示行在场（白名单）④会话续接：发送建档后
 *        sessionStorage 持久→重挂恢复同 sessionId
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DockBar } from "./dockBar";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  task: {
    data: {
      task_id: "t-done-1",
      kind: "enumerate",
      state: "done",
      progress: 1.0,
      stage: "rows",
      condition_key: null,
      stale: false,
      error: null,
      error_type: null,
      result: { unit_id: "municipal_aao" } as Record<string, unknown>,
      project_id: "p1",
    },
    isError: false,
    error: null,
  },
  feed: null as { state: string; percent: number | null; stage: string; error: string | null; stale: boolean } | null,
  chatHistory: { data: undefined, isError: false, error: null },
  chatHistoryLastSession: null as string | null,
  send: { mutate: vi.fn(), isPending: false },
  navigate: vi.fn(),
}));

vi.mock("../../features/ai_chat/api/useAiChat", () => ({
  useChatHistory: (sessionId: string | null) => {
    gate.chatHistoryLastSession = sessionId;
    return gate.chatHistory;
  },
  useSendChatMessage: () => gate.send,
}));
vi.mock("../../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: () => gate.feed,
}));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => gate.task,
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderDock() {
  window.history.replaceState(null, "", "/?task=t-done-1&ia=v4");
  return render(
    <QueryClientProvider client={queryClient}>
      <DockBar onTaskNavigate={gate.navigate} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.navigate.mockClear();
  gate.send.mutate.mockClear();
  gate.feed = null;
  window.sessionStorage.clear();
});
afterEach(cleanup);

describe("完成直达（§一.4）", () => {
  it("done 任务行点击→onTaskNavigate({state:'done', unitId=枚举 result 透传})", () => {
    const { container } = renderDock();
    const row = container.querySelector<HTMLDivElement>(
      '[data-testid="wp-v4-task-row"]',
    );
    expect(row).not.toBeNull();
    row?.click();
    expect(gate.navigate).toHaveBeenCalledWith({
      state: "done",
      unitId: "municipal_aao",
    });
  });

  it("done 且 result 无 unit_id→unitId=null 透传（calc 任务——切分析表不选单元）", () => {
    gate.task = {
      ...gate.task,
      data: {
        ...gate.task.data!,
        kind: "calc",
        result: { design_hash: "h1" },
      },
    };
    try {
      const { container } = renderDock();
      container.querySelector<HTMLDivElement>('[data-testid="wp-v4-task-row"]')?.click();
      expect(gate.navigate).toHaveBeenCalledWith({ state: "done", unitId: null });
    } finally {
      gate.task = {
        ...gate.task,
        data: {
          ...gate.task.data!,
          kind: "enumerate",
          result: { unit_id: "municipal_aao" },
        },
      };
    }
  });
});

describe("failed 错误提示面（白名单）", () => {
  it("failed=错误行在场（快照 error 透出——错误提示白名单）", () => {
    gate.feed = {
      state: "failed",
      percent: null,
      stage: "failed",
      error: "收敛失败：LoopDivergence",
      stale: false,
    };
    const { container } = renderDock();
    const face = container.querySelector('[data-testid="wp-v4-task-error"]');
    expect(face).not.toBeNull();
    expect(face?.textContent).toContain("收敛失败");
  });
});

describe("dock-ai 会话续接（P3 d1-N7）", () => {
  it("发送建档 sessionId→sessionStorage 持久→重挂恢复同会话", () => {
    const first = renderDock();
    const input = first.container.querySelector<HTMLInputElement>(
      'input[data-testid="wp-v4-ai-input"]',
    );
    expect(input).not.toBeNull();
    if (input !== null) {
      fireEvent.change(input, { target: { value: "把污泥龄提到 14" } });
    }
    first.container
      .querySelector<HTMLButtonElement>('button[data-testid="wp-v4-ai-send"]')
      ?.click();
    // 发言建档：mutate 载荷携 sessionId+消息
    const call = gate.send.mutate.mock.calls[0];
    expect(call?.[0]?.message).toContain("污泥龄");
    const sessionId = call?.[0]?.sessionId as string;
    expect(sessionId).toBeTruthy();
    expect(window.sessionStorage.getItem("wp-v4-dock-session")).toBe(sessionId);
    // 重挂（zone 切换卸载/重挂同径——组件态消亡后恢复）
    first.unmount();
    const second = renderDock();
    const input2 = second.container.querySelector<HTMLInputElement>(
      'input[data-testid="wp-v4-ai-input"]',
    );
    if (input2 !== null) {
      fireEvent.change(input2, { target: { value: "再算一次" } });
    }
    second.container
      .querySelector<HTMLButtonElement>('button[data-testid="wp-v4-ai-send"]')
      ?.click();
    const call2 = gate.send.mutate.mock.calls[1];
    expect(call2?.[0]?.sessionId).toBe(sessionId); // 同会话续接
    second.unmount();
  });
});
