/**
 * 布置工具栏：工具组/吸附/坐标网/复位/清空红线/折线参数/保存+错误行
 * （ENG6 自 SiteplanPane 拆出——纯展示组件，态与回调全经 props）。
 *
 * 输入:  工具栏消费面 props（工具+两开关+复位+折线面板挂起态与内容+
 *        红线空旗标+清空回调+保存三态+错误文本+场景不可得旗标）
 * 输出:  工具栏区 JSX（按钮组+清空 Popconfirm 确认门+保存错误文本行）
 *
 * 规格说明（ENG6 批，简报 §一.P2/§三 D3·D4）：
 *   - 工具组四值 select/road/corridor/boundary（L4a 第四态沿承）——当前
 *     工具=primary 其余 default（SiteplanPane 既有先例形态原样搬迁）；
 *   - 清空红线（M3 挂账销账·L4 简报预列在册）：danger Button+Popconfirm
 *     确认门+boundary 空时 disabled（无可清空）；确认才回调 onClearBoundary
 *     （父层 copy-on-write 置 [] 且 dirty 派生置位——清空结果可保存），
 *     取消分支=boundary 不变；
 *   - 折线参数面板内容由父层 ReactNode 注入（lineWidth/corridorKind 态
 *     所有权留 SiteplanPane——本组件只挂 Popover 壳不复制状态机）；
 *   - 保存三态（pending/disabled/label 后缀）+错误文本行（409 锁等文案
 *     父层算好传入——本组件零分支渲染）。
 */
import type { ReactNode } from "react";
import { Button, Popconfirm, Popover, Space, Typography } from "antd";

import type { SiteplanTool } from "../store/siteplanStore";

/** 工具组按钮面（value/label——L4a 四值沿承，顺序=工具语义序）。 */
const TOOL_BUTTONS = [
  ["select", "选择/平移"],
  ["road", "道路"],
  ["corridor", "管线走廊"],
  ["boundary", "边界红线"],
] as const;

export function SiteplanToolbar({
  tool,
  onToolChange,
  snapEnabled,
  onToggleSnap,
  showGrid,
  onToggleGrid,
  onResetView,
  linePanelOpen,
  linePanel,
  boundaryEmpty,
  onClearBoundary,
  savePending,
  saveDisabled,
  saveDirty,
  saveError,
  sceneUnavailable,
  onSave,
}: {
  tool: SiteplanTool;
  onToolChange: (tool: SiteplanTool) => void;
  snapEnabled: boolean;
  onToggleSnap: () => void;
  showGrid: boolean;
  onToggleGrid: () => void;
  onResetView: () => void;
  linePanelOpen: boolean;
  linePanel: ReactNode;
  boundaryEmpty: boolean;
  onClearBoundary: () => void;
  savePending: boolean;
  saveDisabled: boolean;
  saveDirty: boolean;
  saveError: string | null;
  sceneUnavailable: boolean;
  onSave: () => void;
}) {
  return (
    <div style={{ padding: "4px 0", borderBottom: "1px solid #434343" }}>
      <Space size="small" wrap>
        {TOOL_BUTTONS.map(([value, label]) => (
          <Button
            key={value}
            size="small"
            type={tool === value ? "primary" : "default"}
            onClick={() => onToolChange(value)}
          >
            {label}
          </Button>
        ))}
        <Button size="small" onClick={onToggleSnap}>
          吸附 {snapEnabled ? "开" : "关"}
        </Button>
        <Button size="small" onClick={onToggleGrid}>
          坐标网 {showGrid ? "开" : "关"}
        </Button>
        <Button size="small" onClick={onResetView}>
          复位视图
        </Button>
        <Popconfirm
          title="清空红线"
          description="确定移除全部边界红线顶点？"
          okText="确认清空"
          cancelText="取消"
          disabled={boundaryEmpty}
          onConfirm={onClearBoundary}
        >
          <Button size="small" danger disabled={boundaryEmpty}>
            清空红线
          </Button>
        </Popconfirm>
        <Popover
          open={linePanelOpen}
          trigger={[]}
          content={linePanel}
          placement="bottomLeft"
        >
          <Button size="small" type={linePanelOpen ? "primary" : "default"}>
            折线参数
          </Button>
        </Popover>
        <Button
          size="small"
          type="primary"
          loading={savePending}
          disabled={saveDisabled}
          onClick={onSave}
        >
          保存布置{saveDirty ? "（有修改）" : ""}
        </Button>
        {sceneUnavailable ? (
          <Typography.Text type="warning" style={{ fontSize: 12 }}>
            场景不可得——足迹按示意矩形显示（未计算）
          </Typography.Text>
        ) : null}
      </Space>
      {saveError !== null ? (
        <div style={{ marginTop: 4 }}>
          <Typography.Text type="danger">{saveError}</Typography.Text>
        </div>
      ) : null}
    </div>
  );
}
