/**
 * 敏感性龙卷风图组件壳（批2d 三图之三——沿 ProfileChart 薄壳先例：
 * echarts/core 按需注册+init/dispose/setOption 生命周期；数据面归
 * lib/jointCharts tornadoBars/buildTornadoOption 纯函数）。
 *
 * 输入:  combos（jointView 窄化产物——combos 序=score 升序，首位=排名最高）
 *        +sensitivity（批6e：全工况投影报告视图——app 层取数窄化下传，
 *        null=无快照/未跑计算降级）
 * 输出:  方案选择器（默认首位）+水平双向条（批6e 升级=全工况幅度轴：
 *        avg 系列[选定方案联合枚举指标]+检修系列[design_offline_* 快照
 *        投影]）+失守工况标签清单+诚实空态（无 avg/design 成对指标不造假）
 *
 * 规格说明（批2d 简报②+批6e 升级）：
 *   - 三键 avg 对（运行成本/能耗/碳强度——建设投资无 avg 对、六出水指标
 *     无 avg 对不入图）；(avg-design)/design 双向条（正=avg 工况变差）；
 *   - 批6e 全工况幅度：sensitivity 在场且有检修工况→avg 系列后逐
 *     design_offline_<unit> 系列（灰阶循环色+legend）；数据源注记+stale
 *     显式提示（§12 快照绑定——输入变更后旧结果标 stale 禁静默覆盖：
 *     stale=true 呈「结果集已过期」警示文案+design_hash 回显）；
 *   - 失守工况标签清单=failed_conditions 解析后按标签去重（三段式出水
 *     失守+两段式 opex 缺席）；
 *   - 按需注册恰四件（BarChart/GridComponent/TooltipComponent/
 *     CanvasRenderer）；组件壳不测（薄壳先例）；
 *   - 容器 div 常驻（R2 回炉——空态高度塌陷由文案占据；init/dispose 与
 *     挂载同生命周期：容器尺寸就绪才 init，ResizeObserver 驱动空→非空
 *     补 init——旧实现条件渲染容器致首挂载空态后永远无图）；
 *   - 方案选项得分格式与表列统一（formatSolutionValue）；Select value
 *     越界回落 0（combos 缩短后残留索引防御——value 同步显示）；
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
import { comboSummaryText } from "../lib/jointCharts";
import {
  buildTornadoOption,
  sensitivitySeries,
  tornadoBars,
} from "../lib/tornadoCharts";
import type { SensitivityReportView } from "../lib/sensitivityView";
import { formatSolutionValue } from "../lib/solutionsView";

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

/** 图高（px——三键横条+检修系列多系列可视域）。 */
const CHART_HEIGHT = 300;

/** 方案选项（序数=排名——combos 序=score 升序；得分格式与表列统一）。 */
function schemeOptions(combos: readonly JointComboView[]): {
  value: number;
  label: string;
}[] {
  return combos.map((combo, index) => ({
    value: index,
    label: `方案 ${index + 1}${
      combo.score !== null
        ? `（得分 ${formatSolutionValue(combo.score)}）`
        : "（得分缺失）"
    }`,
  }));
}

