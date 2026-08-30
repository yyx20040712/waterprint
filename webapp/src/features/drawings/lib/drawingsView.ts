/**
 * drawings 纯函数层：导出列表窄化门+图纸目录行模型+工况选项投影
 * （estimateView 窄化门模式第六例）。
 *
 * 输入:  GET /api/exports 响应（弱类型 unknown——orval 生成类型不进门，
 *        运行期形状逐字段校验）+cost 同端点响应（工况选项投影面）
 * 输出:  narrowExportsResponse→ExportMetaView[]（逐字段值域拒，非法抛
 *        DrawingsViewError 带键定位）+buildSheetRows→SheetRow[]（目录
 *        行模型——组件薄壳唯一数据源）+narrowConditionOptions→string[]
 *        （工况索引面——drawings/api 工况源 select 消费）
 *
 * 规格说明（FE9 批 6b 段七，D6）：
 *   - 窄化门（FE8 estimateView 同族）：ExportMeta 八字段逐类校验——
 *     kind/project_id/file_name/design_digest/engine_version/data_version
 *     非空串；condition_key 空串容忍（服务端缺省工况=空串——文件名
 *     all 分量 fallback 同源合同）；stale_labeled 严格布尔（字符串/
 *     数值/NaN 异形拒——stale 是 force 导出旧结果的显式标注面，异形
 *     禁入徽标渲染）；顶层非数组/行非对象拒；
 *   - 行模型：行序=服务端序（sorted 边车扫描序——零推导）；key=文件名
 *     （服务端确定性命名——同输入同文件名，天然行键）；design 摘要=
 *     digest 前 10 位显示层口径（服务端文件名分量同款）；工况空串→
 *     显示层 all 兜底；
 *   - 工况选项投影：cost 同端点响应的 conditions 键面（drawings/api
 *     自封装同键查询的 select 消费——非空字符串数组，空数组/空串
 *     元素拒[工况索引面——calc 结果恒有 design 档，空属服务端异形]）；
 *   - 零 antd import（node 环境测试）；零运行期库 import。
 */

/** 窄化产物（D6：单条产物元数据——ExportMeta 形状 snake 透传）。 */
export type ExportMetaView = {
  project_id: string;
  kind: string;
  condition_key: string;
  file_name: string;
  design_digest: string;
  engine_version: string;
  data_version: string;
  stale_labeled: boolean;
};

/** 图纸目录行模型（D6：SheetList 唯一数据源——显示层字段驼峰收口）。 */
export type SheetRow = {
  key: string;
  kind: string;
  conditionKey: string;
  fileName: string;
  designDigest: string;
  engineVersion: string;
  dataVersion: string;
  stale: boolean;
};

/** 窄化非法（顶层非数组/行非对象/字段值域外）——消费面错误薄壳呈现。 */
export class DrawingsViewError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DrawingsViewError";
  }
}

/** digest 显示层摘要长度（服务端文件名分量同款口径）。 */
const DIGEST_PREFIX = 10;

/** 工况空串显示层兜底（服务端文件名 all 分量同源口径）。 */
const CONDITION_FALLBACK = "all";

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function reject(message: string): never {
  throw new DrawingsViewError(message);
}

/** 非空字符串字段校验（键名进消息定位；label=行级前缀）。 */
function requireString(
  raw: Record<string, unknown>,
  key: string,
  label = key,
): string {
  const value = raw[key];
  if (typeof value !== "string" || value === "") {
    reject(
      `${label} 须为非空字符串：得到 ${JSON.stringify(value) ?? "undefined"}`,
    );
  }
  return value;
}

/** 单条产物窄化（八字段逐键——condition_key 空串容忍合同）。 */
function narrowMeta(raw: unknown, index: number): ExportMetaView {
  const face = `exports[${index}]`;
  if (!isRecord(raw)) {
    reject(`${face} 须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const conditionKey = raw["condition_key"];
  if (typeof conditionKey !== "string") {
    reject(`${face}.condition_key 须为字符串（空串=服务端缺省工况）`);
  }
  const stale = raw["stale_labeled"];
  if (typeof stale !== "boolean") {
    reject(
      `${face}.stale_labeled 须为布尔：得到 ${JSON.stringify(stale) ?? "undefined"}`,
    );
  }
  return {
    project_id: requireString(raw, "project_id", `${face}.project_id`),
    kind: requireString(raw, "kind", `${face}.kind`),
    condition_key: conditionKey,
    file_name: requireString(raw, "file_name", `${face}.file_name`),
    design_digest: requireString(raw, "design_digest", `${face}.design_digest`),
    engine_version: requireString(raw, "engine_version", `${face}.engine_version`),
    data_version: requireString(raw, "data_version", `${face}.data_version`),
    stale_labeled: stale,
  };
}

/**
 * D6 窄化门：GET /api/exports 弱类型响应 → ExportMetaView[]（逐字段拒）。
 */
export function narrowExportsResponse(raw: unknown): ExportMetaView[] {
  if (!Array.isArray(raw)) {
    reject(`exports 响应须为数组：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  return raw.map((entry, index) => narrowMeta(entry, index));
}

/**
 * D6 行模型：ExportMetaView[] → SheetRow[]（行序=服务端序零推导）。
 */
export function buildSheetRows(metas: ExportMetaView[]): SheetRow[] {
  return metas.map((meta) => ({
    key: meta.file_name,
    kind: meta.kind,
    conditionKey: meta.condition_key || CONDITION_FALLBACK,
    fileName: meta.file_name,
    designDigest: meta.design_digest.slice(0, DIGEST_PREFIX),
    engineVersion: meta.engine_version,
    dataVersion: meta.data_version,
    stale: meta.stale_labeled,
  }));
}

/**
 * D6 工况选项投影：cost 同端点响应 → conditions 索引面（非空字符串数组）。
 */
export function narrowConditionOptions(raw: unknown): string[] {
  if (!isRecord(raw)) {
    reject(`工况源响应须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const conditions = raw["conditions"];
  if (
    !Array.isArray(conditions) ||
    conditions.length === 0 ||
    !conditions.every((key) => typeof key === "string" && key !== "")
  ) {
    reject("conditions 须为非空字符串数组（工况索引面——元素空串拒）");
  }
  return conditions as string[];
}
