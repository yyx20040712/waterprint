/**
 * 方案浏览器表格：动态列+受控分页+行级应用（D5/D6/D9——替换 M0.5 骨架；
 * C2 方案表重制 2026-09-10——briefs/task-C2-plan.md §2）。
 *
 * 输入:  SolutionPageView（窄化后分页数据）+gridFields+projectId/unitId
 *        +applyGateReason/applyDriftWarn（P0-2 三闸透传面）+受控分页
 *        （currentPage/onPageChange）+onApplied 回调透传
 * 输出:  antd Table（响应 columns 动态建列——列宽策略/固定首列与尾列/
 *        表头两行制[标签主行+单位副行]/数值格式化+悬浮全精度/margin_min
 *        语义色/nan_flag 不可行标记/受控分页+表头吸顶）
 *
 * 规格说明（FE6 批 6b 段四，D5/D6/D9；C2 重制六处置）：
 *   - 动态列=buildTableColumns(columns, gridFields) 列模型映射（列序=
 *     响应序——服务端构造序 grid 先→dim→margin_min/nan_flag/
 *     condition_key，前端不重排；行无固定列名——以 columns 建列）；
 *     B2（PD9）+C2：列头=中文标签（固定列名 margin_min→「最小裕量」
 *     等三列中文映射；grid 列 label_zh 降级 key）+悬浮 title 呈原 key
 *     仅当列头文案≠key（降级态无悬浮——两行重复抑制）；**两行制**：
 *     grid 列单位段=副行（11px 弱色 mono——dimUnitOf 经列模型 unit
 *     字段；空=无副行，th 底对齐保基线）；
 *   - C2 列宽策略（§2a）：tableLayout fixed+按 kind 定宽（grid 120/
 *     数值 128/可行性 96/工况 180/操作 88——antd 无 width 自适应压缩
 *     根治）；scroll.x=列宽和（容器窄出横滚——glm E① 防缝隙）；
 *     **固定首列**（index 0 fixed left——横滚行身份恒在）+**固定尾列**
 *     （操作 fixed right——应用入口恒在）；
 *   - C2 表头吸顶（§2d）：sticky（吸附最近滚动容器=body-holder 滚动域
 *     ——不引入 scroll.y 内滚域，GR-40 单一滚动域纪律防回归）；
 *   - C2 数值格式化（§2c）：formatSolutionValue（整数千分位/非整数恒
 *     3 位小数/小值 3 位有效）——16 位浮点直出根除；**全精度保留**：
 *     数字单元格 title=String(value) 悬浮原值（工程师复核通道）；
 *   - margin_min 语义色：正绿负红 null 灰（0 中性默认色——色源=C1
 *     token colorSuccess/colorError/colorTextTertiary[useToken]，GR-39
 *     散写字面量收敛——「SemanticColor 封装挂账」头注收口）；
 *     nan_flag true→「不可行」红/false→「可行」绿/null→「—」灰（C2b
 *     用户验收反馈修订——FE6「false 不标」骨架规格就此收口）；
 *   - 数字列 fontVariantNumeric:'tabular-nums'（§19.3 等宽对齐）+右对齐；
 *   - rowKey=grid 字段值组合（枚举网格组合唯一——兜底行序）；
 *   - 受控分页（current/total/onChange——size 面恒 50 固定不切换；
 *     服务端分页排序，前端零业务计算零重排）；
 *   - 枚举语义永远单单元（ADR-005）——表内行全属 unitId 单元，无跨
 *     单元多选入口；应用后数据为已提交任务快照不自动刷新（注记）；
 *   - 行密度=size small 维持（C1 controlHeight 28+fontSize 13 工程密度
 *     基线已足——§2e 不再压 cellPadding）。
 */
import { Table, Typography, theme } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { ReactNode } from "react";

import type { ApplyOutcome } from "../../../shared/api/generated/model";
import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { conditionLabel, unitNameIndex } from "../../../shared/conditionLabels";
import type { GridField } from "../lib/solutionsFields";
import {
  buildTableColumns,
  formatSolutionValue,
  type SolutionColumnModel,
  type SolutionPageView,
  type SolutionRow,
} from "../lib/solutionsView";
import { ApplySolutionButton } from "./ApplySolutionButton";

