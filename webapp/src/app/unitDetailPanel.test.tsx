/**
 * @vitest-environment jsdom
 *
 * 单元详情面板测试（M2 批 2026-10-08——Drawer 详情收编 Settings 右窗：
 * 头部四要素/参数面五列+kind 两分空态/端口面四列+回流 Tag/✕ 解除钮/
 * 「到工艺画布」导航钮成对语义/编辑态「添加到画布」/目录无此键 Empty）。
 *
 * 输入:  UnitDetailPanel（vi.mock 边界沿 studyPane/seatTaskPage 纪律=
 *        generated units hook 桩+canvasStore 模块桩〔useEditing 受控态位+
 *        useCanvasStore.getState().addUnit 调用实录〕+useProjectId 桩；
 *        禁 mock react-query 内部/antd——Table/Empty/Button/message 原件
 *        真渲染）
 * 输出:  断言组：①头部四要素（name_zh/unit_id/KindTag/所属线）+
 *        wp-unit-detail 探针锚；②参数面五列头+空 params kind 两分文案；
 *        ③端口面四列头+回流 Tag；④✕→onClose；⑤「到工艺画布」→
 *        onNavigateTab+onClose 成对；⑥编辑态「添加到画布」显/只读态
 *        不显+点击 addUnit 实录；⑦目录无此键→Empty+✕ 仍在。
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { UnitDetailPanel } from "./unitDetailPanel";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面）
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

/** 受控态位（vi.hoisted——各 mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  units: [] as unknown[],
  isPending: false,
  isError: false,
  editing: false,
  projectId: "p1" as string | null,
  addedUnits: [] as { unitId: string; kind: string }[],
}));

vi.mock("../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({
    data: { units: gate.units },
    isPending: gate.isPending,
    isLoading: gate.isPending,
    isError: gate.isError,
    error: null,
    isFetching: false,
    status: gate.isPending ? "pending" : "success",
    refetch: () => Promise.resolve({}),
  }),
}));
vi.mock("../features/canvas/store/canvasStore", () => ({
  useCanvasStore: {
    getState: () => ({
      addUnit: (unitId: string, kind: string) => {
        gate.addedUnits.push({ unitId, kind });
        return `${unitId}-node-1`;
      },
    }),
  },
  useEditing: () => gate.editing,
}));
vi.mock("./useProjectId", () => ({
  useProjectId: () => [gate.projectId, () => {}],
}));

/** 目录单元夹具（params/ports 可覆写——形态对齐 UnitMetaEntry 生成类型）。 */
function makeUnit(overrides: Record<string, unknown> = {}) {
  return {
    unit_id: "municipal_aao",
    name_zh: "AAO 生物池",
    business_line: "municipal",
    kind: "unit",
    params: [
      {
        field_id: "volume",
        label_zh: "池容",
        dim: "VOLUME",
        default: 1000,
        range: { min: 100, max: 5000 },
        grid: null,
      },
    ],
    ports: [
      { port_id: "inlet", fluid: "WATER", direction: "IN", recycle: false },
      { port_id: "return", fluid: "SLUDGE", direction: "IN", recycle: true },
    ],
    ...overrides,
  };
}

/** 三回调 spy 渲染面（onClose/onNavigateTab 调用计数断言源）。 */
function renderPanel(unitId = "municipal_aao") {
  const onClose = vi.fn();
  const onNavigateTab = vi.fn();
  const view = render(
    <UnitDetailPanel
      unitId={unitId}
      onClose={onClose}
      onNavigateTab={onNavigateTab}
    />,
  );
  return { onClose, onNavigateTab, unmount: view.unmount };
}

beforeEach(() => {
  gate.units = [makeUnit()];
  gate.isPending = false;
  gate.isError = false;
  gate.editing = false;
  gate.projectId = "p1";
  gate.addedUnits.length = 0;
});
afterEach(cleanup);

describe("UnitDetailPanel 头部与详情面（M2 D1 收编面）", () => {
  it("①目录单元→头部四要素在场（name_zh/unit_id/KindTag/所属线）+wp-unit-detail 锚", () => {
    renderPanel();
    expect(screen.getByTestId("wp-unit-detail")).toBeTruthy();
    expect(screen.getByText("AAO 生物池")).toBeTruthy();
    expect(screen.getByText("municipal_aao")).toBeTruthy();
    expect(screen.getByText("单元")).toBeTruthy(); // KindTag（kind=unit）
    expect(screen.getByText("市政污水")).toBeTruthy(); // 所属线（BUSINESS_LINE_ZH）
  });

  it("②参数面五列头在场+空 params kind 两分文案（builtin/非 builtin）", () => {
    const { unmount } = renderPanel();
    for (const head of ["参数", "量纲", "默认值", "范围", "网格"]) {
      expect(screen.getByText(head)).toBeTruthy();
    }
    expect(screen.getByText("池容")).toBeTruthy(); // 参数行 label_zh 主列
    unmount();
    cleanup();
    // kind 两分空态：builtin 空 params=「内置节点无参数面」
    gate.units = [makeUnit({ unit_id: "junction", kind: "builtin", params: [] })];
    renderPanel("junction");
    expect(screen.getByText("内置节点无参数面")).toBeTruthy();
    unmount();
    cleanup();
    // 非 builtin 空 params=「该单元无参数面」（未来防御面文案沿袭）
    gate.units = [makeUnit({ params: [] })];
    renderPanel();
    expect(screen.getByText("该单元无参数面")).toBeTruthy();
  });

  it("③端口面四列头在场+回流 Tag（recycle=true）", () => {
    renderPanel();
    for (const head of ["端口", "流体", "方向"]) {
      expect(screen.getByText(head)).toBeTruthy();
    }
    expect(screen.getByText("inlet")).toBeTruthy();
    // 「回流」在列头 th 与 recycle=true 行 Tag 两处复用——多重匹配合规
    // （studyPane 列头先例同口径），断言两处俱在
    expect(screen.getAllByText("回流").length).toBe(2);
  });

  it("④✕ 解除钮→onClose 调用（title=解除选中——关闭详情）", () => {
    const { onClose } = renderPanel();
    fireEvent.click(screen.getByTitle("解除选中——关闭详情"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("⑤「到工艺画布」→onNavigateTab+onClose 成对（导航并解除——Drawer 语义沿袭）", () => {
    const { onClose, onNavigateTab } = renderPanel();
    fireEvent.click(screen.getByText(/到工艺画布/));
    expect(onNavigateTab).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("⑥编辑态「添加到画布」显+点击 addUnit 实录/只读态不显（useEditing 受控）", () => {
    const { unmount } = renderPanel();
    expect(screen.queryByText(/添加到画布/)).toBeNull(); // 只读态零呈现
    unmount();
    cleanup();
    gate.editing = true;
    renderPanel();
    fireEvent.click(screen.getByText(/添加到画布/));
    expect(gate.addedUnits).toEqual([
      { unitId: "municipal_aao", kind: "unit" },
    ]);
  });

  it("⑦目录无此键→Empty「单元目录中无此单元」+✕ 仍在场", () => {
    const { onClose } = renderPanel("ghost_unit");
    expect(screen.getByText("单元目录中无此单元")).toBeTruthy();
    fireEvent.click(screen.getByTitle("解除选中——关闭详情"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
