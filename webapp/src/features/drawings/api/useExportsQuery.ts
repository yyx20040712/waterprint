/**
 * drawings 查询封装：导出列表+工况选项+单元选项（薄封装三查询）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄×3（data=narrowExportsResponse/
 *        narrowConditionOptions/单元 id 列表投影；错误统一 Error 面：
 *        WaterprintApiError 取数失败/DrawingsViewError 形状非法拒）
 *
 * 规格说明（FE9 批 6b 段七，D8；useCostQuery/useProjectUnits 同构先例）：
 *   - drawings 自有封装（features 互禁 import——不借 cost/params/solutions
 *     面）；列表消费 orval useListExportsApiExportsGet：params 显式传
 *     project_id（ENG4 D3 注记：缺省空串恒 []——服务端过滤无「列出全部」
 *     语义），queryKey 恒 ['/api/exports', {project_id}]；select=
 *     narrowExportsResponse 窄化收口（非法形状→查询 error 态呈现）；
 *   - 工况源=cost 同端点（costPane.tsx 工况 Select 同源）：消费
 *     useGetCostApiCostProjectIdGet 缺省请求（不传 condition_key）——
 *     queryKey ['/api/cost/${projectId}'] 与 costPane 缺省键同键缓存
 *     自动共享（单次取数多面板消费——useProjectDesign 先例）；
 *     select=narrowConditionOptions 只投影 conditions 索引面；
 *   - 单元源=projects 同端点（FE5 useProjectDesign/FE6 useProjectUnits
 *     同构）：queryKey ['/api/projects/${projectId}'] 同键缓存共享；
 *     select 投影 design.nodes 键序（单元 id 列表——导出 unit_id 选项）；
 *   - select 全部模块级引用稳定（不逐渲染重跑）。
 */
import { useGetCostApiCostProjectIdGet } from "../../../shared/api/generated/cost/cost";
import { useReadProjectApiProjectsProjectIdGet } from "../../../shared/api/generated/projects/projects";
import { useListExportsApiExportsGet } from "../../../shared/api/generated/exports/exports";

import {
  narrowConditionOptions,
  narrowExportsResponse,
  type ExportMetaView,
} from "../lib/drawingsView";

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** design.nodes → 单元 id 列表投影（形状非法抛 Error——useProjectUnits 同款）。 */
function selectUnitIds(raw: { [key: string]: unknown }): string[] {
  const design = raw["design"];
  if (!isRecord(design)) {
    throw new Error("项目 design 面缺失或非对象——无法列单元清单");
  }
  const nodes = design["nodes"];
  if (!isRecord(nodes)) {
    throw new Error("项目 design.nodes 面缺失或非对象——无法列单元清单");
  }
  return Object.keys(nodes);
}

/** 导出产物列表查询（projectId=null 禁用——drawingsPane 空态省请求）。 */
export function useExportsQuery(projectId: string | null) {
  return useListExportsApiExportsGet<ExportMetaView[], Error>(
    projectId === null ? undefined : { project_id: projectId },
    {
      query: {
        enabled: projectId !== null,
        select: narrowExportsResponse,
      },
    },
  );
}

/** 工况选项查询（cost 同端点同键缓存共享——无 done calc 时 404 error 态）。 */
export function useConditionOptions(projectId: string | null) {
  return useGetCostApiCostProjectIdGet<string[], Error>(
    projectId ?? "",
    undefined,
    {
      query: {
        enabled: projectId !== null,
        select: narrowConditionOptions,
      },
    },
  );
}

/** 单元选项查询（projects 同端点同键缓存共享——导出 unit_id 选项面）。 */
export function useUnitOptions(projectId: string | null) {
  return useReadProjectApiProjectsProjectIdGet<string[], Error>(
    projectId ?? "",
    {
      query: {
        enabled: projectId !== null,
        select: selectUnitIds,
      },
    },
  );
}
