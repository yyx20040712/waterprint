/**
 * v4 计算说明正文渲染件（B6 计算说明批段3 2026-10-09——react-markdown+
 * remark-gfm+remark-math+rehype-katex：服务端 md〔$$ 数学块+GFM 表格〕
 * →KaTeX 阅读态；sections id 锚注入〔rehype 插件——导航滚动定位真源〕）。
 *
 * 输入:  markdown: string（server GET /api/calc/projects/{pid}/report 的
 *        markdown——h2=章/h3=unit_calc 小节）+sections: ReportSectionModel[]
 *        （两级索引——与 md heading 同 AST 序对齐）
 * 输出:  正文卡内容：KaTeX 数学块（display 居中/inline 随行——katex.min.css
 *        模块级 import）+GFM 表格+叙述槽〔HTML 注释形态——react-markdown
 *        缺省不渲染 raw HTML 节点=注释不落正文，占位正文保留〕+h2/h3 携
 *        sections id 锚（左导航点击→getElementById 滚动定位）+元数据段
 *        后置 details 折叠（splitReportMeta 导出纯函数摘出「项目标识与
 *        版本三元组」标记段——V3 D3 信息专业度批；标记缺席零改）
 *
 * 规格说明（B6 任务书 §一.4/§二.⑤——视觉基线 wireframe-d-v4 屏 6）：
 *   - 渲染错误面=不可达（registry 451 条 fixture 门全量零错）但组件层
 *     禁裸 throw：rehype-katex 自带错误降级（katex-error span 红字——
 *     不抛出）+ErrorBoundary 包裹（渲染期意外异常=面板级降级非白屏）；
 *   - id 锚注入走 rehype 插件（解析期一次性序匹配：md 第 N 个 h2↔
 *     sections 第 N 个 level=1、第 N 个 h3↔第 N 个 level=2——两侧同
 *     AST 派生序恒对齐；重复标题零碰撞〔序匹配非文本匹配〕）；
 *   - md 生产面契约沿承：HTML 注释=叙述槽标记（render_md._NARRATIVE_
 *     OPEN/CLOSE）——前端不渲染为正文（react-markdown 缺省丢弃 raw
 *     节点，无 rehype-raw——白名单纪律：不引 raw HTML 渲染面）；
 *   - 视觉规则：字号 12/11/10 三档+FG-1/FG-2 两档+忌加粗（.wp-v4-root
 *     全局复位承载）；公式块排版=KaTeX 默认（微调须视觉微裁决申报）。
 */
import { createElement, useMemo, type HTMLAttributes } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import "katex/dist/katex.min.css";

import { ErrorBoundary } from "../ErrorBoundary";
import type { ReportSectionModel } from "../../shared/api/generated/model/reportSectionModel";

/** sections 行形（orval 生成模型——两级索引：level 1=章/2=unit_calc 小节）。 */
export type ReportSection = ReportSectionModel;

/** mdast 节点最小结构面（结构性类型——零传递依赖 import）。 */
type MdNode = { type?: string; value?: string; children?: MdNode[] };

/** 叙述槽 HTML 注释过滤（remark 插件——md 契约：render_md 的 narrative
 *  open/close 标记为注释形态，注释不落正文；占位正文（注释间段落）保留。
 *  react-markdown 缺省将 raw HTML 节点按原文字面渲染——本插件在解析期
 *  剥离注释节点〔渲染器默认行为与 md 契约的差集补齐，B6 段3 注记〕）。 */
function remarkDropHtmlComments() {
  const strip = (node: MdNode): void => {
    if (!node.children) {
      return;
    }
    node.children = node.children.filter(
      (child) =>
        !(child.type === "html" && (child.value ?? "").startsWith("<!--")),
    );
    for (const child of node.children) {
      strip(child);
    }
  };
  return (tree: MdNode) => {
    strip(tree);
  };
}

/** hast 元素最小结构面（结构性类型——unist Node 结构兼容，零传递依赖 import）。 */
type HastElement = {
  type?: string;
  tagName?: string;
  properties?: Record<string, unknown>;
  children?: HastElement[];
};

