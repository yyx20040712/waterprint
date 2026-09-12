/**
 * solutions 纯函数层：SolutionPage 窄化门+动态列模型+apply 载荷+排序选项
 * +数值格式化。
 *
 * 输入:  solutions 分页响应（弱类型 unknown——生成模型 rows 行为纯弱类型
 *        {[key:string]:unknown}）+gridFields（任务 result 载荷）+行/项目/单元
 * 输出:  五纯函数族（narrowSolutionPage→SolutionPageView 窄化产物/
 *        buildTableColumns→SolutionColumnModel[] 列模型/buildApplyPayload→
 *        ApplyRequest 载荷/buildSortOptions→排序选项/formatSolutionValue→
 *        工程数值显示串；非法形状抛 SolutionsViewError 带键定位）
 *
 * 规格说明（FE6 批 6b 段四，D4/D5/D6/D9；B2 扩面；C2 方案表重制
 *   2026-09-10——briefs/task-C2-plan.md §2b/§2c）：
 *   - D4 窄化门（FE4 D6/FE5 D8 门模式复用）：顶层七字段（task_id/page/
 *     size/total/sort/columns/rows）逐类校验；columns 轻门=非空 string[]
 *     （SolutionPage 无 format_version——版本无关轻门）；行=Record<string,
 *     number|string|boolean|null>（值域四类拒其余——nan_flag 布尔列服务端
 *     pd.isna 面原样下发 true/false，D4「三类」笔误记档以服务端事实为准；
 *     NaN 服务端已转 null——非有限数按非法拒）；非法形状抛
 *     SolutionsViewError（消息带键定位——呈现面可反查）；
 *   - D5 列模型动态：kind 分类固定列名优先（margin_min→margin/nan_flag→
 *     flag/condition_key→text——与 gridFields 无关），gridFields 集内→grid
 *     （可应用标识），其余=dim 输出；numeric=数字列（grid/dim/margin——
 *     组件面 tabular-nums §19.3）；列序=响应序（服务端构造序：grid 先→
 *     dim→margin_min/nan_flag/condition_key——前端不重排）；B2（PD9）：
 *     列模型带 title/unit 两字段——grid 列 title=label_zh（降级 key）+
 *     unit=dim 单位段（C2 两行表头制：title 回归纯标签，单位不再拼串——
 *     拼串形态仅存 buildSortOptions[Select 单行场景]）；C2 固定列名中文
 *     化扩面三列（沿 PD9 模式）：margin_min→「最小裕量」/nan_flag→
 *     「可行性」/condition_key→「工况条件」（无量纲/无元数据——unit 恒
 *     空串）；非 grid 列维持 key 现状；
 *   - D6 apply 载荷=grid 字段投影（dim 输出不可应用——ADR-005 单单元
 *     语义；params 值全 number：grid 值非数值（null/string/boolean）跳过
 *     不进载荷）；gridFields 空=空 params 合法载荷（服务端 design_changed=
 *     false 面）；ApplyRequest 类型只从 generated/ 取（禁手写双份）；
 *     B2②：gridFields 签名扩 GridField[]（对象载荷）——仅投影 key，
 *     键序不变零行为差；
 *   - D9 排序选项=响应 columns 白名单（服务端 422 拒白名单外——前端只出
 *     columns 内选项；cost 列现状无列不加——概算注入挂账；服务端恒降序
 *     ascending=False 默认，UI 不提供方向切换）；B2（PD10）：grid 列
 *     label 中文化与列头同文案（防同列两处两语），非 grid=label=key；
 *   - C2 数值格式化 formatSolutionValue（§2c）：整数→千分位零小数；
 *     非整数且 |v|≥0.001→千分位恒 3 位小数（尾零补齐——列内小数位对
 *     齐，glm R1 采纳）；0<|v|<0.001→3 位有效数字；实现=Intl.Number
 *     Format("en-US") 三实例（模块级复用）——非手写 toFixed 拼接；负号
 *     ASCII 连字符（U+2212 排版优化记档不采——复制粘贴数据保真优先）；
 *     16 位浮点全精度经组件面 title 悬浮保留；
 *   - 零运行期库 import（node 测试不拖 antd/react-query 链——type import
 *     编译期擦除；运行期 import 仅本地零依赖纯件 shared/dimLabels 与
 *     ./solutionsFields——node 测试链零增重；Intl=运行期全局非 import）。
 */
