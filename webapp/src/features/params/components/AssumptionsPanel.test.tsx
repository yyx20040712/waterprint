/**
 * AssumptionsPanel（经验取值页体）SSR 测试（C2-ALIGN A5r——渲染面）。
 *
 * 输入: 种子 query 缓存（假设目录 3 键+原始项目体含覆盖 2 键）
 * 输出: vitest 断言组（中文物理意义标签显/代码名不显/控件单位后缀/
 *       展开钮行行在场/提交钮）
 *
 * 形态说明（沿 ApplySolutionButton.test.tsx SSR 先例——零 jsdom 红线；
 *   交互面[展开钮点击→默认/出处显]归无头 E2E shoot_c2_align A5——
 *   本件锁折叠态渲染结构。数据通道=orval 生成 hook queryKey 种子
 *   setQueryData——零网络面）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { AssumptionsPanel } from "./AssumptionsPanel";
import { getReadProjectApiProjectsProjectIdGetQueryKey } from "../../../shared/api/generated/projects/projects";
import { getListAssumptionsApiAssumptionsGetQueryKey } from "../../../shared/api/generated/units/units";

const PROJECT_ID = "proj-a5r-ssr";

/** 目录 fixture：3 键（LENGTH 量纲×2[覆盖 1]+DIMENSIONLESS×1）。 */
const CATALOG = {
  assumptions: [
    {
      key: "safety.superheight",
      default: 0.3,
      dim: "LENGTH",
      source: "方向 A 冻结值（fixture）",
      note: "跨单元安全超高默认",
      tuning_direction: "增大超高→池体总高与造价上升",
    },
    {
      key: "geometry.pool.spacing",
      default: 3.0,
      dim: "LENGTH",
      source: "给排水手册（fixture）",
      note: "池组列间距",
      tuning_direction: "增大间距→占地上升",
    },
    {
      key: "loop.tolerance",
      default: 1e-10,
      dim: "DIMENSIONLESS",
      source: "UF-08（fixture）",
      note: "收敛判据",
      tuning_direction: "收紧→步数增多",
    },
  ],
};

/** 原始项目体 fixture（narrowDesignParams 形状门：format_version+design）。 */
const RAW_PROJECT = {
  format_version: "1.0",
  design: {
    nodes: {},
    // 覆盖 1 键（superheight）——覆盖蓝点+恢复默认链接渲染面
    assumption_overrides: { "safety.superheight": 0.5 },
  },
};

function renderPanel(): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  queryClient.setQueryData(
    getListAssumptionsApiAssumptionsGetQueryKey(),
    CATALOG,
  );
  queryClient.setQueryData(
    getReadProjectApiProjectsProjectIdGetQueryKey(PROJECT_ID),
    RAW_PROJECT,
  );
  return renderToString(
    <ConfigProvider button={{ autoInsertSpace: false }}>
      <QueryClientProvider client={queryClient}>
        <AssumptionsPanel projectId={PROJECT_ID} />
      </QueryClientProvider>
    </ConfigProvider>,
  );
}

/** SSR 文本归一：剥 react-dom/server 文本分段注释节点（<!-- -->）。 */
function textOf(html: string): string {
  return html.replaceAll("<!-- -->", "");
}

describe("AssumptionsPanel 经验取值页体（C2-ALIGN A5r——折叠态渲染面）", () => {
  it("全部行显中文物理意义标签（assumptionLabel）——代码名仅悬浮 title 不入正文", () => {
    const text = textOf(renderPanel());
    expect(text).toContain("安全超高");
    expect(text).toContain("并联池组列间距");
    expect(text).toContain("回路收敛容差");
    // 代码名不进正文（key 仅 title 悬浮=追溯通道）
    expect(text).not.toContain(">safety.superheight<");
    expect(text).not.toContain(">loop.tolerance<");
  });

  it("行格式对齐参数面板：行行展开钮在场+控件单位后缀（LENGTH→m）", () => {
    const html = renderPanel();
    // 三行行行展开钮（aria-label=展开——折叠态初始）
    expect(html.match(/aria-label="展开"/g)?.length).toBe(3);
    // 单位后缀在场（dimUnit LENGTH→m；DIMENSIONLESS→无后缀 span）
    expect(html).toContain('data-testid="assumption-unit-safety.superheight"');
    expect(html).not.toContain('data-testid="assumption-unit-loop.tolerance"');
  });

  it("折叠态无默认/出处小字（展开交互面归 E2E）+行锚 testid", () => {
    const text = textOf(renderPanel());
    expect(text).toContain('data-testid="assumption-row-safety.superheight"');
    expect(text).toContain('data-testid="assumption-row-loop.tolerance"');
    // 折叠态：出处文案不显（fixture source 串唯一定位）
    expect(text).not.toContain("方向 A 冻结值（fixture）");
  });

  it("提交钮在场（UX2 D4 面零回归——禁用态=无变更）", () => {
    const html = renderPanel();
    // AL-N-05（R2）：锚定提交钮 testid（SSR 属性序不定——testid+文本
    // 双串锚定，disabled 单独断言）
    expect(html).toContain('data-testid="assumption-submit"');
    expect(html).toContain("提交修改");
    expect(html).toContain("disabled");
  });
});