/** C2 列宽策略（§2a——px；tableLayout fixed 逐列显式宽，glm E②；
 * R 轮 A2-N-01：首列恒 120（行身份固定列——不问 kind），非首列按
 * kind 分流（grid 非首/dim/margin=数值 128——§2a 表两行口径）。 */
const FIRST_COL_WIDTH = 120;
const NUM_COL_WIDTH = 128;
const FLAG_COL_WIDTH = 96;
const TEXT_COL_WIDTH = 180;
const APPLY_COL_WIDTH = 88;

/** kind→列宽（非首列——数值列右对齐 mono 千分位 9 字符≈81px+余量）。 */
function columnWidth(model: SolutionColumnModel, isFirst: boolean): number {
  if (isFirst) {
    return FIRST_COL_WIDTH;
  }
  if (model.kind === "flag") {
    return FLAG_COL_WIDTH;
  }
  if (model.kind === "text") {
    return TEXT_COL_WIDTH;
  }
  return NUM_COL_WIDTH;
}

/** 全精度原值串（R 轮 A2-N-03：String(-0)="0" 失负号——Object.is 支
 * 保真 "-0"；显示面 formatSolutionValue 同走 INT_FORMAT 输出 "-0"）。 */
function rawValueText(value: number): string {
  return Object.is(value, -0) ? "-0" : String(value);
}

/** 语义色档（margin 列骨架规格——C1 token 色，useToken 消费）。 */
type SemanticColors = {
  positive: string;
  negative: string;
  null: string;
  tertiary: string;
  mono: string;
};

/** 单元格呈现（纯数据→ReactNode——格式化/tabular-nums/语义色/标记；
 * title=原值全精度悬浮；工况面 UX 反馈批件 1：text 列=condition_key
 * 值中文化（conditionLabel 工程全称，悬浮原始键）。 */
function renderCell(
  model: SolutionColumnModel,
  value: unknown,
  colors: SemanticColors,
  unitNames: Record<string, string>,
): ReactNode {
  if (model.kind === "margin") {
    if (value === null || value === undefined) {
      return <span style={{ color: colors.null }}>—</span>;
    }
    if (typeof value === "number") {
      const color =
        value > 0 ? colors.positive : value < 0 ? colors.negative : undefined;
      return (
        <span
          title={rawValueText(value)}
          style={{ color, fontVariantNumeric: "tabular-nums" }}
        >
          {formatSolutionValue(value)}
        </span>
      );
    }
    return <span>{String(value)}</span>;
  }
  if (model.kind === "flag") {
    // C2b（用户验收反馈 2026-09-10）：三态呈现——true→红「不可行」/
    // false→绿「可行」（全库 nan_flag 恒 false 数据现实下列面全「—」
    // 空观感——FE6「false 不标」骨架规格就此修订）/null→灰「—」（缺值）
    if (value === true) {
      return <Typography.Text type="danger">不可行</Typography.Text>;
    }
    if (value === false) {
      return <Typography.Text type="success">可行</Typography.Text>;
    }
    return <span style={{ color: colors.null }}>—</span>;
  }
  if (value === null || value === undefined) {
    return <span style={{ color: colors.null }}>—</span>;
  }
  if (model.numeric && typeof value === "number") {
    return (
      <span
        title={rawValueText(value)}
        style={{ fontVariantNumeric: "tabular-nums" }}
      >
        {formatSolutionValue(value)}
      </span>
    );
  }
  // 件 1：text 列值域=condition_key（FIXED_TITLES 唯一 text 列）——
  // 工程全称+悬浮原始键（用户裁定追溯面口径）
  if (model.kind === "text") {
    const key = String(value);
    return <span title={key}>{conditionLabel(key, unitNames)}</span>;
  }
  return <span>{String(value)}</span>;
}

/** 两行表头（§2b）：标签主行+单位副行（11px 弱色 mono；空=无副行）；
 * 悬浮 title 呈原 key 仅当文案≠key（B2 PD9 防两行重复口径沿）。 */
