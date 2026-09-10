/**
 * React Flow 画布容器：design 工艺图只读渲染+选中回调+画布工具面
 * （ADR-001 渲染面）。
 *
 * 输入:  projectId（useProjectQuery 数据通道→projectFlow 投影——组件薄壳
 *        唯一数据源，服务端数据不进 store §17.2/D5）+selectedUnitId（受控
 *        选中态——D2 app 层 props）+onNodeClick?: (unitId)=>void（受控回调）
 * 输出:  工艺画布只读工作区（React Flow：UnitNode 域色卡片+方向端口+
 *        recycle 虚线+两色流线+fitView 视口适配+节点点击选中反馈；
 *        图例/MiniMap/缩放工具条浮层；加载/空态/错误薄壳）
 *
 * 规格说明（FE4 批 6b 段一 D1/D4/D5/D7；FE5 批 6b 段三；C2-canvas 批
 *   P1/P2/P4~P7 重制——task-C2-canvas-plan.md §二；glm D 项②③痛点处置）：
 *   - 只读批交互面：视图态（缩放/平移/框选）开；编辑面全关——edges
 *     Connectable=false+不传 onConnect/onNodesChange；nodesDraggable=false
 *     （明示只读免误导光标）；elementsSelectable=true（选中高亮非编辑）；
 *   - FE5 选中接线（D2 props 受控）维持：onNodeClick 透传 node.id 给
 *     app 层；selectedUnitId 回流经 node.selected 驱动 UnitNode 鎏金
 *     描边（C2-canvas：选中色沿 C1 鎏金意图）；只读面加回调不破只读
 *     三重闭合；
 *   - P1 画布底色（视觉稿 A 冻结）：--wp-bg-page 深蓝底+radial 光晕层
 *     +wp-dotgrid 点阵层（C1 预备工具类本批消费兑现——glm「纯黑横带」
 *     观感项根除）；ReactFlow 内建 backgroundColor 退役；
 *   - P2 满高：根容器 100%（canvasPane flex 行高度链+global.css tabs
 *     content 链满高配套）；560 固定高+1px 边框退役（视觉稿无边框）；
 *   - P4 连线着色（渲染层聚合——投影层零触碰）：catalog 构建
 *     unitId→business_line（查表键=kind ?? unitId——内置节点归
 *     catalog kind 键），edges 注入 stroke+箭头色（streamColorOf 两色
 *     制：任一 sludge 端→泥棕；双端已知→水蓝；未知→中性灰）；
 *     recycle 虚线=投影层产物叠加保持；
 *   - P5 图例（左上浮层）：线型三项（水线/污泥线/回流虚线）+当前图
 *     实际出现的域色点（四域动态——BUSINESS_LINE_ZH 同词本地映射，
 *     features 不向上 import app 层 §13.5）；
 *   - P6 MiniMap（左下）：React Flow 内建件（nodeColor=域色+深蓝底
 *     样式定制——默认右下位覆盖至左下）；pannable zoomable；
 *   - P7 缩放工具条（右下）：React Flow 内建 Controls（＋/－/fitView
 *     三钮；showInteractive=false——只读批无编辑锁定面；视觉稿第四钮
 *     ⊞ 不实装记档）；默认左下位覆盖至右下；
 *   - D4 不 lazy 维持（canvas=默认标签首屏必渲染）；D7 样式：
 *     @xyflow/react/dist/style.css 组件内引入+colorMode=dark 维持；
 *   - 投影层三类显式拒（D6）在 useMemo try/catch 落错误薄壳维持；
 *     nodeTypes 模块级常量（引用稳定）；编辑态 store（canvasStore）/
 *     连线规则/自动布局维持骨架挂账（D5）。
 */
import { useEffect, useMemo, useRef } from "react";
import {
  Controls,
  MiniMap,
  ReactFlow,
  useNodesInitialized,
  useReactFlow,
  type Edge,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useListUnitsApiUnitsGet } from "../../../shared/api/generated/units/units";
import { useProjectQuery } from "../api/useProjectQuery";
import {
  ProjectFlowError,
  projectFlow,
  type ProjectFlow,
} from "../lib/projectFlow";
import { domainColorOf, streamColorOf } from "../lib/unitGlyph";
import { UnitNode } from "./UnitNode";

/** 自定义节点注册（模块级常量——引用稳定）。 */
const NODE_TYPES: NodeTypes = { unit: UnitNode };

/** 域中文名（图例色点标签——unitLibraryTree BUSINESS_LINE_ZH 同词本地
 * 映射：features 不向上 import app 层 §13.5；展示层翻译非业务复制）。 */
const DOMAIN_LABELS: Record<string, string> = {
  municipal: "市政污水",
  conveyance: "输送提升",
  mine_water: "矿井水",
  sludge: "污泥处理",
};

