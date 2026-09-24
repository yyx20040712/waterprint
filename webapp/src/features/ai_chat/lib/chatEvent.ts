/**
 * 聊天任务事件解读（B4-4b 门二 P0 修复件——字段协议与 useTaskFeed 同源）。
 *
 * 输入:  SSE data 原文（Event 五键 {type,task_id,percent,message,condition_key}
 *        ——state 名与阶段文本都载于 message 字段）
 * 输出:  TaskEventReading 三态（terminal=state 终名；progress=stage 文案经
 *        stageSink 副作用外送；畸形=drop）
 */
import type { TaskEventReading } from "../../../shared/api/useTaskEventSource";

type StageSink = (stage: string) => void;

const TERMINAL_STATES = ["done", "failed", "cancelled"];

export function interpretChatEvent(data: string, stageSink: StageSink): TaskEventReading {
  let parsed: { type?: string; message?: string | null };
  try {
    parsed = JSON.parse(data) as { type?: string; message?: string | null };
  } catch {
    return { kind: "drop" };
  }
  if (parsed.type === "state" && typeof parsed.message === "string" && TERMINAL_STATES.includes(parsed.message)) {
    return { kind: "terminal", state: parsed.message };
  }
  if (parsed.type === "progress" && typeof parsed.message === "string") {
    stageSink(parsed.message);
  }
  return { kind: "event" };
}
