/**
 * 画布状态 slice：编辑会话态（zustand 实装——P0-3 骨架条款兑现）。
 *
 * 输入:  beginEdit(projectId, raw 快照)一次性摄入+designWriter 纯函数
 *        产物（加单元/连线/删除/拖拽位——本 store 零内联变更逻辑）
 * 输出:  编辑会话单例（session: projectId+基座四面+草稿+baseRaw——
 *        dirty=四面引用比对派生；消费面 selector 带 projectId 守卫）
 *
 * 规格说明（骨架冻结条款兑现+task-c2-edit-plan 红线⑤；呈裁⑤ 显式
 *   编辑钮=会话开关挂点）：
 *   - UI 态走 zustand；一切来自服务端的数据不进本 store（§17.2）：
 *     草稿=beginEdit 时点快照派生的**用户编辑工作副本**（非服务端
 *     缓存态——此后服务端 refetch/事件桥刷新零回流草稿）；保存体=
 *     保存时点最新服务端 raw（非 design 面最新）+草稿 design 面——
 *     既不覆写用户编辑（红线⑤快照隔离）、也不回写陈旧非 design 面；
 *   - 画布状态全经 store 持有，不依赖组件重挂载（§11 R14）；单会话
 *     制：切项目（session.projectId≠当前）消费面视同只读——不跨项目
 *     残留；会话拖拽位=视图态（positions 不入保存体——写侧持久化
 *     挂账段二）；
 *   - design 变更全经 designWriter 纯函数（薄壳通道——红线③ 零默认
 *     填充在纯函数层钉死）；dirty 非 UI 手置位（markSaved 后四面引用
 *     复归一致即自动清——拖拽位不参与 dirty 判定）。
 */
import { create } from "zustand";

import {
  addUnit,
  connectEdge,
  deleteEdge,
  deleteNodes,
  setPosition,
  type DesignDraft,
  type DesignEdgeEndpoint,
} from "../lib/designWriter";

/** 编辑会话（单例——projectId 守卫面）。 */
export type EditSession = {
  projectId: string;
  /** beginEdit 时点 raw 快照（保存体回退基座/布局基座消费面）。 */
  baseRaw: Record<string, unknown>;
  /** 基座四面（dirty 比对锚——markSaved 时与草稿引用复归）。 */
  base: Omit<DesignDraft, "positions">;
  draft: DesignDraft;
};

/** 草稿四面自 raw design 摄入（窄化——beginEdit 前置=projectFlow 已过门）。 */
function draftOf(raw: Record<string, unknown>): {
  base: Omit<DesignDraft, "positions">;
  draft: DesignDraft;
} {
  const design = (raw["design"] ?? {}) as Record<string, unknown>;
  const nodes = (design["nodes"] ?? {}) as Record<string, Record<string, unknown>>;
  const edges = (design["edges"] ?? []) as DesignDraft["edges"];
  const site = (design["site"] ?? {}) as Record<string, unknown>;
  const siteStructures = (site["structures"] ?? {}) as Record<
    string,
    Record<string, unknown>
  >;
  const checkedUnits = (design["checked_units"] ?? []) as string[];
  const base = { nodes, edges, siteStructures, checkedUnits };
  return { base, draft: { ...base, positions: {} } };
}

/** dirty 判定：保存面四引用比对（positions 视图态不参与）。 */
function isDirty(session: EditSession): boolean {
  const { base, draft } = session;
  return (
    draft.nodes !== base.nodes ||
    draft.edges !== base.edges ||
    draft.siteStructures !== base.siteStructures ||
    draft.checkedUnits !== base.checkedUnits
  );
}

type CanvasStore = {
  session: EditSession | null;
  beginEdit: (projectId: string, raw: Record<string, unknown>) => void;
  endEdit: () => void;
  addUnit: (unitId: string, kind: "unit" | "builtin") => string | null;
  connect: (src: DesignEdgeEndpoint, dst: DesignEdgeEndpoint) => void;
  deleteNodes: (ids: readonly string[]) => void;
  deleteEdge: (src: DesignEdgeEndpoint, dst: DesignEdgeEndpoint) => void;
  position: (id: string, pos: { x: number; y: number }) => void;
  markSaved: () => void;
};

export const useCanvasStore = create<CanvasStore>((set) => ({
  session: null,
  beginEdit: (projectId, raw) =>
    set((state) => {
      // 同项目重复进入=幂等续会话（草稿不覆写）；异项目=新会话顶替
      if (state.session?.projectId === projectId) {
        return {};
      }
      const { base, draft } = draftOf(raw);
      return { session: { projectId, baseRaw: raw, base, draft } };
    }),
  endEdit: () => set({ session: null }),
  addUnit: (unitId, kind) => {
    let nodeId: string | null = null;
    set((state) => {
      if (state.session === null) {
        return {};
      }
      const result = addUnit(state.session.draft, unitId, kind);
      nodeId = result.nodeId;
      return { session: { ...state.session, draft: result.draft } };
    });
    return nodeId;
  },
  connect: (src, dst) =>
    set((state) => {
      if (state.session === null) {
        return {};
      }
      return {
        session: {
          ...state.session,
          draft: connectEdge(state.session.draft, src, dst),
        },
      };
    }),
  deleteNodes: (ids) =>
    set((state) => {
      if (state.session === null) {
        return {};
      }
      return {
        session: { ...state.session, draft: deleteNodes(state.session.draft, ids) },
      };
    }),
  deleteEdge: (src, dst) =>
    set((state) => {
      if (state.session === null) {
        return {};
      }
      return {
        session: {
          ...state.session,
          draft: deleteEdge(state.session.draft, src, dst),
        },
      };
    }),
  position: (id, pos) =>
    set((state) => {
      if (state.session === null) {
        return {};
      }
      return {
        session: {
          ...state.session,
          draft: setPosition(state.session.draft, id, pos),
        },
      };
    }),
  markSaved: () =>
    set((state) => {
      if (state.session === null) {
        return {};
      }
      const { draft } = state.session;
      const { positions, ...saved } = draft;
      return {
        session: {
          ...state.session,
          // 基座=已保存草稿（四面引用复归一致→dirty 自清；positions 沿用）
          base: saved,
          draft: { ...saved, positions },
        },
      };
    }),
}));

/** 编辑态 selector（projectId 守卫——异项目会话视同只读零泄漏）。 */
export function useEditing(projectId: string | null): boolean {
  return useCanvasStore(
    (state) => state.session !== null && state.session.projectId === projectId,
  );
}

/** 草稿 selector（projectId 守卫——非编辑/异项目=null 消费面走只读渲染）。 */
export function useDraft(projectId: string | null): DesignDraft | null {
  return useCanvasStore((state) =>
    state.session !== null && state.session.projectId === projectId
      ? state.session.draft
      : null,
  );
}

/** baseRaw selector（保存体回退基座/布局基座——同守卫）。 */
export function useEditBaseRaw(projectId: string | null): Record<
  string,
  unknown
> | null {
  return useCanvasStore((state) =>
    state.session !== null && state.session.projectId === projectId
      ? state.session.baseRaw
      : null,
  );
}

/** dirty selector（四面引用比对派生——非会话恒 false）。 */
export function useDirty(projectId: string | null): boolean {
  return useCanvasStore((state) =>
    state.session !== null && state.session.projectId === projectId
      ? isDirty(state.session)
      : false,
  );
}
