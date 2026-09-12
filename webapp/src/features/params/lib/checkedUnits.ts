/**
 * 工况校核勾选纯函数层（P2 第三批 ADR-018 D4）：受检单元集合的读取/
 * 投影/PUT 载荷构造——CP2（约束勾选持久化）样板同构。
 *
 * 输入:  项目 raw（GET 未窄化原始体）+勾选键集
 * 输出:  checkableUnits 可勾全集/restoreCheckedKeys 恢复投影（幽灵勾选
 *        过滤）/withCheckedUnits PUT 载荷构造
 *
 * 规格说明（P2 第三批 ADR-018 D4；designParams CP2 族同构）：
 *   - 可勾全集=design.nodes 键减内置节点四 kind（municipal_input/
 *     junction/quality_edit/recycle_junction——受检语义=工艺单元 n-1 池
 *     检修敏感性，内置节点无池概念不参与）；字典序稳定；
 *   - 恢复投影=raw checked_units ∩ 可勾全集（删除单元后 checked_units
 *     由 designWriter 级联清理——服务端面；本过滤为呈现侧第二道防线，
 *     幽灵键灰显非目标、静默吞非目标）；
 *   - PUT 构造=withConstraintChoices 同构：仅替换 design.checked_units
 *     （全量替换——空集回空），其余顶层/design 键原样回传。
 */

/** 内置节点 kind 四族（projectFlow 口径——受检面排除）。 */
const BUILTIN_KINDS: ReadonlySet<string> = new Set([
  "municipal_input",
  "junction",
  "quality_edit",
  "recycle_junction",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function reject(detail: string): never {
  throw new Error(`工况校核载荷非法：${detail}`);
}

/** 可勾全集：design.nodes 键减内置四 kind，字典序（勾选面板选项面）。 */
export function checkableUnits(raw: unknown): string[] {
  if (!isRecord(raw)) return [];
  const design = raw["design"];
  if (!isRecord(design)) return [];
  const nodes = design["nodes"];
  if (!isRecord(nodes)) return [];
  return Object.entries(nodes)
    .filter(([, params]) => {
      const kind = isRecord(params) ? params["kind"] : null;
      return typeof kind !== "string" || !BUILTIN_KINDS.has(kind);
    })
    .map(([unitId]) => unitId)
    .sort();
}

/** 恢复投影：raw checked_units ∩ 可勾全集（呈现序=可勾全集字典序）。 */
export function restoreCheckedKeys(raw: unknown): string[] {
  const checkable = new Set(checkableUnits(raw));
  if (!isRecord(raw)) return [];
  const design = raw["design"];
  if (!isRecord(design)) return [];
  const checked = design["checked_units"];
  if (!Array.isArray(checked)) return [];
  return checkableUnits(raw).filter((unitId) => checked.includes(unitId) && checkable.has(unitId));
}

/**
 * D4 PUT 载荷构造：GET 未窄化原始体仅替换 design.checked_units
 * （全量替换——空 keys 回空即全解勾），其余顶层/design 键原样回传
 * （withConstraintChoices 同构——结构化替换禁散拼）。
 */
export function withCheckedUnits(
  raw: unknown,
  keys: string[],
): Record<string, unknown> {
  if (!isRecord(raw)) {
    reject(`PUT 载荷构造须原始 ProjectFile：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const design = raw["design"];
  if (!isRecord(design)) {
    reject(
      `PUT 载荷构造：原始体 design 须为对象：得到 ${JSON.stringify(design) ?? "undefined"}`,
    );
  }
  return { ...raw, design: { ...design, checked_units: keys } };
}
