/**
 * 聊天失败轮错误摘要（F2 C-5——终态 failed 横幅明细补查，前端补查方案
 * 零协议破面；工单 e2e-fix-round3-2026-09-25 §1 C-5）。
 *
 * 输入:  taskId（既有任务状态端点 GET /api/calc/tasks/{task_id}——orval
 *        生成物 getTaskStatusApiCalcTasksTaskIdGet）
 * 输出:  fetchTaskErrorSummary（error 字段摘要〔前 120 字〕——补查失败/
 *        无 error 回落 null）+failedTurnBannerText（failed 横幅文案单源）
 *        +terminalTurnText（批6f：非 failed 终态横幅分派——done null/
 *        cancelled 取消文案/未知终态兜底）+truncateTaskErrorSummary/
 *        TASK_ERROR_SUMMARY_MAX（截断面）
 *
 * 规格说明：
 *   - SSE 事件载荷无 error 字段（taskFeed 双源归一先例）——failed 明细
 *     经任务状态快照补查（turnStage 终态回调后异步取）；
 *   - 回落语义：补查失败/无 error → null → 通用横幅（横幅仍在场，非
 *     静默吞错——降级态可观测）；
 *   - 截断口径：String.length（UTF-16 码元）前 120——横幅单行约束。
 */
import { getTaskStatusApiCalcTasksTaskIdGet } from "../../../shared/api/generated";

/** 摘要截断上限（C-5：前 120 字——工单 e2e-fix-round3 §1 C-5）。 */
export const TASK_ERROR_SUMMARY_MAX = 120;

/** 无摘要回落文案（补查失败/无 error 字段——通用失败横幅，明确态）。 */
export const FAILED_TURN_FALLBACK_TEXT = "本轮失败（failed）——输入已解锁，可重发";

/** 取消终态文案（批6f：cancelled≠失败——三终态文案分派各就位）。 */
export const CANCELLED_TURN_TEXT = "本轮已取消——输入已解锁，可重发";

/** 截断（前 N 字）。 */
export function truncateTaskErrorSummary(text: string): string {
  return text.length > TASK_ERROR_SUMMARY_MAX
    ? text.slice(0, TASK_ERROR_SUMMARY_MAX)
    : text;
}

/** 任务状态补查：取 error 字段摘要；补查失败/无值 → null（回落通用横幅）。 */
export async function fetchTaskErrorSummary(taskId: string): Promise<string | null> {
  try {
    const status = await getTaskStatusApiCalcTasksTaskIdGet(taskId);
    const raw = status.error;
    return typeof raw === "string" && raw.length > 0 ? truncateTaskErrorSummary(raw) : null;
  } catch {
    return null; // 补查失败=回落通用横幅（横幅在场——降级态可观测，非吞错）
  }
}

/** failed 横幅文案单源（批6f：摘要在场=「本轮失败（failed）：{摘要}——
 * 输入已解锁，可重发」——解锁提示与 fallback/cancelled 文案一致面；
 * 摘要缺席回落通用横幅）。 */
export function failedTurnBannerText(summary: string | null): string {
  return summary === null
    ? FAILED_TURN_FALLBACK_TEXT
    : `本轮失败（failed）：${summary}——输入已解锁，可重发`;
}

/** 非 failed 终态横幅文案（批6f 三终态分派：done=null 无横幅/cancelled=
 * 取消文案；failed 误入=回落通用失败横幅〔明细面归 failedTurnBannerText
 * 补查通道——k1-W1 护栏，防「未完成（failed）」同义不同文〕；未知终态
 * =「未完成」兜底带原始 state 名——禁吞态名。调用方契约=仅终态
 * 〔useTaskEventSource onTerminal 双源过滤：interpretChatEvent
 * TERMINAL_STATES+probeTaskStatusTerminal 终态集〕）。 */
export function terminalTurnText(state: string): string | null {
  if (state === "done") {
    return null;
  }
  if (state === "cancelled") {
    return CANCELLED_TURN_TEXT;
  }
  if (state === "failed") {
    return FAILED_TURN_FALLBACK_TEXT;
  }
  return `本轮未完成（${state}）——输入已解锁，可重发`;
}
