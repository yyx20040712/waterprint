/**
 * CompareMatrix SSR 测试（HC25-F4 P3-A——失效列头「已移除」标注可达面）。
 *
 * 输入: 构造 CompareReport（condition_keys=[design]）+pinned=[design, avg]
 *        +catalog 查询缓存种子（单元中文名索引）
 * 输出: vitest 断言组（失效键 avg 列头灰显+「（已移除）」在场/存活列
 *       无标注/pinned=null 未锁定零失效面）
 *
 * 形态说明（沿 AssumptionsPanel.test.tsx SSR 先例——renderToString 零
 *   jsdom 红线；数据通道=orval 生成 hook queryKey 种子 setQueryData
 *   零网络面；交互面归无头 E2E）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CompareMatrix } from "./CompareMatrix";
import { getListUnitsApiUnitsGetQueryKey } from "../../../shared/api/generated/units/units";
import type { CompareReport } from "../lib/compareView";

/** 报告 fixture：condition_keys=[design] 单工况（失效列由 pinned 带入）。 */
const REPORT: CompareReport = {
  project_id: "p-f4",
  task_id: "t-f4",
  stale: false,
  design_hash: "h1",
  engine_version: "e1",
  data_version: "d1",
  condition_keys: ["design"],
  metrics: [
    {
      unit_id: "municipal_aao",
      field_id: "volume",
      label_zh: null,
      dim: "VOLUME",
      values: { design: 1200 },
    },
  ],
  warnings: [{ unit_id: "municipal_aao", counts: { design: 0 } }],
};

function renderMatrix(pinned: readonly string[] | null): string {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  queryClient.setQueryData(getListUnitsApiUnitsGetQueryKey(), {
    units: [{ unit_id: "municipal_aao", name_zh: "AAO 生物池" }],
  });
  return renderToString(
    <QueryClientProvider client={queryClient}>
      <CompareMatrix report={REPORT} pinned={pinned} />
    </QueryClientProvider>,
  );
}

/** SSR 文本归一：剥 react-dom/server 文本分段注释节点（<!-- -->）。 */
function textOf(html: string): string {
  return html.replaceAll("<!-- -->", "");
}

describe("CompareMatrix 失效列头（HC25-F4 P3-A——ADR-018 D3 规格可达面）", () => {
  it("pinned 含失效键=该列头带「（已移除）」标注（condition_keys=[a]+pinned=[a,b]→b 列）", () => {
    const text = textOf(renderMatrix(["design", "avg"]));
    // avg 失效列头：中文化「平均日」+锁定★+失效标注（灰显样式另断言）
    expect(text).toContain("平均日 ★（已移除）");
    expect(text.match(/（已移除）/g)?.length).toBe(1); // 恰一失效列
  });

  it("失效列头灰显（secondary 色）+悬浮述因 title 在场", () => {
    const html = renderMatrix(["design", "avg"]);
    expect(html).toContain("var(--wp-text-secondary)"); // 灰显样式
    expect(html).toContain("avg（该工况已随受检集变更移除——重新锁定可清理）");
  });

  it("存活锁定列=★ 标在场、无失效标注", () => {
    const text = textOf(renderMatrix(["design", "avg"]));
    expect(text).toContain("最高日最高时 ★");
    expect(text).not.toContain("最高日最高时（已移除）");
  });

  it("pinned=null=未锁定零标注（★/已移除均不在场——既有语义回归锁）", () => {
    const text = textOf(renderMatrix(null));
    expect(text).not.toContain("已移除");
    expect(text).not.toContain("★");
  });
});
