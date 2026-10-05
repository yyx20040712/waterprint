/**
 * @vitest-environment jsdom
 *
 * 五结果页签 domainGate 分支两态常驻用例（2A7 批 2026-10-05 UF-57——
 * pane JSX 分支接线面；domainGate 纯核已由 sourceGate.test 锁定，本文件
 * 不复测纯核）。
 *
 * 输入:  costPane/comparePane/drawingsPane/elevationPane/trustPane（真
 *        useProjectId——history.replaceState 摆 ?project=，不 mock 本 hook）
 *        +vi.mock 各取数 hook 的 feature api 模块（mock 边界=feature api
 *        模块面，禁 mock react-query 内部/antd；pane 其余取数 hook〔如
 *        costPane 的 useListUnitsApiUnitsGet〕mock 为无害空数据使渲染可达
 *        门控分支）+QueryClientProvider 每用例新 client（retry:false）
 * 输出:  六分支×两态=12 用例（下限）：domain 态（真实 WaterprintApiError
 *        code+「raw 服务端句式」注入）断言固定摘要「项目暂无完成的计算
 *        结果。」在场+本行前缀不在场；raw 态（真实 new Error「网络中断
 *        探针」注入）断言前缀+raw message 在场（I-3 分级口径）
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ComparePane } from "./comparePane";
import { CostPane } from "./costPane";
import { DrawingsPane } from "./drawingsPane";
import { ElevationPane } from "./elevationPane";
import { TrustPane } from "./trustPane";
import { WaterprintApiError } from "../shared/api/http";

/** 受控态位（vi.hoisted——各 mock 工厂闭包同源读写）。 */
const gate = vi.hoisted(() => {
  const idle = () => ({
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
  });
  return {
    cost: idle(),
    compare: idle(),
    projectRaw: idle(),
    exports: idle(),
    conditions: idle(),
    units: idle(),
    elevation: idle(),
    trust: idle(),
    validation: idle(),
  };
});

vi.mock("../features/cost/api/useCostQuery", () => ({
  useCostQuery: () => gate.cost,
}));
vi.mock("../features/compare/api/useCompareQuery", () => ({
  useCompareQuery: () => gate.compare,
}));
vi.mock("../features/canvas/api/useProjectQuery", () => ({
  useProjectQuery: () => gate.projectRaw,
}));
vi.mock("../features/drawings/api/useExportsQuery", () => ({
  useExportsQuery: () => gate.exports,
  useConditionOptions: () => gate.conditions,
  useUnitOptions: () => gate.units,
}));
vi.mock("../features/elevation/api/useElevationQuery", () => ({
  useElevationQuery: () => gate.elevation,
}));
vi.mock("../features/trust/api/useTrustQuery", () => ({
  useTrustQuery: () => gate.trust,
}));
vi.mock("../features/trust/api/useValidationQuery", () => ({
  useValidationQuery: () => gate.validation,
}));
// generated 面无害空数据（pane 其余取数 hook——渲染可达门控分支；
// trust 视图工况列中文名同源消费）
vi.mock("../shared/api/generated/units/units", () => ({
  useListUnitsApiUnitsGet: () => ({ data: undefined, isError: false }),
}));
vi.mock("../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => ({ data: undefined, isError: false }),
  useSaveProjectApiProjectsProjectIdPut: () => ({
    mutate: () => {},
    isPending: false,
  }),
}));

/** 固定摘要锚（domain 态——六分支共用串）。 */
const NO_CALC_SUMMARY = "项目暂无完成的计算结果。";

/** 领域态注错（真实 WaterprintApiError——raw 服务端句式不透出面）。 */
function domainState(code: string) {
  return {
    data: undefined,
    isError: true,
    error: new WaterprintApiError(code, "raw 服务端句式"),
  };
}

/** raw 态注错（真实普通 Error——网络中断探针，I-3 口径 raw 透出）。 */
function rawState() {
  return { data: undefined, isError: true, error: new Error("网络中断探针") };
}

/** TrustReport 最小形（validation 门控分支可达前提——TrustReportView 纯
 *  展示消费面空数组/伪哈希即可渲染）。 */
const TRUST_REPORT = {
  design_hash: "hash-gate-2a7",
  engine_version: "engine-gate-2a7",
  data_version: "data-gate-2a7",
  task_id: "task-gate-2a7",
  stale: false,
  diagnostics_available: false,
  loop_params: {},
  convergence: [],
  mass_balance: [],
  effluent: [],
  warning_counts: {},
  warnings: [],
};

