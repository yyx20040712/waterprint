/**
 * SVG 画布薄壳：布置渲染+pointer 交互（几何全经 lib——组件零业务推导）。
 *
 * 输入:  model（projectSite 产物）+draft（SiteDesignShape 本地编辑态——
 *        摆放/道路/走廊权威面）+编辑回调（onPlace/onMove/onRotate/onRemove/
 *        onCommitLine）；view 态自 siteplanStore 直读
 * 输出:  SVG 工作区（坐标网背景+构筑物足迹矩形+旋转把手+道路/走廊折线+
 *        绘制中折线+测距层；拖放/拖拽/滚轮缩放/背景平移/双击移除）
 *
 * 规格说明（M3 批 L2b，简报 §三交互面——详面见本 feature README；DxfSvg
 *   原生 SVG 先例零 antd/零运行期库）：
 *   - 世界坐标（米，X 东 Y 北）经 g transform="translate(pan) scale(k -k)"
 *     映射屏幕（Y 翻转=北向上）；k=zoom*PX_PER_M；文本标注走屏幕空间层
 *     （fontSize 恒定可读——不随 zoom 缩放）；
 *   - 足迹 null=未计算示意矩形（UNCALC_SIZE 显示层常量——尺寸永不进
 *     draft/落盘，R3 红线）；rotation=transform rotate（世界逆时针）；
 *   - 交互=pointer 事件自实现：拖放落点/拖拽移动/把手旋转（90° 吸附默认
 *     +Shift 自由角）/背景拖拽平移/滚轮缩放（非被动监听 preventDefault）/
 *     绘制模式点击加点+双击收笔（先弹重复点再 ≥2 前置）+Enter 收笔+Esc
 *     取消；所有落点经 snapToGrid（coord_grid 网点吸附）；折线宽度=
 *     strokeWidth（米·世界单位——随 zoom 缩放即「双线示意」）；
 *   - 测距层：选中结构 → measureToNearest(…, MEASURE_COUNT) 虚线+双值
 *     标注（编辑辅助非校核裁判——L4 面零实现零占位）；
 *   - 双击已摆结构=移除回待摆区（onRemove——pointerdown 时间/位移自实现：
 *     capture 重定向致原生 dblclick 落 svg 不可达）；道路/走廊点击=选中（索引
 *     身份面——折线端点视觉即把手）。
 */
import { useCallback, useEffect, useMemo, useRef } from "react";

import {
  measureToNearest,
  snapRotation,
  snapToGrid,
  type PlacedStructure,
  type SiteDesignShape,
  type SiteModel,
  type SitePoint,
  type StructureFootprint,
} from "../lib/projectSite";
import { useSiteplanStore, type SiteplanSelection } from "../store/siteplanStore";

// ── 显示层常量（出处：简报 §三交互面/§一.4/自定显示值——均不落盘） ──

/** zoom=1 时每米像素（典型 30m 池体≈240px 的可读基准）。 */
const PX_PER_M = 8;
/** 未计算示意矩形（固定 w×h 米——简报 §一.1：仅显示层永不落盘）。 */
const UNCALC_SIZE: StructureFootprint = { w: 12, h: 8 };
/** 坐标网背景世界窗（米——固定窗 MVP；视口自适应挂账）。 */
const GRID_WORLD_MIN = -100;
const GRID_WORLD_MAX = 500;
/** 旋转把手北缘外间距/半径（米·世界单位）。 */
const ROTATE_HANDLE_GAP = 1.6;
const ROTATE_HANDLE_RADIUS = 0.9;
/** 折线端点把手半径（米·世界单位）。 */
const ENDPOINT_RADIUS = 0.6;
/** 结构双击判定窗（毫秒——双击移除自实现阈值，见 rect.onPointerDown）。 */
const DOUBLE_TAP_MS = 500;
/** 结构双击位移容差（像素——超容差=两次单击/拖动非双击）。 */
const DOUBLE_TAP_SLOP_PX = 5;
/** 测距最近数（简报 §一.4：至多 3 个）。 */
const MEASURE_COUNT = 3;
/** 滚轮缩放灵敏度（deltaY→指数因子系数）。 */
const WHEEL_SENSITIVITY = 0.0015;
/** 选中蓝=AssumptionsPanel SELECT_BLUE 同款；走廊 kind 开放 str（GR-21）
 *  ——色映射=展示层非语义复制（≥4 类+默认）。 */
