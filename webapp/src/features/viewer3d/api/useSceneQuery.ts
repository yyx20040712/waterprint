/**
 * 场景图查询：orval 生成 hooks 的消费封装（viewer3d 数据通道唯一入口）。
 *
 * 输入:  projectId + 可选 conditionKey（缺省=服务端排序首键回显）
 * 输出:  useQuery 结果句柄（SceneGraph 类型面；错误统一 WaterprintApiError）
 *
 * 规格说明（FE1 实装 v1）：
 *   - queryKey 由 orval 生成器按 [url, params] 组装（§17.2 输入变自动
 *     失效——工况切换即新键，杜绝旧场景上屏）；
 *   - 类型只从 generated/ 取（禁手写双份，教训 A2）；
 *   - 错误归一在 shared/api/http.ts（本封装零错误处理逻辑）。
 */
import { useGetSceneApiSceneProjectIdGet } from "../../../shared/api/generated/scene/scene";

export function useSceneQuery(projectId: string, conditionKey?: string) {
  const params = conditionKey === undefined ? undefined : { condition_key: conditionKey };
  return useGetSceneApiSceneProjectIdGet(projectId, params);
}
