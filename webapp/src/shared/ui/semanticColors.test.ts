/**
 * semanticColors 真源表测试：键集冻结+逐键值+兜底+三导出（SC1 D3）。
 *
 * 输入:  semanticColors.ts 三导出（SEMANTIC_COLORS/FALLBACK_COLOR/
 *        semanticColor）
 * 输出:  四断言面（34 键字面清单 toEqual+逐键值 toBe+兜底回退+导出
 *        存在性）
 *
 * 键集 34 键（SC1 迁移 24 键全数原值零漂移+SPC2 boundary_error+B3-b
 * domain_* 五键〔同值搬家零漂移——unitGlyph/LEGEND_LINES 收编〕）——
 * 本测试即键集冻结锚：任何增删键/改值必须同步本文件字面清单（键集
 * 反推法同款纪律）。
 */
import { describe, expect, it } from "vitest";

import {
  FALLBACK_COLOR,
  SEMANTIC_COLORS,
  semanticColor,
} from "./semanticColors";

describe("semanticColors 语义色真源表", () => {
  it("键集冻结：恰 34 键（3D 图元 12+2D 场面 7+2D 单点 6+管廊 2[C2-3d]+剖切帽盖 1[C2VD]+检修占位 1[S11]+域色 5[B3-b]）", () => {
    expect(Object.keys(SEMANTIC_COLORS).sort()).toEqual(
      [
        // 3D 图元色族（12）
        "pool_wall", "partition", "channel", "ground",
        "water_surface", "sludge", "aerator", "paddle",
        "media", "gate", "pipe", "decant",
        // C2-3d 管廊两色制（2——与画布域色轴同值）
        "pipe_water", "pipe_sludge",
        // C2VD V1 剖切帽盖（1——缩略图半剖剖面封盖灰）
        "section_cap",
        // 2D 场景色族（7）
        "road", "boundary",
        "corridor_water", "corridor_power", "corridor_gas",
        "corridor_comm", "corridor_fallback",
        // 2D 单点彩色语义族（6——SPC2 +boundary_error 红线越界）
        "selected", "pending", "measure", "spacing_warn", "spacing_error",
        "boundary_error",
        // S11 检修缺位占位（1——viewer3d 警示面）
        "maintenance",
        // B3-b 四域色+中性 JS 面（5——unitGlyph/stream 色/图例线色收编）
        "domain_water", "domain_sludge", "domain_mine", "domain_convey",
        "domain_neutral",
      ].sort(),
    );
  });

  it("逐键值冻结：字面 hex 原值迁移（像素零漂移）", () => {
    expect(SEMANTIC_COLORS.pool_wall).toBe("#a3a9ad"); // 批3 首族视觉验收迭代调灰
    expect(SEMANTIC_COLORS.partition).toBe("#8f9599");
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
    // C2-3d 管廊：水蓝/泥棕（--wp-water/--wp-sludge 轴同值——domain_* 单源引用）
    expect(SEMANTIC_COLORS.pipe_water).toBe("#4da3ff");
    expect(SEMANTIC_COLORS.pipe_sludge).toBe("#9c6b45");
    // B3-b 四域色+中性（JS 面单源——unitGlyph/domainColorOf 与 streamColorOf
    // 及 CanvasFlow LEGEND_LINES 原字面同值搬家；global.css --wp-* 轴同步
    // 义务=UF-53）
    expect(SEMANTIC_COLORS.domain_water).toBe("#4da3ff");
    expect(SEMANTIC_COLORS.domain_sludge).toBe("#9c6b45");
    expect(SEMANTIC_COLORS.domain_mine).toBe("#35c9b0");
    expect(SEMANTIC_COLORS.domain_convey).toBe("#9aa8b8");
    expect(SEMANTIC_COLORS.domain_neutral).toBe("#595959");
    // 管廊键与域色键同值单源（DOMAIN_COLORS 引用——漂移即红）
    expect(SEMANTIC_COLORS.pipe_water).toBe(SEMANTIC_COLORS.domain_water);
    expect(SEMANTIC_COLORS.pipe_sludge).toBe(SEMANTIC_COLORS.domain_sludge);
    // C2VD V1 剖切帽盖：pool_wall 与 ground 之间档剖面灰
    expect(SEMANTIC_COLORS.section_cap).toBe("#a8b4c2");
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
    expect(SEMANTIC_COLORS.boundary_error).toBe("#fa541c");
    // S11 检修缺位占位警示橙
    expect(SEMANTIC_COLORS.maintenance).toBe("#fa8c16");
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
