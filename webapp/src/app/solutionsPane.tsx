/**
 * solutions 标签页装配：?project=/?task= 双参消费+单单元枚举提交+任务态
 * 面板+方案表+排序控件组合（D8 组合面——app 层唯一 features 组合层）。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook——与 canvas/viewer3d 共用）
 *        +?task=（任务 id 单一真相——D3）+useProjectUnits 单元清单+SSE
 *        任务流+TaskStatus 快照
 * 输出:  方案浏览标签页（单元下拉+「提交枚举」+TaskPanel+RankingControls
 *        +SolutionsTable/DiagnosisPanel；?task= 回写 replaceState）
 *
 * 规格说明（FE6 批 6b 段四 D1/D3/D8/D9；R 轮修复 2026-08-29 R1/R2/R3/R7；
 *   canvasPane/viewer3dPane 同构）：
 *   - R1 任务态双轨（xC-1）：enumerateTaskId=表数据源键（方案表/result
 *     载荷/gridFields/feasible_count/diagnosis/挂载门——仅枚举提交
 *     onSuccess 更新）与 panelTaskId（TaskPanel+SSE 订阅+?task= URL 面
 *     ——枚举提交/方案应用/事件监听更新）分立。apply 后只切 panelTaskId
 *     ——方案表与旧行保留不卸载（简报 D6「应用后表格数据为已提交任务
 *     快照不自动刷新（旧行保留）」本意；浏览页码亦不重置）；枚举提交
 *     onSuccess 两轨同更（新枚举=新表源+新面板任务）；
 *   - R2 应用目标固化（yI-2）：枚举 onSuccess 固化 enumeratedUnitId
 *     快照（表源任务的单元）——ApplySolutionButton 消费固化值（实时
 *     下拉仅驱动新枚举提交，改选不影响已展示行的应用目标——服务端
 *     apply 无单元-参数域匹配防护，错位应用会真实原子写错单元）；
 *     deep-link 进 ?task= 时固化值 null→应用按钮禁用维持；
 *   - projectId 单一真相=URL（useProjectId 共享 hook——S3 读方订阅面：
 *     写方 canvas/viewer3d 切项目后本 pane 响应刷新）；面板只读不回写
 *     （项目选择器归 canvas 面）；
 *   - 任务 id 双轨（ENG5 D6/I-4 收口）：?enum= 枚举轨（表源
 *     enumerateTaskId——枚举提交 onSuccess 写 enum 键）与 ?task= 计算
 *     轨（panelTaskId 面板轨——方案应用 onApplied[recalc_task_id]/
 *     ParamForm apply 内联回写）并存互不覆盖（apply 后深链不丢方案
 *     表）；面板轨初值 task 优先（parseTaskParam ?? parseEnumParam——
 *     apply 流后写时间序）；R3（yI-1）URL 回写驱动已挂载 pane:
 *     ParamForm 回写后 dispatchEvent("wp:task")（TASK_EVENT 事件桥——
 *     常量已收口 shared/events[S12]；ParamForm 侧 task 键回写仍内联
 *     ——分层禁 import app）→本 pane 事件桥监听（第二处）→重读 URL
 *     ?task= 比对更新 panelTaskId（不触发导航不抢焦点——跨标签自动跳转
 *     挂账 UX 批；Tabs 保活下 replaceState 无事件、useState 初始化器仅首
 *     挂载执行的双局限经此事件桥收口）；
 *   - D8 枚举提交面：单元下拉（useProjectUnits——design.nodes 投影）
 *     +useRunEnumeration（body={project_id, unit_ids:[unitId], options:
 *     选中约束时 {constraints: 三键载荷}——CP1 兑现「constraints 空槽
 *     挂账」：ConstraintPicker[features/params] 挂单元下拉与提交钮间，
 *     供选=filterSelectable(kind 双门+单元归属)，payload=toPayloadItems
 *     恰三键[severity 不入 worker 面]；无选中=options null 零漂移）；
 *   - 任务态双源：useTaskFeed（SSE 进度）+useGetTaskStatus（终态
 *     invalidate 重拉——result 载荷与 failed 三件详情源）；表挂载=
 *     表源任务 kind==='enumerate'&&state==='done'&&feasible_count>0；
 *     无解=done+feasible_count=0→DiagnosisPanel（合法终态非 failed）；
 *     R7（zM-5）done 而 feasible_count 缺失→「结果载荷缺失」防御提示；
 *     calc 重算任务（apply/参数提交触发）只挂 TaskPanel（409 面由
 *     enabled 防住：非 done 不取表）；
 *   - D9 分页/sort 组件态（useState——不建 store FE5 D2 先例；store 骨架
 *     占位维持）：page 1 基/size=50 固定/sort 初值 margin_min；queryKey
 *     [表源任务 id, {page,size,sort}] 全量进（排序确定性）；select=
 *     narrowSolutionPage 窄化收口（非法形状→查询 error 态呈现）；
 *   - Select 不用占位文案属性（grep 门禁英文占位特征词命中该 prop 名
 *     ——FE3 C3 同款规避）；
 *   - 空态：?project= 缺失=指引文案（先在工艺画布标签选择项目——项目
 *     选择器不重复建，挂账 UX 批）；ErrorBoundary label=方案浏览。
 */
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Button, Select, Typography } from "antd";

