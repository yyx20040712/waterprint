/**
 * 布置编辑器纯函数层测试：site 窄化门/足迹投影/PUT 载荷/吸附/折线删除
 * （node 环境）。
 *
 * 输入:  projectSite 纯函数族（node 环境——零 DOM 依赖，先红后绿）
 * 输出:  契约断言（D6 轻门逐类拒带定位/缺 site 默认/footprint 键镜像+
 *        children 聚合+instance 方阵/withSite 深层引用相等/snap·rotation
 *        数值例/removeLineAt 删项·越界直通[B4 笔②]/projectSiteSafe 围栏
 *        三分支[B4 笔③——合法透传/SEP 原实例/非 SEP 归一包装]；L4a
 *        boundary 红线窄化门——缺省空合法/≥3 点门镜像 core validator；
 *        measure 用例 B4 笔②迁 siteGeometry.test.ts——源件镜像归位+
 *        行预算门禁拆文件）
 */
import { describe, expect, it } from "vitest";

import type { SceneResponse } from "../../../shared/api/generated/model";
import {
  SiteProjectionError,
  narrowSiteDesign,
  projectSite,
  projectSiteSafe,
  removeLineAt,
  snapRotation,
  snapToGrid,
  withSite,
} from "./projectSite";

// ── fixture（scene 节点按 core scene.py node_id="{unit_id}::{semantic}" 产出面） ──

type FixtureNode = {
  node_id: string;
  semantic: string;
  primitive: { kind: string; dims: Record<string, number>; semantic: string };
  position?: [number, number, number];
  instance_count?: number;
  children?: FixtureNode[];
};

function sceneOf(nodes: FixtureNode[]): SceneResponse {
  return {
    condition_key: "design",
    nodes,
    root: nodes.map((node) => node.node_id),
    scene_version: "waterprint-scene-5/z-up/m",
    stale: false,
  };
}

function boxNode(
  nodeId: string,
  dims: Record<string, number>,
  position?: [number, number, number],
): FixtureNode {
  return {
    node_id: nodeId,
    semantic: "pool_wall",
    primitive: { kind: "box", dims, semantic: "pool_wall" },
    ...(position !== undefined ? { position } : {}),
  };
}

// ── narrowSiteDesign：D6 轻形状门 ──

