/**
 * 联合枚举结果装配组件（批2d——R-B44b-4 兑现：combos 表+三图 Tabs；
 * 沿 TaskPanel/DiagnosisPanel 组件面先例，窄化产物驱动零形状判断）。
 *
 * 输入:  result（jointView narrowJointResult 产物——combos 序=score 升序
 *        首位=排名最高；diagnosis 透传）
 * 输出:  combos 表（排名/参数摘要/四键/综合得分/降权标记）+三图 Tabs
 *        （帕累托前沿图/平行坐标图/敏感性龙卷风图——forceRender 全页签
 *        挂载）或无解诊断面（combos 空=done 合法终态沿枚举同款语义）
 *
 * 规格说明（批2d 简报③ DoD 2~5；R1 回炉——无解诊断投影）：
 *   - combos 空 → 无解诊断投影面（projectJointDiagnosis 真形投影：
 *     stage_empty=stage 层展开给 DiagnosisPanel+kind 标签；final_
 *     infeasible=冲突面缺失呈现+note 显著文案；未知 kind=JSON 摘要
 *     fail-visible 不吞）；无方案不进三图面；
 *   - 表列：排名（combos 序=score 升序——首位=排名最高[全目标最小化优，
 *     score 越小越好]）；四键列头=metricLabel 中文+formatSolutionValue
 *     千分位；score null=「（缺失）」诚实呈现；降权=「敏感工况失守」；
 *   - 三图：帕累托前沿图（前沿集挂载方算一次——换轴不重算）/平行坐标图
 *     （分档+虚线）/龙卷风（方案选择器默认首位）；
 *   - Tabs forceRender（SSR 全页签渲染+页签切换零重挂）。
 */
import { Card, Table, Tabs, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";

import type { JointComboView, JointResultView } from "../lib/jointView";
import { TRUE_METRIC_KEYS, metricLabel, projectJointDiagnosis } from "../lib/jointView";
import { comboSummaryText, paretoFront } from "../lib/jointCharts";
import { formatSolutionValue } from "../lib/solutionsView";
import { DiagnosisPanel } from "./DiagnosisPanel";
import { ParetoChart } from "./ParetoChart";
import { ParallelCoordsChart } from "./ParallelCoordsChart";
import { TornadoChart } from "./TornadoChart";

/** 表行模型（combo 随行——渲染函数消费）。 */
type ComboRow = { key: number; rank: number; combo: JointComboView };

/** score 显示（null=缺失诚实呈现——不造假 0）。 */
function scoreText(score: number | null): string {
  return score === null ? "（缺失）" : formatSolutionValue(score);
}

export function JointSolutionsPanel({ result }: { result: JointResultView }) {
  if (result.combos.length === 0) {
    const diag = projectJointDiagnosis(result.diagnosis);
    return (
      <Card size="small" title="联合枚举（方案比选）" style={{ marginTop: 12 }}>
        <Typography.Paragraph type="warning" style={{ fontSize: 12, marginBottom: 8 }}>
          无可行组合——{diag.kindLabel}
          （分段无解=某单元组合层先空；终判不可行=末段全组合不可行）。
        </Typography.Paragraph>
        {diag.note !== null ? (
          <Typography.Paragraph type="danger" strong>
            终判不可行：{diag.note}
          </Typography.Paragraph>
        ) : null}
        {diag.rawSummary !== null ? (
          <Typography.Paragraph type="warning" style={{ wordBreak: "break-all" }}>
            诊断载荷原样：{diag.rawSummary}
          </Typography.Paragraph>
        ) : null}
        <DiagnosisPanel diagnosis={diag.panelPayload} />
      </Card>
    );
  }
  const rows: ComboRow[] = result.combos.map((combo, index) => ({
    key: index,
    rank: index + 1,
    combo,
  }));
  const columns: ColumnsType<ComboRow> = [
    { title: "排名", dataIndex: "rank", key: "rank", width: 64 },
    {
      title: "方案参数",
      key: "params",
      render: (_: unknown, row: ComboRow) => comboSummaryText(row.combo),
    },
    ...TRUE_METRIC_KEYS.map((key) => ({
      title: metricLabel(key),
      key,
      render: (_: unknown, row: ComboRow) =>
        row.combo.metrics[key] === undefined
          ? "（缺失）"
          : formatSolutionValue(row.combo.metrics[key]!),
    })),
    {
      title: metricLabel("score"),
      key: "score",
      render: (_: unknown, row: ComboRow) => scoreText(row.combo.score),
    },
    {
      title: "敏感性",
      key: "degraded",
      render: (_: unknown, row: ComboRow) =>
        row.combo.sensitivity_degraded ? (
          <Tag color="warning">敏感工况失守</Tag>
        ) : (
          "—"
        ),
    },
  ];
  return (
    <Card size="small" title="联合枚举（方案比选）" style={{ marginTop: 12 }}>
      <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 8 }}>
        共 {result.combos.length} 个可行组合（排名=综合得分升序——全目标最小化
        优，首位=排名最高）；「敏感工况失守」=sensitivity 失守降权标记（仍可行）。
      </Typography.Paragraph>
      <Table<ComboRow>
        size="small"
        columns={columns}
        dataSource={rows}
        pagination={false}
        scroll={{ x: true }}
      />
      <Tabs
        style={{ marginTop: 12 }}
        items={[
          {
            key: "pareto",
            label: "帕累托前沿图",
            forceRender: true,
            children: <ParetoChart combos={result.combos} front={paretoFront(result.combos)} />,
          },
          {
            key: "parallel",
            label: "平行坐标图",
            forceRender: true,
            children: <ParallelCoordsChart combos={result.combos} />,
          },
          {
            key: "tornado",
            label: "敏感性龙卷风图",
            forceRender: true,
            children: <TornadoChart combos={result.combos} />,
          },
        ]}
      />
    </Card>
  );
}
