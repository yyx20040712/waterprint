/**
 * 约束目录窄化/供选过滤/payload 投影纯函数（CP1 D6——ConstraintPicker 数据面）。
 *
 * 输入:  /api/constraints 原始载荷（unknown——orval 自由对象面）+ 目标单元
 *        id + 选中 key 集
 * 输出:  narrowConstraintCatalog → 条目视图[]（八键逐条校验，非法抛
 *        ConstraintCatalogError）；filterSelectable → 供选子集
 *        （kind=enumeration_filter 且 unit_kinds 含单元）；toPayloadItems
 *        → 枚举 options.constraints 三键载荷（key/expression/source——
 *        severity 不入 worker 三键面）
 *
 * 规格说明（CP1 2026-08-31，D6/D7；窄化门纪律=solutionsView 同款）：
 *   - 服务端 kb 装载已 fail-visible（库级拒），本门为前端第二防线
 *     （传输破损/缓存异形拒于渲染前——非法形状 error 态呈现非静默）；
 *   - 供选双门=kind+unit_kinds（effluent_standard 恒空表=机制性不供选
 *     ——出水水质非枚举行字段，kb README 收录边界）；
 *   - payload 恰三键对齐 worker.py _run_enumerate 构造面（key/expression/
 *     source；severity 留 UI 呈现面不入载荷）；
 *   - 未知 key 静默滤除：目录刷新与选中集的竞态下不构造半载荷
 *     （提交时目录为准——selected 与 selectable 的差集自然消失）。
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
  const out: ConstraintEntryView = {
    key: String(raw["key"] ?? ""),
    kind: (raw["kind"] as ConstraintEntryView["kind"]) ?? "effluent_standard",
    unit_kinds: Array.isArray(raw["unit_kinds"])
      ? raw["unit_kinds"].map(String)
      : [],
    label: String(raw["label"] ?? ""),
    expression: String(raw["expression"] ?? ""),
    source: String(raw["source"] ?? ""),
    severity: String(raw["severity"] ?? ""),
    value_basis: String(raw["value_basis"] ?? ""),
  };
  const required: (keyof ConstraintEntryView)[] = [
    "key", "kind", "unit_kinds", "label", "expression",
    "source", "severity", "value_basis",
  ];
  for (const field of required) {
    const value = out[field];
    if (typeof value === "string" && value === "") {
      throw new ConstraintCatalogError(
        `约束目录条目[${position}]缺 ${field}（key=${out.key || "?"}）`,
      );
    }
  }
  if (!KINDS.includes(out.kind)) {
    throw new ConstraintCatalogError(
      `约束目录条目 ${out.key} kind 越界：${out.kind}`,
    );
  }
  return out;
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
