/**
 * @vitest-environment jsdom
 *
 * v4 计算说明区导出面测试（V5 P1 拆件 2026-10-16——reportZone.test 498 行
 * 贴预算墙：导出语境区三钮/exportFailText 纯函数/TASK_EVENT 事件桥失效
 * 谓词三 describe 迁件承载；断言逐条对账零弱化，夹具最小复制自
 * reportZone.test〔REPORT_OK/PROJECT_RAW/替身族〕）。
 *
 * 输入:  ReportZone+exportFailText（report 读端点 hook+useExportArtifact
 *        三 kind+项目读 hook 模块替身）+REPORT_OK 夹具（markdown 与
 *        sections 映射一致）+golden orval 键构造器（vi.importActual）
 * 输出:  断言族：①导出语境区三钮在场与载荷（calcbook xlsx design 工况/
 *        audit 空 condition_key 全厂单份/report_pdf design——V3 D3 calcbook
 *        主色化+audit 灰描边）②exportFailText 纯函数（PDF 显式错误面
 *        白名单微文案+404 固定摘要先提交计算引导）③TASK_EVENT 事件桥
 *        失效谓词（真 orval queryKey 形集成——事件后恰本项目报告缓存键
 *        失效，R1 回炉 W-G）
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReportZone, exportFailText } from "./reportZone";
import { WaterprintApiError } from "../../shared/api/http";
import { TASK_EVENT } from "../../shared/events";

/** localStorage 存根（ReportNav 拖宽 usePaneWidth 消费面——jsdom 面无
 *  原生方法族，reportZone.test 同制）。 */
const storageBack = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storageBack.get(key) ?? null,
  setItem: (key: string, value: string) => void storageBack.set(key, value),
  removeItem: (key: string) => void storageBack.delete(key),
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
  projectId: "p1" as string | null,
  report: {
    data: undefined as unknown,
    isError: false,
    error: null as unknown,
    isPending: false,
  },
  projectRaw: undefined as unknown,
  runMutate: vi.fn(),
  exportMutate: vi.fn(),
  exportPending: {} as Record<string, boolean>,
}));

