/**
 * v4 计算说明区（B6 计算说明批段3 2026-10-09——B1 空态壳实装化：左导航
 * 190px 两级数据驱动〔sections〕+右阅读卡 max-width 640px〔react-markdown
 * +KaTeX——reportDoc〕+导出语境区三钮；wireframe-d-v4 屏 6 形）。
 *
 * 输入:  useProjectId（项目单一真相）+useGetProjectReportApiCalcProjects
 *        ProjectIdReportGet（?condition_key=design——markdown+sections 两级
 *        索引+stale/design_hash/generated_from）+useReadProjectApiProjects
 *        ProjectIdGet（卡头副行项目名）+useExportArtifact 三 kind（calcbook/
 *        audit/report_pdf——features/drawings 既有下载通道复用）
 * 输出:  report 区：report-nav（章 level=1+小节 level=2 缩进+选中 AC 着色
 *        +点击滚动定位）+report-export（语境区三钮——任务条/消息面沿仓
 *        惯例）+report-doc（卡头副行=项目名·数据集 R-{digest10}·生成于
 *        最近完成计算+stale 横幅+md 正文）+空态三面（无项目/无完成计算
 *        〔B1 壳文案语义〕/取数失败）
 *
 * 规格说明（B6 任务书 §一.4/§二.⑤——视觉基线 wireframe 屏 6）：
 *   - NAV_SECTIONS 硬编码退役（B1 壳）——导航=sections 数据驱动（章号
 *     前缀不前端伪造：sections.title 真源直出，正文 heading 呈现章号面）；
 *   - 空态/错误文案白名单：B1 壳文案语义沿承+取数失败原文透出（B2 同形）；
 *   - stale=提示性横幅（B2 analysisPane 同形——原因微文案+重算入口直发
 *     run+TASK_EVENT 派发；TASK_EVENT 事件桥失效报告键——重算完成后回看）；
 *   - 导出：calcbook（design 工况）/audit（condition_key 空——全厂单份
 *     跨工况，服务端 422 闸对齐）/report_pdf（design 缺省归一）；unitId
 *     空串=bare POST 全厂整厂语义；409 stale=二选一 force 支线沿仓惯例；
 *   - 404 无完成计算=空态（ReportSourceNotFoundError 领域码门控——raw
 *     API 句式不入用户面）。
 */
import { useEffect, useState } from "react";
import { Modal, message } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { useProjectId } from "../useProjectId";
import { ReportDoc, type ReportSection } from "./reportDoc";
import { useExportArtifact } from "../../features/drawings/api/useExportArtifact";
import {
  useGetProjectReportApiCalcProjectsProjectIdReportGet,
  useRunCalculationApiCalcRunPost,
} from "../../shared/api/generated/calc/calc";
import { useReadProjectApiProjectsProjectIdGet } from "../../shared/api/generated/projects/projects";
import { WaterprintApiError } from "../../shared/api/http";
import { domainGate } from "../../shared/api/sourceGate";
import { TASK_EVENT } from "../../shared/events";
import { writeTaskParam } from "../solutionsUrlState";

/** 空态/横幅文案（白名单：空态引导/stale 原因——B1 壳语义沿承）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「项目」区打开或新建";
const NO_CALC_TEXT = "计算说明在完成计算后生成";
const STALE_TEXT = "说明书已过期（参数已变更）——重算后更新";
const LOADING_TEXT = "正在加载计算说明…";

/** 导出语境区三钮（label=白名单微文案——wireframe 屏 6 注记「计算书
 *  xlsx/审计 HTML」+B6 增 PDF 计算书）。 */
const REPORT_EXPORTS = [
  { kind: "calcbook", label: "计算书 xlsx", testid: "wp-v4-report-export-calcbook" },
  { kind: "audit", label: "审计 HTML", testid: "wp-v4-report-export-audit" },
  { kind: "report_pdf", label: "PDF 计算书", testid: "wp-v4-report-export-pdf" },
] as const;

/** 导出 kind 三值（useExportArtifact 泛化通道——既有 POST /api/exports/{kind}）。 */
export type ReportExportKind = (typeof REPORT_EXPORTS)[number]["kind"];

/** 各 kind 的工况载荷（audit 空=全厂单份跨工况；其余随报告工况 design）。 */
const EXPORT_CONDITION: Record<ReportExportKind, string> = {
  calcbook: "design",
  audit: "",
  report_pdf: "design",
};

