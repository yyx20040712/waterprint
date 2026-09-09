/**
 * 可行域纯函数测试（PD7）：吸附边界/回填格式化/值定位/最近可行格。
 */
import { describe, expect, it } from "vitest";

import {
  formatBackfill,
  isFeasibleValue,
  nearestFeasibleCell,
  snapToBoundary,
  valueAtRatio,
} from "./feasibility";

const SEGMENTS = [
  { start: 2, end: 4 },
  { start: 7, end: 8 },
];

describe("snapToBoundary（PD7 吸附）", () => {
  it("段内原值回填", () => {
    expect(snapToBoundary(3, SEGMENTS)).toBe(3);
    expect(snapToBoundary(7.5, SEGMENTS)).toBe(7.5);
  });
  it("段外吸附最近边界", () => {
    expect(snapToBoundary(1, SEGMENTS)).toBe(2);
    expect(snapToBoundary(5, SEGMENTS)).toBe(4);
    expect(snapToBoundary(6.6, SEGMENTS)).toBe(7);
    expect(snapToBoundary(100, SEGMENTS)).toBe(8);
  });
  it("等距并列取先段边界（确定性）", () => {
    expect(snapToBoundary(5.5, SEGMENTS)).toBe(4); // 距 4 与 7 均 1.5——先见者
  });
  it("空段=null（不编造）", () => {
    expect(snapToBoundary(3, [])).toBeNull();
  });
});

describe("formatBackfill（草稿通道零漂移）", () => {
  it("number→String 形态", () => {
    expect(formatBackfill(3.14)).toBe("3.14");
    expect(formatBackfill(8)).toBe("8");
  });
});

describe("valueAtRatio（条位定位）", () => {
  it("比例→线性值+越界钳制", () => {
    expect(valueAtRatio(0, [0, 1, 2, 3])).toBe(0);
    expect(valueAtRatio(0.5, [0, 1, 2, 3])).toBe(1.5);
    expect(valueAtRatio(1.5, [0, 1, 2, 3])).toBe(3);
    expect(valueAtRatio(-1, [0, 1, 2, 3])).toBe(0);
  });
  it("空值列=null", () => {
    expect(valueAtRatio(0.5, [])).toBeNull();
  });
});

describe("isFeasibleValue", () => {
  it("段内真段外假", () => {
    expect(isFeasibleValue(2, SEGMENTS)).toBe(true);
    expect(isFeasibleValue(4, SEGMENTS)).toBe(true);
    expect(isFeasibleValue(5, SEGMENTS)).toBe(false);
  });
});

describe("nearestFeasibleCell（2D 吸附泛化）", () => {
  const valuesA = [10, 20];
  const valuesB = [2, 3, 4];
  const mask = [
    [0, 0, 0],
    [0, 1, 0],
  ]; // 唯一可行格 (a=20, b=3)

  it("点击不可行格→最近可行格值对", () => {
    expect(nearestFeasibleCell(10, 2, valuesA, valuesB, mask)).toEqual({
      a: 20,
      b: 3,
    });
  });
  it("点击可行格→原值对", () => {
    expect(nearestFeasibleCell(20, 3, valuesA, valuesB, mask)).toEqual({
      a: 20,
      b: 3,
    });
  });
  it("全灰=null（不编造）", () => {
    expect(
      nearestFeasibleCell(10, 2, valuesA, valuesB, [
        [0, 0, 0],
        [0, 0, 0],
      ]),
    ).toBeNull();
  });
});
