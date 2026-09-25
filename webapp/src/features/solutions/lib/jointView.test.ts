/**
 * 联合枚举结果窄化门纯函数单测（批2d——R-B44b-4 兑现；沿 solutionsView
 * D4 窄化门纪律先例：非法形状抛 JointViewError 带定位，error 呈现非静默）。
 *
 * 输入:  features/solutions/lib/jointView.ts 公开符号（node 环境）
 * 输出:  断言：combos 载荷 unknown→JointResultView 逐字段门（params 双层
 *        数值映射/feasible+sensitivity_degraded 布尔/failed_conditions 字符串
 *        组/metrics 数值键白名单+有限数/score number|null）+指标标签中文面
 *        +越界/型异逐门拒（消息带定位）
 */
import { describe, expect, it } from "vitest";

import {
  AVG_METRIC_KEYS,
  INDICATOR_KEYS,
  TRUE_METRIC_KEYS,
  metricLabel,
  narrowJointResult,
} from "./jointView";

/** 合法 combo 夹具（批2b 四真键全量+avg 三键+六出水指标——worker asdict 实形）。 */
const COMBO = {
  params: { unitA: { p1: 1, p2: 2 }, unitB: { q1: 0.5 } },
  feasible: true,
  sensitivity_degraded: false,
  failed_conditions: ["design:gb18918.level_a:BOD5+SS"],
  metrics: {
    cost_opex_yuan_a: 100,
    power_total_kwh_d: 50,
    carbon_intensity_kgco2e_m3: 0.5,
    cost_capex_yuan: 1000,
    "avg.cost_opex_yuan_a": 110,
    "avg.power_total_kwh_d": 55,
    "avg.carbon_intensity_kgco2e_m3": 0.55,
    BOD5: 8,
    CODCR: 40,
    SS: 10,
    NH3N: 5,
    TN: 15,
    TP: 0.5,
  },
  score: 0.9,
};

/** 合法顶层载荷（worker _run_joint_enumerate result 直返实形）。 */
const PAYLOAD = {
  state: "done",
  search_semantics: { mode: "beam" },
  combos: [COMBO],
  diagnosis: null,
  budget_usage: { evals: 10 },
  unit_ids: ["unitA", "unitB"],
  project_id: "proj-1",
};

