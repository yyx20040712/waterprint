/**
 * AI 席位对话分页（M7 批 2026-10-07 ChatPane 退役重造——Drawer 浮层→席位
 * 常驻，B-4/B-5；壳层逻辑自 ChatPane 全量承袭，仅壳退役）。
 *
 * 输入:  无 props（席位常驻——查询门控恒真：useChatSessions(true)/
 *        useChatHistory(sessionId)；原 open/onClose 随 Drawer 壳退役）
 * 输出:  ChatPanel 承载体（flex column 满高容器 height:100%——ChatPanel
 *        会话/历史/发言 hook 装配+任务 SSE 轮进度聚合[stage 文案]+B-1 刚建
 *        会话标记[B-2 polling 降级标记 stage 行]+C-5 failed 横幅 error
 *        摘要补查）
 *
 * 沿革（承 ChatPane 头注逐项——逻辑零变更）：
 *   - P0-D（fix-plan 批3）：终态一律清 turnStage=null（busy 面归零）；失败
 *     态转 turnError 横幅面（ChatPanel 渲染）；发送回调面透传（草稿保留归
 *     ChatPanel）；
 *   - F2（e2e-fix-round3 批 R2）：B-1 本轮 POST 返回的客户端建档会话标记
 *     （freshSessionId——history 失败两态文案判据，历史落盘成功退场）；
 *     B-2 SSE 慢探测降级（onConnection 'polling'）→ stage 行「实时通道
 *     不可达——已切换轮询」；C-5 failed 终态补查任务状态 error 摘要
 *     （前 120 字——lib/taskError 单源）；
 *   - 批6f（wave6 §批6f）：非 failed 终态横幅分派单源 terminalTurnText；
 *   - 回炉 W4：补查落定校验轮次归属（防陈旧横幅复活覆盖新一轮）。
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useTaskEventSource } from "../../../shared/api/useTaskEventSource";

import { interpretChatEvent } from "../lib/chatEvent";
import { failedTurnBannerText, fetchTaskErrorSummary, terminalTurnText } from "../lib/taskError";

import { useChatHistory, useChatSessions, useSendChatMessage, CHAT_HISTORY_KEY } from "../api/useAiChat";
import { ChatPanel, type SendMutation } from "./ChatPanel";

/** 首发建档：客户端生成会话 ID（hex32——agent uuid4 同形态对齐）。 */
const generateSessionId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}new`).replace(/-/g, "");

export function ChatSeat() {
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
  // 席位常驻：查询门控恒真（原 Drawer open 门控随壳退役）
  const sessions = useChatSessions(true);
  const history = useChatHistory(sessionId);
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
        // 批6f：三终态文案分派单源（done=null/cancelled=取消文案/未知终态
        // =「未完成」兜底——旧实现把 cancelled 一律称「失败」）
        setTurnError(terminalTurnText(state));
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
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
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
    </div>
  );
}
