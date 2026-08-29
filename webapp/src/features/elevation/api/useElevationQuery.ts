/**
 * elevation 查询封装：orval 生成 hook 薄封装+窄化门接线（D8/D9）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）+conditionKey（null=缺省
 *        请求——服务端排序首键回显；显式值=按需触发另一工况索引）
 * 输出:  useQuery 结果句柄（data=ElevationView 窄化产物；错误统一 Error
 *        面：WaterprintApiError 取数失败/ElevationViewError 形状非法拒）
 *
 * 规格说明（FE7 批 6b 段五，D8/D9）：
 *   - elevation 自有封装（features 互禁 import——不借 solutions/params 面，
 *     useProjectUnits 同构薄封装先例）；消费 orval 生成 hook：
 *     queryKey 恒 ['/api/elevation/${projectId}', params?]——conditionKey
 *     经 params 全量进键（工况切换=键切换触发按需取数 §17.1）；
 *     "wp:task" 事件后 invalidate 前缀键 ['/api/elevation/${projectId}']
 *     即同键缓存全失效（elevationPane 监听面）；
 *   - select=narrowElevationResponse 窄化收口（非法形状→查询 error 态
 *     呈现）；select 模块级引用稳定（不逐渲染重跑）；
 *   - conditionKey=null 不发 condition_key 参数（服务端缺省=排序首键
 *     回显——scene 先例口径）。
 */
import { useGetElevationApiElevationProjectIdGet } from "../../../shared/api/generated/elevation/elevation";

import { narrowElevationResponse, type ElevationView } from "../lib/profileChart";

/** elevation 纵断查询（projectId=null 禁用——elevationPane 空态省请求）。 */
export function useElevationQuery(
  projectId: string | null,
  conditionKey: string | null,
) {
  return useGetElevationApiElevationProjectIdGet<ElevationView, Error>(
    projectId ?? "",
    conditionKey === null ? undefined : { condition_key: conditionKey },
    {
      query: {
        enabled: projectId !== null,
        select: narrowElevationResponse,
      },
    },
  );
}
