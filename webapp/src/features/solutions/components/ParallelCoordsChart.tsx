/**
 * 平行坐标图组件壳（批2d 三图之二——沿 ProfileChart 薄壳先例：echarts/core
 * 按需注册+init/dispose/setOption 生命周期；数据面归 lib/jointCharts
 * parallelAxesData/buildParallelOption 纯函数，组件零形状判断）。
 *
 * 输入:  combos（jointView 窄化产物——四真键+score 五轴数据源）
 * 输出:  五轴平行坐标图（线色=score 三分位分档优/中/差+失守方案虚线）
 *        +全轴反向开关（全目标低优——反向后上端=优全局一致）+注记文案
 *
 * 规格说明（批2d 简报③ DoD 4）：
 *   - 按需注册恰五件（ParallelChart/ParallelComponent/TooltipComponent/
 *     LegendComponent/CanvasRenderer）；
 *   - 轴反向开关默认开（能耗成本类低优——低值端对齐）；开关只影响显示
 *     不影响数据面（parallelAxesData 与 invert 解耦）；
 *   - 入线资格（四真键+score 全 finite）门外组合不入图；全组合门外=
 *     空态文案（无可绘方案——不造假轴；容器常驻高度塌陷，R3 回炉）；
 *   - 组件壳不测（薄壳先例——投影层纯函数承载全部契约）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Switch, Typography } from "antd";
import * as echarts from "echarts/core";
import { ParallelChart } from "echarts/charts";
import {
  LegendComponent,
  ParallelComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import type { JointComboView } from "../lib/jointView";
import {
  buildParallelOption,
  parallelAxesData,
} from "../lib/jointCharts";

echarts.use([
  ParallelChart,
  ParallelComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

/** 图高（px——五轴横排+图例）。 */
const CHART_HEIGHT = 380;

export function ParallelCoordsChart({
  combos,
}: {
  combos: readonly JointComboView[];
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const [invert, setInvert] = useState(true);
  const axesData = useMemo(() => parallelAxesData(combos), [combos]);
  const empty = axesData.axes.length === 0;

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
    if (axesData.axes.length === 0) {
      return; // 空数据面不 setOption（容器常驻——空态文案承载）
    }
    chartRef.current?.setOption(buildParallelOption(axesData, invert));
  }, [axesData, invert]);

  return (
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Typography.Text type="secondary">全轴反向（低优量反向——上端为优）</Typography.Text>
        <Switch
          checked={invert}
          checkedChildren="反向"
          unCheckedChildren="正向"
          onChange={(checked) => {
            setInvert(checked);
          }}
        />
      </div>
      {empty ? (
        <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>
          无可绘方案（指标/得分不全场）——入线需四项指标与综合得分全在场，
          缺项组合诚实排除不造假轴。
        </Typography.Paragraph>
      ) : (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
          五轴=运行成本/能耗/碳强度/建设投资/综合得分（全低优）；线色=综合得分
          三分位分档（优/中/差档）；虚线=敏感工况失守方案（sensitivity_degraded）；
          指标或综合得分不全场（sparse）的方案不入图（五轴需全值）。
        </Typography.Paragraph>
      )}
      <div ref={containerRef} style={{ width: "100%", height: empty ? 0 : CHART_HEIGHT }} />
    </div>
  );
}
