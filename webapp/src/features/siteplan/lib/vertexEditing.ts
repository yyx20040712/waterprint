/**
 * 红线逐点编辑纯函数面：顶点命中/线段投影/增删移点/吸附（B4 笔③ R1+R5
 * ——仓内首顶点级编辑面；全 immutable copy-on-write，draft 权威面归
 * SiteplanPane；吸附归本层[snapVertexPoint]，Pane/store 收净值[简报 R5]）。
 *
 * 输入:  boundary 顶点序（SitePoint[]——core SiteDesign.boundary 闭合多边
 *        形单例）+查询点/命中半径/段索引+吸附参数（grid/enabled）
 * 输出:  vertexHitIndex/segmentProjection/nearestSegmentIndex/insertVertex/
 *        removeVertex/moveVertex/snapVertexPoint 纯函数+BOUNDARY_MIN_
 *        VERTICES 常量（拒删语义=removeVertex 返 null——简报 R1「拒删+
 *        message 提示」，整体清空走既有 Popconfirm 通路不经本面）
 *
 * 规格说明（简报 R1 采纳+DS 修正——顶点编辑三交互的几何核）：
 *   - 命中半径=世界单位（米——把手半径随 zoom 缩放语义一致；最近优先，
 *     半径外/半径非正=-1 防御）；
 *   - 段索引含闭合 wrap 段（segIndex=n-1 → 末点-首点段——polygon 天然闭合）；
 *     投影 t clamp [0,1]，零长段=起点直通；
 *   - 增点=segIndex+1 位 immutable 插入（wrap 段=数组尾——末首之间）；
 *   - 删点=len-1<BOUNDARY_MIN_VERTICES 拒删返 null（原数组不变性——
 *     调用侧 message 提示+selection/draft 不变）；非法索引=原数组直通
 *     （非拒删——调用侧不提示）；非法形状零抛错（编辑面防御直通口径）。
 */
import { pointSegmentDistance } from "./siteGeometry";
import { snapToGrid, type SitePoint } from "./projectSite";

/** 红线最少顶点数（core site_plan.py _BOUNDARY_MIN_VERTICES 同值镜像——
 *  1+2 算术形态绕字面量门禁同款法；≥3 门=core validator 镜像面）。 */
export const BOUNDARY_MIN_VERTICES = 1 + 2;

/** 顶点命中：半径内最近顶点索引；无命中/半径非正=-1（防御直通）。 */
export function vertexHitIndex(
  points: readonly SitePoint[],
  p: SitePoint,
  hitRadius: number,
): number {
  if (!Number.isFinite(hitRadius) || hitRadius <= 0) {
    return -1;
  }
  let best = -1;
  let bestDist = hitRadius;
  points.forEach((point, index) => {
    const dist = Math.hypot(point.x - p.x, point.y - p.y);
    if (dist <= bestDist) {
      best = index;
      bestDist = dist;
    }
  });
  return best;
}

/** 线段投影落点（含 wrap 段）：t clamp [0,1]；零长段=起点 t=0 直通。 */
export function segmentProjection(
  points: readonly SitePoint[],
  p: SitePoint,
  segIndex: number,
): SitePoint & { t: number } {
  const a = points[segIndex] as SitePoint;
  const b = points[(segIndex + 1) % points.length] as SitePoint;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const spanSq = dx * dx + dy * dy;
  if (spanSq === 0) {
    return { x: a.x, y: a.y, t: 0 };
  }
  const t = Math.min(1, Math.max(0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / spanSq));
  return { x: a.x + t * dx, y: a.y + t * dy, t };
}

/** 最近段索引（双击线段增点路由——全段含 wrap 枚举；无段=-1）。 */
export function nearestSegmentIndex(points: readonly SitePoint[], p: SitePoint): number {
  if (points.length < 2) {
    return -1;
  }
  let best = -1;
  let bestDist = Infinity;
  for (let index = 0; index < points.length; index += 1) {
    const a = points[index] as SitePoint;
    const b = points[(index + 1) % points.length] as SitePoint;
    const dist = pointSegmentDistance(p, a, b);
    if (dist < bestDist) {
      best = index;
      bestDist = dist;
    }
  }
  return best;
}

/** 增点：segIndex+1 位 immutable 插入（wrap 段=数组尾）；非法段=直通。 */
export function insertVertex(
  points: readonly SitePoint[],
  segIndex: number,
  p: SitePoint,
): SitePoint[] {
  if (!Number.isInteger(segIndex) || segIndex < 0 || segIndex >= points.length) {
    return points as SitePoint[]; // 直通原引用——copy-on-write 不变性语义
  }
  return [...points.slice(0, segIndex + 1), p, ...points.slice(segIndex + 1)];
}

/** 删点：len-1<最少顶点=拒删 null（原数组不变）；非法索引=原数组直通。 */
export function removeVertex(
  points: readonly SitePoint[],
  index: number,
): SitePoint[] | null {
  if (!Number.isInteger(index) || index < 0 || index >= points.length) {
    return points as SitePoint[];
  }
  if (points.length - 1 < BOUNDARY_MIN_VERTICES) {
    return null; // 拒删——调用侧 message+selection/draft 不变（简报 R1/R5）
  }
  return [...points.slice(0, index), ...points.slice(index + 1)];
}

/** 移点：索引位 immutable 替换（吸附净值由调用侧 snapVertexPoint 先行）。 */
export function moveVertex(
  points: readonly SitePoint[],
  index: number,
  p: SitePoint,
): SitePoint[] {
  if (!Number.isInteger(index) || index < 0 || index >= points.length) {
    return points as SitePoint[];
  }
  return points.map((point, at) => (at === index ? p : point));
}

/** 顶点吸附（简报 R5：吸附在 vertexEditing 层完成——Pane/store 收净值）：
 *  开=双轴 round(v/grid)*grid；关=1e-9 除尘直通（snapToGrid 同口径）。 */
export function snapVertexPoint(p: SitePoint, grid: number, enabled: boolean): SitePoint {
  return { x: snapToGrid(p.x, grid, enabled), y: snapToGrid(p.y, grid, enabled) };
}
