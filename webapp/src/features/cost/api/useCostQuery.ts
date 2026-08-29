/**
 * cost 查询封装：orval 生成 hook 薄封装+窄化门接线（D8）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）+conditionKey（null=缺省
 *        请求——服务端 design 基线档回显；显式值=按需触发另一工况索引）
 * 输出:  useQuery 结果句柄（data=CostView 窄化产物；错误统一 Error 面：
 *        WaterprintApiError 取数失败/CostViewError 形状非法拒）
 *
 * 规格说明（FE8 批 6b 段六，D8）：
 *   - cost 自有封装（features 互禁 import——useElevationQuery 同构薄封装
 *     先例）；消费 orval 生成 hook：queryKey 恒
 *     ['/api/cost/${projectId}', params?]——conditionKey 经 params 全量进键
 *     （工况切换=键切换触发按需取数 §17.1）；"wp:task" 事件后 invalidate
 *     前缀键 ['/api/cost/${projectId}'] 即同键缓存全失效（costPane 监听面）；
 *   - select=narrowCostResponse 窄化收口（非法形状→查询 error 态呈现）；
 *     select 模块级引用稳定（不逐渲染重跑）；
 *   - conditionKey=null 不发 condition_key 参数（服务端缺省=design 基线档
 *     回显——D2 口径）。
 */
import { useGetCostApiCostProjectIdGet } from "../../../shared/api/generated/cost/cost";

import { narrowCostResponse, type CostView } from "../lib/estimateView";

/** cost 概算查询（projectId=null 禁用——costPane 空态省请求）。 */
export function useCostQuery(projectId: string | null, conditionKey: string | null) {
  return useGetCostApiCostProjectIdGet<CostView, Error>(
    projectId ?? "",
    conditionKey === null ? undefined : { condition_key: conditionKey },
    {
      query: {
        enabled: projectId !== null,
        select: narrowCostResponse,
      },
    },
  );
}
