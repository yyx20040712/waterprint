/**
 * thumbnailStage 纯函数测试（C2-thumb V1/V2——分组/AABB/取景/缓存键）。
 *
 * 输入:  groupUnitConstructs/unitBounds/thumbCamera/thumbCacheKey 纯函数
 * 输出:  unit:: 前缀分组（多构型件合组/场景级件滤除）/AABB 外接
 *        （placements∪dims 合并+cylinder 圆外接方）/取景派生（iso 方向
 *        ×1.25+中心）+最小距离钳/缓存键三组成
 */
import { describe, expect, it } from "vitest";

import {
  groupUnitConstructs,
  groupUnitWaters,
  sectionPlane,
  thumbCacheKey,
  thumbCamera,
  unitBounds,
} from "./thumbnailStage";
import type { RenderNode, RenderScene } from "./projectScene";

function node(
  id: string,
  kind: string,
  dims: Record<string, number>,
  placements: Array<[number, number, number]>,
): RenderNode {
  return {
    id,
    kind,
    semantic: "water",
    position: placements[0] ?? [0, 0, 0],
    rotation: [0, 0, 0],
    dims,
    instanceCount: placements.length,
    placements,
  };
}

function sceneOf(solids: RenderNode[], internals: RenderNode[] = []): RenderScene {
  return {
    sceneVersion: "6",
    conditionKey: "ck",
    root: [],
    solids,
    waters: [],
    internals,
    boundaries: [],
    routes: [],
    bounds: null,
  };
}

describe("groupUnitConstructs（node_id 首段分组——scene API 实锚形态）", () => {
  it("首段=unit_id+多构型件合组（浓缩池 cylinder+channel 两件一单元）", () => {
    const groups = groupUnitConstructs(
      sceneOf([
        node("sludge_nongsuo::pool_cylinder", "cylinder", { diameter: 10, depth: 4 }, [[0, 2, 0]]),
        node("sludge_nongsuo::channel", "box", { length: 6, depth: 2, width: 1 }, [[8, 1, 0]]),
        node("municipal_aao::pool_wall", "box", { length: 30, depth: 5, width: 12 }, [[0, 2.5, 0]]),
      ]),
    );
    expect(groups.size).toBe(2);
    expect(groups.get("sludge_nongsuo")).toHaveLength(2);
    expect(groups.get("municipal_aao")).toHaveLength(1);
  });

  it("管廊场景级件（pipe::）排除+internals 并入同组", () => {
    const groups = groupUnitConstructs(
      sceneOf(
        [node("pipe::1", "box", { length: 30, depth: 1, width: 1 }, [[0, 0, 0]])],
        [node("inlet::pipe_in", "cylinder", { diameter: 1, depth: 1 }, [[0, 0, 0]])],
      ),
    );
    expect(groups.size).toBe(1);
    expect(groups.get("inlet")).toHaveLength(1);
  });
});

describe("unitBounds（AABB 外接——placements∪dims 合并）", () => {
  it("box 半尺寸外接+多摆置合并（8×2×4 双格对角排布）", () => {
    const bounds = unitBounds([
      node("unit::a", "box", { length: 8, depth: 2, width: 4 }, [[0, 1, 0], [10, 1, 0]]),
    ]);
    expect(bounds).not.toBeNull();
    if (bounds !== null) {
      expect(bounds.min).toEqual([-4, 0, -2]);
      expect(bounds.max).toEqual([14, 2, 2]);
    }
  });

  it("cylinder 圆外接方（diameter→半幅方）+空摆置=null", () => {
    const bounds = unitBounds([
      node("unit::c", "cylinder", { diameter: 10, depth: 6 }, [[0, 3, 0]]),
    ]);
    expect(bounds?.min).toEqual([-5, 0, -5]);
    expect(bounds?.max).toEqual([5, 6, 5]);
    expect(unitBounds([node("unit::e", "box", { length: 1, depth: 1, width: 1 }, [])])).toBeNull();
  });
});