const COLOR_SELECTED = "#1668dc";
const COLOR_STRUCTURE = "#3a4552";
const COLOR_STRUCTURE_FILL = "#1f2933";
const COLOR_ROAD = "#6b6f76";
const COLOR_PENDING = "#d48806";
const COLOR_MEASURE = "#2f7fd1";
const COLOR_GRID = "#2c2c2c";
const CORRIDOR_COLORS: Record<string, string> = {
  water: "#2f7fd1",
  power: "#f2a93b",
  gas: "#3fa34d",
  comm: "#9a6dd7",
};
const CORRIDOR_DEFAULT_COLOR = "#8c8c8c";

/** 拖拽会话（pointer capture 期间自持——ref 持有不触发渲染）。 */
type DragSession =
  | { kind: "pan"; startClientX: number; startClientY: number; startPanX: number; startPanY: number }
  | { kind: "move"; unitId: string; offsetX: number; offsetY: number }
  | { kind: "rotate"; unitId: string };

/** 结构双击判定锚（上次结构 rect pointerdown——dblclick 自实现数据面）。 */
type DoubleTapAnchor = { time: number; unitId: string; clientX: number; clientY: number };

/** 测距渲染对（几何线+屏幕标注共用——一次配对两处消费）。 */
type MeasurePair = {
  measure: ReturnType<typeof measureToNearest>[number];
  from: SitePoint;
  to: SitePoint;
};

export type SiteCanvasProps = {
  model: SiteModel;
  draft: SiteDesignShape;
  onPlace: (unitId: string, x: number, y: number) => void;
  onMove: (unitId: string, x: number, y: number) => void;
  onRotate: (unitId: string, rotation: number) => void;
  onRemove: (unitId: string) => void;
  onCommitLine: (points: SitePoint[]) => void;
};

