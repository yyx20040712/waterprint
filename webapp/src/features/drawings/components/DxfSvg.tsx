/**
 * DXF 线稿渲染薄壳：SvgScene 模型 → SVG 元素树（零 antd/零运行期库
 * ——类型 import 自 lib/dxfScene；B 批 D8）。
 *
 * 输入:  SvgScene（projectDxf 产物——DrawingPreview 消费面喂入）
 * 输出:  <svg viewBox="0 0 w h" preserveAspectRatio="xMidYMid meet">
 *        +items 逐类映射（path→stroke 折线/text→系统字体文字/solid→
 *        fill 多边形）；viewBox 缩放=容器自适应（drawingsStore 缩放
 *        面挂账不启用——v1 自适应即足）
 *
 * 规格说明（B 批 D8）：
 *   - path→<path fill="none" stroke={color} stroke-width=1>（v1 线型恒
 *     实线——dxf-parser 线型表 DASHED 缺失=解析器局限，诚实注记在
 *     DrawingPreview 引导文案不遮蔽）；
 *   - text→<text fontSize fill="#303030">（中文走系统字体——零字体
 *     下载；fontSize 已在投影层按图幅可读性放大）；
 *   - solid→<polygon fill={color}>（尺寸线箭头填充面）；
 *   - 薄壳不测（投影层 dxfScene.test 承担契约面——组件薄壳先例）；
 *   - 显示层常量（线宽/文字色/铺满样式）集中本文件顶部。
 */
import type { SvgItem, SvgScene } from "../lib/dxfScene";

/** 折线线宽（显示层常量——viewBox 单位下恒细线）。 */
const STROKE_WIDTH = 1;

/** 文字色（显示层常量——ACI 7 深灰同款，浅底可读）。 */
const TEXT_FILL = "#303030";

/** 单图元映射（kind 三类穷尽——默认分支=不可达防御）。 */
function renderItem(item: SvgItem, key: number) {
  if (item.kind === "path") {
    return (
      <path
        key={key}
        d={item.d}
        fill="none"
        stroke={item.color}
        strokeWidth={STROKE_WIDTH}
      />
    );
  }
  if (item.kind === "text") {
    return (
      <text key={key} x={item.x} y={item.y} fontSize={item.fontSize} fill={TEXT_FILL}>
        {item.text}
      </text>
    );
  }
  return <polygon key={key} points={item.points} fill={item.color} />;
}

/** 线稿渲染薄壳（SvgScene→SVG——容器内铺满自适应）。 */
export function DxfSvg({ scene }: { scene: SvgScene }) {
  return (
    <svg
      viewBox={`0 0 ${scene.width} ${scene.height}`}
      preserveAspectRatio="xMidYMid meet"
      style={{ width: "100%", height: "100%", display: "block" }}
    >
      {scene.items.map(renderItem)}
    </svg>
  );
}
