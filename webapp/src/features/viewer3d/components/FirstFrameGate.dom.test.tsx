/**
 * @vitest-environment jsdom
 *
 * 首帧门活链路 jsdom 常驻用例（2A7 批 2026-10-05 UF-57——P4=甲裁决准入
 * jsdom+@testing-library/react 后，行为级覆盖由门二会话件探针升级为常驻
 * CI 面；探针脚本仍归会话件不入库。既有 FirstFrameGate.test.tsx 纯核/
 * SSR/源文断言面零动）。
 *
 * 输入:  useFirstFrameGate+FirstFrameOverlay/FirstFrameTimeoutPanel（本地
 *        探针组件消费——不渲染 Canvas/@react-three/fiber 面；FirstFrameSignal
 *        薄壳仍归既有源文断言）+@testing-library/react（cleanup 显式——
 *        globals=false 自动 cleanup 不生效）
 * 输出:  活链路六用例：①挂载即 overlay 在场；②act 包裹 signal()→overlay
 *        卸载（signal→subscribe→useSyncExternalStore→重渲染）；③effect
 *        挂计时器（fake timers 限定 setTimeout/clearTimeout——不 fake
 *        rAF/performance 防扰 RTL/antd 内部）advance 满程→超时面板+重试
 *        钮；④signal 先到→advance 满程零 alert（清窗）；⑤enabled=false
 *        零计时器→rerender 翻真→alert 在场（W1 窗起点=scene 就绪）；
 *        ⑥done 后 rerender 换 resetKey→done 归 false、overlay 复现（R1 F1）
 */
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  FIRST_FRAME_TIMEOUT_MS,
  FirstFrameOverlay,
  FirstFrameTimeoutPanel,
  useFirstFrameGate,
} from "./FirstFrameGate";

/** signal 出口（探针渲染期同步——act 内直调，经真实订阅链路触发重渲染）。 */
let fireSignal: () => void = () => {};

/** 活链路探针（Scene 消费形复刻：!done→overlay 在场；timedOut→超时面板
 *  替代——本地定义，不渲染 Canvas 面）。 */
function GateProbe({ enabled = true, resetKey }: { enabled?: boolean; resetKey?: unknown }) {
  const [done, timedOut, signal] = useFirstFrameGate(resetKey, enabled);
  fireSignal = signal;
  return (
    <div>
      {!done ? <FirstFrameOverlay /> : null}
      {timedOut ? <FirstFrameTimeoutPanel onRetry={() => {}} /> : null}
    </div>
  );
}

describe("FirstFrameGate 活链路（UF-57 2A7 批——real timers 轨）", () => {
  afterEach(cleanup);

  it("①挂载即 overlay 在场（getByRole status+「正在构建三维场景…」）", () => {
    render(<GateProbe />);
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByText("正在构建三维场景…")).toBeTruthy();
  });

  it("②act 包裹 signal() → overlay 卸载（signal→订阅→useSyncExternalStore→重渲染活链路）", () => {
    render(<GateProbe />);
    expect(screen.getByRole("status")).toBeTruthy();
    act(() => {
      fireSignal();
    });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("⑥done 后 rerender 换 resetKey → done 归 false、overlay 复现（R1 F1 复位面活链路）", () => {
    const view = render(<GateProbe resetKey="proj-gate#0" />);
    act(() => {
      fireSignal();
    });
    expect(screen.queryByRole("status")).toBeNull();
    view.rerender(<GateProbe resetKey="proj-gate#1" />);
    expect(screen.getByRole("status")).toBeTruthy();
  });
});

describe("FirstFrameGate 超时窗活链路（fake timers 限定 setTimeout/clearTimeout）", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  });
  afterEach(() => {
    vi.useRealTimers();
    cleanup();
  });

  it("③挂载即计时器已挂：advance 满程（act 内）→ getByRole alert+「重试」钮在场（effect 挂计时器活链路）", () => {
    render(<GateProbe />);
    expect(screen.queryByRole("alert")).toBeNull();
    act(() => {
      vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    });
    expect(screen.getByRole("alert")).toBeTruthy();
    // antd Button 两字中文插空（教训 24 先例）：「重试」渲染为「重 试」
    expect(screen.getByRole("button", { name: /重\s*试/ })).toBeTruthy();
  });

  it("④signal 先到 → advance 满程 → queryByRole alert===null（清窗活链路）", () => {
    render(<GateProbe />);
    act(() => {
      fireSignal();
    });
    expect(screen.queryByRole("status")).toBeNull();
    act(() => {
      vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("⑤enabled=false 挂载→advance→无 alert；rerender enabled=true→advance→alert 在场（W1 窗起点=scene 就绪）", () => {
    const view = render(<GateProbe enabled={false} />);
    act(() => {
      vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    });
    expect(screen.queryByRole("alert")).toBeNull();
    view.rerender(<GateProbe enabled={true} />);
    act(() => {
      vi.advanceTimersByTime(FIRST_FRAME_TIMEOUT_MS);
    });
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
