/**
 * opsChain 查询封装：orval 生成 hook 薄封装+窄化门接线（B4-1 实现批）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=OpsChainReport 窄化产物；错误统一 Error 面：
 *        WaterprintApiError 取数失败/OpsChainViewError 形状非法拒）
 *
 * 规格说明（B4-1；useTrustQuery 同构薄封装先例）：
 *   - opsdebug 自有封装（features 互禁 import）；queryKey 恒
 *     ['/api/debug/ops-chain/'+projectId]——"wp:task" 事件后 invalidate
 *     该键（opsDebugPane 监听面）；
 *   - select=narrowOpsChainResponse 窄化收口（非法形状→查询 error 态）；
 *     select 模块级引用稳定（不逐渲染重跑）；
 *   - 全任务时间线无工况参数（诊断面一次全量——与 trust 同口径）。
 */
import { useGetOpsChainApiDebugOpsChainProjectIdGet } from "../../../shared/api/generated/debug/debug";

import { narrowOpsChainResponse, type OpsChainReport } from "../lib/opsChainView";

/** 操作链观测面查询（projectId=null 禁用——opsDebugPane 空态省请求）。 */
export function useOpsChainQuery(projectId: string | null) {
  return useGetOpsChainApiDebugOpsChainProjectIdGet<OpsChainReport, Error>(
    projectId ?? "",
    {
      query: {
        enabled: projectId !== null,
        select: narrowOpsChainResponse,
      },
    },
  );
}
