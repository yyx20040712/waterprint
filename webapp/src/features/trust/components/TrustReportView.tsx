/**
 * 可信度报告主体视图：状态条+四区块卡（收敛/水量平衡/出水裕度/警告汇总）。
 *
 * 输入:  TrustReport 窄化产物（useTrustQuery select 通道）
 * 输出:  纯展示组件（无取数无路由——trustPane 装配壳消费）
 *
 * 规格说明（P2 次批 ADR-012；IndicatorsCard/PumpStationsPanel 展示先例）：
 *   - 状态条：stale 黄条（结果过期——重算提示）+降级蓝条（旧结果无诊断件
 *     ——ADR-012 R1"已算但无数据"与"未算"显式区分）+溯源小字
 *     （repro 三元组+task_id）；
 *   - 收敛卡：loop_params 口径三键（容差/上限/阻尼实际生效值——口径
 *     透明）+逐回路迭代步数/末步残差；空=「本图无回路」前馈直算注记；
 *   - 水量平衡卡：厂级源汇闭合（水/泥线分线）+单元进出偏差清单
 *     （泥线减量单元残差=工艺性水量变化注记——非数值错误）；
 *   - 出水裕度卡：工况×标准×六指标对照（margin 语义色正绿负红——
 *     SolutionsTable 同纪律；值/限值 mg/L 直显）；
 *   - 警告汇总卡：分级计数 Tag+明细表（severity Alert 语义色
 *     PumpStationsPanel 同映射；unit_id 定位+param_key 调节方向）。
 */
import { Alert, Card, Descriptions, Empty, Table, Tag, Typography } from "antd";

import {
  fluidLabel,
  formatFlow,
  formatRel,
  formatSci,
  loopParamLabel,
  marginText,
  marginTone,
  severityTone,
  type TrustReport,
} from "../lib/trustView";

const MARGIN_COLORS: Record<"ok" | "over", string> = {
  ok: "green",
  over: "red",
};

const SEVERITY_COLORS: Record<"error" | "warning" | "info", string> = {
  error: "red",
  warning: "orange",
  info: "blue",
};

function StatusStrip({ report }: { report: TrustReport }) {
  return (
    <div data-testid="wp-trust-status">
      {report.stale && (
        <Alert
          type="warning"
          showIcon
          title="结果已过期：计算后设计有变更——建议重新提交计算获取最新可信度报告。"
          style={{ marginBottom: 12 }}
        />
      )}
      {!report.diagnostics_available && (
        <Alert
          type="info"
          showIcon
          data-testid="wp-trust-degraded"
          title="本结果由旧版本计算（无诊断数据）：重新提交计算后可获取收敛/水量平衡/出水裕度诊断。"
          style={{ marginBottom: 12 }}
        />
      )}
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        结果溯源：design_hash {report.design_hash} · engine {report.engine_version} ·
        data {report.data_version} · task {report.task_id}
      </Typography.Text>
    </div>
  );
}

function ConvergenceCard({ report }: { report: TrustReport }) {
  const paramEntries = Object.entries(report.loop_params);
  return (
    <Card
      size="small"
      title="回路收敛"
      style={{ marginBottom: 12 }}
      data-testid="wp-trust-convergence"
    >
      {paramEntries.length > 0 && (
        <Descriptions
          size="small"
          column={3}
          items={paramEntries.map(([key, value]) => ({
            key,
            label: loopParamLabel(key),
            children: key === "loop.max_iterations" ? value : formatSci(value),
          }))}
          style={{ marginBottom: 8 }}
        />
      )}
      {!report.diagnostics_available ? (
        <Typography.Text type="secondary">
          诊断数据不可用（旧版本结果）——重新提交计算后可获取收敛统计。
        </Typography.Text>
      ) : report.convergence.length === 0 ? (
        <Typography.Text type="secondary">
          本图无回路（前馈直算）——无迭代收敛过程。
        </Typography.Text>
      ) : (
        <Table
          size="small"
          rowKey={(row) => `${row.condition_key}:${row.loop_nodes.join("+")}`}
          pagination={false}
          dataSource={[...report.convergence]}
          columns={[
            { title: "工况", dataIndex: "condition_key" },
            {
              title: "回路单元",
              dataIndex: "loop_nodes",
              render: (nodes: string[]) => nodes.join(" + "),
            },
            { title: "迭代步数", dataIndex: "iterations", align: "right" },
            {
              title: "末步残差",
              dataIndex: "final_residual",
              align: "right",
              render: (value: number) => formatSci(value),
            },
          ]}
        />
      )}
    </Card>
  );
}

