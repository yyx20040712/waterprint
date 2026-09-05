/**
 * 纯几何原语层：OBB 角点族/点-边枚举精确净距/点-线段距/线段相交/
 * 点在多边形+OBB 测距（core geometry/spacing+boundary 的 TS 消费面
 * 镜像——SPC2 笔④拆分自 projectSite.ts，批次 3 减压名单提前兑现）。
 *
 * 输入:  摆位（x/y/rotation 度）+足迹（w/h 米）+多边形顶点序（米）
 * 输出:  obbCorners 四角/obbClearance 两 OBB 精确净距/pointSegmentDistance
 *        /segmentsIntersect/pointInPolygon（射线法奇偶+贴边 1e-9 归内）/
 *        measureToNearest（OBB 同式测距——编辑辅助非校核裁判）
 *
 * 规格说明（SPC2 简报 §2.6 D2 采纳，core 同式镜像——Kimi D9.1 记档：
 *   跨语言 IEEE754 三角函数不保证逐位一致，镜像断言容差 1e-9
 *   [相对/绝对取大]，双侧测试注释显式记档；黄金角 0/30/45/90° 解析值）：
 *   - obbCorners：局部 (±w/2,±h/2) 旋转平移——core spacing._obb_corners 同式；
 *   - obbClearance：{A4 顶点×B4 边,B4 顶点×A4 边}32 对点-线段距取 min+
 *     归零判定先行（边对相交或一方全含[任一顶点在对内]→0；线段零长
 *     退化点-点距）——core spacing._clearance 同式（所见即所得：编辑器
 *     测距与 server 校核同净距口径）；
 *   - pointInPolygon：射线法奇偶（水平右向，半开区间防顶点双计）+
 *     两段式先边上判定（点-线段距 ≤ 1e-9=内）；顶点序顺/逆无关+凹
 *     多边形支持；自交不保证（core boundary.py 同记档）；len<3 恒外
 *     （防御面）——红线越界可视化判定面；
 *   - measureToNearest：净距=obbClearance（footprint null 者净距=null
 *     不猜）；序=中心距升序+同距 unitId 字典序；自身排除；
 *   - 零运行期库 import（node 测试直跑）；零 projectSite 依赖（纯几何
 *     面——footprintOfUnit 依赖单元装配面留 projectSite.ts）。
 */

/** 平面点（结构兼容 projectSite.SitePoint——core SitePoint 镜像）。 */
export type Point = { x: number; y: number };

/** 足迹（w/h 米——结构兼容 projectSite.StructureFootprint）。 */
export type Footprint = { w: number; h: number };

/** OBB 形状（摆位+真形足迹——净距原语消费面）。 */
export type ObbShape = { x: number; y: number; rotation: number; w: number; h: number };

/** 测距行（中心距+OBB 净距——null=未计算不猜）。 */
export type StructureMeasure = {
  unitId: string;
  centerDistance: number;
  clearDistance: number | null;
};

/** 测距对象（结构兼容 projectSite.PlacedStructure——footprint 可空）。 */
export type ObbPlacement = {
  unitId: string;
  x: number;
  y: number;
  rotation: number;
  footprint: Footprint | null;
};

/** 贴边归内容差 1e-9（core boundary._EPS 同值——跨语言镜像口径）。 */
const EDGE_TOLERANCE = 1e-9;

/** 摆位+足迹 → OBB 四角（逆时针环；core spacing._obb_corners 同式）。 */
export function obbCorners(
  x: number, y: number, rotation: number, w: number, h: number,
): Point[] {
  const rad = (rotation * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const halfW = w / 2;
  const halfH = h / 2;
  return ([
    [-halfW, -halfH], [halfW, -halfH], [halfW, halfH], [-halfW, halfH],
  ] as const).map(([lx, ly]) => ({
    x: x + lx * cos - ly * sin,
    y: y + lx * sin + ly * cos,
  }));
}

/** 闭合环棱序列（末角→首角补齐——顶点序即权威，消费方补闭合段）。 */
function edgesOf(corners: readonly Point[]): [Point, Point][] {
  return corners.map((corner, index) => [
    corner, corners[(index + 1) % corners.length]!,
  ]);
}

/** 点-线段距（投影参数 clamp [0,1]；零长线段退化点-点距）。 */
export function pointSegmentDistance(
  point: Point, start: Point, end: Point,
): number {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const spanSq = dx * dx + dy * dy;
  if (spanSq === 0) {
    return Math.hypot(point.x - start.x, point.y - start.y);
  }
  const raw = ((point.x - start.x) * dx + (point.y - start.y) * dy) / spanSq;
  const param = raw < 0 ? 0 : raw > 1 ? 1 : raw;
  return Math.hypot(point.x - (start.x + param * dx), point.y - (start.y + param * dy));
}

/** 三点叉积 z 分量（方向判定原语——相交/内含共用）。 */
function cross(origin: Point, first: Point, second: Point): number {
  return (
    (first.x - origin.x) * (second.y - origin.y)
    - (first.y - origin.y) * (second.x - origin.x)
  );
}

/** 两线段相交判定（CLRS 四方向+共线落段——恰触=相交）。 */
export function segmentsIntersect(
  p1: Point, p2: Point, p3: Point, p4: Point,
): boolean {
  const d1 = cross(p3, p4, p1);
  const d2 = cross(p3, p4, p2);
  const d3 = cross(p1, p2, p3);
  const d4 = cross(p1, p2, p4);
  if (
    ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0))
    && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))
  ) {
    return true;
  }
  const between = (edge: [Point, Point], probe: Point): boolean =>
    Math.min(edge[0].x, edge[1].x) <= probe.x
    && probe.x <= Math.max(edge[0].x, edge[1].x)
    && Math.min(edge[0].y, edge[1].y) <= probe.y
    && probe.y <= Math.max(edge[0].y, edge[1].y);
  return (
    (d1 === 0 && between([p3, p4], p1))
    || (d2 === 0 && between([p3, p4], p2))
    || (d3 === 0 && between([p1, p2], p3))
    || (d4 === 0 && between([p1, p2], p4))
  );
}

