/**
 * 对话中继 API 薄封装（B4-4b 子批 2）：会话清单/历史/发言三 hook。
 *
 * 输入:  orval 生成物（generated/ai-chat）+会话 ID
 * 输出:  useChatSessions（清单查询）/useChatHistory（历史查询）/
 *        useSendChatMessage（发言 mutation→task_id）
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getListSessionsApiAiSessionsGetQueryKey,
  getReadMessagesApiAiSessionsSessionIdMessagesGetQueryKey,
  listSessionsApiAiSessionsGet,
  readMessagesApiAiSessionsSessionIdMessagesGet,
  sendMessageApiAiSessionsSessionIdMessagesPost,
} from "../../../shared/api/generated";
import type { ChatMessageIn } from "../../../shared/api/generated/model";

/** 会话历史/清单失效键（发言终态后刷新——调用方 invalidate）。 */
export const CHAT_HISTORY_KEY = getReadMessagesApiAiSessionsSessionIdMessagesGetQueryKey;

/** 会话清单（Drawer 开态门控查询——aiconnect 同制）。 */
export function useChatSessions(enabled: boolean) {
  return useQuery({
    queryKey: getListSessionsApiAiSessionsGetQueryKey(),
    queryFn: listSessionsApiAiSessionsGet,
    enabled,
  });
}

/** 会话历史（会话选中态门控）。 */
export function useChatHistory(sessionId: string | null) {
  return useQuery({
    queryKey: getReadMessagesApiAiSessionsSessionIdMessagesGetQueryKey(sessionId ?? ""),
    queryFn: () => readMessagesApiAiSessionsSessionIdMessagesGet(sessionId ?? ""),
    enabled: sessionId !== null,
  });
}

/** 发言（返回 task_id——进度走既有任务 SSE 面；sessionId 显式入参防态竞态）。 */
export function useSendChatMessage() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, message }: { sessionId: string } & ChatMessageIn) =>
      sendMessageApiAiSessionsSessionIdMessagesPost(sessionId, { message }),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: getListSessionsApiAiSessionsGetQueryKey(),
      });
    },
  });
}
