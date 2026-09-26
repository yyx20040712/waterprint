/**
 * sensitivity 查询封装：orval 生成 hook 薄封装+窄化门接线（批6e——
 * useCompareQuery 同构薄封装先例；features 互禁 import 本面自持）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=SensitivityReportView 窄化产物；错误
 *        统一 Error 面：窄化非法→SensitivityViewError/HTTP 404 无结果
 *        集→WaterprintApiError——消费面 data??null 降级为提示文案）
 *
 * 规格说明（批6e 设计档 §四）：
 *   - queryKey 恒 ['/api/calc/sensitivity/${projectId}']（§17.2 前端
 *     缓存规则——project id 入键；"wp:task" 事件后失效联动归 app 层
 *     comparePane 同款消费面裁量，本壳不重复挂监听）；
 *   - select=narrowSensitivityResponse 窄化收口（模块级引用稳定）；
 *   - 404=项目未跑过全流程计算的合法态（非错误轰炸面——消费侧
 *     sensitivity===null → 诚实提示文案）。
 */
import { useGetSensitivityReportApiCalcSensitivityProjectIdGet } from "../../../shared/api/generated/calc/calc";

import { narrowSensitivityResponse, type SensitivityReportView } from "../lib/sensitivityView";

/** 全工况投影报告查询（projectId=null 禁用——幅度面省请求）。 */
export function useSensitivityQuery(projectId: string | null) {
  return useGetSensitivityReportApiCalcSensitivityProjectIdGet<SensitivityReportView, Error>(
    projectId ?? "",
    {
      query: {
        enabled: projectId !== null,
        select: narrowSensitivityResponse,
      },
    },
  );
}
