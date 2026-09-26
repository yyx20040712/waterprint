/**
 * 龙卷风图数据面纯函数（批2d 三图之三数据域——批6e 预算墙拆件自
 * jointCharts.ts 迁入〔本件 510>500 顶墙触发，§2 超限拆文件〕；avg 对
 * 相对变化率+批6e 全工况幅度轴检修系列投影）。
 *
 * 输入:  JointComboView（jointView 窄化产物——本件零形状判断）+
 *        SensitivityReportView（批6e 全工况投影——/api/calc/sensitivity
 *        窄化产物）
 * 输出:  tornadoBars（三键 avg 对变化率+失守工况标签解析去重）+
 *        sensitivitySeries（逐 design_offline_* 检修系列相对率）+
 *        buildTornadoOption（水平双向条 option——多系列=avg+检修族）
 *
 * 规格说明（批2d 简报③+批6e 升级；门一回炉双守卫在册）：
 *   - 三键 avg 对（cost_opex/energy/carbon——capex 无 avg 对）的
 *     (avg-design)/design 双向条；design=0 或 avg 对缺席=诚实跳过
 *     （skipped 记键不造假）；六出水指标无 avg 对不入图；
 *     failed_conditions 解析去重（三段式出水失守+两段式 opex_absent）；
 *   - 批6e 全工况幅度轴：sensitivitySeries 逐 design_offline_<unit>
 *     检修系列（sensitivity 报告快照投影——相对率=deltas/design_value，
 *     近零基线 |design|<1e-9 与除后非有限双守卫→null+skipped 诚实跳过；
 *     全键缺席工况不成系列——防空图例）；系列序=报告 condition_keys 序
 *     （服务端字典序——确定性）；buildTornadoOption 多系列挂 legend，
 *     sensitivity 缺席=单 avg 系列旧观（向后兼容）；
 *   - 零运行期库 import（node 测试零增重——jointView 同款纪律）。
 */
import type { JointComboView } from "./jointView";
import { AVG_METRIC_KEYS, metricLabel } from "./jointView";
import {
  OFFLINE_PREFIX,
  type SensitivityReportView,
} from "./sensitivityView";

/** 龙卷风条（avg 对相对变化率）。 */
export type TornadoBar = {
  avgKey: string;
  designKey: string;
  label: string;
  ratio: number;
};

/** 龙卷风数据面（bars+诚实跳过键+失守工况标签去重清单）。 */
export type TornadoData = {
  bars: TornadoBar[];
  skipped: string[];
  failedLabels: string[];
};

/** 龙卷风 option（水平双向条——正负值自然双向；批6e 多系列=avg+检修族）。 */
export type TornadoChartOption = {
  tooltip: Record<string, unknown>;
  legend?: { data: string[]; top: number };
  grid: { left: number; right: number; top: number; bottom: number };
  xAxis: { type: "value"; name: string };
  yAxis: { type: "category"; data: string[] };
  series: { name: string; type: "bar"; data: (number | null)[]; itemStyle: { color: string } }[];
};

/** 龙卷风条色（中性蓝——正=变差/负=变好双向同色，方向由条向呈现）。 */
const TORNADO_COLOR = "#1677ff";

/** 检修系列色循环（灰阶族——与 avg 主色区分；幅值方向由条向呈现；
 *  超 6 工况循环复用（图例同名系列语义不变——回炉 W4 注记）。 */
const OFFLINE_COLORS: readonly string[] = [
  "#8c8c8c", "#bfbfbf", "#595959", "#d9d9d9", "#434343", "#a3a3a3",
];

/** 灰阶循环回退色（noUncheckedIndexedAccess 满足——首色同值）。 */
const OFFLINE_COLOR_FALLBACK = "#8c8c8c";

/** 相对率近零基线守卫（回炉 W1）：|design| 低于此值视为近零——相对率
 *  无意义（放大爆炸），诚实跳过 null+skipped（除零守卫之外的第二道）。 */
const DESIGN_EPS = 1e-9;

/** avg 对声明（avg 键→design 键——单源派生 jointView AVG_METRIC_KEYS；
 *  capex 无 avg 对，六出水指标无 avg 对）。 */
const AVG_PAIRS: readonly { avgKey: string; designKey: string }[] =
  AVG_METRIC_KEYS.map((avgKey) => ({
    avgKey,
    designKey: avgKey.slice("avg.".length),
  }));

/** 失守工况原文→呈现标签（"cond:std:IND+IND"→"cond（std）：IND+IND"；
 *  两段式"cond:tail"→"cond：tail"；空尾三段式同两段式；非注记格式原样）。 */
function parseFailedLabel(item: string): string {
  const firstColon = item.indexOf(":");
  if (firstColon === -1) {
    return item; // 非注记格式原样（诚实呈现不猜语义）
  }
  const conditionKey = item.slice(0, firstColon);
  const secondColon = item.indexOf(":", firstColon + 1);
  if (secondColon === -1) {
    return `${conditionKey}：${item.slice(firstColon + 1)}`;
  }
  const middle = item.slice(firstColon + 1, secondColon);
  const tail = item.slice(secondColon + 1);
  return tail === ""
    ? `${conditionKey}：${middle}`
    : `${conditionKey}（${middle}）：${tail}`;
}

