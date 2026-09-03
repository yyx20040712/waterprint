/**
 * 投影层纯函数测试：SceneGraph JSON → 渲染描述（D4 前端测试策略五面）。
 *
 * 输入:  projectScene 纯函数（node 环境——零 WebGL 依赖，先红后绿）
 * 输出:  投影契约断言（SCENE_VERSION 门/七 kind 完备/摆置确定性/语义 token/
 *        root 一致性；L5b：rotation 放行+scale 仍拒+红线 polyline 分组；
 *        L5R：换轴锚 (x,z,−y)+rz→Y 轴；L6：strip 第五分组 routes——semantic
 *        透传/角点解码/bounds 并入/损坏拒——色值断言零含（G1-09 先例））
 */
import { describe, expect, it } from "vitest";

import {
  RENDER_SCENE_VERSION,
  SceneProjectionError,
  projectScene,
} from "./projectScene";

const VERSION = "waterprint-scene-3/z-up/m";

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
  it("RENDER_SCENE_VERSION 步进 -3（L6 strip 图元语义变即步进——core SCENE_VERSION 双端同窗）", () => {
    expect(RENDER_SCENE_VERSION).toBe("waterprint-scene-3/z-up/m");
  });

  it("非 z-up 标签拒且原因附版本值（L5R 轴标签勘正——步进时误记的 y-up 串同拒）", () => {
    const bad = fixture({ scene_version: "waterprint-scene-2/y-up/m" });
    expect(() => projectScene(bad as never)).toThrow(SceneProjectionError);
    try {
      projectScene(bad as never);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect((error as Error).message).toContain("waterprint-scene-2/y-up/m");
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
    // 步距=原型占位（length=0.5→X 向、width=0.5→世界 Z 向——类型化摆放
    // 非业务推导；origin 已换轴 [2, 1, −0.5]=core (2, 北 0.5, 标高 1)）
    const first = aerator?.placements[0];
    const second = aerator?.placements[1];
    expect(first).toEqual([2, 1, -0.5]);
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

describe("projectScene：非默认变换门（L5R 单轴收编：rz 换算 Y 轴/rx·ry 拒/scale 仍拒）", () => {
  it("平面旋转换算：core (0,0,π/2) → three (0,π/2,0)（保手性映射角不变——绕世界竖轴）", () => {
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
    expect(out.solids[0]?.rotation).toEqual([0, Math.PI / 2, 0]);
  });

  it("rx 非零拒（core 契约恒 (0,0,rz)——rx/ry 非零=场景图契约漂移）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "rxd-1",
        semantic: "media",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "media" },
        rotation: [0.1, 0, 0],
      },
    ];
    const bad = fixture({ nodes, root: ["rxd-1"] });
    try {
      projectScene(bad as never);
      expect.unreachable("必须抛出");
    } catch (error) {
      expect(error).toBeInstanceOf(SceneProjectionError);
      expect((error as Error).message).toContain("rxd-1");
    }
  });

  it("ry 非零拒（同上——三维轴语义不明即拒，不放行不静默丢）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "ryd-1",
        semantic: "media",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "media" },
        rotation: [0, 0.3, 0],
      },
    ];
    const bad = fixture({ nodes, root: ["ryd-1"] });
    expect(() => projectScene(bad as never)).toThrow(SceneProjectionError);
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
    primitive: { kind: "polyline", dims: { x0: -5, y0: -5, x1: 45, y1: -5, x2: 45, y2: 30, x3: -5, y3: 30 }, semantic: "site_boundary" },
  };

  it("polyline kind 归 boundaries 组：x{i}/y{i} 压平键解码并换轴为世界水平面点（北=−Z）", () => {
    const out = projectScene(fixture({ nodes: [boundaryNode], root: ["site::boundary"] }) as never);
    expect(out.boundaries).toHaveLength(1);
    expect(out.boundaries[0]?.id).toBe("site::boundary");
    expect(out.boundaries[0]?.points).toEqual([
      [-5, 5],
      [45, 5],
      [45, -30],
      [-5, -30],
    ]);
  });

  it("红线顶点计入 bounds（总装取景覆盖红线外框——北=−Z 换轴随行）", () => {
    const out = projectScene(fixture({ nodes: [boundaryNode], root: ["site::boundary"] }) as never);
    expect(out.bounds).toEqual({ min: [-5, 0, -30], max: [45, 0, 5] });
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
      primitive: { kind: "polyline", dims: { x0: 0, y0: 0, x1: 10, y1: 10, x2: 20 }, semantic: "site_boundary" },
    };
    expect(() =>
      projectScene(fixture({ nodes: [broken], root: ["site::boundary"] }) as never),
    ).toThrow(SceneProjectionError);
  });
});

