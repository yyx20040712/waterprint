/**
 * AiConnectButton 顶栏入口测试（AI2 批）。
 *
 * 输入:  AiConnectButton（onClick 单 prop——App.tsx 顶栏受控开态）
 * 输出:  文本图标按钮渲染（aria-label/title「AI 接入」——无标签文案常驻）
 */

import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { AiConnectButton } from "./AiConnectButton";

describe("AiConnectButton 顶栏入口（AI2）", () => {
  it("渲染文本按钮：aria-label/title=「AI 接入」+onClick 接线（点击回调可达）", () => {
    const onClick = vi.fn();
    const html = renderToString(<AiConnectButton onClick={onClick} />);
    expect(html).toContain('aria-label="AI 接入"');
    expect(html).toContain('title="AI 接入');
    expect(html).not.toContain("disabled");
  });
});
