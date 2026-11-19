/**
 * @vitest-environment jsdom
 *
 * 任务终态分析面刷新 hook 测试（F1 业务缺陷批 2026-11-19——f1-triage
 * 定责的失效时机缺口：提交时刻失效拉回旧轮值后终态前无人二次点火）。
 *
 * 输入:  useTaskTerminalFaceRefresh（useTaskFeed 模块替身——终态回调
 *        受控位透出）+真 QueryClient（预置分析面四域缓存）
 * 输出:  断言族：①终态 done→unit-results/compare/trust/validation 四域
 *        isInvalidated（本项目域）②他项目键不误伤（predicate 域限定）
 *        ③终态 failed→分析面不失效（无新结果不空转 refetch）④无项目
 *        （projectId=null）→分析面不失效 ⑤TASK_EVENT 重读 ?task= 轨迹
 *        （提交后新任务 id 到场即重新订阅——URL 单一真相）
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useTaskTerminalFaceRefresh } from "./taskTerminalRefresh";
import { TASK_EVENT } from "../../shared/events";

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  onTerminal: null as ((state: string) => void) | null,
  taskId: null as string | null,
}));

vi.mock("../../features/solutions/api/useTaskFeed", () => ({
  useTaskFeed: (
    taskId: string | null,
    onTerminal?: (state: string) => void,
  ) => {
    gate.taskId = taskId; // 订阅轨迹受控位（URL ?task= 派生面）
    gate.onTerminal = onTerminal ?? null; // 终态回调受控位（真壳透传）
    return null;
  },
}));

/** 挂载探针组件（hook 零渲染面——探针仅承载调用）。 */
function Probe() {
  useTaskTerminalFaceRefresh();
  return null;
}

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderHook(url: string): void {
  window.history.replaceState(null, "", url);
  render(
    <QueryClientProvider client={queryClient}>
      <Probe />
    </QueryClientProvider>,
  );
}

const KEYS = {
  unitResults: ["/api/calc/projects/p1/units/municipal_cugeshan/results"],
  compare: ["/api/calc/compare/p1"],
  trust: ["/api/calc/trust/p1"],
  validation: ["/api/calc/validation/p1"],
  otherProject: ["/api/calc/validation/p2"],
} as const;

function seed(): void {
  for (const key of Object.values(KEYS)) {
    queryClient.setQueryData([...key], { seeded: true });
  }
}

function clearAll(): void {
  for (const key of Object.values(KEYS)) {
    queryClient.removeQueries({ queryKey: [...key] });
  }
}

beforeEach(() => {
  gate.onTerminal = null;
});

afterEach(() => {
  clearAll();
  cleanup();
});

describe("F1 任务终态分析面刷新（恒挂载层单点）", () => {
  it("终态 done：分析面四域失效（unit-results/compare/trust/validation）", () => {
    seed();
    renderHook("/?project=p1&task=t-done-1&tab=parameters");
    expect(gate.onTerminal).not.toBeNull();
    expect(queryClient.getQueryState([...KEYS.unitResults])?.isInvalidated).toBe(
      false,
    ); // 终态前未失效（提交时刻失效已拉回旧轮值——缺口现场）
    gate.onTerminal?.("done");
    expect(queryClient.getQueryState([...KEYS.unitResults])?.isInvalidated).toBe(
      true,
    );
    expect(queryClient.getQueryState([...KEYS.compare])?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState([...KEYS.trust])?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState([...KEYS.validation])?.isInvalidated).toBe(
      true,
    );
    // 他项目键不误伤（predicate 域=本项目）
    expect(
      queryClient.getQueryState([...KEYS.otherProject])?.isInvalidated,
    ).toBe(false);
  });

  it("终态 failed：分析面不失效（无新结果不空转 refetch）", () => {
    seed();
    renderHook("/?project=p1&task=t-failed-1");
    gate.onTerminal?.("failed");
    for (const key of [KEYS.unitResults, KEYS.validation]) {
      expect(queryClient.getQueryState([...key])?.isInvalidated).toBe(false);
    }
  });

  it("无项目（projectId=null）：终态 done 分析面不失效（空转守卫）", () => {
    seed();
    renderHook("/?task=t-done-1");
    gate.onTerminal?.("done");
    expect(queryClient.getQueryState([...KEYS.unitResults])?.isInvalidated).toBe(
      false,
    );
  });

  it("TASK_EVENT 重读 ?task=（提交后新任务 id 到场即重新订阅——URL 单一真相）", () => {
    seed();
    renderHook("/?project=p1");
    expect(gate.taskId).toBeNull(); // 无 ?task= 不订阅（taskId 派生面）
    window.history.replaceState(null, "", "/?project=p1&task=t-new-1");
    fireEvent(window, new CustomEvent(TASK_EVENT, { detail: "t-new-1" }));
    // 重渲染后订阅轨迹刷新（新 taskId 订阅建立——终态回调在场）
    expect(gate.taskId).toBe("t-new-1");
    expect(gate.onTerminal).not.toBeNull();
    gate.onTerminal?.("done");
    expect(queryClient.getQueryState([...KEYS.validation])?.isInvalidated).toBe(
      true,
    );
  });
});
