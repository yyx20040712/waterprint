/**
 * 约束目录窄化/供选过滤/payload 投影/勾选恢复投影/本组合成全集纯函数
 * （CP1 D6——ConstraintPicker 数据面；CP2 D3——持久勾选恢复面；
 * CP2 R-1——onChange 合成全集面）。
 *
 * 输入:  /api/constraints 原始载荷（unknown——orval 自由对象面）+ 目标单元
 *        id + 选中 key 集+项目原始 GET 体（恢复投影——design.
 *        constraint_choices）+全集/本组键/本组变更（合成全集）
 * 输出:  narrowConstraintCatalog → 条目视图[]（八键逐条校验，非法抛
 *        ConstraintCatalogError）；filterSelectable → 供选子集
 *        （kind=enumeration_filter 且 unit_kinds 含单元）；toPayloadItems
 *        → 枚举 options.constraints 三键载荷（key/expression/source——
 *        severity 不入 worker 三键面）；restoreConstraintKeys → 勾选
 *        keys 全集（value 恒 "on" 的键——CP2 恢复投影）；
 *        mergeGroupSelection → 本组变更合成全集（跨单元键保留——R-1）
 *
 * 规格说明（CP1 2026-08-31，D6/D7；窄化门纪律=solutionsView 同款；
 *   CP2 2026-09-01，D1/D3/D7；R 轮 2026-09-01，R-1/N-1）：
 *   - 服务端 kb 装载已 fail-visible（库级拒），本门为前端第二防线
 *     （传输破损/缓存异形拒于渲染前——非法形状 error 态呈现非静默）；
 *   - 供选双门=kind+unit_kinds（effluent_standard 恒空表=机制性不供选
 *     ——出水水质非枚举行字段，kb README 收录边界）；
 *   - payload 恰三键对齐 worker.py _run_enumerate 构造面（key/expression/
 *     source；severity 留 UI 呈现面不入载荷）；
 *   - 未知 key 静默滤除：目录刷新与选中集的竞态下不构造半载荷
 *     （提交时目录为准——selected 与 selectable 的差集自然消失）；
 *   - CP2 恢复投影：design.constraint_choices 值恒 "on"（D1 固定值——
 *     档位语义属扩展位禁现在造），非 "on" 值键不恢复；kb 外死键照恢
 *     （持久勾选全集——显示/提交面=全集∩供选面自然滤除，D7 键域宽）；
 *     形状宽容不炸（缺键/非对象→[]——rawCheckedUnits 同口径：恢复面
 *     非窄化门，异形留 PUT 侧守卫）；
 *   - CP2 R-1 合成全集：antd Checkbox.Group onChange 只报本组注册值
 *     （当前供选面 options），跨单元已勾键须由挂载方显式保留——
 *     持久载荷=合成全集非本组值（D4「切回再现」的变更面契约载体）；
 *     次序确定（保留键原序+nextKeys 追加序）+去重（防御面）。
 */
export type ConstraintEntryView = {
  key: string;
  kind: "enumeration_filter" | "effluent_standard";
  unit_kinds: string[];
  label: string;
  expression: string;
  source: string;
  severity: string;
  value_basis: string;
};

/** 目录形状非法（窄化门——error 态呈现面）。 */
export class ConstraintCatalogError extends Error {}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const KINDS = ["enumeration_filter", "effluent_standard"] as const;