describe("narrowSiteDesign（site 弱类型窄化——缺省宽容/逐类拒带定位）", () => {
  it("缺 site 键=全默认态（core SiteDesign default_factory 同象）", () => {
    expect(narrowSiteDesign(undefined)).toEqual({
      structures: {},
      roads: [],
      corridors: [],
      boundary: [],
      options: { coord_grid: 10.0, wind_rose: null },
    });
  });

  it("合法全量过：值镜像+可选键缺省补全（rotation 0/ground_elevation null）", () => {
    const site = narrowSiteDesign({
      structures: {
        tank: { x: 1.5, y: -2, rotation: 90, ground_elevation: 103.2 },
        pump: { x: 0, y: 0 },
      },
      roads: [{ centerline: [{ x: 0, y: 0 }, { x: 10, y: 0 }], width_m: 4 }],
      corridors: [
        { centerline: [{ x: 0, y: 0 }, { x: 0, y: 20 }], width_m: 1.5, kind: "water" },
      ],
      boundary: [
        { x: -5, y: -5 },
        { x: 45, y: -5 },
        { x: 45, y: 30 },
        { x: -5, y: 30 },
      ],
      options: { coord_grid: 5, wind_rose: { N: 0.3, S: 0.1 } },
    });
    expect(site.structures["tank"]).toEqual({
      x: 1.5,
      y: -2,
      rotation: 90,
      ground_elevation: 103.2,
    });
    expect(site.structures["pump"]).toEqual({
      x: 0,
      y: 0,
      rotation: 0,
      ground_elevation: null,
    });
    expect(site.roads).toEqual([
      { centerline: [{ x: 0, y: 0 }, { x: 10, y: 0 }], width_m: 4 },
    ]);
    expect(site.corridors[0]?.kind).toBe("water");
    expect(site.boundary).toEqual([
      { x: -5, y: -5 },
      { x: 45, y: -5 },
      { x: 45, y: 30 },
      { x: -5, y: 30 },
    ]); // L4a 红线顶点序镜像（值透传——闭合语义归渲染/出图面）
    expect(site.options).toEqual({ coord_grid: 5, wind_rose: { N: 0.3, S: 0.1 } });
  });

  it("structures 逐类拒：容器非对象/值非对象/x 非数/ground_elevation 非数非 null——带键定位", () => {
    expect(() => narrowSiteDesign({ structures: [] })).toThrow(SiteProjectionError);
    expect(() => narrowSiteDesign({ structures: [] })).toThrow(/design\.site\.structures/);
    expect(() => narrowSiteDesign({ structures: { tank: 1 } })).toThrow(
      /design\.site\.structures\[tank\]/,
    );
    expect(() =>
      narrowSiteDesign({ structures: { tank: { x: "1", y: 0 } } }),
    ).toThrow(/design\.site\.structures\[tank\]\.x/);
    expect(() =>
      narrowSiteDesign({ structures: { tank: { x: 0, y: 0, rotation: "90" } } }),
    ).toThrow(/rotation/);
    expect(() =>
      narrowSiteDesign({
        structures: { tank: { x: 0, y: 0, ground_elevation: "103" } },
      }),
    ).toThrow(/design\.site\.structures\[tank\]\.ground_elevation/);
  });

  it("roads/corridors 逐类拒：容器非数组/centerline 非数组/点坐标非数/width_m 非数/kind 非串——带索引定位", () => {
    expect(() => narrowSiteDesign({ roads: {} })).toThrow(/design\.site\.roads/);
    expect(() =>
      narrowSiteDesign({ roads: [{ centerline: "x", width_m: 4 }] }),
    ).toThrow(/design\.site\.roads\[0\]\.centerline/);
    expect(() =>
      narrowSiteDesign({
        roads: [{ centerline: [{ x: 0, y: "1" }, { x: 2, y: 2 }], width_m: 4 }],
      }),
    ).toThrow(/design\.site\.roads\[0\]\.centerline\[0\]\.y/);
    expect(() =>
      narrowSiteDesign({
        roads: [{ centerline: [{ x: 0, y: 0 }, { x: 2, y: 2 }], width_m: "4" }],
      }),
    ).toThrow(/design\.site\.roads\[0\]\.width_m/);
    expect(() =>
      narrowSiteDesign({
        corridors: [
          { centerline: [{ x: 0, y: 0 }, { x: 2, y: 2 }], width_m: 1, kind: 7 },
        ],
      }),
    ).toThrow(/design\.site\.corridors\[0\]\.kind/);
  });

  it("options 逐类拒：coord_grid 非数/wind_rose 值非数——带键定位；缺省=core 默认 10.0", () => {
    expect(() => narrowSiteDesign({ options: { coord_grid: "10" } })).toThrow(
      /design\.site\.options\.coord_grid/,
    );
    expect(() =>
      narrowSiteDesign({ options: { wind_rose: { N: "0.3" } } }),
    ).toThrow(/design\.site\.options\.wind_rose\[N\]/);
    expect(narrowSiteDesign({ options: {} }).options.coord_grid).toBe(10.0);
    expect(narrowSiteDesign({ options: { wind_rose: null } }).options.wind_rose).toBeNull();
  });

  it("boundary（L4a 红线）：缺省/空数组合法；≥3 点过；1/2 点拒（core ≥3 点 validator 镜像）", () => {
    expect(narrowSiteDesign({ boundary: [] }).boundary).toEqual([]);
    const triangle = [
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 0, y: 10 },
    ];
    expect(narrowSiteDesign({ boundary: triangle }).boundary).toEqual(triangle);
    expect(() => narrowSiteDesign({ boundary: triangle.slice(0, 1) })).toThrow(
      /design\.site\.boundary/,
    );
    expect(() => narrowSiteDesign({ boundary: triangle.slice(0, 2) })).toThrow(
      /design\.site\.boundary/,
    );
  });

  it("boundary 逐类拒：非数组/点非对象/坐标非数——带索引定位", () => {
    expect(() => narrowSiteDesign({ boundary: {} })).toThrow(/design\.site\.boundary/);
    expect(() =>
      narrowSiteDesign({ boundary: ["x", { x: 0, y: 0 }, { x: 1, y: 1 }] }),
    ).toThrow(/design\.site\.boundary\[0\]/);
    expect(() =>
      narrowSiteDesign({ boundary: [{ x: 0, y: "1" }, { x: 1, y: 1 }, { x: 2, y: 0 }] }),
    ).toThrow(/design\.site\.boundary\[0\]\.y/);
  });

  it("未知键透传不拒（server strict 面是唯一语义门——TS 零业务复制）", () => {
    expect(() =>
      narrowSiteDesign({
        structures: { tank: { x: 0, y: 0, future_key: 1 } },
        future_section: { a: 1 },
      }),
    ).not.toThrow();
  });
});

