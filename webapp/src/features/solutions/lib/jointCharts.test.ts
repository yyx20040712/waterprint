/**
 * 方案比选三图纯函数单测（批2d——帕累托前沿/平行坐标/龙卷风；沿
 * profileChart 投影层承载全部契约的先例：node 直测 option 纯对象）。
 *
 * 输入:  features/solutions/lib/jointCharts.ts 公开符号（node 环境）
 * 输出:  断言：paretoFront 非支配排序（全 minimize/相等向量同前沿/缺键与
 *        不可行不参与）/parallelAxesData 五轴+分档+入线资格（四真键+
 *        score 全 finite——sparse 不入线/轴域只按入线组合/全门外空面）/
 *        buildParetoOption 非资格不入被支配系列/tornadoBars 三键 avg 对
 *        变化率+design=0 诚实跳过+失守标签解析后按标签去重/三 buildOption
 *        纯对象（系列名/数据/轴名/反向/虚线）
 */
import { describe, expect, it } from "vitest";

import type { JointComboView } from "./jointView";
import { TRUE_METRIC_KEYS, metricLabel } from "./jointView";
import {
  buildParallelOption,
  buildParetoOption,
  buildTornadoOption,
  comboSummaryText,
  paretoFront,
  paretoTooltipLines,
  parallelAxesData,
  tornadoBars,
} from "./jointCharts";

/** combo 构造（四真键覆盖——dominance 断言载体）。 */
const comboOf = (
  four: [number, number, number, number],
  over: Partial<JointComboView> = {},
): JointComboView => ({
  params: { unitA: { p1: 1, p2: 2 } },
  feasible: true,
  sensitivity_degraded: false,
  failed_conditions: [],
  metrics: {
    cost_opex_yuan_a: four[0],
    power_total_kwh_d: four[1],
    carbon_intensity_kgco2e_m3: four[2],
    cost_capex_yuan: four[3],
    "avg.cost_opex_yuan_a": four[0] * 1.1,
    "avg.power_total_kwh_d": four[1] * 0.9,
    "avg.carbon_intensity_kgco2e_m3": four[2],
  },
  score: null,
  ...over,
});

describe("paretoFront（四键非支配排序——全 minimize）", () => {
  it("全维占优 → 被支配者出前沿（支配=全 ≤ 且至少一维 <）", () => {
    const a = comboOf([100, 50, 0.5, 1000]);
    const b = comboOf([120, 60, 0.6, 1200]);
    const front = paretoFront([a, b]);
    expect([...front]).toEqual([0]);
  });

  it("-tradeoff 两方案互不支配 → 同前沿", () => {
    const a = comboOf([100, 50, 0.5, 1000]);
    const c = comboOf([90, 70, 0.5, 1000]); // opex 优/能耗劣
    const front = paretoFront([a, c]);
    expect([...front]).toEqual([0, 1]);
  });

  it("相等向量互不支配 → 同前沿（四维性质）", () => {
    const a = comboOf([100, 50, 0.5, 1000]);
    const d = comboOf([100, 50, 0.5, 1000]);
    expect([...paretoFront([a, d])]).toEqual([0, 1]);
  });

  it("传递链：a 支配 b、b 支配 c → 前沿仅 a", () => {
    const a = comboOf([100, 50, 0.5, 1000]);
    const b = comboOf([110, 55, 0.55, 1100]);
    const c = comboOf([120, 60, 0.6, 1200]);
    expect([...paretoFront([a, b, c])]).toEqual([0]);
  });

  it("不可行组合不参与（feasible=false 即使非支配也不入前沿）", () => {
    const a = comboOf([100, 50, 0.5, 1000]);
    const f = comboOf([90, 40, 0.4, 900], { feasible: false });
    expect([...paretoFront([a, f])]).toEqual([0]);
  });

  it("四真键缺席的组合不参与（sparse 防御——缺键组合不支配也不被支配）", () => {
    const a = comboOf([100, 50, 0.5, 1000]);
    const g = comboOf([90, 40, 0.4, 0]);
    delete (g.metrics as Record<string, number>)["cost_capex_yuan"];
    expect([...paretoFront([a, g])]).toEqual([0]);
  });
});

