/**
 * @vitest-environment jsdom
 *
 * 首启运行方式向导 vitest（联机架构第七批 b7 2026-11-19——稿
 * onboarding.html 三选遮罩：桥态分支与选择落地）。
 *
 * 输入:  OnboardingGate（desktopBridge 模块替身受控桥：getConfig 四角色
 *        快照/setNetworkRole 结果受控+window.pywebview 注入态）
 * 输出:  断言五组：①桥缺席=null 渲染（浏览器态诚实降级）②unconfigured
 *        =三卡遮罩在场（三 testid）③单机选择→setNetworkRole
 *        ("standalone")+切换中态 ④客户端选择→第二步连接面板在场
 *        （wp-v4-client-panel）⑤getConfig 失败/已配置角色=不拦壳
 */
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingGate } from "./onboardingGate";
import type { DesktopConfigSnapshot } from "./desktopBridge";

/** 桥替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  snapshot: {
    role: "unconfigured",
    shellOrigin: "http://127.0.0.1:8620",
    engineOrigin: null,
  } as DesktopConfigSnapshot,
  setRoleResult: { ok: true, restartRequired: false },
  setRoleCalls: [] as string[],
}));

vi.mock("./desktopBridge", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./desktopBridge")>();
  return {
    ...actual,
    getDesktopBridge: vi.fn(() =>
      (window as { pywebview?: unknown }).pywebview === undefined
        ? null
        : {
            getConfig: vi.fn(async () => gate.snapshot),
            setNetworkRole: vi.fn(async (role: string) => {
              gate.setRoleCalls.push(role);
              return gate.setRoleResult;
            }),
          },
    ),
  };
});

function injectBridge(): void {
  (window as { pywebview?: unknown }).pywebview = { api: {} };
}

function removeBridge(): void {
  delete (window as { pywebview?: unknown }).pywebview;
}

beforeEach(() => {
  gate.snapshot = {
    role: "unconfigured",
    shellOrigin: "http://127.0.0.1:8620",
    engineOrigin: null,
  };
  gate.setRoleResult = { ok: true, restartRequired: false };
  gate.setRoleCalls = [];
});

afterEach(() => {
  cleanup();
  removeBridge();
});

describe("OnboardingGate 桥态分支", () => {
  it("桥缺席（浏览器态）不渲染遮罩", () => {
    removeBridge();
    const { queryByTestId } = render(<OnboardingGate />);
    expect(queryByTestId("wp-v4-onboarding-overlay")).toBeNull();
  });

  it("getConfig 失败=诚实降级不拦壳", async () => {
    injectBridge();
    const { getDesktopBridge } = await import("./desktopBridge");
    vi.mocked(getDesktopBridge).mockReturnValueOnce({
      getConfig: vi.fn(async () => {
        throw new Error("bridge not ready");
      }),
      setNetworkRole: vi.fn(),
    } as unknown as ReturnType<typeof getDesktopBridge>);
    const { queryByTestId } = render(<OnboardingGate />);
    await waitFor(() => {
      expect(queryByTestId("wp-v4-onboarding-overlay")).toBeNull();
    });
  });

  it.each(["standalone", "server", "client"] as const)(
    "已配置角色 %s=不渲染遮罩",
    async (role) => {
      injectBridge();
      gate.snapshot = {
        role,
        shellOrigin: null,
        engineOrigin: "http://127.0.0.1:8621",
      };
      const { queryByTestId } = render(<OnboardingGate />);
      await waitFor(() => {
        expect(queryByTestId("wp-v4-onboarding-overlay")).toBeNull();
      });
    },
  );
});

describe("OnboardingGate 首启三选", () => {
  it("unconfigured=三卡遮罩在场（稿 onboarding.html 三段）", async () => {
    injectBridge();
    const { getByTestId, findByTestId } = render(<OnboardingGate />);
    await findByTestId("wp-v4-onboarding-overlay");
    for (const role of ["standalone", "server", "client"]) {
      expect(getByTestId(`wp-v4-onboarding-${role}`)).toBeTruthy();
    }
  });

  it("单机选择→setNetworkRole(standalone)+切换中态", async () => {
    injectBridge();
    const { findByTestId, getByText } = render(<OnboardingGate />);
    fireEvent.click(await findByTestId("wp-v4-onboarding-standalone"));
    await waitFor(() => {
      expect(gate.setRoleCalls).toEqual(["standalone"]);
    });
    expect(getByText(/正在切换运行方式/)).toBeTruthy();
  });

  it("客户端选择→第二步连接面板在场（厚客户端配对面）", async () => {
    injectBridge();
    const { findByTestId } = render(<OnboardingGate />);
    fireEvent.click(await findByTestId("wp-v4-onboarding-client"));
    await waitFor(() => {
      expect(gate.setRoleCalls).toEqual(["client"]);
    });
    expect(await findByTestId("wp-v4-client-panel")).toBeTruthy();
  });

  it("切换失败（restartRequired）=持久化提示不进第二步", async () => {
    injectBridge();
    gate.setRoleResult = { ok: false, restartRequired: true };
    const { findByTestId, getByText, queryByTestId } = render(<OnboardingGate />);
    fireEvent.click(await findByTestId("wp-v4-onboarding-server"));
    await waitFor(() => {
      expect(getByText(/重启桌面应用后按新角色运行/)).toBeTruthy();
    });
    expect(queryByTestId("wp-v4-client-panel")).toBeNull();
  });
});
