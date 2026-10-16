/**
 * 取景对象=模型簇纯函数测试（V4 P8——uiglobal B 占比 3~5%；迭代二 2026-
 * 10-15 视觉门 08 帧回炉：图口径 modelBounds 被模板族多实例兜底方阵撑大
 * 〔渲染死码——Scene 渲染层 claimed 族 internals 不渲染，真形=TemplateUnit
 * 池内实例〕，供给改 modelClusterBounds 渲染真形口径+池组槽盒只取已摆
 * cell）。
 *
 * 输入:  projectScene+modelClusterBounds（golden 形状夹具——紧凑模型簇
 *        〔两池 110m 主线〕+640×420 地面 plane+±320/±210 红线+条带+
 *        迭代二夹具：池+2165 实例曝气器方阵）+frameCamera（iso 机位）
 *        +groupExtents（稀疏槽格夹具——offline 工况缺位槽形态）
 * 输出:  断言族：①簇 AABB=渲染真形（地面/红线/条带/claimed 族兜底方阵
 *        不入盒——bounds 对照锚证稀释面）②NDC 主轴跨≥0.6（线性主线
 *        单轴达标）+八角不裁切③空簇 null（Scene 回退现行为——源锚）
 *        ④迭代二逃逸面：兜底方阵把盒 z 撑 3.4 倍 vs 真形盒（claim 盲/
 *        claim 知双口径对照）⑤稀疏槽格+紧凑实体簇：取景吃已摆 cell
 *        不吃缺位槽大盒⑥claimed 含无 plan id=盒口径零改（V4 d1-W2——
 *        排除域×槽覆盖域交叉负例守卫锚）
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { frameCamera, V_FOV_DEG } from "./cameraFrame";
import {
  modelClusterBounds,
  projectScene,
  type SceneBounds,
} from "./projectScene";
import {
  groupExtents,
  type PoolClaim,
  type PoolGroupPlan,
} from "../assemble/poolGroup";
import type { FamilyEntry } from "../assemble/registry";

const TAN_HALF = Math.tan(((V_FOV_DEG / 2) * Math.PI) / 180);

/** 三元组构造（SceneResponse.position 元组面——直写字面量推断 number[]）。 */
const P = (x: number, y: number, z: number): [number, number, number] => [x, y, z];

/** golden 形状夹具（值域同 projectSceneFixtures.node 形——紧簇+大场地）。 */
const GOLDEN_SCENE = {
  scene_version: "waterprint-scene-6/z-up/m",
  condition_key: "design",
  stale: false,
  root: ["pool-1", "pool-2", "ground-1", "site-boundary", "road-1"],
  nodes: [
    { node_id: "pool-1", semantic: "pool_wall", primitive: { kind: "box", dims: { length: 30, width: 14, depth: 6 }, semantic: "pool_wall" }, position: P(0, 0, 0) },
    { node_id: "pool-2", semantic: "pool_wall", primitive: { kind: "box", dims: { length: 30, width: 14, depth: 6 }, semantic: "pool_wall" }, position: P(80, 0, 0) },
    { node_id: "ground-1", semantic: "ground", primitive: { kind: "plane", dims: { length: 640, width: 420 }, semantic: "ground" }, position: P(0, 0, 0) },
    { node_id: "site-boundary", semantic: "site_boundary", primitive: { kind: "polyline", dims: { x0: -320, y0: -210, x1: 320, y1: -210, x2: 320, y2: 210, x3: -320, y3: 210 }, semantic: "site_boundary" }, position: P(0, 0, 0) },
    { node_id: "road-1", semantic: "site_road", primitive: { kind: "strip", dims: { x0: -300, y0: -190, x1: 300, y1: -190, x2: 300, y2: -186, x3: -300, y3: -186 }, semantic: "site_road" }, position: P(0, 0, 0) },
  ],
};

/** 迭代二逃逸面夹具：池体+claimed 族多实例曝气器（2165 实例兜底方阵
 *  —golden 实测形态同构：aerator inst=2165 方阵 ≈141×138m）。 */