/** raw 项目读宽容取项目名（zoneBand rawCheckedUnits 同款形态）。 */
function rawProjectName(raw: unknown): string | null {
  if (typeof raw !== "object" || raw === null) {
    return null;
  }
  const view = (raw as Record<string, unknown>)["view"];
  if (typeof view !== "object" || view === null) {
    return null;
  }
  const name = (view as Record<string, unknown>)["name"];
  return typeof name === "string" && name.trim() ? name.trim() : null;
}

/** 导出失败文案（纯函数——PDF 面显式「PDF 计算书导出失败」前缀；404=
 *  domainGate 固定摘要+先提交计算引导，raw API 句式不入用户面）。 */
export function exportFailText(kind: ReportExportKind, error: unknown): string {
  const label = REPORT_EXPORTS.find((row) => row.kind === kind)?.label ?? kind;
  const gate = domainGate(
    error,
    "ExportSourceNotFoundError",
    "项目暂无完成的计算结果",
  );
  const reason = gate.domain ? `${gate.text}——先提交计算后再导出` : gate.text;
  return `${label}导出失败：${reason}`;
}

/** stale 横幅（B2 analysisPane 同形——原因微文案+重算入口直发 run）。 */
function StaleBanner({ projectId }: { projectId: string }) {
  const run = useRunCalculationApiCalcRunPost();
  return (
    <div
      data-testid="wp-v4-report-stale"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        fontSize: 11,
        color: "var(--wpv4-warn)",
        background: "var(--wpv4-warn-bg, rgba(138, 97, 0, 0.08))",
        border: "1px solid var(--wp-border-2)",
        borderRadius: 6,
        padding: "4px 10px",
        marginBottom: 8,
      }}
    >
      <span>{STALE_TEXT}</span>
      <button
        type="button"
        data-testid="wp-v4-report-rerun"
        disabled={run.isPending}
        onClick={() =>
          run.mutate(
            { data: { project_id: projectId, conditions: [] } },
            {
              onSuccess: (outcome) => {
                writeTaskParam(outcome.task_id);
                window.dispatchEvent(
                  new CustomEvent(TASK_EVENT, { detail: outcome.task_id }),
                );
              },
            },
          )
        }
        style={{
          border: "1px solid var(--wp-border)",
          borderRadius: 4,
          background: "var(--wp-bg-container, #ffffff)",
          color: "var(--wpv4-ac)",
          fontSize: 11,
          padding: "1px 8px",
          cursor: run.isPending ? "default" : "pointer",
        }}
      >
        重算
      </button>
    </div>
  );
}

/** 导出语境区（三钮——下载反馈沿仓惯例：成功 message+409 二选一 force
 *  支线〔surfaceExportError 同语义本地面——该 lib kind 域钉 dxf|ifc〕）。 */
function ExportContextRow({ projectId }: { projectId: string }) {
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
        padding: "6px 10px",
        borderBottom: "1px solid var(--wp-border-2)",
        background: "var(--wp-bg-container)",
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
          style={{
            border: "1px solid var(--wp-border)",
            borderRadius: 4,
            background: "var(--wp-bg-elevated)",
            color: "var(--wp-text)",
            fontSize: 11,
            padding: "1px 8px",
            cursor: mutations[row.kind].isPending ? "default" : "pointer",
          }}
        >
          {row.label}
        </button>
      ))}
    </div>
  );
}

