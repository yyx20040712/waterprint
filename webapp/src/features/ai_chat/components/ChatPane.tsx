/**
 * 对话 Drawer 壳（B4-4b 子批 2——浮层形态：零路由破面，aiconnect 先例）。
 *
 * 输入:  open/onClose（App.tsx 顶栏按钮受控）
 * 输出:  Drawer 壳（ChatPanel 承载——会话/历史/发言 hook 装配+任务 SSE
 *        轮进度聚合[stage 文案]）
 *
 * P0-D（fix-plan 批3）：终态一律清 turnStage=null（done/failed/cancelled
 * 三态旧实现把「轮结束（failed）」文案留在 stage——busy=turnStage!==null
 * 恒真，输入框一次失败即永久锁死）；失败态转 turnError 横幅面（ChatPanel
 * 渲染）。发送回调面透传（onSuccess/onError——草稿保留归 ChatPanel）。
 */
import { Drawer } from "antd";
import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useTaskEventSource } from "../../../shared/api/useTaskEventSource";

import { interpretChatEvent } from "../lib/chatEvent";

import { useChatHistory, useChatSessions, useSendChatMessage, CHAT_HISTORY_KEY } from "../api/useAiChat";
import { ChatPanel, type SendMutation } from "./ChatPanel";

/** 首发建档：客户端生成会话 ID（hex32——agent uuid4 同形态对齐）。 */
const newSessionId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}new`).replace(/-/g, "");

export function ChatPane({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turnTaskId, setTurnTaskId] = useState<string | null>(null);
  const [turnStage, setTurnStage] = useState<string | null>(null);
  const [turnError, setTurnError] = useState<string | null>(null);
  const sessions = useChatSessions(open);
  const history = useChatHistory(open ? sessionId : null);
  const send = useSendChatMessage();
  const client = useQueryClient();

  const wrappedSend: SendMutation = {
    ...send,
    mutate: (
      variables: { sessionId: string; message: string },
      options?: {
        onSuccess?: (data: { task_id: string }) => void;
        onError?: (error: unknown) => void;
      },
    ) =>
      send.mutate(variables, {
        onSuccess: (data: { task_id: string }) => {
          setSessionId(variables.sessionId);
          setTurnTaskId(data.task_id);
          setTurnStage("已提交");
          setTurnError(null);
          options?.onSuccess?.(data);
        },
        onError: (error: unknown) => options?.onError?.(error),
      }),
  };

  const handleTerminal = useCallback(
    (state: string) => {
      setTurnTaskId(null);
      // P0-D：终态一律解锁（清 stage——busy 面归零）；非 done 转横幅面
      setTurnStage(null);
      setTurnError(state === "done" ? null : `本轮失败（${state}）——输入已解锁，可重发`);
      if (sessionId) {
        void client.invalidateQueries({ queryKey: CHAT_HISTORY_KEY(sessionId) });
      }
    },
    [client, sessionId],
  );

  useTaskEventSource(
    turnTaskId,
    (data) => interpretChatEvent(data, setTurnStage),
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
        turnError={turnError}
      />
    </Drawer>
  );
}
