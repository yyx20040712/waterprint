/**
 * @vitest-environment jsdom
 *
 * ParamForm 三式提交测试（B1 骨架批 2026-10-09——DoD §四.3 jsdom 证面：
 * 按钮/Enter/失焦三通道同源 submit——按钮 onClick/输入控件 keydown Enter/
 * 失焦 onBlur 连带提交；三通道 apply 载荷恒等断言）。
 *
 * 输入:  ParamForm（目录/设计值/apply mutation 三 hook 模块替身——
 *        unitDetailPanel.test 同制）+连续区间参数夹具
 * 输出:  断言族：①按钮通道（输入→点提交重算→apply.mutate 载荷）②Enter
 *        通道（输入→keydown Enter→载荷同构）③失焦通道（输入→blur→载荷
 *        同构）④空变更/无效草稿零提交（disabled 门——三通道共守）
 *
 * 规格说明（B1 任务书 §三.3「ParamForm 复用+三式提交补齐 Enter」+DoD §四.3
 *   ——另一面证=probe-b1 N7 真浏览器三式实录）。
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ParamForm } from "./ParamForm";

/** 查询客户端（模块级单例——jsdom 直渲 Provider 壳；零网络面=hook 全替身）。 */
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

/** Provider 壳渲染（ParamForm useQueryClient 消费面）。 */
function renderForm() {
  return render(
    <QueryClientProvider client={queryClient}>
      <ParamForm projectId="p1" unitId="u1" />
    </QueryClientProvider>,
  );
}

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  mutate: vi.fn(),
  isPending: false,
}));

vi.mock("../../../shared/api/generated/calc/calc", () => ({
  useApplySolutionApiCalcSolutionsApplyPost: () => ({
    mutate: gate.mutate,
    isPending: gate.isPending,
    isSuccess: false,
    isError: false,
    error: null,
    data: undefined,
  }),
}));
vi.mock("../api/useUnitCatalog", () => ({
  useUnitCatalog: () => ({
    data: {
      units: [
        {
          unit_id: "municipal_aao",
          name_zh: "AAO 生物池",
          business_line: "municipal",
          kind: "unit",
          params: [
            {
              field_id: "volume",
              label_zh: "池容",
              dim: "VOLUME",
              default: 1000,
              range: { min: 100, max: 5000 },
              grid: null,
            },
          ],
          ports: [],
        },
      ],
    },
    isError: false,
    error: null,
  }),
}));
vi.mock("../api/useProjectDesign", () => ({
  useProjectDesign: () => ({
    data: { nodeParams: { u1: {} }, nodeKinds: { u1: "municipal_aao" } },
    isError: false,
    error: null,
  }),
}));

/** 参数输入框定位（label 行内 InputNumber 控件——title=metaTooltip 悬浮面）。 */
function paramInput(container: HTMLElement): HTMLInputElement {
  const input = container.querySelector(
    'input[title*="volume"], input.ant-input-number-input',
  ) as HTMLInputElement | null;
  if (input === null) {
    throw new Error("参数输入框未找到");
  }
  return input;
}

beforeEach(() => {
  gate.mutate.mockClear();
  gate.isPending = false;
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("B1 ParamForm 三式提交（按钮/Enter/失焦——DoD §四.3 jsdom 证面）", () => {
  it("按钮通道：输入变更→点「提交重算」→apply 载荷含变更参数", () => {
    const { container, getByRole } = renderForm();
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "1500" } });
    fireEvent.click(getByRole("button", { name: /提交重算/ }));
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 1500 } },
    });
  });

  it("Enter 通道：输入变更→keydown Enter→apply 载荷同构", () => {
    const { container } = renderForm();
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "1800" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 1800 } },
    });
  });

  it("失焦通道：输入变更→blur→apply 载荷同构（归一后连带提交）", () => {
    const { container } = renderForm();
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "2200" } });
    fireEvent.blur(input);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 2200 } },
    });
  });

  it("空变更零提交（三通道共守 disabled 门）", () => {
    const { container, getByRole } = renderForm();
    const input = paramInput(container);
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.blur(input);
    fireEvent.click(getByRole("button", { name: /提交重算/ }));
    expect(gate.mutate).not.toHaveBeenCalled();
  });
});
