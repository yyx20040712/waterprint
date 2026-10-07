/**
 * 模型树（M1 批 2026-10-06——左列上区：静态导航骨架，B-1 六节点单源）。
 *
 * 输入:  onNavigate(target: TabTarget)（导航回调——App setTab 接线：工艺流
 *        →canvas/厂区布置→siteplan/研究→studio.study/结果.纵断→elevation/
 *        结果.概算·对比·可信度·图纸→studio 同名子面）+本地过滤词（受控）
 * 输出:  左列上区容器（data-region="model-tree"：根区标题「模型」+静态
 *        六节点计数+Input.Search 过滤框+antd Tree〔unitLibrary 同款受控
 *        形态〕；管网定线节点=默认折叠+「管网预留」挂起徽标
 *        〔data-testid="wp-pending-network"〕+展开子节点=挂起说明文案）
 *
 * 规格说明（draft-ia-v3 §3 B-1 L36-41 六节点逐字+mapping-2b4 M1 行；
 *   live 单元子节点/树→Settings 联动=M2「联动细化」批——M1 静态骨架）：
 *   - 六节点（v3 逐字）：项目〔原始数据·全局假设〕/工艺流〔单元节点=
 *     画布联动〕/厂区布置〔红线·道路走廊·构筑物·标高〕/管网定线〔预留·
 *     默认可见但折叠+挂起徽标〕/研究〔枚举任务·敏感性·无解诊断〕/结果
 *     〔纵断·概算·对比·可信度·图纸〕——中括号注记=tooltip 悬浮非常显；
 *   - 管网定线挂起位（v3 B-3 管网线①挂起展示语义——判据 4 锚①）：
 *     defaultExpandedKeys 不含+Tag 徽标；展开子节点=静态说明文案
 *     （定线/水力计算/平纵图纸——落位说明，不实现）；
 *   - 项目/厂区布置子节点=静态文本（M1 无导航目标——title 悬浮注明
 *     「后续批次接入」）；工艺流/研究=父节点自身导航（子面内容 M2/M6）；
 *   - 过滤=标题+注记双侧 toLowerCase 子串（unitLibraryTree 同款口径；
 *     M1=本地静态节点过滤——命中保留祖先链，过滤态自动展开全部命中）；
 *   - 受控形态沿 unitLibrary：expandedKeys/selectedKeys 受控+onSelect
 *     导航分派（nav 缺席节点=纯静态零分派）。
 */
import { useMemo, useState } from "react";
import { Empty, Input, Tag, Tree, Typography } from "antd";
import type { TreeDataNode } from "antd";

import type { TabTarget } from "./router";

/** 静态节点模型（key=树键；nav=导航目标缺席即静态文本；pending=挂起徽标）。 */
interface ModelNode {
  key: string;
  title: string;
  /** tooltip 悬浮注记（v3 中括号文案/接入批次说明——非常显面）。 */
  note?: string;
  /** 挂起徽标（管网定线——判据 4 锚①）。 */
  pending?: boolean;
  nav?: TabTarget;
  children?: ModelNode[];
}

/** 后续批次接入注记（静态子节点通用 tooltip——M1 无导航目标）。 */
const LATER_BATCH_NOTE = "后续批次接入";

/** 六节点静态骨架（v3 B-1 逐字——M1 冻结面，live 化归 M2 联动批）。 */
const MODEL_NODES: ModelNode[] = [
  {
    key: "project",
    title: "项目",
    note: "原始数据·全局假设",
    children: [
      { key: "project:raw", title: "原始数据", note: LATER_BATCH_NOTE },
      { key: "project:assumptions", title: "全局假设", note: LATER_BATCH_NOTE },
    ],
  },
  {
    key: "process",
    title: "工艺流",
    note: "单元节点=画布联动（M2 联动批）",
    nav: { slot: "canvas" },
  },
  {
    key: "site",
    title: "厂区布置",
    note: "红线·道路走廊·构筑物·标高",
    nav: { slot: "siteplan" },
    children: [
      { key: "site:redline", title: "红线", note: LATER_BATCH_NOTE },
      { key: "site:corridor", title: "道路走廊", note: LATER_BATCH_NOTE },
      { key: "site:structures", title: "构筑物", note: LATER_BATCH_NOTE },
      { key: "site:level", title: "标高", note: LATER_BATCH_NOTE },
    ],
  },
  {
    key: "network",
    title: "管网定线",
    note: "预留——定线挂起于厂区布置红线/管线走廊折线；水力计算/平纵图纸随后续管网批",
    pending: true,
    children: [
      { key: "network:route", title: "定线（挂起）", note: "管网批落位" },
      { key: "network:hydraulic", title: "水力计算（挂起）", note: "管网批落位" },
      { key: "network:sheets", title: "平纵图纸（挂起）", note: "管网批落位" },
    ],
  },
  {
    key: "study",
    title: "研究",
    note: "枚举任务·敏感性·无解诊断",
    nav: { slot: "studio", subface: "study" },
    children: [
      { key: "study:enum", title: "枚举任务", note: "studio.study 内容面 M6 批" },
      { key: "study:sensitivity", title: "敏感性", note: "studio.study 内容面 M6 批" },
      { key: "study:diagnosis", title: "无解诊断", note: "studio.study 内容面 M6 批" },
    ],
  },
  {
    key: "results",
    title: "结果",
    note: "纵断·概算·对比·可信度·图纸",
    children: [
      { key: "results:profile", title: "纵断", nav: { slot: "elevation" } },
      { key: "results:cost", title: "概算", nav: { slot: "studio", subface: "cost" } },
      { key: "results:compare", title: "对比", nav: { slot: "studio", subface: "compare" } },
      { key: "results:trust", title: "可信度", nav: { slot: "studio", subface: "trust" } },
      { key: "results:drawings", title: "图纸", nav: { slot: "studio", subface: "drawings" } },
    ],
  },
];

