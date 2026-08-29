/**
 * 参数面板纯函数层：design 参数面窄化+draft 归一+脏比较+目录索引+假设合成行。
 *
 * 输入:  readProject 返回体（弱类型 {[key:string]:unknown}）+META1 目录条目
 *        （UnitMetaEntry/AssumptionEntry——generated 类型面）+表单草稿
 * 输出:  五纯函数族（DesignParams 窄化产物/normalizeDraftValue 归一/
 *        collectParamChanges 提交面/indexUnits 目录索引/buildAssumptionRows
 *        假设行——非法形状抛 DesignParamsError）
 *
 * 规格说明（FE5 批 6b 段三，D1/D7/D8）：
 *   - D8 窄化门（FE4 projectFlow D6 门模式复用）：顶层 format_version 轻门
 *     （存在+string——具体版本语义归 service/core 双闸）+design/design.nodes/
 *     节点值容器形状逐类拒（错误消息带键定位）；nodeKinds 面=D1 builtin
 *     投影通道（值含 kind 字符串键→目录查找键=kind 值，如 inlet→
 *     municipal_input——D8 签名两映射外增此面为其服务）；叶值宽容：非数值
 *     非 kind 参数略过（server apply 值面收 str——读取链不重复裁判，
 *     projectFlow recycle 非 bool 宽容同构裁量）；
 *   - assumption_overrides 缺省宽容 {}（可选面）；有则须对象+值全有限数值
 *     （server 写侧 strict float——非数值=文件异形，显式拒不静默）；
 *   - D7 draft 归一：string→number|null——空/非数/非有限一律 null（禁提交
 *     态，表单层据此锁提交按钮）；payload 值全 number（JSON 序列化天然
 *     浮点形态——design.nodes 值面 Any 无 strict）；
 *   - 脏比较基准=当前有效值（design 覆盖 ?? manifest 默认 ?? null）——等值
 *     编辑不产空写条目（apply 服务端 merged.update 合并面免 no-op 写）；
 *     range/grid 不参与比较（range 无执行点=UI 展示数据，冻结 §三）；
 *   - 假设合成=DEFAULTS∪overrides（覆盖优先；目录外覆盖键追加成行——
 *     defaultValue=null+覆盖标记）；覆盖标记=key∈assumption_overrides；
 *   - 零运行期库 import（node 测试不拖 antd/react-query 链）。
 */
import type {
  AssumptionEntry,
  ParamEntry,
  UnitMetaEntry,
} from "../../../shared/api/generated/model";

/** 窄化产物（D8：参数面板消费的唯一 design 投影面）。 */
export type DesignParams = {
  /** unit_id → 参数名 → design 覆盖值（有限数值叶——kind/非数值叶除外）。 */
  nodeParams: Record<string, Record<string, number>>;
  /** unit_id → 内置 kind（值含 kind 字符串键；无则 null——目录查找键面）。 */
  nodeKinds: Record<string, string | null>;
  /** 假设覆盖（design.assumption_overrides——strict 数值面）。 */
  assumptionOverrides: Record<string, number>;
};

/** 窄化非法（版本门/形状逐类拒）——消费面错误薄壳呈现。 */
export class DesignParamsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DesignParamsError";
  }
}

