/**
 * 类型化端口渲染件：方向→Position 映射+灰阶中性色 Handle 封装。
 *
 * 输入:  portId（Handle 唯一键=design.edges 端点 port_id）+ 方向
 *        （target=左入/source=右出——投影层边端点方向聚合）
 * 输出:  React Flow Handle（只读渲染——isConnectable 关闭连线交互）
 *
 * 规格说明（FE4 批 6b 段一，D1 方向中性裁决）：
 *   - 端口表不在项目文件（端口声明只在 core manifest——TS 侧零业务复制
 *     红线不可破），本渲染件只按端点方向呈现：target=Position.Left/
 *     source=Position.Right；
 *   - 灰阶中性色（§19.3「语义色之外禁彩色」）——流体色（水蓝/泥棕）
 *     与端口表挂账段二（届时 server 单元清单端点另批立项）；
 *   - 只读批无连线交互：isConnectable=false（编辑面挂账段二——
 *     useConnectionRules 维持骨架契约头）；
 *   - 微型圆点+描边（工程图例端口惯例）；title 提示=port_id（一级信息
 *     悬停可见，§19.3 不下钻）。
 */
import { Handle, Position } from "@xyflow/react";

/** 方向→方位映射（D1：src=Right/target=Left——流向左进右出工程图惯例）。 */
const DIRECTION_POSITION = {
  source: Position.Right,
  target: Position.Left,
} as const;

/** 灰阶中性色（§19.3 非语义承载——蓝/棕语义色挂账段二）。 */
const NEUTRAL_FILL = "#8c8c8c";
const NEUTRAL_BORDER = "#595959";

export function PortHandle({
  portId,
  direction,
}: {
  portId: string;
  direction: "source" | "target";
}) {
  return (
    <Handle
      id={portId}
      type={direction}
      position={DIRECTION_POSITION[direction]}
      isConnectable={false}
      title={portId}
      style={{
        width: 8,
        height: 8,
        background: NEUTRAL_FILL,
        border: `1.5px solid ${NEUTRAL_BORDER}`,
        borderRadius: "50%",
      }}
    />
  );
}
