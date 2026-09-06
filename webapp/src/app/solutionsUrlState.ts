/**
 * 职责：方案面板 URL 键回写纯函数（B15 自 solutionsPane 预拆——495 近顶
 * 减压；零行为变更纯搬迁）。
 *
 * 输入:  window.location 实况+目标键值
 * 输出:  replaceState 写 URL（enum/task 两轨共用共底；不触发导航）
 */

import { withEnumParam, withTaskParam } from "./projectParam";

/** URL 键回写共底（replaceState 不触发导航——enum/task 两轨共用）。 */
export function replaceSearch(search: string): void {
  window.history.replaceState(
    null,
    "",
    search ? `${window.location.pathname}?${search}` : window.location.pathname,
  );
}

/** ?enum= 回写（ENG5 D6 枚举轨——task 键不动）。 */
export function writeEnumParam(nextEnumId: string): void {
  replaceSearch(withEnumParam(window.location.search, nextEnumId));
}

/** ?task= 回写（计算轨——方案应用面；enum 键不动）。 */
export function writeTaskParam(nextTaskId: string): void {
  replaceSearch(withTaskParam(window.location.search, nextTaskId));
}
