/**
 * WindRose 组件冒烟测试：零 jsdom 红线内——零 hook 纯展示件 node 直调
 * 元素树断言（本 feature 首例；组件不进 jsdom 沿 unitLibraryTree 口径）。
 *
 * 输入:  WindRose 纯展示组件（返回值=React 元素树或 null——直调不渲染 DOM）
 * 输出:  契约断言（None/空/全零=null 不渲染；有值=嵌套 svg 子树含辐条+
 *        八方位标注；N 朝上[N 辐条端点 y 小于中心=屏幕向上]+标注文字正向
 *        [屏幕层无 transform 翻转]；pointerEvents=none 装饰面）
 */
import type { ReactElement, ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { WindRose, WIND_ROSE_MARGIN, WIND_ROSE_RADIUS } from "./WindRose";

/** 元素树拍平（嵌套 svg→line/text 叶——数组/单子女两形态归一）。 */
function flatten(node: ReactNode): ReactElement[] {
  if (node === null || node === undefined || typeof node !== "object") {
    return [];
  }
  if (Array.isArray(node)) {
    return node.flatMap(flatten);
  }
  const element = node as ReactElement;
  const children = (element.props as { children?: ReactNode }).children;
  return [element, ...flatten(children)];
}

describe("WindRose（屏幕空间角标——B4 笔① R3 仅渲染）", () => {
  it("None=不渲染（返回 null——core 不画口径）", () => {
    expect(WindRose({ windRose: null })).toBeNull();
  });

  it("空/全零=不渲染（windRoseSpokes 空族直通 null）", () => {
    expect(WindRose({ windRose: {} })).toBeNull();
    expect(WindRose({ windRose: { N: 0, E: 0 } })).toBeNull();
  });

  it("有值=嵌套 svg 子树：辐条+八方位标注齐备，pointerEvents=none", () => {
    const tree = WindRose({ windRose: { N: 8, E: 4, S: 2 } });
    expect(tree).not.toBeNull();
    const nodes = flatten(tree);
    const root = nodes[0]!;
    expect(root.type).toBe("svg");
    expect((root.props as { pointerEvents?: string }).pointerEvents).toBe("none");
    const labels = nodes
      .filter((node) => node.type === "text")
      .map((node) => (node.props as { children?: ReactNode }).children);
    expect(labels).toEqual(["E", "N", "S"]); // sorted 序（core 镜像）
    expect(nodes.filter((node) => node.type === "line")).toHaveLength(3);
  });

  it("N 朝上断言：N 辐条端点 y<中心 y（屏幕向上）+N 标注在中心上方", () => {
    const tree = WindRose({ windRose: { N: 1 } });
    const nodes = flatten(tree);
    const spoke = nodes.find(
      (node) => node.type === "line" && node.key === "wind-rose-spoke-N",
    )!;
    const { y1, y2 } = spoke.props as { y1: number; y2: number };
    expect(y2).toBeLessThan(y1); // 屏幕 Y 向下——端点在中心上方=N 世界 +Y
    const label = nodes.find(
      (node) => node.type === "text" && node.key === "wind-rose-label-N",
    )!;
    const { y } = label.props as { y: number };
    expect(y).toBeLessThan(y1);
    // 标注未缩放=基准半径处：中心 y=MARGIN+RADIUS，N 标注 y=MARGIN
    expect(y1).toBe(WIND_ROSE_MARGIN + WIND_ROSE_RADIUS);
    expect(y).toBe(WIND_ROSE_MARGIN);
  });
});
