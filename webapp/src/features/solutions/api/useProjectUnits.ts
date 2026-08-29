/**
 * 项目单元清单查询：useReadProject 薄封装 select 窄化（D8 枚举提交面）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=ProjectUnitRef[] 窄化产物；错误统一
 *        Error 面：WaterprintApiError 取数失败/形状非法拒）
 *
 * 规格说明（FE6 批 6b 段四，D8；params useProjectDesign 同构薄封装）：
 *   - solutions 自有封装（features 互禁 import——不借 params/canvas 面）；
 *     消费同一 orval 生成 hook：queryKey 恒 ['/api/projects/${projectId}']
 *     与 canvas/params 通道同键缓存自动共享（单次取数多面板消费——
 *     FE5 头注记先例；ParamForm/方案应用 apply 后 invalidate 同键联动）；
 *   - select=design.nodes 投影 {unitId,kind}[]（kind=内置节点元数据键
 *     非参数叶——inlet→municipal_input 目录键面，FE5 D1 同款语义）；
 *     design/nodes 容器形状非法抛 Error→查询 error 态（呈现面文案）；
 *   - select 模块级引用稳定（不逐渲染重跑——react-query 结构保持）。
 */
import { useReadProjectApiProjectsProjectIdGet } from "../../../shared/api/generated/projects/projects";

/** 单元引用（枚举提交下拉消费面——unit_id 与内置 kind 键）。 */
export type ProjectUnitRef = {
  unitId: string;
  kind: string | null;
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** design.nodes → {unitId,kind}[] 投影（形状非法抛 Error）。 */
function selectProjectUnits(raw: {
  [key: string]: unknown;
}): ProjectUnitRef[] {
  const design = raw["design"];
  if (!isRecord(design)) {
    throw new Error("项目 design 面缺失或非对象——无法列单元清单");
  }
  const nodes = design["nodes"];
  if (!isRecord(nodes)) {
    throw new Error("项目 design.nodes 面缺失或非对象——无法列单元清单");
  }
  return Object.entries(nodes).map(([unitId, params]) => ({
    unitId,
    kind:
      isRecord(params) && typeof params["kind"] === "string"
        ? params["kind"]
        : null,
  }));
}

/** 项目单元清单查询（projectId=null 禁用——solutionsPane 空态省请求）。 */
export function useProjectUnits(projectId: string | null) {
  return useReadProjectApiProjectsProjectIdGet<ProjectUnitRef[], Error>(
    projectId ?? "",
    {
      query: {
        enabled: projectId !== null,
        select: selectProjectUnits,
      },
    },
  );
}
