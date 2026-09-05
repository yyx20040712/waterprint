/**
 * SVG 画布显示层常量与纯显示函数（B3 R7 自 SiteCanvas.tsx 模块级外搬）：
 * 显示常量族/交互数据类型/纯显示函数三段——均不落盘（显示层权威面）。
 *
 * 输入:  projectSite 类型面（SitePoint/StructureFootprint）+siteGeometry
 *        measureToNearest（MeasurePair 类型面）+siteplanStore 选中面类型
 * 输出:  显示常量（PX_PER_M/UNCALC_SIZE/坐标网窗/把手半径/双击窗/测距
 *        最近数/滚轮灵敏度/灰阶三色/BOUNDARY_*）+DragSession/
 *        DoubleTapAnchor/MeasurePair 交互类型+pointsAttr/isSelectedLine/
 *        svgOwnsKeyTarget/lineDeleteTarget 纯函数（SiteCanvas 消费——props
 *        面与 handler 族留守组件；键盘删除判定=B4 笔② R2 新增段）
 */
import { measureToNearest } from "./siteGeometry";
import type { SitePoint, StructureFootprint } from "./projectSite";
import type { SiteplanSelection } from "../store/siteplanStore";

// ── 显示层常量（出处：简报 §三交互面/§一.4/自定显示值——均不落盘） ──

/** zoom=1 时每米像素（典型 30m 池体≈240px 的可读基准）。 */
export const PX_PER_M = 8;
/** 未计算示意矩形（固定 w×h 米——简报 §一.1：仅显示层永不落盘）。 */
export const UNCALC_SIZE: StructureFootprint = { w: 12, h: 8 };
/** 坐标网背景世界窗（米——固定窗 MVP；视口自适应挂账）。 */
export const GRID_WORLD_MIN = -100;
export const GRID_WORLD_MAX = 500;
/** 旋转把手北缘外间距/半径（米·世界单位）。 */
export const ROTATE_HANDLE_GAP = 1.6;
export const ROTATE_HANDLE_RADIUS = 0.9;
/** 折线端点把手半径（米·世界单位）。 */
export const ENDPOINT_RADIUS = 0.6;
/** 结构双击判定窗（毫秒——双击移除自实现阈值，见 rect.onPointerDown）。 */
export const DOUBLE_TAP_MS = 500;
/** 结构双击位移容差（像素——超容差=两次单击/拖动非双击）。 */
export const DOUBLE_TAP_SLOP_PX = 5;
/** 测距最近数（简报 §一.4：至多 3 个）。 */
export const MEASURE_COUNT = 3;
/** 滚轮缩放灵敏度（deltaY→指数因子系数）。 */
export const WHEEL_SENSITIVITY = 0.0015;
/** 灰阶三常量（结构描边/结构填充/坐标网）——非彩色语义族（彩色族查
 *  shared/ui/semanticColors.ts 真源表），保留本地。 */
export const COLOR_STRUCTURE = "#3a4552";
export const COLOR_STRUCTURE_FILL = "#1f2933";
export const COLOR_GRID = "#2c2c2c";
/** L4a 边界红线描边宽/虚线节距（boundary 无宽，显示层定值不落盘）。 */
export const BOUNDARY_STROKE = 0.3, BOUNDARY_DASH = "2.5 1";

/** 拖拽会话（pointer capture 期间自持——ref 持有不触发渲染）。 */
export type DragSession =
  | { kind: "pan"; startClientX: number; startClientY: number; startPanX: number; startPanY: number }
  | { kind: "move"; unitId: string; offsetX: number; offsetY: number }
  | { kind: "rotate"; unitId: string };

/** 结构双击判定锚（上次结构 rect pointerdown——dblclick 自实现数据面）。 */
export type DoubleTapAnchor = { time: number; unitId: string; clientX: number; clientY: number };

/** 测距渲染对（几何线+屏幕标注共用——一次配对两处消费）。 */
export type MeasurePair = {
  measure: ReturnType<typeof measureToNearest>[number];
  from: SitePoint; to: SitePoint;
};

/** 折线点列 → SVG points 串（世界米直拼）。 */
export function pointsAttr(points: readonly SitePoint[]): string {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

/** 道路/走廊选中判定（selection 面：kind+index）。 */
export function isSelectedLine(
  selection: SiteplanSelection | null, kind: "road" | "corridor", index: number,
): boolean {
  return selection !== null && selection.kind === kind && selection.index === index;
}

// ── 键盘删除判定（B4 笔② R2——结构化类型消费：node 字面量可测，零 DOM 依赖） ──

/** 焦点判（简报 R2 DS 探针必改④）：event.target 为 svg 本体或其直接子元素
 *  才消费——输入框等表单焦点不消费（SVG DOM tagName 小写/HTML 大写均只判
 *  "svg" 宿主链，表单链天然不中）。 */
export function svgOwnsKeyTarget(target: unknown): boolean {
  if (typeof target !== "object" || target === null) {
    return false;
  }
  const element = target as { tagName?: unknown; parentElement?: unknown };
  if (element.tagName === "svg") {
    return true;
  }
  const parent = element.parentElement;
  return (
    typeof parent === "object" && parent !== null &&
    (parent as { tagName?: unknown }).tagName === "svg"
  );
}

/** select 态 Delete/Backspace 删除目标判定：焦点在画布+选中 road/corridor
 *  时产出删除目标（两路汇同一确认门——侧栏按钮/键盘同回调签名）；否则
 *  null 不消费（structure 选中=双击移除先例面，键盘不删）。 */
export function lineDeleteTarget(
  key: string,
  eventTarget: unknown,
  selection: SiteplanSelection | null,
): { kind: "road" | "corridor"; index: number } | null {
  if (key !== "Delete" && key !== "Backspace") {
    return null;
  }
  if (!svgOwnsKeyTarget(eventTarget)) {
    return null;
  }
  if (selection === null || selection.kind === "structure") {
    return null;
  }
  return { kind: selection.kind, index: selection.index };
}
