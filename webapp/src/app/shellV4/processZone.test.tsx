/**
 * @vitest-environment jsdom
 *
 * v4 工艺区测试（b3 功能面重涂批 2026-11-19——稿 network.html 三栏形：
 * 单元库点选→addRequest 受控通道+inspector 选中面〔身份/参数/端口/操作
 * 钮〕+未选空态。ThumbnailFlow/EnumerateModal stub（props 捕获替身——
 * 画布本体专测件=thumbnailFlow.test）。
 *
 * 输入:  ProcessZone（useProjectId/units 目录/canvasStore/useProjectDesign/
 *        useUnitCatalog 模块替身+ThumbnailFlow stub〔addRequest 捕获〕）
 * 输出:  断言族：①单元库树：组/行在场+点行=addRequest seq 递增〔同请求
 *        幂等〕+onAddHandled 回执清态②inspector：选中=身份+参数键值+
 *        端口行+三操作钮；未选=空态引导③删除钮=canvasStore.deleteNodes
 *        +选中清除上抛④无项目态=空态引导
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ProcessZone } from "./processZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  projectId: "p1" as string | null,
  selectedChange: vi.fn(),
  openParameters: vi.fn(),
  addHandled: vi.fn(),
  deleteNodes: vi.fn(),
  flowProps: null as {
    addRequest: { unitId: string; seq: number } | null;
    onAddHandled?: () => void;
  } | null,
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
vi.mock("./thumbnailFlow", () => ({
  ThumbnailFlow: (props: unknown) => {
    gate.flowProps = props as {
      addRequest: { unitId: string; seq: number } | null;
      onAddHandled?: () => void;
    };
    return <div data-testid="wp-v4-flow-stub" />;
  },
}));
vi.mock("./enumerateModal", () => ({ EnumerateModal: () => null }));
vi.mock("../../features/canvas/store/canvasStore", () => ({
  useCanvasStore: {
    getState: () => ({
      deleteNodes: gate.deleteNodes,
      beginEdit: vi.fn(),
      addUnit: () => null,
      position: vi.fn(),
      connect: vi.fn(),
      session: { projectId: "p1" },
    }),
  },
  useEditing: () => "sess-p1",
  useDraft: () => null,
  useEditBaseRaw: () => null,
}));
vi.mock("../../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({
    data: {
      units: [
        {
          unit_id: "municipal_aao",
          name_zh: "AAO 生物池",
          kind: "unit",
          business_line: "municipal",
          ports: [
            { port_id: "in", direction: "IN" },
            { port_id: "out", direction: "OUT" },
          ],
          params: [
            { field_id: "srt", label_zh: "污泥龄", dim: "TIME_DAY" },
          ],
        },
        {
          unit_id: "sludge_nongsuo",
          name_zh: "污泥浓缩",
          kind: "unit",
          business_line: "sludge",
          ports: [],
          params: [],
        },
        { unit_id: "junction", name_zh: "节点", kind: "builtin", business_line: "municipal", ports: [], params: [] },
      ],
    },
    isError: false,
    isPending: false,
  }),
}));
vi.mock("../../features/params/api/useUnitCatalog", () => ({
  useUnitCatalog: () => ({
    data: {
      units: [
        {
          unit_id: "municipal_aao",
          name_zh: "AAO 生物池",
          kind: "unit",
          business_line: "municipal",
          ports: [
            { port_id: "in", direction: "IN" },
            { port_id: "out", direction: "OUT" },
          ],
          params: [{ field_id: "srt", label_zh: "污泥龄", dim: "TIME_DAY" }],
        },
      ],
    },
    isError: false,
  }),
}));
vi.mock("../../features/params/api/useProjectDesign", () => ({
  useProjectDesign: () => ({
    data: {
      nodeKinds: {},
      nodeParams: { municipal_aao: { srt: 15 } },
    },
    isError: false,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderZone(selectedUnitId: string | null = "municipal_aao") {
  return render(
    <QueryClientProvider client={queryClient}>
      <ProcessZone
        selectedUnitId={selectedUnitId}
        onSelectedUnitChange={gate.selectedChange}
        onOpenParameters={gate.openParameters}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.projectId = "p1";
  gate.selectedChange.mockClear();
  gate.openParameters.mockClear();
  gate.addHandled.mockClear();
  gate.deleteNodes.mockClear();
  gate.flowProps = null;
});
afterEach(cleanup);

describe("工艺区·单元库点选通道（b3——addRequest 受控）", () => {
  it("树组/行在场：一级类组头+组内单元行；点行=addRequest seq 递增", () => {
    renderZone();
    expect(
      document.querySelector('[data-testid="wp-v4-lib-group-secondary"]'),
    ).not.toBeNull();
    const row = document.querySelector(
      '[data-testid="wp-v4-lib-unit-municipal_aao"]',
    ) as HTMLButtonElement;
    expect(row?.textContent).toContain("AAO 生物池");
    fireEvent.click(row);
    expect(gate.flowProps?.addRequest).toEqual({
      unitId: "municipal_aao",
      kind: "unit",
      seq: 1,
    });
    // 回执后请求态清空；再点=seq 递增（幂等门消费）
    gate.flowProps?.onAddHandled?.();
    fireEvent.click(row);
    expect(gate.flowProps?.addRequest?.seq).toBe(2);
  });

  it("折叠组：点组头=组内行隐藏（目录收纳）", () => {
    renderZone();
    const group = document.querySelector(
      '[data-testid="wp-v4-lib-group-sludge"]',
    ) as HTMLButtonElement;
    expect(
      document.querySelector('[data-testid="wp-v4-lib-unit-sludge_nongsuo"]'),
    ).not.toBeNull();
    fireEvent.click(group);
    expect(
      document.querySelector('[data-testid="wp-v4-lib-unit-sludge_nongsuo"]'),
    ).toBeNull();
  });
});

describe("工艺区·inspector（b3——常驻选中面）", () => {
  it("选中=身份（中文名+id+已选中）+参数键值行+端口行+三操作钮", () => {
    const { container } = renderZone("municipal_aao");
    const inspector = container.querySelector('[data-region="unit-inspector"]');
    expect(inspector).not.toBeNull();
    expect(inspector?.textContent).toContain("AAO 生物池");
    expect(inspector?.textContent).toContain("municipal_aao");
    expect(inspector?.textContent).toContain("已选中");
    // 当前参数=design 覆盖值（srt 15——dimUnit 单位后缀）
    expect(inspector?.textContent).toContain("污泥龄");
    expect(inspector?.textContent).toContain("15");
    // 端口行（目录声明 in/out）
    expect(container.querySelectorAll(".wp-v4-portrow").length).toBe(2);
    // 三操作钮
    expect(
      container.querySelector('[data-testid="wp-v4-insp-open-params"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-insp-enumerate"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-insp-delete"]'),
    ).not.toBeNull();
  });

  it("参数与方案钮=onOpenParameters；删除钮=deleteNodes+选中清除上抛", () => {
    renderZone("municipal_aao");
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-insp-open-params"]') as HTMLElement,
    );
    expect(gate.openParameters).toHaveBeenCalledTimes(1);
    fireEvent.click(
      document.querySelector('[data-testid="wp-v4-insp-delete"]') as HTMLElement,
    );
    expect(gate.deleteNodes).toHaveBeenCalledWith(["municipal_aao"]);
    expect(gate.selectedChange).toHaveBeenCalledWith(null);
  });

  it("未选=空态引导（wp-v4-insp-empty）", () => {
    renderZone(null);
    expect(
      document.querySelector('[data-testid="wp-v4-insp-empty"]')?.textContent,
    ).toContain("在画布中选择单元");
  });
});

describe("工艺区·无项目态（沿承）", () => {
  it("projectId=null=空态引导+三栏缺席", () => {
    gate.projectId = null;
    const { container } = renderZone(null);
    expect(container.textContent).toContain("尚未选择项目");
    expect(container.querySelector('[data-region="unit-library"]')).toBeNull();
    expect(container.querySelector('[data-region="unit-inspector"]')).toBeNull();
  });
});