describe("narrowJointResult（联合枚举结果窄化门）", () => {
  it("合法载荷逐字段投影（combos/diagnosis/unit_ids——多余键宽容不校验）", () => {
    const view = narrowJointResult(PAYLOAD);
    expect(view.combos).toHaveLength(1);
    expect(view.combos[0]).toEqual(COMBO);
    expect(view.unit_ids).toEqual(["unitA", "unitB"]);
    expect(view.diagnosis).toBeNull();
  });

  it("diagnosis 对象/缺省透传（宽容面——DiagnosisPanel 自窄化）", () => {
    const withDiag = narrowJointResult({
      ...PAYLOAD,
      diagnosis: { minimal_conflicts: [["k"]], fail_counts: { k: 1 }, suggestions: [] },
    });
    expect(withDiag.diagnosis).toEqual({
      minimal_conflicts: [["k"]],
      fail_counts: { k: 1 },
      suggestions: [],
    });
    const noDiag = narrowJointResult({ combos: [], unit_ids: ["a", "b"] });
    expect(noDiag.diagnosis).toBeNull();
  });

  it("顶层非法：非对象/combos 缺失/combos 非数组/unit_ids 非字符串组 → 抛", () => {
    expect(() => narrowJointResult(null)).toThrow(/联合枚举/);
    expect(() => narrowJointResult({ unit_ids: ["a"] })).toThrow(/combos/);
    expect(() => narrowJointResult({ combos: "nope", unit_ids: ["a"] })).toThrow(/combos/);
    expect(() =>
      narrowJointResult({ combos: [], unit_ids: ["a", 1] }),
    ).toThrow(/unit_ids/);
    expect(() => narrowJointResult({ combos: [], unit_ids: "ab" })).toThrow(/unit_ids/);
  });

  it("combo 条目非法逐门拒（消息带位置定位）", () => {
    const bad = (combo: unknown) => narrowJointResult({ ...PAYLOAD, combos: [combo] });
    expect(() => bad("nope")).toThrow(/combos\[0\]/);
    expect(() => bad({ ...COMBO, feasible: "yes" })).toThrow(/feasible/);
    expect(() => bad({ ...COMBO, sensitivity_degraded: 1 })).toThrow(/sensitivity_degraded/);
    expect(() => bad({ ...COMBO, failed_conditions: ["a", 2] })).toThrow(/failed_conditions/);
    expect(() => bad({ ...COMBO, score: "0.9" })).toThrow(/score/);
    expect(() => bad({ ...COMBO, score: Number.NaN })).toThrow(/score/);
  });

  it("params 双层映射门：非对象/值非有限数 → 抛（带单元与参数定位）", () => {
    const bad = (params: unknown) => narrowJointResult({ ...PAYLOAD, combos: [{ ...COMBO, params }] });
    expect(() => bad({ unitA: { p1: "1" } })).toThrow(/params/);
    expect(() => bad({ unitA: { p1: Number.POSITIVE_INFINITY } })).toThrow(/params/);
    expect(() => bad({ unitA: [1] })).toThrow(/params/);
    expect(() => bad("nope")).toThrow(/params/);
  });

  it("metrics 数值键白名单：白名单外键 → 拒（越界键名入消息）", () => {
    const bad = (metrics: unknown) => narrowJointResult({ ...PAYLOAD, combos: [{ ...COMBO, metrics }] });
    expect(() =>
      bad({ ...COMBO.metrics, cost_opex_eur_a: 1 }),
    ).toThrow(/cost_opex_eur_a/);
    expect(() => bad({ ...COMBO.metrics, "avg.cost_capex_yuan": 1 })).toThrow(
      /avg\.cost_capex_yuan/,
    );
    expect(() => bad({ cost_opex_yuan_a: "100" })).toThrow(/metrics/);
    expect(() => bad("nope")).toThrow(/metrics/);
  });

  it("metrics 子集合法（四真键/avg 对/出水指标均可缺席——sparse 诚实面）", () => {
    const view = narrowJointResult({
      ...PAYLOAD,
      combos: [{ ...COMBO, metrics: { cost_opex_yuan_a: 100 }, score: null }],
    });
    expect(view.combos[0]?.metrics).toEqual({ cost_opex_yuan_a: 100 });
    expect(view.combos[0]?.score).toBeNull();
  });
});

describe("指标键面与中文标签", () => {
  it("三键族常量与 core 键面同源（四真键+avg 三键+六出水指标）", () => {
    expect(TRUE_METRIC_KEYS).toEqual([
      "cost_opex_yuan_a",
      "power_total_kwh_d",
      "carbon_intensity_kgco2e_m3",
      "cost_capex_yuan",
    ]);
    expect(AVG_METRIC_KEYS).toEqual([
      "avg.cost_opex_yuan_a",
      "avg.power_total_kwh_d",
      "avg.carbon_intensity_kgco2e_m3",
    ]);
    expect(INDICATOR_KEYS).toEqual(["BOD5", "CODCR", "SS", "NH3N", "TN", "TP"]);
  });

  it("metricLabel：四真键/avg 前缀/score 中文标签；未知键原样回退（诚实面）", () => {
    expect(metricLabel("cost_opex_yuan_a")).toBe("运行成本（元/年）");
    expect(metricLabel("power_total_kwh_d")).toBe("能耗（kWh/d）");
    expect(metricLabel("carbon_intensity_kgco2e_m3")).toBe("碳强度（kgCO₂e/m³）");
    expect(metricLabel("cost_capex_yuan")).toBe("建设投资（元）");
    expect(metricLabel("avg.cost_opex_yuan_a")).toBe("运行成本·均值（元/年）");
    expect(metricLabel("BOD5")).toBe("BOD5（mg/L）");
    expect(metricLabel("score")).toBe("综合得分（越小越优）");
    expect(metricLabel("unknown_key")).toBe("unknown_key");
  });
});