/** 有项目态（数据面——导航+阅读卡+导出语境区）。 */
function ReportFace({ projectId }: { projectId: string }) {
  const query = useGetProjectReportApiCalcProjectsProjectIdReportGet(projectId, {
    condition_key: "design",
  });
  const projectQuery = useReadProjectApiProjectsProjectIdGet(projectId);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  // TASK_EVENT 事件桥（B2 同制——apply/重算后报告键失效，完成回看即新件）
  const queryClient = useQueryClient();
  useEffect(() => {
    const onTaskParam = () => {
      void queryClient.invalidateQueries({
        predicate: (target) =>
          target.queryKey[0] === `/api/calc/projects/${projectId}/report`,
      });
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  if (query.isError) {
    const gate = domainGate(
      query.error,
      "ReportSourceNotFoundError",
      NO_CALC_TEXT,
    );
    return (
      <section style={{ flex: 1, minWidth: 0, display: "flex" }}>
        <aside
          data-region="report-nav"
          style={{
            width: 190,
            flex: "none",
            background: "var(--wp-bg-container)",
            borderRight: "1px solid var(--wp-border-2)",
            padding: "6px 4px",
            overflow: "auto",
          }}
        >
          <div
            style={{
              fontSize: 11,
              color: "var(--wp-text-2)",
              letterSpacing: 1,
              padding: "4px 8px 6px",
            }}
          >
            说明书导航
          </div>
        </aside>
        <div
          data-testid={gate.domain ? "wp-v4-report-empty" : "wp-v4-report-error"}
          data-region="report-doc"
          style={{
            flex: 1,
            minWidth: 0,
            margin: 8,
            padding: "20px 26px",
            maxWidth: 640,
            background: "#ffffff",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 6,
            color: "var(--wp-text-2)",
            fontSize: 12,
          }}
        >
          {gate.domain
            ? NO_CALC_TEXT
            : `取数失败：${gate.text}`}
        </div>
      </section>
    );
  }
  const report = query.data ?? null;
  if (report === null) {
    return (
      <section style={{ flex: 1, minWidth: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--wp-text-2)" }}>
        {LOADING_TEXT}
      </section>
    );
  }
  const sections = report.sections as readonly ReportSection[];
  const projectName =
    rawProjectName(projectQuery.data) ?? projectId.slice(0, 10);
  return (
    <section style={{ flex: 1, minWidth: 0, display: "flex" }}>
      <aside
        data-region="report-nav"
        style={{
          width: 190,
          flex: "none",
          background: "var(--wp-bg-container)",
          borderRight: "1px solid var(--wp-border-2)",
          padding: "6px 4px",
          overflow: "auto",
        }}
      >
        <div
          style={{
            fontSize: 11,
            color: "var(--wp-text-2)",
            letterSpacing: 1,
            padding: "4px 8px 6px",
          }}
        >
          说明书导航
        </div>
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            data-testid="wp-v4-report-nav-item"
            data-section-id={section.id}
            data-active={selectedId === section.id ? "true" : "false"}
            onClick={() => {
              setSelectedId(section.id);
              document.getElementById(section.id)?.scrollIntoView({
                block: "start",
              });
            }}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              border: "none",
              background: "transparent",
              fontSize: section.level === 1 ? 12 : 11, // 字号归一三档（章 12/小节 11）
              color:
                selectedId === section.id
                  ? "var(--wpv4-ac)"
                  : section.level === 1
                    ? "var(--wp-text)"
                    : "var(--wp-text-2)",
              padding:
                section.level === 1 ? "4px 8px" : "3px 8px 3px 22px", // 小节缩进（两级树）
              cursor: "pointer",
            }}
          >
            {section.title}
          </button>
        ))}
      </aside>
      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
        }}
      >
        <ExportContextRow projectId={projectId} />
        <div
          data-region="report-doc"
          style={{
            flex: "none",
            margin: 8,
            padding: "20px 26px",
            maxWidth: 640, // wireframe 屏 6：阅读卡 max-width 640px
            background: "#ffffff",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 6,
          }}
        >
          <div
            data-testid="wp-v4-report-subline"
            style={{
              color: "var(--wp-text-2)",
              fontSize: 11,
              paddingBottom: 10,
              borderBottom: "1px solid var(--wp-border-2)",
              marginBottom: 10,
            }}
          >
            {projectName} · 数据集 R-{report.generated_from.digest10} · 生成于最近完成计算
          </div>
          {report.stale ? <StaleBanner projectId={projectId} /> : null}
          <ReportDoc markdown={report.markdown} sections={sections} />
        </div>
      </div>
    </section>
  );
}

export function ReportZone() {
  const [projectId] = useProjectId();
  if (projectId === null) {
    return (
      <section style={{ flex: 1, minWidth: 0, display: "flex" }}>
        <aside
          data-region="report-nav"
          style={{
            width: 190,
            flex: "none",
            background: "var(--wp-bg-container)",
            borderRight: "1px solid var(--wp-border-2)",
            padding: "6px 4px",
            overflow: "auto",
          }}
        >
          <div
            style={{
              fontSize: 11,
              color: "var(--wp-text-2)",
              letterSpacing: 1,
              padding: "4px 8px 6px",
            }}
          >
            说明书导航
          </div>
        </aside>
        <div
          data-testid="wp-v4-report-empty"
          data-region="report-doc"
          style={{
            flex: 1,
            minWidth: 0,
            margin: 8,
            padding: "20px 26px",
            maxWidth: 640,
            background: "#ffffff",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 6,
            color: "var(--wp-text-2)",
            fontSize: 12,
          }}
        >
          {NO_PROJECT_HINT}
        </div>
      </section>
    );
  }
  return <ReportFace projectId={projectId} />;
}
