/**
 * 批量任务状态行（B5 D3 增补——deepseek 体验质疑采纳）：导出按钮旁常驻
 * 「最近一次批量任务」回溯行（toast 瞬态呈现+本行回溯=进度可视化闭环）。
 *
 * 输入:  kind（批量导出 kind 面——useExportBatch 工厂参）+progress（进度
 *        视图——null=无在途）+lastOutcome（最近终态——null=在途中/从未提交）
 * 输出:  单行 Typography.Text 三态（进行中 percent·i/N｜完成 N 项｜失败
 *        kind·unit·原因；取消=已产计数行）或 null；文案派生零内联=
 *        useExportBatch.batchStatusText 单源（antd 组件 node 不可直调——
 *        纯逻辑直测先例，本件薄壳不测）
 *
 * 规格说明（B5 批量任务体验批 D3）：
 *   - 常驻面：新提交清空 lastOutcome（hook 内）→行回「进行中」，终态双
 *     路径（SSE finish/GET 快路径）回填；卸载重挂两态皆 null=零渲染；
 *   - 色调：进行中 secondary/完成 success/失败 danger/取消 secondary
 *     （antd Typography type 面映射——TaskPanel STATE_LABELS 先例形态）。
 */
import { Typography } from "antd";

import {
  batchStatusText,
  type ExportBatchOutcome,
  type ExportBatchProgress,
} from "../api/useExportBatch";

/** 终态→Typography 色（进行中恒 secondary；映射面归组件——文案真源在 lib 侧）。 */
function outcomeTone(outcome: ExportBatchOutcome): "success" | "danger" | "secondary" {
  if (outcome.state === "failed") {
    return "danger";
  }
  return outcome.state === "done" ? "success" : "secondary";
}

export function BatchStatusLine({
  kind,
  progress,
  lastOutcome,
}: {
  kind: string;
  progress: ExportBatchProgress | null;
  lastOutcome: ExportBatchOutcome | null;
}) {
  const text = batchStatusText(kind, progress, lastOutcome);
  if (text === null) {
    return null; // 从未提交/在途首事件前——零渲染
  }
  return (
    <Typography.Text type={lastOutcome === null ? "secondary" : outcomeTone(lastOutcome)}>
      {text}
    </Typography.Text>
  );
}
