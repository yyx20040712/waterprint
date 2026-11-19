/**
 * @vitest-environment jsdom
 *
 * v4 项目区客户端模式四态 vitest（联机架构第六批 2026-11-19——稿
 * workbench-remote.html 远程项目列表态：在线/离线/token 失效/版本不匹配）。
 *
 * 输入:  ProjectsZone（生成 projects hook 模块替身+真 clientConnectionStore
 *        〔setState 控 phase/remoteBase/mismatch〕+QueryClient 真客户端
 *        〔invalidate 间谍面〕）
 * 输出:  断言五组：①本地态零变（本地项目徽标+表——回归锚）②online：
 *        远程徽标+说明行+行级「远程 @ 主机」徽标+远程搜索占位 ③offline：
 *        态卡+重试钮→invalidate ④token_invalid：态卡+更新 token 钮→
 *        onOpenRuntimeSettings ⑤version_mismatch：态卡+mismatch 双方值
 *        并陈+表格缺席（不回退本地项目）
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Modal } from "antd";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectsZone } from "./projectsZone";
import { useClientConnectionStore } from "../clientConnectionStore";

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
  projects: [
    { project_id: "ab12cd34ef56", name: "城南污水处理厂", view_timestamp: "" },
  ],
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => ["ab12cd34ef56", vi.fn()],
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
  useDeleteProjectApiProjectsProjectIdDelete: () => ({
    mutate: vi.fn(),
    isPending: false,
    variables: null,
  }),
}));

/** 断开态重置（phase=local——各用例独立控态）。 */
function setPhase(override: {
  phase: "connecting" | "online" | "offline" | "token_invalid" | "version_mismatch";
  mismatch?: { kind: "api" | "data"; expected: string; actual: string } | null;
}): void {
  useClientConnectionStore.setState({
    remoteBase: "http://127.0.0.1:8100",
    serverMeta: null,
    mismatch: null,
    ...override,
  });
}

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderZone(onOpenRuntimeSettings = vi.fn()): void {
  render(
    <QueryClientProvider client={queryClient}>
      <ProjectsZone onOpen={() => {}} onOpenRuntimeSettings={onOpenRuntimeSettings} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  useClientConnectionStore.setState({
    phase: "local",
    remoteBase: null,
    serverMeta: null,
    mismatch: null,
  });
});

afterEach(async () => {
  cleanup();
  Modal.destroyAll();
  await new Promise((resolve) => setTimeout(resolve, 400));
});

describe("v4 项目区客户端模式四态（联机第六批）", () => {
  it("本地态零变：本地项目徽标+表在场（回归锚）", () => {
    renderZone();
    expect(document.body.textContent).toContain("本地项目");
    expect(
      document.querySelector('[data-testid="wp-v4-proj-table"]'),
    ).not.toBeNull();
    expect(
      document.querySelector('[data-testid="wp-v4-remote-badge"]'),
    ).toBeNull();
  });

  it("online：远程徽标+说明行+行级远程来源徽标+远程搜索占位", () => {
    setPhase({ phase: "online" });
    renderZone();
    expect(
      document.querySelector('[data-testid="wp-v4-remote-badge"]')?.textContent,
    ).toContain("远程项目 · 客户端 · 在线");
    expect(
      document.querySelector('[data-testid="wp-v4-remote-notice"]')?.textContent,
    ).toContain("只显示 127.0.0.1 的项目");
    expect(document.body.textContent).toContain("远程 @ 127.0.0.1");
    const search = document.querySelector(
      '[data-testid="wp-v4-proj-search"]',
    ) as HTMLInputElement | null;
    expect(search?.getAttribute("placeholder")).toBe("搜索所连服务器的项目");
    expect(
      document.querySelector('[data-testid="wp-v4-remote-state"]'),
    ).toBeNull();
  });

  it("offline：态卡+重试钮→invalidate（不展示旧列表）", () => {
    setPhase({ phase: "offline" });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    renderZone();
    expect(
      document.querySelector('[data-testid="wp-v4-remote-state"]')?.textContent,
    ).toContain("无法读取远程项目");
    expect(
      document.querySelector('[data-testid="wp-v4-proj-table"]'),
    ).toBeNull();
    fireEvent.click(
      document.querySelector(
        '[data-testid="wp-v4-remote-retry"]',
      ) as HTMLElement,
    );
    expect(invalidateSpy).toHaveBeenCalled();
  });

  it("token_invalid：态卡+更新 token 钮→onOpenRuntimeSettings", () => {
    setPhase({ phase: "token_invalid" });
    const onOpenRuntimeSettings = vi.fn();
    renderZone(onOpenRuntimeSettings);
    expect(
      document.querySelector('[data-testid="wp-v4-remote-state"]')?.textContent,
    ).toContain("配对凭据需要更新");
    fireEvent.click(
      document.querySelector(
        '[data-testid="wp-v4-remote-update-token"]',
      ) as HTMLElement,
    );
    expect(onOpenRuntimeSettings).toHaveBeenCalled();
  });

  it("version_mismatch：态卡双方版本并陈+表格缺席（不回退本地项目）", () => {
    setPhase({
      phase: "version_mismatch",
      mismatch: { kind: "data", expected: "data@1", actual: "data@2" },
    });
    renderZone();
    const card = document.querySelector(
      '[data-testid="wp-v4-remote-state"]',
    );
    expect(card?.textContent).toContain("远程契约需要对齐");
    expect(card?.textContent).toContain("data@1");
    expect(card?.textContent).toContain("data@2");
    expect(
      document.querySelector('[data-testid="wp-v4-proj-table"]'),
    ).toBeNull();
    expect(
      document.querySelector('[data-testid="wp-v4-remote-handshake-detail"]'),
    ).not.toBeNull();
  });
});
