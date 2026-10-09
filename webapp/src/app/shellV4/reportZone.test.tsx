/**
 * @vitest-environment jsdom
 *
 * v4 计算说明区测试（B6 计算说明批段3——任务书 §一.4/§二.⑤：KaTeX 阅读面
 * 实装——react-markdown 渲染〔数学块/表格/叙述槽注释不渲染〕+左导航两级
 * 数据驱动〔章+小节+选中 AC 着色+锚定位〕+空态/stale 横幅+导出语境区三钮）。
 *
 * 输入:  ReportZone（report 读端点 hook+useExportArtifact 三 kind+项目读
 *        hook 模块替身）+REPORT_OK 夹具（markdown 与 sections 映射一致——
 *        h2↔level1/h3↔level2 逐位对齐）
 * 输出:  断言族：①无项目/无完成计算空态 ②非领域错误面 ③md 渲染（display
 *        数学块/inline 数学/表格/HTML 注释不渲染为正文）④导航两级+锚定位
 *        （scrollIntoView）⑤stale 横幅+重算 ⑥卡头副行（项目名·数据集 R-
 *        digest10）⑦导出三钮载荷（audit 空 condition_key 面）⑧exportFailText
 *        纯函数（PDF 显式错误面白名单微文案）
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ReportZone, exportFailText } from "./reportZone";
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

/** 夹具 markdown（与 SECTIONS 逐位对齐：h2 序↔level1 序/h3 序↔level2 序）。 */
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

describe("计算说明区·空态与错误面（§二.⑤）", () => {
  it("无项目=区级空态引导（B1 壳文案语义同源）", () => {
    gate.projectId = null;
    const { container } = renderZone();
    const empty = container.querySelector('[data-testid="wp-v4-report-empty"]');
    expect(empty).not.toBeNull();
    expect(empty?.textContent).toContain("项目");
  });

  it("无完成计算（report 404 领域面）=B1 壳文案空态", () => {
    gate.report = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError(
        "ReportSourceNotFoundError",
        "项目 'p1' 无最近完成结果集（先 POST /api/calc/run）",
      ),
      isPending: false,
    };
    const { container } = renderZone();
    const empty = container.querySelector('[data-testid="wp-v4-report-empty"]');
    expect(empty).not.toBeNull();
    expect(empty?.textContent).toContain("计算说明在完成计算后生成");
  });

  it("非领域错误=取数失败原文透出（错误提示白名单）", () => {
    gate.report = {
      data: undefined,
      isError: true,
      error: new WaterprintApiError("HTTP_500", "服务暂不可用"),
      isPending: false,
    };
    const { container } = renderZone();
    const face = container.querySelector('[data-testid="wp-v4-report-error"]');
    expect(face).not.toBeNull();
    expect(face?.textContent).toContain("取数失败");
    expect(face?.textContent).toContain("服务暂不可用");
  });

  it("加载中=加载占位（非空态壳）", () => {
    gate.report = { data: undefined, isError: false, error: null, isPending: true };
    const { container } = renderZone();
    expect(container.textContent).toContain("正在加载计算说明");
  });
});

describe("计算说明区·md 渲染（react-markdown+KaTeX）", () => {
  it("display 数学块渲染为 KaTeX（katex-display+katex-html 在场）", () => {
    const { container } = renderZone();
    expect(container.querySelector(".katex-display")).not.toBeNull();
    expect(container.querySelector(".katex-html")).not.toBeNull();
    expect(container.querySelector(".katex-mathml")).not.toBeNull();
  });

  it("inline 数学随行渲染（display 形缺席于该段——inline span 在场）", () => {
    const { container } = renderZone();
    const inlines = container.querySelectorAll(".katex");
    expect(inlines.length).toBeGreaterThanOrEqual(2); // display+inline 双面
  });

  it("GFM 表格渲染（表头+数据行）", () => {
    const { container } = renderZone();
    const doc = container.querySelector('[data-region="report-doc"]');
    const table = doc?.querySelector("table");
    expect(table).not.toBeNull();
    expect(table?.querySelector("th")?.textContent).toContain("指标");
    expect(table?.textContent).toContain("350");
  });

  it("叙述槽 HTML 注释不渲染为正文（md 契约——占位正文保留）", () => {
    const { container } = renderZone();
    expect(container.textContent).not.toContain("<!-- narrative");
    expect(container.textContent).not.toContain("/narrative");
    expect(container.textContent).toContain("（本段由撰写管线生成——见管线说明）");
    expect(container.textContent).toContain("撰写要点：概述本章数据来源");
  });

  it("附录表 LaTeX 列行内数学定界渲染（含竖线 \\vert 替代形——管道渲染保真锚）", () => {
    // B6 笔5 主控裁定修正锚：附录行内数学 $…$；含竖线 LaTeX（\left|…\right|
    // 绝对值形）在 md 生产面经 _appendix_math_cell 竖线→\vert 等价替换
    //（表格 \| 转义在 LaTeX 数学域=‖ 双竖线形——渲染失真防；\vert 渲染
    // 单竖线正确形）——断言锁：单元格内 KaTeX 真渲染+数学源含 \vert 形
    gate.report = {
      ...gate.report,
      data: {
        ...REPORT_OK,
        markdown: [
          "## 附录 公式溯源",
          "",
          "| 公式 ID | LaTeX | 条文号 |",
          "| --- | --- | --- |",
          "| HB-F11 | $dev_{pct} = \\frac{100 \\left\\vert{dx_{bio} - s_{y}}\\right\\vert}{s_{y}}$ | GB 50014 |",
          "",
          "## 附录 溯源索引",
          "",
        ].join("\n"),
        sections: [{ id: "formula_appendix", title: "公式溯源", level: 1 }],
      },
      isPending: false,
    };
    const { container } = renderZone();
    const rowKatex = container.querySelector(
      'table td .katex, table td .katex-mathml',
    );
    expect(rowKatex).not.toBeNull(); // 单元格内数学真渲染（非裸文本串）
    const annotation = container.querySelector(
      'table td .katex-mathml annotation',
    );
    expect(annotation?.textContent).toContain("\\left\\vert"); // \vert 入数学源
    expect(annotation?.textContent).not.toContain("\\left\\|"); // ‖ 双竖线形禁现
  });
});

