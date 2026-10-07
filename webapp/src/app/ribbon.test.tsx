/**
 * @vitest-environment jsdom
 *
 * Ribbon 命令带 dom 测试（M1 批——D9 裁量下限：四命令在场+主钮 null
 * 禁用+菜单两项开 Modal 成形）。
 *
 * 输入:  Ribbon（QueryClientProvider 每用例新 client〔retry:false〕）+
 *        vi.mock 边界沿 paneDomainGate 纪律=feature api/store 模块面+
 *        generated 面无害空数据（禁 mock react-query 内部/antd）；提交
 *        逻辑纯函数已由 canvasEditToolbar.test 随迁锁定（不重复测）
 * 输出:  断言组：①四命令锚在场（data-testid=wp-ribbon-run/validate/
 *        export/viewer3d+data-region=ribbon）；②projectId null=主钮
 *        禁用（title 指引）；③Dropdown 菜单两项（单元枚举…/联合枚举…）
 *        各开 Modal 成形（EnumerateBar「提交枚举」/JointSubmitForm
 *        「提交联合枚举」承载在场）；④projectId null=Modal 内提示不渲染
 *        表单；⑤导出/三维快访=onNavigate 目标（studio.drawings/viewer3d）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Ribbon } from "./ribbon";
import type { TabTarget } from "./router";

// jsdom 环境缺口补丁（浏览器 API 级——非组件/react-query/antd mock 面）：
// antd 浮层（Dropdown/Modal/Popover）挂载期消费 ResizeObserver。
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 受控态位（vi.hoisted——各 mock 工厂闭包同源读写；react-query v5 常读
 *  字段族沿 paneDomainGate D4 口径补齐：pending 语义=data undefined）。 */
const gate = vi.hoisted(() => {
  const idle = () => ({
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
    isPending: true,
    isLoading: true,
    isFetching: true,
    status: "pending",
    refetch: () => Promise.resolve({}),
  });
  const mutation = () => ({
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    isPending: false,
    isLoading: false,
  });
  return {
    raw: idle(),
    units: idle(),
    constraints: idle(),
    catalog: idle(),
    mutation,
    enumOnSuccess: null as ((response: { task_id: string }) => void) | null,
  };
});

vi.mock("../features/canvas/store/canvasStore", () => ({
  useEditing: () => false,
  useDirty: () => false,
  useDraft: () => null,
  useCanvasStore: { getState: () => ({ markSaved: vi.fn(), beginEdit: vi.fn(), endEdit: vi.fn() }) },
}));
vi.mock("../features/params/store/paramsStore", () => ({
  useParamsStore: () => 0,
}));
vi.mock("../features/params/api/useConstraints", () => ({
  useConstraints: () => gate.constraints,
}));
vi.mock("../features/params/api/useUnitCatalog", () => ({
  useUnitCatalog: () => gate.catalog,
  useAssumptionCatalog: () => gate.catalog,
}));
vi.mock("../features/solutions/api/useProjectUnits", () => ({
  useProjectUnits: () => gate.units,
}));
vi.mock("../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => gate.raw,
  useSaveProjectApiProjectsProjectIdPut: () => gate.mutation(),
  useValidateProjectApiProjectsProjectIdValidatePost: () => gate.mutation(),
}));
vi.mock("../shared/api/generated/calc/calc", () => ({
  useRunCalculationApiCalcRunPost: () => gate.mutation(),
  useRunEnumerationApiCalcEnumeratePost: (
    options?: { mutation?: { onSuccess?: (response: { task_id: string }) => void } },
  ) => {
    gate.enumOnSuccess = options?.mutation?.onSuccess ?? null;
    return gate.mutation();
  },
}));
vi.mock("../shared/api/generated/solution/solution", () => ({
  useRunJointEnumerationApiSolutionJointEnumeratePost: () => gate.mutation(),
}));

