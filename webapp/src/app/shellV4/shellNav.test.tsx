/**
 * @vitest-environment jsdom
 *
 * v4 八入口导航壳级测试（b2 壳重组批 2026-11-19——mount 真 ShellV4：
 * 窄导航轨八条目序/选中语义/切换写 ?tab=/旧值深链兼容归一〔mount 不改
 * 写地址栏〕/初值四级深链/状态条单机标识+主题切换器槽+任务快速入口。
 * 制式沿 shellV4SelfHealWiring.test——数据面替身，壳装配链实证）。
 *
 * 输入:  ShellV4 真件（jsdom 挂载——useProjectId/生成 hook/取数面模块
 *        替身；各入口重子面 stub 零渲染，navRail/topBar/statusBar/
 *        processZone/parametersZone/deliverablesZone/aiZone 真件保留=
 *        装配链实证面）
 * 输出:  断言族：①轨八条目声明序+中文名+aria-current 选中语义 ②点击切
 *        换：入口体 region 翻转+URL ?tab= 写入（他键保留）③旧值深链：
 *        ?tab=design.analysis→分析面挂载且地址栏不改写 ④初值四级：
 *        ?node=→工艺/?task=→参数方案/缺省→工作台 ⑤状态条：单机标识
 *        在场+主题切换器在场（三钮）+任务 ▴→AI 入口 ⑥deliverables
 *        子页切换：树条目→?tab=deliverables.report；点轨当前入口=
 *        子页重置缺省 sheets
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ShellV4 } from "./shellV4";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** localStorage 存根（本环境 jsdom 面无原生方法族——侧栏宽度/token 回显
 *  消费；Map 薄壳足量三函数面）。 */
