/**
 * 敏感性龙卷风图组件壳（批2d 三图之三——沿 ProfileChart 薄壳先例：
 * echarts/core 按需注册+init/dispose/setOption 生命周期；数据面归
 * lib/jointCharts tornadoBars/buildTornadoOption 纯函数）。
 *
 * 输入:  combos（jointView 窄化产物——combos 序=score 升序，首位=排名最高）
 * 输出:  方案选择器（默认首位）+水平双向条（avg vs design 相对变化率）
 *        +失守工况标签清单+诚实空态（无 avg/design 成对指标不造假）
 *
 * 规格说明（批2d 简报② 龙卷风第一版语义——数据自足裁定）：
 *   - 三键 avg 对（运行成本/能耗/碳强度——建设投资无 avg 对、六出水指标
 *     无 avg 对不入图）；(avg-design)/design 双向条（正=avg 工况变差）；
 *   - 失守工况标签清单=failed_conditions 解析去重（三段式出水失守+两段式
 *     opex 缺席）；sensitivity 检修工况（design_offline_*）的数值幅度=
 *     挂账端点后升（空态文案如实呈现）；
 *   - 按需注册恰五件（BarChart/GridComponent/TooltipComponent/
 *     CanvasRenderer+本图消费面）；组件壳不测（薄壳先例）；
 *   - Select 不用占位文案属性（FE3 C3 grep 门禁规避沿册）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Card, Select, Typography } from "antd";
import * as echarts from "echarts/core";
import { BarChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import type { JointComboView } from "../lib/jointView";
import {
  buildTornadoOption,
  comboSummaryText,
  tornadoBars,
} from "../lib/jointCharts";

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

/** 图高（px——三键横条）。 */
const CHART_HEIGHT = 260;

/** 方案选项（序数=排名——combos 序=score 升序）。 */
function schemeOptions(combos: readonly JointComboView[]): {
  value: number;
  label: string;
}[] {
  return combos.map((combo, index) => ({
    value: index,
    label: `方案 ${index + 1}${combo.score !== null ? `（得分 ${combo.score}）` : "（得分缺失）"}`,
  }));
}

export function TornadoChart({
  combos,
}: {
  combos: readonly JointComboView[];
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const [schemeIndex, setSchemeIndex] = useState(0);
  const combo = combos[schemeIndex] ?? combos[0] ?? null;
  const data = useMemo(() => (combo === null ? null : tornadoBars(combo)), [combo]);

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
    if (data !== null) {
      chartRef.current?.setOption(buildTornadoOption(data), true);
    }
  }, [data]);

  return (
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Typography.Text type="secondary">选定方案</Typography.Text>
        <Select
          style={{ minWidth: 220 }}
          value={combo === null ? undefined : schemeIndex}
          options={schemeOptions(combos)}
          onChange={(value) => {
            setSchemeIndex(value);
          }}
        />
        {combo !== null ? (
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {comboSummaryText(combo)}
          </Typography.Text>
        ) : null}
      </div>
      {data === null || data.bars.length === 0 ? (
        <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>
          无 avg/design 成对指标（建设投资无 avg 对、六出水指标无 avg 对）
          ——不造假数据；sensitivity 检修工况（design_offline_*）的数值幅度
          属挂账端点，接入后在此呈现。
        </Typography.Paragraph>
      ) : (
        <>
          <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
            水平双向条=avg 工况相对 design 工况的指标相对变化率（正=avg 工况
            变差、负=变好；全低优量）；建设投资与六出水指标无 avg 对不入图。
            {data.skipped.length > 0
              ? `诚实跳过（design=0 或 avg 对缺席）：${data.skipped.join("、")}。`
              : null}
          </Typography.Paragraph>
          <div ref={containerRef} style={{ width: "100%", height: CHART_HEIGHT }} />
        </>
      )}
      {data !== null && data.failedLabels.length > 0 ? (
        <Card size="small" title="失守工况（failed_conditions 去重）" style={{ marginTop: 8 }}>
          {data.failedLabels.map((label) => (
            <div key={label}>{label}</div>
          ))}
        </Card>
      ) : null}
    </div>
  );
}
