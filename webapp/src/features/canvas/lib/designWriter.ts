/**
 * design 写侧纯函数（P0-3 画布编辑最小闭环——briefs/task-c2-edit-plan.md）。
 *
 * 输入:  design 草稿四面（nodes/edges/site.structures/checked_units——
 *        beginEdit 快照派生）+编辑动作参数（加单元/连线/删除/拖拽位）
 * 输出:  新草稿（不可变更新——store 薄壳唯一数据通道）；会话视图位合成
 *        （draftViewLayout——投影喂给 projectFlow 的 view.layout 面）
 *
 * 规格说明（task-c2-edit-plan §一/§二 红线五条）：
 *   - 红线①：projectFlow.ts 投影层只读不破——本件=design 数据操作层
 *     （编辑层与几何推导分层，投影零 import 本件、本件只复用其
 *     fallbackLayout 拓扑兜底作新节点缺位坐标源）；
 *   - 红线③：零默认值填充——空参节点写 {} 原样序列化，内置节点只写
 *     {kind}（严禁 TS 侧补默认成第二业务源——core manifest 默认兜底）；
 *   - 红线⑤：草稿=beginEdit 时点快照，服务端后续 refetch 不回流草稿
 *     （store 层防线注记——本件纯函数无此面）；
 *   - 删除级联（D3 悬空即拒防线）：节点删→所连边清+site.structures
 *     键清+checked_units 条清（site 悬空=parse_project 拒——前置防）；
 *   - 多实例 id=呈裁③ 甲案 `_2` 后缀递增（汇流/多系列可读可寻址）；
 *     连线同对去重（幂等——重复拖拽同对不产生平行重复边）。
 */

/** 边端点（design.edges 原生形态——{unit_id,port_id} 蛇键沿 schema）。 */
export type DesignEdgeEndpoint = { unit_id: string; port_id: string };

// 拓扑兜底复用（投影层只读不破红线①——仅 import 其纯函数，不反向）
import { fallbackLayout } from "./projectFlow";

/** 边（design.edges 元素——recycle 可选沿 schema 宽容面）。 */
export type DesignEdgeJson = {
  src: DesignEdgeEndpoint;
  dst: DesignEdgeEndpoint;
  recycle?: boolean;
};

/** 编辑草稿（design 可变四面+会话视图位——positions 不入保存体）。 */
export type DesignDraft = {
  nodes: Record<string, Record<string, unknown>>;
  edges: DesignEdgeJson[];
  siteStructures: Record<string, Record<string, unknown>>;
  checkedUnits: string[];
  positions: Record<string, { x: number; y: number }>;
};

/** 布局坐标（view.layout 条目形态）。 */
export type LayoutPos = { x: number; y: number };

/**
 * 多实例 id 派生（呈裁③ 甲案）：`municipal_aao`→`municipal_aao_2`→
 * `_3`…首例无后缀直用；已被占用的号顺延（`_2` 被占则试 `_3`）。
 */
export function nextInstanceId(
  nodes: Readonly<Record<string, unknown>>,
  unitId: string,
): string {
  if (!(unitId in nodes)) {
    return unitId;
  }
  for (let n = 2; ; n += 1) {
    const candidate = `${unitId}_${n}`;
    if (!(candidate in nodes)) {
      return candidate;
    }
  }
}

/**
 * 加单元（呈裁②/③+红线③）：包单元=`{}` 空参原样；内置=`{kind}` 结构
 * 元数据（design 键=kind 值——app_assembly 装配口径 D5）。
 *
 * **引擎 v1 单实例约束（实装修正——E2E 揪出）**：包单元装配按
 * node_id=注册表键**精确匹配**（app_assembly.assemble），`_2` 实例
 * 装配期必拒（不在注册表且无 kind）——包单元已在场=拒绝再加
 * （nodeId=null，UI 述因）；内置节点值带 kind 自描述，`_2` 多实例
 * 全支持（呈裁③ 落地面）。包多实例=引擎扩展挂账（本批不破装配面）。
 */
export function addUnit(
  draft: DesignDraft,
  unitId: string,
  kind: "unit" | "builtin",
): { draft: DesignDraft; nodeId: string | null } {
  if (kind === "unit" && unitId in draft.nodes) {
    return { draft, nodeId: null };
  }
  const nodeId = nextInstanceId(draft.nodes, unitId);
  const value: Record<string, unknown> = kind === "builtin" ? { kind: unitId } : {};
  return {
    draft: { ...draft, nodes: { ...draft.nodes, [nodeId]: value } },
    nodeId,
  };
}

/** 同边判等（src/dst 端点双等值——recycle 标不参与判等）。 */
function sameEdge(
  edge: DesignEdgeJson,
  src: DesignEdgeEndpoint,
  dst: DesignEdgeEndpoint,
): boolean {
  return (
    edge.src.unit_id === src.unit_id &&
    edge.src.port_id === src.port_id &&
    edge.dst.unit_id === dst.unit_id &&
    edge.dst.port_id === dst.port_id
  );
}

/**
 * 连线（onConnect 通道）：design.edges 追加 {src,dst} 蛇键原生形态；
 * 同对已存在=幂等返回原草稿（重复拖拽不产生平行边）。端点规则判断
 * 不在此层（红线④——规则判断唯一源=校验时点 core validate）。
 */
