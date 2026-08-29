/**
 * 项目文件查询：orval 生成 hooks 的消费封装（canvas 数据通道唯一入口）。
 *
 * 输入:  projectId（裸 id——归一面见 app/projectParam normalizeProjectId）
 * 输出:  useQuery 结果句柄（ReadProjectApiProjectsProjectIdGet200 弱类型
 *        {[key:string]:unknown}——D6 窄化门在 lib/projectFlow 收口）
 *
 * 规格说明（FE4 批 6b 段一，viewer3d useSceneQuery 同构）：
 *   - queryKey 由 orval 生成器按 [url] 组装（§17.2——projectId 变即新键，
 *     杜绝旧项目画面残留）；
 *   - 类型只从 generated/ 取（禁手写双份，教训 A2）；
 *   - 返回体弱类型自由 JSON：router 返回 dict[str, Any] 未建模——投影层
 *     projectFlow 入口窄化（D6）是唯一防线；
 *   - 错误归一在 shared/api/http.ts（本封装零错误处理逻辑）。
 */
import { useReadProjectApiProjectsProjectIdGet } from "../../../shared/api/generated/projects/projects";

export function useProjectQuery(projectId: string) {
  return useReadProjectApiProjectsProjectIdGet(projectId);
}
