/**
 * 概算分级汇总表：分部分项/措施/间接/预备/税（可折叠溯源行）。
 *
 * 输入:  CostView（estimateView 窄化产物——buildTableRows 行模型唯一源）
 * 输出:  分级汇总表（明细行可展开溯源=price_key+source_field_ids+
 *        unit_price+repro 串——M4「任一数字可回溯」前端落点）
 *
 * 规格说明（FE8 批 6b 段六，D5；R 轮 R4/R5 修复 2026-08-29）：
 *   - 行序=服务端装配序（buildTableRows 产物直投——前端不重排）；
 *     小计行族+工程总投资行高亮（R4：onRow 内联 style——webapp 零 CSS
 *     文件，类名无视觉落点，grand 加粗+背景/subtotal 轻背景）；
 *   - 费率列（R5：fee 行 rate 百分比显示，detail/小计行留空——费桶
 *     构成「费率×基数」UI 可见面；显示层格式化非推导）；
 *   - 金额 tabular-nums 右对齐（数字等宽——分级求和目视对位）；零推导：
 *     金额全部行模型原值渲染，前端不重算分级自洽（服务端契约）；
 *   - 每笔溯源=detail 行展开区（price_key+source_field_ids+unit_price+
 *     repro 三元组串——深链 calcbook 挂账 M4④，面板只显示 repro 字符串）；
 *   - 表列中文列名=服务端下发 name_zh 单一真源直投（label 列——禁前端
 *     i18n 双源；fee 行 label=fee_key 字段 ID 原样——骨架「中文列名走
 *     i18n 显示层」措辞随 FE8 裁决 D4 收口：服务面单一真源）；
 *   - Select/Table 不写占位文案属性（grep 门禁英文占位特征词规避——
 *     FE3 C3 先例）；薄壳不测（投影层 estimateView.test 承担契约面）。
 */
import { Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { CSSProperties } from "react";

import {
  buildTableRows,
  type CostView,
  type EstimateTableRow,
} from "../lib/estimateView";

/** 金额格式（千分位+两位小数——显示层格式化，非推导）。 */
function formatAmount(value: number): string {
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** 费率格式（百分比——R5 费桶构成可见面；显示层格式化非推导）。 */
function formatRate(rate: number): string {
  return `${(rate * 100).toLocaleString("zh-CN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}%`;
}

/**
 * 行类别内联样式（R4——§19 视觉层级；webapp 零 CSS 文件：类名无视觉
 * 落点，antd onRow style 直挂 tr；中性背景非语义色位[绿/橙/红/蓝保留]）。
 */
function rowStyle(row: EstimateTableRow): CSSProperties {
  if (row.kind === "grand") {
    return {
      fontWeight: 600,
      background: "rgba(255, 255, 255, 0.10)",
    };
  }
  return row.kind === "subtotal"
    ? { fontWeight: 500, background: "rgba(255, 255, 255, 0.05)" }
    : {};
}

const COLUMNS: ColumnsType<EstimateTableRow> = [
  { title: "项目", dataIndex: "label", key: "label" },
  {
    title: "桶别",
    key: "bucket",
    width: 96,
    render: (_value, row) => row.bucket ?? "",
  },
  {
    title: "数量",
    key: "quantity",
    width: 110,
    align: "right",
    render: (_value, row) =>
      row.quantity === undefined
        ? ""
        : `${row.quantity.toLocaleString("zh-CN")} ${row.unit ?? ""}`.trim(),
  },
  {
    title: "费率",
    key: "rate",
    width: 88,
    align: "right",
    render: (_value, row) =>
      row.rate === undefined ? "" : formatRate(row.rate),
  },
  {
    title: "金额（元）",
    key: "amount",
    width: 160,
    align: "right",
    render: (_value, row) => (
      <span style={{ fontVariantNumeric: "tabular-nums" }}>
        {formatAmount(row.amount)}
      </span>
    ),
  },
];

/** 概算分级汇总表（明细行可展开溯源——D5；高亮/费率面 R4/R5）。 */
export function EstimateTable({ view }: { view: CostView }) {
  const rows = buildTableRows(view);
  return (
    <Table<EstimateTableRow>
      size="small"
      columns={COLUMNS}
      dataSource={rows}
      rowKey="key"
      onRow={(row) => ({ style: rowStyle(row) })}
      pagination={false}
      expandable={{
        // 仅明细行可展开（费用/小计行无逐笔溯源面）
        rowExpandable: (row) => row.kind === "detail" && row.trace !== undefined,
        expandedRowRender: (row) =>
          row.trace ? (
            <Typography.Text type="secondary">
              定额键 {row.trace.price_key}｜来源字段{" "}
              {row.trace.source_field_ids.join("、")}｜单价{" "}
              {row.trace.unit_price.toLocaleString("zh-CN")} 元｜可复算三元组{" "}
              {row.trace.repro}
            </Typography.Text>
          ) : null,
      }}
    />
  );
}
