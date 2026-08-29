/**
 * 项目 design 参数面查询：orval 生成 hooks 的消费封装（params 自有数据通道）。
 *
 * 输入:  projectId（裸 id——归一面见 app/projectParam normalizeProjectId）
 * 输出:  useQuery 结果句柄（data=DesignParams 窄化产物——select 应用；
 *        错误统一 Error 面：WaterprintApiError 取数失败/DesignParamsError 窄化拒）
 *
 * 规格说明（FE5 批 6b 段三，D5/D8；canvas useProjectQuery 同构薄封装）：
 *   - params 自有封装（features 互禁 import——不借 canvas 的 useProjectQuery）；
 *     消费同一 orval 生成 hook：queryKey 恒 ['/api/projects/${projectId}']，
 *     与 canvas 通道同键缓存自动共享（单次取数多面板消费——D8 记档事实）；
 *   - select=narrowDesignParams（D8 窄化门收口于 lib 纯函数——模块级引用
 *     稳定不逐渲染重跑；形状非法抛 DesignParamsError → 查询 error 态，
 *     消费面错误薄壳呈现，不白屏）；
 *   - ParamForm 提交 apply 成功后 invalidateQueries 此键（D5：服务端
 *     apply 已 save——失效 read 键驱动本通道+canvas 通道同步刷新）。
 */
import { useReadProjectApiProjectsProjectIdGet } from "../../../shared/api/generated/projects/projects";
import { narrowDesignParams, type DesignParams } from "../lib/designParams";

/** 项目 design 参数面查询（弱类型返回体经窄化门→DesignParams）。 */
export function useProjectDesign(projectId: string) {
  return useReadProjectApiProjectsProjectIdGet<DesignParams, Error>(
    projectId,
    { query: { select: narrowDesignParams } },
  );
}
