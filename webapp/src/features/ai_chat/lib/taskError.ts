/**
 * 聊天失败轮错误摘要（F2 C-5——终态 failed 横幅明细补查，前端补查方案
 * 零协议破面；工单 e2e-fix-round3-2026-09-25 §1 C-5）。
 *
 * 输入:  taskId（既有任务状态端点 GET /api/calc/tasks/{task_id}——orval
 *        生成物 getTaskStatusApiCalcTasksTaskIdGet）
 * 输出:  fetchTaskErrorSummary（error 字段摘要〔前 120 字〕——补查失败/
 *        无 error 回落 null）+failedTurnBannerText（failed 横幅文案单源）
 *        +truncateTaskErrorSummary/TASK_ERROR_SUMMARY_MAX（截断面）
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

/** failed 横幅文案单源（摘要在场=「本轮失败（failed）：{摘要}」）。 */
export function failedTurnBannerText(summary: string | null): string {
  return summary === null ? FAILED_TURN_FALLBACK_TEXT : `本轮失败（failed）：${summary}`;
}
