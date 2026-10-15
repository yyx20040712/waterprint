/**
 * @vitest-environment jsdom
 *
 * v4 工艺画布缩略形态测试（v3-20261015 D1——信息专业度批：画布左上水线/
 * 泥线图例+MiniMap 左下。真件渲染——取数面/画布 store 模块替身，投影与
 * 呈现链真件；assertion 面=两件在场 testid/选择器+图例文案与色值）。
 *
 * 输入:  ThumbnailFlow（useProjectQuery/units 目录/canvasStore 模块替身
 *        +PROJECT_RAW 夹具〔两节点一边——projectFlow 真投影〕）
 * 输出:  断言族：①图例在场：wp-v4-flow-legend+行子 -water/-sludge+文案
 *        「水线」「泥线」+色条色值=SEMANTIC_COLORS.domain_* 单源（hex→rgb
 *        换算对拍——禁字面 hex 双源）②MiniMap 在场：.react-flow__minimap
 *        +bottom-left 位+白底卡片壳同 Controls 制式+pannable/zoomable
 *        结构锚（行为面 panZoom 绑定无 DOM 痕迹——?raw 源结构锚承载）
 *        ③Controls 右下对角共存④空态互斥：nodes=0 图例缺席+空态提示在场
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ThumbnailFlow, pickMeasured } from "./thumbnailFlow";
import thumbnailFlowSource from "./thumbnailFlow.tsx?raw";
import { SEMANTIC_COLORS } from "../../shared/ui/semanticColors";
import type { NodeChange } from "@xyflow/react";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
if (typeof window.matchMedia !== "function") {
  window.matchMedia = (query: string) => ({
    matches: false, media: query, onchange: null,
    addListener: () => {}, removeListener: () => {},
    addEventListener: () => {}, removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  projectRaw: undefined as unknown,
}));

vi.mock("../../features/canvas/api/useProjectQuery", () => ({
  useProjectQuery: () => ({ data: gate.projectRaw, isError: false }),
}));
// 画布 store 替身：已有会话（editing 真值）——beginEdit 自动面不触发
vi.mock("../../features/canvas/store/canvasStore", () => ({
  useCanvasStore: {
    getState: () => ({
      beginEdit: vi.fn(),
      addUnit: () => null,
      position: vi.fn(),
      connect: vi.fn(),
      deleteNodes: vi.fn(),
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
          unit_id: "municipal_input",
          name_zh: "进水",
          business_line: "municipal",
          ports: [{ port_id: "out", direction: "OUT" }],
        },
        { unit_id: "junction", name_zh: "节点", business_line: "municipal", ports: [] },
      ],
    },
  }),
}));

/** 夹具：两节点一边（projectFlow 真投影——nodes>0 图例面）。 */
const PROJECT_RAW = {
  format_version: "4.0",
  design: {
    nodes: { n1: { kind: "municipal_input" }, n2: { kind: "junction" } },
    edges: [{ src: { unit_id: "n1", port_id: "out" }, dst: { unit_id: "n2", port_id: "in" } }],
  },
};

/** 夹具：空画布（nodes=0——空态提示面）。 */
const PROJECT_EMPTY = {
  format_version: "4.0",
  design: { nodes: {}, edges: [] },
};

