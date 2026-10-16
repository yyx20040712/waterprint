/**
 * @vitest-environment jsdom
 *
 * v4 计算说明正文元数据摘出测试（v3-20261015 D3——信息专业度批：服务端 md
 * 首章「项目标识与版本三元组」标记段+紧随 GFM 表=元数据，正文后置 details
 * 折叠渲染；标记缺席=零改行为——旧报告兼容）。
 *
 * 输入:  splitReportMeta 纯函数（字符串级标记匹配——三态边界）+ReportDoc
 *        真件（jsdom 渲染——details/summary 在场+表入折叠区+正文保留）
 * 输出:  断言族：①纯函数：标准在（摘出+正文接缝收束）/标记缺席（零改返回
 *        原文+meta=null）/表后正文保留（后续章节不误吞）②渲染：details
 *        testid+summary 文案+meta 表在折叠区内+正文区不含标记段③golden
 *        样本回放守卫（V5 P5——V3 d1-N8）：真实报告 verbatim 样本上标记
 *        在场路径（meta 以标记行起头/body 行级差集⊆标记段/原行序子序列/
 *        无三连空行）+零改静默路径（标记段后全部行拼串逐字节零改）+
 *        异常形态真实头片段复证
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ReportDoc, splitReportMeta } from "./reportDoc";

/** 标准形态 md（对拍 .workflow/v3-20261015/report-md-head.txt 首章形）。 */
const MD_WITH_META = [
  "# 污水处理厂设计说明书",
  "",
  "## 第 1 章 设计依据",
  "",
  "**项目标识与版本三元组**",
  "",
  "| 项目 | 值 |",
  "| --- | --- |",
  "| 设计内容哈希（content_hash） | 95a3313a4ee2a361 |",
  "| 引擎版本（engine_version） | waterprint-server 0.1.0 |",
  "",
  "**规范与条文依据（全部公式出处去重）**",
  "",
  "| 序号 | 条文出处 |",
  "| --- | --- |",
  "| 依据 1 | GB 50014-2021 §6.1 |",
  "",
  "## 第 2 章 设计水量水质",
  "",
  "设计进水 COD=350 mg/L。",
].join("\n");

const MD_NO_META = [
  "# 污水处理厂设计说明书",
  "",
  "## 第 1 章 设计依据",
  "",
  "正文无标记段。",
].join("\n");

/** golden 样本（主控落盘 golden 项目 design 工况真实报告 verbatim 五段
 *  裁样——readFileSync 直读〔css?raw 同制〕；标记行/元数据表/依据表/
 *  narrative 注释对/数学块/尾章齐备；样本即数据面照读）。 */
const GOLDEN_SAMPLE = readFileSync(
  join(
    dirname(fileURLToPath(import.meta.url)),
    "__fixtures__/golden-report-sample.md",
  ),
  "utf-8",
);

/** 测试侧标记段定位（简单切片）：标记行+其后首个连续管道行块——非
 *  splitReportMeta 复刻（无接缝收束/无分隔行判形，仅样本内定位）。 */
function goldenMetaSection(): { markerAt: number; tableEnd: number } {
  const lines = GOLDEN_SAMPLE.split("\n");
  const markerAt = lines.findIndex(
    (line) => line.trim() === "**项目标识与版本三元组**",
  );
  expect(markerAt).toBeGreaterThanOrEqual(0);
  let tableAt = -1;
  for (let index = markerAt + 1; index < lines.length; index += 1) {
    const line = (lines[index] as string).trim();
    if (line === "") {
      continue;
    }
    if (line.startsWith("|")) {
      tableAt = index;
    }
    break;
  }
  expect(tableAt).toBeGreaterThanOrEqual(0);
  let tableEnd = tableAt;
  while (
    tableEnd + 1 < lines.length &&
    (lines[tableEnd + 1] as string).trim().startsWith("|")
  ) {
    tableEnd += 1;
  }
  return { markerAt, tableEnd };
}

afterEach(cleanup);

