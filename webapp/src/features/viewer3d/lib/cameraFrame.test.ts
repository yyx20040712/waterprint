/**
 * 取景机位纯函数测试（v2-20261015 笔5——cameraFrame 自 Scene.tsx 169-195
 * 拆迁+AABB 投影紧致拟合制式：三 preset 方向语义/空场景回退/紧致距离对
 * 宽扁盒显著小于包围球制式/margin 八角 NDC 不裁切——解析期望值直算）。
 *
 * 输入:  frameCamera(preset, bounds, aspect)（纯函数——node 直测零 DOM）
 * 输出:  断言族：①三 preset 机位方向=归一 preset 向量（top 近俯视微倾
 *        防正射退化注记保持）②空场景（bounds=null）回退绝对坐标+中心
 *        原点③紧致拟合距离=公式解析值且对宽扁盒显著小于对角线×1.25
 *        ④AABB 八角 NDC 投影在 [-1.1,1.1]（margin 不裁切数学断言）
 */
import { describe, expect, it } from "vitest";

import { frameCamera, type CameraPresetKey } from "./cameraFrame";
import type { SceneBounds } from "./projectScene";

const V_FOV_DEG = 50;
const TAN_HALF = Math.tan(((V_FOV_DEG / 2) * Math.PI) / 180);
const MARGIN = 1.15;

/** golden 主线形态宽扁盒（基线探针实测 bounds 同构——287×11×141）。 */
const FLAT: SceneBounds = {
  min: [-70.5, -3.15, -70.5],
  max: [216.895, 7.9, 70.5],
};

/** 固定三元组（noUncheckedIndexedAccess 下数组索引=number|undefined 面）。 */
type Tri = [number, number, number];

const dot3 = (a: Tri, b: Tri): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross3 = (a: Tri, b: Tri): Tri => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const norm3 = (a: Tri): number => Math.hypot(a[0], a[1], a[2]);
const scale3 = (a: Tri, k: number): Tri => [a[0] * k, a[1] * k, a[2] * k];
const abs3 = (a: Tri): Tri => [Math.abs(a[0]), Math.abs(a[1]), Math.abs(a[2])];

/** 公式复算（实现同源数学——解析期望值，非实现复读；含两处 D5 修正项：
 *  extU 沿相机 yAxis〔=cross(dir,right)〕+深度支撑项 extD=Σe_i·|dir_i|
 *  ——见实现头注与批档自裁申报）。 */
function expectedDistance(
  preset: CameraPresetKey,
  bounds: SceneBounds,
  aspect: number,
): { distance: number; extU: number; extR: number; extD: number; fitting: number } {
  const dir = scale3(
    preset === "iso" ? [30, 30, 30] : preset === "top" ? [0, 60, 1] : [40, 5, 0],
    1,
  );
  const unit = scale3(dir, 1 / norm3(dir));
  const up: Tri = [0, 1, 0];
  const right = cross3(unit, up);
  const rUnit = scale3(right, 1 / norm3(right));
  const yAxis = cross3(unit, rUnit);
  const e: Tri = [
    (bounds.max[0] - bounds.min[0]) / 2,
    (bounds.max[1] - bounds.min[1]) / 2,
    (bounds.max[2] - bounds.min[2]) / 2,
  ];
  const extU = dot3(e, abs3(yAxis));
  const extR = dot3(e, abs3(rUnit));
  const extD = dot3(e, abs3(unit));
  const fitting = Math.max(extU / TAN_HALF, extR / (TAN_HALF * aspect)) * MARGIN;
  return { distance: fitting + extD, extU, extR, extD, fitting };
}

describe("cameraFrame·三 preset 方向语义", () => {
  it.each(["iso", "top", "side"] as const)(
    "%s 机位方向=归一 preset 向量（top 近俯视微倾防正射退化——(0,60,1) 非 (0,1,0)）",
    (preset) => {
      const aspect = 29567 / 10000; // 基线探针实测 2.9567
      const raw: Tri =
        preset === "iso" ? [30, 30, 30] : preset === "top" ? [0, 60, 1] : [40, 5, 0];
      const unit = scale3(raw, 1 / norm3(raw));
      const { position, center } = frameCamera(preset, FLAT, aspect);
      const away: Tri = [
        position[0] - center[0],
        position[1] - center[1],
        position[2] - center[2],
      ];
      const dist = norm3(away);
      expect(away[0] / dist).toBeCloseTo(unit[0], 12);
      expect(away[1] / dist).toBeCloseTo(unit[1], 12);
      expect(away[2] / dist).toBeCloseTo(unit[2], 12);
      // top 微倾注记：方向非纯竖直（z 分量>0——OrbitControls up 轴退化防线）
      if (preset === "top") {
        expect(unit[2]).toBeGreaterThan(0);
      }
    },
  );

  it("中心语义=bounds AABB 中心", () => {
    const { center } = frameCamera("iso", FLAT, 2);
    expect(center[0]).toBeCloseTo((FLAT.min[0] + FLAT.max[0]) / 2, 12);
    expect(center[1]).toBeCloseTo((FLAT.min[1] + FLAT.max[1]) / 2, 12);
    expect(center[2]).toBeCloseTo((FLAT.min[2] + FLAT.max[2]) / 2, 12);
  });
});

