/**
 * trust 标签页装配：?project= 消费+ErrorBoundary+空态引导+TrustReportView
 * +"wp:task" 事件桥（P2 次批 ADR-012 D8）。
 *
 * 输入:  URL ?project=（useProjectId 共享 hook——与 canvas/viewer3d/
 *        solutions/elevation/cost 共用，S3 订阅面）+useTrustQuery 可信度
 *        报告（latest done calc 全工况聚合）+TASK_EVENT 事件（apply 重算后）
 * 输出:  可信度标签页（空态引导/404 引导/状态条+四区块卡；全工况聚合
 *        报告无工况切换——与 cost/elevation 按工况取数不同）
 *
 * 规格说明（P2 次批 2026-09-12；costPane 同构第五例）：
 *   - projectId 单一真相=URL（useProjectId 共享 hook）；面板只读不回写；
 *   - 非 lazy（无 echarts 大件——普通导入）；
 *   - TASK_EVENT 事件桥监听（第五处监听——常量已收口 shared/events[S12]；
 *     ParamForm/solutionsPane/elevationPane/costPane 四处先例）→invalidate
 *     ['/api/calc/trust/'+projectId] 键；
 *   - 空态：?project= 缺失=指引文案；查询 error 分级（costPane R3 同款）：
 *     仅 WaterprintApiError.code==="TrustSourceNotFoundError"（404 无 done
 *     calc）才附「先提交计算」引导——网络错/窄化 TrustViewError 不挂
 *     误导 hint；ErrorBoundary label=可信度。
 */
import { useEffect } from "react";
import { Typography } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { TrustReportView } from "../features/trust/components/TrustReportView";
import { useTrustQuery } from "../features/trust/api/useTrustQuery";
import { WaterprintApiError } from "../shared/api/http";
import { ErrorBoundary } from "./ErrorBoundary";
import { TASK_EVENT } from "../shared/events";
import { useProjectId } from "./useProjectId";

/** 空态指引（?project= 缺失——先经工艺画布标签选择项目）。 */
const NO_PROJECT_HINT =
  "尚未选择项目：请先在「工艺画布」标签选择项目（URL ?project= 参数）——可信度报告针对最近完成计算的结果集装配。";

/** 404 引导（无 done calc——先提交计算）。 */
const NO_CALC_HINT =
  "——请先提交计算（POST /api/calc/run）完成后再回本标签查看可信度报告。";

export function TrustPane() {
  // S3 读方：hook 订阅——写方切项目后 ?project= 响应（查询键随态变 refetch）
  const [projectId] = useProjectId();
  const queryClient = useQueryClient();

  // TASK_EVENT 事件桥监听（第五处——apply 重算后失效键，面板刷新）
  useEffect(() => {
    const onTaskParam = () => {
      if (projectId !== null) {
        void queryClient.invalidateQueries({
          queryKey: [`/api/calc/trust/${projectId}`],
        });
      }
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  const query = useTrustQuery(projectId);
  const report = query.data ?? null;

  if (projectId === null) {
    return (
      <Typography.Paragraph type="secondary">{NO_PROJECT_HINT}</Typography.Paragraph>
    );
  }

  return (
    <ErrorBoundary label="可信度">
      <section data-testid="wp-trust-pane">
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          结果可信度（收敛 / 水量平衡 / 出水裕度 / 校核警告）
        </Typography.Title>
        {query.isError ? (
          <Typography.Paragraph type="danger">
            可信度报告取数失败：
            {query.error instanceof Error ? query.error.message : "未知错误"}
            {/* 仅 404 无 done calc 面附引导——网络错/窄化错不挂（costPane R3 同款） */}
            {query.error instanceof WaterprintApiError &&
            query.error.code === "TrustSourceNotFoundError"
              ? NO_CALC_HINT
              : null}
          </Typography.Paragraph>
        ) : report === null ? (
          <Typography.Paragraph type="secondary">
            正在加载可信度报告…
          </Typography.Paragraph>
        ) : (
          // stale/降级状态条由 TrustReportView.StatusStrip 统一呈现（单点）
          <TrustReportView report={report} />
        )}
      </section>
    </ErrorBoundary>
  );
}
