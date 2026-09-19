/**
 * 操作链观测面主体视图：任务时间线+三源聚合卡（诊断摘要/警告计数/trace 统计）。
 *
 * 输入:  OpsChainReport 窄化产物（useOpsChainQuery select 通道）
 * 输出:  纯展示组件（无取数无路由——opsDebugPane 装配壳消费）
 *
 * 规格说明（B4-1《裁决书》方案五①；TrustReportView 展示先例同构）：
 *   - 时间线卡：注册序任务表（操作序=时间轴——server 档案无时钟字段，
 *     finished_at 为 server 内存值：进程重启后恢复记录=恢复时刻新租约，
 *     时刻列悬浮注记）；状态 Tag 语义色+错误诊断列（error_type/error_code）；
 *   - 聚合块降级：latest_calc=null（无 done calc/结果文件不可读）=蓝条
 *     降级呈现（对照时间线自明——面板不猜因）；stale 黄条同 trust；
 *   - 诊断摘要卡：计数+极值（明细走「可信度」标签——trust 端点全量）；
 *   - trace 卡：总量+按工况/按单元/按公式三桶计数表（字典序=server 确定性）。
 */
import { Alert, Card, Descriptions, Empty, Table, Tag, Typography } from "antd";

import {
  formatProgress,
  formatSci,
  formatUnix,
  kindLabel,
  stateTone,
  type OpsChainReport,
} from "../lib/opsChainView";

function StatusStrip({ report }: { report: OpsChainReport }) {
  const latest = report.latest_calc;
  return (
    <div data-testid="wp-ops-status">
      {latest?.stale && (
        <Alert
          type="warning"
          showIcon
          title="最近结果已过期：计算后设计有变更——建议重新提交计算。"
          style={{ marginBottom: 12 }}
        />
      )}
      {latest === null && (
        <Alert
          type="info"
          showIcon
          data-testid="wp-ops-degraded"
          title="暂无深度聚合块：项目尚无完成态计算（或结果文件已不可读）——时间线仍完整呈现任务历史。"
          style={{ marginBottom: 12 }}
        />
      )}
      {latest !== null && !latest.diagnostics.diagnostics_available && (
        <Alert
          type="info"
          showIcon
          title="本结果无诊断数据（旧版本计算）：重新提交计算后可获取收敛/闭合/裕度诊断。"
          style={{ marginBottom: 12 }}
        />
      )}
    </div>
  );
}

function TimelineCard({ report }: { report: OpsChainReport }) {
  return (
    <Card title="任务时间线（注册序=操作序）" size="small" style={{ marginBottom: 12 }}>
      {report.tasks.length === 0 ? (
        <Empty description="本项目尚无任务记录（提交计算/枚举/导出后在此呈现操作链）" />
      ) : (
        <Table
          size="small"
          rowKey="task_id"
          pagination={false}
          dataSource={[...report.tasks]}
          columns={[
            { title: "任务号", dataIndex: "task_id", ellipsis: true, width: 220 },
            {
              title: "类型",
              dataIndex: "kind",
              width: 96,
              render: (kind: string) => kindLabel(kind),
            },
            {
              title: "状态",
              dataIndex: "state",
              width: 96,
              render: (state: string) => <Tag color={stateTone(state)}>{state}</Tag>,
            },
            {
              title: "进度",
              dataIndex: "progress",
              width: 80,
              render: (progress: number) => formatProgress(progress),
            },
            { title: "阶段", dataIndex: "stage", ellipsis: true, width: 160 },
            {
              title: "完成时刻",
              dataIndex: "finished_at_unix",
              width: 170,
              render: (value: number | null) => (
                <span
                  title={
                    value === null
                      ? "未终态或未落点"
                      : "server 内存值（进程重启后恢复记录=恢复时刻，非原始完成时刻）"
                  }
                >
                  {formatUnix(value)}
                </span>
              ),
            },
            {
              title: "错误诊断",
              dataIndex: "error",
              render: (_: string | null, row) =>
                row.error_type ? (
                  <Typography.Text type="danger" style={{ fontSize: 12 }}>
                    {row.error_type}
                    {row.error_code !== null ? `（HTTP ${row.error_code}）` : ""}:{" "}
                    {row.error ?? ""}
                  </Typography.Text>
                ) : row.stale ? (
                  <Tag color="orange">结果过期</Tag>
                ) : (
                  "—"
                ),
            },
          ]}
        />
      )}
    </Card>
  );
}

function LatestBlockCards({ report }: { report: OpsChainReport }) {
  const latest = report.latest_calc;
  if (latest === null) return null;
  const diag = latest.diagnostics;
  const warnEntries = Object.entries(latest.warning_counts);
  const traceRows = Object.entries(latest.trace.by_unit).map(
    ([unitId, count]) => ({ key: unitId, unitId, count }),
  );
  return (
    <>
      <Card title="最近计算三源聚合" size="small" style={{ marginBottom: 12 }}>
        <Descriptions size="small" column={2}>
          <Descriptions.Item label="任务号">{latest.task_id}</Descriptions.Item>
          <Descriptions.Item label="溯源">
            <Typography.Text style={{ fontSize: 12 }}>
              design {latest.design_hash.slice(0, 12)} · engine{" "}
              {latest.engine_version} · data {latest.data_version}
            </Typography.Text>
          </Descriptions.Item>
          <Descriptions.Item label="诊断摘要">
            {diag.diagnostics_available
              ? `收敛 ${diag.convergence_lines} 组（最多 ${diag.max_iterations} 步·最差残差 ${formatSci(
                  diag.worst_final_residual,
                )}）·闭合 ${diag.mass_balance_lines} 工况·裕度 ${diag.effluent_lines} 条`
              : "无诊断数据（降级呈现——明细见「可信度」标签）"}
          </Descriptions.Item>
          <Descriptions.Item label="警告计数">
            {warnEntries.length === 0
              ? "零警告"
              : warnEntries
                  .map(([level, count]) => `${level}×${count}`)
                  .join(" · ")}
          </Descriptions.Item>
          <Descriptions.Item label="trace 公式应用总量">
            {latest.trace.total_nodes} 次
          </Descriptions.Item>
          <Descriptions.Item label="按工况计数">
            {Object.entries(latest.trace.by_condition)
              .map(([key, count]) => `${key}×${count}`)
              .join(" · ") || "—"}
          </Descriptions.Item>
        </Descriptions>
      </Card>
      <Card title="trace 按单元聚合（公式应用次数）" size="small">
        <Table
          size="small"
          rowKey="key"
          pagination={false}
          dataSource={traceRows}
          columns={[
            { title: "单元", dataIndex: "unitId" },
            { title: "公式应用次数", dataIndex: "count", width: 140 },
          ]}
        />
      </Card>
    </>
  );
}

/** 观测面主体（opsDebugPane 消费——窄化产物直渲染）。 */
export function OpsChainView({ report }: { report: OpsChainReport }) {
  return (
    <section data-testid="wp-ops-chain-view">
      <StatusStrip report={report} />
      <TimelineCard report={report} />
      <LatestBlockCards report={report} />
    </section>
  );
}
