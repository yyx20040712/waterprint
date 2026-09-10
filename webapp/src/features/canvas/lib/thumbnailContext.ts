/**
 * 节点缩略图上下文（C2-thumb V3——app 层组合穿线的 canvas 域消费面）。
 *
 * 输入:  app 层（canvasPane）持 Viewer3d 域 ThumbnailStage 产出
 *        Map<unit_id, dataURL>（features 互不依赖红线——canvas 不
 *        import viewer3d，数据经本 context 注入）
 * 输出:  Provider（CanvasFlow 挂）+useUnitThumbnails（UnitNode 消费
 *        ——缺省空 Map=回退象形图标态[未算/无构型/渲染未及]）
 *
 * 规格说明（task-C2-thumb-plan.md V3；libraryFocusId props 穿线先例的
 *   context 变体——UnitNode 深 React Flow 树内、逐层 props 传递经
 *   nodeTypes 不可达，context 为最小穿线面）：
 *   - 投影 data 零触碰（projectFlow 只读红线维持——缩略图经 context
 *     旁路，投影层不感知）；
 *   - Map 引用批内稳定（ThumbnailStage 整批交付一次——UnitNode
 *     useContext 重渲仅一批一次）。
 */
import { createContext, useContext } from "react";

/** 缺省空 Map（无舞台挂载/未就绪——全节点回退象形图标）。 */
export const EMPTY_THUMBNAILS: ReadonlyMap<string, string> = new Map();

const ThumbnailContext = createContext<ReadonlyMap<string, string>>(
  EMPTY_THUMBNAILS,
);

export const ThumbnailProvider = ThumbnailContext.Provider;

/** 节点缩略图读取（unit_id=design.nodes 键——缺席=回退象形图标）。 */
export function useUnitThumbnail(unitId: string): string | null {
  return useContext(ThumbnailContext).get(unitId) ?? null;
}
