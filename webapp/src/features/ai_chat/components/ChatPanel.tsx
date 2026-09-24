/**
 * 对话面板（B4-4b 子批 2——纯展示层：props 注入查询/mutation 句柄）。
 *
 * 输入:  会话清单/历史查询句柄+发言 mutation+活跃轮状态（turnStage/
 *        turnTaskId）
 * 输出:  会话切换 Select+消息流（用户/助手气泡+工具步折叠卡）+输入框+
 *        轮进度行（stage 文案——任务 SSE 面外聚）
 */
import { Input, Progress, Select, Typography } from "antd";
import { useEffect, useRef, useState } from "react";
import type { UseMutationResult, UseQueryResult } from "@tanstack/react-query";

import type { ChatHistoryMessage, ChatSessionSummary, TaskIdResponse } from "../../../shared/api/generated/model";

import { ToolCallCard } from "./ToolCallCard";

export type SessionsQuery = UseQueryResult<ChatSessionSummary[], unknown>;
export type HistoryQuery = UseQueryResult<ChatHistoryMessage[], unknown>;
export type SendMutation = UseMutationResult<
  TaskIdResponse,
  unknown,
  { sessionId: string; message: string },
  unknown
>;

/** 消息气泡（助手消息带工具步轨迹行+截断标记）。 */
function MessageBubble({ message }: { message: ChatHistoryMessage }) {
  const mine = message.role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: mine ? "flex-end" : "flex-start",
        marginBottom: 8,
      }}
      data-testid={`wp-chat-msg-${message.role}`}
    >
      <div
        style={{
          maxWidth: "82%",
          padding: "6px 10px",
          borderRadius: 8,
          background: mine ? "var(--wp-primary-bg, #1c2540)" : "var(--wp-panel-bg, #141a2e)",
          border: "1px solid var(--wp-border)",
        }}
      >
        {(message.tool_steps ?? []).length > 0 && (
          <div>
            {(message.tool_steps ?? []).map((raw, index) => {
              const step = raw as { name?: string; ok?: boolean };
              return (
                <ToolCallCard
                  key={`${step.name ?? "tool"}-${index}`}
                  step={{ name: String(step.name ?? "工具"), ok: step.ok ?? null }}
                />
              );
            })}
          </div>
        )}
        <Typography.Text style={{ whiteSpace: "pre-wrap" }}>{message.text}</Typography.Text>
        {message.truncated && (
          <Typography.Text type="warning" style={{ display: "block" }}>
            （本轮已达工具调用上限，内容截断）
          </Typography.Text>
        )}
      </div>
    </div>
  );
}

export interface ChatPanelProps {
  sessions: SessionsQuery;
  history: HistoryQuery;
  send: SendMutation;
  sessionId: string | null;
  onSessionChange: (sessionId: string) => void;
  newSessionId: () => string;
  turnStage: string | null;
}

export function ChatPanel({
  sessions,
  history,
  send,
  sessionId,
  onSessionChange,
  newSessionId,
  turnStage,
}: ChatPanelProps) {
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const messages = history.data ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, turnStage]);

  const busy = turnStage !== null;
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", gap: 8 }}>
      <Select
        aria-label="会话选择"
        data-testid="wp-chat-session-select"
        value={sessionId}
        onChange={onSessionChange}
        placeholder="选择会话（发言即自动建档）"
        options={(sessions.data ?? []).map((item) => ({
          value: item.session_id,
          label: item.title || `会话 ${item.session_id.slice(0, 8)}`,
        }))}
        style={{ width: "100%" }}
      />
      <div style={{ flex: 1, overflowY: "auto", minHeight: 200, padding: 4 }}>
        {history.isError && (
          <Typography.Text type="danger">会话读取失败（中继不可达）</Typography.Text>
        )}
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {busy && (
          <div data-testid="wp-chat-turn-stage" style={{ padding: 4 }}>
            <Progress percent={99} status="active" size="small" />
            <Typography.Text type="secondary">{turnStage}</Typography.Text>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <Input.Search
        aria-label="消息输入"
        data-testid="wp-chat-input"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onSearch={(text) => {
          const message = text.trim();
          if (!message || busy || send.isPending) return;
          const sid = sessionId ?? newSessionId();
          if (!sessionId) {
            onSessionChange(sid);
          }
          send.mutate({ sessionId: sid, message });
          setDraft("");
        }}
        enterButton="发送"
        placeholder={sessionId ? "输入设计需求…" : "先选择或新建会话"}
        disabled={send.isPending}
      />
    </div>
  );
}