/** 渲染定式：每用例新 QueryClient（retry:false）包裹。 */
function renderPane(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

/** 两态断言对（domain：摘要在场+前缀不在场+raw 句式不透出；raw：前缀+
 *  raw message 在场）——断言串逐条对源（brief D3 表 2026-10-05 实核）。 */
function expectDomainGate(prefix: string) {
  expect(document.body.textContent).toContain(NO_CALC_SUMMARY);
  expect(document.body.textContent).not.toContain(prefix);
  expect(document.body.textContent).not.toContain("raw 服务端句式");
}

function expectRawGate(prefix: string) {
  expect(document.body.textContent).toContain(prefix);
  expect(document.body.textContent).toContain("网络中断探针");
}

beforeEach(() => {
  // 真 useProjectId（不 mock）——location.search 摆参直读
  window.history.replaceState(null, "", "/?project=proj-gate");
  for (const slot of Object.values(gate)) {
    slot.data = undefined;
    slot.isError = false;
    slot.error = null;
  }
});

afterEach(cleanup);

describe("五结果页签 domainGate 分支两态（UF-57 2A7 批——JSX 接线面）", () => {
  it("①costPane/useCostQuery domain：CostSourceNotFoundError→固定摘要在场+「概算取数失败：」不在场", () => {
    gate.cost = domainState("CostSourceNotFoundError");
    renderPane(<CostPane />);
    expectDomainGate("概算取数失败：");
  });

  it("②costPane/useCostQuery raw：网络错→「概算取数失败：」+raw message 在场", () => {
    gate.cost = rawState();
    renderPane(<CostPane />);
    expectRawGate("概算取数失败：");
  });

  it("③comparePane/useCompareQuery domain：CompareSourceNotFoundError→固定摘要在场+「多工况对比报告取数失败：」不在场", () => {
    gate.compare = domainState("CompareSourceNotFoundError");
    renderPane(<ComparePane />);
    expectDomainGate("多工况对比报告取数失败：");
  });

  it("④comparePane/useCompareQuery raw：网络错→「多工况对比报告取数失败：」+raw message 在场", () => {
    gate.compare = rawState();
    renderPane(<ComparePane />);
    expectRawGate("多工况对比报告取数失败：");
  });

  it("⑤drawingsPane/useConditionOptions domain：CostSourceNotFoundError→固定摘要在场+「工况清单取数失败：」不在场", () => {
    gate.conditions = domainState("CostSourceNotFoundError");
    renderPane(<DrawingsPane />);
    expectDomainGate("工况清单取数失败：");
  });

  it("⑥drawingsPane/useConditionOptions raw：网络错→「工况清单取数失败：」+raw message 在场", () => {
    gate.conditions = rawState();
    renderPane(<DrawingsPane />);
    expectRawGate("工况清单取数失败：");
  });

  it("⑦elevationPane/useElevationQuery domain：ElevationSourceNotFoundError→固定摘要在场+「纵断取数失败：」不在场", () => {
    gate.elevation = domainState("ElevationSourceNotFoundError");
    renderPane(<ElevationPane />);
    expectDomainGate("纵断取数失败：");
  });

  it("⑧elevationPane/useElevationQuery raw：网络错→「纵断取数失败：」+raw message 在场", () => {
    gate.elevation = rawState();
    renderPane(<ElevationPane />);
    expectRawGate("纵断取数失败：");
  });

  it("⑨trustPane/useTrustQuery domain：TrustSourceNotFoundError→固定摘要在场+「可信度报告取数失败：」不在场", () => {
    gate.trust = domainState("TrustSourceNotFoundError");
    renderPane(<TrustPane />);
    expectDomainGate("可信度报告取数失败：");
  });

  it("⑩trustPane/useTrustQuery raw：网络错→「可信度报告取数失败：」+raw message 在场", () => {
    gate.trust = rawState();
    renderPane(<TrustPane />);
    expectRawGate("可信度报告取数失败：");
  });

  it("⑪trustPane/useValidationQuery domain：ValidationSourceNotFoundError→固定摘要在场+「检修观测取数失败：」不在场", () => {
    gate.trust = { data: TRUST_REPORT, isError: false, error: null };
    gate.validation = domainState("ValidationSourceNotFoundError");
    renderPane(<TrustPane />);
    expectDomainGate("检修观测取数失败：");
  });

  it("⑫trustPane/useValidationQuery raw：网络错→「检修观测取数失败：」+raw message 在场", () => {
    gate.trust = { data: TRUST_REPORT, isError: false, error: null };
    gate.validation = rawState();
    renderPane(<TrustPane />);
    expectRawGate("检修观测取数失败：");
  });
});
