/**
 * trust 视图纯函数层：窄化门+语义色/格式化映射（消费 /api/calc/trust 响应）。
 *
 * 输入:  orval 生成 TrustReportResponse（server services.trust 聚合投影）
 * 输出:  narrowTrustResponse 窄化门（非法形状抛 TrustViewError）+
 *        marginTone/marginText 裕度语义色（SolutionsTable 正绿负红先例）+
 *        severityTone 警告级 Alert 映射（PumpStationsPanel 先例）+
 *        formatResidual/formatFlow 数值格式化+fluidLabel/loopParamLabel
 *        中文标签（显示层词典——core 字段 ID 不进正文）
 *
 * 规格说明（P2 次批 ADR-012；estimateView 窄化门同构先例）：
 *   - 窄化门逐字段校验（顶层 13 键+收敛/闭合/裕度/警告条目键域）——
 *     非法形状→查询 error 态呈现（禁带病渲染半张面板）；
 *   - 裕度语义：margin>=0 达标（绿 ok）/负值超限（红 over）——
 *     (限值−值)/限值 口径 server 侧 quality.margin 同源；
 *   - 残差/流量格式化：toExponential(3)（跨量级稳定可读——收敛残差
 *     1e-12 量级/流量 m³/s 0.4 量级同一形态）；百分比 toFixed(2)；
 *   - 泥线减量注记（浓缩/消化/脱水/干化单元残差=工艺性水量变化非数值
 *     错误）归面板文案，本层不判（判读语义在展示层注记）。
 */

/** 窄化门拒绝（非法响应形状——查询 error 态呈现）。 */
export class TrustViewError extends Error {
  constructor(detail: string) {
    super(`可信度报告形状非法：${detail}（server/services/trust 契约漂移？）`);
    this.name = "TrustViewError";
  }
}

/** orval 生成类型再导出（组件面单点 import）。 */
export type TrustReport = {
  project_id: string;
  task_id: string;
  stale: boolean;
  design_hash: string;
  engine_version: string;
  data_version: string;
  diagnostics_available: boolean;
  loop_params: Record<string, number>;
  convergence: ReadonlyArray<{
    condition_key: string;
    loop_nodes: string[];
    iterations: number;
    final_residual: number;
  }>;
  mass_balance: ReadonlyArray<{
    condition_key: string;
    lines: ReadonlyArray<{
      fluid: string;
      q_sources_total: number;
      q_sinks_total: number;
      closure_rel: number;
    }>;
    unit_imbalances: ReadonlyArray<{
      unit_id: string;
      fluid: string;
      q_in: number;
      q_out: number;
      delta_rel: number;
    }>;
  }>;
  effluent: ReadonlyArray<{
    condition_key: string;
    standard_id: string;
    indicator: string;
    value: number;
    limit: number;
    margin: number;
  }>;
  warnings: ReadonlyArray<{
    unit_id: string;
    severity: string;
    source: string;
    message: string;
    param_key: string | null;
    condition_key: string | null;
    affected_unit_ids: string[];
  }>;
  warning_counts: Record<string, number>;
};