/** md 序→sections 序对齐真源：h2（章）消费 level=1 队、h3（小节）消费 level=2 队。 */
function rehypeHeadingIds(options: { sections: readonly ReportSection[] }) {
  const chapters = options.sections.filter((section) => section.level === 1);
  const subsections = options.sections.filter((section) => section.level === 2);
  let chapterAt = 0;
  let subsectionAt = 0;
  const assign = (element: HastElement): void => {
    if (element.tagName === "h2" && chapterAt < chapters.length) {
      element.properties = {
        ...element.properties,
        id: chapters[chapterAt]?.id,
      };
      chapterAt += 1;
    } else if (element.tagName === "h3" && subsectionAt < subsections.length) {
      element.properties = {
        ...element.properties,
        id: subsections[subsectionAt]?.id,
      };
      subsectionAt += 1;
    }
    for (const child of element.children ?? []) {
      assign(child);
    }
  };
  return (tree: HastElement) => {
    assign(tree);
  };
}

/** GFM 表格形（wireframe .rt：浅底表头+细分割+左对齐；字号 11 档）。 */
const TABLE_STYLE = {
  width: "100%",
  borderCollapse: "collapse",
  fontSize: 11,
  margin: "8px 0",
} as const;
const CELL_STYLE = {
  border: "1px solid var(--wp-border-2)",
  padding: "4px 8px",
  textAlign: "left",
} as const;
const HEAD_CELL_STYLE = {
  ...CELL_STYLE,
  background: "#f0f2f5",
  color: "var(--wp-text-2)",
} as const;

/** 呈现件映射（表格面内联形——md 生成元素零类名直挂；正文排版随容器）。 */
const mdComponents: Components = {
  table: ({ children }) => <table style={TABLE_STYLE}>{children}</table>,
  th: ({ children }) => <th style={HEAD_CELL_STYLE}>{children}</th>,
  td: ({ children }) => <td style={CELL_STYLE}>{children}</td>,
};

/** 正文容器排版（wireframe 屏 6 阅读卡内文：12px/行高 2/FG-1）。 */
const DOC_STYLE = {
  fontSize: 12,
  lineHeight: 2,
  color: "var(--wp-text)",
} as const;
const HEADING_STYLE = {
  fontWeight: 400, // 忌加粗——.wp-v4-root 复位之外的内联双保险（卡内独立字号档）
  margin: "14px 0 6px",
} as const;

/** 标题件 props（id 等透传面+react-markdown 的 node 元数据——node 剥离不入 DOM）。 */
type MdHeadingProps = HTMLAttributes<HTMLHeadingElement> & { node?: unknown };

/** 标题件（h1=文档题 16/h2=章 14/h3=小节 12——字号三档制内正文扩展档；
 *  id 锚由 rehype 插件注入 hast properties→props 透传直出）。 */
function headingOf(tag: "h1" | "h2" | "h3", fontSize: number) {
  return function MdHeading(props: MdHeadingProps) {
    const { children, node: _node, ...rest } = props;
    return createElement(
      tag,
      { ...rest, style: { ...HEADING_STYLE, fontSize } },
      children,
    );
  };
}

const headingComponents: Components = {
  h1: headingOf("h1", 16),
  h2: headingOf("h2", 14),
  h3: headingOf("h3", 12),
};

/** 元数据段标记（服务端 render_md 契约——md 首章「项目标识与版本三元组」
 *  段；V3 D3 摘出面锚，标记缺席=零改行为〔旧报告兼容〕）。 */
const META_MARKER = "**项目标识与版本三元组**";

/** splitReportMeta 结果（meta=null=标记缺席/异常形态——零改渲染）。 */
export type SplitReportMeta = { body: string; meta: string | null };

/** GFM 表分隔行判形（| --- |: 形——管道+冒号+横线+空白字符集）。 */
function isTableDelimiterLine(line: string): boolean {
  return /^\|?[\s:|-]+\|?$/.test(line) && line.includes("-");
}

