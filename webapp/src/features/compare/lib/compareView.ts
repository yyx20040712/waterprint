/**
 * compare 视图纯函数层：窄化门+锁定基准判定+矩阵行模型（消费
 * /api/calc/compare 响应——P2 第三批 ADR-018 D1/D3）。
 *
 * 输入:  orval 生成 CompareReportResponse（server services.compare 聚合
 *        投影）+项目 raw.view.compare 锁定态（FE 消费面）
 * 输出:  narrowCompareResponse 窄化门（非法形状抛 CompareViewError）+
 *        pinOf/isPinStale/filterLivePins 锁定基准三件（D3 语义）+
 *        metricRowKey/metricLabel/rowExtremes 矩阵行模型（D1 呈现面）
 *
 * 规格说明（P2 第三批 ADR-018；trustView 窄化门同构先例）：
 *   - 窄化门逐字段校验（顶层 10 键+指标/警告条目键域）——非法形状→
 *     查询 error 态呈现（禁带病渲染半张矩阵）；
 *   - 锁定基准（D3）：pinned=工况键集+pinned_hash=锁定时刻结果件
 *     design_hash；过期判定=比对当前报告 design_hash（改设计→重算→
 *     新结果件 hash 不同→过期——与结果集新旧正交）；失效键=受检集
 *     变更后不在当前 condition_keys 的键（灰显呈现，不自动删——
 *     清理经「重新锁定」或手动解除）；
 *   - 零运行期库 import（node 测试不拖 antd/react-query 链——运行期
 *     import 仅 shared/dimLabels）。
 */

/** 窄化门拒绝（非法响应形状——查询 error 态呈现）。 */
export class CompareViewError extends Error {
  constructor(detail: string) {
    super(`多工况对比报告形状非法：${detail}（server/services/compare 契约漂移？）`);
    this.name = "CompareViewError";
  }
}

/** 对比报告（orval 生成类型镜像——组件面单点 import）。 */
export type CompareReport = {
  project_id: string;
  task_id: string;
  stale: boolean;
  design_hash: string;
  engine_version: string;
  data_version: string;
  condition_keys: string[];
  metrics: ReadonlyArray<{
    unit_id: string;
    field_id: string;
    label_zh: string | null;
    dim: string;
    values: Record<string, number>;
  }>;
  warnings: ReadonlyArray<{
    unit_id: string;
    counts: Record<string, number>;
  }>;
};

/** 锁定基准态（view.compare 载荷——D3 {pinned, pinned_hash}）。 */
export type PinState = {
  pinned: string[];
  pinned_hash: string;
};

