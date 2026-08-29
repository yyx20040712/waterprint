/**
 * solutions 标签页装配：?project=/?task= 双参消费+单单元枚举提交+任务态
 * 面板+方案表+排序控件组合（D8 组合面——app 层唯一 features 组合层）。
 *
 * 输入:  URL ?project=（与 canvas/viewer3d 共用）+?task=（任务 id 单一
 *        真相——D3）+useProjectUnits 单元清单+SSE 任务流+TaskStatus 快照
 * 输出:  方案浏览标签页（单元下拉+「提交枚举」+TaskPanel+RankingControls
 *        +SolutionsTable/DiagnosisPanel；?task= 回写 replaceState）
 *
 * 规格说明（FE6 批 6b 段四，D1/D3/D8/D9；canvasPane/viewer3dPane 同构）：
 *   - 任务 id 单一真相=URL ?task=（与 ?project= 双参共存）：初值
 *     parseTaskParam 直读；写入三面=枚举提交 onSuccess（task_id）/方案
 *     应用 onApplied（recalc_task_id——任务态面板转向重算任务，表数据
 *     为已提交任务快照不自动刷新）/ParamForm apply（FE5 挂账③收口——
 *     params 侧内联回写）；全走 window.history.replaceState（FE3 先例
 *     不触发导航不抢焦点——跨标签自动跳转挂账 UX 批）；
 *   - D8 枚举提交面：单元下拉（useProjectUnits——design.nodes 投影）
 *     +useRunEnumeration（body={project_id, unit_ids:[unitId], options:
 *     null}——options 默认 margin_min 降序，constraints 空槽挂账）；
 *     提交/应用后 page 重置 1；
 *   - 任务态双源：useTaskFeed（SSE 进度）+useGetTaskStatus（终态 invalidate
 *     重拉——result 载荷 columns/grid_fields/feasible_count/diagnosis 与
 *     failed 三件详情源）；表挂载=kind==='enumerate'&&state==='done'&&
 *     feasible_count>0；无解=done+feasible_count=0→DiagnosisPanel（合法
 *     终态非 failed）；calc 重算任务（apply/参数提交触发）只挂 TaskPanel
 *     （进度+失败回显——409 面由 enabled 防住：非 done 不取表）；
 *   - D9 分页/sort 组件态（useState——不建 store FE5 D2 先例；store 骨架
 *     占位维持）：page 1 基/size=50 固定/sort 初值 margin_min；queryKey
 *     [taskId, {page,size,sort}] 全量进（排序确定性）；select=
 *     narrowSolutionPage 窄化收口（非法形状→查询 error 态呈现）；
 *   - Select 不用占位文案属性（grep 门禁英文占位特征词命中该 prop 名
 *     ——FE3 C3 同款规避）；deep-link 直进 ?task= 而单元未选定时应用
 *     按钮禁用（任务 result 载荷无 unit_id 面注记）；
 *   - 空态：?project= 缺失=指引文案（先在工艺画布标签选择项目——项目
 *     选择器不重复建，挂账 UX 批）；ErrorBoundary label=方案浏览。
 */
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Select, Typography } from "antd";

import {
  useGetSolutionsApiCalcTasksTaskIdSolutionsGet,
  useGetTaskStatusApiCalcTasksTaskIdGet,
  useRunEnumerationApiCalcEnumeratePost,
} from "../shared/api/generated/calc/calc";
import type { ApplyOutcome } from "../shared/api/generated/model";
import { WaterprintApiError } from "../shared/api/http";
import { useProjectUnits } from "../features/solutions/api/useProjectUnits";
import { useTaskFeed } from "../features/solutions/api/useTaskFeed";
import { DiagnosisPanel } from "../features/solutions/components/DiagnosisPanel";
import { RankingControls } from "../features/solutions/components/RankingControls";
import { SolutionsTable } from "../features/solutions/components/SolutionsTable";
import { TaskPanel } from "../features/solutions/components/TaskPanel";
import {
  narrowSolutionPage,
  type SolutionPageView,
} from "../features/solutions/lib/solutionsView";
import { ErrorBoundary } from "./ErrorBoundary";
import {
  normalizeProjectId,
  parseProjectParam,
  parseTaskParam,
  withTaskParam,
} from "./projectParam";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——方案枚举针对项目内单元提交。";

/** 分页大小（D9：50 固定——服务端分页默认 200 属全量面，浏览取 50）。 */
const PAGE_SIZE = 50;

/** result 载荷字段窄化（弱类型 Mapping——app 层内联，薄壳不测面）。 */
function resultField(result: unknown, key: string): unknown {
  if (typeof result !== "object" || result === null) {
    return null;
  }
  return (result as Record<string, unknown>)[key] ?? null;
}

/** grid_fields 窄化（string[] 形状非法→空——表挂载仍可无应用列）。 */
function narrowGridFields(result: unknown): string[] {
  const value = resultField(result, "grid_fields");
  return Array.isArray(value) && value.every((f) => typeof f === "string")
    ? (value as string[])
    : [];
}

