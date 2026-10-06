/**
 * sensitivity 视图纯函数层：窄化门（批6e——消费 /api/calc/sensitivity
 * 响应；compareView 窄化门同构先例：orval 生成类型 unknown 入→类型化
 * 视图出，非法形状抛 SensitivityViewError 带定位——error 呈现非静默）。
 *
 * 输入:  /api/calc/sensitivity/{project_id} 响应载荷（server
 *        services.sensitivity 聚合投影——design_offline_* 指标差全量）
 * 输出:  narrowSensitivityResponse 窄化门+SensitivityReportView 类型
 *        （组件面单点 import；stale/design_hash=§12 快照绑定呈现面）
 *
 * 规格说明（批6e 设计档 §四；compareView 同构纪律）：
 *   - 顶层 9 键逐项校验（缺一拒——server/services/sensitivity 契约
 *     漂移面 fail-visible）；rows 条目四键域校验；
 *   - condition_keys 条目前缀=design_offline_（GR-20 冻结字面量镜像
 *     ——jointView 键族镜像同款纪律；非此前缀=契约漂移拒）；
 *   - 消费面裁剪：视图只携 FE 消费的四键面（stale/design_hash/
 *     condition_keys/rows）——溯源三元组/task_id 归 compare 同款锁定
 *     基准面消费，本面不重复取用（结构校验仍全键在场）；
 *   - 零运行期库 import（node 测试零增重——jointView 同款纪律）。
 */

/** 窄化门拒绝（非法响应形状——查询 error 态呈现）。 */
export class SensitivityViewError extends Error {
  constructor(detail: string) {
    super(`全工况投影报告形状非法：${detail}（server/services/sensitivity 契约漂移？）`);
    this.name = "SensitivityViewError";
  }
}

/** 幅度行视图（summary 平键 → 基线值+逐检修工况值与差）。 */
export type SensitivityRowView = {
  field_id: string;
  design_value: number;
  values: Record<string, number>;
  deltas: Record<string, number>;
};

/** 全工况投影报告视图（FE 消费面四键——§批6e）。 */
export type SensitivityReportView = {
  stale: boolean;
  design_hash: string;
  condition_keys: string[];
  rows: SensitivityRowView[];
};

/** GR-20 冻结前缀（core contracts.condition key() 拼接规则镜像——
 *  jointCharts 检修系列标签剥离消费同源）。 */
export const OFFLINE_PREFIX = "design_offline_";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireString(container: Record<string, unknown>, key: string): string {
  if (typeof container[key] !== "string") throw new SensitivityViewError(`${key} 非字符串`);
  return container[key] as string;
}

function requireNumberRecord(
  value: unknown,
  where: string,
): Record<string, number> {
  if (!isRecord(value)) throw new SensitivityViewError(`${where} 非对象`);
  for (const [key, entry] of Object.entries(value)) {
    if (typeof entry !== "number" || !Number.isFinite(entry)) {
      throw new SensitivityViewError(`${where}[${key}] 非有限数值`);
    }
  }
  return value as Record<string, number>;
}

/** 窄化门：顶层 9 键+行条目四键域+工况键前缀逐项校验（非法抛错）。 */
export function narrowSensitivityResponse(raw: unknown): SensitivityReportView {
  if (!isRecord(raw)) throw new SensitivityViewError("顶层非对象");
  const topKeys = [
    "project_id", "task_id", "stale", "design_hash", "engine_version",
    "data_version", "baseline_key", "condition_keys", "rows",
  ];
  for (const key of topKeys) {
    if (!(key in raw)) throw new SensitivityViewError(`顶层缺 ${key}`);
  }
  if (typeof raw.stale !== "boolean") throw new SensitivityViewError("stale 非布尔");
  const designHash = requireString(raw, "design_hash");
  if (!Array.isArray(raw.condition_keys)) {
    throw new SensitivityViewError("condition_keys 非数组");
  }
  for (const key of raw.condition_keys) {
    if (typeof key !== "string" || !key.startsWith(OFFLINE_PREFIX)) {
      throw new SensitivityViewError(`工况键 ${String(key)} 非 ${OFFLINE_PREFIX} 前缀`);
    }
  }
  if (!Array.isArray(raw.rows)) throw new SensitivityViewError("rows 非数组");
  const rows: SensitivityRowView[] = raw.rows.map((entry, index) => {
    if (!isRecord(entry)) throw new SensitivityViewError(`rows[${index}] 非对象`);
    for (const key of ["field_id", "design_value", "values", "deltas"]) {
      if (!(key in entry)) throw new SensitivityViewError(`rows[${index}] 缺 ${key}`);
    }
    if (typeof entry.design_value !== "number" || !Number.isFinite(entry.design_value)) {
      throw new SensitivityViewError(`rows[${index}].design_value 非有限数值`);
    }
    return {
      field_id: requireString(entry, "field_id"),
      design_value: entry.design_value as number,
      values: requireNumberRecord(entry.values, `rows[${index}].values`),
      deltas: requireNumberRecord(entry.deltas, `rows[${index}].deltas`),
    };
  });
  return {
    stale: raw.stale,
    design_hash: designHash,
    condition_keys: [...raw.condition_keys as string[]],
    rows,
  };
}
