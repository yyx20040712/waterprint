/**
 * 投影层纯函数测试：SceneGraph JSON → 渲染描述（D4 前端测试策略五面）。
 *
 * 输入:  projectScene 纯函数（node 环境——零 WebGL 依赖，先红后绿）
 * 输出:  投影契约断言（SCENE_VERSION 门/五 kind 完备/摆置确定性/语义 token/root 一致性）
 */
import { describe, expect, it } from "vitest";

import {
  RENDER_SCENE_VERSION,
  SceneProjectionError,
  projectScene,
} from "./projectScene";

const VERSION = "waterprint-scene-1/y-up/m";

type FixtureNode = {
  node_id: string;
  semantic: string;
  primitive: { kind: string; dims: Record<string, number>; semantic: string };
  position?: [number, number, number];
  instance_count?: number;
};

function fixture(overrides?: Partial<Record<string, unknown>>): Record<string, unknown> {
  const nodes: FixtureNode[] = [
    {
      node_id: "pool-1",
      semantic: "pool_wall",
      primitive: { kind: "box", dims: { length: 10, width: 4, depth: 3 }, semantic: "pool_wall" },
      position: [0, 0, 0],
    },
    {
      node_id: "pool-2",
      semantic: "pool_wall",
      primitive: { kind: "cylinder", dims: { diameter: 6, depth: 4 }, semantic: "pool_wall" },
      position: [20, 0, 0],
    },
    {
      node_id: "chan-1",
      semantic: "channel",
      primitive: { kind: "extrusion", dims: { length: 8, width: 1, depth: 1.5 }, semantic: "channel" },
      position: [30, 0, 0],
    },
    {
      node_id: "surf-1",
      semantic: "water_surface",
      primitive: { kind: "water_surface", dims: { length: 10, width: 4, depth: 2.5 }, semantic: "water_surface" },
      position: [0, 0.1, 0],
    },
    {
      node_id: "ground-1",
      semantic: "ground",
      primitive: { kind: "plane", dims: { length: 50, width: 30 }, semantic: "ground" },
      position: [0, -0.01, 0],
    },
    {
      node_id: "unit-1::aerator",
      semantic: "aerator",
      primitive: { kind: "box", dims: { length: 0.5, width: 0.5, depth: 0.5 }, semantic: "aerator" },
      position: [2, 0.5, 1],
      instance_count: 12,
    },
  ];
  const scene: Record<string, unknown> = {
    scene_version: VERSION,
    condition_key: "design",
    root: ["pool-1", "pool-2", "chan-1", "surf-1"],
    nodes,
  };
  return { ...scene, ...overrides };
}

describe("projectScene：SCENE_VERSION 门", () => {
  it("非 waterprint-scene-1/y-up/m 拒且原因附版本值", () => {
    const bad = fixture({ scene_version: "waterprint-scene-1/z-up/m" });
    expect(() => projectScene(bad as never)).toThrow(SceneProjectionError);
    try {
      projectScene(bad as never);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect((error as Error).message).toContain("waterprint-scene-1/z-up/m");
      expect((error as Error).message).toContain(RENDER_SCENE_VERSION);
    }
  });

  it("合法版本放行且 sceneVersion/conditionKey 透传", () => {
    const out = projectScene(fixture() as never);
    expect(out.sceneVersion).toBe(VERSION);
    expect(out.conditionKey).toBe("design");
  });
});

