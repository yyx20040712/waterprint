/**
 * v4 分析表态纯函数测试（B2 结果与方案批——effluentRows 聚合口径；
 * 零 jsdom 红线：node 直测同 solutionsView 制）。
 *
 * 输入:  effluent 条目族夹具（双工况/缺 design 兜底/超限判定）
 * 输出:  断言族：①indicator 去重聚合+值按工况键 ②限值/判定=design 条目
 *        ③design 缺席=首见兜底 ④超限判定（margin<0=超）⑤空载荷=空行集
 */
import { describe, expect, it } from "vitest";

import { effluentRows, type EffluentEntry } from "./analysisView";

const entry = (
  condition_key: string,
  indicator: string,
  value: number,
  limit: number,
  margin: number,
): EffluentEntry => ({
  condition_key,
  standard_id: "gb18918-1a",
  indicator,
  value,
  limit,
  margin,
});

describe("effluentRows 聚合（全厂指标面数据面）", () => {
  it("indicator 去重聚合+工况值列+design 条目定限值判定", () => {
    const rows = effluentRows([
      entry("avg", "CODCR", 38, 50, 12),
      entry("design", "CODCR", 40, 50, 10),
    ]);
    expect(rows.length).toBe(1);
    expect(rows[0]?.values).toEqual({ avg: 38, design: 40 });
    expect(rows[0]?.limit).toBe(50);
    expect(rows[0]?.compliant).toBe(true);
  });

  it("design 缺席=首见条目兜底（限值/判定）", () => {
    const rows = effluentRows([entry("avg", "TN", 13.1, 15, 1.9)]);
    expect(rows[0]?.limit).toBe(15);
    expect(rows[0]?.compliant).toBe(true);
  });

  it("design 超限条目=判定超（margin<0）", () => {
    const rows = effluentRows([
      entry("avg", "NH3N", 1.8, 5, 3.2),
      entry("design", "NH3N", 6, 5, -1),
    ]);
    expect(rows[0]?.compliant).toBe(false);
  });

  it("空载荷=空行集（呈现面空表不出）", () => {
    expect(effluentRows([])).toEqual([]);
  });
});
