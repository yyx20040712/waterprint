/**
 * @vitest-environment jsdom
 *
 * v4 三维示意区工具簇正分支测试（B2 P3 R6——任务书 §二.⑦.1：viewer3d
 * 三钮正分支断言〔B1 探针只证空态在场——本件证行为正分支：缩放±变换+
 * 重置复位重挂〕；Viewer3dPane 懒件替身——zone 层视图态隔离测面）。
 *
 * 输入:  Viewer3dZone（../viewer3dPane 懒件替身——场景面归探针）+三钮夹具
 * 输出:  断言族：①三钮在场（锚=放大/缩小/重置视图）②放大=包裹变换
 *        scale(1)→scale(1.15)（ZOOM_STEP 0.15）③缩小回落 ④重置=复位
 *        scale(1)+场景重挂（mountKey 换键——pane 实例重建证）
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Viewer3dZone } from "./viewer3dZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 懒件替身（场景面隔离——挂载计数器兼重挂证面）。 */
const paneMounts = vi.hoisted(() => ({ count: 0 }));
vi.mock("../viewer3dPane", () => ({
  Viewer3dPane: () => {
    paneMounts.count += 1;
    return <div data-testid="viewer3d-pane-stub">场景替身</div>;
  },
}));

afterEach(cleanup);

/** 视图包裹变换读取（section 首子 div——zone 层 scale 变换面）。 */
function transformOf(container: HTMLElement): string {
  const section = container.querySelector('[data-region="viewer3d-full"]');
  const wrapper = section?.firstElementChild;
  if (wrapper === null || wrapper === undefined) {
    throw new Error("视图包裹层未找到");
  }
  return (wrapper as HTMLElement).style.transform;
}

describe("viewer3d 工具簇正分支（P3 R6）", () => {
  it("三钮在场+场景替身挂载（非空态正分支）", async () => {
    const { container, findByTestId } = render(<Viewer3dZone />);
    expect(
      container.querySelector('[data-testid="wp-v4-view3d-zoom-in"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-view3d-zoom-out"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-view3d-reset"]'),
    ).not.toBeNull();
    // 懒件异步解析——findBy 等待挂载（Suspense microtask 面）
    expect(
      await findByTestId("viewer3d-pane-stub"),
    ).not.toBeNull();
  });

  it("放大/缩小=包裹变换步进（scale 1→1.15→1）", () => {
    const { container } = render(<Viewer3dZone />);
    expect(transformOf(container)).toBe("scale(1)");
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-view3d-zoom-in"]')!,
    );
    expect(transformOf(container)).toBe("scale(1.15)");
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-view3d-zoom-out"]')!,
    );
    expect(transformOf(container)).toBe("scale(1)");
  });

  it("重置视图=scale 复位+场景重挂（mountKey 换键——pane 重建）", () => {
    const before = paneMounts.count;
    const { container } = render(<Viewer3dZone />);
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-view3d-zoom-in"]')!,
    );
    expect(transformOf(container)).toBe("scale(1.15)");
    fireEvent.click(
      container.querySelector('[data-testid="wp-v4-view3d-reset"]')!,
    );
    expect(transformOf(container)).toBe("scale(1)");
    expect(paneMounts.count).toBeGreaterThan(before); // 重挂证（实例重建）
  });
});
