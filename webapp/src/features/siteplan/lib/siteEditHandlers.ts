/**
 * 厂区编辑回调族工厂（F2 并发丢更新批 2026-11-20 自 SiteplanPane 拆出
 * ——组件 500 行顶墙拆件配方 ADR-024 同构：draft copy-on-write 回调族
 * 纯迁移，闭包依赖经 deps 注入，行为零变）。
 *
 * 输入:  deps{draft/setDraft/setSelection/tool/setFinishedLine/
 *        setRemoveRequest/notifyBoundaryReject}（宿主组件闭包态注入）
 * 输出:  编辑回调族十一件（onPlace/onMove/onRotate/onRemove/onElev/
 *        onCommitLine/onRemoveLine/onRemoveRequest/onMoveVertex/
 *        onInsertVertex/onRemoveVertex——SiteCanvas props 与确认门消费）
 *        +FinishedLine 类型+BOUNDARY_REJECT_HINT（红线拒删文案单源）
 */
import type { Dispatch, SetStateAction } from "react";

import {
  removeLineAt,
  type SiteDesignShape,
  type SitePoint,
  type StructurePlacement,
} from "./projectSite";
import {
  BOUNDARY_MIN_VERTICES,
  insertVertex,
  moveVertex,
  removeVertex,
} from "./vertexEditing";
import type { RemovableSelection, SiteplanTool } from "../store/siteplanStore";

/** 收笔挂起面（折线已成立、宽度/kind 待补）。 */
export type FinishedLine = { kind: "road" | "corridor"; points: SitePoint[] };

/** 红线拒删提示文案（B4 笔③——BOUNDARY_MIN_VERTICES 单源插值不硬编码数字；
 *  整体清空另有「清空红线」Popconfirm 入口）。 */
export const BOUNDARY_REJECT_HINT =
  `红线至少需 ${BOUNDARY_MIN_VERTICES} 个顶点，不能再删（整体移除请用「清空红线」）`;

/** 回调族依赖（宿主闭包态——setState 族与工具态原样注入）。 */
export type SiteEditHandlersDeps = {
  draft: SiteDesignShape | null;
  setDraft: Dispatch<SetStateAction<SiteDesignShape | null>>;
  setSelection: (selection: RemovableSelection | null) => void;
  tool: SiteplanTool;
  setFinishedLine: Dispatch<SetStateAction<FinishedLine | null>>;
  setRemoveRequest: Dispatch<SetStateAction<RemovableSelection | null>>;
  /** 红线拒删提示上行（antd message 注入面——本层零 antd 依赖）。 */
  notifyBoundaryReject: () => void;
};

/** 编辑回调族工厂（结构微改 copy-on-write——draft 永不原位突变）。 */
export function buildSiteEditHandlers(deps: SiteEditHandlersDeps) {
  const { draft, setDraft, setSelection, tool } = deps;

  const updateStructure = (unitId: string, patch: Partial<StructurePlacement>) => {
    setDraft((prev) => {
      const current = prev === null ? undefined : prev.structures[unitId];
      if (prev === null || current === undefined) {
        return prev;
      }
      return {
        ...prev,
        structures: {
          ...prev.structures,
          [unitId]: { ...current, ...patch },
        },
      };
    });
  };

  return {
    onPlace: (unitId: string, x: number, y: number) => {
      setDraft((prev) => {
        if (prev === null) {
          return prev;
        }
        return {
          ...prev,
          structures: {
            ...prev.structures,
            [unitId]: {
              x,
              y,
              rotation: 0,
              ground_elevation: prev.structures[unitId]?.ground_elevation ?? null,
            },
          },
        };
      });
    },
    onMove: (unitId: string, x: number, y: number) => updateStructure(unitId, { x, y }),
    onRotate: (unitId: string, rotation: number) => updateStructure(unitId, { rotation }),
    onRemove: (unitId: string) => {
      setDraft((prev) => {
        if (prev === null || prev.structures[unitId] === undefined) {
          return prev;
        }
        const structures = { ...prev.structures };
        delete structures[unitId];
        return { ...prev, structures };
      });
      setSelection(null); // 选中面随移除收口
    },
    onElev: (unitId: string, elevation: number | null) =>
      updateStructure(unitId, { ground_elevation: elevation }),
    onCommitLine: (points: SitePoint[]) => {
      if (tool === "boundary") {
        // L4a 红线：无宽度/kind 面板（boundary 无宽）——≥3 点即闭合收笔
        // 直接落 draft.boundary；红线只有一个（schema 单多边形），重画=替换。
        setDraft((prev) => (prev === null ? prev : { ...prev, boundary: points }));
        return;
      }
      if (tool !== "road" && tool !== "corridor") {
        return;
      }
      deps.setFinishedLine({ kind: tool, points });
    },
    // B4 笔② R2：immutable splice 删除+setSelection(null) 收口（索引前移
    // ——选中索引随删除失效，onRemove 先例同式）
    onRemoveLine: (kind: "road" | "corridor", index: number) => {
      setDraft((prev) => {
        if (prev === null) {
          return prev;
        }
        return kind === "road"
          ? { ...prev, roads: removeLineAt(prev.roads, index) }
          : { ...prev, corridors: removeLineAt(prev.corridors, index) };
      });
      setSelection(null);
    },
    // 画布 Delete 键上行——汇侧栏同一确认门（不直删：仓内无 undo）；
    // B4 笔③ 泛化 RemovableSelection 签名（boundary 上行=清空通路分支）
    onRemoveRequest: (target: RemovableSelection) => deps.setRemoveRequest(target),
    // B4 笔③ R5 顶点三回调（BoundaryLayer 上行——吸附净值已归 vertexEditing
    // 层完成，本层 copy-on-write 落 draft.boundary；顶点增删后 boundary 单例
    // selection 保持——身份不随顶点数变，简报 R5）
    onMoveVertex: (index: number, p: SitePoint) => {
      setDraft((prev) => (prev === null ? prev : { ...prev, boundary: moveVertex(prev.boundary, index, p) }));
    },
    onInsertVertex: (segIndex: number, p: SitePoint) => {
      setDraft((prev) => (prev === null ? prev : { ...prev, boundary: insertVertex(prev.boundary, segIndex, p) }));
    },
    // 删点：删至 <BOUNDARY_MIN_VERTICES 拒删=提示+零动作（draft/
    // selection 不变——简报 R1；拒删判定先行，副作用不进 setState updater）
    onRemoveVertex: (index: number) => {
      if (draft === null) {
        return;
      }
      if (removeVertex(draft.boundary, index) === null) {
        deps.notifyBoundaryReject(); // 拒删=提示+零动作
        return;
      }
      setDraft((prev) => {
        if (prev === null) {
          return prev;
        }
        const next = removeVertex(prev.boundary, index);
        return next === null ? prev : { ...prev, boundary: next };
      });
    },
  };
}