describe("projectScene：五 kind 完备映射", () => {
  it("box/cylinder/plane/extrusion 归 solids，water_surface 归 waters", () => {
    const out = projectScene(fixture() as never);
    const solidKinds = out.solids.map((n) => n.kind).sort();
    // aerator（box, instance_count=12）归 internals——solids=四 kind 恰合
    expect(solidKinds).toEqual(["box", "cylinder", "extrusion", "plane"]);
    expect(out.waters.map((n) => n.kind)).toEqual(["water_surface"]);
  });

  it("dims 逐键逐值透传（零推导：不重算不增删键）", () => {
    const out = projectScene(fixture() as never);
    const pool = out.solids.find((n) => n.id === "pool-1");
    expect(pool?.dims).toEqual({ length: 10, width: 4, depth: 3 });
    const cyl = out.solids.find((n) => n.id === "pool-2");
    expect(cyl?.dims).toEqual({ diameter: 6, depth: 4 });
  });

  it("未知 kind 显式拒（原因含 kind 与节点 id）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "evil-1",
        semantic: "x",
        primitive: { kind: "sphere", dims: { r: 1 }, semantic: "x" },
      },
    ];
    const bad = fixture({ nodes, root: [] });
    expect(() => projectScene(bad as never)).toThrow(/sphere/);
  });
});

describe("projectScene：instance_count>1 摆置确定性", () => {
  it("摆置数=instance_count；步距=原型自身 dims；近方阵列布局", () => {
    const out = projectScene(fixture() as never);
    const aerator = out.internals.find((n) => n.id === "unit-1::aerator");
    expect(aerator).toBeDefined();
    expect(aerator?.placements).toHaveLength(12);
    expect(aerator?.instanceCount).toBe(12);
    // 步距=原型占位（length=0.5→X 向、width=0.5→Z 向——类型化摆放非业务推导）
    const first = aerator?.placements[0];
    const second = aerator?.placements[1];
    expect(first).toEqual([2, 0.5, 1]);
    expect((second?.[0] ?? 0) - (first?.[0] ?? 0)).toBeCloseTo(0.5, 10);
    // 12 实例 → cols=ceil(sqrt(12))=4：第二行起点=第 5 个实例（X 回原点）
    const fifth = aerator?.placements[4];
    expect(fifth?.[0]).toBeCloseTo(2, 10);
    expect((fifth?.[2] ?? 0) - (first?.[2] ?? 0)).toBeCloseTo(0.5, 10);
  });

  it("同输入双跑摆置逐点相同（确定性）", () => {
    const left = projectScene(fixture() as never);
    const right = projectScene(fixture() as never);
    expect(left).toEqual(right);
  });

  it("instance_count 缺省=1（生成类型可选——单实例组归 solids）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "solo-1",
        semantic: "gate",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "gate" },
      },
    ];
    const out = projectScene(fixture({ nodes, root: ["solo-1"] }) as never);
    expect(out.solids).toHaveLength(1);
    expect(out.solids[0]?.instanceCount).toBe(1);
    expect(out.internals).toHaveLength(0);
  });
});

describe("projectScene：语义 token 与色值隔离", () => {
  it("渲染描述输出 semantic token 透传且无任何色值字段", () => {
    const out = projectScene(fixture() as never);
    const all = [...out.solids, ...out.waters, ...out.internals];
    expect(all.map((n) => n.semantic).sort()).toEqual(
      ["aerator", "channel", "ground", "pool_wall", "pool_wall", "water_surface"].sort(),
    );
    for (const node of all) {
      expect(Object.keys(node)).not.toContain("color");
      expect(node).not.toHaveProperty("material");
    }
  });
});

describe("projectScene：root 序与 nodes 索引一致性", () => {
  it("root 逐 id 命中 nodes 且序保持", () => {
    const out = projectScene(fixture() as never);
    expect(out.root).toEqual(["pool-1", "pool-2", "chan-1", "surf-1"]);
    const ids = new Set(
      [...out.solids, ...out.waters, ...out.internals].map((n) => n.id),
    );
    for (const id of out.root) {
      expect(ids.has(id)).toBe(true);
    }
  });

  it("root 悬空 id 拒（索引一致性守卫）", () => {
    const bad = fixture({ root: ["pool-1", "ghost-9"] });
    expect(() => projectScene(bad as never)).toThrow(/ghost-9/);
  });
});