/** 假设合成行（DEFAULTS∪overrides——AssumptionsPanel 只读消费面）。 */
export type AssumptionRow = {
  key: string;
  dim: string;
  source: string;
  note: string;
  tuningDirection: string;
  /** registry 默认值（目录外覆盖键=null——无声明面）。 */
  defaultValue: number | null;
  /** 合成值（覆盖优先）。 */
  value: number;
  /** 覆盖标记（key∈overrides）。 */
  overridden: boolean;
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 有限数值判定（bool 排除——typeof boolean 先于 number）。 */
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function reject(message: string): never {
  throw new DesignParamsError(message);
}

/**
 * D8 窄化门：readProject 弱类型 → DesignParams（容器形状逐类拒+叶值宽容）。
 */
export function narrowDesignParams(
  raw: Record<string, unknown>,
): DesignParams {
  // 门 1：format_version 轻门（存在+string——版本语义归 service/core）
  const version = raw["format_version"];
  if (typeof version !== "string") {
    reject(
      `项目文件缺 format_version 或非字符串：${JSON.stringify(version) ?? "undefined"}`
        + "（版本语义门在 service/core——前端只做形状轻门）",
    );
  }
  // 门 2：design 容器
  const design = raw["design"];
  if (!isRecord(design)) {
    reject(`design 须为对象：得到 ${JSON.stringify(design) ?? "undefined"}`);
  }
  // 门 3：design.nodes 逐键窄化（kind 元数据提取+数值参数收集）
  const nodesRaw = design["nodes"];
  if (!isRecord(nodesRaw)) {
    reject(
      `design.nodes 须为对象（unit_id→参数 dict）：得到 ${JSON.stringify(nodesRaw) ?? "undefined"}`,
    );
  }
  const nodeParams: Record<string, Record<string, number>> = {};
  const nodeKinds: Record<string, string | null> = {};
  for (const [unitId, params] of Object.entries(nodesRaw)) {
    if (!isRecord(params)) {
      reject(
        `design.nodes[${unitId}] 须为对象（参数 dict）：得到 ${JSON.stringify(params) ?? "undefined"}`,
      );
    }
    const kindRaw = params["kind"];
    nodeKinds[unitId] = typeof kindRaw === "string" ? kindRaw : null;
    const values: Record<string, number> = {};
    for (const [field, value] of Object.entries(params)) {
      // kind=内置节点元数据键（非参数）；非数值叶宽容略过（D8 记档裁量）
      if (field === "kind" || !isFiniteNumber(value)) {
        continue;
      }
      values[field] = value;
    }
    nodeParams[unitId] = values;
  }
  // 门 4：assumption_overrides（缺省宽容 {}；有则 strict 数值面）
  const overridesRaw = design["assumption_overrides"];
  const assumptionOverrides: Record<string, number> = {};
  if (overridesRaw !== undefined) {
    if (!isRecord(overridesRaw)) {
      reject(
        `design.assumption_overrides 须为对象（key→数值）：得到 ${JSON.stringify(overridesRaw) ?? "undefined"}`,
      );
    }
    for (const [key, value] of Object.entries(overridesRaw)) {
      if (!isFiniteNumber(value)) {
        reject(
          `design.assumption_overrides[${key}] 须为数值：得到 ${JSON.stringify(value) ?? "undefined"}`,
        );
      }
      assumptionOverrides[key] = value;
    }
  }
  return { nodeParams, nodeKinds, assumptionOverrides };
}

/**
 * D7 draft 归一：表单输入串 → number|null（空/非数/非有限=null 禁提交态）。
 */
export function normalizeDraftValue(text: string): number | null {
  const trimmed = text.trim();
  if (trimmed === "") {
    return null;
  }
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

/**
 * D5 脏比较+提交面收集：草稿 vs 当前有效值（design 覆盖 ?? manifest 默认）。
 * 返回 changes（差异项——等值不产空写）+invalidFields（null 禁提交项）。
 */
export function collectParamChanges(
  entries: ParamEntry[],
  designValues: Record<string, number>,
  drafts: Record<string, string>,
): { changes: Record<string, number>; invalidFields: string[] } {
  const changes: Record<string, number> = {};
  const invalidFields: string[] = [];
  for (const entry of entries) {
    const fieldId = entry.field_id;
    const draftText = drafts[fieldId];
    if (draftText === undefined) {
      continue; // 未编辑字段不进提交面
    }
    const value = normalizeDraftValue(draftText);
    if (value === null) {
      invalidFields.push(fieldId);
      continue;
    }
    const effective =
      fieldId in designValues
        ? designValues[fieldId]
        : (entry.default ?? null);
    if (effective === null || effective !== value) {
      changes[fieldId] = value;
    }
  }
  return { changes, invalidFields };
}

/** META1 目录索引：unit_id（含 builtin kind 键）→ UnitMetaEntry。 */
export function indexUnits(units: UnitMetaEntry[]): Map<string, UnitMetaEntry> {
  const index = new Map<string, UnitMetaEntry>();
  for (const entry of units) {
    index.set(entry.unit_id, entry);
  }
  return index;
}

/** 目录条目 → 合成行（registry 序保持+默认值/元数据透传）。 */
function assumptionRow(
  key: string,
  dim: string,
  source: string,
  note: string,
  tuningDirection: string,
  defaultValue: number | null,
  overrides: Record<string, number>,
): AssumptionRow {
  const override = overrides[key];
  const overridden = override !== undefined; // key∈overrides（数值面非 undefined 判）
  return {
    key,
    dim,
    source,
    note,
    tuningDirection,
    defaultValue,
    value: overridden ? override : (defaultValue as number),
    overridden,
  };
}

/**
 * 假设合成行：DEFAULTS∪overrides（覆盖优先；目录外覆盖键按 key 序追加成行）。
 */
export function buildAssumptionRows(
  entries: AssumptionEntry[],
  overrides: Record<string, number>,
): AssumptionRow[] {
  const rows = entries.map((entry) =>
    assumptionRow(
      entry.key,
      entry.dim,
      entry.source,
      entry.note,
      entry.tuning_direction,
      entry.default,
      overrides,
    ),
  );
  const known = new Set(entries.map((entry) => entry.key));
  const extras = Object.keys(overrides)
    .filter((key) => !known.has(key))
    .sort();
  for (const key of extras) {
    rows.push(
      assumptionRow(key, "", "", "", "", null, overrides),
    );
  }
  return rows;
}
