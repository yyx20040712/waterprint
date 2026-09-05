/**
 * siteGeometry 纯几何原语测试：OBB 角点/净距枚举/点-线段距/相交/点在
 * 多边形（node 环境——先红后绿）。
 *
 * 输入:  siteGeometry 纯函数族（零 DOM/零 store 依赖）
 * 输出:  契约断言（黄金角 0/30/45/90° 解析值容差 1e-9——跨语言 IEEE754
 *        三角函数不保证逐位一致[core test_spacing 同式镜像，双侧注释
 *        记档]；归零族[相交/全含]/零长退化/射线法奇偶[凹多边形·顶点
 *        序无关·贴边 1e-9 归内]）
 */
import { describe, expect, it } from "vitest";

import {
  measureToNearest,
  obbCorners,
  obbClearance,
  pointInPolygon,
  pointSegmentDistance,
  segmentsIntersect,
  structureStrokeRole,
  type ObbShape,
} from "./siteGeometry";

/** 容差断言（跨语言 IEEE754 镜像口径——相对/绝对取大，Kimi D9.1 记档）。 */
function expectClose(actual: number, expected: number): void {
  const tol = Math.max(1e-9, Math.abs(expected) * 1e-9);
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tol);
}

function shape(
  x: number, y: number, rotation: number, w: number, h: number,
): ObbShape {
  return { x, y, rotation, w, h };
}

describe("obbCorners（OBB 四角——摆位+足迹旋转）", () => {
  it("旋转 0°：轴对齐四角恰 (±w/2,±h/2)+中心平移", () => {
    const corners = obbCorners(10, 20, 0, 6, 4);
    expect(corners.map((c) => [c.x, c.y]).sort((a, b) => a[0]! - b[0]!)).toEqual([
      [7, 18], [7, 22], [13, 18], [13, 22],
    ]);
  });

  it("旋转 45°：方形四角落轴向 ±(w/2)·√2（解析精确）", () => {
    const halfDiag = (10 / 2) * Math.SQRT2;
    const corners = obbCorners(0, 0, 45, 10, 10);
    // 局部 (-5,-5)→(0,-√50)、(5,-5)→(√50,0)、(5,5)→(0,√50)、(-5,5)→(-√50,0)
    expectClose(corners[0]!.x, 0);
    expectClose(corners[0]!.y, -halfDiag);
    expectClose(corners[1]!.x, halfDiag);
    expectClose(corners[1]!.y, 0);
    expectClose(corners[2]!.x, 0);
    expectClose(corners[2]!.y, halfDiag);
    expectClose(corners[3]!.x, -halfDiag);
    expectClose(corners[3]!.y, 0);
  });
});

describe("obbClearance（两 OBB 点-边枚举精确净距——core _clearance 同式）", () => {
  it("旋转 0° 恒等 AABB 式（单轴分离+对角斜距两形态——回归锚）", () => {
    const a = shape(0, 0, 0, 12, 5);
    const diagonal = obbClearance(a, shape(20, 9, 0, 6, 6));
    expectClose(diagonal, Math.hypot(11, 3.5)); // gapX=11、gapY=3.5
    expectClose(obbClearance(a, shape(20, 0, 0, 6, 6)), 11); // 单轴 clamp
  });

  it("黄金角族 30/45/90°：两同旋 OBB 沿 uθ 对置解析值 L-(wA+wB)/2=23", () => {
    for (const deg of [30, 45, 90]) {
      const rad = (deg * Math.PI) / 180;
      const a = shape(0, 0, deg, 12, 4);
      const b = shape(32 * Math.cos(rad), 32 * Math.sin(rad), deg, 6, 6);
      expectClose(obbClearance(a, b), 32 - (12 / 2 + 6 / 2));
    }
  });

  it("归零族：边对相交（十字穿插无顶点内含）与一方全含均=0", () => {
    expect(obbClearance(shape(0, 0, 0, 20, 4), shape(3, 1, 90, 20, 4))).toBe(0);
    expect(obbClearance(shape(0, 0, 0, 20, 20), shape(2, 1, 30, 4, 4))).toBe(0);
  });

  it("零宽足迹退防：棱缩点（零长线段退化点-点距）=中心距", () => {
    expectClose(obbClearance(shape(0, 0, 0, 0, 4), shape(10, 0, 0, 0, 4)), 10);
  });
});

describe("pointSegmentDistance（点-线段距——投影参数 clamp）", () => {
  it("垂足在段内=垂距；段外=端点距；零长线段=点-点距", () => {
    expectClose(pointSegmentDistance({ x: 3, y: 4 }, { x: 0, y: 0 }, { x: 0, y: 10 }), 3);
    // (6,12) 垂足 (0,12) 越段上端 → 端点 (0,10) 距 hypot(6,2)
    expectClose(pointSegmentDistance({ x: 6, y: 12 }, { x: 0, y: 0 }, { x: 0, y: 10 }), Math.hypot(6, 2));
    expectClose(pointSegmentDistance({ x: 3, y: 4 }, { x: 0, y: 0 }, { x: 0, y: 0 }), 5);
  });
});

