/**
 * solutions 纯函数层：SolutionPage 窄化门+动态列模型+apply 载荷+排序选项。
 *
 * 输入:  solutions 分页响应（弱类型 unknown——生成模型 rows 行为纯弱类型
 *        {[key:string]:unknown}）+gridFields（任务 result 载荷）+行/项目/单元
 * 输出:  四纯函数族（narrowSolutionPage→SolutionPageView 窄化产物/
 *        buildTableColumns→SolutionColumnModel[] 列模型/buildApplyPayload→
 *        ApplyRequest 载荷/buildSortOptions→排序选项；非法形状抛
 *        SolutionsViewError 带键定位）
 *
 * 规格说明（FE6 批 6b 段四，D4/D5/D6/D9）：
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
 *     dim→margin_min/nan_flag/condition_key——前端不重排）；
 *   - D6 apply 载荷=grid 字段投影（dim 输出不可应用——ADR-005 单单元
 *     语义；params 值全 number：grid 值非数值（null/string/boolean）跳过
 *     不进载荷）；gridFields 空=空 params 合法载荷（服务端 design_changed=
 *     false 面）；ApplyRequest 类型只从 generated/ 取（禁手写双份）；
 *   - D9 排序选项=响应 columns 白名单（服务端 422 拒白名单外——前端只出
 *     columns 内选项；cost 列现状无列不加——概算注入挂账；服务端恒降序
 *     ascending=False 默认，UI 不提供方向切换）；
 *   - 零运行期库 import（node 测试不拖 antd/react-query 链——type import
 *     编译期擦除）。
 */
import type { ApplyRequest } from "../../../shared/api/generated/model";

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
  kind: SolutionColumnKind;
  /** 数字列（组件面 fontVariantNumeric: tabular-nums §19.3）。 */
  numeric: boolean;
  /** grid 字段=可应用标识（D6 apply 投影面）。 */
  applicable: boolean;
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

/**
 * D5 动态列模型：响应 columns → ColumnModel[]（列序=响应序；固定列名
 * kind 分类优先于 gridFields 判定——margin_min 等语义列不可被覆盖）。
 */
export function buildTableColumns(
  columns: string[],
  gridFields: string[],
): SolutionColumnModel[] {
  const gridSet = new Set(gridFields);
  return columns.map((key) => {
    if (key === "margin_min") {
      return { key, kind: "margin", numeric: true, applicable: false };
    }
    if (key === "nan_flag") {
      return { key, kind: "flag", numeric: false, applicable: false };
    }
    if (key === "condition_key") {
      return { key, kind: "text", numeric: false, applicable: false };
    }
    if (gridSet.has(key)) {
      return { key, kind: "grid", numeric: true, applicable: true };
    }
    return { key, kind: "dim", numeric: true, applicable: false };
  });
}

/**
 * D6 apply 载荷：行+gridFields → {project_id, unit_id, params}（仅 grid
 * 字段投影——dim 输出不可应用；grid 值非有限数值跳过不进 params）。
 */
export function buildApplyPayload(
  row: SolutionRow,
  gridFields: string[],
  projectId: string,
  unitId: string,
): ApplyRequest {
  const params: Record<string, number> = {};
  for (const field of gridFields) {
    const value = row[field];
    if (isFiniteNumber(value)) {
      params[field] = value;
    }
  }
  return { project_id: projectId, unit_id: unitId, params };
}

/**
 * D9 排序选项：响应 columns → Select 选项（白名单=columns∪{cost}——前端
 * 只出 columns 内选项，cost 列现状无列不加）。
 */
export function buildSortOptions(
  columns: string[],
): { value: string; label: string }[] {
  return columns.map((column) => ({ value: column, label: column }));
}
