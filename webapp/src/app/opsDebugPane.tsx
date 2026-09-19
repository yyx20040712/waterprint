/**
 * 诊断标签页装配：?project= 消费+ErrorBoundary+空态引导+OpsChainView
 * +"wp:task" 事件桥（B4-1 实现批《裁决书》方案五①）。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook）+useOpsChainQuery 操作链
 *        观测面（任务时间线+最新结果三源聚合）+TASK_EVENT 事件
 * 输出:  诊断标签页（空态引导/404 引导/状态条+时间线+聚合卡——操作链
 *        全链观测一次呈现）
 *
 * 规格说明（B4-1；trustPane 同构第七例）：
 *   - projectId 单一真相=URL（useProjectId 共享 hook）；面板只读不回写；
 *   - TASK_EVENT 事件桥监听（第七处监听）→invalidate
 *     ['/api/debug/ops-chain/'+projectId] 键（任务完成后时间线/聚合块刷新）；
 *   - 空态：?project= 缺失=指引文案；查询 error 分级（trustPane R3 同款）：
 *     仅 WaterprintApiError.code==="ProjectNotFoundError"（404 项目不存在）
 *     才附「检查项目」引导——网络错/窄化 OpsChainViewError 不挂误导 hint；
 *     ErrorBoundary label=诊断。
 */
import { useEffect } from "react";
import { Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { OpsChainView } from "../features/opsdebug/components/OpsChainView";
import { useOpsChainQuery } from "../features/opsdebug/api/useOpsChainQuery";
import { WaterprintApiError } from "../shared/api/http";
import { ErrorBoundary } from "./ErrorBoundary";
import { TASK_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——诊断观测面针对项目操作链装配。";

/** 404 引导（项目不存在）。 */
const NO_PROJECT_CALC_HINT = "——项目不存在，请检查当前项目是否已被删除或改名。";

export function OpsDebugPane() {
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  const queryClient = useQueryClient();

  // TASK_EVENT 事件桥监听（第七处——任务完成后失效键，面板刷新）
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

  const query = useOpsChainQuery(projectId);
  const report = query.data ?? null;

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">{NO_PROJECT_HINT}</Typography.Paragraph>
    );
  }

  return (
    <ErrorBoundary label="诊断">
      <section data-testid="wp-ops-pane">
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          操作链诊断（任务时间线 / 诊断摘要 / 警告计数 / trace 聚合）
        </Typography.Title>
        {query.isError ? (
          <Typography.Paragraph type="danger">
            操作链观测面取数失败：
            {query.error instanceof Error ? query.error.message : "未知错误"}
            {/* 仅 404 项目不存在面附引导——网络错/窄化错不挂（trustPane 同款） */}
            {query.error instanceof WaterprintApiError &&
            query.error.code === "ProjectNotFoundError"
              ? NO_PROJECT_CALC_HINT
              : null}
          </Typography.Paragraph>
        ) : report === null ? (
          <Typography.Paragraph type="secondary">
            正在加载操作链观测面…
          </Typography.Paragraph>
        ) : (
          // 降级/stale 状态条由 OpsChainView.StatusStrip 统一呈现（单点）
          <OpsChainView report={report} />
        )}
      </section>
    </ErrorBoundary>
  );
}