export function connectEdge(
  draft: DesignDraft,
  src: DesignEdgeEndpoint,
  dst: DesignEdgeEndpoint,
): DesignDraft {
  if (draft.edges.some((edge) => sameEdge(edge, src, dst))) {
    return draft;
  }
  return { ...draft, edges: [...draft.edges, { src, dst }] };
}

/**
 * 删边（键盘删除通道）：按端点四值匹配移除（React Flow 边 id=投影
 * 序号不稳定，端点对=稳定判据）。
 */
export function deleteEdge(
  draft: DesignDraft,
  src: DesignEdgeEndpoint,
  dst: DesignEdgeEndpoint,
): DesignDraft {
  return {
    ...draft,
    edges: draft.edges.filter((edge) => !sameEdge(edge, src, dst)),
  };
}

/**
 * 删节点（级联清——设计书 §一.3）：①所连边（任一端命中即清）；
 * ②site.structures 键（D3 悬空即拒——parse_project 前置防线）；
 * ③checked_units 条（装配期资格校验悬空防）；④会话拖拽位。
 */
export function deleteNodes(draft: DesignDraft, ids: readonly string[]): DesignDraft {
  const removed = new Set(ids);
  const siteStructures = { ...draft.siteStructures };
  const positions = { ...draft.positions };
  for (const id of removed) {
    delete siteStructures[id];
    delete positions[id];
  }
  return {
    nodes: Object.fromEntries(
      Object.entries(draft.nodes).filter(([id]) => !removed.has(id)),
    ),
    edges: draft.edges.filter(
      (edge) => !removed.has(edge.src.unit_id) && !removed.has(edge.dst.unit_id),
    ),
    siteStructures,
    checkedUnits: draft.checkedUnits.filter((id) => !removed.has(id)),
    positions,
  };
}

/** 会话拖拽位写入（onNodesChange position 通道——视图态不进保存体）。 */
export function setPosition(
  draft: DesignDraft,
  id: string,
  position: LayoutPos,
): DesignDraft {
  return { ...draft, positions: { ...draft.positions, [id]: position } };
}

/**
 * 草稿合成项目体（编辑层正门）：基座 raw+草稿四面→可投影/可保存体
 * （view.layout=会话合成面——draftViewLayout 全覆盖保证 readLayout
 * 整体采纳）。基座裁量（红线⑤ 快照隔离的消费面分野）：投影侧喂
 * beginEdit 快照 baseRaw（编辑期视觉连续——服务端 refetch 不回流）；
 * 保存/校验侧喂时点最新 raw（非 design 面最新——不回写陈旧面）。
 */
export function draftProjectRaw(
  baseRaw: Readonly<Record<string, unknown>>,
  draft: DesignDraft,
): Record<string, unknown> {
  const baseView = (baseRaw["view"] ?? {}) as Record<string, unknown>;
  const baseDesign = (baseRaw["design"] ?? {}) as Record<string, unknown>;
  const baseSite = (baseDesign["site"] ?? {}) as Record<string, unknown>;
  const baseLayout = (baseView["layout"] ?? {}) as Record<string, unknown>;
  const nodeIds = Object.keys(draft.nodes).sort();
  const layout = draftViewLayout(
    nodeIds,
    draft.edges.map((edge) => ({ src: edge.src.unit_id, dst: edge.dst.unit_id })),
    baseLayout,
    draft.positions,
  );
  return {
    ...baseRaw,
    design: {
      ...baseDesign,
      nodes: draft.nodes,
      edges: draft.edges,
      site: { ...baseSite, structures: draft.siteStructures },
      checked_units: draft.checkedUnits,
    },
    view: { ...baseView, layout },
  };
}

/** 窄化：view.layout 条目合规（双有限数——projectFlow.readLayout 同判据）。 */
function narrowLayoutEntry(entry: unknown): LayoutPos | null {
  if (
    typeof entry === "object" &&
    entry !== null &&
    !Array.isArray(entry) &&
    typeof (entry as Record<string, unknown>)["x"] === "number" &&
    typeof (entry as Record<string, unknown>)["y"] === "number" &&
    Number.isFinite((entry as Record<string, unknown>)["x"]) &&
    Number.isFinite((entry as Record<string, unknown>)["y"])
  ) {
    return {
      x: (entry as Record<string, unknown>)["x"] as number,
      y: (entry as Record<string, unknown>)["y"] as number,
    };
  }
  return null;
}

/**
 * 会话布局合成（编辑层——投影层只读红线①的分面兑现）：新节点缺位坐标
 * =fallbackLayout 拓扑兜底派生；基座持久位（view.layout 既有条目）与
 * 会话拖拽位逐级覆盖（拖拽>持久>兜底）。产全量覆盖的 layout 喂
 * projectFlow（readLayout 全覆盖才整体采纳——合成保证全覆盖）。
 */
export function draftViewLayout(
  nodeIds: readonly string[],
  edges: readonly { src: string; dst: string }[],
  baseLayout: Readonly<Record<string, unknown>>,
  positions: Readonly<Record<string, LayoutPos>>,
): Record<string, LayoutPos> {
  const fallback = fallbackLayout([...nodeIds], [...edges]);
  const layout: Record<string, LayoutPos> = {};
  for (const id of nodeIds) {
    layout[id] = fallback.get(id) ?? { x: 0, y: 0 };
    const base = narrowLayoutEntry(baseLayout[id]);
    if (base !== null) {
      layout[id] = base;
    }
    const session = positions[id];
    if (session !== undefined) {
      layout[id] = session;
    }
  }
  return layout;
}
