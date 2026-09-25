/**
 * 对话 Drawer 壳（B4-4b 子批 2——浮层形态：零路由破面，aiconnect 先例）。
 *
 * 输入:  open/onClose（App.tsx 顶栏按钮受控）
 * 输出:  Drawer 壳（ChatPanel 承载——会话/历史/发言 hook 装配+任务 SSE
 *        轮进度聚合[stage 文案]+B-1 刚建会话标记[B-2 polling 降级标记
 *        stage 行]+C-5 failed 横幅 error 摘要补查）
 *
 * P0-D（fix-plan 批3）：终态一律清 turnStage=null（done/failed/cancelled
 *        三态旧实现把「轮结束（failed）」文案留在 stage——busy=turnStage!==null
 *        恒真，输入框一次失败即永久锁死）；失败态转 turnError 横幅面（ChatPanel
 *        渲染）。发送回调面透传（onSuccess/onError——草稿保留归 ChatPanel）。
 * F2（e2e-fix-round3 批 R2）：B-1 本轮 POST 返回的客户端建档会话标记
 *        （freshSessionId——history 失败两态文案判据，历史落盘成功退场）；
 *        B-2 SSE 慢探测降级（onConnection 'polling'）→ stage 行「实时
 *        通道不可达——已切换轮询」；C-5 failed 终态补查任务状态 error
 *        摘要（前 120 字——lib/taskError 单源）。
 */
import { Drawer } from "antd";
import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useTaskEventSource } from "../../../shared/api/useTaskEventSource";

import { interpretChatEvent } from "../lib/chatEvent";
import { failedTurnBannerText, fetchTaskErrorSummary } from "../lib/taskError";

import { useChatHistory, useChatSessions, useSendChatMessage, CHAT_HISTORY_KEY } from "../api/useAiChat";
import { ChatPanel, type SendMutation } from "./ChatPanel";

/** 首发建档：客户端生成会话 ID（hex32——agent uuid4 同形态对齐）。 */
const generateSessionId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}new`).replace(/-/g, "");

export function ChatPane({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turnTaskId, setTurnTaskId] = useState<string | null>(null);
  const [turnStage, setTurnStage] = useState<string | null>(null);
  const [turnError, setTurnError] = useState<string | null>(null);
  /** B-1：本轮客户端建档会话（POST 返回后标记——history 失败判「刚建」态）。 */
  const [freshSessionId, setFreshSessionId] = useState<string | null>(null);
  /** B-1：最近生成的建档 ID（POST 返回比对——仅客户端建档会话入标记）。 */
  const generatedSessionRef = useRef<string | null>(null);
  /** 回炉 W4：最新轮任务 ID 镜像（补查落定校验轮次归属防陈旧横幅复活）。 */
  const turnTaskIdRef = useRef<string | null>(null);
  turnTaskIdRef.current = turnTaskId;
  const sessions = useChatSessions(open);
  const history = useChatHistory(open ? sessionId : null);
  const send = useSendChatMessage();
  const client = useQueryClient();

  const newSessionId = () => {
    const id = generateSessionId();
    generatedSessionRef.current = id;
    return id;
  };

  // B-1：建档会话历史落盘成功——刚建标记退场（两态文案判据复位）
  useEffect(() => {
    if (sessionId !== null && history.isSuccess) {
      setFreshSessionId((current) => (current === sessionId ? null : current));
    }
  }, [sessionId, history.isSuccess]);

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
          if (generatedSessionRef.current === variables.sessionId) {
            // B-1：本轮 POST 返回的会话=客户端建档——刚建标记在场
            setFreshSessionId(variables.sessionId);
          }
          options?.onSuccess?.(data);
        },
        onError: (error: unknown) => options?.onError?.(error),
      }),
  };

  const handleTerminal = useCallback(
    (state: string) => {
      const taskId = turnTaskId;
      setTurnTaskId(null);
      // P0-D：终态一律解锁（清 stage——busy 面归零）；非 done 转横幅面
      setTurnStage(null);
      if (state === "failed") {
        // C-5：failed 横幅补 error 摘要（任务状态面补查——前 120 字）；
        // 先落通用横幅即时反馈，补查落定升级明细（失败/无值回落保持通用）
        setTurnError(failedTurnBannerText(null));
        if (taskId !== null) {
          // 回炉 W4：补查落定校验轮次归属——用户已重发（新一轮 task 在场）
          // 时陈旧摘要不得复活覆盖新一轮的干净横幅；本轮已终态（ref=null
          // 且无新轮）照常升级明细
          void fetchTaskErrorSummary(taskId).then((summary) => {
            if (
              turnTaskIdRef.current === null ||
              turnTaskIdRef.current === taskId
            ) {
              setTurnError(failedTurnBannerText(summary));
            }
          });
        }
      } else {
        setTurnError(state === "done" ? null : `本轮失败（${state}）——输入已解锁，可重发`);
      }
      if (sessionId) {
        void client.invalidateQueries({ queryKey: CHAT_HISTORY_KEY(sessionId) });
      }
    },
    [client, sessionId, turnTaskId],
  );

  useTaskEventSource(
    turnTaskId,
    (data) => interpretChatEvent(data, setTurnStage),
    handleTerminal,
    // B-2：SSE 慢探测降级标记——实时通道不可达已切轮询（stage 行展示，
    // 轮询兜底续走——终态经 onTerminal 收口解锁）
    (connection) => {
      if (connection === "polling") {
        setTurnStage("实时通道不可达——已切换轮询");
      }
    },
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
        freshSessionId={freshSessionId}
      />
    </Drawer>
  );
}
