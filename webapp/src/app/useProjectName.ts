/**
 * 项目名 hook（v2-20261015 笔3 新建——rawProjectName 自 reportZone 71-81
 * 迁入单源导出；shellV4 状态条项目名消费面，项目 hex 裸露消除）。
 *
 * 输入:  useProjectId（项目单一真相）+useReadProjectApiProjectsProjectIdGet
 *        （zoneBand 90-92 同制：{query:{enabled:projectId!==null}} 门）
 * 输出:  useProjectName()→string|null——未选项目=null（消费面显「未选择」
 *        不变）；有项目=rawProjectName(data)??「未命名项目」（空白/缺名/
 *        pending/失败同回退——A3 裁决）；rawProjectName 纯函数导出（raw
 *        项目读宽容取项目名——reportZone 卡头副线等共享消费）
 */
import { useProjectId } from "./useProjectId";
import { useReadProjectApiProjectsProjectIdGet } from "../shared/api/generated/projects/projects";

/** 未命名回退（空白/缺名/pending/失败同文——状态条 24px 无 Spinner 预算）。 */
const UNNAMED = "未命名项目";

/** raw 项目读宽容取项目名（zoneBand rawCheckedUnits 同款形态——非对象/
 *  缺 view/name 非串/空白=null，合法名 trim 直出）。 */
export function rawProjectName(raw: unknown): string | null {
  if (typeof raw !== "object" || raw === null) {
    return null;
  }
  const view = (raw as Record<string, unknown>)["view"];
  if (typeof view !== "object" || view === null) {
    return null;
  }
  const name = (view as Record<string, unknown>)["name"];
  return typeof name === "string" && name.trim() ? name.trim() : null;
}

export function useProjectName(): string | null {
  const [projectId] = useProjectId();
  const query = useReadProjectApiProjectsProjectIdGet(projectId ?? "", {
    query: { enabled: projectId !== null },
  });
  if (projectId === null) {
    return null;
  }
  return rawProjectName(query.data) ?? UNNAMED;
}