const ARRAY_SCENE = {
  scene_version: "waterprint-scene-6/z-up/m",
  condition_key: "design",
  stale: false,
  root: ["municipal_aao::pool_wall", "municipal_aao::aerator"],
  nodes: [
    { node_id: "municipal_aao::pool_wall", semantic: "pool_wall", primitive: { kind: "box", dims: { length: 95, width: 38, depth: 5.3 }, semantic: "pool_wall" }, position: P(0, 0, 0) },
    { node_id: "municipal_aao::aerator", semantic: "aerator", primitive: { kind: "box", dims: { length: 3, width: 3, depth: 3 }, semantic: "aerator" }, position: P(0, 0, 0), instance_count: 2165 },
  ],
};

type Tri = [number, number, number];
const dot3 = (a: Tri, b: Tri): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross3 = (a: Tri, b: Tri): Tri => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const norm3 = (a: Tri): number => Math.hypot(a[0], a[1], a[2]);
const scale3 = (a: Tri, k: number): Tri => [a[0] * k, a[1] * k, a[2] * k];

/** AABB 八角 NDC 投影（lookAt 基——cameraFrame.test 同式）。 */
function ndcCorners(bounds: SceneBounds, position: Tri, center: Tri, aspect: number) {
  const away: Tri = [position[0] - center[0], position[1] - center[1], position[2] - center[2]];
  const zAxis = scale3(away, 1 / norm3(away));
  const up: Tri = [0, 1, 0];
  const xRaw = cross3(up, zAxis);
  const xAxis = scale3(xRaw, 1 / norm3(xRaw));
  const yAxis = cross3(zAxis, xAxis);
  const e: Tri = [
    (bounds.max[0] - bounds.min[0]) / 2,
    (bounds.max[1] - bounds.min[1]) / 2,
    (bounds.max[2] - bounds.min[2]) / 2,
  ];
  const xs: number[] = [];
  const ys: number[] = [];
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      for (const sz of [-1, 1]) {
        const corner: Tri = [
          center[0] + sx * e[0],
          center[1] + sy * e[1],
          center[2] + sz * e[2],
        ];
        const d: Tri = [
          corner[0] - position[0],
          corner[1] - position[1],
          corner[2] - position[2],
        ];
        const depth = -dot3(d, zAxis);
        xs.push(dot3(d, xAxis) / (depth * TAN_HALF * aspect));
        ys.push(dot3(d, yAxis) / (depth * TAN_HALF));
      }
    }
  }
  return { xs, ys };
}

describe("viewer3d·V4 取景盒=模型簇（P8——供给面）", () => {
  it("簇 AABB：地面/红线/条带不入盒（bounds 对照锚）", () => {
    const out = projectScene(GOLDEN_SCENE as never);
    const cluster = modelClusterBounds(out, []);
    expect(cluster).not.toBeNull();
    // 模型簇=两池足迹：x∈[-15,95]/y∈[-3,3]/z∈[-7,7]（世界系换轴后同形）
    expect(cluster?.min[0]).toBeCloseTo(-15, 9);
    expect(cluster?.max[0]).toBeCloseTo(95, 9);
    expect(cluster?.min[1]).toBeCloseTo(-3, 9);
    expect(cluster?.max[1]).toBeCloseTo(3, 9);
    expect(cluster?.min[2]).toBeCloseTo(-7, 9);
    expect(cluster?.max[2]).toBeCloseTo(7, 9);
    // 对照：scene.bounds 吃红线/地面 → 场地量级（=图口径稀释源之一）
    expect(out.bounds?.min[0]).toBeLessThanOrEqual(-320);
    expect(out.bounds?.max[0]).toBeGreaterThanOrEqual(320);
  });

  it("空簇（仅红线/条带场景）modelClusterBounds=null（Scene 回退现行为）", () => {
    const out = projectScene(({
      ...GOLDEN_SCENE,
      root: ["site-boundary", "road-1"],
      nodes: GOLDEN_SCENE.nodes.filter(
        (node) => node.node_id === "site-boundary" || node.node_id === "road-1",
      ),
    }) as never);
    expect(modelClusterBounds(out, [])).toBeNull();
    expect(out.bounds).not.toBeNull(); // 场地框仍在（地面/灯位面沿承）
  });
});

