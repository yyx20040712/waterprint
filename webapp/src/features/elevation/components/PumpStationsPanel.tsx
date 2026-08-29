/**
 * 提升点位/跌水警告面板（D4——PumpingPlan 消费面，前端仅渲染）。
 *
 * 输入:  ElevationView（pump_stations 提升站位+drop_warnings 跌水警告）
 * 输出:  提升点位表（AntD Table）+跌水警告列表（语义色警示面）
 *
 * 规格说明（FE7 批 6b 段五，D4）：
 *   - 跌水>阈值/需提升判定全在 core（evaluate_pumping——前端零推导，
 *     骨架规格红线保持）；数值列 tabular-nums（§19.3）；
 *   - 空站位列表=全程自流合法终态（core pumps R4）——非错误态如实呈现
 *     「全程自流」文案；跌水警告空=无跌水面不渲染列表；
 *   - 扬程/流量单位 m 与 m³/s（服务端数值面口径——表头注记）。
 */
import type { CSSProperties } from "react";
import { Table, Typography } from "antd";

import type { ElevationView } from "../lib/profileChart";

const NUMERIC_STYLE: CSSProperties = { fontVariantNumeric: "tabular-nums" };

const PUMP_COLUMNS = [
  { title: "单元", dataIndex: "unit_id", key: "unit_id" },
  {
    title: "静扬程（m）",
    dataIndex: "static_head",
    key: "static_head",
    align: "right" as const,
    render: (value: number) => (
      <span style={NUMERIC_STYLE}>{value.toFixed(3)}</span>
    ),
  },
  {
    title: "总扬程（m）",
    dataIndex: "total_head",
    key: "total_head",
    align: "right" as const,
    render: (value: number) => (
      <span style={NUMERIC_STYLE}>{value.toFixed(3)}</span>
    ),
  },
  {
    title: "设计流量（m³/s）",
    dataIndex: "design_flow",
    key: "design_flow",
    align: "right" as const,
    render: (value: number) => (
      <span style={NUMERIC_STYLE}>{value.toFixed(6)}</span>
    ),
  },
  { title: "工况", dataIndex: "condition_key", key: "condition_key" },
];

export function PumpStationsPanel({ view }: { view: ElevationView }) {
  return (
    <section style={{ marginTop: 16 }}>
      <Typography.Title level={5} style={{ marginTop: 0 }}>
        提升点位与跌水警告
      </Typography.Title>
      {view.pump_stations.length === 0 ? (
        <Typography.Paragraph type="secondary">
          全程自流——无需提升（空站位列表为合法终态；跌水/提升判定来自
          core evaluate_pumping）。
        </Typography.Paragraph>
      ) : (
        <Table
          size="small"
          rowKey="unit_id"
          columns={PUMP_COLUMNS}
          dataSource={view.pump_stations}
          pagination={false}
        />
      )}
      {view.drop_warnings.length > 0 ? (
        <div style={{ marginTop: 8 }}>
          {view.drop_warnings.map((warning) => (
            <Typography.Paragraph
              key={`${warning.source}-${warning.message}`}
              type="warning"
              style={{ marginBottom: 4 }}
            >
              {warning.message}
            </Typography.Paragraph>
          ))}
        </div>
      ) : null}
    </section>
  );
}
