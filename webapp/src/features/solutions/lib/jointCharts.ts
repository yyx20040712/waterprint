/**
 * 方案比选三图纯函数（批2d——帕累托前沿/平行坐标/敏感性龙卷风；沿
 * profileChart 投影层承载全部契约先例：计算与 option 构建纯函数 node
 * 直测，组件薄壳只做 init/setOption 生命周期）。
 *
 * 输入:  JointComboView[]（jointView 窄化产物——本件零形状判断）+轴键
 *        选择/前沿集/反向开关
 * 输出:  paretoFront（四键非支配排序——全 minimize）+buildParetoOption
 *        （双系列投影 option）/parallelAxesData（五轴+分档线数据）+
 *        buildParallelOption（三档系列+降权虚线）/tornadoBars（三键 avg
 *        对变化率+失守工况标签解析去重）+buildTornadoOption（水平双向
 *        条）/comboSummaryText+paretoTooltipLines（纯文本面）
 *
 * 规格说明（批2d 简报③ DoD 3~5——数据自足裁定）：
 *   - 帕累托：combos（feasible 子集）四真键非支配排序；支配=全维 ≤ 且
 *     至少一维 <（相等向量互不支配=同前沿）；前沿是四维性质——换轴投影
 *     不重算（投影只影响显示，轴键只进 buildParetoOption 显示面）；
 *     feasible=false 或四真键缺席的组合不参与排序（sparse/不可行防御）；
 *   - 平行坐标：四真键+score 五轴；入线资格=四真键+score 全 finite
 *     （Number.isFinite 门，与 frontEligible 口径统一——无 score 兜底
 *     不造假值）；轴域只按入线组合取值；全组合资格门外→空 axes/lines
 *     （组件空态文案）；线色=score 三分位分档（优/中/差——score 升序
 *     位次）；失守方案（sensitivity_degraded）虚线区分；轴反向开关作用
 *     全轴（全目标低优——反向后「上端=优」全局一致）；
 *   - 龙卷风：三键 avg 对（cost_opex/energy/carbon——capex 无 avg 对）的
 *     avg vs design 相对变化率 (avg-design)/design（水平双向条）；design=0
 *     或 avg 对缺席=诚实跳过（skipped 记键不造假）；六出水指标无 avg 对
 *     不入图；failed_conditions 解析去重（三段式出水失守+两段式
 *     opex_absent）；sensitivity 检修工况数值幅度=挂账端点后升（空态文案
 *     归组件面）；
 *   - 零运行期库 import（node 测试零增重——jointView 同款纪律）。
 */
import type { JointComboView } from "./jointView";
import { AVG_METRIC_KEYS, TRUE_METRIC_KEYS, metricLabel } from "./jointView";

/** 帕累托轴键（四真键——投影显示面可换轴）。 */
export type ParetoAxisKey = (typeof TRUE_METRIC_KEYS)[number];

/** 散点数据项（value=[x,y] 投影值；combo 随行——tooltip 纯函数消费）。 */
type ParetoPoint = { value: [number, number]; combo: JointComboView };

/** 帕累托 option（双系列 scatter 纯对象——组件薄壳唯一数据源）。 */
export type ParetoChartOption = {
  tooltip: Record<string, unknown>;
  legend: { data: string[]; top: number };
  grid: { left: number; right: number; top: number; bottom: number };
  xAxis: { type: "value"; scale: boolean; name: string };
  yAxis: { type: "value"; scale: boolean; name: string };
  series: {
    name: string;
    type: "scatter";
    data: ParetoPoint[];
    symbolSize: number;
    itemStyle: { color: string };
  }[];
};

/** 平行坐标分档（score 升序三分位——低=优）。 */
export type ParallelBand = "best" | "mid" | "worst";

/** 平行坐标轴（四真键+score 五轴）。 */
export type ParallelAxis = { key: string; label: string; min: number; max: number };

/** 平行坐标线（值序随轴序）。 */
export type ParallelLine = {
  comboIndex: number;
  values: number[];
  degraded: boolean;
  band: ParallelBand;
};

/** 平行坐标数据面（axes+lines——buildParallelOption 消费）。 */
export type ParallelAxesData = { axes: ParallelAxis[]; lines: ParallelLine[] };

/** 平行坐标 option（三档系列——降权虚线行内标注）。 */
export type ParallelChartOption = {
  tooltip: Record<string, unknown>;
  legend: { data: string[]; bottom: number };
  parallelAxis: { dim: number; name: string; inverse: boolean; min: number; max: number }[];
  series: {
    name: string;
    type: "parallel";
    data: { value: number[]; lineStyle?: { type: "dashed" } }[];
    lineStyle: { width: number; color: string };
    smooth: false;
  }[];
};

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

