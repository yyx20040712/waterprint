/**
 * @vitest-environment jsdom
 *
 * v4 壳首启 gate 接线 vitest（e2e-fix-r3 批 2026-11-19 F9：壳级——
 * gate 命中/probing 相整壳换页=壳面不挂载+后台 API 查询零发出；
 * 制式沿 shellNav.test——mount 真 ShellV4，数据面替身+桥模块替身）。
 *
 * 输入:  ShellV4 真件（onboardingGate/desktopBridge 模块替身受控三相；
 *        fetch 全局 stub 计数——查询零发出断言面；各入口重子面 stub
 *        零渲染沿 shellNav 制式）
 * 输出:  断言三组：①unconfigured=独立三选页在场+壳面〔状态条/顶栏/
 *        导航轨〕缺席+fetch 零调用（F9-②查询噪声根除）②probing=探测
 *        占位在场+fetch 零调用 ③浏览器态（桥缺席）=壳面正常渲染
 *        （回归锚——gate 不误伤常规路径）
 */
import { cleanup, render, waitFor } from "@testing-library/react";
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

/** localStorage 存根（jsdom 面无原生方法族——侧栏宽度/token 消费）。 */
const storageBack = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storageBack.get(key) ?? null,
  setItem: (key: string, value: string) => void storageBack.set(key, value),
  removeItem: (key: string) => void storageBack.delete(key),
});

/** fetch 计数 stub（永不 resolve——查询零发出断言面；无未处理拒绝噪声）。 */
const fetchStub = vi.fn(() => new Promise<Response>(() => {}));
vi.stubGlobal("fetch", fetchStub);

/** 桥替身受控位（vi.hoisted——三相受控；pendingConfig=true=getConfig 永
 *  挂起〔钉 probing 相〕，false=按 phase 快照解析）。 */
const bridgeGate = vi.hoisted(() => ({
  phase: "pass" as "pass" | "unconfigured",
  pendingConfig: false,
}));

vi.mock("../desktopBridge", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../desktopBridge")>();
  return {
    ...actual,
    getDesktopBridge: vi.fn(() =>
      bridgeGate.phase === "pass"
        ? null
        : {
            getConfig: vi.fn(
              () =>
                new Promise((resolve) => {
                  if (!bridgeGate.pendingConfig) {
                    resolve({
                      role: bridgeGate.phase,
                      shellOrigin: "http://127.0.0.1:8620",
                      engineOrigin: null,
                    });
                  }
                  // pendingConfig=true：永不解析——探测相钉住
                }),
            ),
            setNetworkRole: vi.fn(async () => ({ ok: true, restartRequired: false })),
          },
    ),
  };
});

// —— 数据面/重子面替身（沿 shellNav.test 制式——gate 断言不触数据面，
//    pass 回归锚渲染需要） ——
vi.mock("../useProjectId", () => ({
  useProjectId: () => ["p1"],
}));
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
vi.mock("./projectsZone", () => ({
  ProjectsZone: () => <section data-testid="wp-v4-projects-stub" />,
}));
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
    data: [],
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
vi.mock("../../shared/api/generated/meta/meta", () => ({
  useGetRuntimeApiRuntimeGet: () => ({
    data: undefined,
    isError: false,
    error: null,
  }),
  useGetMetaApiMetaGet: () => ({
    data: undefined,
    isPending: false,
    isError: false,
    error: null,
  }),
}));
vi.mock("../siteplanPane", () => ({
  SiteplanPane: () => null,
}));
vi.mock("../../features/compare/api/useCompareQuery", () => ({
  useCompareQuery: () => ({ data: undefined, isError: false }),
}));
vi.mock("../../features/ai_chat/api/useAiChat", () => ({
  useChatHistory: () => ({ data: undefined, isError: false, error: null }),
  useSendChatMessage: () => ({ mutate: () => {}, isPending: false }),
  useChatSessions: () => ({ data: [], isPending: false, isError: false }),
}));
vi.mock("../../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: () => null,
}));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => ({
    data: undefined,
    isError: false,
    error: null,
    isLoading: true,
  }),
  useRunCalculationApiCalcRunPost: () => ({
    mutate: () => {},
    mutateAsync: () => Promise.resolve({ task_id: "t-x" }),
    isPending: false,
    isError: false,
    error: null,
    reset: () => {},
  }),
}));
vi.mock("../../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => ({
    data: undefined,
    isError: false,
    error: null,
    isLoading: true,
  }),
  useSaveProjectApiProjectsProjectIdPut: () => ({
    mutate: () => {},
    mutateAsync: () => Promise.resolve({}),
    isPending: false,
    isError: false,
    error: null,
  }),
  useValidateProjectApiProjectsProjectIdValidatePost: () => ({
    mutate: () => {},
    isPending: false,
    isError: false,
    error: null,
    reset: () => {},
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderShell(): ReturnType<typeof render> {
  window.history.replaceState(null, "", "/");
  return render(
    <QueryClientProvider client={queryClient}>
      <ShellV4 />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchStub.mockClear();
  bridgeGate.phase = "pass";
  bridgeGate.pendingConfig = false;
});
afterEach(cleanup);

describe("壳首启 gate 接线（F9——换页与查询抑制）", () => {
  it("unconfigured=独立三选页在场+壳面缺席+fetch 零调用", async () => {
    bridgeGate.phase = "unconfigured";
    const { getByTestId, container } = renderShell();
    await waitFor(() => {
      expect(getByTestId("wp-v4-onboarding-page")).toBeTruthy();
    });
    // 壳面缺席：状态条/顶栏/导航轨 region 均不在场
    expect(
      container.querySelector('[data-region="status-bar"]'),
    ).toBeNull();
    expect(container.querySelector('[data-testid="wp-v4-nav"]')).toBeNull();
    expect(getByTestId("wp-v4-bootstrap-status").textContent).toContain(
      "运行方式：未配置",
    );
    // F9-②：gate 期后台查询零发出（projects/runtime/units 全静默）
    expect(fetchStub).toHaveBeenCalledTimes(0);
  });

  it("probing=探测占位在场+壳面缺席+fetch 零调用（探测期不闪挂壳）", async () => {
    bridgeGate.phase = "unconfigured";
    bridgeGate.pendingConfig = true; // getConfig 永挂起——探测相钉住
    const { getByTestId, container } = renderShell();
    await waitFor(() => {
      expect(getByTestId("wp-v4-bootstrap-probe")).toBeTruthy();
    });
    expect(
      container.querySelector('[data-region="status-bar"]'),
    ).toBeNull();
    expect(fetchStub).toHaveBeenCalledTimes(0);
  });

  it("浏览器态（桥缺席）=壳面正常渲染（回归锚——gate 不误伤）", async () => {
    bridgeGate.phase = "pass";
    const { container } = renderShell();
    await waitFor(() => {
      expect(
        container.querySelector('[data-region="status-bar"]'),
      ).not.toBeNull();
    });
    expect(container.querySelector('[data-testid="wp-v4-onboarding-page"]')).toBeNull();
  });
});