/** 图例线型项（视觉稿冻结——水/泥/回流三项；色值=unitGlyph 主源
 * 联动面成员 R-G3——回流灰沿 text-2 轴）。 */
const LEGEND_LINES = [
  { key: "water", label: "水线流向", color: "#4da3ff" },
  { key: "sludge", label: "污泥线", color: "#9c6b45" },
  { key: "recycle", label: "回流", color: "var(--wp-text-2)" },
] as const;

/** 视口收敛子件（FIX-ACC1②，2026-09-09 验收缺陷）：节点集就绪且**测量
 * 完成**后显式 fitView。两层前置缺陷：① StrictMode dev 双挂载使
 * <ReactFlow fitView> 挂载期一次性拟合失效；② 拟合早于节点测量时
 * fitView 拿不到尺寸=空拟合。useNodesInitialized 门控+fitKey 去重。 */
function FitViewOnNodes({ fitKey }: { fitKey: string }) {
  const { fitView } = useReactFlow();
  const nodesReady = useNodesInitialized();
  const fittedRef = useRef("");
  useEffect(() => {
    if (!nodesReady || fitKey === "" || fittedRef.current === fitKey) {
      return;
    }
    fittedRef.current = fitKey;
    // includeHiddenNodes：未测量节点按位置零尺寸纳入（minZoom 0.1 见
    // ReactFlow prop——默认 0.5 会钳住宽图幅的收敛缩放）。
    void fitView({ padding: 0.1, duration: 200, includeHiddenNodes: true });
  }, [nodesReady, fitKey, fitView]);
  return null;
}