describe("计算说明区·导航两级+锚定位", () => {
  it("sections 数据驱动两级树（章+小节缩进——NAV_SECTIONS 硬编码退役）", () => {
    const { container } = renderZone();
    const items = container.querySelectorAll('[data-testid="wp-v4-report-nav-item"]');
    expect(items.length).toBe(REPORT_OK.sections.length);
    expect(items[0]?.getAttribute("data-section-id")).toBe("design_basis");
    expect(items[0]?.textContent).toContain("设计原始资料");
    expect(items[1]?.getAttribute("data-section-id")).toBe("design_basis-1");
    // 小节缩进（paddingLeft 大于章行——两级形）
    const pad1 = items[0] ? getComputedStyle(items[0]).paddingLeft : "";
    const pad2 = items[1] ? getComputedStyle(items[1]).paddingLeft : "";
    expect(Number.parseInt(pad2, 10)).toBeGreaterThan(Number.parseInt(pad1, 10));
  });

  it("点击导航=右文档滚动定位（heading 注入 sections id 锚）", () => {
    const { container } = renderZone();
    // heading id 注入：章 h2 与小节 h3 均携带服务端 sections id
    const chapter = container.querySelector('#design_basis');
    const subsection = container.querySelector('#design_basis-1');
    expect(chapter?.tagName).toBe("H2");
    expect(subsection?.tagName).toBe("H3");
    const navSecond = container.querySelector<HTMLButtonElement>(
      '[data-section-id="design_basis-1"]',
    );
    fireEvent.click(navSecond as HTMLButtonElement);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
    // 选中态=AC 着色（data-active 锚）
    expect(
      container.querySelector('[data-testid="wp-v4-report-nav-item"][data-active="true"]')
        ?.getAttribute("data-section-id"),
    ).toBe("design_basis-1");
  });
});

describe("计算说明区·stale 横幅（B2 同形）", () => {
  it("stale=true=原因微文案+重算入口（点击发 POST run 载荷）", () => {
    gate.report = {
      data: { ...REPORT_OK, stale: true },
      isError: false,
      error: null,
      isPending: false,
    };
    const { container } = renderZone();
    const banner = container.querySelector('[data-testid="wp-v4-report-stale"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain("参数已变更");
    const rerun = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-report-rerun"]',
    );
    fireEvent.click(rerun as HTMLButtonElement);
    expect(gate.runMutate.mock.calls[0]?.[0]).toEqual({
      data: { project_id: "p1", conditions: [] },
    });
  });
});

describe("计算说明区·卡头副行（项目名·数据集·生成来源）", () => {
  it("副行=项目名+数据集 R-{digest10}+生成于最近完成计算", () => {
    const { container } = renderZone();
    const sub = container.querySelector('[data-testid="wp-v4-report-subline"]');
    expect(sub?.textContent).toContain("城南污水处理厂扩建工程");
    expect(sub?.textContent).toContain("数据集 R-abc123def0");
    expect(sub?.textContent).toContain("生成于最近完成计算");
  });

  it("项目名取数未就绪=id 前缀兜底（不空行不伪名）", () => {
    gate.projectRaw = undefined;
    const { container } = renderZone();
    const sub = container.querySelector('[data-testid="wp-v4-report-subline"]');
    expect(sub?.textContent).toContain("p1");
    expect(sub?.textContent).toContain("R-abc123def0");
  });
});

describe("计算说明区·导出语境区三钮（§二.⑤）", () => {
  it("三钮在场：计算书 xlsx/审计 HTML/PDF 计算书", () => {
    const { container } = renderZone();
    const row = container.querySelector('[data-region="report-export"]');
    expect(row?.textContent).toContain("计算书 xlsx");
    expect(row?.textContent).toContain("审计 HTML");
    expect(row?.textContent).toContain("PDF 计算书");
  });

  it("calcbook 钮→POST /api/exports/calcbook（design 工况+空 unit_id 总图语义）", () => {
    const { container } = renderZone();
    const btn = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-report-export-calcbook"]',
    );
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
    const btn = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-report-export-audit"]',
    );
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
    const btn = container.querySelector<HTMLButtonElement>(
      '[data-testid="wp-v4-report-export-pdf"]',
    );
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