/** 每用例新 QueryClient（retry:false——paneDomainGate 同款）。 */
function renderRibbon(projectId: string | null, onNavigate: (t: TabTarget) => void) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const view = render(<Ribbon projectId={projectId} onNavigate={onNavigate} />, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  });
  return view;
}

describe("Ribbon 四命令在场（M1 定版）", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  afterEach(cleanup);

  it("data-region=ribbon+四命令锚在场（wp-ribbon-run/validate/export/viewer3d）", () => {
    renderRibbon("p1", () => {});
    expect(screen.getByTestId("wp-ribbon-run")).toBeTruthy();
    expect(screen.getByTestId("wp-ribbon-validate")).toBeTruthy();
    expect(screen.getByTestId("wp-ribbon-export")).toBeTruthy();
    expect(screen.getByTestId("wp-ribbon-viewer3d")).toBeTruthy();
  });

  it("projectId null=主钮禁用（title 指引——先在画布槽选择项目）", () => {
    const view = renderRibbon(null, () => {});
    const run = view.container.querySelector(
      'button[data-testid="wp-ribbon-run"]',
    ) as HTMLButtonElement;
    expect(run).toBeTruthy();
    expect(run.disabled).toBe(true);
    expect(run.title).toBe("先在画布槽选择项目");
  });
});

describe("枚举两轨 Modal（三入口收编一——菜单两项）", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  afterEach(cleanup);

  it("菜单「单元枚举…」开 Modal：EnumerateBar 承载在场（提交枚举钮）", () => {
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelector("button.ant-dropdown-trigger") as HTMLElement,
    );
    fireEvent.click(screen.getByText("单元枚举…"));
    expect(screen.getByText("单元枚举")).toBeTruthy();
    expect(screen.getByRole("button", { name: "提交枚举" })).toBeTruthy();
  });

  it("菜单「联合枚举…」开 Modal：JointSubmitForm 承载在场（提交联合枚举钮）", () => {
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelector("button.ant-dropdown-trigger") as HTMLElement,
    );
    fireEvent.click(screen.getByText("联合枚举…"));
    expect(screen.getByText("联合枚举")).toBeTruthy();
    expect(screen.getByRole("button", { name: "提交联合枚举" })).toBeTruthy();
  });

  it("枚举提交 onSuccess 文案：进度指引指向右侧 AI 席位「任务」分页（结果呈现随 M6 批）", () => {
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelector("button.ant-dropdown-trigger") as HTMLElement,
    );
    fireEvent.click(screen.getByText("单元枚举…"));
    expect(gate.enumOnSuccess).not.toBeNull();
    act(() => {
      (gate.enumOnSuccess as (response: { task_id: string }) => void)({
        task_id: "enum-t1",
      });
    });
    expect(
      screen.getByText(/进度见右侧 AI 席位「任务」分页——结果呈现随 M6 批/),
    ).toBeTruthy();
  });

  it("projectId null=Modal 内提示不渲染表单（单元枚举轨）", () => {
    const view = renderRibbon(null, () => {});
    fireEvent.click(
      view.container.querySelector("button.ant-dropdown-trigger") as HTMLElement,
    );
    fireEvent.click(screen.getByText("单元枚举…"));
    expect(
      screen.getByText("尚未选择项目——请先在画布槽选择项目"),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: "提交枚举" })).toBeNull();
  });
});

describe("导出/三维快访（槽切换非 feature 命令）", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  afterEach(cleanup);

  it("导出→onNavigate({studio, drawings})；三维快访→onNavigate({viewer3d})", () => {
    const onNavigate = vi.fn();
    renderRibbon("p1", onNavigate);
    fireEvent.click(screen.getByTestId("wp-ribbon-export"));
    expect(onNavigate).toHaveBeenCalledWith({ slot: "studio", subface: "drawings" });
    fireEvent.click(screen.getByTestId("wp-ribbon-viewer3d"));
    expect(onNavigate).toHaveBeenCalledWith({ slot: "viewer3d" });
  });
});
