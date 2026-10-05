/**
 * validation 查询封装：orval 生成 hook 薄封装+窄化门接线（2A1 消费批）。
 *
 * 输入:  projectId（裸 id——null 时禁用不取数）
 * 输出:  useQuery 结果句柄（data=ValidationObservation 窄化产物；错误统一
 *        Error 面：WaterprintApiError 取数失败/MaintenanceViewError 形状非法拒）
 *
 * 规格说明（2A1 消费批；useTrustQuery 同构薄封装先例）：
 *   - validation 自有封装（features 互禁 import）；queryKey 恒
 *     ['/api/calc/validation/${projectId}']——"wp:task" 事件后 invalidate
 *     该键（trustPane 既有监听面追加，勿新增第二监听）；
 *   - select=narrowValidationObservation 窄化收口（非法形状→查询 error 态）；
 *     select 模块级引用稳定（不逐渲染重跑）；
 *   - 观测面无工况参数（全工况投影——与 trust 同为 latest done calc 聚合）。
 */
import { useGetValidationObservationApiCalcValidationProjectIdGet } from "../../../shared/api/generated/calc/calc";

import {
  narrowValidationObservation,
  type ValidationObservation,
} from "../lib/maintenanceView";

/** 校验观测报告查询（projectId=null 禁用——trustPane 空态省请求）。 */
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
