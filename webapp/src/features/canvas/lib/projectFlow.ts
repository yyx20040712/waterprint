/**
 * 投影层纯函数：design 工艺图 JSON → React Flow nodes/edges（组件薄壳唯一数据源）。
 *
 * 输入:  readProject 返回体（弱类型 {[key:string]:unknown}——D6 窄化门在此收口）
 * 输出:  ProjectFlow（React Flow 受控 nodes/edges——D3 布局坐标+D1 方向中性端口
 *        +recycle 虚线标记；非法形状抛 ProjectFlowError）
 *
 * 规格说明（FE4 批 6b 段一，D1~D6）：
 *   - D6 弱类型窄化门（入口防线，FE1 SCENE_VERSION 门同构轻门）：顶层缺
 *     format_version 或非 string 拒；design.nodes 非 object/节点值非 object/
 *     design.edges 非 array/边缺 src|dst/端点非 {unit_id,port_id} 双 string/
 *     边端 unit_id 悬空（不在 nodes）→逐类显式拒，错误消息带索引/键定位
 *     （呈现错误薄壳可反查，不白屏）；具体版本值不校验——M-3 版本门+
 *     D2 双闸在 service/core（TS 侧零业务复制红线）；
 *   - D2 卡片=纯 unit key+内置 kind 标注：值含 kind 字符串键=内置节点
 *     （四种：municipal_input/junction/quality_edit/recycle_junction——
 *     透传不设白名单，合法性归 server 读取链）；参数值不进投影输出
 *     （参数面板挂账段二）；中文名映射/结果摘要挂账段二（正路=server
 *     单元清单端点）；
 *   - D1 端口=方向中性：端口表不在项目文件（真相在 core manifest——
 *     前端无法从 GET /api/projects 取到），本投影按边端点方向聚合
 *     （src→源端口右向/target→目标端口左向），灰阶中性色归组件层；
 *     流体色+端口表挂账段二；例外（数据驱动可做）：edge.recycle=true
 *     →虚线边（README「回流虚线」语义）；
 *   - D3 坐标=layout 优先+拓扑兜底：view.layout 读侧约定
 *     {[unit_id]:{x,y}}——须形状合规且覆盖全部节点才整体采用，否则整段
 *     忽略走兜底（不炸）；兜底=波次分层（Kahn 波：入度归零为波，无波时
 *     取字典序最小破环——BFS 层深等价），X=波次*LAYOUT_X_STEP，层内按
 *     unit_id 字典序排 Y=LAYOUT_Y_STEP 等距；D6 悬空边拒在前，布局阶段
 *     无悬空端点；全无边=单列 key 排序；确定性纯函数可 node 测；写侧
 *     （拖拽持久化）挂账段二；
 *   - 零运行期库 import（FE1 projectScene 同构）：@xyflow/react 只取
 *     type——node 测试不拖 window/document 面；markerEnd 箭头用
 *     EdgeMarker 字符串字面量（xyflow 视觉常量非业务复制）；
 *   - recycle 非 bool 值宽容呈现为非虚线（core executor 的布尔校验在
 *     calc 链，读取链不重复裁判——记档裁量）。
 */
import type { Edge, Node } from "@xyflow/react";

/** 兜底布局步距（X=波次层距/Y=层内行距——导出供测试计算期望坐标）。 */
export const LAYOUT_X_STEP = 260;
export const LAYOUT_Y_STEP = 120;

/** recycle 虚线样式串（README 回流虚线语义——灰阶中性非语义色）。 */
const RECYCLE_DASH = "6 4";

/** 节点卡片渲染数据（D2 纯 key+kind；端口=边端点方向聚合 D1）。 */
export type UnitFlowNodeData = {
  unitId: string;
  kind: string | null;
  sourcePorts: string[];
  targetPorts: string[];
};

/** React Flow 单元节点（type="unit"——UnitNode 渲染件注册键）。 */
export type UnitFlowNode = Node<UnitFlowNodeData, "unit">;

/** React Flow 边（默认 bezier——D1 方向中性+recycle 虚线例外）。 */
export type FlowEdge = Edge;

