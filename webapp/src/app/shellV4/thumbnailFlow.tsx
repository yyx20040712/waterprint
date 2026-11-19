/**
 * v4 工艺画布缩略形态（B1 骨架批 2026-10-09；b3 功能面重涂批 2026-11-19
 * ——节点卡按批准稿 network.html .flow-node 形重制〔b3 拆件 thumbnailNode：
 * 标题行〔域色字形+中文名〕+id 行〔mono〕+域线 meta 行〕；水/泥线语义=CSS 轴
 * var(--wp-water/sludge)——随主题注入轴换肤〕；连线/图例/MiniMap 全数
 * 并轴 var() 化〔b1 遗留「JS 域色恒 light 档」收口〕；左树点选落画布
 * 通道=addRequest 受控 prop〔screenToFlowPosition 画布中心落点〕）。
 *
 * 输入: projectId+selectedUnitId（受控 ?node= 选中）+onSelectedUnitChange
 *        （选中上抛）+addRequest（左树点选落点请求——ProcessZone 上抛，
 *        本件换算画布中心坐标落节点后 onAddHandled 回执）+useProjectQuery
 *        （raw）+canvasStore（编辑会话——自动 beginEdit）+
 *        useListUnitsApiUnitsGet（图题/端口表/业务线）
 * 输出: 缩略图画布：ThumbnailNode 卡〔glyph+图题+id+域线 meta+左右锚点
 *        Handle〕+连线（streamColorOf 域流色=轴变量串）+fitView+Controls
 *        +MiniMap〔域色 nodeColor〕+图例〔水线/泥线/虚线为回流〕+右键
 *        空白=HierarchicalCatalog 落点；V4 P1 id 副标移除裁决由 b3 批准
 *        稿推翻（稿 .flow-node-id 行在场——id 显示恢复，data-node-id
 *        探针锚保留）
 *
 * 规格说明（B1 任务书 §三.3+b3 批准稿 network.html 画布段）：
 *   - 引擎复用：projectFlow 投影+draftProjectRaw 草稿合成+canvasStore 五
 *     通道（connect/deleteNodes/position——M1 编辑链同源，v4 常开）；
 *   - 无编辑模式：raw 就绪且无会话→自动 beginEdit（快照红线⑤沿袭——
 *     服务端 refetch 不回流草稿）；保存=顶带保存钮（手动）；
 *   - 右键空白=分级目录：pane contextmenu 光标位→菜单；二级项点选=
 *     store.addUnit+position 落右键坐标（新节点即在视线处）；
 *   - 锚点端口=目录首 IN/OUT 端口（catalog 未就绪/无端口回退 in/out 泛键
 *     ——B1 骨架口径；全端口面=B2 批裁量）；
 *   - b3 主题面：colorMode 随 themeStore（dark=暗档）+浮层底/边全轴色；
 *     域色消费=var(--wp-*) 注入轴（零 JS hex——三主题即时换肤）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Controls,
  MiniMap,
  ReactFlow,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useThemeStore } from "../../shared/store/themeStore";

import { useListUnitsApiUnitsGet } from "../../shared/api/generated/units/units";
import { useProjectQuery } from "../../features/canvas/api/useProjectQuery";
import { projectFlow } from "../../features/canvas/lib/projectFlow";
import { draftProjectRaw } from "../../features/canvas/lib/designWriter";
import { streamColorOf } from "../../features/canvas/lib/unitGlyph";
import {
  useCanvasStore,
  useDraft,
  useEditBaseRaw,
  useEditing,
} from "../../features/canvas/store/canvasStore";
import { HierarchicalCatalog } from "./hierarchicalCatalog";
import { ThumbnailNode, type ThumbData } from "./thumbnailNode";

/** 左树点选落点请求（ProcessZone 受控 prop——seq 变更即落一次）。 */
export interface CanvasAddRequest {
  unitId: string;
  kind: "unit" | "builtin";
  seq: number;
}

