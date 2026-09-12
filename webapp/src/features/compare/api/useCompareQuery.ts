/**
 * compare 查询封装：orval 生成 hook 薄封装+窄化门接线（P2 第三批 ADR-018 D5）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=CompareReport 窄化产物；错误统一 Error 面：
 *        WaterprintApiError 取数失败/CompareViewError 形状非法拒）
 *
 * 规格说明（P2 第三批；useTrustQuery 同构薄封装先例）：
 *   - compare 自有封装（features 互禁 import）；queryKey 恒
 *     ['/api/calc/compare/${projectId}']——"wp:task" 事件后 invalidate
 *     该键（comparePane 监听面）；
 *   - select=narrowCompareResponse 窄化收口（非法形状→查询 error 态）；
 *     select 模块级引用稳定（不逐渲染重跑）；
 *   - 全工况聚合矩阵无工况参数（与 trust 同——一次全量多工况列）。
 */
import { useGetCompareReportApiCalcCompareProjectIdGet } from "../../../shared/api/generated/calc/calc";

import { narrowCompareResponse, type CompareReport } from "../lib/compareView";

/** 多工况对比报告查询（projectId=null 禁用——comparePane 空态省请求）。 */
export function useCompareQuery(projectId: string | null) {
  return useGetCompareReportApiCalcCompareProjectIdGet<CompareReport, Error>(
    projectId ?? "",
    {
      query: {
        enabled: projectId !== null,
        select: narrowCompareResponse,
      },
    },
  );
}