function BalanceCard({ report }: { report: TrustReport }) {
  const lineRows = report.mass_balance.flatMap((closure) =>
    closure.lines.map((line) => ({
      key: `${closure.condition_key}:${line.fluid}`,
      condition_key: closure.condition_key,
      fluid: line.fluid,
      q_sources_total: line.q_sources_total,
      q_sinks_total: line.q_sinks_total,
      closure_rel: line.closure_rel,
    })),
  );
  const unitRows = report.mass_balance.flatMap((closure) =>
    closure.unit_imbalances.map((unit) => ({
      key: `${closure.condition_key}:${unit.unit_id}:${unit.fluid}`,
      condition_key: closure.condition_key,
      unit_id: unit.unit_id,
      fluid: unit.fluid,
      q_in: unit.q_in,
      q_out: unit.q_out,
      delta_rel: unit.delta_rel,
    })),
  );
  return (
    <Card
      size="small"
      title="水量平衡（数值闭合审计）"
      style={{ marginBottom: 12 }}
      data-testid="wp-trust-balance"
    >
      {lineRows.length === 0 && unitRows.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            report.diagnostics_available
              ? "暂无水量平衡数据"
              : "诊断数据不可用（旧版本结果）——重新提交计算后可获取"
          }
        />
      ) : (
        <>
          <Table
            size="small"
            rowKey="key"
            pagination={false}
            dataSource={lineRows}
            columns={[
              { title: "工况", dataIndex: "condition_key" },
              {
                title: "流体线",
                dataIndex: "fluid",
                render: (fluid: string) => fluidLabel(fluid),
              },
              {
                title: "源侧总出流（m³/s）",
                dataIndex: "q_sources_total",
                align: "right",
                render: (value: number) => formatFlow(value),
              },
              {
                title: "汇侧总出流（m³/s）",
                dataIndex: "q_sinks_total",
                align: "right",
                render: (value: number) => formatFlow(value),
              },
              {
                title: "厂级闭合差",
                dataIndex: "closure_rel",
                align: "right",
                render: (value: number) => formatRel(value),
              },
            ]}
            style={{ marginBottom: 8 }}
          />
          {unitRows.length > 0 && (
            <>
              <Typography.Text
                type="secondary"
                style={{ fontSize: 12, display: "block", marginBottom: 4 }}
              >
                单元进出偏差（泥线浓缩/消化/脱水/干化单元的水量变化属工艺性
                减量，非数值错误）：
              </Typography.Text>
              <Table
                size="small"
                rowKey="key"
                pagination={{ pageSize: 8, hideOnSinglePage: true }}
                dataSource={unitRows}
                columns={[
                  { title: "工况", dataIndex: "condition_key" },
                  { title: "单元", dataIndex: "unit_id" },
                  {
                    title: "流体线",
                    dataIndex: "fluid",
                    render: (fluid: string) => fluidLabel(fluid),
                  },
                  {
                    title: "入流（m³/s）",
                    dataIndex: "q_in",
                    align: "right",
                    render: (value: number) => formatFlow(value),
                  },
                  {
                    title: "出流（m³/s）",
                    dataIndex: "q_out",
                    align: "right",
                    render: (value: number) => formatFlow(value),
                  },
                  {
                    title: "进出偏差",
                    dataIndex: "delta_rel",
                    align: "right",
                    render: (value: number) => formatRel(value),
                  },
                ]}
              />
            </>
          )}
        </>
      )}
    </Card>
  );
}

function EffluentCard({ report }: { report: TrustReport }) {
  return (
    <Card
      size="small"
      title="出水达标裕度（GB 18918-2002 参考面）"
      style={{ marginBottom: 12 }}
      data-testid="wp-trust-effluent"
    >
      {report.effluent.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            report.diagnostics_available
              ? "暂无出水指标数据（终端无水质指标或标准未覆盖）"
              : "诊断数据不可用（旧版本结果）——重新提交计算后可获取"
          }
        />
      ) : (
        <Table
          size="small"
          rowKey={(row) =>
            `${row.condition_key}:${row.standard_id}:${row.indicator}`
          }
          pagination={{ pageSize: 24, hideOnSinglePage: true }}
          dataSource={[...report.effluent]}
          columns={[
            { title: "工况", dataIndex: "condition_key" },
            { title: "标准", dataIndex: "standard_id" },
            { title: "指标", dataIndex: "indicator" },
            {
              title: "计算值（mg/L）",
              dataIndex: "value",
              align: "right",
              render: (value: number) => value.toFixed(3),
            },
            {
              title: "限值（mg/L）",
              dataIndex: "limit",
              align: "right",
              render: (value: number) => value.toFixed(3),
            },
            {
              title: "裕度",
              dataIndex: "margin",
              align: "right",
              render: (value: number) => (
                <Tag color={MARGIN_COLORS[marginTone(value)]}>
                  {marginText(value)}
                </Tag>
              ),
            },
          ]}
        />
      )}
    </Card>
  );
}

function WarningsCard({ report }: { report: TrustReport }) {
  const counts = Object.entries(report.warning_counts);
  return (
    <Card
      size="small"
      title="校核警告汇总"
      data-testid="wp-trust-warnings"
    >
      {counts.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          {counts.map(([level, count]) => (
            <Tag
              key={level}
              color={SEVERITY_COLORS[severityTone(level)]}
              style={{ marginRight: 8 }}
            >
              {level} × {count}
            </Tag>
          ))}
        </div>
      )}
      {report.warnings.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="全工况零警告——所有校核项均在建议带内"
        />
      ) : (
        <Table
          size="small"
          rowKey={(row, index) =>
            `${row.unit_id}:${row.condition_key ?? ""}:${row.source}:${index}`
          }
          pagination={{ pageSize: 8, hideOnSinglePage: true }}
          dataSource={[...report.warnings]}
          columns={[
            { title: "单元", dataIndex: "unit_id" },
            {
              title: "级别",
              dataIndex: "severity",
              render: (value: string) => (
                <Tag color={SEVERITY_COLORS[severityTone(value)]}>{value}</Tag>
              ),
            },
            { title: "工况", dataIndex: "condition_key" },
            { title: "提示", dataIndex: "message" },
            { title: "出处", dataIndex: "source" },
            {
              title: "调节方向",
              dataIndex: "param_key",
              render: (value: string | null) => value ?? "—",
            },
          ]}
        />
      )}
    </Card>
  );
}

/** 可信度报告主体（纯展示——数据/路由/取数均在 trustPane 装配壳）。 */
export function TrustReportView({ report }: { report: TrustReport }) {
  return (
    <div data-testid="wp-trust-report">
      <StatusStrip report={report} />
      <ConvergenceCard report={report} />
      <BalanceCard report={report} />
      <EffluentCard report={report} />
      <WarningsCard report={report} />
    </div>
  );
}