/** 龙卷风 option（水平双向条——正负值自然双向）。 */
export type TornadoChartOption = {
  tooltip: Record<string, unknown>;
  grid: { left: number; right: number; top: number; bottom: number };
  xAxis: { type: "value"; name: string };
  yAxis: { type: "category"; data: string[] };
  series: { name: string; type: "bar"; data: number[]; itemStyle: { color: string } }[];
};

/** 前沿/被支配双色（前沿高亮蓝/被支配灰阶）。 */
const PARETO_FRONT_COLOR = "#2f54eb";
const PARETO_DOMINATED_COLOR = "#bfbfbf";

/** 三档色（优绿/中蓝/差灰——低优量低位=好）。 */
const BAND_COLORS: Record<ParallelBand, string> = {
  best: "#389e0d",
  mid: "#1677ff",
  worst: "#8c8c8c",
};

/** 龙卷风条色（中性蓝——正=变差/负=变好双向同色，方向由条向呈现）。 */
const TORNADO_COLOR = "#1677ff";

/** combo 排序资格：feasible 且四真键齐（sparse/不可行防御——不参与支配判定）。 */
function frontEligible(combo: JointComboView): boolean {
  return (
    combo.feasible &&
    TRUE_METRIC_KEYS.every((key) => Number.isFinite(combo.metrics[key]))
  );
}

/**
 * 四键非支配排序（全 minimize）：a 支配 b ⟺ ∀k a≤b 且 ∃k a<b（相等向量
 * 互不支配=同前沿）。返回非支配索引集（combos 输入序——投影无关）。
 */
export function paretoFront(combos: readonly JointComboView[]): Set<number> {
  const eligible = combos
    .map((combo, index) => ({ combo, index }))
    .filter((item) => frontEligible(item.combo));
  const front = new Set<number>();
  for (const { combo: candidate, index } of eligible) {
    const dominated = eligible.some(({ combo: other }) =>
      TRUE_METRIC_KEYS.every((key) => other.metrics[key]! <= candidate.metrics[key]!) &&
      TRUE_METRIC_KEYS.some((key) => other.metrics[key]! < candidate.metrics[key]!),
    );
    if (!dominated) {
      front.add(index);
    }
  }
  return front;
}

/** 参数摘要文本（「单元: k=v, k=v」多单元分号接——tooltip/表行消费）。 */
export function comboSummaryText(combo: JointComboView): string {
  return Object.entries(combo.params)
    .map(([unitId, row]) => {
      const pairs = Object.entries(row).map(([k, v]) => `${k}=${v}`);
      return `${unitId}: ${pairs.join(", ")}`;
    })
    .join("；");
}

/** 帕累托悬停行（四键值+score+参数摘要——键缺席/score null=缺失不造假）。 */
export function paretoTooltipLines(combo: JointComboView): string[] {
  const lines = TRUE_METRIC_KEYS.map(
    (key) => `${metricLabel(key)}：${combo.metrics[key] ?? "（缺失）"}`,
  );
  lines.push(`${metricLabel("score")}：${combo.score ?? "（缺失）"}`);
  lines.push(`参数：${comboSummaryText(combo)}`);
  return lines;
}

/**
 * 帕累托投影 option（前沿/被支配双系列）：front=paretoFront 产物（四维
 * 性质——换轴不重算）；缺选中轴键的组合不入系列（无值点不画）；非资格
 * 组合（frontEligible 失败=feasible=false/四真键缺席）不参与排序呈现
 * ——不入前沿也不入被支配系列不画（生产 beam 只发 feasible+全键，此为
 * 防御面口径统一）。
 */
export function buildParetoOption(
  combos: readonly JointComboView[],
  xKey: ParetoAxisKey,
  yKey: ParetoAxisKey,
  front: ReadonlySet<number>,
): ParetoChartOption {
  const pointOf = (combo: JointComboView): ParetoPoint | null => {
    const x = combo.metrics[xKey];
    const y = combo.metrics[yKey];
    return x === undefined || y === undefined
      ? null
      : { value: [x, y], combo };
  };
  const frontPoints: ParetoPoint[] = [];
  const dominatedPoints: ParetoPoint[] = [];
  combos.forEach((combo, index) => {
    if (!frontEligible(combo)) {
      return; // 非资格组合不画（与 paretoFront 排序门同口径）
    }
    const point = pointOf(combo);
    if (point === null) {
      return;
    }
    (front.has(index) ? frontPoints : dominatedPoints).push(point);
  });
  return {
    tooltip: {
      trigger: "item",
      formatter: (params: { data: ParetoPoint }) =>
        paretoTooltipLines(params.data.combo).join("<br/>"),
    },
    legend: { data: ["前沿方案", "被支配方案"], top: 0 },
    grid: { left: 64, right: 32, top: 40, bottom: 48 },
    xAxis: { type: "value", scale: true, name: metricLabel(xKey) },
    yAxis: { type: "value", scale: true, name: metricLabel(yKey) },
    series: [
      {
        name: "前沿方案",
        type: "scatter",
        data: frontPoints,
        symbolSize: 12,
        itemStyle: { color: PARETO_FRONT_COLOR },
      },
      {
        name: "被支配方案",
        type: "scatter",
        data: dominatedPoints,
        symbolSize: 7,
        itemStyle: { color: PARETO_DOMINATED_COLOR },
      },
    ],
  };
}