const storageBack = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storageBack.get(key) ?? null,
  setItem: (key: string, value: string) => void storageBack.set(key, value),
  removeItem: (key: string) => void storageBack.delete(key),
});

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  projectId: "p1" as string | null,
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId],
}));
// 重子面 stub（本测面=壳装配+导航轨——其余面零渲染；真件=navRail/
// topBar/statusBar/processZone/parametersZone/deliverablesZone/aiZone）
vi.mock("../../features/params/components/AssumptionsPanel", () => ({
  AssumptionsPanel: () => null,
}));
vi.mock("../../features/params/components/ParamForm", () => ({
  ParamForm: () => null,
}));
vi.mock("./thumbnailFlow", () => ({ ThumbnailFlow: () => null }));
vi.mock("./enumerateModal", () => ({ EnumerateModal: () => null }));
vi.mock("./analysisPane", () => ({
  AnalysisPane: () => <div data-region="analysis-stub" />,
  StaleBanner: () => null,
}));
vi.mock("./solutionCards", () => ({ SolutionCards: () => null }));
vi.mock("./jointSolutionCards", () => ({ JointSolutionCards: () => null }));
vi.mock("./backfillSection", () => ({ BackfillSection: () => null }));
vi.mock("./reportZone", () => ({
  ReportZone: () => <section data-testid="wp-v4-report-stub" />,
}));
vi.mock("../viewer3dPane", () => ({
  Viewer3dPane: () => null,
}));
// deliverablesZone 重子面 stub（本测面=壳导航——图纸/项目子面零渲染，
// 各子面自有专测件承载真件断言）
vi.mock("./projectsZone", () => ({
  ProjectsZone: () => <section data-testid="wp-v4-projects-stub" />,
}));
// b3 工作台重涂面 stub（建项 Modal/校验聚合/对象树清单——工作台专测件
// workbenchZone.test 承载真件断言）
vi.mock("../createProjectModal", () => ({
  CreateProjectModal: () => null,
}));
vi.mock("../../features/validation/api/useValidationQuery", () => ({
  useValidationQuery: () => ({
    data: undefined,
    isError: false,
    error: null,
  }),
}));
vi.mock("../../features/solutions/api/useProjectUnits", () => ({
  useProjectUnits: () => ({
    data: [
      { unitId: "municipal_aao", kind: null },
      { unitId: "municipal_cass", kind: null },
    ],
    isError: false,
    error: null,
  }),
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
vi.mock("../../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({ data: {} }),
}));
vi.mock("../siteplanPane", () => ({
  SiteplanPane: () => null,
}));
// compare 数据面替身（loading 态——compare-matrix region 仍可锚）
vi.mock("../../features/compare/api/useCompareQuery", () => ({
  useCompareQuery: () => ({ data: undefined, isError: false }),
}));
// aiZone 取数面替身（AiDockWindow 会话/任务条）
vi.mock("../../features/ai_chat/api/useAiChat", () => ({
  useChatHistory: () => ({ data: undefined, isError: false, error: null }),
  useSendChatMessage: () => ({ mutate: () => {}, isPending: false }),
  // b4 会话清单（AiSessionsPane/标题面）——空清单空态
  useChatSessions: () => ({ data: [], isPending: false, isError: false }),
}));
vi.mock("../../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: () => null,
}));
// 生成 hook 替身（aiZone 任务快照+topBar 项目读/存/校验/计算四族）
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => ({
    data: undefined, isError: false, error: null, isLoading: true,
  }),
  useRunCalculationApiCalcRunPost: () => ({
    mutate: () => {}, mutateAsync: () => Promise.resolve({ task_id: "t-x" }),
    isPending: false, isError: false, error: null, reset: () => {},
  }),
}));
vi.mock("../../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => ({
    data: undefined, isError: false, error: null, isLoading: true,
  }),
  useSaveProjectApiProjectsProjectIdPut: () => ({
    mutate: () => {}, mutateAsync: () => Promise.resolve({}),
    isPending: false, isError: false, error: null,
  }),
  useValidateProjectApiProjectsProjectIdValidatePost: () => ({
    mutate: () => {}, isPending: false, isError: false, error: null, reset: () => {},
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderShell(search = "") {
  window.history.replaceState(null, "", `/${search}`);
  return render(
    <QueryClientProvider client={queryClient}>
      <ShellV4 />
    </QueryClientProvider>,
  );
}

/** 轨条目钮定位。 */
const railButton = (nav: string): HTMLButtonElement | null =>
  document.querySelector<HTMLButtonElement>(`[data-testid="wp-v4-nav-${nav}"]`);

beforeEach(() => {
  gate.projectId = "p1";
  storageBack.clear();
});
afterEach(cleanup);

describe("b2 八入口导航壳（mount 真 ShellV4）", () => {
  it("轨八条目声明序+中文名+aria-current 选中语义（缺省工作台）", () => {
    renderShell();
    const rail = document.querySelector('[data-region="nav-rail"]');
    expect(rail).not.toBeNull();
    const links = Array.from(
      rail?.querySelectorAll<HTMLButtonElement>(".wp-v4-rail-link") ?? [],
    );
    expect(links.map((link) => link.textContent)).toEqual([
      "工作台",
      "工艺",
      "参数方案",
      "分析",
      "工况",
      "图纸报告",
      "三维",
      "AI 助手",
    ]);
    expect(links.map((link) => link.dataset.nav)).toEqual([
      "workbench",
      "process",
      "parameters",
      "analysis",
      "compare",
      "deliverables",
      "viewer3d",
      "ai",
    ]);
    // 缺省工作台：aria-current=page 恰一条
    const current = links.filter((link) =>
      link.getAttribute("aria-current") === "page",
    );
    expect(current.length).toBe(1);
    expect(current[0]?.dataset.nav).toBe("workbench");
  });

  it("点击切换：入口体 region 翻转+URL ?tab= 写入（他键保留）", async () => {
    renderShell("?project=p1");
    expect(document.querySelector('[data-region="workbench"]')).not.toBeNull();
    // 工艺
    fireEvent.click(railButton("process") as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="process-canvas"]')).not.toBeNull();
    });
    expect(window.location.search).toBe("?project=p1&tab=process");
    expect(
      railButton("process")?.getAttribute("aria-current"),
    ).toBe("page");
    // AI 助手
    fireEvent.click(railButton("ai") as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="ai-workspace"]')).not.toBeNull();
    });
    expect(window.location.search).toBe("?project=p1&tab=ai");
    // 参数方案/分析（stub 面）/工况/三维
    fireEvent.click(railButton("parameters") as HTMLButtonElement);
    await waitFor(() => {
      expect(
        document.querySelector('[data-region="parameters-workspace"]'),
      ).not.toBeNull();
    });
    fireEvent.click(railButton("analysis") as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="analysis-stub"]')).not.toBeNull();
    });
    fireEvent.click(railButton("compare") as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="compare-matrix"]')).not.toBeNull();
    });
    fireEvent.click(railButton("viewer3d") as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="viewer3d-full"]')).not.toBeNull();
    });
    expect(window.location.search).toBe("?project=p1&tab=viewer3d");
  });

  it("旧值深链兼容归一：?tab=design.analysis→分析面挂载且地址栏不改写（mount 纯读）", () => {
    renderShell("?project=p1&tab=design.analysis");
    expect(document.querySelector('[data-region="analysis-stub"]')).not.toBeNull();
    // mount 不改写：兼容值原样留 URL 至下次切换（M1 边缘语义 a 同口径）
    expect(window.location.search).toBe("?project=p1&tab=design.analysis");
    // 旧 v4 zone 裸值/legacy 值两代抽查
    cleanup();
    renderShell("?tab=report");
    expect(
      document.querySelector('[data-region="deliverables-report"]'),
    ).not.toBeNull();
    cleanup();
    renderShell("?tab=solutions");
    expect(
      document.querySelector('[data-region="parameters-workspace"]'),
    ).not.toBeNull();
    cleanup();
    renderShell("?tab=studio.compare");
    expect(document.querySelector('[data-region="compare-matrix"]')).not.toBeNull();
  });

  it("初值四级深链：?node=→工艺/?task=→参数方案/缺省→工作台", () => {
    renderShell("?node=municipal_aao");
    expect(document.querySelector('[data-region="process-canvas"]')).not.toBeNull();
    cleanup();
    renderShell("?task=t-1");
    expect(
      document.querySelector('[data-region="parameters-workspace"]'),
    ).not.toBeNull();
    cleanup();
    renderShell("");
    expect(document.querySelector('[data-region="workbench"]')).not.toBeNull();
  });

  it("状态条：单机标识+主题切换器（三钮）在场+任务 ▴→AI 入口", async () => {
    renderShell();
    const bar = document.querySelector('[data-region="status-bar"]');
    expect(bar).not.toBeNull();
    expect(
      bar?.querySelector('[data-testid="wp-v4-standalone-mode"]')?.textContent,
    ).toContain("单机模式 · 本地引擎");
    // 主题切换器三钮（b1 件迁状态条）
    const themeButtons = bar?.querySelectorAll("[data-theme-mode]");
    expect(themeButtons?.length).toBe(3);
    // 任务快速入口→AI 入口
    const taskEntry = Array.from(
      bar?.querySelectorAll<HTMLButtonElement>("button") ?? [],
    ).find((button) => button.textContent?.includes("任务"));
    expect(taskEntry).toBeDefined();
    fireEvent.click(taskEntry as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="ai-workspace"]')).not.toBeNull();
    });
    expect(window.location.search).toBe("?tab=ai");
    // AI 页任务入口自隐（任务条本体在场）
    expect(
      Array.from(
        document
          .querySelector('[data-region="status-bar"]')
          ?.querySelectorAll("button") ?? [],
      ).find((button) => button.textContent?.includes("任务")),
    ).toBeUndefined();
  });

  it("deliverables 子页切换：树条目→?tab=deliverables.report；点轨当前入口=子页重置缺省", async () => {
    renderShell("?tab=deliverables");
    await waitFor(() => {
      expect(document.querySelector('[data-region="drafting-tree"]')).not.toBeNull();
    });
    fireEvent.click(
      document.querySelector<HTMLButtonElement>(
        '[data-testid="wp-v4-drafting-report"]',
      ) as HTMLButtonElement,
    );
    await waitFor(() => {
      expect(
        document.querySelector('[data-region="deliverables-report"]'),
      ).not.toBeNull();
    });
    expect(window.location.search).toBe("?tab=deliverables.report");
    // 点轨当前入口（图纸报告）→子页重置缺省 sheets
    fireEvent.click(railButton("deliverables") as HTMLButtonElement);
    await waitFor(() => {
      expect(document.querySelector('[data-region="drafting-tree"]')).not.toBeNull();
    });
    expect(window.location.search).toBe("?tab=deliverables");
  });

  it("顶栏工具区五钮在场（zoneBand 语义迁 topBar——保存/撤销/重做/校验/全项目计算）", () => {
    renderShell();
    const bar = document.querySelector('[data-region="top-bar"]');
    expect(bar).not.toBeNull();
    const labelOf = (testid: string): string =>
      bar?.querySelector(`[data-testid="${testid}"]`)?.textContent ?? "";
    expect(labelOf("wp-v4-save")).toContain("保存");
    expect(labelOf("wp-v4-undo")).toContain("撤销");
    expect(labelOf("wp-v4-redo")).toContain("重做");
    expect(labelOf("wp-v4-validate")).toContain("校验");
    expect(labelOf("wp-v4-run")).toContain("全项目计算");
    // 撤销/重做恒禁用态保持
    expect(
      (bar?.querySelector('[data-testid="wp-v4-undo"]') as HTMLButtonElement)
        ?.disabled,
    ).toBe(true);
    expect(
      (bar?.querySelector('[data-testid="wp-v4-redo"]') as HTMLButtonElement)
        ?.disabled,
    ).toBe(true);
    // 面包屑项目名（useProjectName 单源——未命名回退）
    expect(bar?.querySelector('[data-testid="wp-v4-crumbs"]')?.textContent).toContain(
      "未命名项目",
    );
  });
});