// ── projectSite：投影（footprint=scene dims 键镜像 PoolBox 消费面） ──

describe("projectSite（design+scene → 渲染模型——纯函数确定性）", () => {
  it("scene=null → footprint 全 null+designUnitIds=design.nodes 键集+摆放值透传", () => {
    const model = projectSite(
      {
        nodes: { tank: { kind: "inlet" }, pump: {}, lab: {} },
        site: {
          structures: { tank: { x: 3, y: 4, rotation: 90, ground_elevation: 102.5 } },
        },
      },
      null,
    );
    expect(model.structures).toEqual([
      {
        unitId: "tank",
        x: 3,
        y: 4,
        rotation: 90,
        groundElevation: 102.5,
        footprint: null,
      },
    ]);
    expect(model.designUnitIds).toEqual(["lab", "pump", "tank"]);
  });

  it("scene 命中 box：footprint w/h=length×width 同对键（镜像 PoolBox boxGeometry 消费面）", () => {
    const model = projectSite(
      { nodes: { tank: {} }, site: { structures: { tank: { x: 0, y: 0 } } } },
      sceneOf([
        boxNode("tank::pool_wall", { length: 30, width: 12, depth: 4 }),
        {
          node_id: "tank::water_surface",
          semantic: "water_surface",
          primitive: {
            kind: "water_surface",
            dims: { level: 3, freeboard: 0.5 },
            semantic: "water_surface",
          },
        },
      ]),
    );
    // water_surface 无水平键不计入（level/freeboard 非足迹面）
    expect(model.structures[0]?.footprint).toEqual({ w: 30, h: 12 });
  });

  it("cylinder：footprint w=h=diameter（镜像 PoolBox diameter 消费面）", () => {
    const model = projectSite(
      { nodes: { cls: {} }, site: { structures: { cls: { x: 0, y: 0 } } } },
      sceneOf([
        {
          node_id: "cls::pool_cylinder",
          semantic: "pool_wall",
          primitive: {
            kind: "cylinder",
            dims: { diameter: 20, depth: 5 },
            semantic: "pool_wall",
          },
        },
      ]),
    );
    expect(model.structures[0]?.footprint).toEqual({ w: 20, h: 20 });
  });

  it("children 展开聚合包围盒：父矩形∪子矩形（位置偏移计入——z-up 平面=x,y 槽）", () => {
    const model = projectSite(
      { nodes: { tank: {} }, site: { structures: { tank: { x: 0, y: 0 } } } },
      sceneOf([
        {
          ...boxNode("tank::group", { length: 10, width: 6, depth: 3 }),
          children: [boxNode("tank::group::wing", { length: 4, width: 2, depth: 1 }, [8, 3, 0])],
        },
      ]),
    );
    // 父 x∈[-5,5]/y∈[-3,3] ∪ 子 x∈[6,10]/y∈[2,4] → w=15/h=7
    // （L5R N-1：平面取 (x, y) 槽——fixture [8,3,0]=东 8/北 3/标高 0）
    expect(model.structures[0]?.footprint).toEqual({ w: 15, h: 7 });
  });

  it("instance_count>1 近方阵展开（projectScene placementsOf 同构：cols=ceil(√n) 步距=length/width）", () => {
    const model = projectSite(
      { nodes: { tank: {} }, site: { structures: { tank: { x: 0, y: 0 } } } },
      sceneOf([
        {
          ...boxNode("tank::aerator", { length: 2, width: 2, depth: 1 }),
          instance_count: 4,
        },
      ]),
    );
    // 2×2 方阵（步距 2）：x/z ∈ [-1,3] → w=h=4
    expect(model.structures[0]?.footprint).toEqual({ w: 4, h: 4 });
  });

  it("scene 未命中 unit（node_id 前缀无该 unit_id）→ footprint=null", () => {
    const model = projectSite(
      {
        nodes: { tank: {}, other: {} },
        site: { structures: { tank: { x: 0, y: 0 }, other: { x: 0, y: 0 } } },
      },
      sceneOf([boxNode("other::pool_wall", { length: 8, width: 6, depth: 3 })]),
    );
    const byId = new Map(model.structures.map((s) => [s.unitId, s]));
    expect(byId.get("tank")?.footprint).toBeNull();
    expect(byId.get("other")?.footprint).toEqual({ w: 8, h: 6 });
  });

  it("roads/corridors/options 透传+structures 字典序（确定性渲染序）", () => {
    const model = projectSite(
      {
        nodes: { b: {}, a: {} },
        site: {
          structures: { b: { x: 1, y: 1 }, a: { x: 0, y: 0 } },
          roads: [{ centerline: [{ x: 0, y: 0 }, { x: 1, y: 1 }], width_m: 4 }],
          corridors: [
            { centerline: [{ x: 0, y: 0 }, { x: 1, y: 1 }], width_m: 2, kind: "power" },
          ],
          options: { coord_grid: 20 },
        },
      },
      null,
    );
    expect(model.structures.map((s) => s.unitId)).toEqual(["a", "b"]);
    expect(model.roads).toHaveLength(1);
    expect(model.corridors[0]?.kind).toBe("power");
    expect(model.options.coord_grid).toBe(20);
  });

  it("designUnitIds=design.nodes 键集字典序稳定；site 已布置单元不影响该键集", () => {
    const model = projectSite(
      {
        nodes: { pump: {}, tank: {}, lab: {} },
        site: { structures: { tank: { x: 0, y: 0 } } },
      },
      null,
    );
    // 键集全集直出（已摆 tank 仍在——待摆=组件层减 draft 编辑键集现算）
    expect(model.designUnitIds).toEqual(["lab", "pump", "tank"]);
  });

  it("design.nodes 非对象/非法 site 形状 → SiteProjectionError 透传", () => {
    expect(() => projectSite({ nodes: [] }, null)).toThrow(/design\.nodes/);
    expect(() =>
      projectSite({ nodes: {}, site: { structures: [] } }, null),
    ).toThrow(SiteProjectionError);
  });
});

