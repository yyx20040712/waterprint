/**
 * 投影层纯函数测试：SceneGraph JSON → 渲染描述（D4 前端测试策略五面）。
 *
 * 输入:  projectScene 纯函数（node 环境——零 WebGL 依赖，先红后绿）
 * 输出:  投影契约断言（SCENE_VERSION 门/六 kind 完备/摆置确定性/语义 token/
 *        root 一致性；L5b：rotation 放行透传+scale 仍拒+总装红线 polyline 分组）
 */
import { describe, expect, it } from "vitest";

import {
  RENDER_SCENE_VERSION,
  SceneProjectionError,
  projectScene,
} from "./projectScene";

const VERSION = "waterprint-scene-2/y-up/m";

type FixtureNode = {
  node_id: string;
  semantic: string;
  primitive: { kind: string; dims: Record<string, number>; semantic: string };
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: [number, number, number];
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
  it("非 waterprint-scene-2/y-up/m 拒且原因附版本值（L5b 步进 -2：旧 -1 坐标约定拒）", () => {
    const bad = fixture({ scene_version: "waterprint-scene-1/y-up/m" });
    expect(() => projectScene(bad as never)).toThrow(SceneProjectionError);
    try {
      projectScene(bad as never);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect((error as Error).message).toContain("waterprint-scene-1/y-up/m");
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

describe("projectScene：非默认变换门（L5b 收窄：rotation 放行/scale 仍拒）", () => {
  it("rotation 任意值放行且弧度直透传（R3F 直消费——度→弧度换算归 core 装配层）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "rot-1",
        semantic: "pool_wall",
        primitive: { kind: "box", dims: { length: 10, width: 4, depth: 3 }, semantic: "pool_wall" },
        position: [5, 0, 2],
        rotation: [0, 0, Math.PI / 2],
      },
    ];
    const out = projectScene(fixture({ nodes, root: ["rot-1"] }) as never);
    expect(out.solids).toHaveLength(1);
    expect(out.solids[0]?.rotation).toEqual([0, 0, Math.PI / 2]); // 零换算透传
  });

  it("scale 非默认拒（非 (1,1,1) 即拒——门收窄不撤）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "scl-1",
        semantic: "media",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "media" },
        scale: [2, 1, 1],
      },
    ];
    const bad = fixture({ nodes, root: ["scl-1"] });
    try {
      projectScene(bad as never);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect(error).toBeInstanceOf(SceneProjectionError);
      expect((error as Error).message).toContain("scl-1");
      expect((error as Error).message).toContain("2");
    }
  });

  it("默认值与缺省同路放行且 rotation 默认 (0,0,0) 透传", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "def-1",
        semantic: "gate",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "gate" },
        rotation: [0, 0, 0],
        scale: [1, 1, 1],
      },
    ];
    const out = projectScene(fixture({ nodes, root: ["def-1"] }) as never);
    expect(out.solids).toHaveLength(1);
    expect(out.solids[0]?.id).toBe("def-1");
    expect(out.solids[0]?.rotation).toEqual([0, 0, 0]);
  });
});

// ═══ L5b（webapp 总装模式 2026-09-03）：polyline 红线分组+顶点序解码+bounds ═══
describe("projectScene：总装红线（polyline → boundaries 组——L5b）", () => {
  const boundaryNode: FixtureNode = {
    node_id: "site::boundary",
    semantic: "site_boundary",
    primitive: {
      kind: "polyline",
      dims: { x0: -5, y0: -5, x1: 45, y1: -5, x2: 45, y2: 30, x3: -5, y3: 30 },
      semantic: "site_boundary",
    },
  };

  it("polyline kind 归 boundaries 组：x{i}/y{i} 压平键按索引序解码为平面点序", () => {
    const out = projectScene(fixture({ nodes: [boundaryNode], root: ["site::boundary"] }) as never);
    expect(out.boundaries).toHaveLength(1);
    expect(out.boundaries[0]?.id).toBe("site::boundary");
    expect(out.boundaries[0]?.points).toEqual([
      [-5, -5],
      [45, -5],
      [45, 30],
      [-5, 30],
    ]);
  });

  it("红线顶点计入 bounds（总装取景覆盖红线外框——平面 y 映射世界 Z）", () => {
    const out = projectScene(fixture({ nodes: [boundaryNode], root: ["site::boundary"] }) as never);
    expect(out.bounds).toEqual({ min: [-5, 0, -5], max: [45, 0, 30] });
  });

  it("红线不污染三组（solids/waters/internals 恒空）", () => {
    const out = projectScene(fixture({ nodes: [boundaryNode], root: ["site::boundary"] }) as never);
    expect(out.solids).toHaveLength(0);
    expect(out.waters).toHaveLength(0);
    expect(out.internals).toHaveLength(0);
  });

  it("顶点不完整拒（y{i} 缺键——场景图损坏防御）", () => {
    const broken: FixtureNode = {
      ...boundaryNode,
      primitive: {
        kind: "polyline",
        dims: { x0: 0, y0: 0, x1: 10, y1: 10, x2: 20 },
        semantic: "site_boundary",
      },
    };
    expect(() =>
      projectScene(fixture({ nodes: [broken], root: ["site::boundary"] }) as never),
    ).toThrow(SceneProjectionError);
  });
});

