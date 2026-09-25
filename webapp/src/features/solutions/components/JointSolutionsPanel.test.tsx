/**
 * 联合枚举结果装配组件测试（批2d——沿 TaskPanel.test.tsx SSR 先例：
 * renderToString 零 jsdom 真渲染 antd 树；echarts 壳 useEffect 零执行
 * ——init 不触发，仅断言容器/表行/页签文案）。
 *
 * 输入:  JointSolutionsPanel（窄化产物 JointResultView——组件零形状判断）
 * 输出:  断言：combos 表行数（排名/四键/score/降权标记）+三图 Tabs 页签
 *        文案（forceRender 全页签 SSR 在场）+无解诊断面（combos 空=
 *        done 合法终态沿枚举同款语义）+龙卷风空态文案（无 avg 对不造假）
 */
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { JointComboView, JointResultView } from "../lib/jointView";
import { JointSolutionsPanel } from "./JointSolutionsPanel";

/** combo 构造（四真键+avg 对——表行与三图数据面）。 */
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
  score: 0.9,
  ...over,
});

const RESULT: JointResultView = {
  unit_ids: ["unitA", "unitB"],
  diagnosis: null,
  combos: [
    comboOf([100, 50, 0.5, 1234567]),
    comboOf([120, 60, 0.6, 2345678], {
      sensitivity_degraded: true,
      failed_conditions: ["design:gb18918.level_a:BOD5+SS"],
    }),
    comboOf([90, 70, 0.4, 3456789], { score: null }),
  ],
};

function render(result: JointResultView): string {
  return renderToString(<JointSolutionsPanel result={result} />);
}

describe("JointSolutionsPanel（combos 表+三图 Tabs 装配）", () => {
  it("combos 表：三行排名+四键列+score 列+降权标记（千分位格式）", () => {
    const html = render(RESULT);
    expect(html).toContain("排名"); // 列头
    expect(html).toContain("综合得分");
    expect(html).toContain("1,234,567"); // formatSolutionValue 整数千分位
    expect(html).toContain("0.900"); // score 三位小数
    expect(html).toContain("（缺失）"); // score null 诚实呈现
    expect(html).toContain("敏感工况失守"); // 降权标记
    expect(html).toContain("unitA: p1=1, p2=2"); // 参数摘要列
  });

  it("三图 Tabs 页签文案在场（forceRender——SSR 全页签渲染）", () => {
    const html = render(RESULT);
    expect(html).toContain("帕累托前沿图");
    expect(html).toContain("平行坐标图");
    expect(html).toContain("敏感性龙卷风图");
  });

  it("帕累托轴选择器与龙卷风方案选择器在场（四键可换轴）", () => {
    const html = render(RESULT);
    expect(html).toContain("运行成本（元/年）"); // 轴选项 label
    expect(html).toContain("建设投资（元）");
    expect(html).toContain("方案 1"); // 龙卷风默认首位=排名最高
  });

  it("combos 空 → 无解诊断面（done 合法终态沿枚举同款语义）", () => {
    const html = render({
      unit_ids: ["unitA", "unitB"],
      diagnosis: { minimal_conflicts: [["k1", "k2"]], fail_counts: {}, suggestions: [] },
      combos: [],
    });
    expect(html).toContain("无解诊断");
    expect(html).toContain("k1、k2");
    expect(html).not.toContain("帕累托前沿图"); // 无方案不进三图面
  });

  it("龙卷风空态：无 avg 对组合不造假数据（诚实文案在场）", () => {
    const noAvg: JointResultView = {
      ...RESULT,
      combos: [comboOf([100, 50, 0.5, 1000])],
    };
    delete (noAvg.combos[0]!.metrics as Record<string, number>)["avg.cost_opex_yuan_a"];
    delete (noAvg.combos[0]!.metrics as Record<string, number>)["avg.power_total_kwh_d"];
    delete (noAvg.combos[0]!.metrics as Record<string, number>)["avg.carbon_intensity_kgco2e_m3"];
    const html = render(noAvg);
    expect(html).toContain("无 avg/design 成对指标");
  });
});