/** 折线点列 → SVG points 串（世界米直拼）。 */
function pointsAttr(points: readonly SitePoint[]): string {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

/** 道路/走廊选中判定（selection 面：kind+index）。 */
function isSelectedLine(
  selection: SiteplanSelection | null,
  kind: "road" | "corridor",
  index: number,
): boolean {
  return selection !== null && selection.kind === kind && selection.index === index;
}

export function SiteCanvas({
  model,
  draft,
  onPlace,
  onMove,
  onRotate,
  onRemove,
  onCommitLine,
}: SiteCanvasProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const dragRef = useRef<DragSession | null>(null);
  const doubleTapRef = useRef<DoubleTapAnchor | null>(null); // 双击判定锚（仅结构 rect select 分支记）
  // 单订阅解构（MVP 面板级全订阅——零 selector 微优化；actions 引用稳定）
  const {
    pan, zoom, snapEnabled, showGrid, tool, selection, pendingPoints,
    setPan, zoomBy, setSelection, appendPending, popPending, discardPending,
  } = useSiteplanStore();

  const gridSpacing = draft.options.coord_grid;
  const snap = useCallback(
    (value: number) => snapToGrid(value, gridSpacing, snapEnabled),
    [gridSpacing, snapEnabled],
  );

  // 足迹索引（scene 投影产物——摆放位置以 draft 为权威）
  const footprintById = useMemo(
    () => new Map(model.structures.map((entry) => [entry.unitId, entry.footprint])),
    [model.structures],
  );
  const placedIds = useMemo(() => Object.keys(draft.structures).sort(), [draft.structures]);
  const placed: PlacedStructure[] = useMemo(
    () =>
      placedIds.flatMap((unitId) => {
        const placement = draft.structures[unitId];
        if (placement === undefined) {
          return [];
        }
        return [
          {
            unitId,
            x: placement.x,
            y: placement.y,
            rotation: placement.rotation,
            groundElevation: placement.ground_elevation,
            footprint: footprintById.get(unitId) ?? null,
          },
        ];
      }),
    [placedIds, draft.structures, footprintById],
  );

  // 屏幕/世界换算（标注层恒定字号；世界 Y 北=屏幕上）
  const k = zoom * PX_PER_M;
  const toScreen = useCallback(
    (x: number, y: number): [number, number] => [pan.x + k * x, pan.y - k * y],
    [pan.x, pan.y, k],
  );
  const toWorld = useCallback(
    (clientX: number, clientY: number): SitePoint | null => {
      const rect = svgRef.current?.getBoundingClientRect();
      if (rect === undefined) {
        return null;
      }
      return {
        x: (clientX - rect.left - pan.x) / k,
        y: -(clientY - rect.top - pan.y) / k,
      };
    },
    [pan.x, pan.y, k],
  );

  // 滚轮缩放：非被动监听（React onWheel 被动——preventDefault 需显式注册）
  useEffect(() => {
    const element = svgRef.current;
    if (element === null) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      zoomBy(Math.exp(-event.deltaY * WHEEL_SENSITIVITY));
    };
    element.addEventListener("wheel", onWheel, { passive: false });
    return () => element.removeEventListener("wheel", onWheel);
  }, [zoomBy]);

  const beginSession = (event: React.PointerEvent, session: DragSession) => {
    dragRef.current = session;
    svgRef.current?.setPointerCapture(event.pointerId);
  };

  const handleBackgroundDown = (event: React.PointerEvent) => {
    if (event.button !== 0) {
      return;
    }
    const world = toWorld(event.clientX, event.clientY);
    if (world === null) {
      return;
    }
    if (tool === "road" || tool === "corridor") {
      appendPending({ x: snap(world.x), y: snap(world.y) }); // 绘制模式：点击=加点
      return;
    }
    setSelection(null); // 空白点击=取消选中+开始平移
    beginSession(event, {
      kind: "pan",
      startClientX: event.clientX,
      startClientY: event.clientY,
      startPanX: pan.x,
      startPanY: pan.y,
    });
  };

  const handlePointerMove = (event: React.PointerEvent) => {
    const session = dragRef.current;
    if (session === null) {
      return;
    }
    if (session.kind === "pan") {
      setPan({
        x: session.startPanX + (event.clientX - session.startClientX),
        y: session.startPanY + (event.clientY - session.startClientY),
      });
      return;
    }
    const world = toWorld(event.clientX, event.clientY);
    if (world === null) {
      return;
    }
    if (session.kind === "move") {
      onMove(session.unitId, snap(world.x - session.offsetX), snap(world.y - session.offsetY));
      return;
    }
    const center = draft.structures[session.unitId];
    if (center === undefined) {
      return;
    }
    // 把手方位角（世界逆时针自东起）——把手贴北缘：rotation=φ-90
    const deg = (Math.atan2(world.y - center.y, world.x - center.x) * 180) / Math.PI;
    onRotate(session.unitId, snapRotation(deg - 90, event.shiftKey));
  };

  const endSession = () => {
    dragRef.current = null;
  };

  const handleBackgroundDouble = () => {
    // 双击收笔：双击前两次 click 已加一重复点——先弹出再 ≥2 成立判定
    if (tool !== "road" && tool !== "corridor") {
      return;
    }
    popPending();
    const rest = useSiteplanStore.getState().pendingPoints;
    if (rest.length >= 2) {
      onCommitLine(rest);
    }
    discardPending();
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (tool !== "road" && tool !== "corridor") {
      return;
    }
    if (event.key === "Enter") {
      const points = useSiteplanStore.getState().pendingPoints;
      if (points.length >= 2) {
        onCommitLine(points); // Enter 收笔无重复点（≥2 前置在此收口）
      }
      discardPending();
    } else if (event.key === "Escape") {
      discardPending(); // Esc=取消绘制中折线
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const unitId = event.dataTransfer.getData("text/plain");
    const world = toWorld(event.clientX, event.clientY);
    if (unitId !== "" && world !== null) {
      onPlace(unitId, snap(world.x), snap(world.y));
    }
  };

  // 测距对（选中结构时——编辑辅助非校核裁判）
  const measurePairs = useMemo<MeasurePair[]>(() => {
    if (selection === null || selection.kind !== "structure") {
      return [];
    }
    const target = placed.find((entry) => entry.unitId === selection.id);
    if (target === undefined) {
      return [];
    }
    return measureToNearest(target, placed, MEASURE_COUNT).flatMap((measure) => {
      const other = placed.find((entry) => entry.unitId === measure.unitId);
      return other === undefined
        ? []
        : [{ measure, from: { x: target.x, y: target.y }, to: { x: other.x, y: other.y } }];
    });
  }, [selection, placed]);

  const corridorColor = (kind: string) => CORRIDOR_COLORS[kind] ?? CORRIDOR_DEFAULT_COLOR;

  return (
    <svg
      ref={svgRef}
      tabIndex={0}
      style={{
        width: "100%",
        height: "100%",
        display: "block",
        outline: "none",
        background: "#141414",
        touchAction: "none",
        cursor: tool === "select" ? "default" : "crosshair",
      }}
      onPointerDown={handleBackgroundDown}
      onPointerMove={handlePointerMove}
      onPointerUp={endSession}
      onLostPointerCapture={endSession}
      onDoubleClick={handleBackgroundDouble}
      onKeyDown={handleKeyDown}
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
    >
      <g transform={`translate(${pan.x} ${pan.y}) scale(${k} ${-k})`}>
        {showGrid && gridSpacing > 0 ? (
          <>
            <defs>
              <pattern id="siteplan-grid" width={gridSpacing} height={gridSpacing}
                patternUnits="userSpaceOnUse">
                <path d={`M ${gridSpacing} 0 L 0 0 0 ${gridSpacing}`} fill="none"
                  stroke={COLOR_GRID} strokeWidth={1} vectorEffect="non-scaling-stroke" />
              </pattern>
            </defs>
            <rect x={GRID_WORLD_MIN} y={GRID_WORLD_MIN}
              width={GRID_WORLD_MAX - GRID_WORLD_MIN} height={GRID_WORLD_MAX - GRID_WORLD_MIN}
              fill="url(#siteplan-grid)" pointerEvents="none" />
          </>
        ) : null}

        {/* 道路（实线）/走廊（虚线）：strokeWidth=宽度米——随 zoom 缩放 */}
        {draft.roads.map((road, index) => (
          <polyline key={`road-${index}`} points={pointsAttr(road.centerline)} fill="none"
            stroke={COLOR_ROAD} strokeWidth={road.width_m} strokeLinejoin="round"
            strokeLinecap="round" opacity={isSelectedLine(selection, "road", index) ? 1 : 0.75}
            onPointerDown={(event) => {
              if (tool === "select") {
                event.stopPropagation();
                setSelection({ kind: "road", index });
              }
            }} />
        ))}
        {draft.corridors.map((corridor, index) => (
          <polyline key={`corridor-${index}`} points={pointsAttr(corridor.centerline)} fill="none"
            stroke={corridorColor(corridor.kind)} strokeWidth={corridor.width_m}
            strokeDasharray={isSelectedLine(selection, "corridor", index) ? undefined : "3 1.5"}
            strokeLinejoin="round" strokeLinecap="round"
            onPointerDown={(event) => {
              if (tool === "select") {
                event.stopPropagation();
                setSelection({ kind: "corridor", index });
              }
            }} />
        ))}

        {/* 绘制中折线（虚线+点标记——收笔归 SiteplanPane 参数面板） */}
        {pendingPoints.length > 0 ? (
          <>
            <polyline points={pointsAttr(pendingPoints)} fill="none" stroke={COLOR_PENDING}
              strokeWidth={0.3} strokeDasharray="1.2 0.8" pointerEvents="none" />
            {pendingPoints.map((point, index) => (
              <circle key={`pending-${index}`} cx={point.x} cy={point.y} r={ENDPOINT_RADIUS}
                fill={COLOR_PENDING} pointerEvents="none" />
            ))}
          </>
        ) : null}

        {/* 构筑物：足迹矩形（旋转=transform rotate 世界逆时针）+未计算内框
            +旋转把手（拖拽=角度：90° 吸附/Shift 自由） */}
        {placed.map((entry) => {
          const selected =
            selection !== null &&
            selection.kind === "structure" &&
            selection.id === entry.unitId;
          const size = entry.footprint ?? UNCALC_SIZE;
          return (
            <g key={entry.unitId} transform={`rotate(${entry.rotation} ${entry.x} ${entry.y})`}>
              <rect x={entry.x - size.w / 2} y={entry.y - size.h / 2} width={size.w}
                height={size.h} fill={COLOR_STRUCTURE_FILL}
                stroke={selected ? COLOR_SELECTED : COLOR_STRUCTURE}
                strokeWidth={selected ? 0.5 : 0.25}
                onPointerDown={(event) => {
                  if (tool !== "select" || event.button !== 0) {
                    return; // 绘制模式不拦截（冒泡至画布加点）
                  }
                  event.stopPropagation();
                  // 双击自实现：setPointerCapture 重定向后续 click/dblclick 至
                  // svg——原生 rect.onDoubleClick 不可达，按 pointerdown 判定
                  const last = doubleTapRef.current;
                  const hit =
                    last !== null &&
                    last.unitId === entry.unitId &&
                    event.timeStamp - last.time < DOUBLE_TAP_MS &&
                    Math.hypot(event.clientX - last.clientX, event.clientY - last.clientY) <
                      DOUBLE_TAP_SLOP_PX;
                  if (hit) {
                    doubleTapRef.current = null;
                    onRemove(entry.unitId); // 双击已摆=移除回待摆区
                    return; // 已移除——本次不再起 move 会话
                  }
                  doubleTapRef.current = { time: event.timeStamp, unitId: entry.unitId,
                    clientX: event.clientX, clientY: event.clientY };
                  setSelection({ kind: "structure", id: entry.unitId });
                  const world = toWorld(event.clientX, event.clientY);
                  if (world !== null) {
                    beginSession(event, {
                      kind: "move",
                      unitId: entry.unitId,
                      offsetX: world.x - entry.x,
                      offsetY: world.y - entry.y,
                    });
                  }
                }}
              />
              {entry.footprint === null ? (
                /* 未计算：虚线内框示意（尺寸=显示层常量不落盘） */
                <rect x={entry.x - UNCALC_SIZE.w / 2 + 0.4} y={entry.y - UNCALC_SIZE.h / 2 + 0.4}
                  width={UNCALC_SIZE.w - 0.8} height={UNCALC_SIZE.h - 0.8} fill="none"
                  stroke={COLOR_STRUCTURE} strokeWidth={0.15} strokeDasharray="0.8 0.6"
                  pointerEvents="none" />
              ) : null}
              {selected ? (
                <circle cx={entry.x} cy={entry.y + size.h / 2 + ROTATE_HANDLE_GAP}
                  r={ROTATE_HANDLE_RADIUS} fill={COLOR_SELECTED}
                  onPointerDown={(event) => {
                    if (event.button !== 0) {
                      return;
                    }
                    event.stopPropagation();
                    beginSession(event, { kind: "rotate", unitId: entry.unitId });
                  }}
                />
              ) : null}
            </g>
          );
        })}

        {/* 测距虚线（双值标注走屏幕空间层） */}
        {measurePairs.map((pair) => (
          <line key={`measure-${pair.measure.unitId}`} x1={pair.from.x} y1={pair.from.y}
            x2={pair.to.x} y2={pair.to.y} stroke={COLOR_MEASURE} strokeWidth={0.2}
            strokeDasharray="1 0.8" pointerEvents="none" />
        ))}
      </g>

      {/* 屏幕空间标注层：结构名/未计算角标/测距双值（恒定字号） */}
      {placed.map((entry) => {
        const size = entry.footprint ?? UNCALC_SIZE;
        const [sx, sy] = toScreen(entry.x, entry.y - size.h / 2);
        return (
          <text key={`label-${entry.unitId}`} x={sx} y={sy - 4} fontSize={11}
            fill={entry.footprint === null ? COLOR_PENDING : "#c3ccd6"} textAnchor="middle"
            pointerEvents="none">
            {entry.footprint === null ? `${entry.unitId} · 未计算` : entry.unitId}
          </text>
        );
      })}
      {measurePairs.map((pair) => {
        const [sx, sy] = toScreen((pair.from.x + pair.to.x) / 2, (pair.from.y + pair.to.y) / 2);
        return (
          <text key={`measure-label-${pair.measure.unitId}`} x={sx} y={sy - 4} fontSize={11}
            fill={COLOR_MEASURE} textAnchor="middle" pointerEvents="none">
            {`中心 ${pair.measure.centerDistance.toFixed(1)} m / 净 ${
              pair.measure.clearDistance === null ? "—" : pair.measure.clearDistance.toFixed(1)
            } m`}
          </text>
        );
      })}
    </svg>
  );
}
