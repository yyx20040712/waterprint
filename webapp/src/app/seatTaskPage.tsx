/**
 * 席位任务分页（M7 批 2026-10-07——面板轨接线复刻旧 solutionsPane〔54ba5c2139^
 * L145-148/L173-186/L176-190/L205-235〕+opsdebug 三件入席折叠段〔旧
 * opsDebugPane 装配复刻〕）。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook——S3 读方订阅）+?task=/?enum=
 *        （面板轨双参——task 优先缺省回落 enum）+TASK_EVENT 事件桥+useTaskFeed
 *        （SSE 进度）+useGetTaskStatus 快照+useOpsChainQuery（操作链观测面）
 * 输出:  任务进度面（panelTaskId null=空态引导；否则 TaskPanel 原件 props
 *        注入〔零改消费〕）+「操作链诊断」折叠面板（antd Collapse
 *        defaultActiveKey=[] 收拢——席位最小高 140 下进度面优先，深读按需
 *        展开；体根 wp-seat-task/折叠段 wp-seat-ops）
 *
 * 规格说明（brief D3；复刻源=git show 54ba5c2139^ 两 pane）：
 *   - 面板轨双轨初值：parseTaskParam ?? parseEnumParam（apply 流后写时间序
 *     ——task 优先；缺省回落 enum 轨，deep-link 各形态面板皆有任务）；
 *   - TASK_EVENT 监听重读 URL（task??enum——FIX-ACC1④ 双轨重读口径）+同值
 *     早退（setPanelTaskId 函数式比对零扰动）；卸载移除监听；
 *   - prevProject 切项目守卫：初挂载早退保深链初值→切项目置 null
 *     （withProjectParam 剔除 task/enum 的对方面——跨项目残留防）；
 *   - connection 态随 panelTaskId 变更重置（旧任务中断提示不残留）；
 *   - SSE useTaskFeed(panelTaskId, onTerminal, setConnection)：onTerminal=
 *     invalidate `/api/calc/tasks/{id}` 快照+再派发 TASK_EVENT（AUDIT2-R R3
 *     二段刷新承袭——本页自监听经 URL 重读同值早退幂等）；快照
 *     useGetTaskStatusApiCalcTasksTaskIdGet（enabled=panelTaskId!==null）；
 *   - opsdebug 段（装配复刻）：useOpsChainQuery+TASK_EVENT→invalidate
 *     `/api/debug/ops-chain/{projectId}`+404 分级引导（仅
 *     WaterprintApiError.code==="ProjectNotFoundError" 才附「检查项目」——
 *     网络错/窄化错不挂误导 hint）+ErrorBoundary label=操作链+三态
 *     （projectId null 空态/查询 error/loading/OpsChainView）。
 */
import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Collapse, Typography } from "antd";

import { OpsChainView } from "../features/opsdebug/components/OpsChainView";
import { useOpsChainQuery } from "../features/opsdebug/api/useOpsChainQuery";
import { TaskPanel } from "../features/solutions/components/TaskPanel";
import { useTaskFeed, type ConnectionState } from "../features/solutions/api/useTaskFeed";
import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../shared/api/generated/calc/calc";
import { WaterprintApiError } from "../shared/api/http";
import { TASK_EVENT } from "../shared/events";
import { ErrorBoundary } from "./ErrorBoundary";
import { parseEnumParam, parseTaskParam } from "./projectParam";
import { useProjectId } from "./useProjectId";

/** 空态引导文案（brief D3 逐字——Ribbon「提交计算」/枚举提交为任务源）。 */
const NO_TASK_HINT =
  "尚未跟踪任务——顶部『提交计算』/枚举提交后，进度与终态在此呈现";

/** ops 段空态指引（?project= 缺失——M1 席位同款措辞：槽语义）。 */
const OPS_NO_PROJECT_HINT = "尚未选择项目——请先在画布槽选择项目";

/** ops 段 404 引导（项目不存在——仅 ProjectNotFoundError 附挂）。 */
const OPS_NO_PROJECT_CALC_HINT =
  "——项目不存在，请检查当前项目是否已被删除或改名。";