describe("parallelAxesData（四键+score 五轴——分档线数据）", () => {
  it("五轴序=四真键+score；min/max 取数据域；单值轴邻域扩展（min<max）", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 });
    const b = comboOf([120, 60, 0.6, 1200], { score: 2 });
    const c = comboOf([90, 70, 0.4, 1100], { score: 3 });
    const data = parallelAxesData([a, b, c]);
    expect(data.axes.map((axis) => axis.key)).toEqual([...TRUE_METRIC_KEYS, "score"]);
    expect(data.axes.map((axis) => axis.label)).toEqual([
      ...TRUE_METRIC_KEYS.map((key) => metricLabel(key)),
      metricLabel("score"),
    ]);
    const opex = data.axes[0]!;
    expect(opex.min).toBe(90);
    expect(opex.max).toBe(120);
    const carbon = data.axes[2]!; // a 0.5 / b 0.6 / c 0.4 → 域 [0.4,0.6]
    expect(carbon.min).toBe(0.4);
    expect(carbon.max).toBe(0.6);
    const single = parallelAxesData([a]); // 单组合：各轴 min<max（邻域扩展）
    for (const axis of single.axes) {
      expect(axis.min).toBeLessThan(axis.max);
    }
  });

  it("线值序随轴序；score 三分位分档（升序 best/mid/worst）；降权标记透传", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 });
    const b = comboOf([120, 60, 0.6, 1200], { score: 2 });
    const c = comboOf([90, 70, 0.4, 1100], { score: 3, sensitivity_degraded: true });
    const data = parallelAxesData([a, b, c]);
    expect(data.lines).toHaveLength(3);
    expect(data.lines.map((line) => line.band)).toEqual(["best", "mid", "worst"]);
    expect(data.lines[2]?.degraded).toBe(true);
    expect(data.lines[0]?.values).toEqual([100, 50, 0.5, 1000, 1]);
  });

  it("score 缺席（null）组合不入线（五轴需全值——诚实排除不造假）", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 });
    const noScore = comboOf([90, 40, 0.4, 900]);
    const data = parallelAxesData([a, noScore]);
    expect(data.lines.map((line) => line.comboIndex)).toEqual([0]);
  });

  it("sparse 键组合不入线；轴域只按入线组合取值（资格门=四真键+score 全 finite）", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 });
    const b = comboOf([120, 60, 0.6, 1200], { score: 2 });
    const sparse = comboOf([40, 40, 0.4, 900], { score: 3 });
    delete (sparse.metrics as Record<string, number>)["cost_capex_yuan"];
    const data = parallelAxesData([a, b, sparse]);
    expect(data.lines.map((line) => line.comboIndex)).toEqual([0, 1]);
    const opex = data.axes[0]!;
    expect(opex.min).toBe(100); // sparse 的 40 被资格门排除——不入轴域
    expect(opex.max).toBe(120);
  });

  it("全组合资格门外 → 空 axes/lines（组件空态数据面——不造假轴）", () => {
    const noScore = comboOf([100, 50, 0.5, 1000]); // score null 门外
    const sparse = comboOf([90, 40, 0.4, 900], { score: 2 });
    delete (sparse.metrics as Record<string, number>)["cost_capex_yuan"]; // 缺键门外
    expect(parallelAxesData([noScore, sparse])).toEqual({ axes: [], lines: [] });
  });
});

describe("tornadoBars（avg vs design 指标漂移+失守工况标签）", () => {
  it("三键 avg 对：(avg-design)/design 双向变化率；capex 无 avg 对不入", () => {
    const combo = comboOf([100, 50, 0.5, 1000]);
    const data = tornadoBars(combo);
    expect(data.bars.map((bar) => bar.designKey)).toEqual([
      "cost_opex_yuan_a",
      "power_total_kwh_d",
      "carbon_intensity_kgco2e_m3",
    ]);
    expect(data.bars[0]?.ratio).toBeCloseTo(0.1, 12); // (110-100)/100
    expect(data.bars[1]?.ratio).toBeCloseTo(-0.1, 12); // (45-50)/50
    expect(data.bars[2]?.ratio).toBeCloseTo(0, 12);
    expect(data.skipped).toEqual([]);
  });

  it("design=0 或 avg 对缺席 → 诚实跳过（skipped 记键不造假数据）", () => {
    const zeroDesign = comboOf([0, 50, 0.5, 1000]);
    const data0 = tornadoBars(zeroDesign);
    expect(data0.bars.map((bar) => bar.designKey)).toEqual([
      "power_total_kwh_d",
      "carbon_intensity_kgco2e_m3",
    ]);
    expect(data0.skipped).toEqual(["cost_opex_yuan_a"]);
    const noAvg = comboOf([100, 50, 0.5, 1000]);
    delete (noAvg.metrics as Record<string, number>)["avg.power_total_kwh_d"];
    const dataAvg = tornadoBars(noAvg);
    expect(dataAvg.skipped).toEqual(["power_total_kwh_d"]);
  });

  it("failed_conditions 解析去重：三段式出水失守+两段式 opex 缺席", () => {
    const combo = comboOf([100, 50, 0.5, 1000], {
      failed_conditions: [
        "design:gb18918.level_a:BOD5+SS",
        "design:gb18918.level_a:BOD5+SS", // 重复条目
        "offline_wet:gb18918.level_b:NH3N",
        "design:opex_absent",
      ],
    });
    const data = tornadoBars(combo);
    expect(data.failedLabels).toEqual([
      "design（gb18918.level_a）：BOD5+SS",
      "offline_wet（gb18918.level_b）：NH3N",
      "design：opex_absent",
    ]);
  });

  it("失守标签解析后按标签去重（不同原文同标签只呈现一次）", () => {
    const combo = comboOf([100, 50, 0.5, 1000], {
      failed_conditions: [
        "design:opex_absent", // 两段式
        "design:opex_absent:", // 空尾三段式——解析得同标签
      ],
    });
    expect(tornadoBars(combo).failedLabels).toEqual(["design：opex_absent"]);
  });
});

