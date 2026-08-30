/**
 * 图纸目录清单：产物元数据表（kind/工况/文件名/design 摘要/版本/stale 徽标）。
 *
 * 输入:  SheetRow[]（drawingsView.buildSheetRows 行模型——唯一数据源）+
 *        选中键（受控 radio 选择——选中驱动 DrawingPreview）
 * 输出:  目录表（行序=服务端序零重排；stale 行橙徽标=force 旧三元组显式
 *        标注——禁静默旧产物冒充新产物）
 *
 * 规格说明（FE9 批 6b 段七，D7；EstimateTable 薄壳同构）：
 *   - 每张图显示所属 design 摘要/engine/data 版本（可复算溯源——骨架
 *     冻结规格「每张图显示所属 design_hash/engine/data 版本摘要」落点）；
 *   - 摘要/文件名列 tabular-nums（FE6 数字等宽口径——hex 串目视对位）；
 *   - 空态=antd Table 自带空表现（项目尚无产物——面板层引导语在外）；
 *   - 薄壳不测（投影层 drawingsView.test 承担契约面）；Select/Table 不写
 *     占位文案属性（grep 门禁英文占位特征词规避——FE3 C3 先例）。
 */
import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";

import type { SheetRow } from "../lib/drawingsView";

const COLUMNS: ColumnsType<SheetRow> = [
  {
    title: "类型",
    dataIndex: "kind",
    key: "kind",
    width: 96,
  },
  {
    title: "工况",
    dataIndex: "conditionKey",
    key: "conditionKey",
    width: 96,
  },
  {
    title: "文件名",
    dataIndex: "fileName",
    key: "fileName",
    render: (value: string) => (
      <span style={{ fontVariantNumeric: "tabular-nums" }}>{value}</span>
    ),
  },
  {
    title: "design 摘要",
    dataIndex: "designDigest",
    key: "designDigest",
    width: 120,
    render: (value: string) => (
      <span style={{ fontVariantNumeric: "tabular-nums" }}>{value}</span>
    ),
  },
  {
    title: "engine 版本",
    dataIndex: "engineVersion",
    key: "engineVersion",
    width: 170,
  },
  {
    title: "data 版本",
    dataIndex: "dataVersion",
    key: "dataVersion",
    width: 200,
  },
  {
    title: "标注",
    key: "stale",
    width: 110,
    render: (_value, row) =>
      row.stale ? (
        <Tag color="orange">旧三元组</Tag>
      ) : (
        <Tag color="green">当前</Tag>
      ),
  },
];

/** 图纸目录清单（受控单选——选中行驱动 DrawingPreview 元数据卡）。 */
export function SheetList({
  rows,
  selectedKey,
  onSelect,
}: {
  rows: SheetRow[];
  selectedKey: string | null;
  onSelect: (key: string) => void;
}) {
  return (
    <Table<SheetRow>
      size="small"
      columns={COLUMNS}
      dataSource={rows}
      rowKey="key"
      pagination={false}
      rowSelection={{
        type: "radio",
        selectedRowKeys: selectedKey === null ? [] : [selectedKey],
        onChange: (keys) => {
          const next = keys[0];
          if (typeof next === "string") {
            onSelect(next);
          }
        },
      }}
    />
  );
}