/** 投影产物（CanvasFlow 受控 props 直喂）。 */
export type ProjectFlow = {
  nodes: UnitFlowNode[];
  edges: FlowEdge[];
};

/** 投影非法（版本门/形状逐类拒/悬空边）——渲染层显式拒（错误薄壳呈现）。 */
export class ProjectFlowError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProjectFlowError";
  }
}

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 已窄化的边端点（unit_id/port_id 双 string——悬空校验后的形态）。 */
type FlowEndpoint = { unitId: string; portId: string };

function reject(message: string): never {
  throw new ProjectFlowError(message);
}

function narrowEndpoint(
  element: Record<string, unknown>,
  side: "src" | "dst",
  index: number,
): FlowEndpoint {
  const endpoint = element[side];
  if (!isRecord(endpoint)) {
    reject(
      `design.edges[${index}].${side} 须为含 unit_id/port_id 的对象：得到 ${JSON.stringify(endpoint) ?? "undefined"}`,
    );
  }
  const unitId = endpoint["unit_id"];
  const portId = endpoint["port_id"];
  if (typeof unitId !== "string" || typeof portId !== "string") {
    reject(
      `design.edges[${index}].${side} 端点须为 unit_id/port_id 双字符串：`
        + `unit_id=${JSON.stringify(unitId) ?? "undefined"},`
        + `port_id=${JSON.stringify(portId) ?? "undefined"}`,
    );
  }
  return { unitId, portId };
}

/**
 * 拓扑兜底布局（D3 波次分层——确定性纯函数）。
 * 波=入度归零节点集（Kahn 波）；无波（纯环/残余环）取字典序最小破环；
 * 全无边时全部节点归波 0=单列 key 排序。
 */
export function fallbackLayout(
  nodeIds: string[],
  edges: { src: string; dst: string }[],
): Map<string, { x: number; y: number }> {
  const incoming = new Map<string, string[]>();
  for (const id of nodeIds) {
    incoming.set(id, []);
  }
  for (const edge of edges) {
    incoming.get(edge.dst)?.push(edge.src);
  }
  const positions = new Map<string, { x: number; y: number }>();
  // remaining 恒字典序（排序一次+filter 保序——破环取 remaining[0] 确定）
  let remaining = [...nodeIds].sort();
  let layer = 0;
  while (remaining.length > 0) {
    const settled = new Set(positions.keys());
    const wave = remaining.filter((id) =>
      (incoming.get(id) ?? []).every((src) => settled.has(src)),
    );
    if (wave.length === 0) {
      wave.push(remaining[0] as string);
    }
    wave.forEach((id, row) => {
      positions.set(id, { x: layer * LAYOUT_X_STEP, y: row * LAYOUT_Y_STEP });
    });
    const waved = new Set(wave);
    remaining = remaining.filter((id) => !waved.has(id));
    layer += 1;
  }
  return positions;
}

/**
 * 读侧 layout 采纳（D3：形状合规且覆盖全部节点才整体采用，否则 null 走兜底）。
 * 未知键（不在 nodes 的 unit_id）忽略——nodes 是覆盖面。
 */
function readLayout(
  view: unknown,
  nodeIds: string[],
): Map<string, { x: number; y: number }> | null {
  if (!isRecord(view)) {
    return null;
  }
  const layout = view["layout"];
  if (!isRecord(layout)) {
    return null;
  }
  const positions = new Map<string, { x: number; y: number }>();
  for (const id of nodeIds) {
    const entry = layout[id];
    if (!isRecord(entry)) {
      return null;
    }
    const x = entry["x"];
    const y = entry["y"];
    if (
      typeof x !== "number" ||
      typeof y !== "number" ||
      !Number.isFinite(x) ||
      !Number.isFinite(y)
    ) {
      return null;
    }
    positions.set(id, { x, y });
  }
  return positions;
}

