/**
 * trust 查询封装：orval 生成 hook 薄封装+窄化门接线（P2 次批 ADR-012）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=TrustReport 窄化产物；错误统一 Error 面：
 *        WaterprintApiError 取数失败/TrustViewError 形状非法拒）
 *
 * 规格说明（P2 次批；useCostQuery 同构薄封装先例）：
 *   - trust 自有封装（features 互禁 import）；queryKey 恒
 *     ['/api/calc/trust/${projectId}']——"wp:task" 事件后 invalidate
 *     该键（trustPane 监听面）；
 *   - select=narrowTrustResponse 窄化收口（非法形状→查询 error 态）；
 *     select 模块级引用稳定（不逐渲染重跑）；
 *   - 全工况聚合报告无工况参数（与 cost/elevation 按工况取数不同——
 *     可信度面一次全量）。
 */
import { useGetTrustReportApiCalcTrustProjectIdGet } from "../../../shared/api/generated/calc/calc";

import { narrowTrustResponse, type TrustReport } from "../lib/trustView";

/** trust 可信度报告查询（projectId=null 禁用——trustPane 空态省请求）。 */
export function useTrustQuery(projectId: string | null) {
  return useGetTrustReportApiCalcTrustProjectIdGet<TrustReport, Error>(
    projectId ?? "",
    {
      query: {
        enabled: projectId !== null,
        select: narrowTrustResponse,
      },
    },
  );
}