function renderHeader(model: SolutionColumnModel, colors: SemanticColors): ReactNode {
  const label =
    model.title === model.key ? (
      model.title
    ) : (
      <span title={model.key}>{model.title}</span>
    );
  if (model.unit === "") {
    return <span>{label}</span>;
  }
  return (
    <span>
      <span style={{ display: "block" }}>{label}</span>
      <span
        style={{
          display: "block",
          fontSize: 11,
          fontFamily: colors.mono,
          color: colors.tertiary,
          fontWeight: 400,
        }}
      >
        {model.unit}
      </span>
    </span>
  );
}

export function SolutionsTable({
  page,
  gridFields,
  dimFields,
  projectId,
  unitId,
  applyGateReason,
  applyDriftWarn,
  currentPage,
  onPageChange,
  onApplied,
}: {
  page: SolutionPageView;
  gridFields: GridField[];
  /** V2 GOV5 批尾：计算派生输出量列族（manifest.out_dims 声明面——
   * dim 列中文名真源；缺省 []=历史任务载荷无此键的降级形态）。 */
  dimFields?: GridField[];
  projectId: string;
  unitId: string | null;
  /** P0-2 应用闸禁用因（非 null=行级应用钮禁用+title 述因）。 */
  applyGateReason: string | null;
  /** P0-2 版本漂移警示（true=应用钮 Popconfirm 二次确认）。 */
  applyDriftWarn: boolean;
  currentPage: number;
  onPageChange: (page: number) => void;
  onApplied?: (outcome: ApplyOutcome) => void;
}) {
  // C2 语义色收敛（§2f）：antd token 主源（GR-39——散写字面量删除）
  const { token } = theme.useToken();
  // 工况面 UX 反馈批件 1：工况条件列值中文名（catalog name_zh 真源）
  const unitNames =
    useListUnitsApiUnitsGet({ query: { select: unitNameIndex } }).data ?? {};
  const colors: SemanticColors = {
    positive: token.colorSuccess,
    negative: token.colorError,
    null: token.colorTextTertiary,
    tertiary: token.colorTextTertiary,
    mono: token.fontFamilyCode,
  };

  const columns: ColumnsType<SolutionRow> = buildTableColumns(
    page.columns,
    gridFields,
    dimFields ?? [],
  ).map((model, index) => ({
    title: renderHeader(model, colors),
    dataIndex: model.key,
    key: model.key,
    width: columnWidth(model, index === 0),
    // R 轮 G2-01：th 底对齐（视觉稿同形态——单/两行表头混排基线齐）
    onHeaderCell: () => ({ style: { verticalAlign: "bottom" } }),
    align: model.numeric ? ("right" as const) : ("left" as const),
    // C2 固定首列（§2a）：横滚行身份恒在
    fixed: index === 0 ? ("left" as const) : undefined,
    render: (value: unknown) => renderCell(model, value, colors, unitNames),
  }));
  // 行尾操作列（方案应用——D6；固定尾列：应用入口横滚恒在）
  columns.push({
    title: "操作",
    key: "apply",
    width: APPLY_COL_WIDTH,
    align: "left",
    fixed: "right",
    render: (_, row) => (
      <ApplySolutionButton
        row={row}
        gridFields={gridFields}
        projectId={projectId}
        unitId={unitId}
        gateReason={applyGateReason}
        driftWarn={applyDriftWarn}
        onApplied={onApplied}
      />
    ),
  });
  // C2 scroll.x=列宽和（glm E①：总宽不溢出则固定列空转/缝隙；width 面
  // ColumnsType 允许 string——本表恒 number，非 number 不计）
  const scrollX = columns.reduce(
    (sum, column) => sum + (typeof column.width === "number" ? column.width : 0),
    0,
  );

  return (
    <Table<SolutionRow>
      size="small"
      sticky
      tableLayout="fixed"
      scroll={{ x: scrollX }}
      rowKey={(row) =>
        // ADR-018 D5：condition_key 入键前缀——多工况行同网格档撞键修复
        //（枚举全工况化后同参档各工况一行；退化分支 JSON.stringify 已含
        // condition_key 天然免疫）。
        `${String(row["condition_key"] ?? "")}|` +
        (gridFields.length > 0
          ? gridFields.map((field) => String(row[field.key])).join("|")
          : JSON.stringify(row)) // GD-04：退化分支不截断（长公共前缀撞键
          // 残余风险——行数据量小全量串无代价；antd v6 index 参数弃用沿 D2）
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
