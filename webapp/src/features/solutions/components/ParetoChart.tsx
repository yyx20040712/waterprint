/**
 * 帕累托前沿图组件壳（批2d 三图之一——沿 ProfileChart 薄壳先例：echarts/core
 * 按需注册+init/dispose/setOption 生命周期，禁 echarts-for-react；计算与
 * option 构建归 lib/jointCharts 纯函数，组件零形状判断零推导）。
 *
 * 输入:  combos（jointView 窄化产物）+front（paretoFront 前沿集——四维
 *        性质与投影无关，挂载方算一次）
 * 输出:  双轴投影散点图（前沿高亮+被支配灰阶）+轴选择器（四键可换轴，
 *        默认 运行成本×建设投资）+四维注记文案
 *
 * 规格说明（批2d 简报③ DoD 3）：
 *   - 按需注册恰五件（ScatterChart/GridComponent/TooltipComponent/
 *     LegendComponent/CanvasRenderer）；
 *   - 轴选择器换轴只换显示投影——前沿不重算（四维性质注记在案）；
 *   - 悬停 tooltip=四键值+score+参数摘要（paretoTooltipLines 纯函数）；
 *   - 组件壳不测（薄壳先例——投影层 jointCharts 纯函数承载全部契约）；
 *   - Select 不用占位文案属性（FE3 C3 grep 门禁规避沿册）。
 */
import { useEffect, useRef, useState } from "react";
import { Select, Typography } from "antd";
import * as echarts from "echarts/core";
import { ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import type { JointComboView } from "../lib/jointView";
import { TRUE_METRIC_KEYS, metricLabel } from "../lib/jointView";
import {
  buildParetoOption,
  type ParetoAxisKey,
} from "../lib/jointCharts";

echarts.use([
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

/** 图高（px）。 */
const CHART_HEIGHT = 420;

/** 轴选项（四键可换轴——label=metricLabel 中文）。 */
const AXIS_OPTIONS: { value: ParetoAxisKey; label: string }[] =
  TRUE_METRIC_KEYS.map((key) => ({ value: key, label: metricLabel(key) }));

export function ParetoChart({
  combos,
  front,
}: {
  combos: readonly JointComboView[];
  front: ReadonlySet<number>;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const [xKey, setXKey] = useState<ParetoAxisKey>("cost_opex_yuan_a");
  const [yKey, setYKey] = useState<ParetoAxisKey>("cost_capex_yuan");

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }
    const chart = echarts.init(container);
    chartRef.current = chart;
    const observer = new ResizeObserver(() => {
      chart.resize();
    });
    observer.observe(container);
    return () => {
      observer.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.setOption(buildParetoOption(combos, xKey, yKey, front));
  }, [combos, xKey, yKey, front]);

  return (
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Typography.Text type="secondary">横轴</Typography.Text>
        <Select
          style={{ minWidth: 200 }}
          value={xKey}
          options={AXIS_OPTIONS}
          onChange={(value) => {
            setXKey(value);
          }}
        />
        <Typography.Text type="secondary">纵轴</Typography.Text>
        <Select
          style={{ minWidth: 200 }}
          value={yKey}
          options={AXIS_OPTIONS}
          onChange={(value) => {
            setYKey(value);
          }}
        />
      </div>
      <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
        前沿为四键非支配集（全最小化优）——换轴投影不重算前沿（投影只影响
        显示）；悬停查看四键值、综合得分与参数摘要。
      </Typography.Paragraph>
      <div ref={containerRef} style={{ width: "100%", height: CHART_HEIGHT }} />
    </div>
  );
}
