/**
 * sameSite 深比较测试：三例（空数组同/类型异/键序无关深比较同——SC1 D9④）。
 *
 * 输入:  siteDraftDiff.ts 导出 sameSite（draft dirty 派生比较真源）
 * 输出:  三断言面（[] vs [] 同、[] vs 非 [] 异、键序无关深比较同）
 */
import { describe, expect, it } from "vitest";

import { sameSite } from "./siteDraftDiff";

describe("sameSite 键序无关深比较（SC1 自 SiteplanPane 私有迁 lib）", () => {
  it("[] vs [] 同（清空红线后 dirty 派生比较归零——copy-on-write 置空可保存）", () => {
    expect(sameSite([], [])).toBe(true);
  });

  it("[] vs 非 [] 异（清空 vs 有顶点=dirty 置位）", () => {
    expect(sameSite([], [{ x: 0, y: 0 }])).toBe(false);
  });

  it("键序无关深比较同（draft copy-on-write 不保插入序一致性）", () => {
    const a = { boundary: [], roads: [{ centerline: [{ x: 1, y: 2 }], width_m: 3 }] };
    const b = { roads: [{ width_m: 3, centerline: [{ y: 2, x: 1 }] }], boundary: [] };
    expect(sameSite(a, b)).toBe(true);
  });
});