/** md 元数据段摘出（字符串级标记匹配——V3 D3）：标记行起至其后首个空行
 *  界定的 GFM 表块末整段摘为 meta（标记段+紧随表）；body=前后文接缝收束
 *  （恰一空行衔接）。标记缺席/标记后无表块=零改（{body:原文, meta:null}
 *  ——旧报告与异常形态兼容；meta 段无 heading——摘出不移 h2/h3 序，
 *  sections 锚对齐前提保持）。 */
export function splitReportMeta(markdown: string): SplitReportMeta {
  const lines = markdown.split("\n");
  const markerAt = lines.findIndex((line) => line.trim() === META_MARKER);
  if (markerAt === -1) {
    return { body: markdown, meta: null };
  }
  // 标记后跳空行找首个表行；非管道行=异常形态（零改保守）
  let tableAt = -1;
  for (let index = markerAt + 1; index < lines.length; index += 1) {
    const line = lines[index] as string;
    if (line.trim() === "") {
      continue;
    }
    if (line.trim().startsWith("|")) {
      tableAt = index;
    }
    break;
  }
  if (tableAt === -1 || tableAt + 1 >= lines.length) {
    return { body: markdown, meta: null };
  }
  // 表块=连续管道行（空行界定）；次行须为分隔行（GFM 表判形）
  if (!isTableDelimiterLine((lines[tableAt + 1] as string).trim())) {
    return { body: markdown, meta: null };
  }
  let tableEnd = tableAt + 1;
  while (
    tableEnd + 1 < lines.length &&
    (lines[tableEnd + 1] as string).trim().startsWith("|")
  ) {
    tableEnd += 1;
  }
  const meta = lines.slice(markerAt, tableEnd + 1).join("\n");
  // 接缝收束：前后段各去贴边空行，双非空=恰一空行衔接
  const before = lines.slice(0, markerAt);
  while (before.length > 0 && (before[before.length - 1] as string).trim() === "") {
    before.pop();
  }
  const after = lines.slice(tableEnd + 1);
  while (after.length > 0 && (after[0] as string).trim() === "") {
    after.shift();
  }
  const body =
    before.length === 0 || after.length === 0
      ? [...before, ...after].join("\n")
      : [...before, "", ...after].join("\n");
  return { body, meta };
}

/** 折叠区排版（details 后置——正文流末尾；summary 11 档次级色）。 */
const META_DETAILS_STYLE = {
  marginTop: 14,
  borderTop: "1px solid var(--wp-border-2)",
  paddingTop: 8,
} as const;
const META_SUMMARY_STYLE = {
  fontSize: 11,
  color: "var(--wp-text-2)",
  cursor: "pointer",
} as const;

/** 计算说明正文（md→KaTeX 阅读态；ErrorBoundary=渲染意外面的面板级降级；
 *  V3 D3：元数据段摘出后置 details 折叠渲染——正文阅读流不被机器可读的
 *  哈希/版本行占据首屏）。 */
export function ReportDoc({
  markdown,
  sections,
}: {
  markdown: string;
  sections: readonly ReportSection[];
}) {
  const { body, meta } = useMemo(() => splitReportMeta(markdown), [markdown]);
  return (
    <ErrorBoundary label="计算说明书正文">
      <div data-testid="wp-v4-report-doc" style={DOC_STYLE}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath, remarkDropHtmlComments]}
          rehypePlugins={[
            rehypeKatex,
            [rehypeHeadingIds, { sections }],
          ]}
          components={{ ...headingComponents, ...mdComponents }}
        >
          {body}
        </ReactMarkdown>
        {meta !== null ? (
          <details data-testid="wp-v4-report-meta" style={META_DETAILS_STYLE}>
            <summary style={META_SUMMARY_STYLE}>项目标识与版本（元数据）</summary>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
              {meta}
            </ReactMarkdown>
          </details>
        ) : null}
      </div>
    </ErrorBoundary>
  );
}
