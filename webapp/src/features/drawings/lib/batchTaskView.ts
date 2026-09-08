/**
 * 批量任务纯投影层：终态判定/SSE 事件解析/outcome 投影/进度派生/状态行
 * 文案（SVRB2 实现期拆件——useExportBatch 507>500 预算红线触发，纯函数
 * 面迁本件；useExportBatch 顶部透传再导出保公开面——executor/exports_
 * support 再导出先例同旨，BatchStatusLine/测试件 import 零改动）。
 *
 * 输入:  服务端任务态 JSON 松面（GET /api/calc/tasks+SSE 事件 data）+
 *        kind 文案维度
 * 输出:  ExportBatchOutcome/ExportBatchProgress 投影+四态状态行文案+
 *        终态判定布尔（node 直测——useExportBatch.test 沿 import 面消费）
 */

/** 单项失败记录（worker failures 面逐项四键——SVRB D4 result schema）。 */
export type ExportBatchFailure = {
  index: number;
  unit_id: string | null;
  condition_key: string | null;
  error: string;
};

/** 任务终态产物束（files=产物清单计数面；error=failed 面任务诊断）。 */
export type ExportBatchOutcome = {
  state: string; // done|cancelled|failed
  files: string[];
  failures: ExportBatchFailure[];
  error: string | null;
};

/** 进度视图（done 序数+total+stage 文本+原始 percent——「导出中 i/N·kind·unit」
 * 与 B5 进度条/状态行双消费源）。 */
export type ExportBatchProgress = {
  done: number;
  total: number;
  stageText: string;
  percent: number;
};

/** 任务状态 JSON 松面（GET /api/calc/tasks 面——result/error 消费位）。 */
export type TaskStatusFace = {
  state?: unknown;
  error?: unknown;
  result?: unknown;
};

/** 终态判定（状态机 done/cancelled/failed——manager 三终态单源镜像）。 */
export function isTerminalTaskState(state: string): boolean {
  return state === "done" || state === "cancelled" || state === "failed";
}

/** SSE 事件 data 解析（{type, message, percent} 三面；畸形/缺型拒 null）。 */
export function parseTaskEventData(
  data: string,
): { type: string; message: string | null; percent: number | null } | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return null;
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return null;
  }
  const record = parsed as Record<string, unknown>;
  if (typeof record.type !== "string") {
    return null;
  }
  return {
    type: record.type,
    message: typeof record.message === "string" ? record.message : null,
    percent: typeof record.percent === "number" ? record.percent : null,
  };
}

/** 终态 outcome 投影（TaskStatus→files/failures/error 四面；result null 兜底空清单）。 */
export function toBatchOutcome(status: TaskStatusFace): ExportBatchOutcome {
  const state = typeof status.state === "string" ? status.state : "failed";
  const result =
    typeof status.result === "object" && status.result !== null && !Array.isArray(status.result)
      ? (status.result as Record<string, unknown>)
      : null;
  return {
    state,
    files: Array.isArray(result?.files)
      ? result.files.filter((file): file is string => typeof file === "string")
      : [],
    failures: Array.isArray(result?.failures)
      ? (result.failures.filter(
          (failure) => typeof failure === "object" && failure !== null,
        ) as ExportBatchFailure[])
      : [],
    error: typeof status.error === "string" ? status.error : null,
  };
}

/** 进度派生（percent 幂商式 (i+1)/(total+1) 还原序数+stage 文本化+percent 透传）。 */
export function deriveBatchProgress(
  percent: number,
  total: number,
  stage: string,
): ExportBatchProgress {
  return {
    done: Math.round(percent * (total + 1)),
    total,
    stageText: stage.startsWith("export:")
      ? stage.slice("export:".length).replace(/:/g, "·")
      : stage,
    percent,
  };
}

/** 恢复首帧（SVRB2 D6）：重订阅至首个 progress 事件前的合成帧——done=0
 * 保守下界+存储 total+空 stageText（进行中分支不消费 stageText、toast 恒
 * gated by batching——空串不达呈现面，R4 终裁亲核+vitest 钉断言）。 */
export function makeResumeProgress(total: number): ExportBatchProgress {
  return { done: 0, total, stageText: "", percent: 0 };
}

/** 状态行文案派生（B5 D3——BatchStatusLine 单源；终态优先于残留 progress，
 *  双 null=null〔从未提交〕）。四态：进行中 percent·i/N｜完成 N 项｜失败
 *  kind·unit·原因（首错 failures[0]，兜底任务级 error）｜取消=已产计数行。
 *  percent（幂商平滑值）与 done/total（序数）并列=双信息面——worker
 *  percent=(i+1)/(total+1) 幂商式设计意图，非数值不一致（B5 R1 钉口径）。 */
export function batchStatusText(
  kind: string,
  progress: ExportBatchProgress | null,
  outcome: ExportBatchOutcome | null,
): string | null {
  if (outcome !== null) {
    if (outcome.state === "done") {
      return `批量出图完成：${outcome.files.length} 项`;
    }
    if (outcome.state === "failed") {
      const failure = outcome.failures[0];
      const reason = failure?.error ?? outcome.error ?? "未知错误";
      return `批量出图失败：${kind}·${failure?.unit_id ?? "—"}·${reason}`;
    }
    return `批量出图已取消：已产 ${outcome.files.length} 项`;
  }
  if (progress !== null) {
    return `批量出图进行中 ${Math.round(progress.percent * 100)}%·${progress.done}/${progress.total}`;
  }
  return null;
}
