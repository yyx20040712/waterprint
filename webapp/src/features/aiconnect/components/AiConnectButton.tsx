/**
 * AI 接入顶栏入口按钮（AI2 批）。
 *
 * 输入:  onClick（App.tsx 受控 Modal 开态回调——顶栏设置图标旁挂载）
 * 输出:  文本图标按钮（aria-label/title「AI 接入」——静默常驻零请求）
 */
import { ApiOutlined } from "@ant-design/icons";
import { Button } from "antd";

export function AiConnectButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      type="text"
      icon={<ApiOutlined />}
      onClick={onClick}
      aria-label="AI 接入"
      title="AI 接入（waterprint-mcp 一键连接）"
      data-testid="wp-ai-connect-open"
    />
  );
}