// ── withSite：PUT 结构化替换 ──

describe("withSite（仅替换 design.site——withConstraintChoices 同构禁散拼）", () => {
  it("仅 site 键变化：其余顶层/design 深层原样引用相等", () => {
    const nodes = { tank: { kind: "inlet" } };
    const edges = [{ src: {}, dst: {} }];
    const view = { layout: {} };
    const raw = {
      format_version: "waterprint-project-1",
      design: { nodes, edges, assumption_overrides: { a: 1 }, site: { structures: {} } },
      view,
      metadata: {},
    };
    const site = narrowSiteDesign(undefined);
    const out = withSite(raw, site);
    const outDesign = out["design"] as Record<string, unknown>;
    expect(outDesign["site"]).toBe(site);
    expect(outDesign["nodes"]).toBe(nodes);
    expect(outDesign["edges"]).toBe(edges);
    expect(outDesign["assumption_overrides"]).toEqual({ a: 1 });
    expect(out["view"]).toBe(view);
    expect(out["format_version"]).toBe("waterprint-project-1");
  });

  it("空 design 补全骨架（design={} → 注入 site）；raw/design 非对象 → 拒", () => {
    const site = narrowSiteDesign(undefined);
    const out = withSite({ format_version: "v", design: {}, metadata: {} }, site);
    expect(out["design"]).toEqual({ site });
    expect(() => withSite({ metadata: {} } as Record<string, unknown>, site)).toThrow(
      SiteProjectionError,
    );
    expect(() => withSite("x" as unknown as Record<string, unknown>, site)).toThrow(
      SiteProjectionError,
    );
  });
});

// ── 吸附纯函数数值例 ──

