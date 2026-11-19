/**
 * @vitest-environment jsdom
 *
 * ParamForm 进水必填门测试（E2E 审计 F5 批 2026-11-20——DoD jsdom 证面）：
 * 新项目市政输入空态引导（guide+星标+提交锁）→ 只填平均日流量的部分态
 * 零请求（F8 遗面：失焦/Enter 中途 422 根除）→ 必填补齐后单次提交成功
 * （引导完成路径）；非必填单元面（manifest 包 required 恒 false）零扰动。
 *
 * 输入:  ParamForm（目录/设计值/apply mutation 三 hook 模块替身——
 *        paramFormThreeWay.test 同制）+builtin municipal_input 目录夹具
 *        （required 面镜像服务端 _builtin_entry 投影）
 * 输出:  断言族：①空态引导条在场+缺双必填+星标恰两枚+提交钮锁
 *        ②只填 q：失焦/Enter 零提交（部分态不撞 422）+引导条收窄到 kz
 *        ③补 kz：失焦提交恰一次（载荷含两键——引导完成）
 *        ④design 已有值重开：无引导条+正常提交（历史项目零扰动）
 *        ⑤非必填单元（aao）：无引导条无星标（required=false 面）
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ParamForm } from "./ParamForm";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

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
  /** design 投影（useProjectDesign select 窄化形态——nodeParams/nodeKinds）。 */
  design: { nodeParams: { municipal_input: {} }, nodeKinds: { municipal_input: "municipal_input" } },
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
          // builtin 进水面（服务端 _builtin_entry 投影镜像——required 第七字段）
          unit_id: "municipal_input",
          name_zh: "市政输入",
          business_line: "municipal",
          kind: "builtin",
          params: [
            { field_id: "q_avg_daily", dim: "FLOW", default: null, range: null, grid: null, label_zh: "平均日流量", required: true },
            { field_id: "kz", dim: "DIMENSIONLESS", default: null, range: null, grid: null, label_zh: "总变化系数", required: true },
            { field_id: "SS", dim: "CONCENTRATION", default: null, range: null, grid: null, label_zh: "SS 浓度", required: false },
          ],
          ports: [],
        },
        {
          // manifest 包参数面（required 恒 false——default 恒在场）
          unit_id: "municipal_cugeshan",
          name_zh: "粗格栅",
          business_line: "municipal",
          kind: "unit",
          params: [
            { field_id: "b_clear", dim: "LENGTH", default: 0.3, range: null, grid: null, label_zh: "栅距", required: false },
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
  useProjectDesign: () => ({ data: gate.design, isError: false, error: null }),
}));

/** 进水参数输入框定位（title=metaTooltip 悬浮面——field_id 尾缀唯一）。 */
function inletInput(container: HTMLElement, fieldId: string): HTMLInputElement {
  const input = container.querySelector(
    `input[title*="field_id: ${fieldId}"]`,
  ) as HTMLInputElement | null;
  if (input === null) {
    throw new Error(`参数输入框未找到：${fieldId}`);
  }
  return input;
}

beforeEach(() => {
  gate.mutate.mockClear();
  gate.isPending = false;
  gate.design = {
    nodeParams: { municipal_input: {} },
    nodeKinds: { municipal_input: "municipal_input" },
  };
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderInlet() {
  return render(
    <QueryClientProvider client={queryClient}>
      <ParamForm projectId="p1" unitId="municipal_input" commitOnBlurAndEnter />
    </QueryClientProvider>,
  );
}

describe("F5 进水必填门（空态引导——422 撞墙收口）", () => {
  it("空态：引导条在场列双必填+星标恰两枚+提交钮锁", () => {
    const { container, queryByTestId } = renderInlet();
    const guide = queryByTestId("wp-required-guide");
    expect(guide).not.toBeNull();
    expect(queryByTestId("wp-required-guide-names")?.textContent).toBe(
      "平均日流量、总变化系数",
    );
    // 星标恰两枚（q/kz——SS 可选无标）
    expect(queryByTestId("wp-required-star-q_avg_daily")).not.toBeNull();
    expect(queryByTestId("wp-required-star-kz")).not.toBeNull();
    expect(queryByTestId("wp-required-star-SS")).toBeNull();
    const submit = container.querySelector(
      '[data-testid="wp-param-submit"]',
    ) as HTMLButtonElement | null;
    expect(submit?.disabled).toBe(true);
  });

  it("只填平均日流量（审计复现态）：失焦/Enter/按钮三通道零提交——中途 422 根除+引导条收窄", () => {
    const { container, queryByTestId } = renderInlet();
    const q = inletInput(container, "q_avg_daily");
    fireEvent.change(q, { target: { value: "4" } });
    fireEvent.blur(q); // v4 失焦连带提交通道——必填门拦（修复前此处发 422）
    fireEvent.keyDown(q, { target: {}, key: "Enter" });
    fireEvent.click(container.querySelector('[data-testid="wp-param-submit"]')!);
    expect(gate.mutate).not.toHaveBeenCalled();
    expect(queryByTestId("wp-required-guide-names")?.textContent).toBe("总变化系数");
  });

  it("补 kz 后（引导完成）：失焦提交恰一次——载荷含两必填键", () => {
    const { container } = renderInlet();
    const q = inletInput(container, "q_avg_daily");
    const kz = inletInput(container, "kz");
    fireEvent.change(q, { target: { value: "4" } });
    fireEvent.change(kz, { target: { value: "1.4" } });
    fireEvent.blur(kz);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: {
        project_id: "p1",
        unit_id: "municipal_input",
        params: { q_avg_daily: 4, kz: 1.4 },
      },
    });
    expect(container.querySelector('[data-testid="wp-required-guide"]')).toBeNull();
  });

  it("design 已有必填值（历史项目重开）：无引导条+改可选指标照常提交", () => {
    gate.design = {
      nodeParams: { municipal_input: { q_avg_daily: 34760.7, kz: 1.4 } },
      nodeKinds: { municipal_input: "municipal_input" },
    };
    const { container, queryByTestId } = renderInlet();
    expect(queryByTestId("wp-required-guide")).toBeNull();
    const ss = inletInput(container, "SS");
    fireEvent.change(ss, { target: { value: "250" } });
    fireEvent.blur(ss);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: {
        project_id: "p1",
        unit_id: "municipal_input",
        params: { SS: 250 },
      },
    });
  });

  it("非必填单元面（manifest 包 required 恒 false）：无引导无星标+提交照常（零扰动）", () => {
    const view = render(
      <QueryClientProvider client={queryClient}>
        <ParamForm projectId="p1" unitId="municipal_cugeshan" />
      </QueryClientProvider>,
    );
    expect(view.queryByTestId("wp-required-guide")).toBeNull();
    const input = view.container.querySelector(
      'input[title*="field_id: b_clear"]',
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "0.35" } });
    fireEvent.click(view.getByRole("button", { name: /提交重算/ }));
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(view.queryByTestId("wp-required-star-b_clear")).toBeNull();
  });
});
