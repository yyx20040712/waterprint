/**
 * 单元目录/假设清单查询：orval 生成 hooks 的消费封装（params 声明面数据通道）。
 *
 * 输入:  无参（GET /api/units + GET /api/assumptions——静态目录）
 * 输出:  useQuery 结果句柄（UnitCatalog/AssumptionCatalog 类型面；错误统一
 *        WaterprintApiError 归一——本封装零错误处理逻辑）
 *
 * 规格说明（FE5 批 6b 段三，D1；canvas useProjectQuery 同构薄封装）：
 *   - queryKey=['/api/units']与['/api/assumptions']静态键（META1 registry
 *     投影——进程期内目录不失效，无 invalidate 面）；
 *   - 类型只从 generated/ 取（禁手写双份，教训 A2）；
 *   - ParamForm 消费 useUnitCatalog（META1 manifest 参数面——default/dim/
 *     range/grid 灰阶展示数据）；AssumptionsPanel 消费 useAssumptionCatalog
 *     （21 条 registry 声明序——DEFAULTS 端）。
 */
import {
  useListAssumptionsApiAssumptionsGet,
  useListUnitsApiUnitsGet,
} from "../../../shared/api/generated/units/units";

/** 单元目录查询（36 条=32 包+4 内置 kind——unit_id 序+内置排末）。 */
export function useUnitCatalog() {
  return useListUnitsApiUnitsGet();
}

/** 假设清单查询（21 条 registry 声明序——六字段取五）。 */
export function useAssumptionCatalog() {
  return useListAssumptionsApiAssumptionsGet();
}