describe("snapToGrid（网点吸附——round(v/grid)*grid/1e-9 防浮尾/grid 无效直通）", () => {
  it("开=吸附网格（半值向上），关=原值防浮尾", () => {
    expect(snapToGrid(14, 10, true)).toBe(10);
    expect(snapToGrid(15, 10, true)).toBe(20);
    expect(snapToGrid(23.6, 10, true)).toBe(20);
    expect(snapToGrid(-14, 10, true)).toBe(-10);
    expect(snapToGrid(12.300000000000001, 10, false)).toBe(12.3);
    expect(snapToGrid(0.1 + 0.2, 0.1, true)).toBe(0.3);
  });

  it("grid 非正数=防御直通（不产 NaN）", () => {
    expect(snapToGrid(7, 0, true)).toBe(7);
    expect(snapToGrid(7, -5, true)).toBe(7);
  });
});

describe("snapRotation（90° 档位表/自由角 1° 舍入/归一 [0,360)）", () => {
  it("90° 档位：就近取整档（45 进位 90——JS round 半值向上）", () => {
    expect(snapRotation(0, false)).toBe(0);
    expect(snapRotation(44, false)).toBe(0);
    expect(snapRotation(45, false)).toBe(90);
    expect(snapRotation(134, false)).toBe(90);
    expect(snapRotation(135, false)).toBe(180);
    expect(snapRotation(310, false)).toBe(270);
    expect(snapRotation(350, false)).toBe(0); // 360 归一 0
    expect(snapRotation(-90, false)).toBe(270);
  });

  it("free=true：1° 舍入+归一", () => {
    expect(snapRotation(45.4, true)).toBe(45);
    expect(snapRotation(-0.4, true)).toBe(0);
    expect(snapRotation(719.6, true)).toBe(0); // 720 归一 0
  });
});

// ── removeLineAt：折线删除（B4 笔② R2） ──
// （measureToNearest 用例 B4 笔②迁 siteGeometry.test.ts——源件镜像归位+行预算门禁）

describe("removeLineAt（B4 笔② R2——roads/corridors immutable splice 删除）", () => {
  const lines = [{ v: "a" }, { v: "b" }, { v: "c" }];

  it("删中间项：copy-on-write 新数组+原数组不变+余项前移", () => {
    const next = removeLineAt(lines, 1);
    expect(next).toEqual([{ v: "a" }, { v: "c" }]);
    expect(next).not.toBe(lines); // 新引用——draft dirty 深比较可检出
    expect(lines).toHaveLength(3); // 原数组零突变
  });

  it("越界索引=原数组引用直通（拒删不变性——选中索引失效防御面）", () => {
    expect(removeLineAt(lines, 3)).toBe(lines);
    expect(removeLineAt(lines, -1)).toBe(lines);
    const empty: { v: string }[] = [];
    expect(removeLineAt(empty, 0)).toBe(empty); // 空容器直通
  });
});

// ── projectSiteSafe：投影围栏（B4 笔③行预算拆法——错误捕获归 lib 纯面） ──

describe("projectSiteSafe（design+scene → {model, error}——组件层 useMemo 零 try/catch）", () => {
  it("合法 design：model 产出+error=null（围栏透明直通）", () => {
    const result = projectSiteSafe(
      { nodes: { tank: {} }, site: { structures: { tank: { x: 3, y: 4 } } } },
      null,
    );
    expect(result.error).toBeNull();
    expect(result.model?.structures[0]?.footprint).toBeNull(); // scene=null → 示意矩形态
    expect(result.model?.designUnitIds).toEqual(["tank"]);
  });

  it("非法 design：SiteProjectionError 原实例透传+model=null（错误薄壳呈现面）", () => {
    const result = projectSiteSafe({ nodes: "异形" }, null);
    expect(result.model).toBeNull();
    expect(result.error).toBeInstanceOf(SiteProjectionError);
    expect(result.error?.message).toContain("design.nodes");
  });

  it("非 SiteProjectionError 异常：归一包装（String 化消息不裸抛出围栏）", () => {
    // 惰性 getter 抛非 SEP 异常——围栏须兜底归一（防御面：错误薄壳恒可呈现）
    const hostile: Record<string, unknown> = {};
    Object.defineProperty(hostile, "nodes", {
      enumerable: true,
      get() {
        throw new Error("getter 爆炸");
      },
    });
    const result = projectSiteSafe(hostile, null);
    expect(result.model).toBeNull();
    expect(result.error).toBeInstanceOf(SiteProjectionError);
    expect(result.error?.message).toContain("getter 爆炸");
  });
});
