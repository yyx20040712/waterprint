/**
 * 布置编辑器视图 slice：平移/缩放/吸附开关/网格开关/选中/工具/折线点
 * （M3 L2a——FE6 口径 zustand node 直测首例在本批立：elevationStore 头注
 * 预告的「canvas 编辑批泛化为布置编辑批先立」收口）。
 *
 * 输入:  视图动作（setPan/setZoom/zoomBy/toggleSnap/toggleGrid/setSelection/
 *        setTool/resetPending/appendPending/popPending/discardPending）
 * 输出:  useSiteplanStore（zustand——纯 view 态，禁业务数据 §12.3：
 *        placement/footprint 等数据一律走 useSiteData 数据通道）
 *
 * 规格说明（M3 批 L2a，简报 §一.3/§三 store 面）：
 *   - zustand create 零 DOM 依赖：getState/setState/actions 可 node 直测
 *     （本 store 双测即首例——后续 store 批照此口径）；
 *   - pan/zoom=视口态（像素/倍率）：zoom 夹紧 [ZOOM_MIN, ZOOM_MAX]
 *     （0.1~10——简报 §三 store 面定值）；zoomBy 非有限因子=no-op 防御；
 *   - snapEnabled/showGrid=吸附/网格显示开关（默认开——简报 §一.6）；
 *   - tool=select|road|corridor|boundary（L4a 增第四态「边界红线」）；
 *     setTool 切换即取消绘制中折线（pendingPoints 清空——切换工具=弃笔
 *     语义，收笔 ≥2/红线 ≥3 前置归组件层）；
 *   - pendingPoints=折线绘制中点序列（米——世界坐标非屏幕）；
 *   - selection 三面：structure 按 unit_id、road/corridor 按索引
 *     （roads/corridors 是数组容器——索引即身份）。
 */
import { create } from "zustand";

/** zoom 夹紧下/上界（简报 §三 store 面：0.1~10）。 */
export const ZOOM_MIN = 0.1;
export const ZOOM_MAX = 10;

export type SiteplanSelection =
  | { kind: "structure"; id: string }
  | { kind: "road"; index: number }
  | { kind: "corridor"; index: number };

export type SiteplanTool = "select" | "road" | "corridor" | "boundary";

export type SiteplanPoint = { x: number; y: number };

type SiteplanState = {
  pan: { x: number; y: number };
  zoom: number;
  snapEnabled: boolean;
  showGrid: boolean;
  selection: SiteplanSelection | null;
  tool: SiteplanTool;
  pendingPoints: SiteplanPoint[];
  setPan: (pan: SiteplanPoint) => void;
  setZoom: (zoom: number) => void;
  zoomBy: (factor: number) => void;
  toggleSnap: () => void;
  toggleGrid: () => void;
  setSelection: (selection: SiteplanSelection | null) => void;
  setTool: (tool: SiteplanTool) => void;
  resetPending: (points: SiteplanPoint[]) => void;
  appendPending: (point: SiteplanPoint) => void;
  popPending: () => void;
  discardPending: () => void;
};

/** 夹紧（非有限值防御直通——NaN 不入视口态）。 */
function clampZoom(value: number): number {
  if (!Number.isFinite(value)) {
    return 1;
  }
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, value));
}

export const useSiteplanStore = create<SiteplanState>((set) => ({
  pan: { x: 0, y: 0 },
  zoom: 1,
  snapEnabled: true,
  showGrid: true,
  selection: null,
  tool: "select",
  pendingPoints: [],
  setPan: (pan) => set({ pan }),
  setZoom: (zoom) => set({ zoom: clampZoom(zoom) }),
  zoomBy: (factor) =>
    set((state) => ({
      zoom: Number.isFinite(factor)
        ? clampZoom(state.zoom * factor)
        : state.zoom,
    })),
  toggleSnap: () => set((state) => ({ snapEnabled: !state.snapEnabled })),
  toggleGrid: () => set((state) => ({ showGrid: !state.showGrid })),
  setSelection: (selection) => set({ selection }),
  // 切工具=弃笔：绘制中折线随切换取消（收笔 ≥2 前置在组件层判定）
  setTool: (tool) => set({ tool, pendingPoints: [] }),
  resetPending: (points) => set({ pendingPoints: points }),
  appendPending: (point) =>
    set((state) => ({ pendingPoints: [...state.pendingPoints, point] })),
  popPending: () =>
    set((state) => ({
      pendingPoints:
        state.pendingPoints.length === 0
          ? state.pendingPoints
          : state.pendingPoints.slice(0, -1),
    })),
  discardPending: () => set({ pendingPoints: [] }),
}));
