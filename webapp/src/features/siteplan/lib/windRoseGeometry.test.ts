/**
 * windRoseGeometry 纯计算测试：八方位序/辐条比例/Y 翻转（node 环境——
 * 先红后绿，B4 笔①）。
 *
 * 输入:  windRoseGeometry 纯函数面（WIND_DIRS 方位序常量+windRoseSpokes
 *        辐条/标注点相对向量计算——零 DOM/零 store 依赖）
 * 输出:  契约断言（八方位罗盘序镜像 core site_plan.py:85；azimuth=索引
 *        ×45°；spoke=freq/max×基准半径；None/空/全零=空数组；未知键跳过
 *        +sorted 序；负频率钳 0；标注点=基准半径处未缩放；Y 翻转在计算面
 *        完成——dir="N" 时 dy<0 即屏幕向上[简报 R3 Y 翻转条款]）
 */
import { describe, expect, it } from "vitest";

import { WIND_DIRS, windRoseSpokes } from "./windRoseGeometry";

/** 容差断言（跨语言 IEEE754 镜像口径——siteGeometry.test.ts 同式）。 */
function expectClose(actual: number, expected: number): void {
  const tol = Math.max(1e-9, Math.abs(expected) * 1e-9);
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tol);
}

describe("WIND_DIRS（八方位罗盘序——core site_plan.py:85 _WIND_DIRS 镜像）", () => {
  it("恰八方位 N 起顺时针：N/NE/E/SE/S/SW/W/NW", () => {
    expect([...WIND_DIRS]).toEqual(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]);
  });
});

describe("windRoseSpokes（辐条端点相对向量——core _wind_rose_entities 数据口径镜像）", () => {
  it("None/undefined=空数组（core not wind_rose 不画口径）", () => {
    expect(windRoseSpokes(null, 20)).toEqual([]);
    expect(windRoseSpokes(undefined, 20)).toEqual([]);
  });

  it("空 dict/全零频率=空数组（peak<=0 不画口径）", () => {
    expect(windRoseSpokes({}, 20)).toEqual([]);
    expect(windRoseSpokes({ N: 0, E: 0 }, 20)).toEqual([]);
  });

  it("未知键跳过且不参与 max（投影非校验——core sorted 序输出）", () => {
    const spokes = windRoseSpokes({ FOO: 99, S: 1, N: 2 }, 20);
    expect(spokes.map((spoke) => spoke.dir)).toEqual(["N", "S"]); // sorted 字典序
    // max=2（FOO 不计）→N 满径、S 半径
    const north = spokes[0]!;
    expectClose(Math.hypot(north.dx, north.dy), 20);
    const south = spokes[1]!;
    expectClose(Math.hypot(south.dx, south.dy), 10);
  });

  it("N 朝上断言：dir=N 时 dx≈0 且 dy<0（屏幕 Y 向下——Y 翻转计算面完成）", () => {
    const [north] = windRoseSpokes({ N: 1 }, 20);
    expectClose(north!.dx, 0);
    expect(north!.dy).toBeLessThan(0);
    expectClose(north!.dy, -20);
  });

  it("azimuth=索引×45°：八方位满频端点=基准半径各向（E=+X/S=+Y 屏幕下/W=-X）", () => {
    const full = { N: 1, NE: 1, E: 1, SE: 1, S: 1, SW: 1, W: 1, NW: 1 };
    const byDir = new Map(windRoseSpokes(full, 20).map((spoke) => [spoke.dir, spoke]));
    const diag = 20 * Math.SQRT1_2;
    expectClose(byDir.get("E")!.dx, 20);
    expectClose(byDir.get("E")!.dy, 0);
    expectClose(byDir.get("S")!.dx, 0);
    expectClose(byDir.get("S")!.dy, 20); // 南=屏幕向下（Y 翻转后 +Y）
    expectClose(byDir.get("W")!.dx, -20);
    expectClose(byDir.get("W")!.dy, 0);
    expectClose(byDir.get("NE")!.dx, diag);
    expectClose(byDir.get("NE")!.dy, -diag);
    expectClose(byDir.get("SW")!.dx, -diag);
    expectClose(byDir.get("SW")!.dy, diag);
  });

  it("spoke=freq/max×基准半径：比例 1/4 缩径（max 键满径=基准）", () => {
    const spokes = windRoseSpokes({ N: 4, E: 1 }, 20);
    const north = spokes.find((spoke) => spoke.dir === "N")!;
    const east = spokes.find((spoke) => spoke.dir === "E")!;
    expectClose(Math.hypot(north.dx, north.dy), 20);
    expectClose(Math.hypot(east.dx, east.dy), 5);
  });

  it("负频率钳 0：方位保留零长辐条于中心（core G1-03 裁量——不画反象限线）", () => {
    const spokes = windRoseSpokes({ N: -3, S: 1 }, 20);
    const north = spokes.find((spoke) => spoke.dir === "N")!;
    expectClose(north.dx, 0);
    expectClose(north.dy, 0);
  });

  it("标注点=基准半径处未缩放：spoke 缩短标注点仍满径（含 Y 翻转）", () => {
    // 双方位使 N=半频（单键即 max 必满径——首版误锚记档）
    const north = windRoseSpokes({ N: 0.5, S: 1 }, 20).find((spoke) => spoke.dir === "N")!;
    expectClose(Math.hypot(north.dx, north.dy), 10); // spoke 半径
    expectClose(north.labelDx, 0);
    expectClose(north.labelDy, -20); // 标注满径且屏幕向上
  });

  it("基准半径非正/非有限=空数组（防御直通——snapToGrid 同款口径）", () => {
    expect(windRoseSpokes({ N: 1 }, 0)).toEqual([]);
    expect(windRoseSpokes({ N: 1 }, -5)).toEqual([]);
    expect(windRoseSpokes({ N: 1 }, Number.NaN)).toEqual([]);
  });
});
