/**
 * ToolCallCard 工具步折叠卡测试（B4-4b 子批 2）。
 *
 * 输入:  工具步 {name, ok}（三态：成功/失败/进行中 null）
 * 输出:  状态图标+工具名渲染断言（testid 锚）
 */

import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ToolCallCard } from "./ToolCallCard";

describe("ToolCallCard 工具步卡（B4-4b 子批 2）", () => {
  it("成功态：success 色+工具名+成功图标", () => {
    const html = renderToString(<ToolCallCard step={{ name: "wp_run_calc", ok: true }} />);
    expect(html).toContain("wp-chat-tool-wp_run_calc");
    expect(html).toContain("wp_run_calc");
    expect(html).toContain('aria-label="成功"');
  });

  it("失败态：error 色+失败图标", () => {
    const html = renderToString(<ToolCallCard step={{ name: "wp_update_params", ok: false }} />);
    expect(html).toContain('aria-label="失败"');
  });

  it("进行中态：processing+加载图标", () => {
    const html = renderToString(<ToolCallCard step={{ name: "wp_run_calc", ok: null }} />);
    expect(html).toContain('aria-label="进行中"');
  });
});
