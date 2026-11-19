/**
 * @vitest-environment jsdom
 *
 * v4 工艺画布缩略形态测试（v3-20261015 D1——信息专业度批；b3 功能面
 * 重涂批 2026-11-19：节点卡稿形重制〔标题/id/meta 三行〕+图例/浮层并轴
 * var() 化断言随动。真件渲染——取数面/画布 store 模块替身，投影与呈现链
 * 真件）。
 *
 * 输入:  ThumbnailFlow（useProjectQuery/units 目录/canvasStore 模块替身
 *        +PROJECT_RAW 夹具〔两节点一边——projectFlow 真投影〕）
 * 输出:  断言族：①图例在场：wp-v4-flow-legend+行子 -water/-sludge+文案
 *        「水线」「泥线」+「虚线为回流」注+色条色值=域色注入轴 var() 串
 *        单源（b3——JS hex 断言退役）②MiniMap 在场：.react-flow__minimap
 *        +bottom-left 位+轴色卡片壳（pannable/zoomable 块窗口行锚 V5 P2
 *        升级迁件 thumbnailWiring.test.tsx 承载）③Controls 右下对角共存
 *        ④空态互斥：nodes=0 图例缺席+空态提示在场⑤节点卡稿形：.wp-v4-
 *        node-card 三行〔name/id/meta〕+data-node-id 探针锚（b3 批准稿
 *        恢复 id 行——V4 P1 移除裁决推翻；.wp-v4-sub/.wp-v4-thumb 旧形
 *        零复入防回潮）
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { ThumbnailFlow, pickMeasured } from "./thumbnailFlow";
import thumbnailFlowSource from "./thumbnailFlow.tsx?raw";
import type { NodeChange } from "@xyflow/react";

/** global.css 源文（vitest 的 css 管线将 .css?raw 桩为空串——node fs
 *  直读承载 CSS 断言面；zeroPedagogyGate.test 同制路径构造）。 */
const globalCssSource = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../global.css"),
  "utf-8",
);

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

function mountFlow() {
  return render(
    <ThumbnailFlow projectId="p1" onSelectedUnitChange={() => {}} />,
  );
}

beforeEach(() => {
  gate.projectRaw = PROJECT_RAW;
});
afterEach(cleanup);

describe("工艺画布·图例（D1 左上水线/泥线——b3 横排 chip 形+回流注）", () => {
  it("图例在场：容器+行子 testid+文案「水线」「泥线」+「虚线为回流」", () => {
    const { container } = mountFlow();
    const legend = container.querySelector('[data-testid="wp-v4-flow-legend"]');
    expect(legend).not.toBeNull();
    const water = container.querySelector('[data-testid="wp-v4-flow-legend-water"]');
    const sludge = container.querySelector('[data-testid="wp-v4-flow-legend-sludge"]');
    expect(water?.textContent).toContain("水线");
    expect(sludge?.textContent).toContain("泥线");
    expect(legend?.textContent).toContain("虚线为回流");
  });

  it("色条色值单源：域色注入轴 var() 串（b3——JS hex 双源退役，三主题随轴换肤）", () => {
    const { container } = mountFlow();
    const water = container.querySelector<HTMLElement>('[data-testid="wp-v4-flow-legend-water"]');
    const sludge = container.querySelector<HTMLElement>('[data-testid="wp-v4-flow-legend-sludge"]');
    const waterBar = water?.querySelector<HTMLElement>("span");
    const sludgeBar = sludge?.querySelector<HTMLElement>("span");
    expect(waterBar?.style.background).toBe("var(--wp-water)");
    expect(sludgeBar?.style.background).toBe("var(--wp-sludge)");
  });
});

describe("工艺画布·MiniMap（D1——左下+pannable/zoomable+卡片壳）", () => {
  it("MiniMap 在场：.react-flow__minimap+bottom-left 位+轴色卡片壳（b3 并轴 var 化）", () => {
    const { container } = mountFlow();
    const minimap = container.querySelector<HTMLElement>(".react-flow__minimap");
    expect(minimap).not.toBeNull();
    expect(minimap?.className).toContain("bottom");
    expect(minimap?.className).toContain("left");
    expect(minimap?.style.background).toBe("var(--wp-bg-elevated)");
    expect(minimap?.style.border).toBe("1px solid var(--wp-border-2)");
    expect(minimap?.style.borderRadius).toBe("8px");
    expect(minimap?.querySelector(".react-flow__minimap-svg")).not.toBeNull();
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

describe("工艺画布·节点卡稿形（b3——.flow-node 三行卡；V4 P1 id 移除裁决由批准稿推翻）", () => {
  it("节点卡三行：name（中文名）/id（mono）/meta；data-node-id 探针锚保留", () => {
    const { container } = mountFlow();
    const cards = container.querySelectorAll(".wp-v4-node-card");
    expect(cards.length).toBe(2);
    const names = container.querySelectorAll(".wp-v4-node-name");
    expect(names[0]?.textContent).toContain("进水"); // 图题=中文名（目录替身）
    const ids = container.querySelectorAll(".wp-v4-node-id");
    expect(ids[0]?.textContent).toContain("n1"); // id 行恢复（稿 .flow-node-id）
    // data-node-id 保留（探针/测试锚定面）
    expect(container.querySelectorAll("[data-node-id]").length).toBe(2);
  });

  it("旧形防回潮：.wp-v4-sub/.wp-v4-thumb 零命中+CSS 规则随删（死样式零残留）", () => {
    const { container } = mountFlow();
    expect(container.querySelectorAll(".wp-v4-sub").length).toBe(0);
    expect(container.querySelectorAll(".wp-v4-thumb").length).toBe(0);
    expect(globalCssSource).not.toMatch(/\.wp-v4-sub\s*\{/);
    expect(globalCssSource).not.toMatch(/\.wp-v4-thumb\s*\{/);
    expect(globalCssSource).not.toMatch(/\.wp-v4-cap\s*\{/);
    expect(thumbnailFlowSource).not.toContain('className="wp-v4-sub"');
  });
});
