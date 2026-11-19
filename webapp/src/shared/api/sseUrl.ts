/**
 * SSE 订阅 URL 单源（B6 D8：useTaskFeed/useExportBatch 双实现下沉 shared；
 * 联机第六批 2026-11-19 客户端模式基址切换）。
 *
 * 输入:  taskId（任务 id——用户可控面，路径段编码）+token（getApiToken()
 *        产物；null=匿名零 query）
 * 输出:  buildTaskStreamUrl(taskId, token)——任务事件流 URL（token 非空
 *        拼 ？token= 查询通道：EventSource 无法自定义头=query 是唯一
 *        通道，auth.py sseTokenQuery 双通道对齐；客户端模式前拼
 *        getRemoteBaseUrl 远程 origin——与 http.ts 请求面同源切换）
 */
import { getRemoteBaseUrl } from "./remoteBase";

export function buildTaskStreamUrl(taskId: string, token: string | null): string {
  // 客户端模式远程 origin 前拼（null=本地同源零行为变——http.ts 同制式）
  const origin = getRemoteBaseUrl() ?? "";
  const base = `${origin}/api/events/tasks/${encodeURIComponent(taskId)}`;
  return token === null ? base : `${base}?token=${encodeURIComponent(token)}`;
}
