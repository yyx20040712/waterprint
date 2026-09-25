/**
 * 联合枚举结果装配组件测试（批2d——沿 TaskPanel.test.tsx SSR 先例：
 * renderToString 零 jsdom 真渲染 antd 树；echarts 壳 useEffect 零执行
 * ——init 不触发，仅断言容器/表行/页签文案）。
 *
 * 输入:  JointSolutionsPanel（窄化产物 JointResultView——组件零形状判断）
 * 输出:  断言：combos 表行数（排名/四键/score/降权标记）+三图 Tabs 页签
 *        文案（forceRender 全页签 SSR 在场）+无解诊断投影（combos 空=
 *        done 合法终态——beam.py 真形两态：stage_empty 载荷嵌套 stage 键
 *        /final_infeasible 仅 note；未知 kind 原样 JSON 摘要不吞）+龙卷风
 *        空态文案（无 avg 对不造假）+平行坐标空态（资格门外无可绘文案）
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
  // 剥离 React SSR 相邻文本节点间的 <!-- --> 分隔标记（DOM 文本内容等价断言）
  return renderToString(<JointSolutionsPanel result={result} />).replace(
    /<!-- -->/g,
    "",
  );
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

  it("combos 空+stage_empty → 分段无解标签+stage 层冲突内容展开（beam.py:444 真形——载荷嵌套 stage 键）", () => {
    const html = render({
      unit_ids: ["unitA", "unitB"],
      diagnosis: {
        kind: "stage_empty",
        stage: {
          minimal_conflicts: [["aao_1.n_pool", "cass_1.n_pool"]],
          fail_counts: { "aao_1.n_pool": 12 },
          suggestions: [
            {
              param_key: "aao_1.n_pool",
              direction: "下调",
              magnitude: 1,
              basis: "最小冲突集消解",
              affected_conflicts: ["aao_1.n_pool"],
              expected_effect: "缓解分段无解",
            },
          ],
          frozen_prefix: {},
        },
      },
      combos: [],
    });
    expect(html).toContain("无解诊断");
    expect(html).toContain("分段无解（stage_empty）"); // kind 标签在场
    expect(html).toContain("aao_1.n_pool、cass_1.n_pool"); // stage 层冲突内容展开
    expect(html).toContain("aao_1.n_pool：12 行不可行"); // 失败计数展开
    expect(html).toContain("缓解分段无解"); // 建议内容展开
    expect(html).not.toContain("帕累托前沿图"); // 无方案不进三图面
  });

  it("combos 空+final_infeasible → 终判不可行 note 显著呈现（冲突键空=缺失呈现不造假）", () => {
    const html = render({
      unit_ids: ["unitA", "unitB"],
      diagnosis: {
        kind: "final_infeasible",
        relaxed: false,
        note: "末段组合全不可行且无可放宽 range 域（离散档网格无连续域）",
      },
      combos: [],
    });
    expect(html).toContain("终判不可行（final_infeasible）"); // kind 标签在场
    expect(html).toContain(
      "终判不可行：末段组合全不可行且无可放宽 range 域（离散档网格无连续域）",
    ); // note 文案显著呈现
    expect(html).toContain("（载荷缺失）"); // 冲突消费面空——DiagnosisPanel 缺失呈现
  });

  it("combos 空+未知 kind → 原样呈现 kind+JSON 摘要（fail-visible 不吞）", () => {
    const html = render({
      unit_ids: ["unitA", "unitB"],
      diagnosis: { kind: "novel_kind", detail: "异常负载文本" },
      combos: [],
    });
    expect(html).toContain("未知诊断类型（novel_kind）");
    expect(html).toContain("异常负载文本"); // JSON 摘要在场
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

  it("平行坐标空态：全组合资格门外 → 无可绘方案文案（不造假轴）", () => {
    const allOut: JointResultView = {
      unit_ids: ["unitA", "unitB"],
      diagnosis: null,
      combos: [
        comboOf([100, 50, 0.5, 1000], { score: null }), // score 缺席——资格门外
      ],
    };
    const html = render(allOut);
    expect(html).toContain("无可绘方案（指标/得分不全场）");
  });
});
