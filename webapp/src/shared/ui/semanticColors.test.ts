/**
 * semanticColors 真源表测试：键集冻结+逐键值+兜底+三导出（SC1 D3）。
 *
 * 输入:  semanticColors.ts 三导出（SEMANTIC_COLORS/FALLBACK_COLOR/
 *        semanticColor）
 * 输出:  四断言面（24 键字面清单 toEqual+逐键值 toBe+兜底回退+导出
 *        存在性）
 *
 * 键集 24 键全数原值迁移（像素零漂移）——本测试即键集冻结锚：任何
 * 增删键/改值必须同步本文件字面清单（键集反推法同款纪律）。
 */
import { describe, expect, it } from "vitest";

import {
  FALLBACK_COLOR,
  SEMANTIC_COLORS,
  semanticColor,
} from "./semanticColors";

describe("semanticColors 语义色真源表", () => {
  it("键集冻结：恰 24 键（3D 图元 12+2D 场面 7+2D 单点 5）", () => {
    expect(Object.keys(SEMANTIC_COLORS).sort()).toEqual(
      [
        // 3D 图元色族（12）
        "pool_wall", "partition", "channel", "ground",
        "water_surface", "sludge", "aerator", "paddle",
        "media", "gate", "pipe", "decant",
        // 2D 场面色族（7）
        "road", "boundary",
        "corridor_water", "corridor_power", "corridor_gas",
        "corridor_comm", "corridor_fallback",
        // 2D 单点彩色语义族（5）
        "selected", "pending", "measure", "spacing_warn", "spacing_error",
      ].sort(),
    );
  });

  it("逐键值冻结：字面 hex 原值迁移（像素零漂移）", () => {
    expect(SEMANTIC_COLORS.pool_wall).toBe("#8d99a6");
    expect(SEMANTIC_COLORS.partition).toBe("#7a8694");
    expect(SEMANTIC_COLORS.channel).toBe("#7f8a93");
    expect(SEMANTIC_COLORS.ground).toBe("#cfd6dc");
    expect(SEMANTIC_COLORS.water_surface).toBe("#2f7fd1");
    expect(SEMANTIC_COLORS.sludge).toBe("#8c5a2b");
    expect(SEMANTIC_COLORS.aerator).toBe("#d48806");
    expect(SEMANTIC_COLORS.paddle).toBe("#d48806");
    expect(SEMANTIC_COLORS.media).toBe("#6a7f5a");
    expect(SEMANTIC_COLORS.gate).toBe("#5b8db8");
    expect(SEMANTIC_COLORS.pipe).toBe("#5b8db8");
    expect(SEMANTIC_COLORS.decant).toBe("#5b8db8");
    expect(SEMANTIC_COLORS.road).toBe("#6b6f76");
    expect(SEMANTIC_COLORS.boundary).toBe("#d4380d");
    expect(SEMANTIC_COLORS.corridor_water).toBe("#2f7fd1");
    expect(SEMANTIC_COLORS.corridor_power).toBe("#f2a93b");
    expect(SEMANTIC_COLORS.corridor_gas).toBe("#3fa34d");
    expect(SEMANTIC_COLORS.corridor_comm).toBe("#9a6dd7");
    expect(SEMANTIC_COLORS.corridor_fallback).toBe("#8c8c8c");
    expect(SEMANTIC_COLORS.selected).toBe("#1668dc");
    expect(SEMANTIC_COLORS.pending).toBe("#d48806");
    expect(SEMANTIC_COLORS.measure).toBe("#2f7fd1");
    expect(SEMANTIC_COLORS.spacing_warn).toBe("#faad14");
    expect(SEMANTIC_COLORS.spacing_error).toBe("#ff4d4f");
  });

  it("兜底：未登记语义回退 FALLBACK_COLOR（禁抛错打断渲染）", () => {
    expect(semanticColor("__nope__")).toBe(FALLBACK_COLOR);
  });

  it("三导出存在性：SEMANTIC_COLORS/semanticColor/FALLBACK_COLOR", () => {
    expect(typeof SEMANTIC_COLORS).toBe("object");
    expect(semanticColor).toBeTypeOf("function");
    expect(FALLBACK_COLOR).toBeTypeOf("string");
  });
});