export function CanvasFlow({
  projectId,
  selectedUnitId = null,
  onNodeClick,
}: {
  projectId: string;
  /** 受控选中单元（null=无选中——app 层 D2 props 单一持有面）。 */
  selectedUnitId?: string | null;
  /** 节点点击回调（unitId=React Flow node.id=design.nodes 键）。 */
  onNodeClick?: (unitId: string) => void;
}) {
  const query = useProjectQuery(projectId);
  // 域色数据源=单元清单端点（UnitNode 同一 hook 同一缓存——React Query
  // 去重；P4 边着色/P5 图例域集/P6 MiniMap nodeColor 三面消费）
  const catalog = useListUnitsApiUnitsGet();
  // 投影围栏：D6 显式拒在此收编落错误薄壳（fetch isError 之外第二出口）
  const projection = useMemo<{
    flow: ProjectFlow | null;
    error: ProjectFlowError | null;
  }>(() => {
    if (!query.data) {
      return { flow: null, error: null };
    }
    try {
      return { flow: projectFlow(query.data), error: null };
    } catch (error) {
      return {
        flow: null,
        error:
          error instanceof ProjectFlowError
            ? error
            : new ProjectFlowError(String(error)),
      };
    }
  }, [query.data]);
  // 选中标记：selectedUnitId → node.selected（受控字段——投影 data 零触碰）
  const nodes = useMemo(
    () =>
      (projection.flow?.nodes ?? []).map((node) => ({
        ...node,
        selected: node.id === selectedUnitId,
      })),
    [projection.flow, selectedUnitId],
  );
  // 域归属表：nodeId → business_line（查表键=kind ?? unitId——内置节点
  // 归 catalog kind 键「municipal_input 等，business_line=municipal」）
  const lineByNodeId = useMemo(() => {
    const unitLine = new Map<string, string>();
    for (const unit of catalog.data?.units ?? []) {
      unitLine.set(unit.unit_id, unit.business_line);
    }
    const byNode = new Map<string, string | null>();
    for (const node of projection.flow?.nodes ?? []) {
      byNode.set(node.id, unitLine.get(node.data.kind ?? node.data.unitId) ?? null);
    }
    return byNode;
  }, [catalog.data, projection.flow]);
  // P4 边着色（渲染层聚合——投影产物叠加 stroke/箭头色+域分宽，recycle
  // 虚线保持）：水线 2px/泥线 1.8px/未知域中性 1.5px（三分支按
  // business_line 判——R-G2 处置：判据不比较色值字面量[改色联动失配
  // 风险]，GC-04 中性独立档；视觉稿冻结宽——glm 实现评审 R2 发现只
  // 着色未设宽，React Flow 默认 1px 细线对比度不足）
  const edges = useMemo<Edge[]>(
    () =>
      (projection.flow?.edges ?? []).map((edge) => {
        const srcLine = lineByNodeId.get(edge.source);
        const dstLine = lineByNodeId.get(edge.target);
        const color = streamColorOf(srcLine, dstLine);
        const width =
          srcLine === "sludge" || dstLine === "sludge"
            ? 1.8
            : srcLine != null && dstLine != null
              ? 2
              : 1.5;
        return {
          ...edge,
          style: { ...edge.style, stroke: color, strokeWidth: width },
          markerEnd: { type: "arrowclosed", color },
        };
      }),
    [projection.flow, lineByNodeId],
  );
  // P5 图例域集：当前图实际出现的域（四域声明序去重——未知域不列）
  const legendDomains = useMemo(() => {
    const seen = new Set(lineByNodeId.values());
    return Object.keys(DOMAIN_LABELS).filter((line) => seen.has(line));
  }, [lineByNodeId]);
  // 视口收敛键：节点集签名（选中态变化不触发重拟合——只有数据面变化才收敛）
  const fitKey =
    nodes.length > 0 ? `${nodes.length}:${nodes[0]?.id ?? ""}` : "";

  if (query.isError) {
    return (
      <div role="alert">
        工艺图加载失败：
        {query.error instanceof Error ? query.error.message : "未知错误"}
      </div>
    );
  }
  if (projection.error) {
    return (
      <div role="alert">工艺图投影失败：{projection.error.message}</div>
    );
  }
  const flow = projection.flow;
  if (!flow) {
    return <div>工艺图加载中…（{projectId.slice(0, 8)}）</div>;
  }
  if (flow.nodes.length === 0) {
    return (
      <div>
        该项目工艺图为空（design.nodes 无节点）——建图流程见
        docs/user-manual.md「快速开始」。
      </div>
    );
  }
  return (
    <div
      style={{
        position: "relative",
        height: "100%",
        overflow: "hidden",
        borderRadius: 8,
        background:
          "radial-gradient(1100px 500px at 62% 30%, rgba(37,72,128,.16), transparent 70%), var(--wp-bg-page)",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        minZoom={0.1}
        colorMode="dark"
        nodesDraggable={false}
        nodesConnectable={false}
        edgesFocusable={false}
        elementsSelectable
        deleteKeyCode={null}
        onNodeClick={(_event, node) => {
          onNodeClick?.(node.id);
        }}
        proOptions={{ hideAttribution: true }}
        style={{ backgroundColor: "transparent" }}
      >
        <FitViewOnNodes fitKey={fitKey} />
        {/* P6 MiniMap（左下——默认右下位覆盖）：域色节点缩略+视口框 */}
        <MiniMap
          pannable
          zoomable
          nodeColor={(node) =>
            domainColorOf(lineByNodeId.get(node.id) ?? null)
          }
          nodeStrokeWidth={0}
          style={{
            left: 14,
            right: "auto",
            background: "rgba(18,33,58,.88)",
            border: "1px solid var(--wp-border)",
            borderRadius: 8,
            width: 168,
            height: 108,
          }}
        />
        {/* P7 缩放工具条（右下——默认左下位覆盖）：＋/－/fitView 三钮 */}
        <Controls
          showInteractive={false}
          style={{
            left: "auto",
            right: 14,
            background: "var(--wp-bg-container)",
            border: "1px solid var(--wp-border)",
            borderRadius: 8,
            overflow: "hidden",
            boxShadow: "0 4px 16px rgba(3,10,22,.5)",
          }}
        />
      </ReactFlow>
      {/* P1 点阵层（C1 工具类消费兑现——指针穿透） */}
      <div
        aria-hidden
        className="wp-dotgrid"
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      />
      {/* P5 图例（左上浮层——线型三项+当前图域色点） */}
      <div
        style={{
          position: "absolute",
          left: 14,
          top: 12,
          display: "flex",
          gap: 14,
          alignItems: "center",
          background: "rgba(18,33,58,.85)",
          border: "1px solid var(--wp-border-2)",
          borderRadius: 8,
          padding: "5px 12px",
          fontSize: 11,
          color: "var(--wp-text-2)",
          zIndex: 5,
          pointerEvents: "none",
        }}
      >
        {LEGEND_LINES.map((item) => (
          <span key={item.key} style={{ display: "inline-flex", alignItems: "center" }}>
            <span
              aria-hidden
              style={{
                display: "inline-block",
                width: 14,
                borderTop: `2px ${item.key === "recycle" ? "dashed" : "solid"} ${item.color}`,
                borderRadius: 2,
                marginRight: 5,
              }}
            />
            {item.label}
          </span>
        ))}
        {legendDomains.length > 0 && (
          <>
            <span aria-hidden style={{ width: 1, height: 12, background: "var(--wp-border-2)" }} />
            {legendDomains.map((line) => (
              <span key={line} style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                <span
                  aria-hidden
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 2,
                    background: domainColorOf(line),
                  }}
                />
                {DOMAIN_LABELS[line] ?? line}
              </span>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