/** 静态节点计数（根区标题行——「模型」+六节点）。 */
const NODE_COUNT = MODEL_NODES.length;

/** key→节点索引（onSelect 分派反查——模块级一次构建）。 */
const NODE_BY_KEY = new Map<string, ModelNode>(
  MODEL_NODES.flatMap(function walk(node: ModelNode): [string, ModelNode][] {
    return [[node.key, node], ...(node.children ?? []).flatMap(walk)];
  }),
);

/** 过滤（标题+注记双侧 toLowerCase 子串——unitLibraryTree 同款口径）：
 *  命中节点保留祖先链；子命中则父保留（导航父节点过滤期仍可点）。 */
function filterNodes(nodes: readonly ModelNode[], query: string): ModelNode[] {
  const q = query.trim().toLowerCase();
  if (q === "") {
    return nodes as ModelNode[];
  }
  const out: ModelNode[] = [];
  for (const node of nodes) {
    const selfHit =
      node.title.toLowerCase().includes(q) ||
      (node.note ?? "").toLowerCase().includes(q);
    const children = node.children ? filterNodes(node.children, query) : [];
    if (selfHit || children.length > 0) {
      out.push(children.length > 0 ? { ...node, children } : { ...node, children: [] });
    }
  }
  return out;
}

/** 节点→antd TreeDataNode（title 挂 tooltip/徽标——注记与常显文案分策）。 */
function toTreeData(nodes: readonly ModelNode[]): TreeDataNode[] {
  return nodes.map((node) => ({
    key: node.key,
    title: (
      <span title={node.note}>
        {node.title}
        {node.pending ? (
          <Tag
            data-testid="wp-pending-network"
            style={{ marginLeft: 6, marginRight: 0, fontSize: 11, lineHeight: "16px" }}
          >
            管网预留
          </Tag>
        ) : null}
      </span>
    ),
    children: node.children && node.children.length > 0 ? toTreeData(node.children) : undefined,
  }));
}

/** 过滤态自动展开键（命中子树全展开——过滤可见性优先于折叠记忆）。 */
function allKeys(nodes: readonly ModelNode[]): string[] {
  return nodes.flatMap((node) => [node.key, ...(node.children ? allKeys(node.children) : [])]);
}

export function ModelTree({ onNavigate }: { onNavigate: (target: TabTarget) => void }) {
  const [filter, setFilter] = useState("");
  const [expandedKeys, setExpandedKeys] = useState<string[]>(["project", "results"]);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  // 过滤=受控：词变即重建（命中链保留）；空词=原样六节点
  const visibleNodes = useMemo(() => filterNodes(MODEL_NODES, filter), [filter]);
  const treeData = useMemo(() => toTreeData(visibleNodes), [visibleNodes]);
  const filtering = filter.trim() !== "";

  return (
    <section
      data-region="model-tree"
      style={{ display: "flex", flexDirection: "column", minHeight: 0, height: "100%" }}
    >
      {/* 根区标题行：模型+静态六节点计数（live 计数归 M2） */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "6px 10px 4px",
          flex: "none",
        }}
      >
        <Typography.Text strong>模型</Typography.Text>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {NODE_COUNT} 节点
        </Typography.Text>
      </div>
      <div style={{ padding: "0 10px 6px", flex: "none" }}>
        <Input.Search
          size="small"
          allowClear
          placeholder="过滤节点/注记"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        />
      </div>
      {visibleNodes.length === 0 ? (
        <Empty description="无匹配节点" style={{ marginTop: 24 }} />
      ) : (
        <div style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
          <Tree
            blockNode
            treeData={treeData}
            expandedKeys={filtering ? allKeys(visibleNodes) : expandedKeys}
            selectedKeys={selectedKeys}
            onExpand={(keys) => {
              // 过滤态展开=allKeys 派生不写记忆（清词不污染折叠记忆）
              if (!filtering) {
                setExpandedKeys(keys.map(String));
              }
            }}
            onSelect={(keys, info) => {
              const next = keys.map(String);
              setSelectedKeys(next);
              const node = NODE_BY_KEY.get(String(info.node.key));
              if (node !== undefined && node.nav !== undefined) {
                onNavigate(node.nav);
              }
            }}
          />
        </div>
      )}
    </section>
  );
}
