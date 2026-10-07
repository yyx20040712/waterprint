/**
 * 方案研究子面（M6 批 2026-10-07 实装——studio.study 内容面：方案表段+
 * 联合结果段双段收编 solutions 族；沿革：M1 批 2026-10-06 立占位空态容器，
 * 本批实装）。
 *
 * 复刻源（权威底稿，git 锚）：
 *   - git show 54ba5c2139^:webapp/src/app/solutionsPane.tsx（M1 删除 495
 *     行——消费面复刻：双轨初值 L145-148/TASK_EVENT 监听 L173-186/切项目
 *     重置 L176-190/表源快照与挂载门 L228-249/深链回填 effect L251-266/
 *     solutionsQuery L268-278/handleApplied L318-326/applyGate 接线
 *     L349-358/render 段）；
 *   - git show 54ba5c2139^:webapp/src/app/jointSolutions.tsx L152-345
 *     （JointSolutionsSection 段——联合轨/任务门/sensitivity/窄化
 *     try-catch/jointNotice 三色/Card 渲染）。
 *
 * 三剔除（M1 分工纪律——本件只复刻消费面）：EnumerateBar 提交面+CP2 约束
 * 勾选面（Ribbon EnumerateModalBody 职责）+TaskPanel 进度面/SSE 连接态
 * （席位任务分页 M7 职责）+JointSubmitForm 提交条（Ribbon 联合枚举 Modal
 * 职责）——unitId 下拉态随提交面剔除（applyGateReason 传 unitId=null=
 * 「未选定不触发闸①」语义，applyGates 头注在案）。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook——S3 读方订阅）+?enum=（表
 *        源轨——枚举任务键）+?task=（联合轨——计算/联合任务键）+TASK_EVENT
 *        事件桥+useTaskFeed×2（SSE 终态自刷——useTaskEventSource 单源共享）
 *        +useReadProject 原始 GET 体（enumSource 四源窄化 raw 面）
 * 输出:  段A 方案浏览（单单元枚举——四挂载门+分页方案表+排序+三提示）+
 *        段B 联合枚举（方案比选——combos 表+三图 Tabs/任务态三色提示/
 *        载荷非法 fail-visible）；?task= 回写 replaceState（handleApplied）
 *
 * 规格说明（brief D1；分工=提交=Ribbon/进度=席位/结果=本件）：
 *   - 双轨非对称初值（旧 solutionsPane L145-148 同款）：表源轨
 *     enumerateTaskId=parseEnumParam ?? parseTaskParam（enum 键优先，缺省
 *     回落 task 键——旧深链兼容，kind 门自然滤 calc 任务）；联合轨
 *     jointTaskId=parseTaskParam（enum 键不读——旧 JointSolutionsSection
 *     制「双轨语义不混」）；
 *   - TASK_EVENT 监听×1（旧 L173-186+批6e W5 合流）：双轨重读（表源
 *     enum??task/联合 task）同值早退（函数式 set 零扰动）+invalidate 三键
 *     ——旧表源任务键/旧联合任务键（存在时）+sensitivity 键（终态后敏感
 *     性重取——comparePane 同款）；卸载移除监听；
 *   - useTaskFeed×2 终态自刷（表源/联合各一实例——不依赖席位挂载；仅消费
 *     终态回调 invalidate 本轨 status 键；联合实例追加 sensitivity 键失效
 *     〔批6e W5 复刻〕；视图/连接态零消费〔进度呈现归席位 M7 分工〕；
 *     **不派发 TASK_EVENT**〔席位 seatTaskPage 终态二段派发在案——禁双
 *     派发职责混淆，本件自监听经 URL 重读同值早退幂等〕；SSE 经
 *     useTaskEventSource 单源共享〔假设 A2——同 taskId 订阅同连接〕）；
 *   - 切项目重置（旧 L176-190 复刻）：双轨/固化单元/page/sort 全置
 *     null/初值（prevProject 初挂载同值早退保深链初值；URL 面由
 *     withProjectParam 剔除 enum/task 键）；
 *   - 段A 四挂载门（旧 L243-249 逐字口径）：enumerateDone（kind===
 *     "enumerate"&&state==="done"）/noSolutions（done+feasible_count=0）/
 *     payloadMissing（done 而 feasible_count 缺失——R7 防御）/tableEnabled
 *     （done+feasible>0）；solutionsQuery（enabled=tableEnabled，select=
 *     narrowSolutionPage，queryKey 含 {page,size,sort}——D9 复刻：page 1 基/
 *     PAGE_SIZE=50/sort 初值 margin_min）；应用闸=applyGates 纯函数（闸⓪①②
 *     禁用因+闸③漂移——unitsReady 面 GD-N-01）；深链回填 effect（旧
 *     L251-266 复刻裁剪：enumSource.resultUnitId 就绪且未固化且 task_id
 *     比对当前表源时回填 enumeratedUnitId——应用目标固化快照，R2 语义）；
 *   - handleApplied（旧 L318-326 裁剪）：writeTaskParam(recalc_task_id)+
 *     派发 TASK_EVENT——表源轨/enum 键/页码全不动（R1 已提交任务快照语义：
 *     方案表与旧行保留不卸载）；
 *   - 段B 任务门（旧 JointSolutionsSection 复刻）：jointDone（kind===
 *     "joint_enumerate"&&state==="done"）→窄化 try-catch（非法载荷→danger
 *     「联合枚举结果载荷非法：{message}」——error 呈现非静默）；非 done
 *     终态→jointTaskNotice 三色（failed danger/cancelled warning/其余
 *     secondary）；非 joint_enumerate kind/进行中→静默（进度在席位任务
 *     分页——M7 分工不重复呈现）；sensitivityQuery=useSensitivityQuery
 *     （404→data null 降级+isError→issue 透传——批6e k1-W2 口径）；
 *   - 空项目早退：「尚未选择项目——请先在画布槽选择项目」（studioPane D7
 *     措辞单源）；ErrorBoundary label="方案研究"（drawingsPane 族制）。
 */
