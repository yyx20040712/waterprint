/**
 * @vitest-environment jsdom
 *
 * v4 连接设置真壳接线测试（B7 收口批 U6——k2 delta 放行条件③「可并入
 * 下一笔」在案：mount 真 ShellV4 三帧断言；数据面替身制式沿
 * designZoneJointEntry.test——真壳 prop 链 shellV4→designZone→dockBar
 * 承载手动入口，AUTH_EVENT 自愈经 settingsSelfHeal 恒挂载层）。
 *
 * 输入:  ShellV4 真件（jsdom 挂载——useProjectId/生成 hook/取数面模块
 *        替身；designZone 重子面 stub 零渲染，dockBar/zoneBand 真件
 *        保留=接线链实证面）+AUTH_EVENT（window 派发）
 * 输出:  断言族三帧：①手动路径：dockBar 设置钮（wp-v4-open-settings）
 *        →TokenSettingsModal 开（真壳 prop 链 shellV4→designZone→
 *        dockBar 承载——标题/密码框在场）②非 design 区自愈：切
 *        network 区（dock 卸载态实证）→dispatch AUTH_EVENT→Modal 开
 *        （恒挂载层实证——监听不随 dockBar 卸载死区）③E3 帧：Modal
 *        关闭动画期（离场 motion 类在场）dispatch AUTH_EVENT→重开
 *        （401 压过用户关闭语义——入场 motion 类翻转证，jsdom 无
 *        transition 事件物理卸载不可实测，同 designZoneJointEntry 口径）
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
 *  回显消费；Map 薄壳足量三函数面，沿 designZoneJointEntry.test 先例）。 */
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
// designZone 重子面 stub（本测面=壳接线+设置 Modal——其余面零渲染；
// dockBar/zoneBand 真件保留=prop 链/zone 切换实证面）
vi.mock("../../features/params/components/AssumptionsPanel", () => ({
  AssumptionsPanel: () => null,
}));
vi.mock("../../features/params/components/ParamForm", () => ({
  ParamForm: () => null,
}));
vi.mock("./thumbnailFlow", () => ({ ThumbnailFlow: () => null }));
vi.mock("./enumerateModal", () => ({ EnumerateModal: () => null }));
vi.mock("./analysisPane", () => ({ AnalysisPane: () => null }));
vi.mock("./solutionCards", () => ({ SolutionCards: () => null }));
vi.mock("./jointSolutionCards", () => ({ JointSolutionCards: () => null }));
vi.mock("./backfillSection", () => ({ BackfillSection: () => null }));
// dockBar 取数面替身（dockBar.test 同款——AiDockWindow 会话/任务条）
vi.mock("../../features/ai_chat/api/useAiChat", () => ({
  useChatHistory: () => ({ data: undefined, isError: false, error: null }),
  useSendChatMessage: () => ({ mutate: () => {}, isPending: false }),
}));
vi.mock("../../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: () => null,
}));
vi.mock("../../features/aiconnect/api/useAiConnection", () => ({
  useAiConnection: () => ({
    statusQuery: { data: undefined, isLoading: true, isError: false, error: null },
    setupMutation: { mutate: () => {}, isPending: false, isError: false, error: null, reset: () => {} },
  }),
}));
vi.mock("../../features/aiconnect/api/useAiConfig", () => ({
  useAiConfig: () => ({
    configQuery: { data: undefined, isLoading: true, isError: false, error: null },
    saveMutation: { mutate: () => {}, isPending: false, isError: false, error: null },
  }),
}));
// 生成 hook 替身（dockBar 任务快照+zoneBand 项目读/存/校验/计算四族——
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
    isPending: false, isError: false, error: null, reset: () => {},
  }),
  useValidateProjectApiProjectsProjectIdValidatePost: () => ({
    mutate: () => {}, isPending: false, isError: false, error: null, reset: () => {},
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderShell() {
  window.history.replaceState(null, "", "/?ia=v4&project=p1&tab=design");
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
 *  物理卸载不可实测，ant-zoom-leave 类为关闭态翻转证）。 */
const leaveMotion = () => document.querySelector(".ant-zoom-leave");
/** 入场 motion 在场（重开态翻转证）。 */
const enterMotion = () => document.querySelector(".ant-zoom-enter, .ant-zoom-appear");

beforeEach(() => {
  gate.projectId = "p1";
});
afterEach(cleanup);

describe("连接设置真壳接线（B7 U6——mount 真 ShellV4 三帧）", () => {
  it("帧①手动路径：dockBar 设置钮→TokenSettingsModal 开（真壳 prop 链 shellV4→designZone→dockBar 承载）", async () => {
    renderShell();
    // 真壳链在场证：zone-band+dock（design 区常驻）+设置钮（dockBar 承载）
    expect(document.querySelector('[data-region="zone-band"]')).not.toBeNull();
    expect(document.querySelector('[data-testid="wp-v4-dock"]')).not.toBeNull();
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

  it("帧②非 design 区自愈：切 network 区（dock 卸载态实证）→dispatch AUTH_EVENT→Modal 开（恒挂载层）", async () => {
    renderShell();
    // 切 network 区（真 zoneBand 页签——setZone 单通道）
    fireEvent.click(
      document.querySelector<HTMLButtonElement>('[data-testid="wp-v4-zone-network"]') as HTMLButtonElement,
    );
    await waitFor(() => {
      expect(document.querySelector('[data-region="network-placeholder"]')).not.toBeNull();
    });
    // dock 卸载态实证（design 区外 dock 收起——监听死区根因面已上提）
    expect(document.querySelector('[data-testid="wp-v4-dock"]')).toBeNull();
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
    // 手动开（网络区自愈同源 state——design 区入口位）
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
});