describe("splitReportMeta 纯函数（字符串级标记匹配）", () => {
  it("标准在：摘出标记段+紧随表块；body=前后章接缝收束（无三连空行）", () => {
    const { body, meta } = splitReportMeta(MD_WITH_META);
    expect(meta).not.toBeNull();
    expect(meta as string).toContain("**项目标识与版本三元组**");
    expect(meta as string).toContain("| 项目 | 值 |");
    expect(meta as string).toContain("waterprint-server 0.1.0");
    // 摘出面只吞标记段——后续「规范与条文」段保留在 body
    expect(body).toContain("**规范与条文依据（全部公式出处去重）**");
    expect(body).toContain("## 第 2 章 设计水量水质");
    expect(body).not.toContain("**项目标识与版本三元组**");
    expect(body).not.toContain("| 项目 | 值 |");
    // 接缝收束：摘出点前后以恰一个空行衔接（禁残留双空行）
    expect(body).toContain("## 第 1 章 设计依据\n\n**规范与条文依据");
  });

  it("标记缺席：零改行为——body=原文、meta=null（旧报告兼容）", () => {
    const result = splitReportMeta(MD_NO_META);
    expect(result.meta).toBeNull();
    expect(result.body).toBe(MD_NO_META);
  });

  it("表后正文保留：表块末空行界定——表后段落/标题全数留 body", () => {
    const { body } = splitReportMeta(MD_WITH_META);
    expect(body).toContain("设计进水 COD=350 mg/L。");
    // 末章标题与首章标题均在 body（heading 序不受摘出影响——sections 锚前提）
    expect(body.startsWith("# 污水处理厂设计说明书")).toBe(true);
    expect(body.endsWith("设计进水 COD=350 mg/L。")).toBe(true);
  });

  it("标记在场但后无表块=异常形态零改（meta=null——诚实保守）", () => {
    const odd = "## 第 1 章\n\n**项目标识与版本三元组**\n\n正文直接续。";
    const result = splitReportMeta(odd);
    expect(result.meta).toBeNull();
    expect(result.body).toBe(odd);
  });
});

describe("ReportDoc 渲染（元数据折叠后置——V3 D3）", () => {
  const SECTIONS = [
    { id: "ch1", title: "设计依据", level: 1 },
    { id: "ch2", title: "设计水量水质", level: 1 },
  ];

  it("标准在：details 折叠区在场+summary 文案+meta 表入折叠区", () => {
    const { container } = render(
      <ReportDoc markdown={MD_WITH_META} sections={SECTIONS} />,
    );
    const details = container.querySelector('[data-testid="wp-v4-report-meta"]');
    expect(details).not.toBeNull();
    expect(details?.tagName).toBe("DETAILS");
    const summary = details?.querySelector("summary");
    expect(summary?.textContent).toContain("项目标识与版本（元数据）");
    // meta 表在折叠区内（含元数据行）
    expect(details?.querySelector("table")).not.toBeNull();
    expect(details?.textContent).toContain("waterprint-server 0.1.0");
  });

  it("正文区不含标记段（摘出真迁移非复制）；后续章正文保留", () => {
    const { container } = render(
      <ReportDoc markdown={MD_WITH_META} sections={SECTIONS} />,
    );
    const doc = container.querySelector('[data-testid="wp-v4-report-doc"]');
    // 真迁移非复制：标记段全 doc 恰一份（唯一份在折叠区内——正文流零残留）
    const occurrences =
      (doc?.textContent?.split("项目标识与版本三元组").length ?? 1) - 1;
    expect(occurrences).toBe(1);
    expect(doc?.textContent).toContain("规范与条文依据");
    expect(doc?.textContent).toContain("设计进水 COD=350 mg/L。");
  });

  it("标记缺席：零改渲染——details 不在场（旧报告兼容）", () => {
    const { container } = render(
      <ReportDoc markdown={MD_NO_META} sections={[SECTIONS[0]!]} />,
    );
    expect(
      container.querySelector('[data-testid="wp-v4-report-meta"]'),
    ).toBeNull();
    expect(container.textContent).toContain("正文无标记段。");
  });
});