/**
 * 龙卷风数据面（选定方案单 combo）：三键 avg 对相对变化率
 * (avg-design)/design（design=0 或对缺席=诚实跳过记键）+failed_conditions
 * 标签解析去重（解析后按标签去重——不同原文同标签只呈现一次）。
 */
export function tornadoBars(combo: JointComboView): TornadoData {
  const bars: TornadoBar[] = [];
  const skipped: string[] = [];
  for (const { avgKey, designKey } of AVG_PAIRS) {
    const avg = combo.metrics[avgKey];
    const design = combo.metrics[designKey];
    if (avg === undefined || design === undefined || design === 0) {
      skipped.push(designKey);
      continue;
    }
    bars.push({
      avgKey,
      designKey,
      label: metricLabel(designKey),
      ratio: (avg - design) / design,
    });
  }
  const seenLabels = new Set<string>();
  const failedLabels: string[] = [];
  for (const item of combo.failed_conditions) {
    const label = parseFailedLabel(item);
    if (seenLabels.has(label)) {
      continue; // 解析后按标签去重（原文异形同标签只呈现一次）
    }
    seenLabels.add(label);
    failedLabels.push(label);
  }
  return { bars, skipped, failedLabels };
}

/** 检修工况系列（批6e——design_offline_<unit> 相对 design 幅度）。 */
export type SensitivitySeries = {
  conditionKey: string;
  label: string;
  ratios: (number | null)[];
};

/**
 * 检修工况系列数据（批6e）：sensitivity 报告 × avg 对键族——相对率
 * =deltas[cond]/design_value（绝对差服务端返回，相对率归呈现面——除零
 * 与近零基线双守卫：design=0 或 |design|<1e-9 相对率无意义，行缺席/
 * 工况值缺席均 null 诚实跳过并记 skipped 注记；系列序=报告
 * condition_keys 序[服务端字典序——确定性]；全键缺席的工况不成系列
 * （skipped 记注——compare R2 全空行不呈现同口径，防空图例）。
 */
export function sensitivitySeries(
  sensitivity: SensitivityReportView,
  designKeys: readonly string[],
): { series: SensitivitySeries[]; skipped: string[] } {
  const rowByField = new Map(sensitivity.rows.map((row) => [row.field_id, row]));
  const series: SensitivitySeries[] = [];
  const skipped: string[] = [];
  for (const conditionKey of sensitivity.condition_keys) {
    const label = `检修 ${conditionKey.slice(OFFLINE_PREFIX.length)}`;
    const ratios: (number | null)[] = designKeys.map((key) => {
      const row = rowByField.get(key);
      if (row === undefined) {
        skipped.push(`${label}：${metricLabel(key)} 行缺席`);
        return null;
      }
      const delta = row.deltas[conditionKey];
      if (delta === undefined) {
        skipped.push(`${label}：${metricLabel(key)} 工况值缺席`);
        return null;
      }
      if (row.design_value === 0 || Math.abs(row.design_value) < DESIGN_EPS) {
        skipped.push(`${label}：${metricLabel(key)} design 近零`);
        return null;
      }
      const ratio = delta / row.design_value;
      if (!Number.isFinite(ratio)) {
        skipped.push(`${label}：${metricLabel(key)} 相对率非有限`);
        return null; // 溢出面（k1-W3 回炉）——诚实跳过防坐标轴爆炸
      }
      return ratio;
    });
    if (ratios.every((ratio) => ratio === null)) {
      skipped.push(`${label}：全键缺席（系列不呈现）`);
      continue;
    }
    series.push({ conditionKey, label, ratios });
  }
  return { series, skipped };
}

/**
 * 龙卷风 option：水平双向条（类目=指标标签+值=相对变化率）；批6e 全工况
 * 幅度轴——sensitivity 在场时 avg 系列后逐检修系列（灰阶循环色），多系列
 * 挂 legend；缺席（null/无条件）=单 avg 系列旧观（向后兼容面）。
 */
export function buildTornadoOption(
  data: TornadoData,
  sensitivity: SensitivityReportView | null = null,
): TornadoChartOption {
  const series: TornadoChartOption["series"] = [
    {
      name: "avg 相对 design 变化率",
      type: "bar",
      data: data.bars.map((bar) => bar.ratio),
      itemStyle: { color: TORNADO_COLOR },
    },
  ];
  if (sensitivity !== null && sensitivity.condition_keys.length > 0) {
    const offline = sensitivitySeries(
      sensitivity,
      data.bars.map((bar) => bar.designKey),
    );
    offline.series.forEach((item, index) => {
      series.push({
        name: item.label,
        type: "bar",
        data: item.ratios,
        itemStyle: {
          color: OFFLINE_COLORS[index % OFFLINE_COLORS.length] ?? OFFLINE_COLOR_FALLBACK,
        },
      });
    });
  }
  return {
    tooltip: { trigger: "item" },
    legend: series.length > 1 ? { data: series.map((item) => item.name), top: 0 } : undefined,
    grid: { left: 140, right: 48, top: series.length > 1 ? 48 : 24, bottom: 40 },
    xAxis: { type: "value", name: "相对变化率（相对 design）" },
    yAxis: { type: "category", data: data.bars.map((bar) => bar.label) },
    series,
  };
}
