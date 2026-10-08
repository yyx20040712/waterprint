/**
 * v4 工艺画布缩略形态（B1 骨架批 2026-10-09——现行画布引擎复用、节点呈现
 * 换缩略图形态：react-flow 投影/草稿通道全沿 CanvasFlow 链，节点=预绘简笔
 * SVG+图题+左右锚点；无编辑模式——数据就绪自动 beginEdit，右键/拖拽/连线/
 * 删除均常规交互直开；wireframe-d-v4 屏 1 形）。
 *
 * 输入:  projectId+selectedUnitId（受控 ?node= 选中）+onSelectedUnitChange
 *        （选中上抛）+useProjectQuery（raw）+canvasStore（编辑会话——自动
 *        beginEdit）+useListUnitsApiUnitsGet（图题/端口表）
 * 输出:  缩略图画布：ThumbnailNode 域色缩略卡〔glyph+图题+ nodeId 副标+
 *        左右锚点 Handle〕+连线（streamColorOf 域流色）+fitView+Controls
 *        +右键空白=HierarchicalCatalog 落点（screenToFlowPosition）
 *
 * 规格说明（B1 任务书 §三.3——plan §九.1）：
 *   - 引擎复用：projectFlow 投影+draftProjectRaw 草稿合成+canvasStore 五
 *     通道（connect/deleteNodes/position——M1 编辑链同源，v4 常开）；
 *   - 无编辑模式：raw 就绪且无会话→自动 beginEdit（快照红线⑤沿袭——
 *     服务端 refetch 不回流草稿）；保存=顶带保存钮（手动）；
 *   - 右键空白=分级目录：pane contextmenu 光标位→菜单；二级项点选=
 *     store.addUnit+position 落右键坐标（新节点即在视线处）；
 *   - 锚点端口=目录首 IN/OUT 端口（catalog 未就绪/无端口回退 in/out 泛键
 *     ——B1 骨架口径；全端口面=B2 批裁量）；
 *   - 亮色：colorMode=light+白底（v4 亮色基线——CanvasFlow 深色面不复用）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Controls,
  Handle,
  Position,
  ReactFlow,
  useNodesInitialized,
  useReactFlow,
  type Connection,
  type Edge,
  type NodeChange,
  type NodeProps,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import { useProjectQuery } from "../../features/canvas/api/useProjectQuery";
import { projectFlow, type UnitFlowNode } from "../../features/canvas/lib/projectFlow";
import { draftProjectRaw } from "../../features/canvas/lib/designWriter";
import { streamColorOf } from "../../features/canvas/lib/unitGlyph";
import {
  useCanvasStore,
  useDraft,
  useEditBaseRaw,
  useEditing,
} from "../../features/canvas/store/canvasStore";
import { ThumbnailGlyph } from "../../features/canvas/components/thumbnailGlyph";
import { HierarchicalCatalog } from "./hierarchicalCatalog";

/** 缩略图节点 data（渲染层聚合注入——投影 data 零触碰，M1 editData 同制）。 */
type ThumbData = UnitFlowNode["data"] & {
  nameZh?: string;
  inPort?: string;
  outPort?: string;
};

/** 缩略图节点（glyph+图题+左右锚点——selected 经 node.selected 驱动描边）。 */
function ThumbnailNode({ data, selected }: NodeProps) {
  const thumb = data as ThumbData;
  const title = thumb.unitId;
  return (
    <div className={`wp-v4-node${selected ? " selected" : ""}`} data-node-id={title}>
      <Handle
        type="target"
        position={Position.Left}
        id={thumb.inPort ?? "in"}
        style={{ background: "#ffffff", borderColor: "var(--wp-text-2)" }}
      />
      <span className="wp-v4-thumb">
        <ThumbnailGlyph kind={thumb.kind ?? thumb.unitId} />
      </span>
      <span className="wp-v4-cap">{thumb.nameZh ?? title}</span>
      <span className="wp-v4-sub">{title}</span>
      <Handle
        type="source"
        position={Position.Right}
        id={thumb.outPort ?? "out"}
        style={{ background: "#ffffff", borderColor: "var(--wp-text-2)" }}
      />
    </div>
  );
}

/** 自定义节点注册（模块级常量——引用稳定）。 */
const NODE_TYPES: NodeTypes = { unit: ThumbnailNode };