import type { ApplyRequest } from "../../../shared/api/generated/model";
import { dimLabel } from "../../../shared/dimLabels";
import type { GridField } from "./solutionsFields";

/** 方案行（值域四类：grid/dim 数值列、condition_key 字符串、nan_flag 布尔、NaN→null）。 */
export type SolutionRow = Record<string, number | string | boolean | null>;

/** 窄化产物（D4：solutions 消费面的唯一分页投影面）。 */
export type SolutionPageView = {
  task_id: string;
  page: number;
  size: number;
  total: number;
  sort: string;
  columns: string[];
  rows: SolutionRow[];
};

/** 窄化非法（顶层逐类拒/行值域外）——消费面错误薄壳呈现。 */
export class SolutionsViewError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SolutionsViewError";
  }
}

/** 列模型 kind（D5 语义面：margin 语义色/flag 可行性标记/grid 可应用标识）。 */
export type SolutionColumnKind = "grid" | "dim" | "margin" | "flag" | "text";

/** 动态列模型（纯数据——组件面映射 antd Table columns）。 */
export type SolutionColumnModel = {
  key: string;
  /** 列头文案（C2 两行制：纯标签——label_zh 降级 key/固定列名中文；单位在 unit 字段）。 */
  title: string;
  /** 单位段（C2：grid 列=dimUnitOf(dim)——空串=无单位副行；固定/dim 列恒空）。 */
  unit: string;
  kind: SolutionColumnKind;
  /** 数字列（组件面 fontVariantNumeric: tabular-nums §19.3）。 */
  numeric: boolean;
  /** grid 字段=可应用标识（D6 apply 投影面）。 */
  applicable: boolean;
};