/** 自定义节点注册（模块级常量——引用稳定）。 */
const NODE_TYPES: NodeTypes = { unit: ThumbnailNode };

/** 画布图例行（V3 D1+b3 稿 .flow-leg形重制：横排单行 chip——水线/泥线
 *  色条+「虚线为回流」注；色值=--wp-* 注入轴 var() 串〔b1 遗留 JS 域色
 *  三态收口——随主题换肤零重渲染〕；空态提示同槽互斥——nodes>0 才渲染）。 */
function FlowLegend() {
  const rows = [
    {
      key: "water",
      testid: "wp-v4-flow-legend-water",
      label: "水线",
      color: "var(--wp-water)",
    },
    {
      key: "sludge",
      testid: "wp-v4-flow-legend-sludge",
      label: "泥线",
      color: "var(--wp-sludge)",
    },
  ] as const;
  return (
    <div
      className="wp-v4-flow-legend"
      data-testid="wp-v4-flow-legend"
    >
      {rows.map((row) => (
        <span
          key={row.key}
          data-testid={row.testid}
          className="wp-v4-legend-item"
        >
          <span
            aria-hidden
            style={{ background: row.color }}
          />
          {row.label}
        </span>
      ))}
      <span className="wp-v4-legend-note">虚线为回流</span>
    </div>
  );
}

/** 受控测量回写析出（V3 W-A 回炉）：受控 nodes prop 下 xyflow 内部测量
 *  链不落外部 state（node.measured 永不填充——MiniMap 的
 *  nodeHasDimensions 门恒 null，缩略面板零节点 rect，probe-mm*.json
 *  实证），dimensions 变更须宿主回写。纯函数：从变更流析出各节点
 *  测量值（无 dimensions 变更=-null 不触发 setState）。 */
export function pickMeasured(
  changes: NodeChange[],
): Record<string, { width: number; height: number }> | null {
  let picked: Record<string, { width: number; height: number }> | null = null;
  for (const change of changes) {
    if (change.type === "dimensions" && change.dimensions != null) {
      (picked ??= {})[change.id] = change.dimensions;
    }
  }
  return picked;
}

/** fitView 参数（美感抛光批 #8：maxZoom=1+padding 0.18——少节点不再
 *  放大到越界裁切、多节点按节点卡原生 128–168px 尺度体系缩放；大图
 *  全入镜缩小的承接面=MiniMap 导航，不靠缩放制造字号）。 */
const FIT_OPTIONS = { maxZoom: 1, padding: 0.18 } as const;

/** 视口收敛子件（B2 P3 k1-N10 修复版：fitKey 变更 refit——首键跳过
 *  〔mount 拟合=ReactFlow fitView prop 承担〕。CanvasFlow 原制的
 *  useNodesInitialized 门在受控 nodes prop 下恒 false〔store 聚合旗不
 *  翻转——B2 探针实录 fitKey 1:→2: 期恒 skip、includeHiddenNodes 形
 *  同滞〕，refit 链死路；改自足键序门=节点增删确定性 refit，
 *  includeHiddenNodes 未测量节点按位置零尺寸纳入）。 */
function FitViewOnNodes({ fitKey }: { fitKey: string }) {
  const { fitView } = useReactFlow();
  const prevKeyRef = useRef<string | null>(null);
  useEffect(() => {
    if (fitKey === "" || prevKeyRef.current === fitKey) {
      return;
    }
    const isFirstKey = prevKeyRef.current === null;
    prevKeyRef.current = fitKey;
    if (isFirstKey) {
      return; // mount 拟合归 fitView prop（受控面 nodesInitialized 门不可依赖）
    }
    void fitView({ ...FIT_OPTIONS, duration: 200, includeHiddenNodes: true });
  }, [fitKey, fitView]);
  return null;
}

