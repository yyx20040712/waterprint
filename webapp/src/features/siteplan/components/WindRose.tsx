/**
 * 风玫瑰画布角标：屏幕空间 SVG overlay（B4 笔① R3——仅渲染批：值编辑
 * 面板挂账，README「风玫瑰值编辑面板」续记）。
 *
 * 输入:  windRose（design.site.options.wind_rose——null/空/全零=不渲染）
 * 输出:  嵌套 svg 屏幕空间子树（右上角：辐条族+八方位标注）或 null
 *
 * 规格说明（简报 R3——数据计算镜像 core site_plan.py:288-323，落位=webapp
 *   屏幕角标语义[DS 新发现①：数据镜像/落位语义两分离]）：
 *   - 嵌套 svg x="100%" y=0 锚定宿主画布右缘+overflow="visible" 内容左伸
 *     ——零测量零视口态（屏幕空间层天然不随 pan/zoom；挂 SiteCanvas svg
 *     根级 g transform 之外）；
 *   - Y 翻转已在 windRoseSpokes 计算面完成（dy 负=屏幕向上），本件零再
 *     翻转；标注=屏幕层正向文字天然不倒（简报 R3 Y 翻转条款配套）；
 *   - pointerEvents="none" 装饰面不拦截画布交互；windRoseSpokes 空族
 *     （None/空/全零/半径非法）=返回 null（core 不画口径）；
 *   - 本件零 hook 纯展示——node 直调元素树断言可测（零 jsdom 红线内，
 *     WindRose.test.tsx 同形态首例）。
 */
import { windRoseSpokes } from "../lib/windRoseGeometry";

/** 角标基准半径（像素·屏幕空间——显示层定值不落盘；典型可读尺寸，
 *  B 面探针可点性/落位核对后可微调）。 */
export const WIND_ROSE_RADIUS = 44;
/** 距画布右/上缘边距（像素——含标注文字外伸余量：标注落基准半径处，
 *  textAnchor=middle 水平半宽内收）。 */
export const WIND_ROSE_MARGIN = 18;
/** 角标色（沿 SiteCanvas 屏幕标注层字色 #c3ccd6——同层同族不另设色）。 */
const WIND_ROSE_COLOR = "#c3ccd6";
/** 标注字号（沿 SiteCanvas 屏幕标注层 fontSize=11 同值）。 */
const WIND_ROSE_FONT_SIZE = 11;

export type WindRoseProps = {
  windRose: Record<string, number> | null;
};

export function WindRose({ windRose }: WindRoseProps) {
  const spokes = windRoseSpokes(windRose, WIND_ROSE_RADIUS);
  if (spokes.length === 0) {
    return null; // None/空/全零=不画（core _wind_rose_entities 同口径）
  }
  // 嵌套 svg 锚右缘：内部坐标系原点=画布右上角——中心负 X 内收
  const cx = -(WIND_ROSE_MARGIN + WIND_ROSE_RADIUS);
  const cy = WIND_ROSE_MARGIN + WIND_ROSE_RADIUS;
  return (
    <svg x="100%" y={0} width={0} height={0} overflow="visible" pointerEvents="none">
      {spokes.map((spoke) => (
        <line
          key={`wind-rose-spoke-${spoke.dir}`}
          x1={cx}
          y1={cy}
          x2={cx + spoke.dx}
          y2={cy + spoke.dy}
          stroke={WIND_ROSE_COLOR}
          strokeWidth={1}
        />
      ))}
      {spokes.map((spoke) => (
        <text
          key={`wind-rose-label-${spoke.dir}`}
          x={cx + spoke.labelDx}
          y={cy + spoke.labelDy}
          fontSize={WIND_ROSE_FONT_SIZE}
          fill={WIND_ROSE_COLOR}
          textAnchor="middle"
          dominantBaseline="central"
        >
          {spoke.dir}
        </text>
      ))}
    </svg>
  );
}