// ═══ L6（roads/corridors 条带 2026-09-04）：strip 第五分组 routes+角点解码
// +bounds 并入——红先行锚 scene_version: RENDER_SCENE_VERSION（kind 面直测）；
// 色值断言零含（归组件层，G1-09 先例） ═══
describe("projectScene：条带图元（strip → routes 组——L6）", () => {
  // core 产出锚（角点 core 预计算——零业务几何）：
  // road 段 (0,0)→(30,0)、width=4、n=(0,1)、half=2 → (0,2),(30,2),(30,−2),(0,−2)
  const roadNode: FixtureNode = {
    node_id: "site::road[0]",
    semantic: "site_road",
    primitive: { kind: "strip", dims: { x0: 0, y0: 2, x1: 30, y1: 2, x2: 30, y2: -2, x3: 0, y3: -2 }, semantic: "site_road" },
  };
  // corridor 段 (0,5)→(0,25)、width=2、n=(−1,0)、half=1 → (−1,5),(−1,25),(1,25),(1,5)
  const corridorNode: FixtureNode = {
    node_id: "site::corridor[0]",
    semantic: "site_corridor:water",
    primitive: { kind: "strip", dims: { x0: -1, y0: 5, x1: -1, y1: 25, x2: 1, y2: 25, x3: 1, y3: 5 }, semantic: "site_corridor:water" },
  };
  const routeScene = () => fixture({
    nodes: [roadNode, corridorNode],
    root: ["site::road[0]", "site::corridor[0]"],
    scene_version: RENDER_SCENE_VERSION,
  });

  it("strip 归 routes 组：semantic token 透传+角点序解码换轴（北=−Z，段数=点数/4）", () => {
    const out = projectScene(routeScene() as never);
    expect(out.routes).toHaveLength(2);
    expect(out.routes[0]?.node_id).toBe("site::road[0]");
    expect(out.routes[0]?.semantic).toBe("site_road");
    expect(out.routes[0]?.points).toEqual([[0, -2], [30, -2], [30, 2], [0, 2]]);
    expect(out.routes[1]?.node_id).toBe("site::corridor[0]");
    expect(out.routes[1]?.semantic).toBe("site_corridor:water");
    expect(out.routes[1]?.points).toEqual([[-1, -5], [-1, -25], [1, -25], [1, -5]]);
  });

  it("strip 全部角点计入 bounds（取景覆盖——boundary 顶点聚合先例照搬）", () => {
    const out = projectScene(routeScene() as never);
    expect(out.bounds).toEqual({ min: [-1, 0, -25], max: [30, 0, 2] });
  });

  it("strip 不污染四组（solids/waters/internals/boundaries 恒空）", () => {
    const out = projectScene(routeScene() as never);
    expect([out.solids, out.waters, out.internals, out.boundaries]).toStrictEqual([[], [], [], []]);
  });

  it("编码损坏拒：顶点数非 4 倍数（6 点=1.5 段）与压平键缺口（y{i} 缺键）", () => {
    const brokenCount: FixtureNode = {
      node_id: "site::road[1]",
      semantic: "site_road",
      primitive: { kind: "strip", dims: { x0: 0, y0: 0, x1: 10, y1: 0, x2: 10, y2: 5, x3: 0, y3: 5, x4: 1, y4: 1, x5: 2, y5: 2 }, semantic: "site_road" },
    };
    expect(() =>
      projectScene(fixture({ nodes: [brokenCount], root: ["site::road[1]"], scene_version: RENDER_SCENE_VERSION }) as never),
    ).toThrow(/site::road\[1\]/);
    const brokenGap: FixtureNode = {
      ...roadNode,
      primitive: { kind: "strip", dims: { x0: 0, y0: 2, x1: 30, y1: 2, x2: 30, y2: -2, x3: 0 }, semantic: "site_road" },
    };
    expect(() =>
      projectScene(fixture({ nodes: [brokenGap], root: ["site::road[0]"], scene_version: RENDER_SCENE_VERSION }) as never),
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
  it("数值锚：fixture 全 placements 的 AABB（含 internals 摆置极值，换轴后世界系）", () => {
    const out = projectScene(fixture() as never);
    // 换轴后世界系（y=标高槽=source z、z=−北槽）：y max=1（aerator 标高
    // 槽=source z=1）、z 极值 ±0.5（aerator 12 实例方阵 z=−0.5+row*0.5
    // 至 0.5）；x 极值=chan-1 的 30；y min=0（池体/水面标高槽全 0——
    // surf source y=0.1/ground −0.01 归世界 z=−0.1/0.01 在 z 极值内）。
    expect(out.bounds).toEqual({
      min: [0, 0, -0.5],
      max: [30, 1, 0.5],
    });
  });

  it("空场景（nodes 空→placements 总数 0）bounds=null", () => {
    const out = projectScene(fixture({ nodes: [], root: [] }) as never);
    expect(out.bounds).toBeNull();
  });

  it("单节点场景 bounds=该 placement 的退化盒（min=max，换轴后世界系）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "solo-1",
        semantic: "gate",
        primitive: { kind: "box", dims: { length: 1, width: 1, depth: 1 }, semantic: "gate" },
        position: [5, 2, -3],
      },
    ];
    const out = projectScene(fixture({ nodes, root: ["solo-1"] }) as never);
    expect(out.bounds).toEqual({ min: [5, -3, -2], max: [5, -3, -2] });
  });
});

