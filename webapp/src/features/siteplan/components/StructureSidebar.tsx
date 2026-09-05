/**
 * 选中结构侧栏纯展示子件（B3 R7 自 SiteplanPane.tsx L410-488 侧栏块抽离
 * ——ENG6 SiteplanToolbar 同构先例）：标高编辑/间距校核分组/红线越界分组/
 * 移出按钮/操作提示。
 *
 * 输入:  props 单向穿隧——selection（store 选中面）/structure（选中摆放）/
 *        spacingRows（该结构间距违规行）/boundaryRows（该结构红线越界行）/
 *        onElev/onRemove（编辑回调——unitId 随selection 携带）
 * 输出:  aside 侧栏 JSX（零业务推导——行数据全部由 SiteplanPane 预聚合）
 */

import { Button, InputNumber, Typography } from "antd";

import type {
  BoundaryViolationEntry,
  SpacingViolationEntry,
} from "../../../shared/api/generated/model";
import { semanticColor } from "../../../shared/ui/semanticColors";
import type { StructurePlacement } from "../lib/projectSite";
import type { SiteplanSelection } from "../store/siteplanStore";

/** 选中结构侧栏宽度（像素——显示层常量）。 */
const SIDE_WIDTH = 220;

export type StructureSidebarProps = {
  selection: SiteplanSelection;
  structure: StructurePlacement;
  spacingRows: SpacingViolationEntry[];
  boundaryRows: BoundaryViolationEntry[];
  onElev: (unitId: string, elevation: number | null) => void;
  onRemove: (unitId: string) => void;
};

export function StructureSidebar({
  selection, structure, spacingRows, boundaryRows, onElev, onRemove,
}: StructureSidebarProps) {
  const selectedId = selection.kind === "structure" ? selection.id : "";
  return (
    <aside
      style={{
        width: SIDE_WIDTH,
        flexShrink: 0,
        padding: "8px 12px",
        borderLeft: "1px solid #434343",
        overflowY: "auto",
      }}
    >
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        选中构筑物
      </Typography.Text>
      <div style={{ fontFamily: "monospace", fontSize: 12, margin: "4px 0" }}>
        {selection.kind === "structure" ? selection.id : ""}
      </div>
      <div style={{ fontSize: 12, color: "#8c8c8c" }}>
        x {structure.x} m · y {structure.y} m · 旋转{" "}
        {structure.rotation}°
      </div>
      <div style={{ margin: "8px 0 4px", fontSize: 12 }}>
        设计地面标高 ground_elevation（m，可空）
      </div>
      <InputNumber
        size="small"
        style={{ width: 140 }}
        value={structure.ground_elevation}
        onChange={(value) => {
          if (selection !== null && selection.kind === "structure") {
            onElev(selection.id, value);
          }
        }}
      />
      {spacingRows.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            间距校核（越限 {spacingRows.length}）
          </Typography.Text>
          {spacingRows.map((row) => (
            <div key={`${row.a}:${row.b}:${row.threshold_m}:${row.severity}`} style={{ fontSize: 12, marginTop: 4, color: row.severity === "ERROR" ? "#ff4d4f" : "#faad14" }}>
              {row.a === selectedId ? row.b : row.a}：净距 {row.clearance_m.toFixed(1)} m ＜ 阈值 {row.threshold_m} m（{row.severity === "ERROR" ? "错误" : "警告"}）
            </div>
          ))}
        </div>
      ) : null}
      {boundaryRows.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            红线越界（{boundaryRows.length}）
          </Typography.Text>
          {boundaryRows.map((row) => (
            <div
              key={`${row.unit_id}:${row.severity}`}
              style={{ fontSize: 12, marginTop: 4, color: semanticColor("boundary_error") }}
            >
              {row.message}（{row.severity === "ERROR" ? "错误" : "警告"}）
            </div>
          ))}
        </div>
      ) : null}
      <div style={{ marginTop: 10 }}>
        <Button
          size="small"
          danger
          onClick={() => {
            if (selection !== null && selection.kind === "structure") {
              onRemove(selection.id);
            }
          }}
        >
          移出布置（回待摆区）
        </Button>
      </div>
      <div style={{ marginTop: 10, fontSize: 12, color: "#8c8c8c" }}>
        拖拽移动=坐标网吸附；旋转把手=90° 吸附（Shift 自由）；画布双击
        构筑物=移出。
      </div>
    </aside>
  );
}
