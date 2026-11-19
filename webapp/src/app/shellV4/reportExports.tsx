/**
 * 计算说明导出区（b4 功能面重涂 II 批 2026-11-19 自 reportZone 拆件
 * 〔行数预算〕——稿 deliverables.html 导出操作形：三钮〔下载形图标+
 * 导出前缀标签〕+409 二选一 force 支线+失败白名单文案；useExportArtifact
 * 既有下载通道零改）。
 *
 * 输入:  projectId+useExportArtifact 三 kind（calcbook/audit/report_pdf
 *        ——features/drawings 既有通道）
 * 输出:  ExportContextRow（语境行：区块标题+三导出钮——calcbook 主色
 *        主钮）+exportFailText（失败文案纯函数——404=domainGate 固定
 *        摘要+先提交计算引导）+REPORT_EXPORTS/ReportExportKind/
 *        EXPORT_CONDITION（kind 域与工况载荷单源）
 *
 * 规格说明（B6 §一.4 沿承+b4 稿标签更新；409 stale=二选一 force 支线
 *   沿仓惯例——仍导出旧结果或先重算）：
 *   - 按钮标签=稿 deliverables.html（导出计算书 XLSX/导出审计包/导出
 *     PDF 计算书——下载动词前缀形）；失败消息面=failLabel 短名（「PDF
 *     计算书导出失败」前缀语义沿承不变）；
 *   - audit 空 condition_key=全厂单份跨工况（服务端 422 闸对齐）；
 *   - useExportArtifact 泛化通道 POST /api/exports/{kind} 零改。
 */
import { Modal, message } from "antd";

import { useExportArtifact } from "../../features/drawings/api/useExportArtifact";
import { WaterprintApiError } from "../../shared/api/http";
import { domainGate } from "../../shared/api/sourceGate";

/** 导出语境区三钮（label=按钮文案〔稿导出前缀形〕；failLabel=失败消息短名）。 */
export const REPORT_EXPORTS = [
  {
    kind: "calcbook",
    label: "导出计算书 XLSX",
    failLabel: "计算书 XLSX",
    testid: "wp-v4-report-export-calcbook",
  },
  {
    kind: "audit",
    label: "导出审计包",
    failLabel: "审计包",
    testid: "wp-v4-report-export-audit",
  },
  {
    kind: "report_pdf",
    label: "导出 PDF 计算书",
    failLabel: "PDF 计算书",
    testid: "wp-v4-report-export-pdf",
  },
] as const;

/** 导出 kind 三值（useExportArtifact 泛化通道——既有 POST /api/exports/{kind}）。 */
export type ReportExportKind = (typeof REPORT_EXPORTS)[number]["kind"];

/** 各 kind 的工况载荷（audit 空=全厂单份跨工况；其余随报告工况 design）。 */
export const EXPORT_CONDITION: Record<ReportExportKind, string> = {
  calcbook: "design",
  audit: "",
  report_pdf: "design",
};

/** 导出失败文案（纯函数——PDF 面显式「PDF 计算书导出失败」前缀；404=
 *  domainGate 固定摘要+先提交计算引导，raw API 句式不入用户面）。 */
export function exportFailText(kind: ReportExportKind, error: unknown): string {
  const row = REPORT_EXPORTS.find((item) => item.kind === kind);
  const failLabel = row?.failLabel ?? kind;
  const gate = domainGate(
    error,
    "ExportSourceNotFoundError",
    "项目暂无完成的计算结果",
  );
  const reason = gate.domain ? `${gate.text}——先提交计算后再导出` : gate.text;
  return `${failLabel}导出失败：${reason}`;
}

/** 导出语境区（三钮——下载反馈沿仓惯例：成功 message+409 二选一 force
 *  支线〔仍导出旧结果或先重算——静默弱化禁〕；b4：calcbook 主色主钮
 *  消费 --wp-on-accent 轴文字）。 */
export function ExportContextRow({ projectId }: { projectId: string }) {
  const calcbook = useExportArtifact("calcbook");
  const audit = useExportArtifact("audit");
  const reportPdf = useExportArtifact("report_pdf");
  const [messageApi, contextHolder] = message.useMessage();
  const mutations = { calcbook, audit, report_pdf: reportPdf };

  const submitExport = (kind: ReportExportKind, force: boolean) => {
    mutations[kind].mutate(
      { projectId, unitId: "", conditionKey: EXPORT_CONDITION[kind], force },
      {
        onSuccess: (outcome) => {
          messageApi.success(`已导出：${outcome.fileName}`);
        },
        onError: (error) => {
          // 409 stale=二选一（仍导出旧结果 force）——静默弱化禁
          if (
            error instanceof WaterprintApiError &&
            error.code === "StaleExportError"
          ) {
            Modal.confirm({
              title: "结果集已过期（stale）",
              content: error.message,
              okText: "仍导出旧结果（force）",
              cancelText: "先重算",
              onOk: () => {
                submitExport(kind, true);
              },
            });
            return;
          }
          messageApi.error(exportFailText(kind, error));
        },
      },
    );
  };

  return (
    <div
      data-region="report-export"
      style={{
        flex: "none",
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 12px",
        borderBottom: "1px solid var(--wp-border-2)",
        background: "var(--wp-bg-container)",
        flexWrap: "wrap",
      }}
    >
      {contextHolder}
      <span style={{ fontSize: 11, color: "var(--wp-text-2)", letterSpacing: 1 }}>
        计算说明书 · 导出
      </span>
      {REPORT_EXPORTS.map((row) => (
        <button
          key={row.kind}
          type="button"
          data-testid={row.testid}
          disabled={mutations[row.kind].isPending}
          onClick={() => submitExport(row.kind, false)}
          style={
            row.kind === "calcbook"
              ? {
                  // V3 D3 沿承：主钮主色化（AC 底+on-accent 文字+同色描边）
                  border: "1px solid var(--wp-accent)",
                  borderRadius: 4,
                  background: "var(--wp-accent)",
                  color: "var(--wp-on-accent)",
                  fontSize: 11,
                  padding: "2px 10px",
                  cursor: mutations[row.kind].isPending ? "default" : "pointer",
                }
              : {
                  border: "1px solid var(--wp-border)",
                  borderRadius: 4,
                  background: "var(--wp-bg-elevated)",
                  color: "var(--wp-text)",
                  fontSize: 11,
                  padding: "2px 10px",
                  cursor: mutations[row.kind].isPending ? "default" : "pointer",
                }
          }
        >
          {row.label}
        </button>
      ))}
    </div>
  );
}