// ═══ L5R（换轴收编 2026-09-03）：G1-01 教训钉进测试面——存储 z-up/
// 渲染 Y-up 保手性映射与平面旋转换算的端到端锚（A 二审矩阵+数值实证） ═══
describe("projectScene：L5R 换轴锚（保手性 (x,z,−y)——存储 z-up→渲染 Y-up）", () => {
  it("core site 摆放 (x=10, y北=20, z标高=0.5)+rz=π/2 → three (10, 0.5, −20)+绕 Y π/2（镜像 [x,z,y] 会使旋转视觉反向——弃用形）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "site-pool",
        semantic: "pool_wall",
        primitive: { kind: "box", dims: { length: 10, width: 4, depth: 3 }, semantic: "pool_wall" },
        position: [10, 20, 0.5],
        rotation: [0, 0, Math.PI / 2],
      },
    ];
    const out = projectScene(fixture({ nodes, root: ["site-pool"] }) as never);
    expect(out.solids[0]?.position).toEqual([10, 0.5, -20]);
    expect(out.solids[0]?.rotation).toEqual([0, Math.PI / 2, 0]);
  });

  it("水面抬升锚：core (0,0,水位 z) → three y=水位（北分量归 −Z——不悬空不水平偏移）", () => {
    const nodes: FixtureNode[] = [
      {
        node_id: "surf-z",
        semantic: "water_surface",
        primitive: {
          kind: "water_surface",
          dims: { level: 1.25, length: 4.5, width: 3 },
          semantic: "water_surface",
        },
        position: [0, 0, 1.25],
      },
    ];
    const out = projectScene(fixture({ nodes, root: ["surf-z"] }) as never);
    expect(out.waters[0]?.position).toEqual([0, 1.25, 0]);
  });
});
