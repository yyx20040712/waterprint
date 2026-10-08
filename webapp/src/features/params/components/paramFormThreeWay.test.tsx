/**
 * @vitest-environment jsdom
 *
 * ParamForm 三式提交测试（B1 骨架批 2026-10-09+回炉 R1 批 R5/T1——DoD
 * §四.3 jsdom 证面：按钮恒提；Enter/失焦两通道=commitOnBlurAndEnter prop
 * 门控〔缺省 false=M1 面零行为变——失焦仅 F8 归一；true=v4 左栏三式全开
 * 且失焦先归一后提交——归一值随载荷发出〕）。
 *
 * 输入:  ParamForm（目录/设计值/apply mutation 三 hook 模块替身——
 *        unitDetailPanel.test 同制）+连续区间参数夹具+自由值参数夹具
 *        （Input 分支——归一随载荷断言面）
 * 输出:  断言族：①按钮通道（缺省门——输入→点提交重算→apply.mutate 载荷）
 *        ②M1 门控缺省零行为变（Enter/失焦零提交——回炉 R5 证面）③v4
 *        门控开 Enter 通道 ④v4 门控开失焦通道（InputNumber 分支）⑤v4
 *        门控开失焦先归一后提交（Input 分支——0.30000000000000004→0.3
 *        随载荷）⑥v4 门控开 Enter 同款先归一后提交（Input 分支——B1
 *        R2/M1：Enter 通道归一值随载荷，非渲染期 raw drafts）⑦防双发
 *        两机制（T1：relatedTarget=提交钮 blur 零调用+
 *        isPending=false 注入下 blur+click 双发恰 1 次）⑧空变更零提交
 *
 * 规格说明（B1 任务书 §三.3+回炉简报 R5/T1——另一面证=probe-b1 N7 真浏览器
 *   三式实录〔v4 面〕；M1 面零行为变承诺=缺省门关两通道不动）。
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ParamForm } from "./ParamForm";

/** 查询客户端（模块级单例——jsdom 直渲 Provider 壳；零网络面=hook 全替身）。 */
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

/** Provider 壳渲染（ParamForm useQueryClient 消费面；props 透传门控面）。 */
function renderForm(props?: { commitOnBlurAndEnter?: boolean }) {
  return render(
    <QueryClientProvider client={queryClient}>
      <ParamForm projectId="p1" unitId="u1" {...props} />
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
            {
              // 自由值参数（grid/range 均缺——Input 分支：失焦归一随载荷断言面）
              field_id: "dosing",
              label_zh: "投配比",
              dim: "RATIO",
              default: 0.25,
              range: null,
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

/** 连续参数输入框定位（InputNumber——title=metaTooltip 悬浮面）。 */
function paramInput(container: HTMLElement): HTMLInputElement {
  const input = container.querySelector(
    'input[title*="volume"]',
  ) as HTMLInputElement | null;
  if (input === null) {
    throw new Error("参数输入框未找到");
  }
  return input;
}

/** 自由值参数输入框定位（Input 分支——title=metaTooltip 悬浮面）。 */
function freeInput(container: HTMLElement): HTMLInputElement {
  const input = container.querySelector(
    'input[title*="dosing"]',
  ) as HTMLInputElement | null;
  if (input === null) {
    throw new Error("自由值参数输入框未找到");
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

describe("B1 ParamForm 三式提交（回炉 R5 门控双态——DoD §四.3 jsdom 证面）", () => {
  it("按钮通道（缺省门）：输入变更→点「提交重算」→apply 载荷含变更参数", () => {
    const { container, getByRole } = renderForm();
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "1500" } });
    fireEvent.click(getByRole("button", { name: /提交重算/ }));
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 1500 } },
    });
  });

  it("M1 门控缺省零行为变（回炉 R5）：Enter/失焦两通道零提交（失焦仅归一）", () => {
    const { container } = renderForm();
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "1800" } });
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.blur(input);
    const free = freeInput(container);
    fireEvent.change(free, { target: { value: "0.30000000000000004" } });
    fireEvent.blur(free);
    expect(gate.mutate).not.toHaveBeenCalled();
  });

  it("v4 门控开·Enter 通道：输入变更→keydown Enter→apply 载荷同构", () => {
    const { container } = renderForm({ commitOnBlurAndEnter: true });
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "1800" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 1800 } },
    });
  });

  it("v4 门控开·失焦通道（InputNumber 分支）：输入变更→blur→载荷同构", () => {
    const { container } = renderForm({ commitOnBlurAndEnter: true });
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "2200" } });
    fireEvent.blur(input);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 2200 } },
    });
  });

  it("v4 门控开·失焦先归一后提交（Input 分支）：噪声值→blur→归一值随载荷发出", () => {
    const { container } = renderForm({ commitOnBlurAndEnter: true });
    const free = freeInput(container);
    fireEvent.change(free, { target: { value: "0.30000000000000004" } });
    fireEvent.blur(free);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { dosing: 0.3 } },
    });
  });

  it("v4 门控开·Enter 先归一后提交（Input 分支）：噪声值→Enter→归一值随载荷发出", () => {
    const { container } = renderForm({ commitOnBlurAndEnter: true });
    const free = freeInput(container);
    fireEvent.change(free, { target: { value: "0.30000000000000004" } });
    fireEvent.keyDown(free, { key: "Enter" });
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { dosing: 0.3 } },
    });
  });

  it("防双发两机制（回炉 T1）：relatedTarget=提交钮 blur 零调用+isPending=false 下 blur+click 恰 1 次", () => {
    const { container, getByRole } = renderForm({ commitOnBlurAndEnter: true });
    const input = paramInput(container);
    fireEvent.change(input, { target: { value: "1300" } });
    const submitBtn = getByRole("button", { name: /提交重算/ });
    // T1①：焦点移向提交钮（relatedTarget）→blur 通道让位——零调用
    fireEvent.blur(input, { relatedTarget: submitBtn });
    expect(gate.mutate).not.toHaveBeenCalled();
    // T1②：isPending=false 注入（pending 门不设防）→click 提交恰 1 次
    // ——双发防线=让位机制非 pending 态，两机制有效性由此区分
    fireEvent.click(submitBtn);
    expect(gate.mutate).toHaveBeenCalledTimes(1);
    expect(gate.mutate).toHaveBeenCalledWith({
      data: { project_id: "p1", unit_id: "u1", params: { volume: 1300 } },
    });
  });

  it("空变更零提交（门控开三通道共守 disabled 门）", () => {
    const { container, getByRole } = renderForm({ commitOnBlurAndEnter: true });
    const input = paramInput(container);
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.blur(input);
    fireEvent.click(getByRole("button", { name: /提交重算/ }));
    expect(gate.mutate).not.toHaveBeenCalled();
  });
});
