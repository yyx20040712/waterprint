/**
 * @vitest-environment jsdom
 *
 * v4 工艺画布行为级接线测试（V5 P2 2026-10-16——V3 d1 首轮 N5+复审 N1：
 * ReactFlow 桩件捕获 props 面驱动 onNodesChange，断言受控 nodes prop 的
 * node.measured 注入行为〔受控测量回写 W-A 的行为级补面〕；另承载 MiniMap
 * pannable/zoomable 块窗口行锚〔自 thumbnailFlow.test 升级迁入——全文件
 * 域裸行锚 /^\s+pannable$/m 误配面退役〕）。
 *
 * 输入:  ThumbnailFlow（useProjectQuery/canvasStore/units 目录模块替身同
 *        thumbnailFlow.test 制）+PROJECT_RAW 夹具〔两节点一边——node id
 *        =n1/n2〕+vi.mock("@xyflow/react") importOriginal 展开仅替换
 *        ReactFlow 为捕获 props 的桩 div（children 照渲染）；测试树包
 *        <ReactFlowProvider>（FitViewOnNodes 顶层 useReactFlow 上下文供给）
 * 输出:  断言族：①dimensions 变更→桩收 nodes prop 中对应 node.measured
 *        注入 ②position/select 变更旁路=不注入（measured 缺席）③两次
 *        不同 id dimensions=累积并存（两 node.measured 同在）④MiniMap
 *        块窗口行锚（开标签 <MiniMap 至该元素闭合 /> 窗口内含裸 pannable、
 *        zoomable+position="bottom-left"——?raw 源结构）
 */
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReactFlowProvider, type NodeChange } from "@xyflow/react";
import { ThumbnailFlow } from "./thumbnailFlow";
import thumbnailFlowSource from "./thumbnailFlow.tsx?raw";

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
  flowProps: [] as Array<Record<string, unknown>>,
}));

vi.mock("@xyflow/react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@xyflow/react")>();
  /** ReactFlow 桩件：捕获 props 的 div（children 照渲染——FitViewOnNodes/
   *  Controls/MiniMap 走 ReactFlowProvider 上下文；仅替换 ReactFlow，
   *  其余导出面 importOriginal 展开）。 */
  const StubFlow = (props: Record<string, unknown>) => {
    gate.flowProps.push(props);
    return <div data-testid="wp-v4-flow-stub">{props.children as never}</div>;
  };
  return { ...actual, ReactFlow: StubFlow };
});

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

/** 夹具：两节点一边（projectFlow 真投影——受控 nodes prop 断言面）。 */
const PROJECT_RAW = {
  format_version: "4.0",
  design: {
    nodes: { n1: { kind: "municipal_input" }, n2: { kind: "junction" } },
    edges: [{ src: { unit_id: "n1", port_id: "out" }, dst: { unit_id: "n2", port_id: "in" } }],
  },
};

/** 桩捕获面读取（末次渲染 props——未渲染即读=测试侧显式错）。 */
function latestFlowProps(): Record<string, unknown> {
  const props = gate.flowProps[gate.flowProps.length - 1];
  if (props === undefined) {
    throw new Error("ReactFlow 桩未捕获 props（渲染未发生）");
  }
  return props;
}

/** 驱动捕获的 onNodesChange（受控变更通道——真件 handler 闭环）。 */
function driveNodesChange(changes: NodeChange[]): void {
  act(() => {
    (latestFlowProps().onNodesChange as (changes: NodeChange[]) => void)(changes);
  });
}

/** 桩收 nodes prop（受控面——measured 注入断言对象）。 */
type StubNode = { id: string; measured?: { width: number; height: number } };
function stubNodes(): StubNode[] {
  return latestFlowProps().nodes as StubNode[];
}

function mountFlow() {
  return render(
    <ReactFlowProvider>
      <ThumbnailFlow projectId="p1" onSelectedUnitChange={() => {}} />
    </ReactFlowProvider>,
  );
}

beforeEach(() => {
  gate.projectRaw = PROJECT_RAW;
  gate.flowProps = [];
});
afterEach(cleanup);

describe("工艺画布·受控测量回写接线（行为级——V5 P2）", () => {
  it("dimensions 变更→桩收 nodes prop 中对应 node.measured 注入", () => {
    mountFlow();
    driveNodesChange([
      { id: "n1", type: "dimensions", dimensions: { width: 47, height: 53 } },
    ] as NodeChange[]);
    const n1 = stubNodes().find((node) => node.id === "n1");
    expect(n1?.measured).toEqual({ width: 47, height: 53 });
  });

  it("position/select 变更旁路=不注入（measured 缺席）", () => {
    mountFlow();
    driveNodesChange([
      { id: "n1", type: "position", position: { x: 1, y: 2 } },
      { id: "n1", type: "select", selected: true },
    ] as NodeChange[]);
    for (const node of stubNodes()) {
      expect(node.measured).toBeUndefined();
    }
  });

  it("两次不同 id dimensions=累积并存（两 node.measured 同在）", () => {
    mountFlow();
    driveNodesChange([
      { id: "n1", type: "dimensions", dimensions: { width: 47, height: 53 } },
    ] as NodeChange[]);
    driveNodesChange([
      { id: "n2", type: "dimensions", dimensions: { width: 78, height: 31 } },
    ] as NodeChange[]);
    const nodes = stubNodes();
    expect(nodes.find((node) => node.id === "n1")?.measured).toEqual({
      width: 47,
      height: 53,
    });
    expect(nodes.find((node) => node.id === "n2")?.measured).toEqual({
      width: 78,
      height: 31,
    });
  });
});

describe("工艺画布·MiniMap 块窗口行锚（V5 P2——pannable/zoomable 自裸行锚升级）", () => {
  it("块窗口（<MiniMap 开标签至该元素闭合 />）：窗口内含裸 pannable、zoomable+position=bottom-left", () => {
    // 窗口域锚：自 `<MiniMap` 起至其后首个 `/>`（该元素自身闭合——style
    // 对象字面量内无 `/>` 形）——裸行锚不再全文件域匹配（旧 /^\s+pannable$/m
    // 误配面退役：注释字样/他件同名 prop 行不兜底）
    const openAt = thumbnailFlowSource.indexOf("<MiniMap");
    expect(openAt).toBeGreaterThanOrEqual(0);
    const closeAt = thumbnailFlowSource.indexOf("/>", openAt);
    expect(closeAt).toBeGreaterThan(openAt);
    const windowText = thumbnailFlowSource.slice(openAt, closeAt + 2);
    expect(windowText).toMatch(/^\s+pannable$/m);
    expect(windowText).toMatch(/^\s+zoomable$/m);
    expect(windowText).toContain('position="bottom-left"');
  });
});
