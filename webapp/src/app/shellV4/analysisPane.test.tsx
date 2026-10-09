/**
 * @vitest-environment jsdom
 *
 * v4 分析表态测试（B2 结果与方案批 2026-10-09——任务书 §一.2/§二.③/§二.⑤：
 * 全厂指标面〔工况对比矩阵——compare+trust effluent 双现行端点〕/选中单元
 * 明细〔unit_detail 新端点满行〕/stale 态〔原因微文案+重算入口〕/空态三态
 * 〔无项目/无结果/无选中单元=全厂面默认〕）。
 *
 * 输入:  AnalysisPane（compare/trust/unit_detail 三数据 hook 模块替身+
 *        CompareMatrix 呈现件替身——隔离 M1 组件面）+三态夹具
 * 输出:  断言族：①无项目空态 ②全厂面 effluent 行+判定 ③全厂面 stale
 *        横幅+重算钮 ④无结果空态（引导「全项目计算」）⑤选中单元满行
 *        （行集==载荷 rows——行模型对账 FE 面）+端口段+warnings ⑥选中
 *        单元 stale ⑦单元不在快照错误面（文案区分）
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
  unit: {
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
  },
  runMutate: vi.fn(),
}));

vi.mock("../../features/compare/api/useCompareQuery", () => ({
  useCompareQuery: () => gate.compare,
}));
vi.mock("../../features/trust/api/useTrustQuery", () => ({
  useTrustQuery: () => gate.trust,
}));
vi.mock("../../features/compare/components/CompareMatrix", () => ({
  CompareMatrix: () => <div data-testid="wp-compare-matrix-stub">矩阵替身</div>,
}));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGet: () => gate.unit,
  useRunCalculationApiCalcRunPost: () => ({
    mutate: gate.runMutate,
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
    { condition_key: "avg", standard_id: "gb18918-1a", indicator: "CODCR", value: 38, limit: 50, margin: 12 },
    { condition_key: "design", standard_id: "gb18918-1a", indicator: "CODCR", value: 40, limit: 50, margin: 10 },
    { condition_key: "design", standard_id: "gb18918-1a", indicator: "NH3N", value: 6, limit: 5, margin: -1 },
  ],
  warnings: [],
  warning_counts: {},
};

const UNIT_DETAIL = {
  project_id: "p1",
  task_id: "t1",
  unit_id: "municipal_aao",
  condition_key: "design",
  stale: false,
  design_hash: "hash-1",
  engine_version: "e",
  data_version: "d",
  rows: [
    { field_id: "v_o", label_zh: "好氧区容积", dim: "VOLUME", value: 19460 },
    { field_id: "hrt", label_zh: "水力停留时间", dim: "TIME_H", value: null },
  ],
  outflows: { "municipal_aao.out.q_design": 0.805 },
  outqualities: { "municipal_aao.out.CODCR": 40 },
  warnings: [
    {
      unit_id: "municipal_aao",
      severity: "warning",
      source: "aao",
      message: "污泥龄偏低",
      param_key: "srt",
      condition_key: "design",
      affected_unit_ids: [],
    },
  ],
  formula_ids: ["aao_v_o"],
};

beforeEach(() => {
  gate.compare = { data: undefined, isError: false, error: null };
  gate.trust = { data: undefined, isError: false, error: null };
  gate.unit = { data: undefined, isError: false, error: null };
  gate.runMutate.mockClear();
});
afterEach(cleanup);

describe("分析表态·空态三态（§二.⑤）", () => {
  it("无项目=区级空态引导（无结果面不呈现）", () => {
    const { container } = renderPane({ projectId: null, selectedUnitId: null });
    const empty = container.querySelector('[data-testid="wp-v4-analysis-empty"]');
    expect(empty).not.toBeNull();
    expect(empty?.textContent).toContain("项目");
  });

  it("无结果=引导「全项目计算」顶带钮（compare 领域 404 面）", () => {
    gate.compare = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError(
        "CompareSourceNotFoundError",
        "项目 'p1' 无最近完成结果集（先 POST /api/calc/run）",
      ),
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const empty = container.querySelector('[data-testid="wp-v4-analysis-empty"]');
    expect(empty).not.toBeNull();
    expect(empty?.textContent).toContain("全项目计算");
  });

  it("无选中单元=全厂面默认呈现（非空态——工况对比矩阵在场）", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = { data: TRUST_REPORT, isError: false, error: null };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    expect(
      container.querySelector('[data-testid="wp-v4-analysis-plant"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-compare-matrix-stub"]'),
    ).not.toBeNull();
  });
});

describe("分析表态·全厂指标面（§二.③）", () => {
  it("出水指标行：avg/design 值+限值+判定（margin>=0=达）", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = { data: TRUST_REPORT, isError: false, error: null };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const effluent = container.querySelector('[data-testid="wp-v4-effluent-table"]');
    expect(effluent).not.toBeNull();
    expect(effluent?.textContent).toContain("CODCR");
    expect(effluent?.textContent).toContain("NH3N");
    expect(effluent?.textContent).toContain("达");
    expect(effluent?.textContent).toContain("超");
  });

  it("stale=true=原因微文案+重算入口（点击发 POST run 载荷）", () => {
    gate.compare = {
      data: { ...COMPARE_REPORT, stale: true },
      isError: false,
      error: null,
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const banner = container.querySelector('[data-testid="wp-v4-analysis-stale"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain("参数已变更");
    const rerun = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-analysis-rerun"]',
    );
    expect(rerun).not.toBeNull();
    rerun?.click();
    expect(gate.runMutate.mock.calls[0]?.[0]).toEqual({
      data: { project_id: "p1", conditions: [] },
    });
  });
});

describe("分析表态·选中单元明细（§二.③）", () => {
  it("满行呈现：行集==载荷 rows（行模型对账 FE 面）+端口段+warnings", () => {
    gate.unit = { data: UNIT_DETAIL, isError: false, error: null };
    const { container } = renderPane({
      projectId: "p1",
      selectedUnitId: "municipal_aao",
    });
    const rows = container.querySelectorAll('[data-testid="wp-v4-unit-row"]');
    expect(rows.length).toBe(UNIT_DETAIL.rows.length); // 行集==载荷 rows 满行
    expect(rows[0]?.textContent).toContain("好氧区容积");
    expect(rows[0]?.textContent).toContain("19,460"); // 千分位（formatSolutionValue 同源）
    expect(rows[1]?.textContent).toContain("—"); // 缺值 None 诚实呈现
    const ports = container.querySelector('[data-testid="wp-v4-unit-ports"]');
    expect(ports?.textContent).toContain("municipal_aao.out.q_design");
    expect(ports?.textContent).toContain("municipal_aao.out.CODCR");
    const warnings = container.querySelector('[data-testid="wp-v4-unit-warnings"]');
    expect(warnings?.textContent).toContain("污泥龄偏低");
  });

  it("选中单元 stale=原因微文案+重算入口", () => {
    gate.unit = {
      data: { ...UNIT_DETAIL, stale: true },
      isError: false,
      error: null,
    };
    const { container } = renderPane({
      projectId: "p1",
      selectedUnitId: "municipal_aao",
    });
    expect(
      container.querySelector('[data-testid="wp-v4-analysis-stale"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('[data-testid="wp-v4-unit-rows"]'),
    ).not.toBeNull();
  });

  it("单元不在结果快照=错误提示面（非空态壳——错误文案透出）", () => {
    gate.unit = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError(
        "UnitDetailEntryNotFoundError",
        "单元 'municipal_cass' 不在工况 'design' 结果快照",
      ),
    };
    const { container } = renderPane({
      projectId: "p1",
      selectedUnitId: "municipal_cass",
    });
    const face = container.querySelector('[data-testid="wp-v4-analysis-error"]');
    expect(face).not.toBeNull();
    expect(face?.textContent).toContain("不在工况");
  });
});
