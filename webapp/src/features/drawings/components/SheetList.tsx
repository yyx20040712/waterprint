/**
 * 图纸目录清单：产物元数据表（M5 序号+kind/工况/文件名/design 摘要/版本/
 * stale 徽标+EXPD 操作列下载按钮）。
 *
 * 输入:  SheetRow[]（drawingsView.buildSheetRows 行模型——唯一数据源）+
 *        选中键（受控 radio 选择——选中驱动 DrawingPreview）
 * 输出:  目录表（行序=服务端序零重排；stale 行橙徽标=force 旧三元组显式
 *        标注——禁静默旧产物冒充新产物；操作列下载=GET /api/exports/
 *        {file_name}——浏览器下载动作即反馈，成功零额外消息）
 *
 * 规格说明（FE9 批 6b 段七，D7；EstimateTable 薄壳同构；EXPD §2.4 D5
 *   +总控修正③ 2026-09-05）：
 *   - 每张图显示所属 design 摘要/engine/data 版本（可复算溯源——骨架
 *     冻结规格「每张图显示所属 design_hash/engine/data 版本摘要」落点）；
 *   - 摘要/文件名列 tabular-nums（FE6 数字等宽口径——hex 串目视对位）；
 *   - 空态=antd Table 自带空表现（项目尚无产物——面板层引导语在外）；
 *   - EXPD 操作列：hook（useExportDownload）组件内直调（行操作与行渲染
 *     同文件内聚——Kimi D5 裁量）；每行下载 Button loading=行 pending
 *     （仅当前行禁用转圈不阻塞他行）；错误呈现沿 ExportButton 先例
 *     message.useMessage()+contextHolder（不用静态 message.error）——
 *     WaterprintApiError→messageApi.error(err.message)，网络错/未知面
 *     「下载失败：」前缀（I-3 分级——不挂误导引导）；
 *   - 薄壳不测（投影层 drawingsView.test 承担契约面；下载可测核归
 *     useExportDownload.test）；Select/Table 不写占位文案属性（grep
 *     门禁英文占位特征词规避——FE3 C3 先例）。
 */
import { Button, Table, Tag, message } from "antd";
import type { ColumnsType } from "antd/es/table";

import { WaterprintApiError } from "../../../shared/api/http";
import { useExportDownload } from "../api/useExportDownload";
import type { SheetRow } from "../lib/drawingsView";

const COLUMNS: ColumnsType<SheetRow> = [
  {
    // M5 D5：序号=行序 1..N（目录序——render index 派生非 ExportMeta 字段，
    // lib 行模型零改最小面；列首位置=类型列前）。
    title: "序号",
    key: "index",
    width: 64,
    render: (_value, _row, index) => index + 1,
  },
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

/** 图纸目录清单（受控单选——选中行驱动 DrawingPreview 元数据卡；操作列行级下载）。 */
export function SheetList({
  rows,
  selectedKey,
  onSelect,
}: {
  rows: SheetRow[];
  selectedKey: string | null;
  onSelect: (key: string) => void;
}) {
  // EXPD 修正③：错误呈现沿 ExportButton 先例（useMessage+contextHolder——
  // 不用静态 message.error）；成功零额外消息（浏览器下载动作即反馈）。
  const [messageApi, contextHolder] = message.useMessage();
  const { download, pendingFileName } = useExportDownload();
  const startDownload = (fileName: string) => {
    void download(fileName).catch((error: unknown) => {
      if (error instanceof WaterprintApiError) {
        messageApi.error(error.message); // 服务端统一错误体 detail 原文透传
        return;
      }
      messageApi.error(
        `下载失败：${error instanceof Error ? error.message : String(error)}`,
      ); // 网络错/未知面（I-3 分级——不挂误导引导）
    });
  };
  const columns: ColumnsType<SheetRow> = [
    ...COLUMNS,
    {
      // EXPD D5：操作列下载（行级 pending——仅当前行禁用转圈不阻塞他行）。
      title: "操作",
      key: "actions",
      width: 96,
      render: (_value, row) => (
        <Button
          size="small"
          loading={pendingFileName === row.fileName}
          onClick={() => startDownload(row.fileName)}
        >
          下载
        </Button>
      ),
    },
  ];
  return (
    <>
      {contextHolder}
      <Table<SheetRow>
        size="small"
        columns={columns}
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
    </>
  );
}
