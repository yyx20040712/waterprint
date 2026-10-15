/**
 * @vitest-environment jsdom
 *
 * v4 工程制图区测试（v2-20261015 R1-N5 主控扩权新件——拖宽接入锚：
 * sheets 态左树侧栏 wp-v4-sider+拖柄在场+初始 190px+拖拽往返持久；
 * siteplan 分支无左树锚〔hook 顶层恒调不消费〕）。制式沿 reportZone.test
 * 拖拽锚（vi.mock 族+localStorage 存根+MouseEvent 带类型串派发补
 * buttons:1〔R1-W2 语义〕）。
 *
 * 输入:  DraftingZone（sheets/siteplan 两态——drawings 取数面/siteplanPane
 *        懒件模块替身零渲染）+localStorage Map 存根
 * 输出:  断言族：①sheets 态：aside.wp-v4-sider+data-region=drafting-tree+
 *        拖柄 wp-v4-drag-drafting-left（title/⟷）+初始宽 190px②拖拽往返：
 *        down(buttons:1)+move(+50)→240px+onUp 持久写键 wp-v4-drafting-left-w
 *        ③siteplan 分支：无左树/无拖柄（子页全幅现状保持——返回条在场）
 */
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DraftingZone } from "./draftingZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** localStorage 存根（usePaneWidth 消费面——jsdom 无原生方法族，
 *  designZoneJointEntry.test 先例）。 */
const storageBack = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storageBack.get(key) ?? null,
  setItem: (key: string, value: string) => void storageBack.set(key, value),
  removeItem: (key: string) => void storageBack.delete(key),
});

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({ projectId: "p1" as string | null }));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
vi.mock("../../features/drawings/api/useExportsQuery", () => ({
  useExportsQuery: () => ({ data: [], isError: false, isPending: false }),
  useConditionOptions: () => ({ data: [] }),
  useUnitOptions: () => ({ data: [] }),
}));
vi.mock("../../features/drawings/api/useUnitCatalog", () => ({
  useUnitCatalog: () => ({ data: null }),
}));
vi.mock("../../features/drawings/components/ExportButton", () => ({
  ExportButton: () => null,
}));
// siteplan 懒件替身（siteplan 分支锚不载重编辑器 chunk）
vi.mock("../siteplanPane", () => ({
  SiteplanPane: () => null,
}));

function mountZone(subpage: "sheets" | "siteplan") {
  return render(
    <DraftingZone subpage={subpage} onSubpageChange={() => {}} />,
  );
}

beforeEach(() => {
  storageBack.clear();
  gate.projectId = "p1";
});
afterEach(cleanup);

describe("工程制图区·sheets 态左树拖宽（v2 笔2+R1-N5 锚）", () => {
  it("左树在场：aside.wp-v4-sider+拖柄（testid/title/⟷）+初始宽 190px", () => {
    const { container } = mountZone("sheets");
    const aside = container.querySelector('[data-region="drafting-tree"]');
    expect(aside).not.toBeNull();
    expect(aside?.classList.contains("wp-v4-sider")).toBe(true);
    expect((aside as HTMLElement).style.width).toBe("190px");
    const handle = container.querySelector<HTMLDivElement>(
      '[data-testid="wp-v4-drag-drafting-left"]',
    );
    expect(handle).not.toBeNull();
    expect(handle?.title).toBe("拖拽调整宽度");
    expect(handle?.textContent).toContain("⟷");
  });

  it("拖拽往返：down(buttons:1)+move(+50)→240px+onUp 持久写键", () => {
    const { container } = mountZone("sheets");
    const handle = container.querySelector<HTMLDivElement>(
      '[data-testid="wp-v4-drag-drafting-left"]',
    ) as HTMLDivElement;
    act(() => {
      handle.dispatchEvent(
        new MouseEvent("pointerdown", { button: 0, buttons: 1, clientX: 300, bubbles: true }),
      );
    });
    act(() => {
      document.dispatchEvent(new MouseEvent("pointermove", { clientX: 350, buttons: 1 }));
    });
    const aside = container.querySelector('[data-region="drafting-tree"]') as HTMLElement;
    expect(aside.style.width).toBe("240px"); // 190+50
    act(() => {
      document.dispatchEvent(new MouseEvent("pointerup"));
    });
    expect(storageBack.get("wp-v4-drafting-left-w")).toBe("240");
  });
});

describe("工程制图区·siteplan 分支（无左树现状保持）", () => {
  it("siteplan 子页：无左树/无拖柄（返回条在场——子页全幅）", () => {
    const { container } = mountZone("siteplan");
    expect(container.querySelector('[data-region="drafting-tree"]')).toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-drag-drafting-left"]'),
    ).toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-drafting-back-sheets"]'),
    ).not.toBeNull();
  });
});
