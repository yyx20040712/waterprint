/**
 * @vitest-environment jsdom
 *
 * v4 连接设置真壳接线测试（B7 收口批 U6——k2 delta 放行条件③「可并入
 * 下一笔」在案：mount 真 ShellV4 三帧断言；数据面替身制式沿
 * parametersZone.test——真壳 prop 链 shellV4→aiZone→设置钮承载手动
 * 入口，AUTH_EVENT 自愈经 settingsSelfHeal 恒挂载层。b2 壳重组批：
 * dockBar→aiZone〔AI 助手入口页〕，zone 切换=导航轨 rail）。
 *
 * 输入:  ShellV4 真件（jsdom 挂载——useProjectId/生成 hook/取数面模块
 *        替身；重子面 stub 零渲染，aiZone/navRail 真件保留=接线链实证
 *        面）+AUTH_EVENT（window 派发）
 * 输出:  断言族三帧：①手动路径：AI 助手页设置钮（wp-v4-open-settings）
 *        →TokenSettingsModal 开（真壳 prop 链 shellV4→aiZone 承载——
 *        标题/密码框在场）②非 AI 入口自愈：切 compare 入口（aiZone
 *        卸载态实证）→dispatch AUTH_EVENT→Modal 开（恒挂载层实证——
 *        监听不随 aiZone 卸载死区）③E3 帧：Modal 关闭动画期（离场
 *        motion 类在场）dispatch AUTH_EVENT→重开（401 压过用户关闭
 *        语义——入场 motion 类翻转证，jsdom 无 transition 事件物理
 *        卸载不可实测）
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AUTH_EVENT } from "../../shared/events";
import { ShellV4 } from "./shellV4";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** localStorage 存根（本环境 jsdom 面无原生方法族——tokenSettings 令牌
 *  回显消费；Map 薄壳足量三函数面）。 */
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
// 重子面 stub（本测面=壳接线+设置 Modal——其余面零渲染；aiZone/navRail
// 真件保留=prop 链/入口切换实证面）
vi.mock("../../features/params/components/AssumptionsPanel", () => ({
  AssumptionsPanel: () => null,
}));
vi.mock("../../features/params/components/ParamForm", () => ({
  ParamForm: () => null,
}));
vi.mock("./thumbnailFlow", () => ({ ThumbnailFlow: () => null }));
vi.mock("./enumerateModal", () => ({ EnumerateModal: () => null }));
vi.mock("./analysisPane", () => ({
  AnalysisPane: () => null,
  StaleBanner: () => null,
}));
vi.mock("./solutionCards", () => ({ SolutionCards: () => null }));
vi.mock("./jointSolutionCards", () => ({ JointSolutionCards: () => null }));
vi.mock("./backfillSection", () => ({ BackfillSection: () => null }));
// compare 数据面替身（帧② 切 compare 入口——loading 态零渲染面）
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
// 生成 hook 替身（aiZone 任务快照+topBar 项目读/存/校验/计算四族——
// 真壳渲染所需取数面全空态）
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

function renderShell() {
  window.history.replaceState(null, "", "/?project=p1&tab=ai");
  return render(
    <QueryClientProvider client={queryClient}>
      <ShellV4 />
    </QueryClientProvider>,
  );
}

/** footer 钮文本定位（antd 两字钮插空格——空白归一比对）。 */
const footerButton = (label: string): HTMLButtonElement | undefined =>
  (Array.from(document.querySelectorAll<HTMLButtonElement>(".ant-modal-footer button"))
    .find((b) => (b.textContent ?? "").replace(/\s/g, "") === label));

/** 离场 motion 在场（Modal 关闭动画期证——jsdom 无 transition 事件，
 * 物理卸载不可实测，ant-zoom-leave 类为关闭态翻转证）。 */
const leaveMotion = () => document.querySelector(".ant-zoom-leave");
/** 入场 motion 在场（重开态翻转证）。 */
const enterMotion = () => document.querySelector(".ant-zoom-enter, .ant-zoom-appear");

beforeEach(() => {
  gate.projectId = "p1";
});
afterEach(cleanup);