const TOP_KEYS: readonly string[] = [
  "project_id", "task_id", "stale", "design_hash", "engine_version",
  "data_version", "diagnostics_available", "loop_params", "convergence",
  "mass_balance", "effluent", "warnings", "warning_counts",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** 窄化门：顶层 13 键+四条目族键域逐项校验（非法抛 TrustViewError）。 */
export function narrowTrustResponse(raw: unknown): TrustReport {
  if (!isRecord(raw)) throw new TrustViewError("顶层非对象");
  for (const key of TOP_KEYS) {
    if (!(key in raw)) throw new TrustViewError(`顶层缺 ${key}`);
  }
  const report = raw as unknown as TrustReport;
  if (typeof report.diagnostics_available !== "boolean") {
    throw new TrustViewError("diagnostics_available 非布尔");
  }
  if (!Array.isArray(report.convergence)) {
    throw new TrustViewError("convergence 非数组");
  }
  report.convergence.forEach((item, index) => {
    if (
      typeof item.condition_key !== "string" ||
      !Array.isArray(item.loop_nodes) || typeof item.iterations !== "number" ||
      typeof item.final_residual !== "number"
    ) {
      throw new TrustViewError(`convergence[${index}] 键域非法`);
    }
  });
  if (!Array.isArray(report.mass_balance)) {
    throw new TrustViewError("mass_balance 非数组");
  }
  report.mass_balance.forEach((item, index) => {
    if (
      typeof item.condition_key !== "string" || !Array.isArray(item.lines) ||
      !Array.isArray(item.unit_imbalances)
    ) {
      throw new TrustViewError(`mass_balance[${index}] 键域非法`);
    }
  });
  if (!Array.isArray(report.effluent)) throw new TrustViewError("effluent 非数组");
  report.effluent.forEach((item, index) => {
    if (
      typeof item.condition_key !== "string" ||
      typeof item.standard_id !== "string" || typeof item.indicator !== "string" ||
      typeof item.value !== "number" || typeof item.limit !== "number" ||
      typeof item.margin !== "number"
    ) {
      throw new TrustViewError(`effluent[${index}] 键域非法`);
    }
  });
  if (!Array.isArray(report.warnings)) throw new TrustViewError("warnings 非数组");
  report.warnings.forEach((item, index) => {
    if (
      typeof item.unit_id !== "string" || typeof item.severity !== "string" ||
      typeof item.message !== "string" || typeof item.source !== "string"
    ) {
      throw new TrustViewError(`warnings[${index}] 键域非法`);
    }
  });
  if (!isRecord(report.loop_params) || !isRecord(report.warning_counts)) {
    throw new TrustViewError("loop_params/warning_counts 非对象");
  }
  return report;
}

/** 裕度语义色（正=达标绿/负=超限红——SolutionsTable margin 同纪律）。 */
export function marginTone(margin: number): "ok" | "over" {
  return margin >= 0 ? "ok" : "over";
}

/** 裕度文案：+12.3% / -8.7%（达标带正号——工程对照表惯例；
 * 符号=toFixed ASCII 连字符）。 */
export function marginText(margin: number): string {
  const percent = (margin * 100).toFixed(2);
  return margin >= 0 ? `+${percent}%` : `${percent}%`;
}

/** 警告级→antd 语义（PumpStationsPanel severity Alert 先例同映射）。 */
export function severityTone(
  severity: string,
): "error" | "warning" | "info" {
  if (severity === "ERROR") return "error";
  if (severity === "WARN") return "warning";
  return "info";
}

/** 残差/小量级流量格式化：科学计数三位尾（跨量级稳定可读）。 */
export function formatSci(value: number): string {
  return value.toExponential(3);
}

/** 常规流量格式化：四位小数（m³/s 量级）。 */
export function formatFlow(value: number): string {
  return value.toFixed(4);
}

/** 相对闭合差/偏差文案：百分比两位（<0.01% 显 "<0.01%"——零漂移可读）。 */
export function formatRel(value: number): string {
  const percent = Math.abs(value) * 100;
  if (percent < 0.01 && percent > 0) return "<0.01%";
  return `${(value * 100).toFixed(2)}%`;
}

/** 流体线中文标签（显示层词典——字段 ID 不进正文）。 */
export function fluidLabel(fluid: string): string {
  if (fluid === "WATER") return "水线";
  if (fluid === "SLUDGE") return "泥线";
  return fluid;
}

/** 回路参数中文标签（loop.* 三键——口径透明卡）。 */
export function loopParamLabel(key: string): string {
  if (key === "loop.tolerance") return "收敛容差";
  if (key === "loop.max_iterations") return "迭代上限";
  if (key === "loop.damping") return "阻尼系数";
  return key;
}
