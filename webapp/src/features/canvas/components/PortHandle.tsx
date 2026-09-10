/**
 * 类型化端口渲染件：方向→Position 映射+域色 Handle 封装。
 *
 * 输入:  portId（Handle 唯一键=design.edges 端点 port_id）+方向
 *        （target=左入/source=右出——投影层边端点方向聚合）
 *        +domainColor?（节点域色——C2-canvas P8 端口流体色）
 * 输出:  React Flow Handle（只读渲染——isConnectable 关闭连线交互）
 *
 * 规格说明（FE4 批 6b 段一 D1；C2-canvas 批 P8 流体色兑现）：
 *   - 端口表不在项目文件（端口声明只在 core manifest——TS 侧零业务复制
 *     红线不可破），本渲染件只按端点方向呈现：target=Position.Left/
 *     source=Position.Right；
 *   - FE4 挂账④「端口流体色（水蓝/泥棕）」本批兑现：默认灰阶中性色
 *     保持（未传域色=中性兼容面）；domainColor 传入时描边随域
 *     （填充恒底色深蓝——工程图例端口惯例：描边承语义、填充承底）；
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

/** 灰阶中性色（未传域色回退——§19.3 非语义承载）。 */
const NEUTRAL_BORDER = "#595959";

export function PortHandle({
  portId,
  direction,
  domainColor,
}: {
  portId: string;
  direction: "source" | "target";
  /** 节点域色（可选——缺省灰阶中性；视觉稿端口=描边承域语义）。 */
  domainColor?: string;
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
        background: "var(--wp-bg-page)",
        border: `1.5px solid ${domainColor ?? NEUTRAL_BORDER}`,
        borderRadius: "50%",
      }}
    />
  );
}