/** 点在凸四边形内（含边上——叉积同号；core spacing._point_in_box 同式）。 */
function pointInBox(point: Point, corners: readonly Point[]): boolean {
  const signs: boolean[] = [];
  for (const [start, end] of edgesOf(corners)) {
    const turn = (end.x - start.x) * (point.y - start.y)
      - (end.y - start.y) * (point.x - start.x);
    if (turn > 0) {
      signs.push(true);
    } else if (turn < 0) {
      signs.push(false);
    }
  }
  return !(signs.includes(true) && signs.includes(false));
}

/** 两 OBB 精确净距（core spacing._clearance 同式——归零判定先行+32 对枚举 min）。 */
export function obbClearance(a: ObbShape, b: ObbShape): number {
  const cornersA = obbCorners(a.x, a.y, a.rotation, a.w, a.h);
  const cornersB = obbCorners(b.x, b.y, b.rotation, b.w, b.h);
  const touching = edgesOf(cornersA).some((edgeA) =>
    edgesOf(cornersB).some((edgeB) =>
      segmentsIntersect(edgeA[0], edgeA[1], edgeB[0], edgeB[1]),
    ),
  ) || cornersA.some((point) => pointInBox(point, cornersB))
    || cornersB.some((point) => pointInBox(point, cornersA));
  if (touching) {
    return 0;
  }
  let best = Infinity;
  for (const [corners, other] of [[cornersA, cornersB], [cornersB, cornersA]] as const) {
    const otherEdges = edgesOf(other);
    for (const point of corners) {
      for (const [start, end] of otherEdges) {
        const distance = pointSegmentDistance(point, start, end);
        if (distance < best) {
          best = distance;
        }
      }
    }
  }
  return best;
}

/** 点在多边形内（含边上容差 1e-9——射线法奇偶+两段式；core boundary 同式）。 */
export function pointInPolygon(point: Point, vertices: readonly Point[]): boolean {
  if (vertices.length < 3) {
    return false; // 未划界/退化恒外（防御面——core boundary R3 同构）
  }
  const edges = edgesOf(vertices);
  for (const [start, end] of edges) {
    if (pointSegmentDistance(point, start, end) <= EDGE_TOLERANCE) {
      return true; // 贴边=内（半开区间顶点双计由此前置归内消解）
    }
  }
  let inside = false;
  for (const [start, end] of edges) {
    if ((start.y > point.y) !== (end.y > point.y)) {
      const crossingX = start.x
        + ((point.y - start.y) / (end.y - start.y)) * (end.x - start.x);
      if (crossingX > point.x) {
        inside = !inside;
      }
    }
  }
  return inside;
}

/** 测距：至最近 count 个{中心距,OBB 净距}——中心距升序+同距字典序。 */
export function measureToNearest(
  target: ObbPlacement,
  others: readonly ObbPlacement[],
  count: number,
): StructureMeasure[] {
  if (count <= 0) {
    return [];
  }
  const rows: StructureMeasure[] = [];
  for (const other of others) {
    if (other.unitId === target.unitId) {
      continue; // 自身排除（防御面——调用方常含全集）
    }
    const dx = other.x - target.x;
    const dy = other.y - target.y;
    const centerDistance = Math.hypot(dx, dy);
    let clearDistance: number | null = null;
    if (target.footprint !== null && other.footprint !== null) {
      clearDistance = obbClearance(
        {
          x: target.x, y: target.y, rotation: target.rotation,
          w: target.footprint.w, h: target.footprint.h,
        },
        {
          x: other.x, y: other.y, rotation: other.rotation,
          w: other.footprint.w, h: other.footprint.h,
        },
      );
    }
    rows.push({ unitId: other.unitId, centerDistance, clearDistance });
  }
  rows.sort((a, b) =>
    a.centerDistance !== b.centerDistance
      ? a.centerDistance - b.centerDistance
      : a.unitId < b.unitId
        ? -1
        : 1,
  );
  return rows.slice(0, count);
}
