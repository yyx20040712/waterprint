/**
 * opsChain 视图纯函数层：窄化门+状态语义色/格式化映射（消费 /api/debug/ops-chain 响应）。
 *
 * 输入:  orval 生成 OpsChainResponse（server services.ops_debug 聚合投影）
 * 输出:  narrowOpsChainResponse 窄化门（非法形状抛 OpsChainViewError）+
 *        stateTone/stateLabel 任务状态语义（done 绿/failed 红/cancelled 灰/
 *        running 蓝进行中）+kindLabel 任务类中文+formatUnix 完成时刻+
 *        formatSci 残差格式化（trustView 同款跨量级形态）
 *
 * 规格说明（B4-1 实现批《裁决书》方案五①；trustView 窄化门同构先例）：
 *   - 窄化门逐字段校验（顶层 3 键+任务条目 13 键域+聚合块 8 键）——
 *     非法形状→查询 error 态呈现（禁带病渲染半张面板）；
 *   - latest_calc=null 双因（无 done calc/结果文件不可读）由面板对照
 *     任务时间线推断呈现——本层不猜因（server 侧单义空块）；
 *   - finished_at_unix=server 内存 WP4 值（进程重启恢复记录=恢复时刻
 *     新租约——时刻注记归面板文案，本层只格式化不判读）。
 */

/** 窄化门拒绝（非法响应形状——查询 error 态呈现）。 */
export class OpsChainViewError extends Error {
  constructor(detail: string) {
    super(`操作链观测面形状非法：${detail}（server/services/ops_debug 契约漂移？）`);
    this.name = "OpsChainViewError";
  }
}

/** orval 生成类型再导出（组件面单点 import）。 */
export type OpsTaskEntry = {
  task_id: string;
  kind: string;
  state: string;
  progress: number;
  stage: string;
  condition_key: string | null;
  stale: boolean;
  error: string | null;
  error_type: string | null;
  error_code: number | null;
  snapshot_hash: string | null;
  finished_at_unix: number | null;
  result?: Record<string, unknown> | null;
};

export type OpsChainReport = {
  project_id: string;
  tasks: ReadonlyArray<OpsTaskEntry>;
  latest_calc: {
    task_id: string;
    stale: boolean;
    design_hash: string;
    engine_version: string;
    data_version: string;
    diagnostics: {
      diagnostics_available: boolean;
      convergence_lines: number;
      max_iterations: number;
      worst_final_residual: number;
      mass_balance_lines: number;
      effluent_lines: number;
    };
    warning_counts: Record<string, number>;
    trace: {
      total_nodes: number;
      by_condition: Record<string, number>;
      by_unit: Record<string, number>;
      by_formula: Record<string, number>;
    };
  } | null;
};

const TOP_KEYS: readonly string[] = ["project_id", "tasks", "latest_calc"];

const TASK_KEYS: readonly string[] = [
  "task_id", "kind", "state", "progress", "stage", "condition_key", "stale",
  "error", "error_type", "error_code", "snapshot_hash", "finished_at_unix",
  "result",
];

/** 可空字符串叶子校验（null 合法——服务端 None 直投影）。 */
function strOrNull(value: unknown): boolean {
  return value === null || typeof value === "string";
}

/** 可空数值叶子校验。 */
function numOrNull(value: unknown): boolean {
  return value === null || typeof value === "number";
}

const LATEST_KEYS: readonly string[] = [
  "task_id", "stale", "design_hash", "engine_version", "data_version",
  "diagnostics", "warning_counts", "trace",
];

const DIAG_KEYS: readonly string[] = [
  "diagnostics_available", "convergence_lines", "max_iterations",
  "worst_final_residual", "mass_balance_lines", "effluent_lines",
];

const TRACE_KEYS: readonly string[] = [
  "total_nodes", "by_condition", "by_unit", "by_formula",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function requireKeys(
  raw: Record<string, unknown>,
  keys: readonly string[],
  where: string,
): void {
  for (const key of keys) {
    if (!(key in raw)) throw new OpsChainViewError(`${where} 缺 ${key}`);
  }
}

/** 窄化门：顶层 3 键+任务条目 13 键域逐项校验（非法抛 OpsChainViewError）。 */
export function narrowOpsChainResponse(raw: unknown): OpsChainReport {
  if (!isRecord(raw)) throw new OpsChainViewError("顶层非对象");
  requireKeys(raw, TOP_KEYS, "顶层");
  const report = raw as unknown as OpsChainReport;
  if (!Array.isArray(report.tasks)) throw new OpsChainViewError("tasks 非数组");
  report.tasks.forEach((task, index) => {
    if (!isRecord(task)) throw new OpsChainViewError(`tasks[${index}] 非对象`);
    requireKeys(task, TASK_KEYS, `tasks[${index}]`);
    // result 叶子：null（未终态）或对象（句柄投影）——server 恒发该键
    const resultOk =
      task.result === null ||
      (isRecord(task.result) && task.result !== null);
    if (
      typeof task.task_id !== "string" || typeof task.kind !== "string" ||
      typeof task.state !== "string" || typeof task.progress !== "number" ||
      typeof task.stage !== "string" || typeof task.stale !== "boolean" ||
      !strOrNull(task.condition_key) || !strOrNull(task.error) ||
      !strOrNull(task.error_type) || !strOrNull(task.snapshot_hash) ||
      !numOrNull(task.error_code) || !numOrNull(task.finished_at_unix) ||
      !resultOk
    ) {
      throw new OpsChainViewError(`tasks[${index}] 键域非法`);
    }
  });
  if (report.latest_calc !== null && report.latest_calc !== undefined) {
    const latest = report.latest_calc as unknown as Record<string, unknown>;
    requireKeys(latest, LATEST_KEYS, "latest_calc");
    const diag = latest.diagnostics as unknown as Record<string, unknown>;
    if (!isRecord(diag)) throw new OpsChainViewError("diagnostics 非对象");
    requireKeys(diag, DIAG_KEYS, "latest_calc.diagnostics");
    const trace = latest.trace as unknown as Record<string, unknown>;
    if (!isRecord(trace)) throw new OpsChainViewError("trace 非对象");
    requireKeys(trace, TRACE_KEYS, "latest_calc.trace");
    if (!isRecord(latest.warning_counts)) {
      throw new OpsChainViewError("warning_counts 非对象");
    }
  }
  return report;
}

/** 任务状态语义色（done 绿/failed 红/cancelled 灰/进行态蓝——展示层词典）。 */
export function stateTone(state: string): string {
  if (state === "done") return "green";
  if (state === "failed") return "red";
  if (state === "cancelled") return "default";
  return "processing";
}

/** 任务类中文标签（kind 三值——显示层词典）。 */
export function kindLabel(kind: string): string {
  if (kind === "calc") return "全厂计算";
  if (kind === "enumerate") return "方案枚举";
  if (kind === "export_batch") return "批量导出";
  return kind;
}

/** 完成时刻格式化（本地时刻+秒——运行诊断面可读口径；null=未终态/未落点）。 */
export function formatUnix(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return new Date(value * 1000).toLocaleString("zh-CN", { hour12: false });
}

/** 残差格式化：科学计数三位尾（trustView formatSci 同款跨量级形态）。 */
export function formatSci(value: number): string {
  return value.toExponential(3);
}

/** 进度格式化：百分比整数（时间线紧凑口径）。 */
export function formatProgress(value: number): string {
  return `${Math.round(value * 100)}%`;
}
