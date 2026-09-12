/**
 * instanceLayout 单测（批3 主体——P7 裁定+S5 前提位姿）。
 *
 * 输入:  原型 AABB（基座环位）+场景计数+壳缩放
 * 输出:  契约断言（P7 无值不渲染；位姿=anchor⊙s；环均布含原型角）
 */

import { describe, expect, it } from "vitest";

import { instanceLayout } from "./instanceLayout";

const POST_AABB = {
  min: [21.475, 4.12, -0.025] as const,
  max: [21.525, 5.22, 0.025] as const,
};

describe("instanceLayout（P7 数量唯一真源=场景图）", () => {
  it("count=null 不渲染（P7：禁推导补数）", () => {
    expect(instanceLayout(POST_AABB, null, [1, 1, 1])).toEqual({
      kind: "skipped",
      reason: "no_scene_count",
    });
  });
  it("count<1 同 skipped（非法计数防御）", () => {
    expect(instanceLayout(POST_AABB, 0, [1, 1, 1]).kind).toBe("skipped");
    expect(instanceLayout(POST_AABB, Number.NaN, [1, 1, 1]).kind).toBe("skipped");
  });
  it("count=1=原型位本身（anchor⊙s 恒等 s=𝟙）", () => {
    const laid = instanceLayout(POST_AABB, 1, [1, 1, 1]);
    expect(laid).toMatchObject({ kind: "laid" });
    if (laid.kind === "laid") {
      expect(laid.positions).toHaveLength(1);
      expect(laid.positions[0]?.[0]).toBeCloseTo(21.5, 10);
      expect(laid.positions[0]?.[1]).toBeCloseTo(4.12, 10);
      expect(laid.positions[0]?.[2]).toBeCloseTo(0, 10);
    }
  });
  it("位姿=anchor⊙s（σ=𝟙——环半径/基座高随壳缩放，几何恒定）", () => {
    const laid = instanceLayout(POST_AABB, 1, [1.5, 1.2, 1.5]);
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    const [x, y, z] = laid.positions[0] ?? [NaN, NaN, NaN];
    expect(x).toBeCloseTo(21.5 * 1.5, 10);
    expect(y).toBeCloseTo(4.12 * 1.2, 10);
    expect(z).toBeCloseTo(0, 10); // −0 归一
  });
  it("环均布：首实例=原型角，等角距；半径恒 21.5×s", () => {
    const laid = instanceLayout(POST_AABB, 4, [1, 1, 1]);
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions).toHaveLength(4);
    const radii = laid.positions.map(([x, , z]) => Math.hypot(x, z));
    for (const r of radii) {
      expect(r).toBeCloseTo(21.5, 9);
    }
    // 相邻角距=π/2（原型角 0 起步：atan2(0,21.5)=0）
    expect(laid.positions[1]?.[0]).toBeCloseTo(0, 9);
    expect(laid.positions[1]?.[2]).toBeCloseTo(21.5, 9);
    expect(laid.positions[2]?.[0]).toBeCloseTo(-21.5, 9);
  });
});
