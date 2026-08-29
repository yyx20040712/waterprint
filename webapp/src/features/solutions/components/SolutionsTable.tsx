/**
 * 方案浏览器表格：动态列+受控分页+行级应用（D5/D6/D9——替换 M0.5 骨架）。
 *
 * 输入:  SolutionPageView（窄化后分页数据）+gridFields+projectId/unitId
 *        +受控分页（currentPage/onPageChange）+onApplied 回调透传
 * 输出:  antd Table（响应 columns 动态建列——margin_min 语义色/nan_flag
 *        不可行标记/数字列 tabular-nums；行尾「应用」按钮；受控分页）
 *
 * 规格说明（FE6 批 6b 段四，D5/D6/D9；骨架「AntD Table virtual 虚拟
 *   滚动」随实装校正——行数=网格组合数（golden 案例个位数~几十行），
 *   antd Table 常规渲染足够；万级行虚拟滚动挂账）：
 *   - 动态列=buildTableColumns(columns, gridFields) 列模型映射（列序=
 *     响应序——服务端构造序 grid 先→dim→margin_min/nan_flag/
 *     condition_key，前端不重排；行无固定列名——以 columns 建列）；
 *   - margin_min 语义色：正绿负红 null 灰（骨架规格；0 中性默认色）；
 *     nan_flag true→「不可行」红色标记（false→「—」不标）；
 *   - 数字列 fontVariantNumeric:'tabular-nums'（§19.3 等宽对齐）+右对齐；
 *   - rowKey=grid 字段值组合（枚举网格组合唯一——兜底行序）；
 *   - 受控分页（current/total/onChange——size 面恒 50 固定不切换；
 *     服务端分页排序，前端零业务计算零重排）；
 *   - 枚举语义永远单单元（ADR-005）——表内行全属 unitId 单元，无跨
 *     单元多选入口；应用后数据为已提交任务快照不自动刷新（注记）。
 */
import { Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";

import type { ApplyOutcome } from "../../../shared/api/generated/model";
import {
  buildTableColumns,
  type SolutionColumnModel,
  type SolutionPageView,
  type SolutionRow,
} from "../lib/solutionsView";
import { ApplySolutionButton } from "./ApplySolutionButton";

/** 语义色 token（正绿负红 null 灰——margin 列骨架规格；SemanticColor
 * 封装未实装，本处直用色值挂账统一出口批）。 */
const MARGIN_POSITIVE = "#52c41a";
const MARGIN_NEGATIVE = "#ff4d4f";
const VALUE_NULL = "#8c8c8c";

/** 单元格呈现（纯数据→ReactNode——数字 tabular-nums/语义色/标记）。 */
function renderCell(model: SolutionColumnModel, value: unknown) {
  if (model.kind === "margin") {
    if (value === null || value === undefined) {
      return <span style={{ color: VALUE_NULL }}>—</span>;
    }
    const numeric = typeof value === "number" ? value : null;
    if (numeric === null) {
      return <span>{String(value)}</span>;
    }
    const color =
      numeric > 0 ? MARGIN_POSITIVE : numeric < 0 ? MARGIN_NEGATIVE : undefined;
    return <span style={{ color, fontVariantNumeric: "tabular-nums" }}>{numeric}</span>;
  }
  if (model.kind === "flag") {
    return value === true ? (
      <Typography.Text type="danger">不可行</Typography.Text>
    ) : (
      <span style={{ color: VALUE_NULL }}>—</span>
    );
  }
  if (value === null || value === undefined) {
    return <span style={{ color: VALUE_NULL }}>—</span>;
  }
  if (model.numeric) {
    return (
      <span style={{ fontVariantNumeric: "tabular-nums" }}>
        {typeof value === "number" ? value : String(value)}
      </span>
    );
  }
  return <span>{String(value)}</span>;
}

export function SolutionsTable({
  page,
  gridFields,
  projectId,
  unitId,
  currentPage,
  onPageChange,
  onApplied,
}: {
  page: SolutionPageView;
  gridFields: string[];
  projectId: string;
  unitId: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  onApplied?: (outcome: ApplyOutcome) => void;
}) {
  const columns: ColumnsType<SolutionRow> = buildTableColumns(
    page.columns,
    gridFields,
  ).map((model) => ({
    title: model.key,
    dataIndex: model.key,
    key: model.key,
    align: model.numeric ? ("right" as const) : ("left" as const),
    render: (value: unknown) => renderCell(model, value),
  }));
  // 行尾操作列（方案应用——D6）
  columns.push({
    title: "操作",
    key: "apply",
    align: "left",
    render: (_, row) => (
      <ApplySolutionButton
        row={row}
        gridFields={gridFields}
        projectId={projectId}
        unitId={unitId}
        onApplied={onApplied}
      />
    ),
  });

  return (
    <Table<SolutionRow>
      size="small"
      rowKey={(row, index) =>
        gridFields.length > 0
          ? gridFields.map((field) => String(row[field])).join("|")
          : `row-${index ?? 0}`
      }
      columns={columns}
      dataSource={page.rows}
      pagination={{
        current: currentPage,
        pageSize: page.size,
        total: page.total,
        onChange: (next) => onPageChange(next),
        showSizeChanger: false,
        showTotal: (total) => `共 ${total} 行`,
      }}
    />
  );
}