describe("Internals 图元选择（dims 键驱动——FE1 M2）", () => {
  // 红先行：动态 import 隔离红面（实现前该导出不存在——单测红不殃及全文件）
  it("diameter 键在→cylinder（半径=直径/2[three 接口适配]，高度=depth）", async () => {
    const { internalsGeometry } = await import("../components/Internals");
    const node = {
      id: "cyl-1",
      kind: "cylinder",
      semantic: "aerator",
      position: [0, 0, 0] as [number, number, number],
      rotation: [0, 0, 0] as [number, number, number],
      dims: { diameter: 6, depth: 4 },
      instanceCount: 4,
      placements: [],
    };
    expect(internalsGeometry(node)).toEqual({ kind: "cylinder", args: [3, 3, 4] });
  });

  it("无 diameter 键→box（length/depth/width 直读；缺键兜底 1）", async () => {
    const { internalsGeometry } = await import("../components/Internals");
    const base = {
      id: "box-1",
      kind: "box",
      semantic: "aerator",
      position: [0, 0, 0] as [number, number, number],
      rotation: [0, 0, 0] as [number, number, number],
      instanceCount: 12,
      placements: [],
    };
    expect(internalsGeometry({ ...base, dims: { length: 0.5, width: 0.5, depth: 0.5 } })).toEqual(
      { kind: "box", args: [0.5, 0.5, 0.5] },
    );
    expect(internalsGeometry({ ...base, dims: {} })).toEqual({ kind: "box", args: [1, 1, 1] });
  });
});

// ═══ UX2 U2（取景自适应 2026-08-30）：bounds 聚合 TDD 红先——AABB 全
// placements（solids+waters+internals）；机位薄壳不测（app 层惯例） ═══
describe("UX2 projectScene：bounds 聚合（全 placements AABB——D5）", () => {
  it("数值锚：fixture 全 placements 的 AABB（含 internals 摆置极值）", async () => {
    const { projectScene: project } = await import("./projectScene");
    const out = project(fixture() as never);
    // 摆置极值实锚：y max=0.5 与 z max=2 来自 aerator 12 实例方阵
    // （y=0.5 摆位列、z=1+row*0.5 至 2——z 极值非原型 position 的 1）；
    // x 极值=chan-1 的 30；y min=ground-1 的 -0.01。
    expect(out.bounds).toEqual({
      min: [0, -0.01, 0],
      max: [30, 0.5, 2],
    });
  });

  it("空场景（nodes 空→placements 总数 0）bounds=null", async () => {
    const { projectScene: project } = await import("./projectScene");
    const out = project(fixture({ nodes: [], root: [] }) as never);
    expect(out.bounds).toBeNull();
  });

  it("单节点场景 bounds=该 placement 的退化盒（min=max）", async () => {
    const { projectScene: project } = await import("./projectScene");
    const nodes: FixtureNode[] = [
      {
        node_id: "solo-1",
        semantic: "gate",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "gate" },
        position: [5, 2, -3],
      },
    ];
    const out = project(fixture({ nodes, root: ["solo-1"] }) as never);
    expect(out.bounds).toEqual({ min: [5, 2, -3], max: [5, 2, -3] });
  });
});