import {
  useGetSolutionsApiCalcTasksTaskIdSolutionsGet,
  useGetTaskStatusApiCalcTasksTaskIdGet,
  useRunEnumerationApiCalcEnumeratePost,
} from "../shared/api/generated/calc/calc";
import type { ApplyOutcome } from "../shared/api/generated/model";
import { WaterprintApiError } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";
import { useProjectUnits } from "../features/solutions/api/useProjectUnits";
import { useConstraints } from "../features/params/api/useConstraints";
import { ConstraintPicker } from "../features/params/components/ConstraintPicker";
import {
  filterSelectable,
  toPayloadItems,
} from "../features/params/lib/constraintPicker";
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
  parseEnumParam,
  parseTaskParam,
  withEnumParam,
  withTaskParam,
} from "./projectParam";
import { useProjectId } from "./useProjectId";

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
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  // R1 双轨初值（ENG5 D6 键分立+R1 旧链兼容：表源轨=枚举任务[?enum=]
  // 优先、纯 ?task= 旧深链兜底[FE6~UX1 时代枚举提交写 task 键的历史
  // 分享链——kind 门自然滤 calc 任务]；面板轨=计算轨[?task=]优先、缺省
  // 回落枚举轨——两轨非对称初值各守其主，deep-link 各形态面板皆有任务）
  const [enumerateTaskId, setEnumerateTaskId] = useState<string | null>(() =>
    parseEnumParam(window.location.search) ?? parseTaskParam(window.location.search),
  );
  const [panelTaskId, setPanelTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search) ?? parseEnumParam(window.location.search),
  );
  const [unitId, setUnitId] = useState<string | null>(null);
  // R2：表源任务单元固化快照（应用目标——下拉实时值仅驱动新枚举提交）
  const [enumeratedUnitId, setEnumeratedUnitId] = useState<string | null>(null);
  const [constraintKeys, setConstraintKeys] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("margin_min");
  const queryClient = useQueryClient();
  const unitsQuery = useProjectUnits(projectId);
  // CP1 D6：约束目录（静态 kb——窄化门 select；失败=error 态不阻断枚举）
  const constraintsQuery = useConstraints();

  // R3：?task= 回写驱动已挂载 pane（ParamForm dispatchEvent——URL 单一
  // 真相重读比对；同值早退不扰动；卸载移除监听）
  useEffect(() => {
    const onTaskParam = () => {
      const next = parseTaskParam(window.location.search);
      setPanelTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  // SSE 进度流（面板轨）：终态回调→失效面板任务快照（failed 三件详情）
  // AUDIT2-R R3（DS-03 跨基座一审发现）：终态再派发 TASK_EVENT——重算
  // 完成后已挂载 elevation/cost 自动刷新（stale 横幅随之解除）；apply 时刻
  // 的首派发只拉到旧快照+警示,二段刷新此前缺失。本 pane 自监听经 URL
  // 重读幂等（?task= 未再变,同值早退）。
  const view = useTaskFeed(panelTaskId, () => {
    if (panelTaskId !== null) {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/tasks/${panelTaskId}`],
      });
      window.dispatchEvent(
        new CustomEvent(TASK_EVENT, { detail: panelTaskId }),
      );
    }
  });
  const panelStatusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(
    panelTaskId ?? "",
    { query: { enabled: panelTaskId !== null } },
  );
  // 表源轨快照（result 载荷/挂载门依据——同任务时与面板轨同键缓存共享）
  const tableStatusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(
    enumerateTaskId ?? "",
    { query: { enabled: enumerateTaskId !== null } },
  );
  const tableStatus = tableStatusQuery.data ?? null;
  const result = tableStatus?.result ?? null;
  const gridFields = narrowGridFields(result);
  const feasibleRaw = resultField(result, "feasible_count");
  const feasibleCount =
    typeof feasibleRaw === "number" && Number.isFinite(feasibleRaw)
      ? feasibleRaw
      : null;
  const diagnosis = resultField(result, "diagnosis");
  const enumerateDone =
    enumerateTaskId !== null &&
    tableStatus?.kind === "enumerate" &&
    tableStatus?.state === "done";
  const noSolutions = enumerateDone && feasibleCount === 0;
  // R7：done 而 feasible_count 缺失（result 载荷异形）——防御提示面
  const payloadMissing = enumerateDone && feasibleCount === null;
  const tableEnabled =
    enumerateDone && feasibleCount !== null && feasibleCount > 0;

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

  /** URL 键回写共底（replaceState 不触发导航——enum/task 两轨共用）。 */
  const replaceSearch = (search: string) => {
    window.history.replaceState(
      null,
      "",
      search
        ? `${window.location.pathname}?${search}`
        : window.location.pathname,
    );
  };
  /** ?enum= 回写（ENG5 D6 枚举轨——task 键不动）。 */
  const writeEnumParam = (nextEnumId: string) => {
    replaceSearch(withEnumParam(window.location.search, nextEnumId));
  };
  /** ?task= 回写（计算轨——方案应用面；enum 键不动）。 */
  const writeTaskParam = (nextTaskId: string) => {
    replaceSearch(withTaskParam(window.location.search, nextTaskId));
  };
  const enumerate = useRunEnumerationApiCalcEnumeratePost<WaterprintApiError>({
    mutation: {
      onSuccess: (response) => {
        // R1 两轨同更（新枚举=新表源+新面板任务）；R2 固化表源单元
        setEnumerateTaskId(response.task_id);
        setPanelTaskId(response.task_id);
        setEnumeratedUnitId(unitId);
        setPage(1); // 新任务重置页码（D9）
        writeEnumParam(response.task_id); // ENG5 D6：枚举轨写 enum 键（task 键不动）
      },
    },
  });
  // R1：方案应用只切面板轨+URL——表源键不动（方案表与旧行保留不卸载，
  // 浏览页码不重置——D6 已提交任务快照语义）
  // AUDIT2 FIX2 C-2：补派发 TASK_EVENT——ParamForm 路径先例对齐；原缺
  // 派发使已挂载高程/概算 pane 零刷新（浏览器实证 apply 后切回 0 请求，
  // 陈旧缓存直出）。本 pane 自监听经 URL 重读幂等（同值早退不扰动）。
  const handleApplied = (outcome: ApplyOutcome) => {
    setPanelTaskId(outcome.recalc_task_id);
    writeTaskParam(outcome.recalc_task_id);
    window.dispatchEvent(
      new CustomEvent(TASK_EVENT, { detail: outcome.recalc_task_id }),
    );
  };

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">
        {NO_PROJECT_HINT}
      </Typography.Paragraph>
    );
  }

  const units = unitsQuery.data ?? [];
  const selectableConstraints = filterSelectable(
    constraintsQuery.data ?? [],
    unitId,
  );
  return (
    <ErrorBoundary label="方案浏览">
      <section>
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          方案浏览（单单元枚举——ADR-005）
        </Typography.Title>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <Select
            style={{ minWidth: 260 }}
            value={unitId ?? undefined}
            loading={unitsQuery.isLoading}
            status={unitsQuery.isError ? "error" : undefined}
            options={units.map((unit) => ({
              value: unit.unitId,
              label: unit.kind !== null ? `${unit.unitId}（${unit.kind}）` : unit.unitId,
            }))}
            onChange={(value) => {
              setUnitId(value);
              setConstraintKeys([]); // 单元切换清空（供选面随单元变——CP1 D6）
            }}
          />
          <ConstraintPicker
            entries={selectableConstraints}
            selectedKeys={constraintKeys}
            onChange={setConstraintKeys}
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
                  options:
                    constraintKeys.length === 0
                      ? null
                      : {
                          constraints: toPayloadItems(
                            selectableConstraints,
                            constraintKeys,
                          ),
                        },
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
          {panelTaskId !== null ? (
            <TaskPanel
              taskId={panelTaskId}
              view={view}
              status={panelStatusQuery.data ?? null}
              statusError={
                panelStatusQuery.error instanceof Error
                  ? panelStatusQuery.error.message
                  : panelStatusQuery.isError
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
        {payloadMissing ? (
          <Typography.Paragraph
            type="warning"
            style={{ marginBottom: 0, marginTop: 8 }}
          >
            枚举已完成但结果载荷缺失（feasible_count）——请重新提交枚举。
          </Typography.Paragraph>
        ) : null}
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
              unitId={enumeratedUnitId}
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
            {/* AUDIT2 FIX2 I-3（zM-2 纪律回灌）：409/422 说明仅挂对应
                领域码（TaskNotComplete/InvalidPageParameter）——网络错/
                其他错误码不挂误导注记。 */}
            {solutionsQuery.error instanceof WaterprintApiError &&
            (solutionsQuery.error.code === "TaskNotCompleteError" ||
              solutionsQuery.error.code === "InvalidPageParameterError")
              ? "（未完成任务取方案=409/排序键白名单外=422——详见任务状态）"
              : null}
          </Typography.Paragraph>
        ) : null}
      </section>
    </ErrorBoundary>
  );
}