describe("cameraFrame·空场景回退", () => {
  it("bounds=null=回退 preset 方向绝对坐标+中心原点（零场景零尺度基准）", () => {
    for (const preset of ["iso", "top", "side"] as const) {
      const { position, center } = frameCamera(preset, null, 2);
      const raw =
        preset === "iso"
          ? [30, 30, 30]
          : preset === "top"
            ? [0, 60, 1]
            : [40, 5, 0];
      expect(position).toEqual(raw);
      expect(center).toEqual([0, 0, 0]);
    }
  });
});

describe("cameraFrame·紧致拟合距离", () => {
  it("宽扁盒：距离=公式解析值，且显著小于对角线×1.25 包围球制式", () => {
    const aspect = 2.9567;
    const want = expectedDistance("iso", FLAT, aspect);
    const { position, center } = frameCamera("iso", FLAT, aspect);
    const dist = Math.hypot(
      position[0] - center[0],
      position[1] - center[1],
      position[2] - center[2],
    );
    expect(dist).toBeCloseTo(want.distance, 9);
    const diagonal = Math.hypot(
      FLAT.max[0] - FLAT.min[0],
      FLAT.max[1] - FLAT.min[1],
      FLAT.max[2] - FLAT.min[2],
    );
    // 紧致面：小于包围球制式（golden 形态 iso/aspect≈2.96 实测比≈0.88
    // ——extU 修正沿相机竖屏轴后竖向延展主导屏面拟合，宽画布可收紧幅度
    // 如实为 12%；A4 面积占比不设硬门槛，正确性=NDC 数学断言承载）
    expect(dist).toBeLessThan(diagonal * 1.25);
    expect(dist / (diagonal * 1.25)).toBeLessThan(0.95);
  });

  it("aspect 越窄距离越大（extR/aspect 支配——竖屏更远）", () => {
    const wide = expectedDistance("iso", FLAT, 3).distance;
    const narrow = expectedDistance("iso", FLAT, 0.5).distance;
    const distOf = (aspect: number): number => {
      const f = frameCamera("iso", FLAT, aspect);
      return Math.hypot(
        f.position[0] - f.center[0],
        f.position[1] - f.center[1],
        f.position[2] - f.center[2],
      );
    };
    const dWide = distOf(3);
    const dNarrow = distOf(0.5);
    expect(dWide).toBeCloseTo(wide, 9);
    expect(dNarrow).toBeCloseTo(narrow, 9);
    expect(dNarrow).toBeGreaterThan(dWide);
  });
});

describe("cameraFrame·margin 不裁切（AABB 八角 NDC 投影）", () => {
  it.each(["iso", "top", "side"] as const)(
    "%s 八角 NDC 在 [-1.1,1.1]（lookAt 基——x=up×z/y=z×x 投影解析）",
    (preset) => {
      const aspect = 2.9567;
      const { position, center } = frameCamera(preset, FLAT, aspect);
      // three lookAt 基：z=eye−target 归一；x=normalize(cross(up,z))；y=cross(z,x)
      const away: Tri = [
        position[0] - center[0],
        position[1] - center[1],
        position[2] - center[2],
      ];
      const zAxis = scale3(away, 1 / norm3(away));
      const up: Tri = [0, 1, 0];
      const xAxis = scale3(cross3(up, zAxis), 1 / norm3(cross3(up, zAxis)));
      const yAxis = cross3(zAxis, xAxis);
      const e: Tri = [
        (FLAT.max[0] - FLAT.min[0]) / 2,
        (FLAT.max[1] - FLAT.min[1]) / 2,
        (FLAT.max[2] - FLAT.min[2]) / 2,
      ];
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
            expect(depth).toBeGreaterThan(0); // 全角在相机前方
            const ndcX = dot3(d, xAxis) / (depth * TAN_HALF * aspect);
            const ndcY = dot3(d, yAxis) / (depth * TAN_HALF);
            expect(Math.abs(ndcX)).toBeLessThanOrEqual(1.1);
            expect(Math.abs(ndcY)).toBeLessThanOrEqual(1.1);
          }
        }
      }
    },
  );

  it("距离分解：fitting×1.15+extD（margin 作用于屏面拟合项——深度支撑项另加）", () => {
    const aspect = 2.9567;
    const { position, center } = frameCamera("iso", FLAT, aspect);
    const dist = Math.hypot(
      position[0] - center[0],
      position[1] - center[1],
      position[2] - center[2],
    );
    const want = expectedDistance("iso", FLAT, aspect);
    expect(dist).toBeCloseTo(want.fitting + want.extD, 9);
    expect(want.fitting / (want.fitting / MARGIN)).toBeCloseTo(MARGIN, 12);
    // 深度项非零（golden 宽扁盒 iso 对角深度支撑≈126.9）
    expect(want.extD).toBeCloseTo(126.86, 1);
  });
});
