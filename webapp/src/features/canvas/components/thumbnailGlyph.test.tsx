/**
 * @vitest-environment jsdom
 *
 * 缩略图字形件单测（B1 骨架批 2026-10-09——36 类预绘简笔 SVG：键集唯一性
 * +逐 kind 渲染冒烟+未知 kind 回退象形）。
 *
 * 输入:  thumbnailGlyph.tsx 的 THUMBNAIL_GLYPH_KINDS/hasThumbnailGlyph/
 *        ThumbnailGlyph（jsdom——SVG 渲染面）
 * 输出:  断言族：①键集 36 无重 ②全量 kind 渲染冒烟（svg 根在场+stroke
 *        currentColor 线性形）③未知 kind 回退象形框（hasThumbnailGlyph
 *        false+组件不炸）
 *
 * 规格说明（B1 任务书 §二.③ 白名单件——目录全量×键集对账在 app 层
 *   catalogCategories.test（分层红线：features 禁 import app）；本件=
 *   features 层自洽面）。
 */
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { hasThumbnailGlyph, THUMBNAIL_GLYPH_KINDS, ThumbnailGlyph } from "./thumbnailGlyph";

describe("B1 缩略图字形键集", () => {
  it("36 kind 无重（计数+唯一）", () => {
    expect(THUMBNAIL_GLYPH_KINDS).toHaveLength(36);
    expect(new Set(THUMBNAIL_GLYPH_KINDS).size).toBe(36);
  });

  it("hasThumbnailGlyph 判别（成员 true/未知 false）", () => {
    expect(hasThumbnailGlyph("municipal_aao")).toBe(true);
    expect(hasThumbnailGlyph("recycle_junction")).toBe(true);
    expect(hasThumbnailGlyph("aao_tank")).toBe(false);
  });
});

describe("B1 缩略图字形渲染冒烟（全量 kind）", () => {
  it.each([...THUMBNAIL_GLYPH_KINDS])("%s 渲染 svg 根（线性 stroke=currentColor）", (kind) => {
    const { container } = render(<ThumbnailGlyph kind={kind} />);
    const svg = container.querySelector("svg");
    expect(svg, `${kind} 缺 svg 根`).not.toBeNull();
    expect(svg?.getAttribute("stroke")).toBe("currentColor");
    expect(svg?.querySelectorAll("path, circle, rect, line, polyline, ellipse").length).toBeGreaterThan(0);
  });

  it("未知 kind 回退象形框（不炸+svg 在场）", () => {
    const { container } = render(<ThumbnailGlyph kind="aao_tank" />);
    expect(container.querySelector("svg")).not.toBeNull();
  });
});