describe("连接设置真壳接线（B7 U6——mount 真 ShellV4 三帧；b2 入口链=aiZone）", () => {
  it("帧①手动路径：AI 助手页设置钮→TokenSettingsModal 开（真壳 prop 链 shellV4→aiZone 承载）", async () => {
    renderShell();
    // 真壳链在场证：AI 入口体+设置钮（aiZone AI 窗头行承载）
    await waitFor(() => {
      expect(document.querySelector('[data-region="ai-workspace"]')).not.toBeNull();
    });
    const settingsBtn = document.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-open-settings"]',
    );
    expect(settingsBtn).not.toBeNull();
    // 关闭态起点：Modal 未渲染（antd 关态零 portal 内容）
    expect(document.querySelector(".ant-modal")).toBeNull();
    settingsBtn?.click();
    await waitFor(() => {
      expect(document.querySelector(".ant-modal")).not.toBeNull();
      expect(document.querySelector(".ant-input-password")).not.toBeNull();
    });
    const title = document.querySelector(".ant-modal-title")?.textContent;
    expect(title).toBe("连接设置");
    // 关 Modal（帧②前置：关闭态起点——motion 后隐藏非卸载）
    fireEvent.click(footerButton("关闭") as HTMLButtonElement);
    await waitFor(() => {
      expect(leaveMotion()).not.toBeNull();
    });
  });

  it("帧②非 AI 入口自愈：切 compare 入口（aiZone 卸载态实证）→dispatch AUTH_EVENT→Modal 开（恒挂载层）", async () => {
    renderShell();
    // 切 compare 入口（真导航轨——setNav 单通道）
    fireEvent.click(
      document.querySelector<HTMLButtonElement>('[data-testid="wp-v4-nav-compare"]') as HTMLButtonElement,
    );
    await waitFor(() => {
      expect(document.querySelector('[data-region="compare-matrix"]')).not.toBeNull();
    });
    // aiZone 卸载态实证（AI 入口外设置钮收起——监听死区根因面已上提）
    expect(document.querySelector('[data-testid="wp-v4-open-settings"]')).toBeNull();
    expect(document.querySelector(".ant-modal")).toBeNull();
    // dispatch AUTH_EVENT（customInstance 401 派发面 parity）
    window.dispatchEvent(new Event(AUTH_EVENT));
    await waitFor(() => {
      expect(document.querySelector(".ant-modal")).not.toBeNull();
      expect(document.querySelector(".ant-input-password")).not.toBeNull();
    });
    const title = document.querySelector(".ant-modal-title")?.textContent;
    expect(title).toBe("连接设置");
  });

  it("帧③E3 帧：Modal 关闭动画期 dispatch AUTH_EVENT→重开（401 压过用户关闭语义）", async () => {
    renderShell();
    // 手动开（compare 入口自愈同源 state——AI 入口位）
    await waitFor(() => {
      expect(document.querySelector('[data-region="ai-workspace"]')).not.toBeNull();
    });
    document.querySelector<HTMLButtonElement>('[data-testid="wp-v4-open-settings"]')?.click();
    await waitFor(() => {
      expect(document.querySelector(".ant-modal")).not.toBeNull();
    });
    // 用户关闭：离场 motion 期（动画未完——401 到达时窗）
    fireEvent.click(footerButton("关闭") as HTMLButtonElement);
    await waitFor(() => {
      expect(leaveMotion()).not.toBeNull();
    });
    // 关闭动画期 dispatch AUTH_EVENT→重开（入场 motion 翻转证）
    window.dispatchEvent(new Event(AUTH_EVENT));
    await waitFor(() => {
      expect(enterMotion()).not.toBeNull();
      expect(leaveMotion()).toBeNull();
    });
    await waitFor(() => {
      expect(document.querySelector(".ant-input-password")).not.toBeNull();
    });
    const title = document.querySelector(".ant-modal-title")?.textContent;
    expect(title).toBe("连接设置");
  });

  it("状态条项目名（v2 笔3+R1-N3 截断防护）：未命名回退+hex 退役/title 全名+省略号样式", () => {
    renderShell();
    const bar = document.querySelector(".wp-v4-statusbar");
    expect(bar?.textContent).toContain("项目：未命名项目");
    expect(bar?.textContent).not.toContain("p1"); // hex 前缀不再裸露
    const nameSpan = Array.from(
      bar?.querySelectorAll("span") ?? [],
    ).find((el) => el.textContent?.includes("项目："));
    expect(nameSpan?.getAttribute("title")).toBe("未命名项目"); // 全名悬停
    expect((nameSpan as HTMLElement).style.maxWidth).toBe("200px"); // 省略号截断防护
    expect((nameSpan as HTMLElement).style.textOverflow).toBe("ellipsis");
    cleanup();
    gate.projectId = null;
    renderShell();
    expect(
      document.querySelector(".wp-v4-statusbar")?.textContent,
    ).toContain("项目：未选择");
  });
});