/** score 三分位分档（升序位次 i、总数 n——n<3 时退化 best/worst 两档）。 */
function bandOf(rank: number, total: number): ParallelBand {
  if (rank <= (total - 1) / 3) {
    return "best";
  }
  if (rank >= (2 * (total - 1)) / 3) {
    return "worst";
  }
  return "mid";
}

/**
 * 平行坐标数据面：五轴（四真键+score）——入线资格=四真键+score 全 finite
 * （Number.isFinite 门，与 frontEligible 口径统一；无 score 兜底——缺项
 * 组合诚实排除不造假值）；轴域只按入线组合取值（min/max 数据域，单值轴
 * 邻域扩展 min<max）；全组合资格门外→空 axes/lines（组件空态文案承载）；
 * band=score 升序三分位；degraded 透传（虚线归 option 面）。
 */
export function parallelAxesData(
  combos: readonly JointComboView[],
): ParallelAxesData {
  const axisKeys: readonly string[] = [...TRUE_METRIC_KEYS, "score"];
  const plotted = combos
    .map((combo, index) => ({ combo, index }))
    .filter(
      (item) =>
        TRUE_METRIC_KEYS.every((key) =>
          Number.isFinite(item.combo.metrics[key]),
        ) && Number.isFinite(item.combo.score),
    );
  if (plotted.length === 0) {
    return { axes: [], lines: [] };
  }
  const valueOf = (combo: JointComboView, key: string): number =>
    key === "score" ? combo.score! : combo.metrics[key]!;
  const axes: ParallelAxis[] = axisKeys.map((key) => {
    const values = plotted.map((item) => valueOf(item.combo, key));
    const min = Math.min(...values);
    const max = Math.max(...values);
    if (min === max) {
      const width = min === 0 ? 1 : Math.abs(min) * 0.5;
      return { key, label: metricLabel(key), min: min - width, max: max + width };
    }
    return { key, label: metricLabel(key), min, max };
  });
  const ranked = [...plotted].sort(
    (a, b) => (a.combo.score ?? 0) - (b.combo.score ?? 0),
  );
  const rankOf = new Map<number, number>();
  ranked.forEach((item, rank) => rankOf.set(item.index, rank));
  const lines: ParallelLine[] = plotted.map(({ combo, index }) => ({
    comboIndex: index,
    values: axisKeys.map((key) => valueOf(combo, key)),
    degraded: combo.sensitivity_degraded,
    band: bandOf(rankOf.get(index)!, plotted.length),
  }));
  return { axes, lines };
}

/** 平行坐标 option：三档系列（优/中/差档）+降权虚线；反向开关作用全轴。 */
export function buildParallelOption(
  data: ParallelAxesData,
  invert: boolean,
): ParallelChartOption {
  const bands: ParallelBand[] = ["best", "mid", "worst"];
  const bandNames: Record<ParallelBand, string> = {
    best: "优档",
    mid: "中档",
    worst: "差档",
  };
  return {
    tooltip: { trigger: "item" },
    legend: { data: bands.map((band) => bandNames[band]), bottom: 0 },
    parallelAxis: data.axes.map((axis, dim) => ({
      dim,
      name: axis.label,
      inverse: invert,
      min: axis.min,
      max: axis.max,
    })),
    series: bands.map((band) => ({
      name: bandNames[band],
      type: "parallel" as const,
      data: data.lines
        .filter((line) => line.band === band)
        .map((line) => ({
          value: line.values,
          ...(line.degraded ? { lineStyle: { type: "dashed" as const } } : {}),
        })),
      lineStyle: { width: 1.5, color: BAND_COLORS[band] },
      smooth: false as const,
    })),
  };
}

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

/** 龙卷风 option：水平双向条（类目=指标标签+值=相对变化率）。 */
export function buildTornadoOption(data: TornadoData): TornadoChartOption {
  return {
    tooltip: { trigger: "item" },
    grid: { left: 140, right: 48, top: 24, bottom: 40 },
    xAxis: { type: "value", name: "相对变化率（avg 相对 design）" },
    yAxis: { type: "category", data: data.bars.map((bar) => bar.label) },
    series: [
      {
        name: "avg 相对 design 变化率",
        type: "bar",
        data: data.bars.map((bar) => bar.ratio),
        itemStyle: { color: TORNADO_COLOR },
      },
    ],
  };
}