/** 视口收敛子件（CanvasFlow FitViewOnNodes 同制——nodesInitialized 门控）。 */
function FitViewOnNodes({ fitKey }: { fitKey: string }) {
  const { fitView } = useReactFlow();
  const nodesReady = useNodesInitialized();
  const fittedRef = useRef("");
  useEffect(() => {
    if (!nodesReady || fitKey === "" || fittedRef.current === fitKey) {
      return;
    }
    fittedRef.current = fitKey;
    void fitView({ padding: 0.12, duration: 200, includeHiddenNodes: true });
  }, [nodesReady, fitKey, fitView]);
  return null;
}

export function ThumbnailFlow({
  projectId,
  selectedUnitId = null,
  onSelectedUnitChange,
}: {
  projectId: string;
  /** ?node= 对象选中真相（受控——node.selected 驱动缩略卡描边）。 */
  selectedUnitId?: string | null;
  /** 选中写入回调（node 点击上抛——shellV4 写 ?node=）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
}) {
  const query = useProjectQuery(projectId);
  const editing = useEditing(projectId);
  const draft = useDraft(projectId);
  const baseRaw = useEditBaseRaw(projectId);
  const catalog = useListUnitsApiUnitsGet();
  // flow 实例（onInit 捕获——右键目录落点坐标换算；useReactFlow 在本组件
  // 根不可用〔Provider 外〕——实例 ref 为 xyflow 官方外部消费通道；
  // 泛型宽松面=仅消费 screenToFlowPosition 几何换算）
  const flowRef = useRef<{ screenToFlowPosition: (pos: { x: number; y: number }) => { x: number; y: number } } | null>(null);
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);

  // 无编辑模式：raw 就绪且无本项目会话→自动 beginEdit（幂等——同项目续会话）
  useEffect(() => {
    if (!editing && query.data !== undefined) {
      useCanvasStore.getState().beginEdit(projectId, query.data);
    }
  }, [editing, projectId, query.data]);

  const projectionRaw = useMemo<Record<string, unknown> | undefined>(() => {
    if (draft !== null && baseRaw !== null) {
      return draftProjectRaw(baseRaw, draft);
    }
    return query.data;
  }, [draft, baseRaw, query.data]);

  const projection = useMemo(() => {
    if (projectionRaw === undefined) {
      return null;
    }
    try {
      return projectFlow(projectionRaw);
    } catch {
      return null; // 投影拒（版本门/形状）——错误薄壳（M1 CanvasFlow 同类面）
    }
  }, [projectionRaw]);

  // 目录聚合：图题+锚点端口（查表键=kind ?? unitId——内置归 kind 键）
  const metaByUnit = useMemo(() => {
    const map = new Map<string, { nameZh: string; inPort?: string; outPort?: string }>();
    for (const unit of catalog.data?.units ?? []) {
      const inPort = (unit.ports ?? []).find((p) => p.direction === "IN")?.port_id;
      const outPort = (unit.ports ?? []).find((p) => p.direction === "OUT")?.port_id;
      map.set(unit.unit_id, { nameZh: unit.name_zh, inPort, outPort });
    }
    return map;
  }, [catalog.data]);

  const nodes = useMemo(
    () =>
      (projection?.nodes ?? []).map((node) => {
        const meta = metaByUnit.get(node.data.kind ?? node.data.unitId);
        return {
          ...node,
          selected: node.id === selectedUnitId,
          data: { ...node.data, nameZh: meta?.nameZh, inPort: meta?.inPort, outPort: meta?.outPort },
        };
      }),
    [projection, selectedUnitId, metaByUnit],
  );

  const edges = useMemo<Edge[]>(() => {
    const lineByNode = new Map<string, string | null>();
    for (const node of projection?.nodes ?? []) {
      const entry = (catalog.data?.units ?? []).find(
        (unit) => unit.unit_id === (node.data.kind ?? node.data.unitId),
      );
      lineByNode.set(node.id, entry?.business_line ?? null);
    }
    return (projection?.edges ?? []).map((edge) => {
      const color = streamColorOf(
        lineByNode.get(edge.source),
        lineByNode.get(edge.target),
      );
      return {
        ...edge,
        style: { ...edge.style, stroke: color, strokeWidth: 1.6 },
        markerEnd: { type: "arrowclosed", color },
      };
    });
  }, [projection, catalog.data]);

  const sig = nodes.length > 0 ? `${nodes.length}:${nodes[0]?.id ?? ""}` : "";

  /** 右键目录落点（addUnit+position 右键坐标——视线处落节点）。 */
  const addFromCatalog = (unit: { unit_id: string; kind: "unit" | "builtin" }, screen: { x: number; y: number }) => {
    const store = useCanvasStore.getState();
    if (store.session?.projectId !== projectId && query.data !== undefined) {
      store.beginEdit(projectId, query.data);
    }
    const flowPos = flowRef.current?.screenToFlowPosition(screen) ?? { x: 0, y: 0 };
    const nodeId = useCanvasStore.getState().addUnit(unit.unit_id, unit.kind);
    if (nodeId !== null) {
      useCanvasStore.getState().position(nodeId, flowPos);
    }
  };

  if (query.isError) {
    return (
      <div role="alert" style={{ padding: 14, color: "var(--wp-error)" }}>
        工艺图加载失败：
        {query.error instanceof Error ? query.error.message : "未知错误"}
      </div>
    );
  }
  if (projectionRaw === undefined) {
    return <div style={{ padding: 14, color: "var(--wp-text-2)" }}>工艺图加载中…</div>;
  }
  if (projection === null) {
    return (
      <div role="alert" style={{ padding: 14, color: "var(--wp-error)" }}>
        工艺图投影失败（项目文件形状非法）
      </div>
    );
  }

  return (
    <div style={{ position: "relative", height: "100%", overflow: "hidden" }}>
      <ReactFlow
        onInit={(instance) => {
          flowRef.current = instance;
        }}
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        minZoom={0.1}
        colorMode="light"
        nodesDraggable
        nodesConnectable
        elementsSelectable
        deleteKeyCode={["Backspace", "Delete"]}
        onPaneClick={() => onSelectedUnitChange(null)}
        onNodeClick={(_event, node) => onSelectedUnitChange(node.id)}
        onPaneContextMenu={(event) => {
          event.preventDefault();
          setMenu({ x: event.clientX, y: event.clientY });
        }}
        onNodeContextMenu={(event) => {
          // 回炉 R15：节点右键不弹建工艺目录（规约=右键空白落点）——
          // 吞默认菜单，不落 menu 态
          event.preventDefault();
        }}
        onConnect={(connection: Connection) => {
          const { source, sourceHandle, target, targetHandle } = connection;
          if (source == null || sourceHandle == null || target == null || targetHandle == null) {
            return;
          }
          useCanvasStore.getState().connect(
            { unit_id: source, port_id: sourceHandle },
            { unit_id: target, port_id: targetHandle },
          );
        }}
        onNodesDelete={(deleted) => {
          useCanvasStore.getState().deleteNodes(deleted.map((node) => node.id));
        }}
        onNodesChange={(changes: NodeChange[]) => {
          for (const change of changes) {
            if (change.type === "position" && change.position != null) {
              useCanvasStore.getState().position(change.id, change.position);
            }
          }
        }}
        proOptions={{ hideAttribution: true }}
        style={{ backgroundColor: "transparent" }}
      >
        <FitViewOnNodes fitKey={sig} />
        <Controls
          showInteractive={false}
          position="bottom-right"
          style={{
            background: "#ffffff",
            border: "1px solid var(--wp-border-2)",
            borderRadius: 8,
            overflow: "hidden",
            boxShadow: "0 2px 10px rgba(31,35,41,.12)",
          }}
        />
      </ReactFlow>
      {nodes.length === 0 ? (
        <div
          aria-hidden
          style={{
            position: "absolute",
            left: 14,
            top: 10,
            color: "var(--wp-text-2)",
            fontSize: 11,
            pointerEvents: "none",
          }}
        >
          画布为空——右键空白处选择工艺单元
        </div>
      ) : null}
      {menu !== null ? (
        <HierarchicalCatalog
          x={menu.x}
          y={menu.y}
          onPick={(unit) => addFromCatalog(unit, menu)}
          onClose={() => setMenu(null)}
        />
      ) : null}
    </div>
  );
}