describe("三图 option 纯对象（投影层承载全部契约）", () => {
  it("buildParetoOption：前沿/被支配双系列+轴名标签+缺轴键组合跳过", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 }); // 前沿
    const b = comboOf([120, 60, 0.6, 1200], { score: 2 }); // 被 a 支配
    const front = paretoFront([a, b]);
    const option = buildParetoOption(
      [a, b],
      "cost_opex_yuan_a",
      "cost_capex_yuan",
      front,
    );
    expect(option.series.map((series) => series.name)).toEqual(["前沿方案", "被支配方案"]);
    expect(option.series[0]?.data).toEqual([{ value: [100, 1000], combo: a }]);
    expect(option.series[1]?.data).toEqual([{ value: [120, 1200], combo: b }]);
    expect(option.xAxis.name).toBe(metricLabel("cost_opex_yuan_a"));
    expect(option.yAxis.name).toBe(metricLabel("cost_capex_yuan"));
    // 换轴投影不重算前沿：front 集不变，仅显示面换（注记断言——四维性质）
    const swapped = buildParetoOption([a, b], "power_total_kwh_d", "cost_opex_yuan_a", front);
    expect(swapped.series[0]?.data).toEqual([{ value: [50, 100], combo: a }]);
    // 缺选中轴键的组合不入任何系列（无值点不画）
    const g = comboOf([90, 40, 0.4, 900]);
    delete (g.metrics as Record<string, number>)["cost_capex_yuan"];
    const withG = buildParetoOption([a, g], "cost_opex_yuan_a", "cost_capex_yuan", front);
    expect(withG.series[1]?.data).toEqual([]); // g 缺 y 轴键——灰系列空
  });

  it("非资格组合不入「被支配方案」系列（frontEligible 失败不画——口径统一）", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 }); // 前沿
    const ineligible = comboOf([90, 40, 0.4, 900], { score: 2, feasible: false });
    const front = paretoFront([a, ineligible]); // 非资格不参与排序——仅 a
    const option = buildParetoOption(
      [a, ineligible],
      "cost_opex_yuan_a",
      "cost_capex_yuan",
      front,
    );
    expect(option.series[0]?.data).toEqual([{ value: [100, 1000], combo: a }]);
    expect(option.series[1]?.data).toEqual([]); // 非资格不入被支配系列——不画
  });

  it("buildParallelOption：三档系列+降权虚线+反向开关作用全轴", () => {
    const a = comboOf([100, 50, 0.5, 1000], { score: 1 });
    const b = comboOf([120, 60, 0.6, 1200], { score: 2 });
    const c = comboOf([90, 70, 0.4, 1100], { score: 3, sensitivity_degraded: true });
    const data = parallelAxesData([a, b, c]);
    const inverted = buildParallelOption(data, true);
    expect(inverted.parallelAxis.every((axis) => axis.inverse)).toBe(true);
    const normal = buildParallelOption(data, false);
    expect(normal.parallelAxis.every((axis) => axis.inverse)).toBe(false);
    expect(normal.series.map((series) => series.name)).toEqual(["优档", "中档", "差档"]);
    const worst = normal.series[2]!;
    expect(worst.data).toEqual([{ value: [90, 70, 0.4, 1100, 3], lineStyle: { type: "dashed" } }]);
    expect(normal.series[0]?.data[0]).toEqual({ value: [100, 50, 0.5, 1000, 1] });
  });

  it("buildTornadoOption：水平双向条（类目=指标标签+值=变化率）", () => {
    const combo = comboOf([100, 50, 0.5, 1000]);
    const data = tornadoBars(combo);
    const option = buildTornadoOption(data);
    expect(option.yAxis.data).toEqual(data.bars.map((bar) => bar.label));
    expect(option.series[0]?.data).toEqual(data.bars.map((bar) => bar.ratio));
    expect(option.xAxis.name).toContain("相对变化率");
  });
});

describe("tooltip 与参数摘要（纯文本面）", () => {
  it("comboSummaryText：单元: 参数=值 串接；多单元分号分隔", () => {
    const combo = comboOf([100, 50, 0.5, 1000]);
    expect(comboSummaryText(combo)).toBe("unitA: p1=1, p2=2");
    combo.params["unitB"] = { q1: 0.5 };
    expect(comboSummaryText(combo)).toBe("unitA: p1=1, p2=2；unitB: q1=0.5");
  });

  it("paretoTooltipLines：四键值+score+参数摘要（score null=缺失不造假）", () => {
    const combo = comboOf([100, 50, 0.5, 1000], { score: 0.9 });
    const lines = paretoTooltipLines(combo);
    expect(lines).toHaveLength(6);
    expect(lines[0]).toBe("运行成本（元/年）：100");
    expect(lines[4]).toBe("综合得分（越小越优）：0.9");
    expect(lines[5]).toBe("参数：unitA: p1=1, p2=2");
    const noScore = paretoTooltipLines(comboOf([100, 50, 0.5, 1000]));
    expect(noScore[4]).toBe("综合得分（越小越优）：（缺失）");
  });
});
