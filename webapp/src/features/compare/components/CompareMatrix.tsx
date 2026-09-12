/**
 * CompareMatrix（多工况对比矩阵——P2 第三批 ADR-018 D1 呈现件）。
 *
 * 输入:  CompareReport（窄化产物：condition_keys 列头+metrics/warnings
 *        行族）+pinned 锁定基准键集（失效键灰显列头标注）
 * 输出:  指标矩阵表（行=单元×字段[输出量]，列=工况；max/min 差异
 *        高亮——同值无差异不高亮）+警告计数表（稀疏面）
 *
 * 规格说明（P2 第三批 ADR-018 D1/D3）：
 *   - 行=单元 out_dims 声明面（服务端聚合——本组件纯呈现）；列=
 *     condition_keys sorted 序；单元格缺值键="—"（NaN 无值键不出载荷）；
 *   - 差异高亮（D1）：行内跨工况 max=加粗、min=下划线（全等行零标注
 *     ——正绿负红语义不适用于容积/时长等无上限指标，极值标注即差异面）；
 *   - 锁定基准列头：pinned 键集打 ★ 标；失效键（受检集变更后不在
 *     当前工况）灰显+「已移除」标注（D3——不自动删，清理经重新锁定）；
 *   - 单位列=dimUnit(dim)（shared/dimLabels 单位真源——空串=无量纲
 *     不出列段）。
 */
import { Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";

import { dimUnit } from "../../../shared/dimLabels";
import {
  formatMetricValue,
  metricLabel,
  metricRowKey,
  rowExtremes,
  type CompareReport,
} from "../lib/compareView";

/** 矩阵行模型（Table dataSource 面——指标行拍平）。 */
type MatrixRow = {
  key: string;
  unit_id: string;
  field: string;
  unit: string;
  values: Record<string, number>;
};

const MATRIX_VALUE_STYLE: React.CSSProperties = {
  fontVariantNumeric: "tabular-nums",
};

/** 工况列头（锁定基准标★+失效灰显——D3 锁定语义呈现面）。 */
function conditionTitle(key: string, pinned: boolean, expired: boolean) {
  return (
    <span
      style={expired ? { color: "var(--wp-text-secondary)" } : undefined}
      title={expired ? "该工况已随受检集变更移除（重新锁定可清理）" : undefined}
    >
      {key}
      {pinned ? " ★" : ""}
      {expired ? "（已移除）" : ""}
    </span>
  );
}

export function CompareMatrix({
  report,
  pinned,
}: {
  report: CompareReport;
  /** 锁定基准键集（null=未锁定零标注）。 */
  pinned: readonly string[] | null;
}) {
  const rows: MatrixRow[] = report.metrics.map((metric) => ({
    key: metricRowKey(metric.unit_id, metric.field_id),
    unit_id: metric.unit_id,
    field: metricLabel(metric),
    unit: dimUnit(metric.dim),
    values: metric.values,
  }));

  const columns: ColumnsType<MatrixRow> = [
    {
      title: "单元",
      dataIndex: "unit_id",
      key: "unit_id",
      width: 160,
      ellipsis: true,
    },
    {
      title: "指标",
      dataIndex: "field",
      key: "field",
      width: 150,
      ellipsis: true,
    },
    {
      title: "单位",
      dataIndex: "unit",
      key: "unit",
      width: 80,
      render: (unit: string) => (unit === "" ? "—" : unit),
    },
    ...report.condition_keys.map<ColumnsType<MatrixRow>[number]>((key) => ({
      title: conditionTitle(
        key,
        pinned?.includes(key) ?? false,
        pinned !== null && !report.condition_keys.includes(key) && pinned.includes(key),
      ),
      key,
      align: "right" as const,
      render: (_, row) => {
        const value = row.values[key];
        if (typeof value !== "number") {
          return <span style={{ color: "var(--wp-text-secondary)" }}>—</span>;
        }
        const { maxKey, minKey } = rowExtremes(row.values, report.condition_keys);
        return (
          <span
            style={{
              ...MATRIX_VALUE_STYLE,
              fontWeight: key === maxKey ? 700 : undefined,
              textDecoration: key === minKey ? "underline" : undefined,
            }}
          >
            {formatMetricValue(value)}
          </span>
        );
      },
    })),
  ];

  return (
    <div data-testid="wp-compare-matrix">
      <Table<MatrixRow>
        size="small"
        rowKey="key"
        columns={columns}
        dataSource={rows}
        pagination={false}
        locale={{ emptyText: "暂无对比指标（单元尚未声明 out_dims 输出量——随批扩面）" }}
      />
      {report.warnings.length > 0 ? (
        <section style={{ marginTop: 12 }}>
          <Typography.Text type="secondary">警告计数（分级明细见「可信度」标签）</Typography.Text>
          <Table
            size="small"
            rowKey="unit_id"
            pagination={false}
            dataSource={[...report.warnings]}
            columns={[
              { title: "单元", dataIndex: "unit_id", key: "unit_id", width: 200 },
              ...report.condition_keys.map<ColumnsType<(typeof report.warnings)[number]>[number]>(
                (key) => ({
                  title: key,
                  key,
                  align: "right" as const,
                  render: (_, row) => {
                    const count = row.counts[key];
                    return typeof count === "number" && count > 0 ? (
                      <Typography.Text type="warning">{count}</Typography.Text>
                    ) : (
                      <span style={{ color: "var(--wp-text-secondary)" }}>0</span>
                    );
                  },
                }),
              ),
            ]}
          />
        </section>
      ) : null}
    </div>
  );
}
