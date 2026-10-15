/**
 * @vitest-environment jsdom
 *
 * v4 项目区测试（v3-20261015 D4——信息专业度批：操作列删除流+名称列未命名
 * 回退。制式沿 reportZone.test——vi.mock 族+QueryClientProvider 真客户端
 * 〔invalidate 间谍面〕；antd Modal.confirm 帝国式弹层入 document.body——
 * Modal.destroyAll afterEach 收口）。
 *
 * 输入:  ProjectsZone（项目列表/复制/重命名/删除生成 hook 模块替身+
 *        useProjectId 替身〔setter 间谍〕+CreateProjectModal 替身）
 * 输出:  断言族：①操作列删除钮在场（danger 形+testid）②名称列无名回退
 *        =「未命名项目 (id 前 8)」③删除流：点删除→确认弹窗（标题「删除
 *        项目」+内容含项目名/未命名回退）→确认→delete mutate 载荷
 *        ④onSuccess：删当前项目→列表 invalidate+setProjectId(null)；删他
 *        项目→setter 不动 ⑤onError：错误提示面（白名单微文案）
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Modal } from "antd";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectsZone } from "./projectsZone";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}
// antd Table/Grid 断点观察面（FdInlinePanel.test 先例存根）
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
  projectId: "ab12cd34ef56" as string | null,
  setProjectId: vi.fn(),
  projects: [] as Array<{ project_id: string; name: string | null; view_timestamp: string }>,
  deleteMutate: vi.fn(),
  deleteConfig: {} as {
    onSuccess?: (outcome: unknown, vars: { projectId: string }) => void;
    onError?: (error: unknown) => void;
  },
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId, gate.setProjectId],
}));
vi.mock("../../shared/api/generated/projects/projects", () => ({
  getListProjectsApiProjectsGetQueryKey: () => ["/api/projects"],
  useListProjectsApiProjectsGet: () => ({
    data: gate.projects,
    isError: false,
    error: null,
    isLoading: false,
  }),
  useCopyProjectApiProjectsProjectIdCopyPost: () => ({
    mutate: vi.fn(),
    isPending: false,
    variables: null,
  }),
  useRenameProjectApiProjectsProjectIdRenamePost: () => ({
    mutate: vi.fn(),
    isPending: false,
    variables: null,
    reset: vi.fn(),
  }),
  useDeleteProjectApiProjectsProjectIdDelete: (options?: {
    mutation?: {
      onSuccess?: (outcome: unknown, vars: { projectId: string }) => void;
      onError?: (error: unknown) => void;
    };
  }) => {
    // 回调挂 hook 配置（组件经 mutation 选项注入——测试侧捕获后模拟服务端回执）
    gate.deleteConfig = options?.mutation ?? {};
    return { mutate: gate.deleteMutate, isPending: false, variables: null };
  },
}));
vi.mock("../createProjectModal", () => ({
  CreateProjectModal: () => null,
}));

/** 帝国式弹层/消息 DOM 均落 document.body——随测收口（destroyAll 动画期
 *  不摘 DOM——jsdom 无 transition 事件，强摘节点兜底防跨测残留）。 */
afterEach(() => {
  cleanup();
  Modal.destroyAll();
  document
    .querySelectorAll(".ant-modal-confirm, .ant-modal-root, .ant-message")
    .forEach((node) => node.remove());
});

beforeEach(() => {
  gate.projectId = "ab12cd34ef56";
  gate.setProjectId.mockClear();
  gate.projects = [
    { project_id: "ab12cd34ef56", name: "城南污水处理厂", view_timestamp: "2026-10-14T10:00:00" },
    { project_id: "cd9988776655", name: null, view_timestamp: "" },
  ];
  gate.deleteMutate.mockClear();
  gate.deleteConfig = {};
});

function renderZone() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <ProjectsZone onOpen={() => {}} />
    </QueryClientProvider>,
  );
  return { ...utils, invalidateSpy };
}

/** 末枚确认弹窗（新 confirm 追加 body 末——取末枚防陈旧残留）。 */
function lastConfirm(): Element | null {
  const all = document.querySelectorAll(".ant-modal-confirm");
  return all.length > 0 ? all[all.length - 1] as Element : null;
}

/** 确认弹窗主钮（antd Modal.confirm 异步挂载——waitFor 后取末枚 primary）。 */
async function confirmAppeared(): Promise<HTMLElement> {
  return waitFor(() => {
    const oks = document.querySelectorAll<HTMLButtonElement>(
      ".ant-modal-confirm-btns .ant-btn-primary",
    );
    expect(oks.length).toBeGreaterThan(0);
    return oks[oks.length - 1] as HTMLElement;
  });
}

