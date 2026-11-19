/**
 * v4 工况区（b2 壳重组批 2026-11-19——八入口「工况」：多工况对比矩阵
 * 全幅；沿革 compare=AnalysisPane 全厂面内嵌段〔B2〕→b2 独立入口
 * 〔useCompareQuery+CompareMatrix feature 原件复用组合——app 层组合面
 * 职权；分析页内嵌矩阵保持不动〕。稿 compare.html 主区宽表形——工况
 * 筛选/锁定基准列=后续功能批不新建）。
 *
 * 输入:  useProjectId+useCompareQuery（compare 查询）+TASK_EVENT（事件桥
 *        ——apply 重算后失效）+StaleBanner（analysisPane 导出件复用——
 *        stale 横幅+重算入口同源单件）
 * 输出:  工况对比面：空态三态（无项目/无结果——重算引导/取数失败）+
 *        stale 横幅+CompareMatrix（pinned=null——锁定基准 UI 未实装）
 *
 * 规格说明（b2 任务书——分析/工况拆分裁决）：
 *   - 只读呈现（零回写——与 AnalysisPane 全厂面同口径）；
 *   - 错误面=domainGate 领域码固定摘要+重算引导（analysisPane GATE_TEXT
 *     同口径文案，不新增第二文案口径）；
 *   - TASK_EVENT 失效键=compare 生成键（精确域——前缀字符串死键防）。
 */
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useCompareQuery } from "../../features/compare/api/useCompareQuery";
import { CompareMatrix } from "../../features/compare/components/CompareMatrix";
import { useProjectId } from "../useProjectId";
import { TASK_EVENT } from "../../shared/events";
import { domainGate } from "../../shared/api/sourceGate";
import { StaleBanner } from "./analysisPane";

/** 空态引导文案（白名单：空态引导——analysisPane 同口径）。 */
const NO_PROJECT_HINT = "尚未选择项目——在「工作台」打开或新建";
const NO_RESULT_HINT = "尚无计算结果——点顶栏「全项目计算」钮提交后回看";
/** 领域 404 固定摘要（analysisPane GATE_TEXT.compare 同文案单源口径）。 */
const GATE_COMPARE_TEXT = "项目暂无完成的计算结果";

export function CompareZone() {
  const [projectId] = useProjectId();
  const queryClient = useQueryClient();
  const query = useCompareQuery(projectId);

  // TASK_EVENT 事件桥（analysisPane 根级同制——apply 重算后失效本面）
  useEffect(() => {
    if (projectId === null) {
      return;
    }
    const onTaskParam = () => {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/compare/${projectId}`],
      });
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, [projectId, queryClient]);

  if (projectId === null) {
    return (
      <section
        data-region="compare-matrix"
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--wp-text-2)",
          fontSize: 12,
        }}
      >
        {NO_PROJECT_HINT}
      </section>
    );
  }
  if (query.isError) {
    // 领域 404=固定摘要+重算引导；网络/窄化错=raw 透出（错误提示白名单）
    const gate = domainGate(query.error, "CompareSourceNotFoundError", GATE_COMPARE_TEXT);
    return (
      <section
        data-region="compare-matrix"
        data-testid="wp-v4-compare-error"
        style={{ flex: 1, padding: 24, color: "var(--wp-text-2)", fontSize: 12, overflow: "auto" }}
      >
        {gate.domain ? `${gate.text}——${NO_RESULT_HINT}` : `取数失败：${gate.text}`}
      </section>
    );
  }
  if (query.data === undefined || query.data === null) {
    return (
      <section
        data-region="compare-matrix"
        style={{ flex: 1, padding: 24, color: "var(--wp-text-2)", fontSize: 12 }}
      >
        正在加载工况对比…
      </section>
    );
  }
  return (
    <section
      data-region="compare-matrix"
      data-testid="wp-v4-compare-plant"
      style={{ flex: 1, minWidth: 0, padding: "10px 12px", overflow: "auto" }}
    >
      {query.data.stale ? <StaleBanner projectId={projectId} /> : null}
      <CompareMatrix report={query.data} pinned={null} />
    </section>
  );
}
