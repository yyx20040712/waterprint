/**
 * 对话 Drawer 壳（B4-4b 子批 2——浮层形态：零路由破面，aiconnect 先例）。
 *
 * 输入:  open/onClose（App.tsx 顶栏按钮受控）
 * 输出:  Drawer 壳（ChatPanel 承载——会话/历史/发言 hook 装配+任务 SSE
 *        轮进度聚合[stage 文案]）
 */
import { Drawer } from "antd";
import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useTaskEventSource } from "../../../shared/api/useTaskEventSource";
import type { TaskEventReading } from "../../../shared/api/useTaskEventSource";

import { useChatHistory, useChatSessions, useSendChatMessage, CHAT_HISTORY_KEY } from "../api/useAiChat";
import { ChatPanel } from "./ChatPanel";

/** 任务 SSE 解读（TaskEventReading 三态协议——stage 文案经 stageSink 副作用外送）。 */
type StageSink = (stage: string) => void;

function interpretEvent(data: string, stageSink: StageSink): TaskEventReading {
  try {
    const parsed = JSON.parse(data) as { type?: string; state?: string; stage?: string };
    if (parsed.type === "state" && parsed.state && ["done", "failed", "cancelled"].includes(parsed.state)) {
      return { kind: "terminal", state: parsed.state };
    }
    if (parsed.type === "progress" && typeof parsed.stage === "string") {
      stageSink(parsed.stage);
      return { kind: "event" };
    }
  } catch {
    /* 非法行=drop（协议口径：畸形不计链路健康） */
    return { kind: "drop" };
  }
  return { kind: "event" };
}

/** 首发建档：客户端生成会话 ID（hex32——agent uuid4 同形态对齐）。 */
const newSessionId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}new`).replace(/-/g, "");

export function ChatPane({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turnTaskId, setTurnTaskId] = useState<string | null>(null);
  const [turnStage, setTurnStage] = useState<string | null>(null);
  const sessions = useChatSessions(open);
  const history = useChatHistory(open ? sessionId : null);
  const send = useSendChatMessage();
  const client = useQueryClient();

  const wrappedSend = {
    ...send,
    mutate: (variables: { sessionId: string; message: string }) =>
      send.mutate(variables, {
        onSuccess: (data: { task_id: string }) => {
          setSessionId(variables.sessionId);
          setTurnTaskId(data.task_id);
          setTurnStage("已提交");
        },
      }),
  };

  const handleTerminal = useCallback(
    (state: string) => {
      setTurnTaskId(null);
      setTurnStage(state === "done" ? null : `轮结束（${state}）`);
      if (sessionId) {
        void client.invalidateQueries({ queryKey: CHAT_HISTORY_KEY(sessionId) });
      }
    },
    [client, sessionId],
  );

  useTaskEventSource(
    turnTaskId,
    (data) => interpretEvent(data, setTurnStage),
    handleTerminal,
  );

  return (
    <Drawer
      title="设计对话"
      placement="right"
      width={420}
      open={open}
      onClose={onClose}
      styles={{ body: { padding: 12 } }}
    >
      <ChatPanel
        sessions={sessions}
        history={history}
        send={wrappedSend}
        sessionId={sessionId}
        onSessionChange={setSessionId}
        newSessionId={newSessionId}
        turnStage={turnStage}
      />
    </Drawer>
  );
}
