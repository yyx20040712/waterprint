/**
 * 联合枚举任务态提示（批6f——批2d 欠账②收口：failed/cancelled 终态文案
 * 分派，「非 done 一律『进行中』」幽灵退役；工单 wave6 §批6f）。
 *
 * 输入:  TaskStatus 快照弱类型 JSON 体（kind=joint_enumerate 且非 done——
 *        调用方门控；本函数只管 state 分派）
 * 输出:  jointTaskNotice → JointTaskNotice {kind, text}（kind=failed 取
 *        danger 段/cancelled 取 warning 段/progress 取 secondary 段——
 *        呈现色归组件 Typography type 映射；done → null 防御返空）
 *
 * 规格说明（批6f 简报——工单验收「三终态文案各就位」）：
 *   - failed 明细=taskStatusToView 快照单源（error_type 中文前缀+error+
 *     HTTP 段组合——TaskPanel R6 同款单源纪律，组件内不第二套组装）；
 *   - cancelled≠失败：独立文案（「已取消——可重新提交」）；
 *   - queued/running/未知态维持进度口径「进行中」（误报方向=晚提示安全
 *     ——终态已全分派，非终态不猜终局）；
 *   - 零运行期库 import（node 测试不拖 antd/react 链——taskFeed 同款）。
 */
import { taskStatusToView } from "./taskFeed";

/** 联合枚举任务态提示（kind→呈现段位；text=完整文案单源）。 */
export type JointTaskNotice = {
  kind: "progress" | "failed" | "cancelled";
  text: string;
};

/** 非终态（queued/running/未知态）进度口径——原文案保序（批2d 存量）。
 * 未知态宽容吞入进度面=与 chat terminalTurnText「未完成（态名）」呈示相反
 * 的**有意域差**：joint 消费 TaskStatus 快照（畸形载荷不猜终局——progress
 * 兜底晚提示安全）；chat 消费 SSE 终态回调（真实终态必露名禁吞）。 */
const PROGRESS_TEXT =
  "联合枚举任务进行中——结果将在完成后呈现（进度见上方任务面板）。";

/** 明细空白检（d1-W1 回炉）：?? 只兜 null——空串/纯标点残骸（上游组合
 * 面极端形态）显式落「失败详情缺失」占位，防冒号悬空。 */
function detailOrPlaceholder(error: string | null): string {
  return error !== null && error.trim() !== "" ? error : "失败详情缺失";
}

/** 任务态提示分派：done → null（结果面由调用方挂载，无提示段）。 */
export function jointTaskNotice(status: unknown): JointTaskNotice | null {
  const view = taskStatusToView(status);
  if (view.state === "done") {
    return null;
  }
  if (view.state === "failed") {
    return {
      kind: "failed",
      text: `联合枚举任务失败：${detailOrPlaceholder(view.error)}——可重新提交。`,
    };
  }
  if (view.state === "cancelled") {
    return { kind: "cancelled", text: "联合枚举任务已取消——可重新提交。" };
  }
  return { kind: "progress", text: PROGRESS_TEXT };
}