export function projectFlow(raw: Record<string, unknown>): ProjectFlow {
  // D6 门 1：format_version 轻门（存在+string——具体值归 service/core 双闸）
  const version = raw["format_version"];
  if (typeof version !== "string") {
    reject(
      `项目文件缺 format_version 或非字符串：${JSON.stringify(version) ?? "undefined"}`
        + "（版本语义门在 service/core——前端只做形状轻门）",
    );
  }
  // D6 门 2：design 容器
  const design = raw["design"];
  if (!isRecord(design)) {
    reject(
      `design 须为对象：得到 ${JSON.stringify(design) ?? "undefined"}`,
    );
  }
  // D6 门 3：design.nodes 逐键窄化
  const nodesRaw = design["nodes"];
  if (!isRecord(nodesRaw)) {
    reject(
      `design.nodes 须为对象（unit_id→参数 dict）：得到 ${JSON.stringify(nodesRaw) ?? "undefined"}`,
    );
  }
  for (const [unitId, params] of Object.entries(nodesRaw)) {
    if (!isRecord(params)) {
      reject(
        `design.nodes[${unitId}] 须为对象（参数 dict）：得到 ${JSON.stringify(params) ?? "undefined"}`,
      );
    }
  }
  const unitIds = Object.keys(nodesRaw).sort();
  const knownUnits = new Set(unitIds);
  // D6 门 4：design.edges 逐条窄化+悬空校验
  const edgesRaw = design["edges"];
  if (!Array.isArray(edgesRaw)) {
    reject(
      `design.edges 须为数组：得到 ${JSON.stringify(edgesRaw) ?? "undefined"}`,
    );
  }
  const narrowedEdges: { src: FlowEndpoint; dst: FlowEndpoint; recycle: boolean }[] = [];
  edgesRaw.forEach((element, index) => {
    if (!isRecord(element)) {
      reject(
        `design.edges[${index}] 须为对象：得到 ${JSON.stringify(element) ?? "undefined"}`,
      );
    }
    if (!("src" in element) || !("dst" in element)) {
      reject(
        `design.edges[${index}] 缺 src 或 dst 端点：得到 ${JSON.stringify(element)}`,
      );
    }
    const src = narrowEndpoint(element, "src", index);
    const dst = narrowEndpoint(element, "dst", index);
    for (const [side, endpoint] of [
      ["src", src],
      ["dst", dst],
    ] as const) {
      if (!knownUnits.has(endpoint.unitId)) {
        reject(
          `design.edges[${index}].${side} 悬空 unit_id：${endpoint.unitId} 不在 design.nodes`
            + "（工艺图与节点表一致性破坏）",
        );
      }
    }
    narrowedEdges.push({ src, dst, recycle: element["recycle"] === true });
  });
  // D3：坐标=layout 优先，形状不符或覆盖不全整段忽略走拓扑兜底
  const positions =
    readLayout(raw["view"], unitIds) ??
    fallbackLayout(
      unitIds,
      narrowedEdges.map((edge) => ({ src: edge.src.unitId, dst: edge.dst.unitId })),
    );
  // D1：端口=边端点方向聚合（端口表不在项目文件——流体色挂账段二）
  const sourcePorts = new Map<string, Set<string>>();
  const targetPorts = new Map<string, Set<string>>();
  for (const id of unitIds) {
    sourcePorts.set(id, new Set());
    targetPorts.set(id, new Set());
  }
  for (const edge of narrowedEdges) {
    sourcePorts.get(edge.src.unitId)?.add(edge.src.portId);
    targetPorts.get(edge.dst.unitId)?.add(edge.dst.portId);
  }
  const nodes: UnitFlowNode[] = unitIds.map((unitId) => {
    const params = nodesRaw[unitId] as Record<string, unknown>;
    const kindRaw = params["kind"];
    return {
      id: unitId,
      type: "unit",
      position: positions.get(unitId) ?? { x: 0, y: 0 },
      data: {
        unitId,
        kind: typeof kindRaw === "string" ? kindRaw : null,
        sourcePorts: [...(sourcePorts.get(unitId) ?? [])].sort(),
        targetPorts: [...(targetPorts.get(unitId) ?? [])].sort(),
      },
    };
  });
  const edges: FlowEdge[] = narrowedEdges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.src.unitId,
    sourceHandle: edge.src.portId,
    target: edge.dst.unitId,
    targetHandle: edge.dst.portId,
    markerEnd: { type: "arrowclosed" },
    ...(edge.recycle ? { style: { strokeDasharray: RECYCLE_DASH } } : {}),
  }));
  return { nodes, edges };
}
