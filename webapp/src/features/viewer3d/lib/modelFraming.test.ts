/**
 * 取景对象=模型簇纯函数测试（V4 P8——uiglobal B 占比 3~5%：紧致拟合消费
 * Scene effective bounds〔含红线/条带/地面外框〕=拟合的是场地不是模型簇；
 * 改制=取景盒走 modelBounds〔solids/waters/internals 足迹聚合——Ground
 * Stage/场界/条带不入盒〕+Scene 消费锚）。
 *
 * 输入:  projectScene（golden 形状夹具——紧凑模型簇〔两池 110m 主线〕+
 *        640×420 地面 plane+±320/±210 红线+条带）+frameCamera（iso 机位）
 * 输出:  断言族：①modelBounds=模型簇 AABB（地面/红线/条带不入盒——scene.
 *        bounds 对照锚证稀释面）②NDC 主轴跨≥0.6（模型簇投影占屏——线性
 *        主线单轴达标用例）③margin 不裁切（八角 |NDC|≤1 沿承）④空簇
 *        modelBounds=null（Scene 回退现行为——源锚）
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { frameCamera, V_FOV_DEG } from "./cameraFrame";
import { projectScene } from "./projectScene";
import type { SceneBounds } from "./projectScene";

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
    {
      node_id: "pool-1",
      semantic: "pool_wall",
      primitive: { kind: "box", dims: { length: 30, width: 14, depth: 6 }, semantic: "pool_wall" },
      position: P(0, 0, 0),
    },
    {
      node_id: "pool-2",
      semantic: "pool_wall",
      primitive: { kind: "box", dims: { length: 30, width: 14, depth: 6 }, semantic: "pool_wall" },
      position: P(80, 0, 0),
    },
    {
      node_id: "ground-1",
      semantic: "ground",
      primitive: { kind: "plane", dims: { length: 640, width: 420 }, semantic: "ground" },
      position: P(0, 0, 0),
    },
    {
      node_id: "site-boundary",
      semantic: "site_boundary",
      primitive: {
        kind: "polyline",
        dims: {
          x0: -320, y0: -210, x1: 320, y1: -210,
          x2: 320, y2: 210, x3: -320, y3: 210,
        },
        semantic: "site_boundary",
      },
      position: P(0, 0, 0),
    },
    {
      node_id: "road-1",
      semantic: "site_road",
      primitive: {
        kind: "strip",
        dims: { x0: -300, y0: -190, x1: 300, y1: -190, x2: 300, y2: -186, x3: -300, y3: -186 },
        semantic: "site_road",
      },
      position: P(0, 0, 0),
    },
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
  it("modelBounds=模型簇 AABB：地面/红线/条带不入盒（bounds 对照锚）", () => {
    const out = projectScene(GOLDEN_SCENE as never);
    expect(out.modelBounds).not.toBeNull();
    // 模型簇=两池足迹：x∈[-15,95]/y∈[-3,3]/z∈[-7,7]（世界系换轴后同形）
    expect(out.modelBounds?.min[0]).toBeCloseTo(-15, 9);
    expect(out.modelBounds?.max[0]).toBeCloseTo(95, 9);
    expect(out.modelBounds?.min[1]).toBeCloseTo(-3, 9);
    expect(out.modelBounds?.max[1]).toBeCloseTo(3, 9);
    expect(out.modelBounds?.min[2]).toBeCloseTo(-7, 9);
    expect(out.modelBounds?.max[2]).toBeCloseTo(7, 9);
    // 对照：scene.bounds 吃红线/地面 → 场地量级（=现状拟合过远的稀释源）
    expect(out.bounds?.min[0]).toBeLessThanOrEqual(-320);
    expect(out.bounds?.max[0]).toBeGreaterThanOrEqual(320);
  });

  it("空簇（仅红线/条带场景）modelBounds=null（Scene 回退现行为）", () => {
    const out = projectScene(({
      ...GOLDEN_SCENE,
      root: ["site-boundary", "road-1"],
      nodes: GOLDEN_SCENE.nodes.filter(
        (node) => node.node_id === "site-boundary" || node.node_id === "road-1",
      ),
    }) as never);
    expect(out.modelBounds).toBeNull();
    expect(out.bounds).not.toBeNull(); // 场地框仍在（地面/灯位面沿承）
  });
});

describe("viewer3d·V4 取景盒=模型簇（P8——NDC 跨度红证）", () => {
  it("golden 线性主线：模型簇投影主轴跨≥0.6（iso/aspect=2——单轴达标）", () => {
    const out = projectScene(GOLDEN_SCENE as never);
    const aspect = 2;
    const frame = frameCamera("iso", out.modelBounds, aspect);
    const { xs, ys } = ndcCorners(
      out.modelBounds as SceneBounds,
      frame.position,
      frame.center,
      aspect,
    );
    const spanX = Math.max(...xs) - Math.min(...xs);
    const spanY = Math.max(...ys) - Math.min(...ys);
    // 主轴（水平——主线沿 X）跨≥0.6：现状（拟合 scene.bounds）实测簇占比
    // 3~5%——模型簇取景盒下簇占屏主量级
    expect(spanX).toBeGreaterThanOrEqual(0.6);
    expect(Math.max(spanX, spanY)).toBeGreaterThanOrEqual(0.6);
    // margin 不裁切沿承：八角 |NDC|≤1
    for (const x of xs) expect(Math.abs(x)).toBeLessThanOrEqual(1);
    for (const y of ys) expect(Math.abs(y)).toBeLessThanOrEqual(1);
  });

  it("对照锚：拟合 scene.bounds（现状）下模型簇主轴跨<0.6（稀释实证）", () => {
    const out = projectScene(GOLDEN_SCENE as never);
    const aspect = 2;
    const frame = frameCamera("iso", out.bounds, aspect);
    const { xs } = ndcCorners(
      out.modelBounds as SceneBounds,
      frame.position,
      frame.center,
      aspect,
    );
    const spanX = Math.max(...xs) - Math.min(...xs);
    expect(spanX).toBeLessThan(0.6); // 现状供给=簇过远（uiglobal 3~5% 量级）
  });
});

describe("viewer3d·V4 取景盒=模型簇（P8——Scene 消费锚）", () => {
  it("Scene 源：modelBounds 入取景盒+空簇回退 effectiveBounds（?raw 源结构）", () => {
    const sceneSource = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../components/Scene.tsx"),
      "utf-8",
    );
    expect(sceneSource).toContain("modelBounds");
    expect(sceneSource).toMatch(/\?\s*effectiveBounds/); // 空簇回退现行为
    // CameraRig/Canvas 初始机位同取景盒（framingBounds 单源消费）
    expect(sceneSource).toContain("framingBounds");
  });
});