export function TornadoChart({
  combos,
  sensitivity = null,
  sensitivityIssue = null,
}: {
  combos: readonly JointComboView[];
  /** 批6e：全工况投影报告（null=无快照降级——avg-only 旧观）。 */
  sensitivity?: SensitivityReportView | null;
  /** 批6e 回炉 k1-W2：取数失败面（404 detail 等——服务端 fail-loud 原因透传）。 */
  sensitivityIssue?: string | null;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const applyRef = useRef<() => void>(() => {});
  const [schemeIndex, setSchemeIndex] = useState(0);
  // 越界兜底（N-10）：combos 缩短后残留索引回落 0——value 与显示同同步
  const effectiveIndex = schemeIndex < combos.length ? schemeIndex : 0;
  const combo = combos[effectiveIndex] ?? null;
  const data = useMemo(() => (combo === null ? null : tornadoBars(combo)), [combo]);
  // 检修系列诚实跳过注记（sensitivitySeries 纯函数面——option 内同源）
  const offlineNotes = useMemo(() => {
    if (data === null || sensitivity === null || sensitivity.condition_keys.length === 0) {
      return [] as string[];
    }
    return sensitivitySeries(
      sensitivity,
      data.bars.map((bar) => bar.designKey),
    ).skipped;
  }, [data, sensitivity]);
  const empty = data === null || data.bars.length === 0;
  // 全零差判定（k1-W4 回炉）：有检修工况且逐行 deltas 全零——显式语义说明
  const allOfflineZero =
    sensitivity !== null &&
    sensitivity.condition_keys.length > 0 &&
    sensitivity.rows.length > 0 &&
    sensitivity.rows.every(
      (row) =>
        Object.keys(row.deltas).length === 0 ||
        Object.values(row.deltas).every((delta) => delta === 0),
    );

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }
    let chart: echarts.ECharts | null = null;
    const ensure = () => {
      if (
        chart === null &&
        container.clientWidth > 0 &&
        container.clientHeight > 0
      ) {
        chart = echarts.init(container); // 容器常驻：尺寸就绪才 init（0×0 防御）
        chartRef.current = chart;
        return true;
      }
      return false;
    };
    const observer = new ResizeObserver(() => {
      const created = chart === null; // 本次回调是否可能新建（空→显/高度恢复）
      ensure();
      chart?.resize();
      if (created && chart !== null) {
        // 懒 init 补挂时重放当前 option——echarts canvas 随首次 setOption
        // 创建（挂载隐藏页签时 data effect 已跑过，此处补齐唯一通路）
        applyRef.current();
      }
    });
    observer.observe(container); // 空态→非空/隐藏→显示尺寸恢复均经此驱动
    return () => {
      observer.disconnect();
      chartRef.current = null;
      chart?.dispose();
    };
  }, []);

  useEffect(() => {
    applyRef.current = () => {
      if (data !== null && data.bars.length > 0) {
        chartRef.current?.setOption(buildTornadoOption(data, sensitivity), true);
      }
    };
    applyRef.current();
  }, [data, sensitivity]);

  return (
    <div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Typography.Text type="secondary">选定方案</Typography.Text>
        <Select
          style={{ minWidth: 220 }}
          value={combo === null ? undefined : effectiveIndex}
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
      {empty ? (
        <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>
          无 avg/design 成对指标（建设投资无 avg 对、六出水指标无 avg 对）
          ——不造假数据。
        </Typography.Paragraph>
      ) : (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
          水平双向条=各工况相对 design 工况的指标相对变化率（正=该工况变差、
          负=变好；全低优量）；avg 系列=选定方案联合枚举指标，检修系列
          （design_offline_*）=最近完成计算快照全工况投影；建设投资与六出水
          指标无 avg 对不入图。
          {data !== null && data.skipped.length > 0
            ? `诚实跳过（design=0 或 avg 对缺席）：${data.skipped.join("、")}。`
            : null}
          {offlineNotes.length > 0
            ? `检修系列跳过：${offlineNotes.join("；")}。`
            : null}
        </Typography.Paragraph>
      )}
      {sensitivity === null ? (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 0 }}>
          检修工况幅度面（design_offline_*）=最近完成计算快照——当前项目尚无
          完成结果集（先提交一次全流程计算），呈现降级为 avg 单系列。
          {sensitivityIssue !== null
            ? `取数失败详情：${sensitivityIssue}（结果件损坏/基线工况缺席等异常面——服务端 fail-loud 原因如上，非「尚未计算」）。`
            : null}
        </Typography.Paragraph>
      ) : sensitivity.condition_keys.length === 0 ? (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 0 }}>
          全工况投影无检修工况（计算提交时未勾选受检单元——POST
          /api/calc/run 的 conditions 携带受检单元 id 后重算可激活检修系列）。
        </Typography.Paragraph>
      ) : sensitivity.stale ? (
        <Typography.Paragraph type="warning" style={{ fontSize: 12, marginTop: 0 }}>
          快照已过期（stale——设计已变更未重算，§12 禁静默覆盖）：幅度面仍为
          旧结果集（design_hash={sensitivity.design_hash.slice(0, 12)}…），
          重算后自动更新。
        </Typography.Paragraph>
      ) : allOfflineZero ? (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 0 }}>
          全部检修工况差值为零（k1-W4 回炉注记）：当前单元库未声明检修降级映射
          （condition_mappings 空），各检修工况与 design 同值为预期现状——
          非端点失效；单元侧声明降级映射后幅度自然分化。
        </Typography.Paragraph>
      ) : (
        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 0 }}>
          快照绑定：design_hash={sensitivity.design_hash.slice(0, 12)}…
          （最近完成计算结果集——与上方方案表配置可不同，以快照为准）。
        </Typography.Paragraph>
      )}
      <div ref={containerRef} style={{ width: "100%", height: empty ? 0 : CHART_HEIGHT }} />
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
