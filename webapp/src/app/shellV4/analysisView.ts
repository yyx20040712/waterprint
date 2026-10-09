/**
 * v4 分析表态纯函数层（B2 结果与方案批 2026-10-09——全厂指标面 effluent
 * 聚合行构建；零运行期库 import——node 直测同 solutionsView 制）。
 *
 * 输入:  trust.effluent 条目族（condition_key/indicator/value/limit/margin）
 * 输出:  effluentRows → 聚合行（指标×工况值+限值+判定——wireframe 屏 3
 *        「指标|基准 avg|设计 design|限值|判定」形的数据面）
 *
 * 规格说明（B2 任务书 §二.③——数据源定形：compare=关键容积行矩阵+
 * trust effluent=出水指标限值判定行，双现行端点复用零新 server 面）：
 *   - 行=indicator 去重聚合（值=condition_key→value；工况列序=首见序——
 *     design 键固定在内）；
 *   - 限值/判定=design 工况条目（design 缺席=首见条目兜底）；判定口径
 *     =margin>=0（达/超——trust ADR-012 effluent 同源语义）；
 *   - 行序=indicator 首见序（确定性——载荷序稳定）。
 */

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
