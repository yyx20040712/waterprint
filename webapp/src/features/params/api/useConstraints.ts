/**
 * 约束知识库目录查询：orval 生成 hook 薄封装 select 窄化（CP1 D6）。
 *
 * 输入:  无参（静态目录——无单元过滤面，过滤归纯函数 filterSelectable）
 * 输出:  useQuery 结果句柄（data=ConstraintEntryView[] 窄化产物）
 *
 * 规格说明（CP1 2026-08-31；useProjectUnits 同构薄封装）：
 *   - params 自有封装（ConstraintPicker 同 feature）；queryKey 恒
 *     ['/api/constraints']（静态目录——单次取数多消费面缓存共享）；
 *   - select=narrowConstraintCatalog（窄化门第二防线——非法形状→查询
 *     error 态呈现非静默）；
 *   - select 模块级引用稳定（不逐渲染重跑——react-query 结构保持）。
 */
import { useListConstraintsApiConstraintsGet } from "../../../shared/api/generated/units/units";

import { narrowConstraintCatalog } from "../lib/constraintPicker";

/** 约束目录查询（静态 kb——18 条两类整发，D6 不分页）。 */
export function useConstraints() {
  return useListConstraintsApiConstraintsGet({
    query: {
      select: narrowConstraintCatalog,
    },
  });
}
