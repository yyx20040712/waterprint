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
 *        testid+summary 文案+meta 表在折叠区内+正文区不含标记段
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

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