describe("项目区·操作列删除钮（V3 D4）", () => {
  it("删除钮在场：danger 形+testid wp-v4-proj-delete-<id8>", () => {
    const { container } = renderZone();
    const del = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-proj-delete-ab12cd34"]',
    );
    expect(del).not.toBeNull();
    expect(del?.classList.contains("ant-btn-dangerous")).toBe(true);
    expect(del?.textContent).toContain("删除");
  });

  it("名称列无名回退=「未命名项目 (id 前 8)」（projectOptionLabel 单源）", () => {
    const { container } = renderZone();
    expect(container.textContent).toContain("未命名项目 (cd998877)");
  });
});

describe("项目区·删除流（确认弹窗→mutate→回执）", () => {
  it("点删除→确认弹窗（标题「删除项目」+内容含项目名）→确认=delete 载荷", async () => {
    const { container } = renderZone();
    const del = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-proj-delete-ab12cd34"]',
    );
    fireEvent.click(del as HTMLButtonElement);
    // 帝国式弹层入 document.body（antd 异步挂载——waitFor 取末枚）
    const modal = await waitFor(() => {
      const found = lastConfirm();
      expect(found).not.toBeNull();
      return found;
    });
    expect(modal?.textContent).toContain("删除项目");
    expect(modal?.textContent).toContain("城南污水处理厂");
    // 确认前零突变（危险动作显式确认）
    expect(gate.deleteMutate).not.toHaveBeenCalled();
    fireEvent.click(await confirmAppeared());
    await waitFor(() => expect(gate.deleteMutate).toHaveBeenCalledTimes(1));
    expect(gate.deleteMutate.mock.calls[0]?.[0]).toEqual({ projectId: "ab12cd34ef56" });
  });

  it("无名项目确认弹窗内容=未命名回退（不裸 hex）", async () => {
    const { container } = renderZone();
    const del = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-proj-delete-cd998877"]',
    );
    fireEvent.click(del as HTMLButtonElement);
    const modal = await waitFor(() => {
      const found = lastConfirm();
      expect(found).not.toBeNull();
      return found;
    });
    expect(modal?.textContent).toContain("未命名项目 (cd998877)");
  });

  it("onSuccess：删当前项目→列表 invalidate+setProjectId(null)（留本区无项目态）", async () => {
    const { container, invalidateSpy } = renderZone();
    const del = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-proj-delete-ab12cd34"]',
    );
    fireEvent.click(del as HTMLButtonElement);
    fireEvent.click(await confirmAppeared());
    await waitFor(() => expect(gate.deleteMutate).toHaveBeenCalledTimes(1));
    // 服务端成功回执（hook 配置注入的 onSuccess）
    gate.deleteConfig.onSuccess?.(undefined, { projectId: "ab12cd34ef56" });
    await waitFor(() => expect(invalidateSpy).toHaveBeenCalled());
    expect(gate.setProjectId).toHaveBeenCalledWith(null);
    await waitFor(() =>
      expect(document.body.textContent).toContain("项目已删除"),
    );
  });

  it("onSuccess：删他项目→setProjectId 不动（当前选择保持）", async () => {
    const { container } = renderZone();
    const del = container.querySelector<HTMLButtonElement>(
      '[data-testid^="wp-v4-proj-delete-cd99"]',
    );
    fireEvent.click(del as HTMLButtonElement);
    fireEvent.click(await confirmAppeared());
    await waitFor(() => expect(gate.deleteMutate).toHaveBeenCalledTimes(1));
    gate.deleteConfig.onSuccess?.(undefined, { projectId: "cd9988776655" });
    expect(gate.setProjectId).not.toHaveBeenCalled();
  });

  it("onError：错误提示面（白名单微文案——删除失败前缀+原文）", async () => {
    const { container } = renderZone();
    const del = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-proj-delete-ab12cd34"]',
    );
    fireEvent.click(del as HTMLButtonElement);
    fireEvent.click(await confirmAppeared());
    await waitFor(() => expect(gate.deleteMutate).toHaveBeenCalledTimes(1));
    gate.deleteConfig.onError?.(new Error("项目文件已被移动"));
    await waitFor(() =>
      expect(document.body.textContent).toContain("删除失败：项目文件已被移动"),
    );
  });
});
