/**
 * validation 查询封装：orval 生成 hook 薄封装+窄化门接线（T3 前端警告
 * 聚合批）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=ValidationObservation 窄化产物；错误统一
 *        Error 面：WaterprintApiError 取数失败〔含 ValidationSourceNotFound
 *        Error 404〕/ValidationViewError 形状非法拒）
 *
 * 规格说明（T3 批；useTrustQuery 同构薄封装先例）：
 *   - validation 自有封装（features 互禁 import）；queryKey 恒
 *     ['/api/calc/validation/${projectId}']——TASK_EVENT 事件桥经
 *     analysisFacesPredicate 纳入失效面（analysisView 单源扩展）；
 *   - select=narrowValidationObservation 窄化收口（非法形状→查询 error
 *     态）；select 模块级引用稳定（不逐渲染重跑）；
 *   - 全项目观测无工况参数（与 trust 同——一次全量）。
 */
import { useGetValidationObservationApiCalcValidationProjectIdGet } from "../../../shared/api/generated/calc/calc";

import {
  narrowValidationObservation,
  type ValidationObservation,
} from "../lib/validationView";

/** 校验观测查询（projectId=null 禁用——空态省请求）。 */
export function useValidationQuery(projectId: string | null) {
  return useGetValidationObservationApiCalcValidationProjectIdGet<
    ValidationObservation,
    Error
  >(projectId ?? "", {
    query: {
      enabled: projectId !== null,
      select: narrowValidationObservation,
    },
  });
}