const TOP_KEYS: readonly string[] = [
  "project_id", "task_id", "stale", "design_hash", "engine_version",
  "data_version", "condition_keys", "metrics", "warnings",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** 窄化门：顶层 10 键+指标/警告条目键域逐项校验（非法抛 CompareViewError）。 */
export function narrowCompareResponse(raw: unknown): CompareReport {
  if (!isRecord(raw)) throw new CompareViewError("顶层非对象");
  for (const key of TOP_KEYS) {
    if (!(key in raw)) throw new CompareViewError(`顶层缺 ${key}`);
  }
  const report = raw as unknown as CompareReport;
  if (typeof report.project_id !== "string" || typeof report.task_id !== "string") {
    throw new CompareViewError("溯源双键非字符串");
  }
  if (typeof report.stale !== "boolean") throw new CompareViewError("stale 非布尔");
  if (
    typeof report.design_hash !== "string" ||
    typeof report.engine_version !== "string" ||
    typeof report.data_version !== "string"
  ) {
    throw new CompareViewError("repro 三元组键域非法");
  }
  if (
    !Array.isArray(report.condition_keys) ||
    report.condition_keys.some((key) => typeof key !== "string")
  ) {
    throw new CompareViewError("condition_keys 非字符串数组");
  }
  if (!Array.isArray(report.metrics)) throw new CompareViewError("metrics 非数组");
  report.metrics.forEach((item, index) => {
    if (
      typeof item.unit_id !== "string" || typeof item.field_id !== "string" ||
      (item.label_zh !== null && typeof item.label_zh !== "string") ||
      typeof item.dim !== "string" || !isRecord(item.values) ||
      Object.values(item.values).some((value) => typeof value !== "number")
    ) {
      throw new CompareViewError(`metrics[${index}] 键域非法`);
    }
  });
  if (!Array.isArray(report.warnings)) throw new CompareViewError("warnings 非数组");
  report.warnings.forEach((item, index) => {
    if (
      typeof item.unit_id !== "string" || !isRecord(item.counts) ||
      Object.values(item.counts).some((value) => typeof value !== "number")
    ) {
      throw new CompareViewError(`warnings[${index}] 键域非法`);
    }
  });
  return report;
}

/** raw.view.compare 锁定态宽容读取（缺省/异形=null=未锁定）。 */
export function pinOf(viewCompare: unknown): PinState | null {
  if (!isRecord(viewCompare)) return null;
  const pinned = viewCompare["pinned"];
  const pinnedHash = viewCompare["pinned_hash"];
  if (
    !Array.isArray(pinned) || pinned.some((key) => typeof key !== "string") ||
    typeof pinnedHash !== "string" || pinnedHash === ""
  ) {
    return null;
  }
  return { pinned: pinned as string[], pinned_hash: pinnedHash };
}

/** D3 过期判定：锁定基准 hash ≠ 当前报告结果件 design_hash=基准已过期。 */
export function isPinStale(pin: PinState | null, report: CompareReport): boolean {
  if (pin === null) return false;
  return pin.pinned_hash !== report.design_hash;
}

/** D3 失效键过滤：pinned ∩ 当前工况键集=存活；不在=失效（灰显不自动删）。 */
export function filterLivePins(
  pinned: readonly string[],
  conditionKeys: readonly string[],
): { live: string[]; expired: string[] } {
  const live = new Set(conditionKeys);
  return {
    live: pinned.filter((key) => live.has(key)),
    expired: pinned.filter((key) => !live.has(key)),
  };
}

/** 矩阵行键：unit×field 全序（同一单元同字段跨工况一行）。 */
export function metricRowKey(unitId: string, fieldId: string): string {
  return `${unitId}.${fieldId}`;
}

/** 指标显示名：label_zh 真源降级 field_id（V2 制式——key 兜底归显示层）。 */
export function metricLabel(
  row: Readonly<{ label_zh: string | null; field_id: string }>,
): string {
  return row.label_zh ?? row.field_id;
}

/** 行极值标注（D1 差异高亮）：跨工况 max/min 键（全等=双 null——无差异不高亮）。 */
export function rowExtremes(
  values: Record<string, number>,
  conditionKeys: readonly string[],
): { maxKey: string | null; minKey: string | null } {
  const entries: ReadonlyArray<readonly [string, number]> = conditionKeys.flatMap((key) => {
    const value = values[key];
    return typeof value === "number" ? [[key, value] as const] : [];
  });
  const first = entries[0];
  if (entries.length < 2 || first === undefined) {
    return { maxKey: null, minKey: null };
  }
  let maxKey = first[0];
  let minKey = first[0];
  for (const [key, value] of entries) {
    const max = values[maxKey];
    const min = values[minKey];
    if (max !== undefined && value > max) maxKey = key;
    if (min !== undefined && value < min) minKey = key;
  }
  const maxValue = values[maxKey];
  const minValue = values[minKey];
  if (maxValue === undefined || minValue === undefined || maxValue === minValue) {
    return { maxKey: null, minKey: null };
  }
  return { maxKey, minKey };
}

/** ══ 数值格式化（solutionsView §2c 同配方本层复刻——features 互禁 import）══ */

const INT_FORMAT = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const FIXED3_FORMAT = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});
const SIG3_FORMAT = new Intl.NumberFormat("en-US", {
  maximumSignificantDigits: 3,
});

/** 矩阵单元格数值显示串（整数千分位/非整数 3 位小数/小值 3 位有效数字）。 */
export function formatMetricValue(value: number): string {
  if (Number.isInteger(value)) return INT_FORMAT.format(value);
  if (value !== 0 && Math.abs(value) < 0.001) return SIG3_FORMAT.format(value);
  return FIXED3_FORMAT.format(value);
}
