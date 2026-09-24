/**
 * ChatPanel 对话面板测试（B4-4b 子批 2——props 注入查询句柄直构，零 mock）。
 *
 * 输入:  会话/历史/发言句柄桩（UseQueryResult/UseMutationResult 形态）
 * 输出:  消息流渲染（工具步+截断标记）+轮进度行+输入禁用态断言
 */

import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import type { ChatHistoryMessage, ChatSessionSummary } from "../../../shared/api/generated/model";

import { ChatPanel } from "./ChatPanel";

function sessionStub(data: ChatSessionSummary[]) {
  return { data, isError: false } as unknown as Parameters<typeof ChatPanel>[0]["sessions"];
}

function historyStub(data: ChatHistoryMessage[]) {
  return { data, isError: false } as unknown as Parameters<typeof ChatPanel>[0]["history"];
}

const sendStub = {
  mutate: vi.fn(),
  isPending: false,
} as unknown as Parameters<typeof ChatPanel>[0]["send"];

const MESSAGES: ChatHistoryMessage[] = [
  { role: "user", text: "建一座三万吨市政厂", turn: 1, truncated: false, tool_steps: [] },
  {
    role: "assistant",
    text: "已完成计算",
    turn: 1,
    truncated: false,
    tool_steps: [
      { name: "wp_create_project", ok: true },
      { name: "wp_run_calc", ok: true },
    ],
  },
  {
    role: "assistant",
    text: "（截断示例）",
    turn: 2,
    truncated: true,
    tool_steps: [{ name: "wp_run_calc", ok: false }],
  },
];

describe("ChatPanel 对话面板（B4-4b 子批 2）", () => {
  it("消息流渲染：双角色气泡+工具步卡+截断标记", () => {
    const html = renderToString(
      <ChatPanel
        sessions={sessionStub([])}
        history={historyStub(MESSAGES)}
        send={sendStub}
        sessionId="s1"
        onSessionChange={() => undefined}
        newSessionId={() => "fresh-id"}
        turnStage={null}
        turnError={null}
      />,
    );
    expect(html).toContain("wp-chat-msg-user");
    expect(html).toContain("wp-chat-msg-assistant");
    expect(html).toContain("wp-chat-tool-wp_create_project");
    expect(html).toContain("本轮已达工具调用上限");
  });

  it("轮进度行：turnStage 在场时渲染阶段文案", () => {
    const html = renderToString(
      <ChatPanel
        sessions={sessionStub([])}
        history={historyStub([])}
        send={sendStub}
        sessionId="s1"
        onSessionChange={() => undefined}
        newSessionId={() => "fresh-id"}
        turnStage="调用工具 wp_run_calc"
        turnError={null}
      />,
    );
    expect(html).toContain("wp-chat-turn-stage");
    expect(html).toContain("调用工具 wp_run_calc");
  });

  it("读取失败面：错误文案在场（中继不可达诚实提示）", () => {
    const html = renderToString(
      <ChatPanel
        sessions={sessionStub([])}
        history={{ data: undefined, isError: true } as unknown as Parameters<typeof ChatPanel>[0]["history"]}
        send={sendStub}
        sessionId="s1"
        onSessionChange={() => undefined}
        newSessionId={() => "fresh-id"}
        turnStage={null}
        turnError={null}
      />,
    );
    expect(html).toContain("会话读取失败");
  });
});

describe("ChatPanel P0-D（fix-plan 批3——失败轮解锁/横幅/空会话引导）", () => {
  it("失败终态横幅：turnError 在场渲染 wp-chat-turn-error", () => {
    const html = renderToString(
      <ChatPanel
        sessions={sessionStub([])}
        history={historyStub([])}
        send={sendStub}
        sessionId="s1"
        onSessionChange={() => undefined}
        newSessionId={() => "fresh-id"}
        turnStage={null}
        turnError="本轮失败（failed）——输入已解锁，可重发"
      />,
    );
    expect(html).toContain("wp-chat-turn-error");
    expect(html).toContain("输入已解锁");
  });

  it("终态解锁回归锚：turnStage=null 时输入不因残留 stage 锁死（busy 面恒假）", () => {
    const html = renderToString(
      <ChatPanel
        sessions={sessionStub([])}
        history={historyStub([])}
        send={sendStub}
        sessionId="s1"
        onSessionChange={() => undefined}
        newSessionId={() => "fresh-id"}
        turnStage={null}
        turnError={null}
      />,
    );
    expect(html).not.toContain("wp-chat-turn-stage");
    expect(html).toContain('placeholder="输入设计需求…"');
  });

  it("空会话清单引导：无会话时 Select 占位「暂无会话——直接发言即建档」", () => {
    const html = renderToString(
      <ChatPanel
        sessions={{ data: [], isError: false, isLoading: false } as unknown as Parameters<typeof ChatPanel>[0]["sessions"]}
        history={historyStub([])}
        send={sendStub}
        sessionId={null}
        onSessionChange={() => undefined}
        newSessionId={() => "fresh-id"}
        turnStage={null}
        turnError={null}
      />,
    );
    expect(html).toContain("暂无会话——直接发言即建档");
  });
});
