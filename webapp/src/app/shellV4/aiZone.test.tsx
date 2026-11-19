/**
 * @vitest-environment jsdom
 *
 * v4 AI 助手区测试（b2 壳重组批——B1 底栏 dockBar 升整页 AI 入口：
 * 完成直达〔§一.4 done 任务行→分析面直达+相关单元选中〕+failed 错误
 * 提示面+dock-ai 会话续接〔P3 d1-N7——入口切换卸载/重挂与刷新两径
 * sessionId 持久恢复〕+连接设置钮在场+模型配置钮〔LlmConfigSection
 * 恢复迁 ai_chat〕。dockBar.test.tsx 断言面原样迁入——挂载件换 AiZone）。
 *
 * 输入:  AiZone（任务态/SSE/会话三 hook 模块替身+useAiConfig 替身）+
 *        done/failed 任务夹具
 * 输出:  断言族：①done 任务行点击→onTaskNavigate({state:"done",unitId})
 *        〔unitId=枚举任务 result.unit_id 透传〕②done 且无 unit_id=null
 *        透传 ③failed=错误提示行在场（白名单）④会话续接：发送建档后
 *        sessionStorage 持久→重挂恢复同 sessionId ⑤连接设置钮→
 *        onOpenSettings 调用（Modal 承载在 shellV4）⑥模型配置钮→
 *        LLM 配置 Modal 开（useAiConfig enabled 门控随开态翻转）
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AiZone } from "./aiZone";

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
  chatHistory: {
    data: undefined as
      | Array<{
          role: string;
          text: string;
          turn?: number;
          truncated?: boolean;
          tool_steps?: Array<{ name: string; ok: boolean }>;
        }>
      | undefined,
    isError: false,
    error: null,
  },
  chatHistoryLastSession: null as string | null,
  send: { mutate: vi.fn(), isPending: false },
  llmEnabledLog: [] as boolean[],
  navigate: vi.fn(),
  openSettings: vi.fn(),
}));

vi.mock("../../features/ai_chat/api/useAiChat", () => ({
  useChatHistory: (sessionId: string | null) => {
    gate.chatHistoryLastSession = sessionId;
    return gate.chatHistory;
  },
  useSendChatMessage: () => gate.send,
  useChatSessions: () => ({
    data: [
      {
        session_id: "s1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
        project_id: "p1",
        title: "出水指标与 AAO 方案",
        turns: 2,
      },
      {
        session_id: "s2a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
        project_id: "p1",
      },
      {
        session_id: "s3a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
        project_id: "other",
        title: "他项目会话",
      },
    ],
    isPending: false,
    isError: false,
  }),
}));
vi.mock("../useProjectName", () => ({
  useProjectName: () => "城南污水处理厂扩建工程",
}));
vi.mock("../../features/ai_chat/api/useAiConfig", () => ({
  useAiConfig: (enabled: boolean) => {
    gate.llmEnabledLog.push(enabled);
    return {
      configQuery: { data: undefined, isLoading: true, isError: false, error: null },
      saveMutation: {
        mutate: vi.fn(),
        isPending: false,
        isSuccess: false,
        isError: false,
        error: null,
        reset: vi.fn(),
      },
    };
  },
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

function renderAiZone(url = "/?task=t-done-1&tab=ai") {
  window.history.replaceState(null, "", url);
  return render(
    <QueryClientProvider client={queryClient}>
      <AiZone onTaskNavigate={gate.navigate} onOpenSettings={gate.openSettings} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.navigate.mockClear();
  gate.send.mutate.mockClear();
  gate.openSettings.mockClear();
  gate.llmEnabledLog.length = 0;
  gate.feed = null;
  window.sessionStorage.clear();
});
afterEach(cleanup);

describe("完成直达（§一.4）", () => {
  it("done 任务行点击→onTaskNavigate({state:'done', unitId=枚举 result 透传})", () => {
    const { container } = renderAiZone();
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

  it("done 且 result 无 unit_id→unitId=null 透传（calc 任务——切分析面不选单元）", () => {
    gate.task = {
      ...gate.task,
      data: {
        ...gate.task.data!,
        kind: "calc",
        result: { design_hash: "h1" },
      },
    };
    try {
      const { container } = renderAiZone();
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
    const { container } = renderAiZone();
    const face = container.querySelector('[data-testid="wp-v4-task-error"]');
    expect(face).not.toBeNull();
    expect(face?.textContent).toContain("收敛失败");
  });
});

describe("连接设置入口（B3 U3——R1-W1 透传制）", () => {
  it("连接设置钮在场（AI 窗头行右缀——wp-v4-open-settings）", () => {
    const { container } = renderAiZone();
    expect(
      container.querySelector('[data-testid="wp-ai-connect-open"]'),
    ).toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-open-settings"]'),
    ).not.toBeNull();
  });

  it("点连接设置→onOpenSettings 调用（R1-W1：Modal/自愈监听上提 shellV4 恒挂载层——本件仅入口透传契约）", () => {
    const { container } = renderAiZone();
    fireEvent.click(
      container.querySelector<HTMLButtonElement>(
        '[data-testid="wp-v4-open-settings"]',
      ) as HTMLButtonElement,
    );
    expect(gate.openSettings).toHaveBeenCalledTimes(1);
  });
});

describe("模型配置入口（本地 chat LLM 三键——LlmConfigSection 恢复迁 ai_chat）", () => {
  it("点模型配置→LLM 配置 Modal 开（LlmConfigSection 在场+enabled 翻 true）", () => {
    const { container } = renderAiZone();
    fireEvent.click(
      container.querySelector<HTMLButtonElement>(
        '[data-testid="wp-v4-llm-config"]',
      ) as HTMLButtonElement,
    );
    // Modal 门户挂 document.body——标题+区块标题在场证开态
    expect(document.body.textContent).toContain("模型配置");
    expect(document.body.textContent).toContain("聊天模型接入（LLM）");
    expect(gate.llmEnabledLog.at(-1)).toBe(true);
  });

  it("挂载期 Modal 未开→useAiConfig 零消费（开态门控——关态零请求扰动）", () => {
    renderAiZone();
    expect(gate.llmEnabledLog).toEqual([]);
  });
});

describe("dock-ai 会话续接（P3 d1-N7）", () => {
  it("发送建档 sessionId→sessionStorage 持久→重挂恢复同会话", () => {
    const first = renderAiZone();
    const input = first.container.querySelector<HTMLTextAreaElement>(
      'textarea[data-testid="wp-v4-ai-input"]',
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
    // 重挂（入口切换卸载/重挂同径——组件态消亡后恢复）
    first.unmount();
    const second = renderAiZone();
    const input2 = second.container.querySelector<HTMLTextAreaElement>(
      'textarea[data-testid="wp-v4-ai-input"]',
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

describe("b4 三栏会话面（稿 ai.html——会话清单/消息流/语境栏）", () => {
  it("会话清单：当前项目两行（标题+轮次副行）+他项目会话不入列；点击切换会话", () => {
    const { container } = renderAiZone("/?project=p1&tab=ai");
    const rows = container.querySelectorAll('[data-testid="wp-v4-ai-session-row"]');
    expect(rows.length).toBe(2);
    expect(rows[0]?.textContent).toContain("出水指标与 AAO 方案");
    expect(rows[0]?.textContent).toContain("2 轮对话");
    expect(rows[1]?.textContent).toContain("未命名会话"); // title 缺席回退
    expect(container.textContent).not.toContain("他项目会话");
    fireEvent.click(rows[0] as HTMLElement);
    expect(window.sessionStorage.getItem("wp-v4-dock-session")).toBe(
      "s1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
    );
    // 切换后 useChatHistory 收到该会话 id（AiToolSummary/AiChatFace 同键）
    expect(gate.chatHistoryLastSession).toBe("s1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6");
  });

  it("新建会话=视图态复位（sessionStorage 清键——下次发送重新建档）", () => {
    const { container, getByTestId } = renderAiZone("/?project=p1&tab=ai");
    fireEvent.click(getByTestId("wp-v4-ai-new-session"));
    expect(window.sessionStorage.getItem("wp-v4-dock-session")).toBeNull();
    // 新建后发送 → 新建档（sessionId 非空且写入存储）
    const input = container.querySelector<HTMLTextAreaElement>(
      'textarea[data-testid="wp-v4-ai-input"]',
    );
    if (input !== null) {
      fireEvent.change(input, { target: { value: "新会话首条" } });
    }
    fireEvent.click(getByTestId("wp-v4-ai-send"));
    const call = gate.send.mutate.mock.calls.at(-1);
    expect(typeof call?.[0]?.sessionId).toBe("string");
    expect(window.sessionStorage.getItem("wp-v4-dock-session")).toBe(call?.[0]?.sessionId);
  });

  it("消息流：用户泡/助手卡+工具调用卡（ok 两态）+截断徽标——全量历史呈现", () => {
    gate.chatHistory = {
      data: [
        { role: "user", text: "帮我检查出水指标" },
        {
          role: "assistant",
          text: "已读取可信度报告。",
          turn: 1,
          tool_steps: [
            { name: "读取可信度报告", ok: true },
            { name: "读取警告聚合", ok: false },
          ],
        },
        { role: "assistant", text: "长回复", turn: 2, truncated: true },
      ],
      isError: false,
      error: null,
    };
    const { container } = renderAiZone("/?project=p1&tab=ai");
    fireEvent.click(
      container.querySelector<HTMLButtonElement>(
        '[data-testid="wp-v4-ai-session-row"]',
      ) as HTMLButtonElement,
    );
    const log = container.querySelector('[data-testid="wp-v4-ai-log"]');
    expect(log?.querySelectorAll('[data-testid="wp-v4-ai-msg-user"]').length).toBe(1);
    const assistants = log?.querySelectorAll('[data-testid="wp-v4-ai-msg-assistant"]');
    expect(assistants?.length).toBe(2);
    const tools = log?.querySelectorAll('[data-testid="wp-v4-ai-tool-call"]');
    expect(tools?.length).toBe(2);
    expect(tools?.[0]?.textContent).toContain("读取可信度报告");
    expect(tools?.[0]?.textContent).toContain("完成");
    expect(tools?.[1]?.textContent).toContain("失败"); // 失败不伪装成功
    expect(log?.textContent).toContain("已截断"); // truncated 徽标
    gate.chatHistory = { data: undefined, isError: false, error: null };
  });

  it("语境栏：当前项目名+选中单元投影+本轮工具节", () => {
    gate.chatHistory = {
      data: [
        {
          role: "assistant",
          text: "完成",
          tool_steps: [{ name: "枚举方案", ok: true }],
        },
      ],
      isError: false,
      error: null,
    };
    const { container } = renderAiZone("/?project=p1&node=municipal_aao&tab=ai");
    const context = container.querySelector('[data-region="ai-context"]');
    expect(context?.textContent).toContain("城南污水处理厂扩建工程");
    expect(context?.textContent).toContain("municipal_aao");
    expect(context?.textContent).toContain("枚举方案");
    expect(context?.textContent).toContain("1 次调用");
    gate.chatHistory = { data: undefined, isError: false, error: null };
  });
});
