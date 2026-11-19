/**
 * @vitest-environment jsdom
 *
 * 首启运行方式向导 vitest（联机架构第七批 b7 2026-11-19；e2e-fix-r3 批
 * 2026-11-19 独立页形态重制——稿 onboarding.html 整页：三相探测+三选页
 * +未配置中性状态行）。
 *
 * 输入:  useBootstrapGate/BootstrapProbePane/OnboardingGate
 *        （desktopBridge 模块替身受控桥：getConfig 四角色快照/
 *        setNetworkRole 结果受控+window.pywebview 注入态）
 * 输出:  断言五组：①三相：桥缺席=getDefault pass/unconfigured=换页/
 *        已配置三角色+getConfig 失败=pass（诚实降级）②unconfigured=
 *        独立三选页在场（三 testid+响应式栅格容器）③页内状态行
 *        「运行方式：未配置」中性呈现——全页不含「已连接」（F9-①）
 *        ④单机选择→setNetworkRole("standalone")+切换中态；客户端选择
 *        →第二步连接面板在场 ⑤切换失败（restartRequired）=持久化提示
 */
import { cleanup, fireEvent, render, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  BootstrapProbePane,
  OnboardingGate,
  useBootstrapGate,
} from "./onboardingGate";
import type { DesktopConfigSnapshot } from "./desktopBridge";

/** 桥替身受控位（vi.hoisted——mock 工厂闭包同源读写；configThrows=
 * getConfig 恒 throw 开关——phase 更触发重渲染后组件体重取桥，once 形
 * mock 会被第二次调用消耗，受控 flag 无此竞态）。 */
const gate = vi.hoisted(() => ({
  snapshot: {
    role: "unconfigured",
    shellOrigin: "http://127.0.0.1:8620",
    engineOrigin: null,
  } as DesktopConfigSnapshot,
  setRoleResult: { ok: true, restartRequired: false },
  setRoleCalls: [] as string[],
  configThrows: false,
}));

vi.mock("./desktopBridge", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./desktopBridge")>();
  return {
    ...actual,
    getDesktopBridge: vi.fn(() =>
      (window as { pywebview?: unknown }).pywebview === undefined
        ? null
        : {
            getConfig: vi.fn(async () => {
              if (gate.configThrows) {
                throw new Error("bridge not ready");
              }
              return gate.snapshot;
            }),
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
  gate.configThrows = false;
});
afterEach(() => {
  cleanup();
  removeBridge();
});

describe("useBootstrapGate 三相探测（e2e-fix-r3——壳接线单源）", () => {
  it("桥缺席（浏览器态）=pass，不触发探测", () => {
    removeBridge();
    const { result } = renderHook(() => useBootstrapGate());
    expect(result.current).toBe("pass");
  });

  it("桥在场初值=probing，getConfig 返回 unconfigured=换页相", async () => {
    injectBridge();
    const { result } = renderHook(() => useBootstrapGate());
    expect(result.current).toBe("probing");
    await waitFor(() => {
      expect(result.current).toBe("unconfigured");
    });
  });

  it.each(["standalone", "server", "client"] as const)(
    "已配置角色 %s=pass（不拦壳）",
    async (role) => {
      injectBridge();
      gate.snapshot = {
        role,
        shellOrigin: null,
        engineOrigin: "http://127.0.0.1:8621",
      };
      const { result } = renderHook(() => useBootstrapGate());
      await waitFor(() => {
        expect(result.current).toBe("pass");
      });
    },
  );

  it("getConfig 失败=pass（桥协议异常诚实降级不拦壳）", async () => {
    injectBridge();
    gate.configThrows = true;
    const { result } = renderHook(() => useBootstrapGate());
    await waitFor(() => {
      expect(result.current).toBe("pass");
    });
  });

  it("探测占位页=中性确认文案（壳挂载前的 gate 面）", () => {
    const { getByTestId } = render(<BootstrapProbePane />);
    expect(getByTestId("wp-v4-bootstrap-probe").textContent).toContain(
      "正在确认运行方式",
    );
  });
});

describe("OnboardingGate 独立三选页（unconfigured 相呈现）", () => {
  function renderGate() {
    injectBridge();
    return render(<OnboardingGate />);
  }

  it("unconfigured=独立页+三卡在场（稿 onboarding.html 三段）", () => {
    const { getByTestId } = renderGate();
    const page = getByTestId("wp-v4-onboarding-page");
    expect(page).toBeTruthy();
    for (const role of ["standalone", "server", "client"]) {
      expect(getByTestId(`wp-v4-onboarding-${role}`)).toBeTruthy();
    }
    // 不透明整页背景轴（F9-④：盖住壳，无透明遮罩露底）
    expect(page.style.background).toContain("var(--wp-bg-page)");
  });

  it("页内状态行=「运行方式：未配置」中性态，全页无「已连接」虚报（F9-①）", () => {
    const { getByTestId, container } = renderGate();
    expect(getByTestId("wp-v4-bootstrap-status").textContent).toContain(
      "运行方式：未配置",
    );
    expect(container.textContent).not.toContain("已连接");
  });

  it("单机选择→setNetworkRole(standalone)+切换中态", async () => {
    const { findByTestId, getByText } = renderGate();
    fireEvent.click(await findByTestId("wp-v4-onboarding-standalone"));
    await waitFor(() => {
      expect(gate.setRoleCalls).toEqual(["standalone"]);
    });
    expect(getByText(/正在切换运行方式/)).toBeTruthy();
  });

  it("客户端选择→第二步连接面板在场（厚客户端配对面）", async () => {
    const { findByTestId } = renderGate();
    fireEvent.click(await findByTestId("wp-v4-onboarding-client"));
    await waitFor(() => {
      expect(gate.setRoleCalls).toEqual(["client"]);
    });
    expect(await findByTestId("wp-v4-client-panel")).toBeTruthy();
  });

  it("切换失败（restartRequired）=持久化提示不进第二步", async () => {
    gate.setRoleResult = { ok: false, restartRequired: true };
    const { findByTestId, getByText, queryByTestId } = renderGate();
    fireEvent.click(await findByTestId("wp-v4-onboarding-server"));
    await waitFor(() => {
      expect(getByText(/重启桌面应用后按新角色运行/)).toBeTruthy();
    });
    expect(queryByTestId("wp-v4-client-panel")).toBeNull();
  });
});
