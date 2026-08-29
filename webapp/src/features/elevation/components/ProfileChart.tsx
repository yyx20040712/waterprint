/**
 * 高程纵断图组件壳：echarts/core 按需注册+init/dispose/setOption 生命周期
 * （FE7 D6 echarts 首消费——禁 echarts-for-react，手写薄壳 FE1 渲染器先例）。
 *
 * 输入:  ElevationView（lib/profileChart 窄化产物——组件零形状判断零推导）
 * 输出:  四线纵断图（echarts Canvas）+基准面/损失口径注记文案区
 *
 * 规格说明（FE7 批 6b 段五，D2/D3/D6）：
 *   - D6 按需注册：echarts/core+LineChart/GridComponent/TooltipComponent/
 *     LegendComponent/CanvasRenderer 恰五件（本图消费面——多一件即冗余
 *     体积）；React.lazy 动态导入（elevationPane 侧）→vite 自动切独立
 *     异步 chunk，不触 vite.config manualChunks 冻结面（FE2 P4 纪律）；
 *   - 生命周期薄壳：useEffect init（挂载）→setOption（view 变更——工况
 *     切换/重取数）→dispose（卸载）；容器尺寸监听=ResizeObserver（含
 *     Tabs 保活显示/隐藏与窗口缩放两场景）；
 *   - D2 注记=datum_note 服务面下发（口径单一真源——前端不硬编码）；
 *     D3 损失口径注记「沿程损失未接线——loss_in 恒 0」如实呈现；
 *   - 组件壳不测（薄壳先例——投影层 profileChart 纯函数承载全部契约）。
 */
import { useEffect, useRef } from "react";
import { Typography } from "antd";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import { buildChartOption, type ElevationView } from "../lib/profileChart";

// D6 按需注册（模块级一次——五件恰合本图消费面）
echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

/** 图高（px——四线+图例+轴标注的固定可视面）。 */
const CHART_HEIGHT = 420;

/** D3 损失口径注记（沿程损失未接线——恒 0 如实呈现）。 */
const LOSS_NOTE = "沿程损失未接线（管线几何归 M5）——loss_in 现值恒 0";

export function ProfileChart({ view }: { view: ElevationView }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }
    const chart = echarts.init(container);
    chartRef.current = chart;
    // 容器尺寸监听（Tabs 保活显示/隐藏+窗口缩放两场景——resize 事件
    // 不覆盖 display:none→block 的容器尺寸变化，ResizeObserver 才覆盖）
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
    chartRef.current?.setOption(buildChartOption(view));
  }, [view]);

  return (
    <div>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
        {view.datum_note}；{LOSS_NOTE}。
      </Typography.Paragraph>
      <div ref={containerRef} style={{ width: "100%", height: CHART_HEIGHT }} />
    </div>
  );
}
