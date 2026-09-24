/**
 * 工具步折叠卡（B4-4b 子批 2——社区基线：工具调用可见非裸 JSON）。
 *
 * 输入:  工具步 {name, ok}（历史消息 tool_steps 投影）
 * 输出:  单行状态卡（✓/✗+工具名——进行中态由 pane 传 ok=null）
 */
import { CheckCircleFilled, CloseCircleFilled, LoadingOutlined } from "@ant-design/icons";
import { Tag } from "antd";

export interface ToolStep {
  name: string;
  ok: boolean | null;
}

export function ToolCallCard({ step }: { step: ToolStep }) {
  const icon =
    step.ok === null ? (
      <LoadingOutlined aria-label="进行中" />
    ) : step.ok ? (
      <CheckCircleFilled aria-label="成功" />
    ) : (
      <CloseCircleFilled aria-label="失败" />
    );
  return (
    <Tag
      icon={icon}
      color={step.ok === null ? "processing" : step.ok ? "success" : "error"}
      style={{ margin: 2 }}
      data-testid={`wp-chat-tool-${step.name}`}
    >
      {step.name}
    </Tag>
  );
}
