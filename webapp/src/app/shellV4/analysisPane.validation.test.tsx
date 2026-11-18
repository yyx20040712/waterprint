/**
 * @vitest-environment jsdom
 *
 * v4 分析表态 T3 警告聚合接线测试（2026-11-19——warning-aggregation.md §3：
 * analysisPane 全厂指标面内嵌 WarningsPanel〔stale 横幅后/出水指标前〕，
 * validation 副数据面错误局部呈现不阻断 compare 主面；独立成件系
 * analysisPane.test.tsx 500 行预算约束——mock 模式同款复制）。
 *
 * 输入:  AnalysisPane（compare/trust/validation 三数据 hook 模块替身+
 *        CompareMatrix 呈现件替身——隔离 M1 组件面；WarningsPanel 真件渲染
 *        ——三分区呈现归本断言面）+validation 观测各态夹具
 * 输出:  断言族：①三分区渲染+摆放位次（stale 横幅→警告聚合→出水指标）
 *        ②validation_available=false=旧结果降级提示条（无数据行）
 *        ③空 warnings=区块整体不渲染 ④取数 pending=静默 ⑤404
 *        （ValidationSourceNotFoundError）=compare 同口径摘要+重算引导
 *        ——局部错误行不阻断主面 ⑥非域错误=raw 透出
 */
import { cleanup, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AnalysisPane } from "./analysisPane";
import { WaterprintApiError } from "../../shared/api/http";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  } as unknown as typeof ResizeObserver;
}

/** 替身受控位（vi.hoisted——mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => ({
  compare: {
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
  },
  trust: {
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
  },
  validation: {
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
  },
}));

vi.mock("../../features/compare/api/useCompareQuery", () => ({
  useCompareQuery: () => gate.compare,
}));
vi.mock("../../features/trust/api/useTrustQuery", () => ({
  useTrustQuery: () => gate.trust,
}));
vi.mock("../../features/validation/api/useValidationQuery", () => ({
  useValidationQuery: () => gate.validation,
}));
vi.mock("../../features/compare/components/CompareMatrix", () => ({
  CompareMatrix: () => <div data-testid="wp-compare-matrix-stub">矩阵替身</div>,
}));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGet: () => ({
    data: undefined,
    isError: false,
    error: null,
  }),
  useRunCalculationApiCalcRunPost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderPane(props: { projectId: string | null; selectedUnitId: string | null }) {
  return render(
    <QueryClientProvider client={queryClient}>
      <AnalysisPane {...props} />
    </QueryClientProvider>,
  );
}

const COMPARE_REPORT = {
  project_id: "p1",
  task_id: "t1",
  stale: false,
  design_hash: "hash-1",
  engine_version: "e",
  data_version: "d",
  condition_keys: ["avg", "design"],
  metrics: [
    {
      unit_id: "municipal_aao",
      field_id: "v_o",
      label_zh: "好氧区容积",
      dim: "VOLUME",
      values: { avg: 15568, design: 19460 },
    },
  ],
  warnings: [],
};

const TRUST_REPORT = {
  project_id: "p1",
  task_id: "t1",
  stale: false,
  design_hash: "hash-1",
  engine_version: "e",
  data_version: "d",
  diagnostics_available: true,
  kb_injected: null,
  loop_params: {},
  convergence: [],
  mass_balance: [],
  effluent: [
    { condition_key: "design", standard_id: "gb18918-1a", indicator: "CODCR", value: 40, limit: 50, margin: 10 },
  ],
  warnings: [],
  warning_counts: {},
};

/** validation 观测夹具（三分区各一形态：∅ 哨兵/双工况/单工况）。 */
const VALIDATION_REPORT = {
  project_id: "p1",
  task_id: "t1",
  stale: false,
  design_hash: "hash-1",
  engine_version: "e",
  data_version: "d",
  kb_injected: null,
  validation_available: true,
  conditions: ["avg", "design"],
  nodes: [],
  warnings: [
    {
      code: "kb.influent.bod_band",
      param_key: "bod",
      scope: "plant",
      message: "进水 BOD 300mg/L 超出建议带 [80, 250]",
      condition_keys: [],
      severity: "WARN",
    },
    {
      code: "kb.aao.n_band",
      param_key: "n",
      scope: "municipal_aao",
      message: "N=28 越门：kb.aao.n_band——n 违反 n<=25",
      condition_keys: ["avg", "design"],
      severity: "ERROR",
    },
    {
      code: "kb.cass.srt_band",
      param_key: "srt",
      scope: "municipal_cass",
      message: "泥龄 8d 低于建议带 [12, 25]",
      condition_keys: ["design"],
      severity: "WARN",
    },
  ],
};