describe("golden 样本回放（零改守卫——V5 P5）", () => {
  it("⓪样本结构自检（R2 d1-N7——未来裁样守卫：关键结构缺席即红）", () => {
    // 裁样代表性前提：标记行/GFM 表/数学定界/叙述注释/章标题五类结构
    // 齐备——后续任何人裁剪样本（如删数学块）本例红，守卫面显式化。
    const lines = GOLDEN_SAMPLE.split("\n");
    const count = (pred: (line: string) => boolean) =>
      lines.filter(pred).length;
    expect(lines.filter((l) => l.trim() === "**项目标识与版本三元组**").length).toBe(1);
    expect(count((l) => l.trim() === "| 项目 | 值 |")).toBeGreaterThanOrEqual(1);
    expect(count((l) => l.trim() === "$$")).toBeGreaterThanOrEqual(2); // 数学块定界成对
    expect(count((l) => l.trim().startsWith("<!--"))).toBeGreaterThanOrEqual(2); // 叙述注释对
    expect(count((l) => l.startsWith("## "))).toBeGreaterThanOrEqual(3); // 章标题
  });

  it("①标记在场路径：meta 以标记行起头含元数据表；body 差集⊆标记段+原行序子序列+无三连空行", () => {
    const { body, meta } = splitReportMeta(GOLDEN_SAMPLE);
    expect(meta).not.toBeNull();
    expect(meta?.startsWith("**项目标识与版本三元组**")).toBe(true);
    expect(meta).toContain("| 项目 | 值 |");
    expect(meta).toContain("waterprint-server 0.1.0");
    expect(body).not.toContain("**项目标识与版本三元组**"); // 零残留
    const lines = GOLDEN_SAMPLE.split("\n");
    const { markerAt, tableEnd } = goldenMetaSection();
    // 行级差集⊆标记段（multiset 计数差——R2 d1-N6：unique 集差对重复行
    // 不敏感〔off-by-one 恰留重复行在 body 的回归漏检面收口〕）
    const countOf = (source: string[]) => {
      const map = new Map<string, number>();
      for (const line of source) {
        map.set(line, (map.get(line) ?? 0) + 1);
      }
      return map;
    };
    const originCounts = countOf(lines);
    const bodyCounts = countOf(body.split("\n"));
    // 逐行精确闭合（multiset 计数差——R2 d1-N6）：每行被摘数=其在标记段内
    // 的出现数（段内行全数离场、段外非空行零丢失——「段内重复行〔如
    // | --- | 分隔行〕在正文别处的额外丢失」漏检面一并收口）；空行容差=
    // 接缝收束（贴边空行归一恰一份——splitReportMeta 既有契约语义）
    const segmentCounts = countOf(lines.slice(markerAt, tableEnd + 1));
    let missingNonBlank = 0;
    for (const [line, n] of originCounts) {
      if (line.trim() === "") {
        continue;
      }
      const dropped = n - (bodyCounts.get(line) ?? 0);
      const expected = segmentCounts.get(line) ?? 0;
      expect(dropped).toBe(expected);
      missingNonBlank += expected;
    }
    expect(missingNonBlank).toBeGreaterThan(0); // 摘出真发生（非平凡守卫）
    // 行数闭合（seam 感知）：body=原−标记段−接缝收束（收束面=摘出点两侧
    // 贴边空行归一，至多回收 2 行——超出即有额外增删行）
    const segmentLen = tableEnd - markerAt + 1;
    const bodyLen = body.split("\n").length;
    expect(bodyLen).toBeLessThanOrEqual(lines.length - segmentLen);
    expect(bodyLen).toBeGreaterThanOrEqual(lines.length - segmentLen - 2);
    // body=原行序子序列（双指针单调推进——摘出不移行序）
    const bodyLines = body.split("\n");
    let cursor = 0;
    for (const line of bodyLines) {
      while (cursor < lines.length && lines[cursor] !== line) {
        cursor += 1;
      }
      expect(cursor).toBeLessThan(lines.length);
      cursor += 1;
    }
    // 接缝收束：摘出点不残留三连空行
    expect(body).not.toContain("\n\n\n");
  });

  it("②零改静默路径：标记段之后全部行拼串→body 逐字节相等+meta=null", () => {
    const { tableEnd } = goldenMetaSection();
    const tail = GOLDEN_SAMPLE.split("\n").slice(tableEnd + 1).join("\n");
    expect(tail).toContain("规范与条文依据"); // 真实结构正文（非平凡串）
    expect(tail).toContain("## 第 4 章");
    const result = splitReportMeta(tail);
    expect(result.meta).toBeNull();
    expect(result.body).toBe(tail); // 逐字节零改（真实结构多样性守卫）
  });

  it("③异常形态：真实样本头片段标记行后紧跟非管道行=零改（可并②口径）", () => {
    const { markerAt } = goldenMetaSection();
    const head = [
      ...GOLDEN_SAMPLE.split("\n").slice(0, markerAt + 1),
      "",
      "正文直接续。",
    ].join("\n");
    const result = splitReportMeta(head);
    expect(result.meta).toBeNull();
    expect(result.body).toBe(head);
  });
});