export function SolutionsPane() {
  const [projectId] = useState<string | null>(() =>
    normalizeProjectId(parseProjectParam(window.location.search)),
  );
  // 任务 id 单一真相=URL ?task=（D3——初值直读+提交/应用回写 replaceState）
  const [taskId, setTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search),
  );
  const [unitId, setUnitId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("margin_min");
  const queryClient = useQueryClient();
  const unitsQuery = useProjectUnits(projectId);

  // SSE 进度流：终态回调→失效任务快照（拉 result 载荷+failed 三件详情）
  const view = useTaskFeed(taskId, () => {
    if (taskId !== null) {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/tasks/${taskId}`],
      });
    }
  });
  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(taskId ?? "", {
    query: { enabled: taskId !== null },
  });
  const status = statusQuery.data ?? null;
  const result = status?.result ?? null;
  const gridFields = narrowGridFields(result);
  const feasibleRaw = resultField(result, "feasible_count");
  const feasibleCount =
    typeof feasibleRaw === "number" && Number.isFinite(feasibleRaw)
      ? feasibleRaw
      : null;
  const diagnosis = resultField(result, "diagnosis");
  const enumerateDone =
    taskId !== null && status?.kind === "enumerate" && status?.state === "done";
  const noSolutions = enumerateDone && feasibleCount === 0;
  const tableEnabled =
    enumerateDone && feasibleCount !== null && feasibleCount > 0;

  const solutionsQuery =
    useGetSolutionsApiCalcTasksTaskIdSolutionsGet<SolutionPageView, Error>(
      taskId ?? "",
      { page, size: PAGE_SIZE, sort },
      {
        query: {
          enabled: tableEnabled,
          select: narrowSolutionPage,
        },
      },
    );

  /** ?task= 回写（replaceState 不触发导航——两写入面共用）。 */
  const writeTaskParam = (nextTaskId: string) => {
    const search = withTaskParam(window.location.search, nextTaskId);
    window.history.replaceState(
      null,
      "",
      search
        ? `${window.location.pathname}?${search}`
        : window.location.pathname,
    );
  };
  const enumerate = useRunEnumerationApiCalcEnumeratePost<WaterprintApiError>({
    mutation: {
      onSuccess: (response) => {
        setTaskId(response.task_id);
        setPage(1); // 新任务重置页码（D9）
        writeTaskParam(response.task_id);
      },
    },
  });
  // 方案应用回调（D6）：任务态面板转向重算任务（?task= 联动——表数据为
  // 已提交任务快照不自动刷新，旧行保留语义）
  const handleApplied = (outcome: ApplyOutcome) => {
    setTaskId(outcome.recalc_task_id);
    setPage(1);
    writeTaskParam(outcome.recalc_task_id);
  };

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">
        {NO_PROJECT_HINT}
      </Typography.Paragraph>
    );
  }

  const units = unitsQuery.data ?? [];
  return (
    <ErrorBoundary label="方案浏览">
      <section>
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          方案浏览（单单元枚举——ADR-005）
        </Typography.Title>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Select
            style={{ minWidth: 260 }}
            value={unitId ?? undefined}
            loading={unitsQuery.isLoading}
            status={unitsQuery.isError ? "error" : undefined}
            options={units.map((unit) => ({
              value: unit.unitId,
              label: unit.kind !== null ? `${unit.unitId}（${unit.kind}）` : unit.unitId,
            }))}
            onChange={(value) => setUnitId(value)}
          />
          <Button
            type="primary"
            loading={enumerate.isPending}
            disabled={unitId === null}
            onClick={() => {
              if (unitId === null) {
                return;
              }
              enumerate.mutate({
                data: {
                  project_id: projectId,
                  unit_ids: [unitId],
                  options: null,
                },
              });
            }}
          >
            提交枚举
          </Button>
          {enumerate.isError ? (
            <Typography.Text type="danger">
              提交失败：
              {enumerate.error instanceof Error
                ? enumerate.error.message
                : "未知错误"}
            </Typography.Text>
          ) : null}
        </div>
        {unitsQuery.isError ? (
          <Typography.Paragraph type="danger">
            单元清单加载失败：
            {unitsQuery.error instanceof Error
              ? unitsQuery.error.message
              : "未知错误"}
          </Typography.Paragraph>
        ) : null}

        <div style={{ marginTop: 12 }}>
          {taskId !== null ? (
            <TaskPanel
              taskId={taskId}
              view={view}
              status={status}
              statusError={
                statusQuery.error instanceof Error
                  ? statusQuery.error.message
                  : statusQuery.isError
                    ? "未知错误"
                    : null
              }
            />
          ) : (
            <Typography.Paragraph type="secondary">
              选定单元后提交枚举：任务进度与失败回显将在此呈现，完成后展示
              方案表（margin_min 降序）。
            </Typography.Paragraph>
          )}
        </div>

        {noSolutions ? <DiagnosisPanel diagnosis={diagnosis} /> : null}
        {tableEnabled && solutionsQuery.data ? (
          <div style={{ marginTop: 12 }}>
            <div style={{ marginBottom: 8 }}>
              <RankingControls
                columns={solutionsQuery.data.columns}
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
              projectId={projectId}
              unitId={unitId}
              currentPage={page}
              onPageChange={setPage}
              onApplied={handleApplied}
            />
          </div>
        ) : null}
        {solutionsQuery.isError ? (
          <Typography.Paragraph type="danger">
            方案取数失败：
            {solutionsQuery.error instanceof Error
              ? solutionsQuery.error.message
              : "未知错误"}
            （未完成任务取方案=409/排序键白名单外=422——详见任务状态）
          </Typography.Paragraph>
        ) : null}
      </section>
    </ErrorBoundary>
  );
}
