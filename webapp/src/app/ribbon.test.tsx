/**
 * @vitest-environment jsdom
 *
 * Ribbon 命令带 dom 测试（M1 批——D9 裁量下限：四命令在场+主钮 null
 * 禁用+菜单两项开 Modal 成形；M4 批 D1 导出快访接内容——导出钮改
 * Dropdown 形〔主钮切槽保持+总图直发+子面导航〕，旧导出/三维快访用例
 * 随形态迁入新 describe〔断言语义零弱化〕；M4 回炉 R1 轮 2026-10-07：
 * 用例④补 disabled 项点击后 not called 断言〔d1-W3 禁用不裸发锚——
 * 原仅读属性恒真〕+新增 R2 取数失败态 title 分流用例〔k1-W3+d1-W2：
 * isError≠无工况，I-3 分级禁「先提交计算」误导〕+新增 d1-N2 直发
 * onError→confirm 接线断言〔Modal.confirm spy——409 二选一在快访面
 * 保持的接线面锚〕；回炉 R4 轮〔门二探针 5/6——G6 态②红项处置〕：
 * 取数失败用例 error mock 改非 domain 网络错形〔维持锚非 domain 态〕
 * +新增 domain 态用例〔404 CostSourceNotFoundError→title 恢复「先提交
 * 计算」正确引导——R2 全 isError 合流取数失败使该引导不可达=G6 红项〕；
 * 回炉 R5 轮〔delta 二轮 d1 条件转化项〕：新增异构领域码负例用例
 * 〔WaterprintApiError 非 CostSourceNotFoundError→「取数失败」——防
 * domainGate 未来退化为按类判域的回归锚 d1-W1：类+code 全等双条件〕）。
 *
 * 输入:  Ribbon（QueryClientProvider 每用例新 client〔retry:false〕）+
 *        vi.mock 边界沿 paneDomainGate 纪律=feature api/store 模块面+
 *        generated 面无害空数据（禁 mock react-query 内部/antd；M4 增
 *        drawings 面 useConditionOptions/useExportArtifact 两 mock）；
 *        提交逻辑纯函数已由 canvasEditToolbar.test 随迁锁定（不重复测）
 * 输出:  断言组：①四命令锚在场（data-testid=wp-ribbon-run/validate/
 *        export/viewer3d+data-region=ribbon）；②projectId null=主钮
 *        禁用（title 指引）；③Dropdown 菜单两项（单元枚举…/联合枚举…）
 *        各开 Modal 成形（EnumerateBar「提交枚举」/JointSubmitForm
 *        「提交联合枚举」承载在场）；④projectId null=Modal 内提示不渲染
 *        表单；⑤导出快访 Dropdown 组（M4 D1）：主钮/下拉整体 null 禁用+
 *        title 指引/下拉两项 testid 两锚在场/主钮点击=onNavigate
 *        （studio.drawings——迁自旧用例，三维快访 viewer3d 同案保持）/
 *        无工况态总图直发项禁用+title 引导+disabled 项点击不裸发〔R3〕/
 *        取数失败态禁用+title 取数失败口径〔R2〕/有工况点击=真发起
 *        （unitId 空串 bare POST 总图语义+缺省首工况）/直发 onError→
 *        confirm 分支接线四字段〔d1-N2〕。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Modal } from "antd";
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Ribbon } from "./ribbon";
import type { TabTarget } from "./router";
import { WaterprintApiError } from "../shared/api/http";

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
    conditions: idle(),
    exportMutate: vi.fn(),
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
// M4 D1：导出快访面——工况源（drawings API）+总图直发 mutation 独立实例
vi.mock("../features/drawings/api/useExportsQuery", () => ({
  useConditionOptions: () => gate.conditions,
}));
vi.mock("../features/drawings/api/useExportArtifact", () => ({
  useExportArtifact: () => ({
    mutate: gate.exportMutate,
    mutateAsync: vi.fn(),
    isPending: false,
    isLoading: false,
  }),
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

describe("导出快访 Dropdown（M4 D1——主钮切槽保持+总图直发+子面导航）", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 缺省=idle（data undefined→空工况=直发项禁用面——④⑤用例各自覆写）
    gate.conditions = {
      data: undefined as unknown,
      isError: false,
      error: null as unknown,
      isPending: true,
      isLoading: true,
      isFetching: true,
      status: "pending",
      refetch: () => Promise.resolve({}),
    };
  });
  afterEach(cleanup);

  it("projectId null=主钮+下拉触发钮整体禁用（title 指引——先在画布槽选择项目）", () => {
    const view = renderRibbon(null, () => {});
    const main = view.container.querySelector(
      'button[data-testid="wp-ribbon-export"]',
    ) as HTMLButtonElement;
    expect(main).toBeTruthy();
    expect(main.disabled).toBe(true);
    expect(main.title).toBe("先在画布槽选择项目——图纸导出针对最近完成计算的结果集");
    // 下拉整体禁用（触发钮同禁——run 族 null 态口径对齐）
    const trigger = view.container.querySelectorAll(
      "button.ant-dropdown-trigger",
    )[1] as HTMLButtonElement;
    expect(trigger).toBeTruthy();
    expect(trigger.disabled).toBe(true);
  });

  it("下拉两项在场（容器 wp-ribbon-export-menu+总图直发/子面导航两锚）", () => {
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
    );
    const menu = screen.getByTestId("wp-ribbon-export-menu");
    expect(within(menu).getByTestId("wp-ribbon-export-total-dxf")).toBeTruthy();
    expect(within(menu).getByTestId("wp-ribbon-export-open-pane")).toBeTruthy();
  });

  it("主钮点击=onNavigate({studio, drawings})（既有用例随形态迁移——断言语义零弱化；三维快访→viewer3d 同案保持）", () => {
    const onNavigate = vi.fn();
    renderRibbon("p1", onNavigate);
    fireEvent.click(screen.getByTestId("wp-ribbon-export"));
    expect(onNavigate).toHaveBeenCalledWith({ slot: "studio", subface: "drawings" });
    fireEvent.click(screen.getByTestId("wp-ribbon-viewer3d"));
    expect(onNavigate).toHaveBeenCalledWith({ slot: "viewer3d" });
  });

  it("总图直发项无工况态禁用+title 引导+disabled 项点击不裸发（工况源=最近完成计算的结果集；R3——点击在先非恒真）", () => {
    gate.conditions = { ...gate.conditions, data: [] };
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
    );
    const item = screen.getByTestId("wp-ribbon-export-total-dxf");
    const li = item.closest("li") as HTMLLIElement;
    expect(li.getAttribute("aria-disabled")).toBe("true");
    expect(li.title).toBe("先提交计算——工况源为最近完成计算的结果集");
    // R3（d1-W3）：disabled 项点击（rc-menu 对 disabled onClick 抑制——
    // 真实可测面）→禁用不裸发（DoD 语义两锚之一：菜单抑制+组件守卫）
    fireEvent.click(item);
    expect(gate.exportMutate).not.toHaveBeenCalled();
  });

  it("总图直发项取数失败态（非 domain：网络错/5xx/select 拒）禁用+title 取数失败口径（R2+R4——I-3 分级禁「先提交计算」误导）", () => {
    gate.conditions = {
      ...gate.conditions,
      data: [],
      isError: true,
      error: new Error("工况端点网络错"),
    };
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
    );
    const li = screen.getByTestId("wp-ribbon-export-total-dxf").closest("li") as HTMLLIElement;
    expect(li.getAttribute("aria-disabled")).toBe("true");
    expect(li.title).toBe("工况源取数失败——请稍后重试或检查服务");
    expect(li.title).not.toContain("先提交计算"); // 误导字样禁入非 domain error 态（R4：domain 态合法含）
  });

  it("总图直发项 domain 态（404 无 done calc）title 恢复先提交计算引导（R4——G6 红项：真无完成计算的用户该提交计算非重试）", () => {
    gate.conditions = {
      ...gate.conditions,
      data: [],
      isError: true,
      error: new WaterprintApiError("CostSourceNotFoundError", "raw 服务端句式不入用户面"),
    };
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
    );
    const li = screen.getByTestId("wp-ribbon-export-total-dxf").closest("li") as HTMLLIElement;
    expect(li.getAttribute("aria-disabled")).toBe("true");
    expect(li.title).toBe("先提交计算——工况源为最近完成计算的结果集");
  });

  it("总图直发项异构领域码负例（WaterprintApiError 非 CostSourceNotFoundError）→取数失败口径（R5——防 domainGate 退化为按类判域的回归锚 d1-W1：类+code 全等双条件）", () => {
    gate.conditions = {
      ...gate.conditions,
      data: [],
      isError: true,
      error: new WaterprintApiError("StaleExportError", "类同码异——异构领域码负例"),
    };
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
    );
    const li = screen.getByTestId("wp-ribbon-export-total-dxf").closest("li") as HTMLLIElement;
    expect(li.getAttribute("aria-disabled")).toBe("true");
    expect(li.title).toBe("工况源取数失败——请稍后重试或检查服务");
    expect(li.title).not.toContain("先提交计算"); // 类同码异=domain:false（fail-closed）
  });

  it("有工况时总图直发项点击=真发起（unitId 空串 bare POST 总图语义+缺省首工况——DoD1 直发链锚）", () => {
    gate.conditions = { ...gate.conditions, data: ["design", "avg"] };
    const view = renderRibbon("p1", () => {});
    fireEvent.click(
      view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
    );
    fireEvent.click(screen.getByTestId("wp-ribbon-export-total-dxf"));
    expect(gate.exportMutate).toHaveBeenCalledTimes(1);
    expect(gate.exportMutate).toHaveBeenCalledWith(
      { projectId: "p1", unitId: "", conditionKey: "design", force: false },
      expect.anything(),
    );
  });

  it("直发 onError→surfaceExportError confirm 分支接线（409 二选一在快访面保持——d1-N2：Modal.confirm spy 四字段）", () => {
    gate.conditions = { ...gate.conditions, data: ["design"] };
    const confirmSpy = vi
      .spyOn(Modal, "confirm")
      .mockImplementation(() => ({ destroy: vi.fn(), update: vi.fn() }));
    try {
      const view = renderRibbon("p1", () => {});
      fireEvent.click(
        view.container.querySelectorAll("button.ant-dropdown-trigger")[1] as HTMLElement,
      );
      fireEvent.click(screen.getByTestId("wp-ribbon-export-total-dxf"));
      expect(gate.exportMutate).toHaveBeenCalledTimes(1);
      // 经 mutation mock 触发 onError（StaleExportError 面）→断言 confirm 接线
      const onError = (gate.exportMutate.mock.calls[0]?.[1] as {
        onError: (error: unknown) => void;
      }).onError;
      act(() => {
        onError(new WaterprintApiError("StaleExportError", "结果集落后当前设计 2 版"));
      });
      expect(confirmSpy).toHaveBeenCalledTimes(1);
      const config = confirmSpy.mock.calls[0]?.[0] as Record<string, unknown>;
      expect(config.title).toBe("结果集已过期（stale）");
      expect(config.content).toBe("结果集落后当前设计 2 版");
      expect(config.okText).toBe("仍导出旧结果（force）");
      expect(config.cancelText).toBe("先重算");
    } finally {
      confirmSpy.mockRestore();
    }
  });
});
