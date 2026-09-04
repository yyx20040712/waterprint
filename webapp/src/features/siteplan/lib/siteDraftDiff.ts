/**
 * site draft 深比较：dirty 派生真源（SC1 D9④ 自 SiteplanPane 私有迁 lib）。
 *
 * 输入:  两任意值（装载 site vs 本地 draft——SiteDesignShape 归一态）
 * 输出:  sameSite（键序无关深比较布尔——draft copy-on-write 不保插入序
 *        一致性，键排序后逐键递归）
 */

/** 深比较（键序无关——draft copy-on-write 不保插入序一致性）。 */
export function sameSite(a: unknown, b: unknown): boolean {
  if (a === b) {
    return true;
  }
  if (typeof a !== "object" || typeof b !== "object" || a === null || b === null) {
    return false;
  }
  const aKeys = Object.keys(a).sort();
  const bKeys = Object.keys(b).sort();
  if (aKeys.length !== bKeys.length || aKeys.some((key, i) => key !== bKeys[i])) {
    return false;
  }
  return aKeys.every((key) =>
    sameSite((a as Record<string, unknown>)[key], (b as Record<string, unknown>)[key]),
  );
}
