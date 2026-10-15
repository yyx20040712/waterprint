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
 *        ④V3 D5：空态「去计算」钮〔onGoCalc 调用〕+SheetsGallery→Export
 *        Button disabled 接线〔props 捕获〕+ExportButton 真件 disabled 并入
 *        三钮两 Select〔importActual 真件渲染——内部 hook 替身〕
 */
import { act, cleanup, fireEvent, render } from "@testing-library/react";
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
const gate = vi.hoisted(() => ({
  projectId: "p1" as string | null,
  exportsRows: [] as unknown[],
  exportProps: [] as Array<{ disabled?: boolean }>,
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
vi.mock("../../features/drawings/api/useExportsQuery", () => ({
  useExportsQuery: () => ({ data: gate.exportsRows, isError: false, isPending: false }),
  useConditionOptions: () => ({ data: [] }),
  useUnitOptions: () => ({ data: [] }),
}));
vi.mock("../../features/drawings/api/useUnitCatalog", () => ({
  useUnitCatalog: () => ({ data: null }),
}));
// V3 D5：props 捕获替身（SheetsGallery→ExportButton disabled 接线锚）
vi.mock("../../features/drawings/components/ExportButton", () => ({
  ExportButton: (props: { disabled?: boolean }) => {
    gate.exportProps.push(props);
    return null;
  },
}));
// V3 D5：真件渲染面内部依赖替身（importActual 取真 ExportButton 时其
// 内部 hook/回溯行模块走替身——vi.mock 工厂不拦 importActual 路径上的
// 依赖解析，两替身各自生效）
vi.mock("../../features/drawings/api/useExportArtifact", () => ({
  useExportArtifact: () => ({ mutate: vi.fn(), isPending: false }),
}));
vi.mock("../../features/drawings/api/useExportBatch", () => ({
  useExportBatch: () => ({
    submitBatch: vi.fn(),
    cancelActive: vi.fn(),
    progress: null,
    lastOutcome: null,
    activeTaskId: null,
    cancelPending: false,
    cancelError: null,
    restoreNotice: null,
  }),
}));
vi.mock("../../features/drawings/components/BatchStatusLine", () => ({
  BatchStatusLine: () => null,
}));
// siteplan 懒件替身（siteplan 分支锚不载重编辑器 chunk）
vi.mock("../siteplanPane", () => ({
  SiteplanPane: () => null,
}));

function mountZone(subpage: "sheets" | "siteplan") {
  return render(
    <DraftingZone
      subpage={subpage}
      onSubpageChange={() => {}}
      onGoCalc={() => {}}
    />,
  );
}

beforeEach(() => {
  storageBack.clear();
  gate.projectId = "p1";
  gate.exportsRows = [];
  gate.exportProps = [];
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

describe("工程制图区·V3 空态引导与导出禁用（D5——信息专业度）", () => {
  it("空态卡「去计算」钮：点击=onGoCalc 调用（testid+type=button）", () => {
    const onGoCalc = vi.fn();
    const { container } = render(
      <DraftingZone
        subpage="sheets"
        onSubpageChange={() => {}}
        onGoCalc={onGoCalc}
      />,
    );
    const grid = container.querySelector('[data-testid="wp-v4-sheet-grid"]');
    expect(grid?.textContent).toContain("尚无图纸");
    const goCalc = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-drafting-go-calc"]',
    );
    expect(goCalc).not.toBeNull();
    expect(goCalc?.type).toBe("button");
    fireEvent.click(goCalc as HTMLButtonElement);
    expect(onGoCalc).toHaveBeenCalledTimes(1);
  });

  it("SheetsGallery→ExportButton disabled 接线：空态（rows=0）传 disabled=true", () => {
    render(
      <DraftingZone
        subpage="sheets"
        onSubpageChange={() => {}}
        onGoCalc={() => {}}
      />,
    );
    expect(gate.exportProps.length).toBeGreaterThan(0);
    expect(gate.exportProps[gate.exportProps.length - 1]?.disabled).toBe(true);
  });

  it("有图纸（rows>0）disabled 不置位（导出可用）", () => {
    gate.exportsRows = [
      {
        project_id: "p1",
        kind: "dxf",
        condition_key: "design",
        file_name: "p1-unit-design.dxf",
        design_digest: "abcdef1234567890",
        engine_version: "e",
        data_version: "d",
        stale_labeled: false,
      },
    ];
    const { container } = render(
      <DraftingZone
        subpage="sheets"
        onSubpageChange={() => {}}
        onGoCalc={() => {}}
      />,
    );
    expect(
      container.querySelector('[data-testid="wp-v4-sheet-card"]'),
    ).not.toBeNull();
    expect(gate.exportProps[gate.exportProps.length - 1]?.disabled).toBeFalsy();
  });
});

describe("工程制图区·V3 ExportButton disabled 并入（D5——真件渲染）", () => {
  /** 真件装载（模块替身不拦 importActual 依赖解析——内部 hook 走上方替身）。 */
  async function realExportButton() {
    return (
      await vi.importActual<
        typeof import("../../features/drawings/components/ExportButton")
      >("../../features/drawings/components/ExportButton")
    ).ExportButton;
  }

  it("disabled=true：三导出钮+两 Select 全禁用（enable 门 AND——空态整组禁用）", async () => {
    const RealExportButton = await realExportButton();
    const { container } = render(
      <RealExportButton
        projectId="p1"
        units={["municipal_aao"]}
        conditions={["design"]}
        disabled
      />,
    );
    // 两 Select：antd 禁用态类
    const selects = container.querySelectorAll(".ant-select-disabled");
    expect(selects.length).toBe(2);
    // 三导出钮：disabled 属性在场（ready 闸本应放行——disabled 恒禁用证）
    const buttons = Array.from(container.querySelectorAll("button")).filter(
      (button) => button.textContent?.includes("导出"),
    );
    expect(buttons.length).toBe(3);
    for (const button of buttons) {
      expect(button.hasAttribute("disabled")).toBe(true);
    }
  });

  it("disabled 缺省+选项齐备：三钮可用（既有 ready 闸语义零改）", async () => {
    const RealExportButton = await realExportButton();
    const { container } = render(
      <RealExportButton
        projectId="p1"
        units={["municipal_aao"]}
        conditions={["design"]}
      />,
    );
    const buttons = Array.from(container.querySelectorAll("button")).filter(
      (button) => button.textContent?.includes("导出"),
    );
    expect(buttons.length).toBe(3);
    for (const button of buttons) {
      expect(button.hasAttribute("disabled")).toBe(false);
    }
  });
});
