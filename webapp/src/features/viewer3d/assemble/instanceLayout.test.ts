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
      expect(laid.positions[0]?.[1]).toBeCloseTo(4.67, 10);  // y 锚=几何中心（门二 P1 修复）
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
    expect(y).toBeCloseTo(4.67 * 1.2, 10);
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

describe("instanceLayout 段二 box 族模式（grid/line/rect）", () => {
  // AAO 曝气头原型：几何居中于原点（盘 Φ0.3）、TRS 抬到池底板顶 0.5
  const AERATOR_AABB = { min: [-0.15, 0.5, -0.15] as const, max: [0.15, 0.76, 0.15] as const };
  // AAO 立柱原型：几何居中、TRS=走道角位 (48.75, 20.05)
  const POST_AABB_RECT = { min: [48.725, 5.42, 20.025] as const, max: [48.775, 6.52, 20.075] as const };
  // CASS 滗水器原型：居中悬臂、TRS=(18.7, 0, 0)
  const DECANT_AABB = { min: [15.23, 0, -2.025] as const, max: [22.17, 1.3, 2.025] as const };

  it("grid：cols=L0/spacing 起算+行优先+居中+baseY 随壳深", () => {
    const laid = instanceLayout(AERATOR_AABB, 4, [1, 1, 1], {
      mode: "grid", spacing: 0.8, envelope: { L0: 95, W0: 38 },
    });
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions).toHaveLength(4);
    // cols=round(95/0.8)=119→4 实例单行居中，z 恒 0（单行 (rows−1)/2=0）
    const [x0, y0, z0] = laid.positions[0] ?? [];
    expect(x0).toBeCloseTo(-1.5 * 0.8, 10); // (0−(4−1)/2)×0.8
    expect(y0).toBeCloseTo(0.63, 10);  // (0.5+0.76)/2
    expect(z0).toBeCloseTo(0, 10);
    expect(laid.positions[3]?.[0]).toBeCloseTo(1.5 * 0.8, 10);
  });
  it("grid：count>cols 多行排布（cols=2 域包络下 5 实例=3 行）", () => {
    const laid = instanceLayout(AERATOR_AABB, 5, [1, 1, 1], {
      mode: "grid", spacing: 0.8, envelope: { L0: 1.6, W0: 38 },
    });
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions).toHaveLength(5);
    // rows=ceil(5/2)=3：z 行位 −0.8/0/+0.8（(r−1)×0.8）
    expect(laid.positions[0]?.[2]).toBeCloseTo(-0.8, 10);
    expect(laid.positions[2]?.[2]).toBeCloseTo(0, 10);
    expect(laid.positions[4]?.[2]).toBeCloseTo(0.8, 10);
    expect(laid.positions[4]?.[0]).toBeCloseTo(-0.4, 10); // 末行缺额左起（网格对齐——core internals R3 同构）
  });
  it("grid：位置随壳缩放（p⊙s——包络缩放语义）", () => {
    const laid = instanceLayout(AERATOR_AABB, 2, [2, 1, 3], {
      mode: "grid", spacing: 0.8, envelope: { L0: 95, W0: 38 },
    });
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions[0]?.[0]).toBeCloseTo(-0.4 * 2, 10);
    expect(laid.positions[0]?.[2]).toBeCloseTo(0, 10);
    expect(laid.positions[1]?.[0]).toBeCloseTo(0.4 * 2, 10);
  });
  it("line_z：横轴=原型中心 x、纵轴居中均布（CASS 滗水器）", () => {
    const laid = instanceLayout(DECANT_AABB, 2, [1, 1, 1], {
      mode: "line_z", spacing: 7.5,
    });
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions).toHaveLength(2);
    const cx = (15.23 + 22.17) / 2;
    expect(laid.positions[0]?.[0]).toBeCloseTo(cx, 10);
    expect(laid.positions[0]?.[1]).toBeCloseTo(0.65, 10);  // (0+1.3)/2
    expect(laid.positions[0]?.[2]).toBeCloseTo(-3.75, 10);
    expect(laid.positions[1]?.[2]).toBeCloseTo(3.75, 10);
  });
  it("line_x：纵轴=原型中心 z、横轴居中均布", () => {
    const laid = instanceLayout(AERATOR_AABB, 3, [1, 1, 1], {
      mode: "line_x", spacing: 2.0,
    });
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions[0]?.[0]).toBeCloseTo(-2.0, 10);
    expect(laid.positions[1]?.[0]).toBeCloseTo(0, 10);
    expect(laid.positions[2]?.[0]).toBeCloseTo(2.0, 10);
    expect(laid.positions[0]?.[2]).toBeCloseTo(0, 10); // 原型 cz=0
  });
  it("rect：周界步进（起点=原型角位顺时针西行）", () => {
    const laid = instanceLayout(POST_AABB_RECT, 3, [1, 1, 1], {
      mode: "rect", spacing: 3.5,
    });
    if (laid.kind !== "laid") {
      throw new Error("expected laid");
    }
    expect(laid.positions).toHaveLength(3);
    const hx = 48.75, hz = 20.05;
    expect(laid.positions[0]?.[0]).toBeCloseTo(hx, 10);
    expect(laid.positions[0]?.[2]).toBeCloseTo(hz, 10);
    expect(laid.positions[1]?.[0]).toBeCloseTo(hx - 3.5, 10); // 顶行西行
    expect(laid.positions[1]?.[2]).toBeCloseTo(hz, 10);
    expect(laid.positions[2]?.[0]).toBeCloseTo(hx - 7.0, 10);
    expect(laid.positions[2]?.[1]).toBeCloseTo(5.97, 10); // y 锚=中心(5.42+6.52)/2
  });
  it("非 ring 模式 spacing 病=skipped（registry 声明病显式登记）", () => {
    expect(
      instanceLayout(AERATOR_AABB, 4, [1, 1, 1], { mode: "grid", spacing: 0 }),
    ).toEqual({ kind: "skipped", reason: "bad_spacing" });
    expect(
      instanceLayout(AERATOR_AABB, 4, [1, 1, 1], { mode: "line_z" }),
    ).toEqual({ kind: "skipped", reason: "bad_spacing" });
  });
});