export function SeatTaskPage() {
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  // 面板轨双轨初值（task 优先，缺省回落 enum——旧 solutionsPane L145-148）
  const [panelTaskId, setPanelTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search) ?? parseEnumParam(window.location.search),
  );
  // B7 D3/D4：SSE 连接态（useTaskFeed onConnection 消费源→TaskPanel
  // connection prop——reconnecting/probing 显中断提示行；ok/任务切换置 null）
  const [connection, setConnection] = useState<ConnectionState | null>(null);
  const queryClient = useQueryClient();
  const prevProject = useRef(projectId); // 切项目守卫（初挂载早退保深链初值）

  // TASK_EVENT 重读（旧 solutionsPane L173-186——URL 单一真相重读比对；
  // 双轨重读口径 task??enum；同值早退不扰动；卸载移除监听）
  useEffect(() => {
    const onTaskParam = () => {
      const next =
        parseTaskParam(window.location.search) ??
        parseEnumParam(window.location.search);
      setPanelTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  // 切项目守卫（旧 solutionsPane L176-190——prevProject 初值同值早退保深链
  // 初值；切项目置 null：旧项目任务深链对新项目无意义）
  useEffect(() => {
    if (prevProject.current === projectId) return;
    prevProject.current = projectId;
    setPanelTaskId(null);
  }, [projectId]);

  // 面板任务切换重置连接态（旧任务中断提示不残留到新任务；effect 声明先于
  // useTaskFeed 挂载序，重置先于新连接回调——旧 solutionsPane 同序）
  useEffect(() => {
    setConnection(null);
  }, [panelTaskId]);

  // SSE 进度流（面板轨）：终态回调→失效面板任务快照（failed 三件详情）
  // +再派发 TASK_EVENT（AUDIT2-R R3 二段刷新——重算完成后已挂载面自动
  // 刷新；本页自监听经 URL 重读幂等〔?task= 未再变，同值早退〕）
  const view = useTaskFeed(
    panelTaskId,
    () => {
      if (panelTaskId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/tasks/${panelTaskId}`],
        });
        window.dispatchEvent(
          new CustomEvent(TASK_EVENT, { detail: panelTaskId }),
        );
      }
    },
    setConnection,
  );
  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(
    panelTaskId ?? "",
    { query: { enabled: panelTaskId !== null } },
  );

  // opsdebug 入席装配（旧 opsDebugPane 复刻）：TASK_EVENT→invalidate
  // ops-chain 键（任务完成后时间线/聚合块刷新——第七处监听面归席位）
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/debug/ops-chain/${projectId}`],
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  const opsQuery = useOpsChainQuery(projectId);
  const opsReport = opsQuery.data ?? null;

  return (
    <div
      data-testid="wp-seat-task"
      style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "8px 10px" }}
    >
      {panelTaskId !== null ? (
        <TaskPanel
          taskId={panelTaskId}
          view={view}
          connection={connection}
          status={statusQuery.data ?? null}
          statusError={
            statusQuery.error instanceof Error
              ? statusQuery.error.message
              : statusQuery.isError
                ? "未知错误"
                : null
          }
        />
      ) : (
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {NO_TASK_HINT}
        </Typography.Paragraph>
      )}
      {/* opsdebug 折叠段（密度裁量=默认收拢：席位最小高 140 下进度面优先，
          深读按需展开——自裁申报项①） */}
      <Collapse
        data-testid="wp-seat-ops"
        size="small"
        defaultActiveKey={[]}
        style={{ marginTop: 12 }}
        items={[
          {
            key: "ops",
            label: "操作链诊断",
            children: (
              <ErrorBoundary label="操作链">
                {projectId === null ? (
                  <Typography.Paragraph type="secondary">
                    {OPS_NO_PROJECT_HINT}
                  </Typography.Paragraph>
                ) : opsQuery.isError ? (
                  <Typography.Paragraph type="danger">
                    操作链观测面取数失败：
                    {opsQuery.error instanceof Error
                      ? opsQuery.error.message
                      : "未知错误"}
                    {/* 仅 404 项目不存在面附引导——网络错/窄化错不挂（旧
                        opsDebugPane 同款） */}
                    {opsQuery.error instanceof WaterprintApiError &&
                    opsQuery.error.code === "ProjectNotFoundError"
                      ? OPS_NO_PROJECT_CALC_HINT
                      : null}
                  </Typography.Paragraph>
                ) : opsReport === null ? (
                  <Typography.Paragraph type="secondary">
                    正在加载操作链观测面…
                  </Typography.Paragraph>
                ) : (
                  // 降级/stale 状态条由 OpsChainView.StatusStrip 统一呈现（单点）
                  <OpsChainView report={opsReport} />
                )}
              </ErrorBoundary>
            ),
          },
        ]}
      />
    </div>
  );
}
