/**
 * 红线层子件：polygon 渲染+选中态顶点把手+双击增删点路由（B4 笔③ R1——
 * 自 SiteCanvas polygon 段子件化[行预算通路]；仓内首顶点级编辑交互面）。
 *
 * 输入:  points（draft.boundary——<3 点=不渲染）+grid/snapEnabled（吸附参
 *        数——snapVertexPoint 归 vertexEditing 层，Pane 收净值[简报 R5]）+
 *        toWorld（屏幕→世界归 SiteCanvas）+三顶点回调（onMoveVertex/
 *        onInsertVertex/onRemoveVertex——copy-on-write 归父层）；tool/
 *        selection/setSelection 自 siteplanStore 直读（SiteCanvas 同例）
 * 输出:  世界空间 SVG 子树（g transform 内——polygon+顶点把手）或 null
 *
 * 规格说明（简报 R1/R4/R5——双击判定=isDoubleTapAt[canvasDisplay 通用化
 *   DoubleTapAnchor 先例]）：
 *   - pointerEvents 解锁为描边可命中（fill=none 保持——仅描边窄带命中；
 *     重叠区 structure 渲染在后优先，z 序实测归 B 面探针⑥不做序断言）；
 *     非 select 工具=装饰态 pointerEvents=none（绘制点击落背景加点）；
 *   - 选中态：描边加粗 BOUNDARY_STROKE_SELECTED+顶点把手 r=VERTEX_HANDLE_
 *     RADIUS=1.0 世界单位（简报 R1 弃屏幕空间公式——天然随 zoom）；
 *   - 把手 pointerdown=拖拽会话（capture 自收容于把手圆——逐帧 toWorld→
 *     snapVertexPoint→onMoveVertex）；双击顶点=删点（拒删 message 归父层，
 *     selection 不变）；双击线段=nearestSegmentIndex+segmentProjection 投
 *     影落点+吸附→onInsertVertex；歧义序=顶点优先（把手 stopPropagation
 *     天然截流——Kimi 不确定项⑥裁定）。
 */
import { useRef } from "react";

import { semanticColor } from "../../../shared/ui/semanticColors";
import {
  BOUNDARY_DASH, BOUNDARY_STROKE, BOUNDARY_STROKE_SELECTED, VERTEX_HANDLE_RADIUS,
  isDoubleTapAt, pointsAttr, type TapAnchor,
} from "../lib/canvasDisplay";
import type { SitePoint } from "../lib/projectSite";
import {
  BOUNDARY_MIN_VERTICES, nearestSegmentIndex, segmentProjection, snapVertexPoint,
} from "../lib/vertexEditing";
import { useSiteplanStore } from "../store/siteplanStore";

export type BoundaryLayerProps = {
  points: readonly SitePoint[];
  grid: number;
  snapEnabled: boolean;
  toWorld: (clientX: number, clientY: number) => SitePoint | null;
  onMoveVertex: (index: number, p: SitePoint) => void;
  onInsertVertex: (segIndex: number, p: SitePoint) => void;
  onRemoveVertex: (index: number) => void;
};

export function BoundaryLayer({
  points, grid, snapEnabled, toWorld, onMoveVertex, onInsertVertex, onRemoveVertex,
}: BoundaryLayerProps) {
  const { tool, selection, setSelection } = useSiteplanStore();
  const vertexTapRef = useRef<TapAnchor | null>(null);
  const strokeTapRef = useRef<TapAnchor | null>(null);
  const dragIndexRef = useRef<number | null>(null); // 顶点拖拽会话（ref 自持不触发渲染）
  const endDrag = () => { dragIndexRef.current = null; };
  if (points.length < BOUNDARY_MIN_VERTICES) { return null; } // <3 点=不渲染（core ≥3 门镜像）
  const interactive = tool === "select";
  const selected = selection !== null && selection.kind === "boundary";
  const snap = (p: SitePoint): SitePoint => snapVertexPoint(p, grid, snapEnabled);

  const handleStrokeDown = (event: React.PointerEvent) => {
    if (!interactive || event.button !== 0) { return; }
    event.stopPropagation(); // 描边命中=选中（不落背景平移/加点——道路同例）
    setSelection({ kind: "boundary" });
    if (!isDoubleTapAt(strokeTapRef.current, null, event.timeStamp, event.clientX, event.clientY)) {
      strokeTapRef.current = { time: event.timeStamp, clientX: event.clientX, clientY: event.clientY, key: null };
      return;
    }
    strokeTapRef.current = null; // 双击线段=增点路由
    const world = toWorld(event.clientX, event.clientY);
    const segIndex = world === null ? -1 : nearestSegmentIndex(points, world);
    if (world !== null && segIndex >= 0) {
      // R 轮 G1-02:投影可能 null(非法段守卫)——null 跳过不插入
      const projected = segmentProjection(points, world, segIndex);
      if (projected !== null) {
        onInsertVertex(segIndex, snap(projected));
      }
    }
  };

  const handleVertexDown = (event: React.PointerEvent, index: number) => {
    if (!interactive || event.button !== 0) { return; }
    event.stopPropagation(); // 顶点优先于线段（双击歧义序=顶点——截流）
    if (isDoubleTapAt(vertexTapRef.current, index, event.timeStamp, event.clientX, event.clientY)) {
      vertexTapRef.current = null;
      onRemoveVertex(index); // 双击顶点=删点（拒删提示归父层——selection 不变）
      return;
    }
    vertexTapRef.current = { time: event.timeStamp, clientX: event.clientX, clientY: event.clientY, key: index };
    dragIndexRef.current = index;
    event.currentTarget.setPointerCapture(event.pointerId); // 会话自收容于把手圆
  };

  const handleVertexMove = (event: React.PointerEvent) => {
    const index = dragIndexRef.current;
    const world = index === null ? null : toWorld(event.clientX, event.clientY);
    if (index !== null && world !== null) {
      onMoveVertex(index, snap(world)); // 吸附归 vertexEditing 层——Pane 收净值
    }
  };

  return (
    <>
      <polygon points={pointsAttr(points)} fill="none" stroke={semanticColor("boundary")}
        strokeWidth={selected ? BOUNDARY_STROKE_SELECTED : BOUNDARY_STROKE}
        strokeDasharray={BOUNDARY_DASH} strokeLinejoin="round"
        pointerEvents={interactive ? "visibleStroke" : "none"} onPointerDown={handleStrokeDown} />
      {selected
        ? points.map((point, index) => (
            <circle key={`vertex-${index}`} cx={point.x} cy={point.y} r={VERTEX_HANDLE_RADIUS}
              fill={semanticColor("selected")}
              pointerEvents={interactive ? "visiblePainted" : "none"}
              onPointerDown={(event) => handleVertexDown(event, index)}
              onPointerMove={handleVertexMove}
              onPointerUp={endDrag} onLostPointerCapture={endDrag} />
          ))
        : null}
    </>
  );
}
