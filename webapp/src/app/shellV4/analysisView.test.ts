/**
 * v4 分析表态纯函数测试（B2 结果与方案批——effluentRows 聚合口径+
 * R1 回炉 analysisFacesPredicate 失效键面；node 直测——QueryClient=
 * react-query 纯 JS 实例零 DOM 面）。
 *
 * 输入:  effluent 条目族夹具（双工况/缺 design 兜底/超限判定）+QueryClient
 *        以 orval 生成键注入的缓存夹具（R1a——生成键建查询断言失效命中，
 *        关闭「实现与测试同错面」）
 * 输出:  断言族：①indicator 去重聚合+值按工况键 ②限值/判定=design 条目
 *        ③design 缺席=首见兜底 ④超限判定（margin<0=超）⑤空载荷=空行集
 *        ⑥R1a：predicate 失效命中生成 unit-results 键+compare/trust 精确键
 *        ⑦R1a：他项目键不误伤（前缀字符串死键根治证）
 */
import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import {
  getGetCompareReportApiCalcCompareProjectIdGetQueryKey,
  getGetTrustReportApiCalcTrustProjectIdGetQueryKey,
  getGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGetQueryKey,
} from "../../shared/api/generated/calc/calc";
import { analysisFacesPredicate, effluentRows, type EffluentEntry } from "./analysisView";

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

describe("analysisFacesPredicate（R1a 失效键面——生成键断言）", () => {
  /** 缓存注入客户端（staleTime Infinity——isInvalidated 即失效标记位）。 */
  const clientWith = () =>
    new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } });

  it("predicate 失效命中：生成 unit-results 键+compare/trust 精确键（死键根治）", async () => {
    const qc = clientWith();
    const unitKey =
      getGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGetQueryKey(
        "p1",
        "municipal_aao",
        undefined,
      );
    const compareKey =
      getGetCompareReportApiCalcCompareProjectIdGetQueryKey("p1");
    const trustKey = getGetTrustReportApiCalcTrustProjectIdGetQueryKey("p1");
    qc.setQueryData(unitKey, { rows: [] });
    qc.setQueryData(compareKey, { metrics: [] });
    qc.setQueryData(trustKey, { effluent: [] });
    await qc.invalidateQueries({ predicate: analysisFacesPredicate("p1") });
    expect(qc.getQueryCache().find({ queryKey: unitKey, exact: true })?.state.isInvalidated).toBe(true);
    expect(qc.getQueryCache().find({ queryKey: compareKey, exact: true })?.state.isInvalidated).toBe(true);
    expect(qc.getQueryCache().find({ queryKey: trustKey, exact: true })?.state.isInvalidated).toBe(true);
  });

  it("他项目/非本面键不误伤（前缀字符串旧死键对照证）", async () => {
    const qc = clientWith();
    const ownKey =
      getGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGetQueryKey(
        "p1",
        "municipal_aao",
        undefined,
      );
    const otherProjectKey =
      getGetUnitResultsApiCalcProjectsProjectIdUnitsUnitIdResultsGetQueryKey(
        "p2",
        "municipal_aao",
        undefined,
      );
    const projectReadKey = [`/api/projects/p1`] as const;
    qc.setQueryData(ownKey, { rows: [] });
    qc.setQueryData(otherProjectKey, { rows: [] });
    qc.setQueryData([...projectReadKey], { design: {} });
    await qc.invalidateQueries({ predicate: analysisFacesPredicate("p1") });
    expect(qc.getQueryCache().find({ queryKey: ownKey, exact: true })?.state.isInvalidated).toBe(true);
    expect(qc.getQueryCache().find({ queryKey: otherProjectKey, exact: true })?.state.isInvalidated).toBe(
      false,
    );
    expect(qc.getQueryCache().find({ queryKey: [...projectReadKey], exact: true })?.state.isInvalidated).toBe(
      false,
    );
  });
});