export function ThumbnailFlow({
  projectId,
  selectedUnitId = null,
  onSelectedUnitChange,
  addRequest = null,
  onAddHandled,
}: {
  projectId: string;
  /** ?node= 对象选中真相（受控——node.selected 驱动缩略卡描边）。 */
  selectedUnitId?: string | null;
  /** 选中写入回调（node 点击上抛——shellV4 写 ?node=）。 */
  onSelectedUnitChange: (unitId: string | null) => void;
  /** 左树点选落点请求（seq 变更触发——null/同 seq 零动作）。 */
  addRequest?: CanvasAddRequest | null;
  /** 落点回执（addRequest 处理完成——ProcessZone 清请求态）。 */
  onAddHandled?: () => void;
}) {
  const query = useProjectQuery(projectId);
  const editing = useEditing(projectId);
  const draft = useDraft(projectId);
  const baseRaw = useEditBaseRaw(projectId);
  const catalog = useListUnitsApiUnitsGet();
  const themeMode = useThemeStore((state) => state.mode);
  // flow 实例（onInit 捕获——右键目录落点坐标换算+树点选中心落点；本组件
  // 根在 Provider 外不可用 useReactFlow〔实例 ref=xyflow 官方外部消费通道〕
  // 泛型宽松面=仅消费 screenToFlowPosition 几何换算）
  const flowRef = useRef<{ screenToFlowPosition: (pos: { x: number; y: number }) => { x: number; y: number } } | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  // 受控测量回写（V3 W-A 回炉）：dimensions 变更累积 map——注入 node.measured
  const [measuredById, setMeasuredById] = useState<
    Record<string, { width: number; height: number }>
  >({});
  // 树点选落点请求序（已处理 seq——同请求幂等跳过）
  const handledAddSeqRef = useRef<number>(-1);

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

  // 目录聚合：图题+锚点端口+业务线（查表键=kind ?? unitId——内置归 kind 键）
  const metaByUnit = useMemo(() => {
    const map = new Map<string, { nameZh: string; inPort?: string; outPort?: string; line?: string | null }>();
    for (const unit of catalog.data?.units ?? []) {
      const inPort = (unit.ports ?? []).find((p) => p.direction === "IN")?.port_id;
      const outPort = (unit.ports ?? []).find((p) => p.direction === "OUT")?.port_id;
      map.set(unit.unit_id, { nameZh: unit.name_zh, inPort, outPort, line: unit.business_line ?? null });
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
          measured: measuredById[node.id],
          data: { ...node.data, nameZh: meta?.nameZh, inPort: meta?.inPort, outPort: meta?.outPort, line: meta?.line },
        };
      }),
    [projection, selectedUnitId, metaByUnit, measuredById],
  );

  const lineByNode = useMemo(() => {
    const map = new Map<string, string | null>();
    for (const node of projection?.nodes ?? []) {
      map.set(node.id, metaByUnit.get(node.data.kind ?? node.data.unitId)?.line ?? null);
    }
    return map;
  }, [projection, metaByUnit]);

  const edges = useMemo<Edge[]>(() => {
    return (projection?.edges ?? []).map((edge) => {
      // b3：域流色=轴变量串（var(--wp-water/sludge)——随主题注入轴换肤）
      const color = streamColorOf(
        lineByNode.get(edge.source),
        lineByNode.get(edge.target),
      );
      return {
        ...edge,
        style: { ...edge.style, stroke: color, strokeWidth: 1.8 },
        markerEnd: { type: "arrowclosed", color },
      };
    });
  }, [projection, lineByNode]);

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

  // b3 左树点选落点（画布中心 screenToFlowPosition——请求 seq 门幂等）
  useEffect(() => {
    if (addRequest === null || addRequest.seq === handledAddSeqRef.current) {
      return;
    }
    handledAddSeqRef.current = addRequest.seq;
    const rect = stageRef.current?.getBoundingClientRect();
    const screen =
      rect === undefined
        ? { x: 0, y: 0 }
        : { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    addFromCatalog({ unit_id: addRequest.unitId, kind: addRequest.kind }, screen);
    onAddHandled?.();
  }, [addRequest, onAddHandled]);

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

  const floatingStyle = {
    background: "var(--wp-bg-elevated)",
    border: "1px solid var(--wp-border-2)",
    borderRadius: 8,
    overflow: "hidden",
    boxShadow: "0 2px 10px var(--wp-shadow)",
  };

  return (
    <div ref={stageRef} style={{ position: "relative", height: "100%", overflow: "hidden" }}>
      <ReactFlow
        onInit={(instance) => {
          flowRef.current = instance;
        }}
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        fitViewOptions={FIT_OPTIONS}
        minZoom={0.1}
        colorMode={themeMode === "dark" ? "dark" : "light"}
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
          const deletedIds = deleted.map((node) => node.id);
          useCanvasStore.getState().deleteNodes(deletedIds);
          // B2 P3 k1-N8：删后选中滞留清理——被删集含 ?node= 选中真相时
          // 解除选中（剥 ?node=），防幻影选中（左栏参数/右栏方案面悬空）。
          if (
            selectedUnitId !== null &&
            deletedIds.includes(selectedUnitId)
          ) {
            onSelectedUnitChange(null);
          }
        }}
        onNodesChange={(changes: NodeChange[]) => {
          for (const change of changes) {
            if (change.type === "position" && change.position != null) {
              useCanvasStore.getState().position(change.id, change.position);
            }
          }
          // dimensions 变更回写（V3 W-A 回炉——受控测量路径补全；R2 k2-N3：
          // 等值短路——全同值批返回 prev 引用，免无谓 nodes memo 重算）
          const dims = pickMeasured(changes);
          if (dims !== null) {
            setMeasuredById((prev) => {
              const unchanged = Object.entries(dims).every(
                ([id, d]) => prev[id]?.width === d.width && prev[id]?.height === d.height,
              );
              return unchanged ? prev : { ...prev, ...dims };
            });
          }
        }}
        proOptions={{ hideAttribution: true }}
        style={{ backgroundColor: "transparent" }}
      >
        <FitViewOnNodes fitKey={sig} />
        {/* W-B 回炉：复位右下（V2 基线位——笔1 擅改 bottom-left 与 MiniMap
            叠压且右下按钮组丢失，probe-minimap.json 实证嵌压；一行还原；
            b3：底/边/影并轴 var() 化（三主题随轴换肤） */}
        <Controls
          showInteractive={false}
          position="bottom-right"
          style={floatingStyle}
        />
        {/* V3 D1：MiniMap 左下（与 Controls 右下对角；pannable/zoomable
            +卡片壳同 Controls 制式；b3：nodeColor=域色轴变量串〔水/泥线
            语义延伸至缩略图〕+底色并轴）。W-C 注记：浮动面板遮画布左下
            节点（golden 布局 2 节点）=浮动控件常态（fitView 动态视口可
            平移避让，导航价值大于遮挡代价）——保留不移位。 */}
        <MiniMap
          position="bottom-left"
          pannable
          zoomable
          style={floatingStyle}
          nodeColor={(node: Node) =>
            lineByNode.get(node.id) === "sludge"
              ? "var(--wp-sludge)"
              : lineByNode.has(node.id)
                ? "var(--wp-water)"
                : "var(--wp-border)"
          }
          /* b4 留观收口（暖档 MiniMap 饱和度）：遮罩色并 canvas 轴〔暖档
             不再套亮灰默认遮罩——三主题随轴〕，节点描边并 elevated 阅读面 */
          maskColor="color-mix(in srgb, var(--wp-canvas) 72%, transparent)"
          nodeStrokeColor="var(--wp-bg-elevated)"
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
      ) : (
        <FlowLegend />
      )}
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
