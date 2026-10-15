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
    { field_id: "q_air", label_zh: "需气量", dim: "FLOW", value: 0.805 },
    { field_id: "回收率", label_zh: "回流比", dim: "DIMENSIONLESS", value: 1.2 },
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
  it("出水指标行：avg/design 值+限值+判定（margin>=0=达标——V3 D2 徽标全词）", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = { data: TRUST_REPORT, isError: false, error: null };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const effluent = container.querySelector('[data-testid="wp-v4-effluent-table"]');
    expect(effluent).not.toBeNull();
    expect(effluent?.textContent).toContain("CODCR");
    expect(effluent?.textContent).toContain("NH3N");
    expect(effluent?.textContent).toContain("达标");
    expect(effluent?.textContent).toContain("超标");
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

  it("V4 P4 单位列=dimUnit(dim,\"output\") 映射值（与矩阵面同源；空串=—）", () => {
    gate.unit = { data: UNIT_DETAIL, isError: false, error: null };
    const { container } = renderPane({
      projectId: "p1",
      selectedUnitId: "municipal_aao",
    });
    const rows = container.querySelectorAll('[data-testid="wp-v4-unit-row"]');
    const cellOf = (row: Element, index: number): string =>
      row.querySelectorAll("td")[index]?.textContent ?? "";
    expect(cellOf(rows[0] as Element, 2)).toBe("m³"); // VOLUME→m³（上标美化）
    expect(cellOf(rows[1] as Element, 2)).toBe("h"); // TIME_H→h
    expect(cellOf(rows[2] as Element, 2)).toBe("m³/s"); // FLOW 输出面语境（UF-63）
    expect(cellOf(rows[3] as Element, 2)).toBe("—"); // DIMENSIONLESS 空串→—
    // 裸枚举名禁现（旧实现直出 VOLUME/TIME_H）
    expect(rows[0]?.textContent).not.toContain("VOLUME");
    expect(rows[1]?.textContent).not.toContain("TIME_H");
  });
});

describe("分析表态·R1 W-effluent（列并集+缺值占位）", () => {
  it("缺值=「—」占位（禁伪 0）——指标行单工况覆盖时他列诚实缺省", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = {
      data: {
        ...TRUST_REPORT,
        effluent: [
          // CODCR 仅 avg——design 列=—（旧实现 ?? 0 伪值面）
          { condition_key: "avg", standard_id: "s", indicator: "CODCR", value: 38, limit: 50, margin: 12 },
          { condition_key: "design", standard_id: "s", indicator: "NH3N", value: 4, limit: 5, margin: 1 },
        ],
      },
      isError: false,
      error: null,
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const table = container.querySelector('[data-testid="wp-v4-effluent-table"]');
    expect(table).not.toBeNull();
    const rows = table?.querySelectorAll("tbody tr") ?? [];
    // 列集=全行并集：avg+design 两列均在（首行截断旧面=design 列丢）
    const headerText = table?.querySelector("thead")?.textContent ?? "";
    expect(headerText).toContain("基准");
    expect(headerText).toContain("设计");
    expect(headerText).not.toMatch(/avg|design/i); // R2 d1-W1：表头纯中文守卫（回退「基准 avg」即红）
    // CODCR 行：单位=mg/L/avg=38/design=—（design 单元格精确断言——非伪 0；
    // V3 D2 列序=指标/单位/〔工况列〕/限值/判定——单位列后工况格索引+1）
    const codRow = Array.from(rows).find((r) => r.textContent?.includes("CODCR"));
    const cells = Array.from(codRow?.querySelectorAll("td") ?? []);
    expect(cells[1]?.textContent).toBe("mg/L");
    expect(cells[2]?.textContent).toBe("38");
    expect(cells[3]?.textContent).toBe("—");
  });

  it("trust 取数失败=错误提示面（白名单）——矩阵面仍在不阻断", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = {
      data: undefined,
      isError: true,
      error: new Error("可信度报告取数失败"),
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const plant = container.querySelector('[data-testid="wp-v4-analysis-plant"]');
    expect(plant?.textContent).toContain("出水指标读取失败");
    expect(
      container.querySelector('[data-testid="wp-compare-matrix-stub"]'),
    ).not.toBeNull(); // 矩阵面不阻断
  });
});

describe("分析表态·V3 单位列（D2——冻结六指标 mg/L+未知回退「—」）", () => {
  it("表头含「单位」列（列序=指标/单位/工况/限值/判定）+冻结域指标行=mg/L", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = { data: TRUST_REPORT, isError: false, error: null };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const table = container.querySelector('[data-testid="wp-v4-effluent-table"]');
    expect(table).not.toBeNull();
    const headerCells = Array.from(
      table?.querySelectorAll("thead th") ?? [],
    ).map((cell) => cell.textContent);
    // 列序冻结锚：指标→单位→工况列→限值→判定（R2 k2-N6：全列 toEqual 钉死
    // ——avg/design 对调即红；工况列序=夹具 effluent 首见序 avg→design）
    expect(headerCells).toEqual(["指标", "单位", "基准", "设计", "限值", "判定"]);
    const nh3nRow = Array.from(table?.querySelectorAll("tbody tr") ?? []).find(
      (row) => row.textContent?.includes("NH3N"),
    );
    const cells = Array.from(nh3nRow?.querySelectorAll("td") ?? []);
    expect(cells[1]?.textContent).toBe("mg/L");
  });

  it("冻结域外指标（如 TEMP）=「—」回退（禁伪单位）", () => {
    gate.compare = { data: COMPARE_REPORT, isError: false, error: null };
    gate.trust = {
      data: {
        ...TRUST_REPORT,
        effluent: [
          { condition_key: "design", standard_id: "s", indicator: "TEMP", value: 20, limit: 25, margin: 5 },
        ],
      },
      isError: false,
      error: null,
    };
    const { container } = renderPane({ projectId: "p1", selectedUnitId: null });
    const table = container.querySelector('[data-testid="wp-v4-effluent-table"]');
    const row = Array.from(table?.querySelectorAll("tbody tr") ?? []).find(
      (target) => target.textContent?.includes("TEMP"),
    );
    const cells = Array.from(row?.querySelectorAll("td") ?? []);
    expect(cells[1]?.textContent).toBe("—");
  });
});
