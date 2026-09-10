/**
 * deriveStep 黄金值互锁（PD8）：与 core tests/solution/test_design_map.py
 * _GOLDEN_STEPS 共享同一组期望——同一 range→同一 step，防 Python/JS
 * 派生漂移（IEEE754 双精度两语言同算术）；isContinuousParam=PD7 入口
 * 精确条件（grid None 且 range 非 None——93 连续区间参数主战场）。
 *
 * 输入:  deriveStep 纯函数族（node 环境——零 antd/react-query import 链）
 * 输出:  纯函数契约断言（黄金值三锚[浮点尾差面 aao ns+精确面 aao
 *        x_mlss/vxinglvchi v_filter]/点数期望 11 点[core axis_point_budget
 *        同式]/入口条件三族[真+档位拒+无 range 拒——undefined 归一面]）
 */
import { describe, expect, it } from "vitest";

import { deriveStep, isContinuousParam } from "./deriveStep";

describe("deriveStep（PD8 单源）", () => {
  it("黄金值与 core 同组（浮点尾差面+精确面）", () => {
    expect(deriveStep({ min: 0.05, max: 0.15 })).toBe(0.009999999999999998); // aao ns
    expect(deriveStep({ min: 3500.0, max: 4500.0 })).toBe(100.0); // aao x_mlss
    expect(deriveStep({ min: 7.0, max: 10.0 })).toBe(0.3); // vxinglvchi v_filter
  });

  it("点数期望互锁：全距缺省步长=11 点", () => {
    const step = deriveStep({ min: 0.05, max: 0.15 });
    expect(Math.floor((0.15 - 0.05) / step + 0.5) + 1).toBe(11); // core axis_point_budget 同式
  });
});

describe("isContinuousParam（PD7 入口条件）", () => {
  it("grid 缺席且 range 在场=真", () => {
    expect(isContinuousParam({ grid: null, range: { min: 0, max: 1 } })).toBe(true);
    expect(isContinuousParam({ range: { min: 0, max: 1 } })).toBe(true); // undefined 归一
  });
  it("档位参数（grid 在场）不入口——即便带 range", () => {
    expect(
      isContinuousParam({ grid: [2, 3, 4], range: { min: 2, max: 4 } }),
    ).toBe(false);
  });
  it("无 range 参数不入口", () => {
    expect(isContinuousParam({ grid: null, range: null })).toBe(false);
    expect(isContinuousParam({})).toBe(false);
  });
});