function narrowEntry(raw: unknown, position: number): ConstraintEntryView {
  if (!isRecord(raw)) {
    throw new ConstraintCatalogError(
      `约束目录条目[${position}]非对象：${String(raw)}`,
    );
  }
  // R1（DS-01）：与服务端 _REQUIRED_KEYS 同强度——缺键/型异/空串显式抛，
  // 禁默认值静默降级（kind 缺失→effluent、unit_kinds 缺失→[] 类路径即红）。
  const required: (keyof ConstraintEntryView)[] = [
    "key", "kind", "unit_kinds", "label", "expression",
    "source", "severity", "value_basis",
  ];
  for (const field of required) {
    if (!(field in raw)) {
      throw new ConstraintCatalogError(
        `约束目录条目[${position}]缺键 ${field}`,
      );
    }
  }
  for (const field of ["key", "label", "expression", "source", "severity", "value_basis"] as const) {
    if (typeof raw[field] !== "string" || (raw[field] as string) === "") {
      throw new ConstraintCatalogError(
        `约束目录条目[${position}] ${field} 须为非空字符串（key=${String(raw["key"]) || "?"}）`,
      );
    }
  }
  if (typeof raw["kind"] !== "string" || !KINDS.includes(raw["kind"] as ConstraintEntryView["kind"])) {
    throw new ConstraintCatalogError(
      `约束目录条目[${position}] kind 越界或型异：${JSON.stringify(raw["kind"])}`,
    );
  }
  if (!Array.isArray(raw["unit_kinds"]) || !raw["unit_kinds"].every((u) => typeof u === "string")) {
    throw new ConstraintCatalogError(
      `约束目录条目[${position}] unit_kinds 须为字符串数组（key=${String(raw["key"])}）`,
    );
  }
  return {
    key: raw["key"] as string,
    kind: raw["kind"] as ConstraintEntryView["kind"],
    unit_kinds: raw["unit_kinds"] as string[],
    label: raw["label"] as string,
    expression: raw["expression"] as string,
    source: raw["source"] as string,
    severity: raw["severity"] as string,
    value_basis: raw["value_basis"] as string,
  };
}

/** 目录窄化正门（八键逐条——非法抛 ConstraintCatalogError）。 */
export function narrowConstraintCatalog(raw: unknown): ConstraintEntryView[] {
  if (!isRecord(raw) || !Array.isArray(raw["entries"])) {
    throw new ConstraintCatalogError("约束目录载荷非法（须 {entries: […]}）");
  }
  return raw["entries"].map((item, position) => narrowEntry(item, position));
}

/** 供选过滤：kind 双门+单元归属（unitId null=未选不供选）。 */
export function filterSelectable(
  entries: ConstraintEntryView[],
  unitId: string | null,
): ConstraintEntryView[] {
  if (unitId === null) {
    return [];
  }
  return entries.filter(
    (entry) =>
      entry.kind === "enumeration_filter" && entry.unit_kinds.includes(unitId),
  );
}

/** 选中集 → options.constraints 三键载荷（未知 key 滤除——目录为准）。 */
export function toPayloadItems(
  entries: ConstraintEntryView[],
  selectedKeys: string[],
): { key: string; expression: string; source: string }[] {
  const byKey = new Map(entries.map((entry) => [entry.key, entry]));
  return selectedKeys.flatMap((key) => {
    const entry = byKey.get(key);
    return entry
      ? [{ key: entry.key, expression: entry.expression, source: entry.source }]
      : [];
  });
}

/** CP2 D1：勾选值恒 "on"（解勾=删键；档位语义属扩展位禁现在造）。 */
const CHOICE_ON = "on";

/**
 * CP2 D3 恢复投影：raw GET 体 design.constraint_choices → 勾选 keys 全集
 * （value 恒 "on" 的键——死键照收，供选面∩过滤归显示/提交面）。
 */
export function restoreConstraintKeys(raw: unknown): string[] {
  if (!isRecord(raw)) {
    return [];
  }
  const design = raw["design"];
  if (!isRecord(design)) {
    return [];
  }
  const choices = design["constraint_choices"];
  if (!isRecord(choices)) {
    return []; // 缺省/非对象宽容回空（恢复面不炸——异形留 PUT 侧守卫）
  }
  return Object.entries(choices).flatMap(([key, value]) =>
    value === CHOICE_ON ? [key] : [],
  );
}

/**
 * CP2 R-1（N-1 2026-09-01）本组变更合成全集：Checkbox.Group onChange(values)
 * 只报本组（当前供选面）注册值——挂载方持久前须经此合成，跨单元已勾键
 * 不被覆盖删除。结果=totalKeys 中不属于本组 groupKeys 的键（原序保留）
 * ∪ nextKeys（其序追加），去重（防御 nextKeys 重复/与保留键重叠）。
 */
export function mergeGroupSelection(
  totalKeys: string[],
  groupKeys: string[],
  nextKeys: string[],
): string[] {
  const group = new Set(groupKeys);
  const seen = new Set<string>();
  const merged: string[] = [];
  for (const key of totalKeys) {
    if (!group.has(key) && !seen.has(key)) {
      seen.add(key);
      merged.push(key);
    }
  }
  for (const key of nextKeys) {
    if (!seen.has(key)) {
      seen.add(key);
      merged.push(key);
    }
  }
  return merged;
}