describe("segmentsIntersect（线段相交——CLRS 四方向）", () => {
  it("十字相交=真；共线搭接=真；分离/平行=假", () => {
    expect(segmentsIntersect(
      { x: -1, y: 0 }, { x: 1, y: 0 }, { x: 0, y: -1 }, { x: 0, y: 1 },
    )).toBe(true);
    expect(segmentsIntersect(
      { x: 0, y: 0 }, { x: 2, y: 0 }, { x: 1, y: 0 }, { x: 3, y: 0 },
    )).toBe(true);
    expect(segmentsIntersect(
      { x: -1, y: 0 }, { x: 1, y: 0 }, { x: 5, y: -1 }, { x: 5, y: 1 },
    )).toBe(false);
  });
});

describe("pointInPolygon（射线法奇偶+两段式贴边归内——core boundary 同式）", () => {
  const square = [
    { x: 0, y: 0 }, { x: 100, y: 0 }, { x: 100, y: 100 }, { x: 0, y: 100 },
  ];
  const lShape = [
    { x: 0, y: 0 }, { x: 100, y: 0 }, { x: 100, y: 60 },
    { x: 60, y: 60 }, { x: 60, y: 100 }, { x: 0, y: 100 },
  ];

  it("内=真/外=假；顶点序逆转无关", () => {
    expect(pointInPolygon({ x: 50, y: 50 }, square)).toBe(true);
    expect(pointInPolygon({ x: 150, y: 50 }, square)).toBe(false);
    expect(pointInPolygon({ x: 50, y: 50 }, [...square].reverse())).toBe(true);
  });

  it("贴边（容差 1e-9）=内：边上点+恰在顶点", () => {
    expect(pointInPolygon({ x: 50, y: 0 }, square)).toBe(true);
    expect(pointInPolygon({ x: 100, y: 100 }, square)).toBe(true);
    expect(pointInPolygon({ x: 50, y: 1e-10 }, square)).toBe(true);
  });

  it("凹多边形：凹口（东北象限）=外；主体=内", () => {
    expect(pointInPolygon({ x: 80, y: 80 }, lShape)).toBe(false);
    expect(pointInPolygon({ x: 30, y: 80 }, lShape)).toBe(true);
  });

  it("短多边形（len<3）恒外（防御面同 core R3）", () => {
    expect(pointInPolygon({ x: 0, y: 0 }, [])).toBe(false);
    expect(pointInPolygon({ x: 0, y: 0 }, [{ x: 0, y: 0 }, { x: 1, y: 1 }])).toBe(false);
  });
});

describe("measureToNearest（OBB 净距测距——编辑辅助非校核裁判）", () => {
  it("OBB 同式：黄金角 45° 对置解析值 23（容差 1e-9）；null 足距=null", () => {
    const rad = Math.PI / 4;
    const target = {
      unitId: "t", x: 0, y: 0, rotation: 45, footprint: { w: 12, h: 4 },
    };
    const other = {
      unitId: "o",
      x: 32 * Math.cos(rad), y: 32 * Math.sin(rad), rotation: 45,
      footprint: { w: 6, h: 6 },
    };
    const rows = measureToNearest(target, [other], 3);
    expectClose(rows[0]?.clearDistance ?? Number.NaN, 23);
    const noFp = { unitId: "n", x: 5, y: 5, rotation: 0, footprint: null };
    expect(measureToNearest(target, [noFp], 3)[0]?.clearDistance).toBeNull();
  });

  it("序=中心距升序+同距 unitId 字典序；自身排除；count 0=空表", () => {
    const target = { unitId: "t", x: 0, y: 0, rotation: 0, footprint: { w: 4, h: 4 } };
    const b = { unitId: "bTank", x: 30, y: 0, rotation: 0, footprint: { w: 4, h: 4 } };
    const a = { unitId: "aTank", x: 30, y: 0, rotation: 0, footprint: { w: 4, h: 4 } };
    expect(
      measureToNearest(target, [b, a, { ...target }], 3).map((m) => m.unitId),
    ).toEqual(["aTank", "bTank"]);
    expect(measureToNearest(target, [a], 0)).toEqual([]);
  });
});

describe("structureStrokeRole（描边优先级角色枚举——B3 R7 链序冻结）", () => {
  it("五态各归：selected/boundary_error/spacing_error/spacing_warn/default", () => {
    expect(structureStrokeRole(true, false, undefined)).toBe("selected");
    expect(structureStrokeRole(false, true, undefined)).toBe("boundary_error");
    expect(structureStrokeRole(false, false, "ERROR")).toBe("spacing_error");
    expect(structureStrokeRole(false, false, "WARN")).toBe("spacing_warn");
    expect(structureStrokeRole(false, false, undefined)).toBe("default");
  });

  it("链序边界：选中压越界压 ERROR 压 WARN（左侧高者优先——冻结序）", () => {
    expect(structureStrokeRole(true, true, "ERROR")).toBe("selected");
    expect(structureStrokeRole(false, true, "ERROR")).toBe("boundary_error");
    expect(structureStrokeRole(false, true, "WARN")).toBe("boundary_error");
    expect(structureStrokeRole(true, false, "WARN")).toBe("selected");
  });

  it("severity 缺省（无违规/降级面）=default（越界仍独立生效）", () => {
    expect(structureStrokeRole(false, false, undefined)).toBe("default");
    expect(structureStrokeRole(false, true, undefined)).toBe("boundary_error");
  });
});
