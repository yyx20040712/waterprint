/**
 * 批量任务恢复决策纯函数层：挂载恢复四分支判定+覆盖核对+404 分类
 * （SVRB2 D5——决策树从 hook effect 抽出，node 直测零 IO）。
 *
 * 输入:  StoredBatchTask 载荷+RestoreSnapshot 三态（status/notFound/
 *        unreachable）+重读存储值+GET 异常对象
 * 输出:  RestorePlan 四计划（fill 终态回填/resume 重订阅/drop 清存储/
 *        keep 保留待重试）+stillCurrent 布尔+isNotFoundApiError 分类
 */

import { WaterprintApiError } from "../../../shared/api/http";
import type { StoredBatchTask } from "./batchTaskStore";

/**
 * GET 快照结果三态（hook 侧构造——terminal 预判定归此处快照面，本层
 * 零 api 模块依赖防循环 import；status 原样携带供 fill 分支投影）。
 */
export type RestoreSnapshot =
  | { kind: "status"; terminal: boolean; status: unknown }
  | { kind: "notFound" }
  | { kind: "unreachable" };

/** 恢复计划四分支（PD5：网络异常不清存储=R1 必改；覆盖核对=R5 必改）。 */
export type RestorePlan =
  | { plan: "fill" }
  | { plan: "resume"; taskId: string; total: number }
  | { plan: "drop" }
  | { plan: "keep" };

/** 决策纯函数：notFound=服务端权威否定→drop；unreachable=未知态→keep。 */
export function resolveRestore(
  stored: StoredBatchTask,
  snapshot: RestoreSnapshot,
): RestorePlan {
  if (snapshot.kind === "notFound") {
    return { plan: "drop" };
  }
  if (snapshot.kind === "unreachable") {
    return { plan: "keep" };
  }
  return snapshot.terminal
    ? { plan: "fill" }
    : { plan: "resume", taskId: stored.taskId, total: stored.total };
}

/** 覆盖核对（R5）：异步 GET 窗口内存储被新提交覆盖/清除即放弃本次恢复。 */
export function stillCurrent(reread: StoredBatchTask | null, taskId: string): boolean {
  return reread !== null && reread.taskId === taskId;
}

/** 404 分类：UnknownTaskError（服务端 error_type 面）或 HTTP_404 兜底。 */
export function isNotFoundApiError(error: unknown): boolean {
  return (
    error instanceof WaterprintApiError &&
    (error.code === "UnknownTaskError" || error.code === "HTTP_404")
  );
}
