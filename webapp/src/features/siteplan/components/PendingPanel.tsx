/**
 * 待摆区：design.nodes 有而 site.structures 无的单元列表（拖入画布即摆放）。
 *
 * 输入:  pendingUnitIds（projectSite 产物——字典序）+已摆数（提示面）
 * 输出:  可拖单元清单（原生 DnD：dataTransfer 携 unit_id——落点换算与
 *        snap 归 SiteCanvas onDrop；零 antd 拖拽库）
 *
 * 规格说明（M3 批 L2b，简报 §三交互面）：
 *   - unit_id 直用（core D3 悬空校验镜像面：摆入=structures 增键、移除
 *     =删键——键集与 design.nodes 恒一致由编辑流保证）；
 *   - 双击移除在画布侧（本面板零按钮——单一交互入口不重复）；
 *   - 列表空态=「全部已摆」提示；面板宽度=显示层常量。
 */
import { Typography } from "antd";

/** 面板宽度（像素——显示层常量：canvasPane 侧栏 320 级的窄列版）。 */
const PANEL_WIDTH = 180;

/** 拖拽项样式（显示层常量——暗底描边卡片）。 */
const ITEM_STYLE: React.CSSProperties = {
  margin: "4px 0",
  padding: "2px 8px",
  border: "1px solid #434343",
  borderRadius: 4,
  fontFamily: "monospace",
  fontSize: 12,
  cursor: "grab",
  userSelect: "none",
};

export function PendingPanel({
  pendingUnitIds,
  placedCount,
}: {
  pendingUnitIds: string[];
  placedCount: number;
}) {
  return (
    <aside
      style={{
        width: PANEL_WIDTH,
        flexShrink: 0,
        padding: "0 8px",
        borderRight: "1px solid #434343",
        overflowY: "auto",
      }}
    >
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        待摆单元 {pendingUnitIds.length} · 已摆 {placedCount}（拖入画布摆放）
      </Typography.Text>
      {pendingUnitIds.map((unitId) => (
        <div
          key={unitId}
          draggable
          onDragStart={(event) => {
            event.dataTransfer.setData("text/plain", unitId);
            event.dataTransfer.effectAllowed = "copy";
          }}
          style={ITEM_STYLE}
        >
          {unitId}
        </div>
      ))}
      {pendingUnitIds.length === 0 ? (
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          design.nodes 单元全部已摆
        </Typography.Text>
      ) : null}
    </aside>
  );
}
