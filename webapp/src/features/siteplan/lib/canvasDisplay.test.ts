/**
 * canvasDisplay 纯函数测试：键盘删除判定面（node 环境——B4 笔② 先红后绿；
 * 常量/交互类型面不断言）。
 *
 * 输入:  canvasDisplay.svgOwnsKeyTarget/lineDeleteTarget 纯函数（结构化
 *        类型消费——node 环境以字面量模拟 EventTarget 形态）
 * 输出:  契约断言（svg 本体/直接子元素=消费面；输入框等表单焦点=不消费
 *        [简报 R2 DS 探针必改④]；Delete/Backspace 双键；road/corridor
 *        选中=删除目标产出；structure 选中/无选中/他键=null 不消费）
 */
import { describe, expect, it } from "vitest";

import { lineDeleteTarget, svgOwnsKeyTarget } from "./canvasDisplay";

/** svg 形态字面量（结构化类型——tagName 小写=SVG DOM 实测口径）。 */
const SVG_SELF = { tagName: "svg" };
/** svg 直接子元素形态（polygon 挂在根 svg 下）。 */
const SVG_CHILD = { tagName: "polygon", parentElement: SVG_SELF };
/** 输入框形态（antd Input 渲染 input——tagName 大写=HTML DOM 口径）。 */
const INPUT_EL = { tagName: "INPUT", parentElement: { tagName: "DIV" } };

describe("svgOwnsKeyTarget（焦点判：svg 本体或直接子元素才消费——输入框不消费）", () => {
  it("svg 本体/直接子元素=消费面", () => {
    expect(svgOwnsKeyTarget(SVG_SELF)).toBe(true);
    expect(svgOwnsKeyTarget(SVG_CHILD)).toBe(true);
  });

  it("输入框/深层元素/非元素=null 不消费（输入编辑零劫持）", () => {
    expect(svgOwnsKeyTarget(INPUT_EL)).toBe(false);
    expect(
      svgOwnsKeyTarget({ tagName: "circle", parentElement: { tagName: "g", parentElement: SVG_SELF } }),
    ).toBe(false); // g 包裹的孙层——直接子元素之外不消费
    expect(svgOwnsKeyTarget(null)).toBe(false);
    expect(svgOwnsKeyTarget("svg")).toBe(false);
  });
});

describe("lineDeleteTarget（select 态 Delete/Backspace 删除目标判定——两路汇同一确认门）", () => {
  it("Delete+svg 焦点+road 选中=删除目标产出", () => {
    expect(lineDeleteTarget("Delete", SVG_SELF, { kind: "road", index: 1 }))
      .toEqual({ kind: "road", index: 1 });
  });

  it("Backspace+直接子元素焦点+corridor 选中=删除目标产出", () => {
    expect(lineDeleteTarget("Backspace", SVG_CHILD, { kind: "corridor", index: 0 }))
      .toEqual({ kind: "corridor", index: 0 });
  });

  it("不消费面：输入框焦点/structure 选中/无选中/非删除键=null", () => {
    const road = { kind: "road", index: 0 } as const;
    expect(lineDeleteTarget("Delete", INPUT_EL, road)).toBeNull(); // 输入框焦点
    expect(lineDeleteTarget("Delete", SVG_SELF, { kind: "structure", id: "a" })).toBeNull();
    expect(lineDeleteTarget("Delete", SVG_SELF, null)).toBeNull();
    expect(lineDeleteTarget("a", SVG_SELF, road)).toBeNull();
  });

  it("boundary 选中（B4 笔③——红线单例无索引）=删除目标产出（清空通路上行）", () => {
    expect(lineDeleteTarget("Delete", SVG_SELF, { kind: "boundary" }))
      .toEqual({ kind: "boundary" });
  });
});
