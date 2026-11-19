/**
 * v4 计算说明区（B6 计算说明批段3 2026-10-09——左导航 190px 两级数据
 * 驱动〔sections〕+右阅读卡〔react-markdown+KaTeX——reportDoc〕+导出
 * 语境区三钮；b4 功能面重涂 II 批 2026-11-19 稿 deliverables.html 阅读
 * 面重制：稿纸幅 760px+衬线标题〔reportDoc〕+居中元信息行+导出三钮
 * 下载动词形〔拆件 reportExports——行数预算〕；wireframe-d-v4 屏 6 形
 * →稿 .report-paper 形）。
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
 *     API 句式不入用户面）；
 *   - 左导航三态去重为局部 ReportNav 组件（v2 笔2：无项目/错误/数据三
 *     态同形 aside——拖宽 usePaneWidth 默认 190/140~420/键 wp-v4-report
 *     -left-w；data-region="report-nav" 与既有 testid 语义原样保持）。
 */
import { useEffect, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useProjectId } from "../useProjectId";
import { rawProjectName } from "../useProjectName";
import { ReportDoc, type ReportSection } from "./reportDoc";
import { usePaneWidth } from "./usePaneWidth";
import { ExportContextRow } from "./reportExports";
export { exportFailText, type ReportExportKind } from "./reportExports";
import {
  useGetProjectReportApiCalcProjectsProjectIdReportGet,
  useRunCalculationApiCalcRunPost,
} from "../../shared/api/generated/calc/calc";
import { useReadProjectApiProjectsProjectIdGet } from "../../shared/api/generated/projects/projects";
import { domainGate } from "../../shared/api/sourceGate";
import { TASK_EVENT } from "../../shared/events";
import { writeTaskParam } from "../solutionsUrlState";

/** 空态/横幅文案（白名单：空态引导/stale 原因——B1 壳语义沿承）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「项目」区打开或新建";
const NO_CALC_TEXT = "计算说明在完成计算后生成";
const STALE_TEXT = "说明书已过期（参数已变更）——重算后更新";
const LOADING_TEXT = "正在加载计算说明…";

/** V4 P5：尾部 id 括注（服务端 Section title=「单元名（unit_id）」形〔core
 *  report build.py Section title f 串〕）——显示面剥除，title 悬浮全称归
 *  消费面。d1-W2 收紧：仅剥**小写起首标识形** [a-z][A-Za-z0-9_]*（unit_id
 *  契约域 GR-26 小写蛇形——inlet/municipal_aao/design_offline_x 命中；
 *  CODcr/BOD5/SS/大写单字母=有效限定词不剥）；全/半角括号对均可；中段
 *  括注/中文括注不动。d1-N6：剥后空串（全括注标题）回退原串渲染。 */
const ID_PARENTHETICAL_RE = /[（(]([a-z][A-Za-z0-9_]*)[)）]\s*$/;

/** 剥尾部 id 括注（纯函数——无括注/非标识形/中文括注/剥后空串均原样返回）。 */
export function stripIdParenthetical(title: string): string {
  const match = title.match(ID_PARENTHETICAL_RE);
  if (match === null) {
    return title;
  }
  const stripped = title.slice(0, match.index).trimEnd();
  return stripped === "" ? title : stripped; // d1-N6：禁不可见导航条目
}

/** 左导航 aside（v2 笔2：三态 nav 去重为局部组件——拖宽 hook+柄+
 *  「说明书导航」头；children=章按钮（数据态）/空（无项目/错误态）。
 *  data-region="report-nav" 与既有 testid 语义原样保持）。 */
function ReportNav({ children }: { children?: ReactNode }) {
  // 左导航栏宽+拖宽（默认 190/140~420/键 wp-v4-report-left-w）
  const pane = usePaneWidth({
    key: "wp-v4-report-left-w",
    fallback: 190,
    min: 140,
    max: 420,
    side: "left",
  });
  return (
    <aside
      className="wp-v4-sider"
      data-region="report-nav"
      style={{
        width: pane.width,
        flex: "none",
        background: "var(--wp-bg-container)",
        borderRight: "1px solid var(--wp-border-2)",
        padding: "6px 4px",
        // 回炉 R1：overflow auto 双轴下 3px 幻影横滚（舍入/纵滚条互作——
        // 子元素无实外溢实测在档）→ 横轴裁剪、纵滚保留
        overflowY: "auto",
        overflowX: "hidden",
      }}
    >
      <div
        className="wp-v4-drag"
        data-testid="wp-v4-drag-report-left"
        title="拖拽调整宽度"
        onPointerDown={pane.onDragStart}
      >
        ⟷
      </div>
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
      {children}
    </aside>
  );
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
        color: "var(--wp-warning)",
        background: "var(--wp-warning-soft, rgba(138, 97, 0, 0.08))",
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
          background: "var(--wp-bg-container)",
          color: "var(--wp-accent)",
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
        <ReportNav />
        <div
          data-testid={gate.domain ? "wp-v4-report-empty" : "wp-v4-report-error"}
          data-region="report-doc"
          style={{
            flex: 1,
            minWidth: 0,
            margin: "8px auto", // V3 D3：阅读卡三态同形居中（R1 C8 不变量沿承）
            padding: "32px 44px",
            maxWidth: 760,
            background: "var(--wp-bg-elevated)",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 6,
            color: "var(--wp-text-2)",
            fontSize: 12,
            // R1 C8（视觉回炉）：空态/错误态=卡内居中引导（LOADING 态同形）
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
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
      <ReportNav>
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            data-testid="wp-v4-report-nav-item"
            data-section-id={section.id}
            data-active={selectedId === section.id ? "true" : "false"}
            title={section.title}
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
                  ? "var(--wp-accent)"
                  : section.level === 1
                    ? "var(--wp-text)"
                    : "var(--wp-text-2)",
              padding:
                section.level === 1 ? "4px 8px" : "3px 8px 3px 22px", // 小节缩进（两级树）
              cursor: "pointer",
              // V4 P6：省略三件套+minWidth:0（长文不撑宽侧栏——scrollWidth
              // 守卫；条目全称经 title 悬浮）
              minWidth: 0,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {stripIdParenthetical(section.title)}
          </button>
        ))}
      </ReportNav>
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
            margin: "8px auto", // V3 D3：阅读卡居中沿承（b4 稿 .report-paper 幅面 760）
            padding: "32px 44px",
            maxWidth: 760, // b4 稿 deliverables.html .report-paper 稿纸幅
            background: "var(--wp-bg-elevated)",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 6,
          }}
        >
          <div
            data-testid="wp-v4-report-subline"
            style={{
              color: "var(--wp-text-2)",
              fontSize: 11,
              textAlign: "center",
              paddingBottom: 10,
              borderBottom: "1px solid var(--wp-border-2)",
              marginBottom: 14,
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
        <ReportNav />
        <div
          data-testid="wp-v4-report-empty"
          data-region="report-doc"
          style={{
            flex: 1,
            minWidth: 0,
            margin: "8px auto", // V3 D3：阅读卡三态同形居中（R1 C8 不变量沿承）
            padding: "32px 44px",
            maxWidth: 760,
            background: "var(--wp-bg-elevated)",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 6,
            color: "var(--wp-text-2)",
            fontSize: 12,
            // R1 C8（视觉回炉）：无项目空态同形收编（居中引导——卡面三态一致）
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {NO_PROJECT_HINT}
        </div>
      </section>
    );
  }
  return <ReportFace projectId={projectId} />;
}
