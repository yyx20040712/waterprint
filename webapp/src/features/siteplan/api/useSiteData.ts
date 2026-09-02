/**
 * 布置数据通道：项目文件+场景图两查询的薄封装（siteplan 数据唯一入口）。
 *
 * 输入:  projectId（裸 id——归一面见 app/projectParam normalizeProjectId）
 * 输出:  { projectQuery, sceneQuery }（useQuery 句柄；scene 失败≠致命——
 *        data undefined 即足迹降级示意矩形，错误呈现归消费面）
 *
 * 规格说明（M3 批 L2b，简报 §一.1/§三）：
 *   - 轮廓数据源=既有 GET /api/scene/{project_id}（openapi 恒红线零新端点
 *     ——直用 orval 生成 hook，viewer3d useSceneQuery 同构但零 import
 *     其他 feature：本封装独立持钩）；
 *   - scene 不可得（项目无已完成计算/查询失败）→ data undefined → 消费面
 *     按 footprint=null 示意矩形+「未计算」角标渲染——编辑面不阻断；
 *   - 类型只从 generated/ 取（禁手写双份）；queryKey 由 orval 按
 *     [url, params] 组装（projectId 变即新键——杜绝旧项目画面残留）。
 */
import { useReadProjectApiProjectsProjectIdGet } from "../../../shared/api/generated/projects/projects";
import { useGetSceneApiSceneProjectIdGet } from "../../../shared/api/generated/scene/scene";

export function useSiteData(projectId: string) {
  const projectQuery = useReadProjectApiProjectsProjectIdGet(projectId);
  const sceneQuery = useGetSceneApiSceneProjectIdGet(projectId);
  return { projectQuery, sceneQuery };
}
