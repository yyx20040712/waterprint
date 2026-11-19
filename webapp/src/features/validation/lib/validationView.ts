/**
 * validation 视图纯函数层：窄化门+警告三分区+severity 语义色/影响面中文
 * 标签（消费 /api/calc/validation 响应——T3 前端警告聚合批）。
 *
 * 输入:  orval 生成 ValidationObservationResponse（server services.validation
 *        两源聚合投影——docs/archive/warning-aggregation.md §1~§3 冻结规格）
 * 输出:  narrowValidationObservation 窄化门（非法形状抛 ValidationViewError）+
 *        partitionWarnings 三分区纯函数（声明级 ∅ 哨兵/工况聚合 ≥2/单工况
 *        直通——§3 分区规则逐条绑定）+severityTone/severityLabel 警告级
 *        语义色与中文徽标+scopeLabel 影响面标签+conditionKeysText 工况键
 *        紧凑文案（中列窄面板单行 meta）
 *
 * 规格说明（warning-aggregation.md §3/§5——分区与聚合归属条款）：
 *   - 窄化门逐字段校验（顶层 11 键+warnings 行对象形/键域/severity 三值域
 *     ——null/裸标量行同拒带 index 定位）——非法形状→查询 error 态呈现
 *     （trustView 窄化门同构先例，禁带病渲染）；
 *   - 分区判据（§3）：condition_keys=∅（源 A 声明级哨兵）→声明级区，不与
 *     工况区混排；命中工况 ≥2 →工况聚合区；单工况命中=直通行（同 schema，
 *     视图位次在聚合区后）；
 *   - 服务端响应行已按 (scope,code,param_key) 排序冻结（§5 A3）——分区=
 *     稳定过滤零重排（区内序=服务端序，确定性）；客户端零去重（服务端
 *     已聚合，§5 单一口径条款）；
 *   - v1 只消费 warnings 聚合行+validation_available 降级位；nodes 观测面
 *     不消费（窄化仅守数组形——深校验归后续消费批扩面）。
 */

/** 窄化门拒绝（非法响应形状——查询 error 态呈现）。 */
export class ValidationViewError extends Error {
  constructor(detail: string) {
    super(`校验观测形状非法：${detail}（server/services/validation 契约漂移？）`);
    this.name = "ValidationViewError";
  }
}

/** 警告级别（server Severity 三值域镜像——D3 字面量冻结）。 */
export type WarningSeverity = "INFO" | "WARN" | "ERROR";

/** 聚合警告行（§3 行 schema——去重键三元组+命中清单+severity 分级）。 */
export type AggregatedWarningRow = {
  code: string;
  param_key: string;
  scope: string;
  message: string;
  condition_keys: string[];
  severity: WarningSeverity;
};

/** 窄化产物（v1 消费面：warnings+validation_available；nodes 不消费）。 */
export type ValidationObservation = {
  project_id: string;
  task_id: string;
  stale: boolean;
  design_hash: string;
  engine_version: string;
  data_version: string;
  kb_injected: boolean | null;
  validation_available: boolean;
  conditions: string[];
  /** 观测面（R5）——v1 零消费（T3 用户定案：仅聚合行），守形不守义。 */
  nodes: readonly unknown[];
  warnings: AggregatedWarningRow[];
};

const TOP_KEYS: readonly string[] = [
  "project_id", "task_id", "stale", "design_hash", "engine_version",
  "data_version", "kb_injected", "validation_available", "conditions",
  "nodes", "warnings",
];

const STRING_KEYS: readonly string[] = [
  "project_id", "task_id", "design_hash", "engine_version", "data_version",
];