import { useEffect, useRef, useState, type ReactElement } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, Typography } from "antd";

import {
  useGetSolutionsApiCalcTasksTaskIdSolutionsGet,
  useGetTaskStatusApiCalcTasksTaskIdGet,
} from "../shared/api/generated/calc/calc";
import type { ApplyOutcome } from "../shared/api/generated/model";
import { useReadProjectApiProjectsProjectIdGet } from "../shared/api/generated/projects/projects";
import { TASK_EVENT } from "../shared/events";
import { useProjectUnits } from "../features/solutions/api/useProjectUnits";
import { useTaskFeed } from "../features/solutions/api/useTaskFeed";
import { useSensitivityQuery } from "../features/solutions/api/useSensitivityQuery";
import { applyDriftWarn, applyGateReason, narrowEnumSource } from "../features/solutions/lib/applyGates";
import { narrowDimFields, narrowGridFields, resultField } from "../features/solutions/lib/solutionsFields";
import { jointTaskNotice } from "../features/solutions/lib/jointTaskNotice";
import { narrowJointResult } from "../features/solutions/lib/jointView";
import { RankingControls } from "../features/solutions/components/RankingControls";
import { SolutionsTable } from "../features/solutions/components/SolutionsTable";
import { JointSolutionsPanel } from "../features/solutions/components/JointSolutionsPanel";
import {
  narrowSolutionPage,
  type SolutionPageView,
} from "../features/solutions/lib/solutionsView";
import { SolutionsFetchError, SolutionsNotices } from "./solutionsNotices";
import { ErrorBoundary } from "./ErrorBoundary";
import { parseEnumParam, parseTaskParam } from "./projectParam";
import { useProjectId } from "./useProjectId";
import { writeTaskParam } from "./solutionsUrlState";

