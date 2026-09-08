/**
 * 批量任务恢复存储层：sessionStorage 读写清除三函数（SVRB2 D4——webapp
 * sessionStorage 首例；异常静默降级沿 token.ts 保守先例：隐私模式/配额
 * 满时恢复面整体退化为现状，提交主流程不受损）。
 *
 * 输入:  projectId+kind（键维度——R3 终裁 A 案 hook 显式入参）+
 *        {taskId,total} 载荷+storage 注入面（默认 sessionStorage——node
 *        直测传 mock）
 * 输出:  read→StoredBatchTask|null（缺失/畸形/异常同归 null 单一空态）、
 *        write/clear→void（异常静默）
 */

/** 恢复载荷最小面（taskId 供重挂订阅；total 供恢复首帧与进度派生分母）。 */
export type StoredBatchTask = { taskId: string; total: number };

/** 键前缀（waterprint: 命名空间——token 键同族隔离）。 */
const KEY_PREFIX = "waterprint:exportBatch:";

/** 键名（project+kind 双维度——同项目多 kind 并发批量互不串台）。 */
export function batchTaskKey(projectId: string, kind: string): string {
  return `${KEY_PREFIX}${projectId}:${kind}`;
}

/** 读（缺失/JSON 畸形/字段类型不符/存储异常→null 单一空态）。 */
export function readBatchTask(
  storage: Storage | null,
  projectId: string,
  kind: string,
): StoredBatchTask | null {
  try {
    const raw = storage?.getItem(batchTaskKey(projectId, kind));
    if (raw === null || raw === undefined) {
      return null;
    }
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) {
      return null;
    }
    const record = parsed as Record<string, unknown>;
    const { taskId, total } = record;
    if (typeof taskId !== "string" || taskId === "") {
      return null;
    }
    if (typeof total !== "number" || !Number.isInteger(total) || total <= 0) {
      return null;
    }
    return { taskId, total };
  } catch {
    return null; // 隐私模式/配额/JSON 畸形——保守视同未存储（token.ts 先例）
  }
}

/** 写（PD4 写入点=submitBatch POST 成功取得 task_id 后立即；异常静默）。 */
export function writeBatchTask(
  storage: Storage | null,
  projectId: string,
  kind: string,
  task: StoredBatchTask,
): void {
  try {
    storage?.setItem(batchTaskKey(projectId, kind), JSON.stringify(task));
  } catch {
    // 静默降级：恢复面退化不阻断提交主流程
  }
}

/** 清（PD4 清除点=三终态收束/恢复 404/取消 404；异常静默）。 */
export function clearBatchTask(
  storage: Storage | null,
  projectId: string,
  kind: string,
): void {
  try {
    storage?.removeItem(batchTaskKey(projectId, kind));
  } catch {
    // 静默降级：残留记录下次挂载 GET 兜底
  }
}

/** 默认存储面（SSR/测试无 window→null=三函数全静默降级）。 */
export function defaultBatchStorage(): Storage | null {
  return typeof sessionStorage === "undefined" ? null : sessionStorage;
}