describe("viewer3d·V4 取景盒=模型簇（P8——NDC 跨度红证）", () => {
  it("golden 线性主线：簇投影主轴跨≥0.6（iso/aspect=2——单轴达标）", () => {
    const out = projectScene(GOLDEN_SCENE as never);
    const cluster = modelClusterBounds(out, []) as SceneBounds;
    const aspect = 2;
    const frame = frameCamera("iso", cluster, aspect);
    const { xs, ys } = ndcCorners(cluster, frame.position, frame.center, aspect);
    const spanX = Math.max(...xs) - Math.min(...xs);
    const spanY = Math.max(...ys) - Math.min(...ys);
    // 主轴（水平——主线沿 X）跨≥0.6：图口径取景（吃场地框）实测簇占比
    // 3~5%——簇取景盒下簇占屏主量级
    expect(spanX).toBeGreaterThanOrEqual(0.6);
    expect(Math.max(spanX, spanY)).toBeGreaterThanOrEqual(0.6);
    // margin 不裁切沿承：八角 |NDC|≤1
    for (const x of xs) expect(Math.abs(x)).toBeLessThanOrEqual(1);
    for (const y of ys) expect(Math.abs(y)).toBeLessThanOrEqual(1);
  });

  it("对照锚：图口径取景（拟合 scene.bounds）下簇主轴跨<0.6（稀释实证）", () => {
    const out = projectScene(GOLDEN_SCENE as never);
    const cluster = modelClusterBounds(out, []) as SceneBounds;
    const aspect = 2;
    const frame = frameCamera("iso", out.bounds, aspect);
    const { xs } = ndcCorners(cluster, frame.position, frame.center, aspect);
    const spanX = Math.max(...xs) - Math.min(...xs);
    expect(spanX).toBeLessThan(0.6); // 图口径供给=簇过远（uiglobal 3~5% 量级）
  });
});

