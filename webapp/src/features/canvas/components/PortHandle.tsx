/**
 * 类型化端口渲染件：方向→Position 映射+域色 Handle 封装。
 *
 * 输入:  portId（Handle 唯一键=design.edges 端点 port_id）+方向
 *        （target=左入/source=右出——投影层边端点方向聚合）+domainColor?
 *        （节点域色——C2-canvas P8 端口流体色）+connectable?（P0-3 编辑
 *        态连线交互开关——缺省 false 只读沿袭）
 * 输出:  React Flow Handle（只读渲染/编辑态连线起点终点）
 *
 * 规格说明（FE4 批 6b 段一 D1；C2-canvas 批 P8 流体色兑现；P0-3）：
 *   - 端口表不在项目文件（端口声明只在 core manifest——TS 侧零业务复制
 *     红线不可破），本渲染件只按端点方向呈现：target=Position.Left/
 *     source=Position.Right；
 *   - FE4 挂账④「端口流体色（水蓝/泥棕）」C2-canvas 兑现：默认灰阶中性色
 *     保持（未传域色=中性兼容面）；domainColor 传入时描边随域
 *     （填充恒底色深蓝——工程图例端口惯例：描边承语义、填充承底）；
 *   - P0-3（task-c2-edit-plan）：编辑态 isConnectable=connectable 透传
 *     （useConnectionRules 即时规则求值不做——红线④：规则判断唯一源
 *     =校验时点 core validate_design_structure）；只读批 false 沿袭；
 *   - 微型圆点+描边（工程图例端口惯例）；title 提示=port_id（一级信息
 *     悬停可见，§19.3 不下钻）。
 */
import { Handle, Position } from "@xyflow/react";

/** 方向→方位映射（D1：src=Right/target=Left——流向左进右出工程图惯例）。 */
const DIRECTION_POSITION = {
  source: Position.Right,
  target: Position.Left,
} as const;

/** 灰阶中性色（未传域色回退——§19.3 非语义承载）。 */
const NEUTRAL_BORDER = "#595959";

export function PortHandle({
  portId,
  direction,
  domainColor,
  connectable = false,
}: {
  portId: string;
  direction: "source" | "target";
  /** 节点域色（可选——缺省灰阶中性；视觉稿端口=描边承域语义）。 */
  domainColor?: string;
  /** P0-3 编辑态连线开关（缺省 false=只读批零回归）。 */
  connectable?: boolean;
}) {
  return (
    <Handle
      id={portId}
      type={direction}
      position={DIRECTION_POSITION[direction]}
      isConnectable={connectable}
      title={portId}
      style={{
        width: 8,
        height: 8,
        background: "var(--wp-bg-page)",
        border: `1.5px solid ${domainColor ?? NEUTRAL_BORDER}`,
        borderRadius: "50%",
      }}
    />
  );
}