describe("thumbCamera（V4 口径派生——iso 30/×1.25 复用）", () => {
  it("中心=AABB 中点+机位=中心+iso 方向归一×距离（对称盒恰落对角线上）", () => {
    const spec = thumbCamera({ min: [-5, 0, -5], max: [5, 6, 5] });
    expect(spec.center).toEqual([0, 3, 0]);
    // 对称 AABB：iso 方向归一分量≈0.577——距离=对角线×1.25；水平轴
    // 中心 0 直落分量值，竖轴叠加中心 3
    const diagonal = Math.hypot(10, 6, 10);
    const offset = 0.5773502691896258 * diagonal * 1.25;
    expect(spec.position[0]).toBeCloseTo(offset, 5);
    expect(spec.position[1]).toBeCloseTo(3 + offset, 5);
    expect(spec.position[2]).toBeCloseTo(offset, 5);
  });

  it("微构型最小距离钳（4——GD-N-05：断言=机位到 AABB 中心距非原点距）", () => {
    const spec = thumbCamera({ min: [500, 500, 500], max: [500.1, 500.1, 500.1] });
    const dist = Math.hypot(
      spec.position[0] - spec.center[0],
      spec.position[1] - spec.center[1],
      spec.position[2] - spec.center[2],
    );
    expect(dist).toBeGreaterThanOrEqual(4 - 1e-9); // 浮点尾差容差（钳值恰 4）
  });
});

describe("thumbCacheKey（场景三组成——任一变整批失效）", () => {
  it("projectId/conditionKey/sceneVersion 三段合成（Map 内层键=unit_id）", () => {
    expect(thumbCacheKey("p1", "ck", "6")).toBe("p1:ck:6");
    expect(thumbCacheKey("p1", "ck2", "6")).not.toBe(thumbCacheKey("p1", "ck", "6"));
    expect(thumbCacheKey("p1", "ck", "7")).not.toBe(thumbCacheKey("p1", "ck", "6"));
  });
});

// ═══ C2-visual T1/T2：waters 独立分组+半剖面高派生 ═══
describe("groupUnitWaters（{unit}::water_surface 分组——T2 彩色入图）", () => {
  it("waters 首段分组（solids/internals 不入）+裸 id 排除", () => {
    const scene = sceneOf([], []);
    scene.waters = [
      node("municipal_aao::water_surface", "water_surface", { length: 20, depth: 3, width: 10 }, [[0, 1, 0]]),
      node("municipal_uv::water_surface", "water_surface", { length: 4, depth: 2, width: 2 }, [[0, 1, 0]]),
      node("orphan", "water_surface", { length: 1, depth: 1, width: 1 }, [[0, 0, 0]]),
    ];
    const waters = groupUnitWaters(scene);
    expect(waters.size).toBe(2);
    expect(waters.get("municipal_aao")).toHaveLength(1);
  });

  it("unitBounds 并入 waters（T2 取景含水面稳定）", () => {
    const bounds = unitBounds([
      node("municipal_aao::pool_wall", "box", { length: 20, depth: 5, width: 10 }, [[0, 2.5, 0]]),
      node("municipal_aao::water_surface", "water_surface", { length: 18, depth: 3, width: 8 }, [[0, 3.5, 0]]),
    ]);
    expect(bounds?.min).toEqual([-10, 0, -5]);
    expect(bounds?.max).toEqual([10, 5, 5]);
  });
});

describe("sectionPlane（T1 半剖切面——纵向对角剖·二轮勘正）", () => {
  it("法向面向相机（-x-z 对角归一）+常数=对角中面（远半保留）", () => {
    const spec = sectionPlane({ min: [-5, 0, -5], max: [5, 6, 5] });
    expect(spec.normal[0]).toBeCloseTo(-1 / Math.SQRT2, 9);
    expect(spec.normal[1]).toBe(0);
    expect(spec.normal[2]).toBeCloseTo(-1 / Math.SQRT2, 9);
    // 对角中面 x+z=0（对称盒）→ 常数 0
    expect(spec.constant).toBeCloseTo(0, 9);
  });

  it("偏置盒：中心对角值决定切面（min/max 派生）", () => {
    const spec = sectionPlane({ min: [10, 0, 20], max: [20, 4, 30] });
    // 中心 x=15,z=25 → x+z=40 → 常数 40/√2
    expect(spec.constant).toBeCloseTo(40 / Math.SQRT2, 9);
  });
});
