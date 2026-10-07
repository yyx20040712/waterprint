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
 *        「管网图纸预留」③说明行全文逐字（v3 B-3 挂起位③口径——
 *        「纵断面图」用词对齐 elevation 面既有中文词，申报见任务书 §7）
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

  it("Tag 文案「管网图纸预留」（default 色，style 沿树徽标同形）", () => {
    render(<PendingDrawingTemplates />);
    expect(screen.getByText("管网图纸预留")).toBeTruthy();
  });

  it("说明行全文逐字（挂起展示，不实现——v3 B-3 演示止步口径）", () => {
    render(<PendingDrawingTemplates />);
    expect(
      screen.getByText(
        "管网平面布置图·纵断面图将随后续管网批加入图纸目录（挂起展示，不实现）",
      ),
    ).toBeTruthy();
  });
});
