/**
 * @vitest-environment jsdom
 *
 * v4 方案卡双向数据流测试（B2 结果与方案批——任务书 §二.②/§一.3：数据流①
 * 点方案→apply 回填+方案驱动来源上抛；数据流②当前参数变更→卡重排+Δ随动；
 * 无枚举方案空态=选中单元无方案集引导 ⟳）。
 *
 * 输入:  SolutionCards（状态/方案分页/项目 design 三 hook 模块替身——
 *        unitDetailPanel.test 同制）+枚举任务夹具（grid_fields/rows/unit_id）
 * 输出:  断言族：①卡面（标题 枚举 N+S 编号+★推荐+参数摘要）②数据流①
 *        点卡=apply 载荷（grid 投影）+onApplied 方案驱动来源上抛 ③数据流②
 *        当前参数变更→重排+Δ徽标在场 ④枚举单元≠选中单元=空态引导 ⟳
 */
import { cleanup, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SolutionCards } from "./solutionCards";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  status: {
    data: {
      task_id: "t-enum-1",
      kind: "enumerate",
      state: "done",
      progress: 1.0,
      stage: "rows",
      condition_key: null,
      stale: false,
      error: null,
      error_type: null,
      result: {
        unit_id: "municipal_aao",
        grid_fields: [
          { key: "srt", dim: "TIME_H", label_zh: "污泥龄" },
          { key: "n", dim: "DIMENSIONLESS", label_zh: "系列数" },
        ],
      },
      project_id: "p1",
    },
    isError: false,
    error: null,
  },
  solutions: {
    data: {
      task_id: "t-enum-1",
      page: 1,
      size: 50,
      total: 2,
      sort: "margin_min",
      columns: ["srt", "n", "margin_min"],
      rows: [
        { srt: 12, n: 3, margin_min: 0.5 },
        { srt: 14, n: 3, margin_min: 0.4 },
      ],
      unit_id: "municipal_aao",
    },
    isError: false,
    error: null,
  },
  design: {
    data: { nodeParams: { municipal_aao: { srt: 15, n: 3 } }, nodeKinds: {} },
    isError: false,
    error: null,
  },
  applyMutate: vi.fn(),
  applied: vi.fn(),
}));

vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetTaskStatusApiCalcTasksTaskIdGet: () => gate.status,
  useGetSolutionsApiCalcTasksTaskIdSolutionsGet: () => gate.solutions,
  useApplySolutionApiCalcSolutionsApplyPost: () => ({
    mutate: gate.applyMutate,
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
    data: undefined,
  }),
}));
vi.mock("../../features/params/api/useProjectDesign", () => ({
  useProjectDesign: () => gate.design,
}));
vi.mock("../../features/params/api/useUnitCatalog", () => ({
  useUnitCatalog: () => ({
    data: {
      units: [
        {
          unit_id: "municipal_aao",
          name_zh: "AAO 生物池",
          business_line: "municipal",
          kind: "unit",
          params: [],
          ports: [],
        },
      ],
    },
    isError: false,
    error: null,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderCards(props?: { unitId?: string | null; projectId?: string | null }) {
  // ?enum= 枚举轨深链（组件 URL 单一真相——jsdom 地址面就位）
  window.history.replaceState(null, "", "/?enum=t-enum-1");
  return render(
    <QueryClientProvider client={queryClient}>
      <SolutionCards
        projectId={props?.projectId ?? "p1"}
        unitId={props?.unitId === undefined ? "municipal_aao" : props.unitId}
        onOpenEnumerate={() => {}}
        onApplied={gate.applied}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  gate.applyMutate.mockClear();
  gate.applied.mockClear();
});
afterEach(cleanup);

describe("方案卡·数据流①（点方案→回填）", () => {
  it("卡面：标题枚举 N+S 编号+★推荐+参数摘要", () => {
    const { container } = renderCards();
    const section = container.querySelector('[data-testid="wp-v4-solution-cards"]');
    expect(section).not.toBeNull();
    expect(section?.textContent).toContain("AAO 生物池 · 方案（枚举 2）");
    expect(section?.textContent).toContain("S01");
    expect(section?.textContent).toContain("★推荐");
    expect(section?.textContent).toContain("污泥龄 12");
  });

  it("点卡=apply 载荷（grid 投影）+onApplied 方案驱动来源上抛", () => {
    const { container } = renderCards();
    const card = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-solution-card-S02"]',
    );
    expect(card).not.toBeNull();
    card?.click();
    const call = gate.applyMutate.mock.calls[0];
    expect(call?.[0]?.data).toEqual({
      project_id: "p1",
      unit_id: "municipal_aao",
      params: { srt: 14, n: 3 }, // S02 grid 投影（margin_min 不入载荷）
    });
    // onApplied 经 mutate onSuccess 承载——组件面直调断言归 probe（e2e 双证）
    expect(typeof call?.[1]?.onSuccess).toBe("function");
  });
});

describe("方案卡·数据流②（当前参数→重排+Δ）", () => {
  it("当前 srt=15：S02（偏差 1）列首+Δ徽标在场；S01 偏差 3 列次", () => {
    const { container } = renderCards();
    const cards = container.querySelectorAll('[data-testid^="wp-v4-solution-card-"]');
    expect(cards.length).toBe(2);
    expect(cards[0]?.getAttribute("data-testid")).toBe(
      "wp-v4-solution-card-S02",
    );
    expect(cards[0]?.textContent).toContain("Δsrt -1");
    expect(cards[1]?.getAttribute("data-testid")).toBe("wp-v4-solution-card-S01");
    expect(cards[1]?.textContent).toContain("Δsrt -3");
  });

  it("当前参数变更（srt=14）→重排随动（S02 零偏差列首、Δ 消隐）", () => {
    gate.design = {
      data: { nodeParams: { municipal_aao: { srt: 14, n: 3 } }, nodeKinds: {} },
      isError: false,
      error: null,
    };
    const { container } = renderCards();
    const cards = container.querySelectorAll('[data-testid^="wp-v4-solution-card-"]');
    expect(cards[0]?.getAttribute("data-testid")).toBe("wp-v4-solution-card-S02");
    expect(cards[0]?.textContent).not.toContain("Δ");
    expect(cards[1]?.textContent).toContain("Δsrt -2");
    gate.design = {
      data: { nodeParams: { municipal_aao: { srt: 15, n: 3 } }, nodeKinds: {} },
      isError: false,
      error: null,
    };
  });
});

describe("方案卡·空态（无枚举方案）", () => {
  it("枚举单元≠选中单元=空态引导 ⟳ 重新枚举", () => {
    const { container } = renderCards({ unitId: "municipal_cass" });
    const empty = container.querySelector('[data-testid="wp-v4-solution-empty"]');
    expect(empty).not.toBeNull();
    expect(empty?.textContent).toContain("重新枚举");
  });

  it("未选单元=引导选择（空态白名单）", () => {
    const { container } = renderCards({ unitId: null });
    const empty = container.querySelector('[data-testid="wp-v4-solution-empty"]');
    expect(empty?.textContent).toContain("选择单元");
  });
});
