/**
 * ApplySolutionButton 应用三闸测试（P0-2——F5 死锁修复 r2 三守卫）。
 *
 * 输入:  ApplySolutionButton（gateReason/driftWarn/unitId 三变量面）
 * 输出:  闸禁用（gateReason 非空=disabled+title 述因）/漂移态 Popconfirm
 *        二次确认文案在场（呈裁⑧ 甲案：警示后放行）/unitId=null 兜底
 *        禁用文案（F5 原误导文案「先在下拉选定」根除断言）
 *
 * 形态说明（沿 TaskPanel.test.tsx SSR 先例——零 jsdom 红线：renderToString
 * 服务端渲染真 antd 树，HTML 串包含断言；交互面（Popconfirm 点击流）归
 * 无头 E2E——本件锁渲染面文案与禁用态）。
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ApplySolutionButton } from "./ApplySolutionButton";
import type { GridField } from "../lib/solutionsFields";
import type { SolutionRow } from "../lib/solutionsView";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
});

const gridFields: GridField[] = [{ key: "n", dim: "DIMENSIONLESS", label_zh: "系列数" }];
const row: SolutionRow = { n: 3, margin_min: 0.5 };

/** 渲染至 HTML 串（三变量单点注入——其余必需 props 恒定；ConfigProvider
 * 镜像 providers.tsx Button.autoInsertSpace=false[F10 收口]——不 import
 * app 层 Providers 守分层红线）。 */
function renderButton(
  unitId: string | null,
  gateReason: string | null = null,
  driftWarn = false,
): string {
  return renderToString(
    <ConfigProvider button={{ autoInsertSpace: false }}>
      <QueryClientProvider client={queryClient}>
        <ApplySolutionButton
          row={row}
          gridFields={gridFields}
          projectId="proj-p0-2"
          unitId={unitId}
          gateReason={gateReason}
          driftWarn={driftWarn}
        />
      </QueryClientProvider>
    </ConfigProvider>,
  );
}

describe("ApplySolutionButton 应用三闸（P0-2 r2）", () => {
  it("放行面：gateReason=null+unitId 在场=按钮可点（无禁用态无 Popconfirm）", () => {
    const html = renderButton("inlet", null, false);
    expect(html).toContain("应用");
    expect(html).not.toContain("disabled");
    expect(html).not.toContain("仍要应用");
  });

  it("闸①/②禁用面：gateReason 非空=disabled+title 述因（防误配/单元删除）", () => {
    const html = renderButton(
      "inlet",
      "单元下拉已选 inlet2，方案表来自 inlet 的枚举——切回 inlet 或重新提交枚举后再应用",
    );
    expect(html).toContain("disabled");
    expect(html).toContain("方案表来自 inlet 的枚举");
  });

  it("闸③漂移面：driftWarn=true=行级「旧版本」警示标记在场（警示后放行）", () => {
    const html = renderButton("inlet", null, true);
    expect(html).toContain("旧版本");
    expect(html).toContain("ant-typography-warning");
  });

  it("unitId=null 兜底：禁用+文案不再误导「先在下拉选定」（F5 根除断言）", () => {
    const html = renderButton(null);
    expect(html).toContain("disabled");
    expect(html).toContain("历史任务载荷缺 unit_id");
    expect(html).not.toContain("先在上方单元下拉选定");
  });
});