beforeEach(() => {
  gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
  gate.trust = { data: TRUST_REPORT, isError: false, error: null };
  gate.validation = { data: undefined, isError: false, error: null };
});
afterEach(cleanup);

describe("分析表态·T3 警告聚合面（warning-aggregation.md §3 三分区）", () => {
  it("三分区渲染+摆放位次：stale 横幅后、出水指标前（违规面优先于指标阅读）", () => {
    gate.compare = {
      data: { ...COMPARE_REPORT, stale: true },
      isError: false,
      error: null,
    };
    gate.validation = { data: VALIDATION_REPORT, isError: false, error: null };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const panel = container.querySelector('[data-testid="wp-v4-warnings-panel"]');
    expect(panel).not.toBeNull();
    // 三分区各归其区（WarningsPanel 真件渲染——∅ 哨兵/≥2/单工况）
    expect(
      container.querySelector('[data-testid="wp-v4-warnings-declaration"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-warnings-aggregated"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-warnings-single"]'),
    ).not.toBeNull();
    expect(panel?.textContent).toContain("进水 BOD 300mg/L 超出建议带");
    // 位次（DOM 序）：stale 横幅 → 警告聚合面板 → 出水指标表
    const html = container.innerHTML;
    expect(html.indexOf("wp-v4-analysis-stale")).toBeLessThan(
      html.indexOf("wp-v4-warnings-panel"),
    );
    expect(html.indexOf("wp-v4-warnings-panel")).toBeLessThan(
      html.indexOf("wp-v4-effluent-table"),
    );
  });

  it("validation_available=false=旧结果降级提示条（无数据行；主面不阻断）", () => {
    gate.validation = {
      data: { ...VALIDATION_REPORT, validation_available: false },
      isError: false,
      error: null,
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    expect(
      container.querySelector('[data-testid="wp-v4-validation-unavailable"]'),
    ).not.toBeNull();
    expect(container.textContent).toContain("结果集无校验观测（旧版本结果）");
    expect(container.querySelector('[data-testid="wp-v4-warning-row"]')).toBeNull();
    expect(
      container.querySelector('[data-testid="wp-compare-matrix-stub"]'),
    ).not.toBeNull();
  });

  it("空 warnings=区块整体不渲染（零警告不打扰；他面不受扰）", () => {
    gate.validation = {
      data: { ...VALIDATION_REPORT, warnings: [] },
      isError: false,
      error: null,
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    expect(
      container.querySelector('[data-testid="wp-v4-warnings-panel"]'),
    ).toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-effluent-table"]'),
    ).not.toBeNull();
  });

  it("取数 pending=静默（面板与错误行均不在场——trust 副数据同制）", () => {
    gate.validation = { data: undefined, isError: false, error: null };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    expect(
      container.querySelector('[data-testid="wp-v4-warnings-panel"]'),
    ).toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-validation-error"]'),
    ).toBeNull();
  });

  it("404（ValidationSourceNotFoundError）=compare 同口径摘要+重算引导——局部错误行不阻断主面", () => {
    gate.validation = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError(
        "ValidationSourceNotFoundError",
        "项目 'p1' 无最近完成结果集（先 POST /api/calc/run）",
      ),
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const errorFace = container.querySelector('[data-testid="wp-v4-validation-error"]');
    expect(errorFace).not.toBeNull();
    // 与 compare 404 同一口径：固定摘要+重算引导（不新增第二文案口径）
    expect(errorFace?.textContent).toBe(
      "项目暂无完成的计算结果——尚无计算结果——点顶带「全项目计算」钮提交后回看",
    );
    expect(
      container.querySelector('[data-testid="wp-compare-matrix-stub"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-effluent-table"]'),
    ).not.toBeNull();
  });

  it("非域错误=raw 透出（取数失败——网络/窄化错诊断诚实）", () => {
    gate.validation = {
      data: undefined,
      isError: true,
      error: new Error("校验观测形状非法：warnings 非数组"),
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const errorFace = container.querySelector('[data-testid="wp-v4-validation-error"]');
    expect(errorFace?.textContent).toContain("取数失败：校验观测形状非法");
  });
});
