/**
 * @vitest-environment jsdom
 *
 * v4 工作台区测试（b3 功能面重涂批 2026-11-19——稿 workbench.html 形：
 * 页头两钮建项流〔initialMode 直开导入态〕+指标带/当前工艺/继续工作/
 * 规划能力锚族+建项成功 openProject 动线。ProjectsZone/CreateProjectModal
 * 子面 stub（各自专测件承载真件断言——Modal 以 props 捕获替身参与流）。
 *
 * 输入:  WorkbenchZone（useProjectId/项目读/units 目录/校验聚合/任务快照
 *        模块替身+ProjectsZone/CreateProjectModal stub——onCreated 可触发）
 * 输出:  断言族：①页头两钮：新建=initialMode blank/导入=import 开 Modal
 *        ②onCreated=切项目+清 ?node=+onNavigate process ③指标带 region
 *        在场+无项目三格「—」占位④继续工作三行→onNavigate 对应入口
 *        ⑤规划能力条 wp-pending-network 锚族在场⑥任务卡空态引导
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { WorkbenchZone } from "./workbenchZone";

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
  setProjectId: vi.fn(),
  navigate: vi.fn(),
  openSettings: vi.fn(),
  createProps: null as {
    open: boolean;
    initialMode?: string;
    onCreated: (id: string) => void;
    onClose: () => void;
  } | null,
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId, gate.setProjectId],
}));
vi.mock("./projectsZone", () => ({
  ProjectsZone: () => <section data-testid="wp-v4-projects-stub" />,
}));
vi.mock("../createProjectModal", () => ({
  CreateProjectModal: (props: {
    open: boolean;
    initialMode?: string;
    onCreated: (id: string) => void;
    onClose: () => void;
  }) => {
    gate.createProps = props;
    return null;
  },
}));
vi.mock("../../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => ({
    data: undefined,
    isError: false,
    error: null,
  }),
}));
vi.mock("../../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({ data: { units: [] }, isError: false }),
}));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => ({
    data: undefined,
    isError: false,
    error: null,
    isLoading: true,
  }),
}));
vi.mock("../../features/validation/api/useValidationQuery", () => ({
  // enabled 门语义替身：projectId=null=禁用零数据（真 hook 同口径）
  useValidationQuery: (projectId: string | null) =>
    projectId === null
      ? { data: undefined, isError: false, error: null }
      : { data: { warnings: [{}, {}, {}] }, isError: false, error: null },
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderZone() {
  return render(
    <QueryClientProvider client={queryClient}>
      <WorkbenchZone onNavigate={gate.navigate} onOpenSettings={gate.openSettings} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.projectId = "p1";
  gate.setProjectId.mockClear();
  gate.navigate.mockClear();
  gate.openSettings.mockClear();
  gate.createProps = null;
  window.history.replaceState(null, "", "/");
});
afterEach(cleanup);

describe("工作台·页头建项两钮（b3——initialMode 直开两态）", () => {
  it("新建项目钮=blank 态开 Modal；导入项目钮=import 态开 Modal", () => {
    renderZone();
    fireEvent.click(document.querySelector('[data-testid="wp-v4-proj-create"]') as HTMLElement);
    expect(gate.createProps?.open).toBe(true);
    expect(gate.createProps?.initialMode).toBe("blank");
    // 关闭后重开导入态
    gate.createProps?.onClose();
    fireEvent.click(document.querySelector('[data-testid="wp-v4-proj-import"]') as HTMLElement);
    expect(gate.createProps?.initialMode).toBe("import");
  });

  it("onCreated=切项目+清 ?node=+onNavigate process（建项即进工艺页）", () => {
    window.history.replaceState(null, "", "/?node=municipal_aao&x=1");
    renderZone();
    gate.createProps?.onCreated("ab12cd34");
    expect(gate.setProjectId).toHaveBeenCalledWith("ab12cd34");
    expect(gate.navigate).toHaveBeenCalledWith({ nav: "process" });
    // 清 ?node= 他键保留（replaceState 面）
    expect(window.location.search).toBe("?x=1");
  });
});

describe("工作台·信息面锚（b3 稿 workbench.html 段）", () => {
  it("指标带 region 在场+聚合警告计数=3（validation 通道单源）", () => {
    const { container } = renderZone();
    expect(
      container.querySelector('[data-region="workbench-metrics"]'),
    ).not.toBeNull();
    expect(container.textContent).toContain("聚合警告");
    const values = container.querySelectorAll(".wp-wb-metric .value");
    expect(values[2]?.textContent).toBe("3");
  });

  it("无项目态：指标三格「—」占位+当前工艺面板缺席", () => {
    gate.projectId = null;
    const { container } = renderZone();
    const values = container.querySelectorAll(".wp-wb-metric .value");
    expect(values.length).toBe(3);
    for (const value of values) {
      expect(value.textContent).toBe("—");
    }
    expect(
      container.querySelector('[data-region="workbench-process"]'),
    ).toBeNull();
  });

  it("继续工作三行→onNavigate（parameters/analysis/deliverables.report）", () => {
    renderZone();
    fireEvent.click(document.querySelector('[data-testid="wp-v4-continue-params"]') as HTMLElement);
    fireEvent.click(document.querySelector('[data-testid="wp-v4-continue-analysis"]') as HTMLElement);
    fireEvent.click(document.querySelector('[data-testid="wp-v4-continue-report"]') as HTMLElement);
    expect(gate.navigate).toHaveBeenCalledTimes(3);
    expect(gate.navigate).toHaveBeenNthCalledWith(1, { nav: "parameters" });
    expect(gate.navigate).toHaveBeenNthCalledWith(2, { nav: "analysis" });
    expect(gate.navigate).toHaveBeenNthCalledWith(3, {
      nav: "deliverables",
      subpage: "report",
    });
  });

  it("规划能力条 wp-pending-network 锚族在场（G5 沿承）+任务卡空态引导", () => {
    const { container } = renderZone();
    expect(
      container.querySelector('[data-testid="wp-pending-network"]')?.textContent,
    ).toContain("规划中，未实装");
    expect(container.textContent).toContain("暂无任务记录");
  });
});
