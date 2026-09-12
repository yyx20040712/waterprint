/**
 * compareView 纯函数测试（P2 第三批 ADR-018）：窄化门+锁定基准三件+
 * 矩阵行模型。
 *
 * 输入:  features/compare/lib/compareView 公开符号（node 纯函数——零
 *        antd/react 运行期依赖）
 * 输出:  窄化门正反两向+isPinStale 过期判定+filterLivePins 失效键过滤+
 *        rowExtremes 极值标注+formatMetricValue 数值格式化断言组
 */
import { describe, expect, it } from "vitest";

import {
  CompareViewError,
  filterLivePins,
  formatMetricValue,
  isPinStale,
  metricLabel,
  metricRowKey,
  narrowCompareResponse,
  pinOf,
  rowExtremes,
  type CompareReport,
} from "./compareView";

/** 合法报告 fixture（最小面：单指标双工况+零警告）。 */
function fixtureReport(overrides: Partial<CompareReport> = {}): CompareReport {
  return {
    project_id: "p1",
    task_id: "t1",
    stale: false,
    design_hash: "hash-1",
    engine_version: "e",
    data_version: "d",
    condition_keys: ["avg", "design"],
    metrics: [
      {
        unit_id: "municipal_aao",
        field_id: "v_o",
        label_zh: "好氧区容积",
        dim: "VOLUME",
        values: { design: 100.5, avg: 80.25 },
      },
    ],
    warnings: [],
    ...overrides,
  };
}

describe("narrowCompareResponse 窄化门", () => {
  it("合法形状透传（顶层 10 键全在场）", () => {
    const report = narrowCompareResponse(fixtureReport());
    expect(report.condition_keys).toEqual(["avg", "design"]);
    expect(report.metrics[0]?.values.design).toBe(100.5);
  });

  it("顶层缺键拒（CompareViewError——查询 error 态呈现）", () => {
    const broken = fixtureReport() as unknown as Record<string, unknown>;
    delete broken["design_hash"];
    expect(() => narrowCompareResponse(broken)).toThrow(CompareViewError);
  });

  it("metrics 条目 values 非数值拒", () => {
    const broken = fixtureReport();
    (broken.metrics[0] as unknown as { values: Record<string, unknown> }).values = {
      design: "not-a-number",
    };
    expect(() => narrowCompareResponse(broken)).toThrow(/metrics\[0\]/);
  });
});

describe("锁定基准三件（D3）", () => {
  it("pinOf：合法 {pinned,pinned_hash} 读取+异形 null", () => {
    expect(pinOf({ pinned: ["design"], pinned_hash: "h" })).toEqual({
      pinned: ["design"],
      pinned_hash: "h",
    });
    expect(pinOf({})).toBeNull();
    expect(pinOf({ pinned: "design", pinned_hash: "h" })).toBeNull();
    expect(pinOf(null)).toBeNull();
  });

  it("isPinStale：hash 不同=过期；相同=新鲜；未锁定恒 false", () => {
    const report = fixtureReport();
    expect(isPinStale({ pinned: ["design"], pinned_hash: "hash-1" }, report)).toBe(false);
    expect(isPinStale({ pinned: ["design"], pinned_hash: "hash-2" }, report)).toBe(true);
    expect(isPinStale(null, report)).toBe(false);
  });

  it("filterLivePins：pinned∩现工况=存活，不在=失效", () => {
    const { live, expired } = filterLivePins(
      ["design", "design_offline_aao"],
      ["avg", "design", "design_offline_cass"],
    );
    expect(live).toEqual(["design"]);
    expect(expired).toEqual(["design_offline_aao"]);
  });
});

describe("矩阵行模型（D1）", () => {
  it("metricRowKey/metricLabel：unit.field 全序+label_zh 降级", () => {
    expect(metricRowKey("aao", "v_o")).toBe("aao.v_o");
    expect(metricLabel({ label_zh: "好氧区容积", field_id: "v_o" })).toBe("好氧区容积");
    expect(metricLabel({ label_zh: null, field_id: "v_o" })).toBe("v_o");
  });

  it("rowExtremes：max/min 标注+全等行零标注", () => {
    expect(rowExtremes({ design: 3, avg: 1, off: 2 }, ["design", "avg", "off"])).toEqual({
      maxKey: "design",
      minKey: "avg",
    });
    expect(rowExtremes({ design: 2, avg: 2 }, ["design", "avg"])).toEqual({
      maxKey: null,
      minKey: null,
    });
    expect(rowExtremes({ design: 5 }, ["design", "avg"])).toEqual({
      maxKey: null,
      minKey: null,
    });
  });

  it("formatMetricValue：整数千分位/3 位小数/小值有效数字", () => {
    expect(formatMetricValue(18466)).toBe("18,466");
    expect(formatMetricValue(2129.0928751763995)).toBe("2,129.093");
    expect(formatMetricValue(0.00012345)).toBe("0.000123");
  });
});
