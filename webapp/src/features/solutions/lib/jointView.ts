/**
 * 联合枚举结果窄化门（批2d——R-B44b-4 兑现；沿 solutionsView D4 门纪律：
 * combos 载荷 unknown→类型化视图，非法形状抛 JointViewError 带定位——
 * error 呈现非静默，传输破损/缓存异形拒于渲染前）。
 *
 * 输入:  GET /api/calc/tasks/{id} result 载荷（kind=joint_enumerate 且
 *        state=done——worker _run_joint_enumerate 直返体）
 * 输出:  narrowJointResult → JointResultView（combos 类型化+diagnosis
 *        透传[DiagnosisPanel 自窄化]+unit_ids）；三键族常量（四真键/avg
 *        三键/六出水指标——core final_eval.py _METRIC_KEYS/_AVG_PREFIX/
 *        _SUMMARY_INDICATORS 镜像）+metricLabel 中文标签
 *
 * 规格说明（批2d 简报④数据形状——只读事实）：
 *   - ComboResult={params:{unit_id:{param:value}}, feasible,
 *     sensitivity_degraded, failed_conditions:[...], metrics:{...},
 *     score|null}；combos 序=score 升序（ranking 越小越好——首位=排名
 *     最高）；
 *   - metrics 数值键白名单=四真键（design）+avg. 三键（cost_opex/
 *     energy/carbon——capex 无 avg 对）+design 工况六出水指标；白名单外
 *     键=载荷异形显式拒（fail-visible——core 键面扩 member 属 spec 面
 *     变更，前端门同步升为正路，禁静默吞新键）；
 *   - metrics 子集合法（sparse 诚实面——avg 对/出水指标均可缺席）；
 *   - failed_conditions 条目 "condition_key:standard_id:IND1+IND2" 与
 *     "condition_key:opex_absent" 两式（解析面归 jointCharts.tornadoBars）；
 *   - 顶层消费面=combos/diagnosis/unit_ids 三键（search_semantics/
 *     budget_usage/project_id 本批 UI 不消费——多余键宽容不校验）；
 *   - 零运行期库 import（node 测试不拖 antd/react-query 链——type import
 *     编译期擦除；solutionsView 同款纪律）。
 */

/** 联合枚举组合视图（窄化产物——组件零形状判断）。 */
export type JointComboView = {
  params: Record<string, Record<string, number>>;
  feasible: boolean;
  sensitivity_degraded: boolean;
  failed_conditions: string[];
  metrics: Record<string, number>;
  score: number | null;
};

/** 联合枚举结果视图（顶层消费面三键）。 */
export type JointResultView = {
  combos: JointComboView[];
  /** 无解诊断载荷（worker 可下发 None→null；DiagnosisPanel 自窄化宽容面）。 */
  diagnosis: unknown;
  unit_ids: string[];
};

/** 窄化非法（顶层/条目/字段逐门拒——消息带定位，呈现面反查）。 */
export class JointViewError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "JointViewError";
  }
}

/** 四真键（design 工况——批2b：opex/energy/carbon/capex 全最小化优）。 */
export const TRUE_METRIC_KEYS = [
  "cost_opex_yuan_a",
  "power_total_kwh_d",
  "carbon_intensity_kgco2e_m3",
  "cost_capex_yuan",
] as const;

/** avg 工况附带三键（capex 无 avg 对——core final_eval.py ④事实）。 */
export const AVG_METRIC_KEYS = [
  "avg.cost_opex_yuan_a",
  "avg.power_total_kwh_d",
  "avg.carbon_intensity_kgco2e_m3",
] as const;

/** design 工况六出水指标（_SUMMARY_INDICATORS 镜像）。 */
export const INDICATOR_KEYS = ["BOD5", "CODCR", "SS", "NH3N", "TN", "TP"] as const;

/** metrics 数值键白名单（四真键+avg 三键+六出水指标）。 */
const METRIC_KEY_WHITELIST: ReadonlySet<string> = new Set<string>([
  ...TRUE_METRIC_KEYS,
  ...AVG_METRIC_KEYS,
  ...INDICATOR_KEYS,
]);

/** 指标中文标签表（四真键+avg 前缀派生+六指标+score；白名单外原样回退——dimLabel 同口径）。 */
const METRIC_LABELS: Record<string, string> = {
  cost_opex_yuan_a: "运行成本（元/年）",
  power_total_kwh_d: "能耗（kWh/d）",
  carbon_intensity_kgco2e_m3: "碳强度（kgCO₂e/m³）",
  cost_capex_yuan: "建设投资（元）",
  BOD5: "BOD5（mg/L）",
  CODCR: "CODCr（mg/L）",
  SS: "SS（mg/L）",
  NH3N: "NH₃-N（mg/L）",
  TN: "TN（mg/L）",
  TP: "TP（mg/L）",
  score: "综合得分（越小越优）",
};