/** C2 固定列名中文映射（沿 B2 PD9 模式扩面；原 key 悬浮呈现防两行重复）。 */
const FIXED_TITLES: Record<string, string> = {
  margin_min: "最小裕量",
  nan_flag: "可行性",
  condition_key: "工况条件",
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 有限数值判定（bool 排除——typeof boolean 先于 number 面）。 */
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function reject(message: string): never {
  throw new SolutionsViewError(message);
}

/**
 * D4 窄化门：solutions 分页弱类型响应 → SolutionPageView（顶层逐类拒）。
 */
export function narrowSolutionPage(raw: unknown): SolutionPageView {
  if (!isRecord(raw)) {
    reject(
      `方案分页须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`,
    );
  }
  const taskId = raw["task_id"];
  if (typeof taskId !== "string" || taskId === "") {
    reject(`task_id 须为非空字符串：得到 ${JSON.stringify(taskId) ?? "undefined"}`);
  }
  const page = raw["page"];
  if (typeof page !== "number" || !Number.isInteger(page) || page < 1) {
    reject(`page 须为 >=1 整数（1 基页码）：得到 ${JSON.stringify(page) ?? "undefined"}`);
  }
  const size = raw["size"];
  if (typeof size !== "number" || !Number.isInteger(size) || size < 1) {
    reject(`size 须为 >=1 整数：得到 ${JSON.stringify(size) ?? "undefined"}`);
  }
  const total = raw["total"];
  if (typeof total !== "number" || !Number.isInteger(total) || total < 0) {
    reject(`total 须为 >=0 整数：得到 ${JSON.stringify(total) ?? "undefined"}`);
  }
  const sort = raw["sort"];
  if (typeof sort !== "string") {
    reject(`sort 须为字符串：得到 ${JSON.stringify(sort) ?? "undefined"}`);
  }
  const columnsRaw = raw["columns"];
  if (!Array.isArray(columnsRaw) || columnsRaw.length === 0) {
    reject(`columns 须为非空数组（轻门=非空 string[]）：得到 ${JSON.stringify(columnsRaw) ?? "undefined"}`);
  }
  columnsRaw.forEach((column, index) => {
    if (typeof column !== "string") {
      reject(`columns[${index}] 须为字符串：得到 ${JSON.stringify(column) ?? "undefined"}`);
    }
  });
  const rowsRaw = raw["rows"];
  if (!Array.isArray(rowsRaw)) {
    reject(`rows 须为数组：得到 ${JSON.stringify(rowsRaw) ?? "undefined"}`);
  }
  rowsRaw.forEach((row, rowIndex) => {
    if (!isRecord(row)) {
      reject(`rows[${rowIndex}] 须为对象（行记录）：得到 ${JSON.stringify(row) ?? "undefined"}`);
    }
    for (const [key, value] of Object.entries(row)) {
      if (
        value === null ||
        typeof value === "string" ||
        typeof value === "boolean" ||
        isFiniteNumber(value)
      ) {
        continue;
      }
      reject(
        `rows[${rowIndex}].${key} 值域外（须 number|string|boolean|null）：得到 `
          + `${JSON.stringify(value) ?? "undefined"}`,
      );
    }
  });
  return {
    task_id: taskId,
    page,
    size,
    total,
    sort,
    columns: [...columnsRaw],
    rows: rowsRaw as SolutionRow[],
  };
}

/** dim 单位段：dimLabel 输出「量名 单位」的空格后段（无量纲/未知枚举
 * 无单位段——单位符号串零空格为 CANONICAL_UNITS 真源约定；纯显示层
 * 派生，不建第二单位真源）。 */
function dimUnitOf(dim: string): string {
  const label = dimLabel(dim);
  const at = label.indexOf(" ");
  return at === -1 ? "" : label.slice(at + 1);
}

/** grid 列头文案（PD9/PD10 单源；R 轮 G2-03 记档：C2 起仅 sort 选项
 * 消费——表头两行制改走 title+unit 双字段不经此函数）：「label_zh
 * 单位」——label_zh=null 降级 key（显示层兜底）；无单位段不附后缀。 */
function gridColumnTitle(field: GridField): string {
  const base = field.label_zh ?? field.key;
  const unit = dimUnitOf(field.dim);
  return unit === "" ? base : `${base} ${unit}`;
}

/**
 * D5 动态列模型：响应 columns → ColumnModel[]（列序=响应序；固定列名
 * kind 分类优先于 gridFields 判定——margin_min 等语义列不可被覆盖；
 * C2：title 纯标签+unit 单位段两行制，固定列名中文映射；V2 GOV5 批尾：
 * dim 列族中文名=dimFields（manifest.out_dims 声明面真源）降级 key）。
 */
export function buildTableColumns(
  columns: string[],
  gridFields: GridField[],
  dimFields: GridField[] = [],
): SolutionColumnModel[] {
  const gridByKey = new Map(gridFields.map((field) => [field.key, field]));
  const dimByKey = new Map(dimFields.map((field) => [field.key, field]));
  return columns.map((key) => {
    if (key === "margin_min") {
      return {
        key,
        title: FIXED_TITLES["margin_min"] ?? key,
        unit: "",
        kind: "margin",
        numeric: true,
        applicable: false,
      };
    }
    if (key === "nan_flag") {
      return {
        key,
        title: FIXED_TITLES["nan_flag"] ?? key,
        unit: "",
        kind: "flag",
        numeric: false,
        applicable: false,
      };
    }
    if (key === "condition_key") {
      return {
        key,
        title: FIXED_TITLES["condition_key"] ?? key,
        unit: "",
        kind: "text",
        numeric: false,
        applicable: false,
      };
    }
    const field = gridByKey.get(key);
    if (field !== undefined) {
      return {
        key,
        title: field.label_zh ?? field.key,
        unit: dimUnitOf(field.dim),
        kind: "grid",
        numeric: true,
        applicable: true,
      };
    }
    // V2 GOV5 批尾（视觉验收批注②）：dim 列（计算派生输出量）——
    // manifest.out_dims 声明面中文名+单位；未声明键降级 key（B2 PD9
    // 同制：title≠key 时悬浮 title 呈原 key 追溯链）。
    const outField = dimByKey.get(key);
    if (outField !== undefined) {
      return {
        key,
        title: outField.label_zh ?? key,
        unit: dimUnitOf(outField.dim),
        kind: "dim",
        numeric: true,
        applicable: false,
      };
    }
    return { key, title: key, unit: "", kind: "dim", numeric: true, applicable: false };
  });
}

/** ══ C2 数值格式化（§2c——Intl 三实例模块级复用）══ */

/** 整数支：千分位零小数（12480→12,480；6→6）。 */
const INT_FORMAT = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

/** 定点支：千分位恒 3 位小数（2129.0928751763995→2,129.093；1.5→1.500）。 */
const FIXED3_FORMAT = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

/** 小值支（0<|v|<0.001）：3 位有效数字（0.00012345→0.000123）。 */
const SIG3_FORMAT = new Intl.NumberFormat("en-US", {
  maximumSignificantDigits: 3,
});

/**
 * C2 工程数值显示串（§2c）：整数千分位/非整数恒 3 位小数/小值 3 位有效
 * 数字——16 位浮点直出根除（全精度经组件面 title 悬浮保留）。
 */
export function formatSolutionValue(value: number): string {
  if (Number.isInteger(value)) {
    return INT_FORMAT.format(value);
  }
  if (value !== 0 && Math.abs(value) < 0.001) {
    return SIG3_FORMAT.format(value);
  }
  return FIXED3_FORMAT.format(value);
}

/**
 * D6 apply 载荷：行+gridFields → {project_id, unit_id, params}（仅 grid
 * 字段投影——dim 输出不可应用；grid 值非有限数值跳过不进 params；
 * B2②对象数组签名仅投影 key——键序不变零行为差）。
 */
export function buildApplyPayload(
  row: SolutionRow,
  gridFields: GridField[],
  projectId: string,
  unitId: string,
): ApplyRequest {
  const params: Record<string, number> = {};
  for (const field of gridFields) {
    const value = row[field.key];
    if (isFiniteNumber(value)) {
      params[field.key] = value;
    }
  }
  return { project_id: projectId, unit_id: unitId, params };
}

/**
 * D9 排序选项：响应 columns → Select 选项（白名单=columns∪{cost}——前端
 * 只出 columns 内选项，cost 列现状无列不加）；B2 PD10：grid 列 label
 * 中文化与列头同文案（gridColumnTitle 单源），非 grid=label=key；C2：
 * 固定列名同 FIXED_TITLES 中文映射（同列两处两语防线沿 PD10 精神）。
 */
export function buildSortOptions(
  columns: string[],
  gridFields: GridField[],
): { value: string; label: string }[] {
  const gridByKey = new Map(gridFields.map((field) => [field.key, field]));
  return columns.map((column) => {
    // R 轮 A2-N-02：固定列名优先于 gridFields 判定（与 buildTableColumns
    // 的 kind 分类优先口径对齐——病态重名 gridFields 下同列两处两语防线）
    const fixed = FIXED_TITLES[column];
    if (fixed !== undefined) {
      return { value: column, label: fixed };
    }
    const field = gridByKey.get(column);
    return {
      value: column,
      label: field === undefined ? column : gridColumnTitle(field),
    };
  });
}