/** hex→rgb（jsdom style 归一形对拍——色值单源断言的换算面）。 */
function hexToRgb(hex: string): string {
  const value = hex.replace("#", "");
  const r = Number.parseInt(value.slice(0, 2), 16);
  const g = Number.parseInt(value.slice(2, 4), 16);
  const b = Number.parseInt(value.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

function mountFlow() {
  return render(
    <ThumbnailFlow projectId="p1" onSelectedUnitChange={() => {}} />,
  );
}

beforeEach(() => {
  gate.projectRaw = PROJECT_RAW;
});
afterEach(cleanup);

describe("工艺画布·V3 图例（D1——左上水线/泥线）", () => {
  it("图例在场：容器+行子 testid+文案「水线」「泥线」", () => {
    const { container } = mountFlow();
    const legend = container.querySelector('[data-testid="wp-v4-flow-legend"]');
    expect(legend).not.toBeNull();
    const water = container.querySelector('[data-testid="wp-v4-flow-legend-water"]');
    const sludge = container.querySelector('[data-testid="wp-v4-flow-legend-sludge"]');
    expect(water?.textContent).toContain("水线");
    expect(sludge?.textContent).toContain("泥线");
  });

  it("色条色值单源：SEMANTIC_COLORS.domain_water/domain_sludge（hex→rgb 对拍）", () => {
    const { container } = mountFlow();
    const water = container.querySelector<HTMLElement>('[data-testid="wp-v4-flow-legend-water"]');
    const sludge = container.querySelector<HTMLElement>('[data-testid="wp-v4-flow-legend-sludge"]');
    const waterBar = water?.querySelector<HTMLElement>("span");
    const sludgeBar = sludge?.querySelector<HTMLElement>("span");
    expect(waterBar?.style.background).toBe(hexToRgb(SEMANTIC_COLORS.domain_water));
    expect(sludgeBar?.style.background).toBe(hexToRgb(SEMANTIC_COLORS.domain_sludge));
  });
});

describe("工艺画布·V3 MiniMap（D1——左下+pannable/zoomable+卡片壳）", () => {
  it("MiniMap 在场：.react-flow__minimap+bottom-left 位+白底卡片壳同 Controls 制式", () => {
    const { container } = mountFlow();
    const minimap = container.querySelector<HTMLElement>(".react-flow__minimap");
    expect(minimap).not.toBeNull();
    expect(minimap?.className).toContain("bottom");
    expect(minimap?.className).toContain("left");
    expect(minimap?.style.background).toBe("rgb(255, 255, 255)");
    expect(minimap?.style.border).toBe("1px solid var(--wp-border-2)");
    expect(minimap?.style.borderRadius).toBe("8px");
    expect(minimap?.querySelector(".react-flow__minimap-svg")).not.toBeNull();
  });

  it("pannable/zoomable 行锚（R2 k2-W1：裸 prop 行锚定——注释字样不兜底；?raw 源结构）", () => {
    expect(thumbnailFlowSource).toContain("<MiniMap");
    expect(thumbnailFlowSource).toMatch(/^\s+pannable$/m);
    expect(thumbnailFlowSource).toMatch(/^\s+zoomable$/m);
  });

  it("Controls 右下对角共存（W-B 回炉位锁锚——两件同屏+Controls 类含 bottom/right）", () => {
    const { container } = mountFlow();
    const controls = container.querySelector<HTMLElement>(".react-flow__controls");
    expect(controls).not.toBeNull();
    expect(controls?.className).toContain("bottom");
    expect(controls?.className).toContain("right");
    expect(container.querySelector(".react-flow__minimap")).not.toBeNull();
  });
});

describe("工艺画布·V3 W-A 受控测量回写（MiniMap 零 rect 缺陷修复面）", () => {
  it("pickMeasured：从变更流析出各节点 dimensions（position 变更旁路）", () => {
    const changes = [
      { id: "n1", type: "dimensions", dimensions: { width: 47, height: 53 } },
      { id: "n2", type: "position", position: { x: 1, y: 2 } },
      { id: "n3", type: "dimensions", dimensions: { width: 78, height: 53 } },
    ] as NodeChange[];
    expect(pickMeasured(changes)).toEqual({
      n1: { width: 47, height: 53 },
      n3: { width: 78, height: 53 },
    });
  });

  it("pickMeasured：无 dimensions 变更=null（不触发 setState 面）", () => {
    const changes = [
      { id: "n2", type: "position", position: { x: 1, y: 2 } },
      { id: "n4", type: "select", selected: true },
    ] as NodeChange[];
    expect(pickMeasured(changes)).toBeNull();
  });

  it("接线锚：onNodesChange 吃 dimensions+nodes 注入 measured（?raw 源结构）", () => {
    expect(thumbnailFlowSource).toContain("pickMeasured(changes)");
    expect(thumbnailFlowSource).toMatch(/measured: measuredById\[node\.id\]/);
  });
});

describe("工艺画布·V3 图例空态互斥（D1——同槽 nodes>0 才渲染）", () => {
  it("nodes=0：图例缺席+空态提示在场", () => {
    gate.projectRaw = PROJECT_EMPTY;
    const { container } = mountFlow();
    expect(
      container.querySelector('[data-testid="wp-v4-flow-legend"]'),
    ).toBeNull();
    expect(container.textContent).toContain("画布为空");
  });
});