/** 指标标签：avg. 前缀→「基标签·均值」；未知键原样（诚实回退不猜语义）。 */
export function metricLabel(key: string): string {
  const direct = METRIC_LABELS[key];
  if (direct !== undefined) {
    return direct;
  }
  if (key.startsWith("avg.")) {
    const base = METRIC_LABELS[key.slice("avg.".length)];
    if (base !== undefined) {
      return `${base.replace(/（(.*)）$/, "·均值（$1）")}`;
    }
  }
  return key;
}

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 有限数值判定（bool 排除——typeof 先于 number 面）。 */
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** combo 条目窄化（逐字段门——消息带 [position] 定位）。 */
function narrowCombo(raw: unknown, position: number): JointComboView {
  if (!isRecord(raw)) {
    throw new JointViewError(`联合枚举 combos[${position}] 非对象`);
  }
  const paramsRaw = raw["params"];
  if (!isRecord(paramsRaw)) {
    throw new JointViewError(`联合枚举 combos[${position}] params 非对象`);
  }
  const params: Record<string, Record<string, number>> = {};
  for (const [unitId, rowParams] of Object.entries(paramsRaw)) {
    if (!isRecord(rowParams)) {
      throw new JointViewError(
        `联合枚举 combos[${position}] params.${unitId} 非对象`,
      );
    }
    const row: Record<string, number> = {};
    for (const [param, value] of Object.entries(rowParams)) {
      if (!isFiniteNumber(value)) {
        throw new JointViewError(
          `联合枚举 combos[${position}] params.${unitId}.${param} 须为有限数`,
        );
      }
      row[param] = value;
    }
    params[unitId] = row;
  }
  if (typeof raw["feasible"] !== "boolean") {
    throw new JointViewError(`联合枚举 combos[${position}] feasible 须为布尔`);
  }
  if (typeof raw["sensitivity_degraded"] !== "boolean") {
    throw new JointViewError(
      `联合枚举 combos[${position}] sensitivity_degraded 须为布尔`,
    );
  }
  const failedRaw = raw["failed_conditions"];
  if (
    !Array.isArray(failedRaw) ||
    !failedRaw.every((item) => typeof item === "string")
  ) {
    throw new JointViewError(
      `联合枚举 combos[${position}] failed_conditions 须为字符串组`,
    );
  }
  const metricsRaw = raw["metrics"];
  if (!isRecord(metricsRaw)) {
    throw new JointViewError(`联合枚举 combos[${position}] metrics 非对象`);
  }
  const metrics: Record<string, number> = {};
  for (const [key, value] of Object.entries(metricsRaw)) {
    if (!METRIC_KEY_WHITELIST.has(key)) {
      throw new JointViewError(
        `联合枚举 combos[${position}] metrics 键越界：${key}（白名单外——core 键面扩 member 属 spec 变更）`,
      );
    }
    if (!isFiniteNumber(value)) {
      throw new JointViewError(
        `联合枚举 combos[${position}] metrics.${key} 须为有限数`,
      );
    }
    metrics[key] = value;
  }
  const scoreRaw = raw["score"];
  if (scoreRaw !== null && !isFiniteNumber(scoreRaw)) {
    throw new JointViewError(
      `联合枚举 combos[${position}] score 须为有限数或 null`,
    );
  }
  return {
    params,
    feasible: raw["feasible"],
    sensitivity_degraded: raw["sensitivity_degraded"],
    failed_conditions: failedRaw as string[],
    metrics,
    score: scoreRaw,
  };
}

/**
 * 联合枚举结果窄化正门（kind=joint_enumerate 且 state=done 的 result 载荷
 * → JointResultView；非法形状抛 JointViewError——error 态呈现非静默）。
 */
export function narrowJointResult(raw: unknown): JointResultView {
  if (!isRecord(raw)) {
    throw new JointViewError("联合枚举结果载荷非对象");
  }
  const combosRaw = raw["combos"];
  if (!Array.isArray(combosRaw)) {
    throw new JointViewError("联合枚举结果载荷 combos 须为数组");
  }
  const unitIdsRaw = raw["unit_ids"];
  if (
    !Array.isArray(unitIdsRaw) ||
    !unitIdsRaw.every((item) => typeof item === "string")
  ) {
    throw new JointViewError("联合枚举结果载荷 unit_ids 须为字符串组");
  }
  return {
    combos: combosRaw.map((item, position) => narrowCombo(item, position)),
    diagnosis: raw["diagnosis"] ?? null,
    unit_ids: unitIdsRaw as string[],
  };
}