/** 空项目早退文案（studioPane D7 措辞单源——旧 solutionsPane 措辞退役）。 */
const NO_PROJECT_HINT = "尚未选择项目——请先在画布槽选择项目";

/** 表源轨空源引导（brief D1 逐字——提交入口=Ribbon「提交计算」命令带）。 */
const NO_ENUM_HINT =
  "暂无单单元枚举任务——提交入口在顶部「提交计算」命令带；完成后此处展示方案表（margin_min 降序）。";

/** 联合轨空源引导（brief D1 逐字——联合枚举提交=Ribbon Modal 承载）。 */
const NO_JOINT_HINT =
  "暂无联合枚举结果——提交入口在顶部「提交计算」命令带（联合枚举）；完成后此处展示方案比选表与三图。";

/** 分页大小（D9 复刻：50 固定——服务端分页默认 200 属全量面，浏览取 50）。 */
const PAGE_SIZE = 50;

export function StudyPane() {
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  // 双轨非对称初值（旧 solutionsPane L145-148 复刻——见头注规格段）
  const [enumerateTaskId, setEnumerateTaskId] = useState<string | null>(() =>
    parseEnumParam(window.location.search) ?? parseTaskParam(window.location.search),
  );
  const [jointTaskId, setJointTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search),
  );
  // R2：表源任务单元固化快照（应用目标——深链回填 effect 就绪后固化）
  const [enumeratedUnitId, setEnumeratedUnitId] = useState<string | null>(null);
  // D9 分页/sort 组件态（store 骨架占位维持——FE5 D2 先例）
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("margin_min");
  const queryClient = useQueryClient();
  const prevProject = useRef(projectId); // 切项目守卫（初挂载早退保深链初值）

  // TASK_EVENT 监听×1（旧 L173-186+批6e W5 合流——URL 单一真相双轨重读，
  // 同值早退零扰动；invalidate 三键=旧表源/联合任务键+sensitivity 键）
  useEffect(() => {
    const onTaskParam = () => {
      const nextEnum =
        parseEnumParam(window.location.search) ??
        parseTaskParam(window.location.search);
      const nextJoint = parseTaskParam(window.location.search);
      setEnumerateTaskId((prev) => (prev === nextEnum ? prev : nextEnum));
      setJointTaskId((prev) => (prev === nextJoint ? prev : nextJoint));
      if (enumerateTaskId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/tasks/${enumerateTaskId}`],
        });
      }
      if (jointTaskId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/tasks/${jointTaskId}`],
        });
      }
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/sensitivity/${projectId}`],
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [enumerateTaskId, jointTaskId, projectId, queryClient]);

  // 切项目重置（旧 L176-190 复刻——prevProject 初挂载同值早退保深链初值；
  // withProjectParam 已剔除 URL enum/task 键——双轨置 null 全重置）
  useEffect(() => {
    if (prevProject.current === projectId) return;
    prevProject.current = projectId;
    setEnumerateTaskId(null);
    setJointTaskId(null);
    setEnumeratedUnitId(null);
    setPage(1);
    setSort("margin_min");
  }, [projectId]);

  // useTaskFeed×2 终态自刷（视图/连接态零消费——进度呈现归席位 M7 分工；
  // 不派发 TASK_EVENT——席位 seatTaskPage 终态二段派发在案，禁双派发）
  useTaskFeed(enumerateTaskId, () => {
    if (enumerateTaskId !== null) {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/tasks/${enumerateTaskId}`],
      });
    }
  });
  useTaskFeed(jointTaskId, () => {
    if (jointTaskId !== null) {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/tasks/${jointTaskId}`],
      });
      if (projectId !== null) {
        // 批6e W5 复刻：联合终态后敏感性重取（stale 报告即时刷新）
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/sensitivity/${projectId}`],
        });
      }
    }
  });

  // 段A 数据面：表源轨快照（result 载荷/挂载门依据）
  const unitsQuery = useProjectUnits(projectId);
  // CP2 遗产 raw 面（enumSource 四源窄化——content_hash 漂移比对源；同键
  // 不带 select 的原始 GET 体缓存共享）
  const rawQuery = useReadProjectApiProjectsProjectIdGet(projectId ?? "", {
    query: { enabled: projectId !== null },
  });
  const tableStatusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(
    enumerateTaskId ?? "",
    { query: { enabled: enumerateTaskId !== null } },
  );
  const tableStatus = tableStatusQuery.data ?? null;
  const result = tableStatus?.result ?? null;
  const gridFields = narrowGridFields(result);
  const dimFields = narrowDimFields(result);
  const feasibleRaw = resultField(result, "feasible_count");
  const feasibleCount =
    typeof feasibleRaw === "number" && Number.isFinite(feasibleRaw)
      ? feasibleRaw
      : null;
  const diagnosis = resultField(result, "diagnosis");
  const enumSource = narrowEnumSource(result, rawQuery.data); // 四源窄化
  const enumerateDone =
    enumerateTaskId !== null &&
    tableStatus?.kind === "enumerate" &&
    tableStatus?.state === "done";
  const noSolutions = enumerateDone && feasibleCount === 0;
  // R7：done 而 feasible_count 缺失（result 载荷异形）——防御提示面
  const payloadMissing = enumerateDone && feasibleCount === null;
  const tableEnabled =
    enumerateDone && feasibleCount !== null && feasibleCount > 0;

  // 深链回填 effect（旧 L251-266 复刻裁剪）：result.unit_id 就绪且未固化
  // 且 task_id 比对当前表源时回填 enumeratedUnitId（应用目标固化快照；
  // 竞态守卫=task_id 比对——旧查询返回不回填新上下文双保险）
  useEffect(() => {
    const sourceUnitId = enumSource.resultUnitId;
    if (
      enumerateTaskId === null ||
      enumeratedUnitId !== null ||
      sourceUnitId === null ||
      tableStatus?.task_id !== enumerateTaskId
    ) {
      return;
    }
    setEnumeratedUnitId(sourceUnitId);
  }, [enumerateTaskId, enumeratedUnitId, enumSource.resultUnitId, tableStatus]);

  const solutionsQuery =
    useGetSolutionsApiCalcTasksTaskIdSolutionsGet<SolutionPageView, Error>(
      enumerateTaskId ?? "",
      { page, size: PAGE_SIZE, sort },
      {
        query: {
          enabled: tableEnabled,
          select: narrowSolutionPage,
        },
      },
    );

  // 段B 数据面：联合轨快照+sensitivity（批6e——404→data null 降级）
  const jointStatusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(
    jointTaskId ?? "",
    { query: { enabled: jointTaskId !== null } },
  );
  const jointStatus = jointStatusQuery.data ?? null;
  const jointDone =
    jointStatus?.kind === "joint_enumerate" && jointStatus?.state === "done";
  const sensitivityQuery = useSensitivityQuery(projectId);
  const sensitivity = sensitivityQuery.data ?? null;
  // 回炉 k1-W2 口径：404/损坏面详情透传（服务端 fail-loud 原因非折叠）
  const sensitivityIssue = sensitivityQuery.isError
    ? sensitivityQuery.error instanceof Error
      ? sensitivityQuery.error.message
      : "未知错误"
    : null;

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">
        {NO_PROJECT_HINT}
      </Typography.Paragraph>
    );
  }

  // 段A 应用闸接线（旧 L349-358 复刻——applyGates 纯函数；三剔除后无
  // EnumerateBar 下拉面：unitId 恒 null=「未选定不触发闸①」语义在案）
  const units = unitsQuery.data ?? [];
  const applyGateReasonValue = applyGateReason({
    projectId,
    resultProjectId: enumSource.resultProjectId,
    enumeratedUnitId,
    unitId: null,
    units,
    unitsReady: !unitsQuery.isLoading && !unitsQuery.isError, // GD-N-01
    tableEnabled,
  });
  const applyDriftWarnValue = applyDriftWarn(enumSource, tableEnabled);

  // R1（裁剪面）：方案应用只写 task 键+派发 TASK_EVENT——表源轨/enum 键/
  // 页码全不动（已提交任务快照语义：方案表与旧行保留不卸载）
  const handleApplied = (outcome: ApplyOutcome) => {
    writeTaskParam(outcome.recalc_task_id);
    window.dispatchEvent(
      new CustomEvent(TASK_EVENT, { detail: outcome.recalc_task_id }),
    );
  };

  // 段B 窄化门（旧 JointSolutionsSection 复刻——error 呈现非静默；
  // JointViewError message 带定位）
  let jointPanel: ReactElement | null = null;
  if (jointDone) {
    try {
      jointPanel = (
        <JointSolutionsPanel
          result={narrowJointResult(jointStatus?.result)}
          sensitivity={sensitivity}
          sensitivityIssue={sensitivityIssue}
        />
      );
    } catch (error) {
      jointPanel = (
        <Typography.Paragraph type="danger">
          联合枚举结果载荷非法：
          {error instanceof Error ? error.message : "未知错误"}
        </Typography.Paragraph>
      );
    }
  }
  // 批6f：非 done 终态文案分派（failed/cancelled/进度三色；done 态 null）
  const jointNotice =
    jointStatus !== null &&
    jointStatus.kind === "joint_enumerate" &&
    !jointDone
      ? jointTaskNotice(jointStatus)
      : null;

  return (
    <ErrorBoundary label="方案研究">
      <section data-testid="wp-study-pane">
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          方案浏览（单单元枚举——ADR-005）
        </Typography.Title>
        <div data-testid="wp-study-solutions">
          {enumerateTaskId === null ? (
            <Typography.Paragraph type="secondary">
              {NO_ENUM_HINT}
            </Typography.Paragraph>
          ) : null}
          <SolutionsNotices
            noSolutions={noSolutions}
            diagnosis={diagnosis}
            driftWarn={applyDriftWarnValue}
            payloadMissing={payloadMissing}
          />
          {tableEnabled && solutionsQuery.data ? (
            <div style={{ marginTop: 12 }}>
              <div style={{ marginBottom: 8 }}>
                <RankingControls
                  columns={solutionsQuery.data.columns}
                  gridFields={gridFields}
                  value={sort}
                  onChange={(next) => {
                    setSort(next);
                    setPage(1); // sort 切换重置页码（D9）
                  }}
                />
              </div>
              <SolutionsTable
                page={solutionsQuery.data}
                gridFields={gridFields}
                dimFields={dimFields}
                projectId={projectId}
                unitId={enumeratedUnitId}
                applyGateReason={applyGateReasonValue}
                applyDriftWarn={applyDriftWarnValue}
                currentPage={page}
                onPageChange={setPage}
                onApplied={handleApplied}
              />
            </div>
          ) : null}
          {solutionsQuery.isError ? (
            <SolutionsFetchError
              error={solutionsQuery.error}
              isError={solutionsQuery.isError}
            />
          ) : null}
        </div>
        <div data-testid="wp-study-joint">
          <Card
            size="small"
            title="联合枚举（方案比选——多单元组合）"
            style={{ marginTop: 12 }}
          >
            {jointTaskId === null ? (
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {NO_JOINT_HINT}
              </Typography.Paragraph>
            ) : null}
            {jointNotice !== null ? (
              <Typography.Paragraph
                type={
                  jointNotice.kind === "failed"
                    ? "danger"
                    : jointNotice.kind === "cancelled"
                      ? "warning"
                      : "secondary"
                }
                style={{ marginBottom: 0 }}
              >
                {jointNotice.text}
              </Typography.Paragraph>
            ) : null}
            {jointPanel}
          </Card>
        </div>
      </section>
    </ErrorBoundary>
  );
}
