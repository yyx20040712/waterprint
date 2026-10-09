/**
 * v4 分析表态纯函数层（B2 结果与方案批 2026-10-09——全厂指标面 effluent
 * 聚合行构建；R1 回炉 R1a 增失效键 predicate 面；运行期零依赖——
 * react-query 仅 type import 编译期擦除，node 直测 QueryClient 纯 JS
 * 实例同 solutionsView 制）。
 *
 * 输入:  trust.effluent 条目族（condition_key/indicator/value/limit/margin）
 *        +projectId（失效键 predicate 构造）
 * 输出:  effluentRows → 聚合行（指标×工况值+限值+判定——wireframe 屏 3
 *        「指标|基准 avg|设计 design|限值|判定」形的数据面）；
 *        analysisFacesPredicate/unitResultsKeyPredicate → invalidateQueries
 *        predicate 面（R1a：orval 生成键〔url, params?〕首元素=完整 URL
 *        字符串——旧前缀字符串键打不中=死键根治）
 *
 * 规格说明（B2 任务书 §二.③——数据源定形：compare=关键容积行矩阵+
 * trust effluent=出水指标限值判定行，双现行端点复用零新 server 面）：
 *   - 行=indicator 去重聚合（值=condition_key→value；工况列序=首见序——
 *     design 键固定在内）；
 *   - 限值/判定=design 工况条目（design 缺席=首见条目兜底）；判定口径
 *     =margin>=0（达/超——trust ADR-012 effluent 同源语义）；
 *   - 行序=indicator 首见序（确定性——载荷序稳定）。
 *   - R1a：predicate 只认键首元素=完整生成 URL——compare/trust 精确等值
 *     +unit-results〈/api/calc/projects/{pid}/units/ 前缀且 /results 尾〉
 *     （他项目/项目读键不误伤——测试断言面）。
 */
import type { Query } from "@tanstack/react-query";

/** effluent 条目（trust 窄化产物成员形——窄化门在 trustView）。 */
export type EffluentEntry = {
  condition_key: string;
  standard_id: string;
  indicator: string;
  value: number;
  limit: number;
  margin: number;
};

/** 聚合行（EffluentTable dataSource 面）。 */
export type EffluentRow = {
  indicator: string;
  values: Record<string, number>;
  limit: number;
  compliant: boolean;
};

/** effluent 条目族→聚合行（空载荷=空行集——呈现面空表不出）。 */
export function effluentRows(effluent: readonly EffluentEntry[]): EffluentRow[] {
  const rows: EffluentRow[] = [];
  const byIndicator = new Map<string, EffluentRow>();
  for (const entry of effluent) {
    let row = byIndicator.get(entry.indicator);
    if (row === undefined) {
      row = {
        indicator: entry.indicator,
        values: {},
        limit: entry.limit,
        compliant: entry.margin >= 0,
      };
      byIndicator.set(entry.indicator, row);
      rows.push(row);
    }
    row.values[entry.condition_key] = entry.value;
    // 限值/判定基准=design 条目（缺席=首见兜底——纯提升类无 design 面）
    if (entry.condition_key === "design") {
      row.limit = entry.limit;
      row.compliant = entry.margin >= 0;
    }
  }
  return rows;
}

/** 键首元素读取（orval 生成键 [url, params?] 形）。 */
function keyHead(query: Query): string | null {
  const head = query.queryKey[0];
  return typeof head === "string" ? head : null;
}

/** unit-results 失效键 predicate（R1a——生成键精确域：本项目 units 前缀
 *  且 /results 尾；他项目/非本端点键不误伤）。 */
export function unitResultsKeyPredicate(projectId: string): (query: Query) => boolean {
  return (query) => {
    const head = keyHead(query);
    return (
      head !== null &&
      head.startsWith(`/api/calc/projects/${projectId}/units/`) &&
      head.endsWith("/results")
    );
  };
}

/** 分析面三键失效 predicate（R1a：compare/trust 精确键+unit-results 域）。 */
export function analysisFacesPredicate(projectId: string): (query: Query) => boolean {
  const unitResults = unitResultsKeyPredicate(projectId);
  return (query) => {
    const head = keyHead(query);
    return (
      head === `/api/calc/compare/${projectId}` ||
      head === `/api/calc/trust/${projectId}` ||
      unitResults(query)
    );
  };
}
