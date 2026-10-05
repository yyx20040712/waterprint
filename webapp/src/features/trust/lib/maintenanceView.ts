/**
 * maintenance 观测视图纯函数层：窄化门+降级态判定+格式化（消费
 * /api/calc/validation 响应——2A1 消费批 UF-61① FE 面数据源）。
 *
 * 输入:  orval 生成 ValidationObservationResponse（server services.validation
 *        观测投影+两源聚合）
 * 输出:  narrowValidationObservation 窄化门（非法形状抛 MaintenanceViewError）
 *        +observationDegradation 降级态判定（kb 未注入/val 件缺席/空态）+
 *        nodeFailed 节点故障灯+formatRatio/formatFixgeom 数值格式化
 *
 * 规格说明（2A1 消费批；trustView 窄化门同构先例）：
 *   - 窄化门逐字段校验（顶层 11 键+nodes/faces/warnings 条目键域）——
 *     非法形状→查询 error 态呈现（禁带病渲染半张面板）；
 *   - 本层零消费 warnings 聚合行（聚合行 FE 渲染=T3 批面——UF-18 登记
 *     册口径；窄化门仅校验形状不投影行内容）；
 *   - kb_injected=null=diag 件缺席不可知（禁伪造 False——server 同口径）；
 *   - ratio=offline/design 分化键原值（×N 形文案）；fixgeom_min<0=固定
 *     几何超载深度（归一裕度）。
 */

/** 窄化门拒绝（非法响应形状——查询 error 态呈现）。 */
export class MaintenanceViewError extends Error {
  constructor(detail: string) {
    super(`校验观测报告形状非法：${detail}（server/services/validation 契约漂移？）`);
    this.name = "MaintenanceViewError";
  }
}

/** orval 生成类型再导出（组件面单点 import）。 */
export type MaintenanceFace = {
  condition_key: string;
  kb: Record<string, boolean>;
  any_fail: boolean;
  ratio: Record<string, number>;
  fixgeom_min: number | null;
};

export type NodeObservation = {
  node_id: string;
  faces: MaintenanceFace[];
};

export type AggregatedWarningRow = {
  code: string;
  param_key: string;
  scope: string;
  message: string;
  condition_keys: string[];
  severity: string;
};

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
  nodes: NodeObservation[];
  warnings: AggregatedWarningRow[];
};

const TOP_KEYS: readonly string[] = [
  "project_id", "task_id", "stale", "design_hash", "engine_version",
  "data_version", "kb_injected", "validation_available", "conditions",
  "nodes", "warnings",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

function isStringRecord(
  value: unknown,
  leaf: "boolean" | "number",
): boolean {
  return (
    isRecord(value) &&
    Object.values(value).every((item) => typeof item === leaf)
  );
}

/** 窄化门：顶层 11 键+nodes/faces/warnings 条目键域逐项校验（非法抛错）。 */
export function narrowValidationObservation(raw: unknown): ValidationObservation {
  if (!isRecord(raw)) throw new MaintenanceViewError("顶层非对象");
  for (const key of TOP_KEYS) {
    if (!(key in raw)) throw new MaintenanceViewError(`顶层缺 ${key}`);
  }
  const observation = raw as unknown as ValidationObservation;
  if (typeof observation.stale !== "boolean") {
    throw new MaintenanceViewError("stale 非布尔");
  }
  if (
    observation.kb_injected !== null &&
    typeof observation.kb_injected !== "boolean"
  ) {
    throw new MaintenanceViewError("kb_injected 非布尔/null");
  }
  if (typeof observation.validation_available !== "boolean") {
    throw new MaintenanceViewError("validation_available 非布尔");
  }
  if (
    !Array.isArray(observation.conditions) ||
    !observation.conditions.every((item) => typeof item === "string")
  ) {
    throw new MaintenanceViewError("conditions 非字符串数组");
  }
  if (!Array.isArray(observation.nodes)) {
    throw new MaintenanceViewError("nodes 非数组");
  }
  observation.nodes.forEach((node, nodeIndex) => {
    if (typeof node.node_id !== "string" || !Array.isArray(node.faces)) {
      throw new MaintenanceViewError(`nodes[${nodeIndex}] 键域非法`);
    }
    node.faces.forEach((face, faceIndex) => {
      if (
        typeof face.condition_key !== "string" ||
        !isStringRecord(face.kb, "boolean") ||
        typeof face.any_fail !== "boolean" ||
        !isStringRecord(face.ratio, "number") ||
        !(face.fixgeom_min === null || typeof face.fixgeom_min === "number")
      ) {
        throw new MaintenanceViewError(
          `nodes[${nodeIndex}].faces[${faceIndex}] 键域非法`,
        );
      }
    });
  });
  if (!Array.isArray(observation.warnings)) {
    throw new MaintenanceViewError("warnings 非数组");
  }
  observation.warnings.forEach((row, index) => {
    if (
      typeof row.code !== "string" || typeof row.param_key !== "string" ||
      typeof row.scope !== "string" || typeof row.message !== "string" ||
      typeof row.severity !== "string" ||
      !Array.isArray(row.condition_keys) ||
      !row.condition_keys.every((item) => typeof item === "string")
    ) {
      throw new MaintenanceViewError(`warnings[${index}] 键域非法`);
    }
  });
  return observation;
}

/** 观测面降级三态（kb 未注入注记/val 件缺席降级/无可观测工况空态）。 */
export function observationDegradation(observation: ValidationObservation): {
  kbMissing: boolean;
  valMissing: boolean;
  noObservableFaces: boolean;
} {
  return {
    kbMissing: observation.kb_injected === false,
    valMissing: !observation.validation_available,
    noObservableFaces:
      observation.nodes.every((node) => node.faces.length === 0),
  };
}

/** 节点故障灯：任一工况 any_fail（节点头检修越门指示）。 */
export function nodeFailed(node: NodeObservation): boolean {
  return node.faces.some((face) => face.any_fail);
}

/** ratio 值文案：×2.000 形（offline/design 比值——分化键原值直呈）。 */
export function formatRatio(value: number): string {
  return `×${value.toFixed(3)}`;
}

/** fixgeom 文案：归一裕度两位小数（<0=固定几何超载深度——负号 ASCII）。 */
export function formatFixgeom(value: number): string {
  return value.toFixed(2);
}