const SEVERITIES: readonly WarningSeverity[] = ["INFO", "WARN", "ERROR"];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** 窄化门：顶层 11 键+warnings 行键域逐项校验（非法抛 ValidationViewError）。 */
export function narrowValidationObservation(raw: unknown): ValidationObservation {
  if (!isRecord(raw)) throw new ValidationViewError("顶层非对象");
  for (const key of TOP_KEYS) {
    if (!(key in raw)) throw new ValidationViewError(`顶层缺 ${key}`);
  }
  for (const key of STRING_KEYS) {
    if (typeof raw[key] !== "string") throw new ValidationViewError(`${key} 非字符串`);
  }
  if (typeof raw["stale"] !== "boolean") {
    throw new ValidationViewError("stale 非布尔");
  }
  if (typeof raw["validation_available"] !== "boolean") {
    throw new ValidationViewError("validation_available 非布尔");
  }
  if (typeof raw["kb_injected"] !== "boolean" && raw["kb_injected"] !== null) {
    throw new ValidationViewError("kb_injected 非布尔|null");
  }
  if (
    !Array.isArray(raw["conditions"]) ||
    raw["conditions"].some((item) => typeof item !== "string")
  ) {
    throw new ValidationViewError("conditions 非字符串数组");
  }
  if (!Array.isArray(raw["nodes"])) {
    throw new ValidationViewError("nodes 非数组");
  }
  if (!Array.isArray(raw["warnings"])) {
    throw new ValidationViewError("warnings 非数组");
  }
  const warnings = raw["warnings"] as unknown[];
  warnings.forEach((item, index) => {
    // 先守对象形再取键（null/裸标量行禁裸 TypeError——窄化门契约：
    // 一切非法形状抛 ValidationViewError 带定位）
    if (!isRecord(item)) {
      throw new ValidationViewError(`warnings[${index}] 非对象`);
    }
    if (
      typeof item["code"] !== "string" || typeof item["param_key"] !== "string" ||
      typeof item["scope"] !== "string" || typeof item["message"] !== "string" ||
      !Array.isArray(item["condition_keys"]) ||
      (item["condition_keys"] as unknown[]).some((key) => typeof key !== "string") ||
      !SEVERITIES.includes(item["severity"] as WarningSeverity)
    ) {
      throw new ValidationViewError(`warnings[${index}] 键域非法`);
    }
  });
  return raw as unknown as ValidationObservation;
}

/** 三分区（§3——空分区由呈现件不渲染，此处如实交付空数组）。 */
export type WarningZones = {
  /** 声明级区（源 A ∅ 哨兵行——与工况区不混排）。 */
  declaration: AggregatedWarningRow[];
  /** 工况聚合区（源 B 命中工况 ≥2——去重价值面恰在重复）。 */
  aggregated: AggregatedWarningRow[];
  /** 单工况直通区（命中工况=1——位次在聚合区后）。 */
  single: AggregatedWarningRow[];
};

/** 聚合行三分区（§3 判据：∅ 哨兵/≥2/单工况；区内序=服务端 (scope,code,
 *  param_key) 冻结序稳定过滤——零重排零去重）。 */
export function partitionWarnings(
  warnings: readonly AggregatedWarningRow[],
): WarningZones {
  const zones: WarningZones = { declaration: [], aggregated: [], single: [] };
  for (const row of warnings) {
    if (row.condition_keys.length === 0) {
      zones.declaration.push(row);
    } else if (row.condition_keys.length >= 2) {
      zones.aggregated.push(row);
    } else {
      zones.single.push(row);
    }
  }
  return zones;
}

/** 警告级语义色（EffluentTable 判定徽标/StaleBanner 黄条同款 token：
 *  ERROR=--wp-error+浅红底/WARN=--wp-warning+黄底/INFO=次级灰）。 */
export function severityTone(
  severity: WarningSeverity,
): { color: string; background: string } {
  if (severity === "ERROR") {
    return { color: "var(--wp-error)", background: "var(--wp-error-soft)" };
  }
  if (severity === "WARN") {
    return {
      color: "var(--wp-warning)",
      background: "var(--wp-warning-soft, rgba(138, 97, 0, 0.08))",
    };
  }
  return { color: "var(--wp-text-2)", background: "transparent" };
}

/** 警告级中文徽标（显示层词典——域值不进正文）。 */
export function severityLabel(severity: WarningSeverity): string {
  if (severity === "ERROR") return "错误";
  if (severity === "WARN") return "警告";
  return "提示";
}

/** 影响面标签（scope="plant"=「全厂」，否则节点 ID 原样——§1 影响面轴）。 */
export function scopeLabel(scope: string): string {
  return scope === "plant" ? "全厂" : scope;
}

/** 工况键紧凑文案：∅=空串（声明级无工况轴）/单键直书/多键=清单+计数。 */
export function conditionKeysText(keys: readonly string[]): string {
  if (keys.length === 0) return "";
  if (keys.length === 1) return `工况 ${keys[0] ?? ""}`;
  return `工况 ${keys.join("、")}（${keys.length}）`;
}
