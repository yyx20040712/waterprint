/**
 * 选中折线/红线删除侧栏纯展示子件（B4 笔② R2——ENG6 SiteplanToolbar/
 * StructureSidebar 拆出先例第三例；行预算门禁 500 硬顶拆文件出路；B4 笔③
 * 泛化 boundary 面——红线删除=清空通路[简报 R2 必改②收口语义]；M3 批 D1
 * 增管网定线挂起位载体注记[mapping-2b4 §A M3 行「红线/走廊折线=管网挂起
 * 位载体」]）。
 *
 * 输入:  selection（RemovableSelection——road/corridor 索引身份/boundary
 *        单例无索引）+removeOpen（确认门开态=父层 removeRequest 挂起）+
 *        onRequest/onConfirmRemove/onCancelRemove（三回调——态所有权留
 *        SiteplanPane）
 * 输出:  aside 侧栏 JSX（danger 按钮+Popconfirm 确认门+提示行——零业务推导）
 *
 * 规格说明（简报 R2——侧栏按钮为主、Delete 键为辅，两路汇同一确认门）：
 *   - Popconfirm open 受控：按钮点击经 onRequest 上行置挂起态开；画布
 *      Delete/Backspace 键上行同一挂起态=本门同开（回调签名汇合面）；
 *   - 确认=onConfirmRemove（父层 immutable splice/清空+setSelection(null)
 *     收口）；取消/外部点击/Esc=onCancelRemove 零动作（简报取消路径条款）；
 *   - 仓内无 undo——删除必经本门（双击移除先例仅限结构 rect 不泛化）。
 *   - M3 批 D1（载体注记——挂起展示不实现[v3 B-3 逐字口径]）：选中
 *      corridor/boundary=载体块在场（「管网定线预留」Tag[style 沿树徽标
 *      同形]+共用一份说明行——mapping「红线/走廊折线」并列表述不分案）；
 *      road 非管线载体不渲染——条件=正向白名单 corridor|boundary
 *      [M3 回炉 R1 fail-closed：RemovableSelection 扩值不静默渲染载体]；
 *      纯展示零业务推导。
 */
import { Button, Popconfirm, Tag, Typography } from "antd";

import type { RemovableSelection } from "../store/siteplanStore";

/** 折线删除侧栏宽度（像素——显示层定值，比结构侧栏 220 略窄）。 */
const LINE_SIDE_WIDTH = 200;

export type LineSidebarProps = {
  selection: RemovableSelection;
  removeOpen: boolean;
  onRequest: (target: RemovableSelection) => void;
  onConfirmRemove: () => void;
  onCancelRemove: () => void;
};

export function LineSidebar({
  selection, removeOpen, onRequest, onConfirmRemove, onCancelRemove,
}: LineSidebarProps) {
  const label =
    selection.kind === "boundary" ? "边界红线" : selection.kind === "road" ? "道路" : "管线走廊";
  const boundary = selection.kind === "boundary"; // 红线删除=清空通路（同工具栏文案族）
  return (
    <aside
      style={{ width: LINE_SIDE_WIDTH, flexShrink: 0, padding: "8px 12px", borderLeft: "1px solid var(--wp-border-2)" }}
    >
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {boundary ? "选中边界红线（单例）" : `选中${label} #${selection.index + 1}`}
      </Typography.Text>
      {selection.kind === "corridor" || selection.kind === "boundary" ? (
        <div data-testid="wp-pending-network-carrier" style={{ marginTop: 8 }}>
          <Tag style={{ fontSize: 11, lineHeight: "16px" }}>管网定线预留</Tag>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            管网定线将挂起于红线/管线走廊折线——定线·水力计算·平纵图纸随后续管网批（挂起展示，不实现）
          </Typography.Text>
        </div>
      ) : null}
      <div style={{ marginTop: 8 }}>
        <Popconfirm
          title={boundary ? "清空红线" : `删除${label}`}
          description={boundary ? "确定移除全部边界红线顶点？" : "确定删除选中折线？（无撤销——删除须确认）"}
          okText={boundary ? "确认清空" : "确认删除"}
          cancelText="取消"
          open={removeOpen}
          onConfirm={onConfirmRemove}
          onCancel={onCancelRemove}
          onOpenChange={(nextOpen) => {
            if (!nextOpen) {
              onCancelRemove(); // 外部点击/Esc 关闭=取消路径零动作
            }
          }}
        >
          <Button size="small" danger onClick={() => onRequest(selection)}>
            {boundary ? "清空选中红线" : `删除选中${selection.kind === "road" ? "道路" : "走廊"}`}
          </Button>
        </Popconfirm>
      </div>
      <div style={{ marginTop: 10, fontSize: 12, color: "#8c8c8c" }}>
        画布聚焦按 Delete/Backspace 同效（汇同一确认门）；取消=零动作。
      </div>
    </aside>
  );
}