vi.mock("../useProjectId", () => ({
  useProjectId: () => [gate.projectId, vi.fn()],
}));
vi.mock("../../shared/api/generated/calc/calc", () => ({
  useGetProjectReportApiCalcProjectsProjectIdReportGet: () => gate.report,
  useRunCalculationApiCalcRunPost: () => ({
    mutate: gate.runMutate,
    isPending: false,
  }),
}));
vi.mock("../../shared/api/generated/projects/projects", () => ({
  useReadProjectApiProjectsProjectIdGet: () => ({ data: gate.projectRaw }),
}));
vi.mock("../../features/drawings/api/useExportArtifact", () => ({
  useExportArtifact: (kind: string) => ({
    mutate: (input: unknown, opts?: { onError?: (e: unknown) => void }) => {
      gate.exportMutate(kind, input, opts);
    },
    isPending: gate.exportPending[kind] ?? false,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

function renderZone() {
  return render(
    <QueryClientProvider client={queryClient}>
      <ReportZone />
    </QueryClientProvider>,
  );
}

/** 夹具 markdown（与 SECTIONS 逐位对齐：h2 序↔level1 序/h3 序↔level2 序
 *  ——reportZone.test 同源复制，渲染语境一致）。 */
const REPORT_MARKDOWN = [
  "# 污水处理厂设计说明书",
  "",
  "## 第 1 章 设计原始资料",
  "",
  "### 1.1 进出水水质",
  "",
  "设计进水 COD=350 mg/L。",
  "",
  "$$",
  "v_{o} = \\frac{86400 q_{avg}}{x_{mlss}}",
  "$$",
  "",
  "（公式 AO-F1——条文出处：GB 50014-2021）",
  "",
  "**进出水指标**",
  "",
  "| 指标 | 进水 | 限值 |",
  "| --- | --- | --- |",
  "| COD | 350 | 50 |",
  "",
  "> 撰写要点：概述本章数据来源",
  "",
  "<!-- narrative:ch2_intro -->",
  "（本段由撰写管线生成——见管线说明）",
  "<!-- /narrative -->",
  "",
  "## 第 2 章 设计水量水质",
  "",
  "行内公式 $E = m c^{2}$ 随行呈现。",
].join("\n");

const REPORT_OK = {
  project_id: "p1",
  condition_key: "design",
  stale: false,
  design_hash: "d1d1d1d1d1d1",
  markdown: REPORT_MARKDOWN,
  sections: [
    { id: "design_basis", title: "设计原始资料", level: 1 },
    { id: "design_basis-1", title: "进出水水质", level: 2 },
    { id: "flow_quality", title: "设计水量水质", level: 1 },
  ],
  generated_from: { digest10: "abc123def0" },
};

const PROJECT_RAW = {
  project_id: "p1",
  view: { name: "城南污水处理厂扩建工程" },
};

beforeEach(() => {
  gate.projectId = "p1";
  gate.report = { data: REPORT_OK, isError: false, error: null, isPending: false };
  gate.projectRaw = PROJECT_RAW;
  gate.runMutate.mockClear();
  gate.exportMutate.mockClear();
  gate.exportPending = {};
  // jsdom 无 scrollIntoView——锚定位断言面（点击后真调用）
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(cleanup);

describe("计算说明区·导出语境区三钮（§二.⑤）", () => {
  it("三钮在场：计算书 xlsx/审计 HTML/PDF 计算书（V3 D3：calcbook 主色化+audit 保持灰描边）", () => {
    const { container } = renderZone();
    const row = container.querySelector('[data-region="report-export"]');
    expect(row?.textContent).toContain("计算书 xlsx");
    expect(row?.textContent).toContain("审计 HTML");
    expect(row?.textContent).toContain("PDF 计算书");
    // V3 D3 导出主钮主色：AC 底+白字（jsdom 色归一 rgb 形）；audit 现状保持
    const calcbook = container.querySelector<HTMLButtonElement>('[data-testid="wp-v4-report-export-calcbook"]');
    expect(calcbook?.style.background).toBe("var(--wpv4-ac)");
    expect(calcbook?.style.color).toBe("rgb(255, 255, 255)");
    expect(container.querySelector<HTMLButtonElement>('[data-testid="wp-v4-report-export-audit"]')?.style.background).toBe("var(--wp-bg-elevated)");
  });

  it("calcbook 钮→POST /api/exports/calcbook（design 工况+空 unit_id 总图语义）", () => {
    const { container } = renderZone();
    const btn = container.querySelector<HTMLButtonElement>('[data-testid="wp-v4-report-export-calcbook"]');
    fireEvent.click(btn as HTMLButtonElement);
    expect(gate.exportMutate).toHaveBeenCalledTimes(1);
    const [kind, input] = gate.exportMutate.mock.calls[0] as [string, unknown];
    expect(kind).toBe("calcbook");
    expect(input).toEqual({
      projectId: "p1",
      unitId: "",
      conditionKey: "design",
      force: false,
    });
  });

  it("audit 钮→condition_key 空（audit 全厂单份跨工况——服务端 422 闸对齐）", () => {
    const { container } = renderZone();
    const btn = container.querySelector<HTMLButtonElement>('[data-testid="wp-v4-report-export-audit"]');
    fireEvent.click(btn as HTMLButtonElement);
    const [kind, input] = gate.exportMutate.mock.calls[0] as [string, unknown];
    expect(kind).toBe("audit");
    expect(input).toEqual({
      projectId: "p1",
      unitId: "",
      conditionKey: "",
      force: false,
    });
  });

  it("PDF 钮→report_pdf（design 工况）", () => {
    const { container } = renderZone();
    const btn = container.querySelector<HTMLButtonElement>('[data-testid="wp-v4-report-export-pdf"]');
    fireEvent.click(btn as HTMLButtonElement);
    const [kind, input] = gate.exportMutate.mock.calls[0] as [string, unknown];
    expect(kind).toBe("report_pdf");
    expect(input).toEqual({
      projectId: "p1",
      unitId: "",
      conditionKey: "design",
      force: false,
    });
  });
});

describe("计算说明区·exportFailText 纯函数（PDF 显式错误面白名单）", () => {
  it("PDF 编译失败=显式「PDF 计算书导出失败」前缀+原文", () => {
    expect(
      exportFailText("report_pdf", new WaterprintApiError("TypstCompileError", "typst 编译失败（returncode 1）")),
    ).toContain("PDF 计算书导出失败");
    expect(
      exportFailText("report_pdf", new WaterprintApiError("TypstCompileError", "typst 编译失败（returncode 1）")),
    ).toContain("typst 编译失败（returncode 1）");
  });

  it("404 无完成计算=固定摘要+先提交计算引导（raw API 句式不入用户面）", () => {
    const text = exportFailText(
      "calcbook",
      new WaterprintApiError("ExportSourceNotFoundError", "项目 'p1' 无最近完成结果集（先 POST /api/calc/run）"),
    );
    expect(text).toContain("项目暂无完成的计算结果");
    expect(text).toContain("先提交计算");
    expect(text).not.toContain("/api/calc/run");
  });
});

describe("计算说明区·TASK_EVENT 事件桥失效谓词（R1 回炉 W-G）", () => {
  it("真 orval queryKey 形集成：事件后恰本项目报告缓存键失效", async () => {
    // orval 生成件经 vi.importActual 取真实模块（本文件模块替身仅盖
    // hook 面——键构造器真实形=被断言对象，orval 再生成漂移即本锚红）
    const actual = await vi.importActual<
      typeof import("../../shared/api/generated/calc/calc")
    >("../../shared/api/generated/calc/calc");
    const keyOf = (pid: string) =>
      actual.getGetProjectReportApiCalcProjectsProjectIdReportGetQueryKey(pid, {
        condition_key: "design",
      });
    const keyP1 = keyOf("p1");
    const keyP2 = keyOf("p2");
    queryClient.setQueryData(keyP1, REPORT_OK);
    queryClient.setQueryData(keyP2, REPORT_OK);
    renderZone(); // projectId=p1 → TASK_EVENT 监听挂载（stale 横幅效应同源）
    expect(queryClient.getQueryState(keyP1)?.isInvalidated).toBe(false);
    window.dispatchEvent(new CustomEvent(TASK_EVENT, { detail: "t1" }));
    expect(queryClient.getQueryState(keyP1)?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState(keyP2)?.isInvalidated).toBe(false);
    queryClient.removeQueries({ queryKey: keyP1 });
    queryClient.removeQueries({ queryKey: keyP2 });
  });
});