describe("viewer3d·V4 迭代二（渲染真形口径——08 帧回炉逃逸面）", () => {
  it("claimed 族兜底方阵不入簇盒：claim 知口径=池盒，claim 盲口径被方阵撑大", () => {
    const out = projectScene(ARRAY_SCENE as never);
    const graph = modelClusterBounds(out, []); // claim 盲=图口径（方阵计入）
    const rendered = modelClusterBounds(out, ["municipal_aao"]); // claim 知
    // 图口径：aerator 2165 方阵（cols=47×3m）把 z 撑到 ±70.5（golden 实测同构）
    expect(graph?.min[2]).toBeCloseTo(-70.5, 6);
    expect(graph?.max[2]).toBeCloseTo(70.5, 6);
    // 渲染真形：池宽 38 → z∈±19（方阵足迹=渲染死码剔除）
    expect(rendered?.min[2]).toBeCloseTo(-19, 6);
    expect(rendered?.max[2]).toBeCloseTo(19, 6);
    expect(rendered?.min[0]).toBeCloseTo(-47.5, 6); // 池长 95 → x∈±47.5
    // 稀释倍率对照（golden 实测 z 跨 141 vs 41 ≈3.4 倍同构）
    const zSpanGraph = (graph?.max[2] ?? 0) - (graph?.min[2] ?? 0);
    const zSpanRendered = (rendered?.max[2] ?? 0) - (rendered?.min[2] ?? 0);
    expect(zSpanGraph / zSpanRendered).toBeGreaterThanOrEqual(3);
  });

  it("claimed 含无 plan id=盒口径零改（d1-W2——排除域×槽覆盖域交叉负例）", () => {
    // no_plan_unit=场景零节点的 claimed id（claimTemplateUnits 键与场景
    // 节点集非同域）：Set 查询天然容纳未知 id——不贡献幻影盒也不抛错；
    // 与不含该 id 的盒口径逐值相等（守卫锚：实现若改走 plan 键集过滤或
    // 对未知 id throw 即本例红）
    const out = projectScene(ARRAY_SCENE as never);
    const withUnknown = modelClusterBounds(out, ["municipal_aao", "no_plan_unit"]);
    const baseline = modelClusterBounds(out, ["municipal_aao"]);
    expect(baseline).not.toBeNull();
    expect(withUnknown).not.toBeNull();
    expect(withUnknown?.min).toEqual(baseline?.min);
    expect(withUnknown?.max).toEqual(baseline?.max);
  });

  it("稀疏槽格+紧凑实体簇：取景盒吃已摆 cell 不吃缺位槽大盒（includeMissing）", () => {
    // 槽格夹具：nPools=9（3×3 方阵 spacing=11），offline 工况 1 摆 8 缺——
    // 缺位槽铺开=预留格非模型簇；锚=世界原点旋 0（missingSlotPlaceholders
    // 同坐标系：槽心=(col-(cols-1)/2)·spacing 网格）
    const nPools = 9;
    const spacing = 11;
    const cellL = 10;
    const cellW = 8;
    const cols = Math.ceil(Math.sqrt(nPools));
    const grid: Array<[number, number, number]> = [];
    for (let index = 0; index < nPools; index += 1) {
      grid.push([
        (index % cols - (cols - 1) / 2) * spacing,
        0,
        (Math.floor(index / cols) - (cols - 1) / 2) * spacing,
      ]);
    }
    const nActive = 1; // offline：仅首格已摆
    const plan: PoolGroupPlan = {
      templateScope: "cell",
      nPools,
      nActive,
      cellL,
      cellW,
      spacing,
      activeSlots: grid.slice(0, nActive),
      missing: grid.slice(nActive).map((position, index) => ({ index: nActive + index, position })),
    };
    const claim: PoolClaim = {
      entry: { unitId: "u1" } as unknown as FamilyEntry,
      dimNode: { dims: { length: cellL, width: cellW }, placements: [P(0, 0, 0)] },
    };
    const planMap = new Map<string, PoolGroupPlan>([["u1", plan]]);
    const claimMap = new Map<string, PoolClaim>([["u1", claim]]);
    const withMissing = groupExtents(planMap, claimMap); // F5 语义（缺省）
    const activeOnly = groupExtents(planMap, claimMap, { includeMissing: false });
    expect(withMissing).not.toBeNull();
    expect(activeOnly).not.toBeNull();
    // 全槽盒：3×3 方阵 z 跨 2 格+cell 幅（22+8=30）；已摆=单 cell 幅 8
    const spanAll = (withMissing as SceneBounds).max[2] - (withMissing as SceneBounds).min[2];
    const spanActive = (activeOnly as SceneBounds).max[2] - (activeOnly as SceneBounds).min[2];
    expect(spanActive).toBeCloseTo(cellW, 6);
    expect(spanAll).toBeGreaterThan(spanActive * 3); // 大盒 vs 小簇
    // 取景吃 cluster：active 口径机位显著更近（frameCamera 同式距离）
    const dist = (b: SceneBounds): number => {
      const f = frameCamera("iso", b, 2);
      return Math.hypot(
        f.position[0] - f.center[0],
        f.position[1] - f.center[1],
        f.position[2] - f.center[2],
      );
    };
    expect(dist(activeOnly as SceneBounds)).toBeLessThan(dist(withMissing as SceneBounds));
  });
});

describe("viewer3d·V4 取景盒=模型簇（P8——Scene 消费锚）", () => {
  it("Scene 源：modelClusterBounds 入取景盒+空簇回退 effectiveBounds（?raw 源结构）", () => {
    const sceneSource = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../components/Scene.tsx"),
      "utf-8",
    );
    expect(sceneSource).toContain("modelClusterBounds(projection.scene, templateClaims.keys())");
    expect(sceneSource).toMatch(/includeMissing:\s*false/); // 槽盒只取已摆 cell
    expect(sceneSource).toMatch(/\?\s*effectiveBounds/); // 空簇回退现行为
    expect(sceneSource).toContain("framingBounds");
  });

  it("空簇回退=显式分支（d1-W3——scene null 前置 return）", () => {
    const sceneSource = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../components/Scene.tsx"),
      "utf-8",
    );
    // d1-W3：窄差收口——空场景显式回退（非仅 union 双 null 隐式回退）
    expect(sceneSource).toMatch(
      /if \(projection\.scene === null\) \{\s*\n\s*return effectiveBounds;\s*\n\s*\}/,
    );
  });
});
