/**
 * @vitest-environment jsdom
 *
 * PendingDrawingTemplates 组件测试（M4 批 D4——挂起位③载体：studio.drawings
 * 管网图纸模板位展示；契约头制式照 LineSidebar.test.tsx）。
 *
 * 输入:  PendingDrawingTemplates（无参纯展示子件——jsdom 直渲；组件零
 *        浮层零按钮，无 ResizeObserver/ConfigProvider 面需补丁）
 * 输出:  断言组：①载体容器在场（data-testid=wp-pending-drawing-templates
 *        ——门二探针消费面，wp-pending-network 命名族对齐）②Tag 文案
 *        「管网图纸 · 规划中」（回炉 R1 批 R8——诚实短文案）③说明行
 *        全文逐字（「纵断面图」用词对齐 elevation 面既有中文词，申报见
 *        任务书 §7）
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { PendingDrawingTemplates } from "./PendingDrawingTemplates";

describe("PendingDrawingTemplates（M4 D4——挂起位③载体纯展示）", () => {
  afterEach(cleanup);

  it("载体容器在场（data-testid=wp-pending-drawing-templates——门二探针锚）", () => {
    render(<PendingDrawingTemplates />);
    expect(screen.getByTestId("wp-pending-drawing-templates")).toBeTruthy();
  });

  it("Tag 文案「管网图纸 · 规划中」（回炉 R8——诚实短文案，default 色 style 沿树徽标同形）", () => {
    render(<PendingDrawingTemplates />);
    expect(screen.getByText("管网图纸 · 规划中")).toBeTruthy();
  });

  it("说明行全文逐字（回炉 R8——后续批加入目录的诚实说明，无内部口径语）", () => {
    render(<PendingDrawingTemplates />);
    expect(
      screen.getByText("管网平面布置图·纵断面图将随后续管网批加入图纸目录"),
    ).toBeTruthy();
  });
});
