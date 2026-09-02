/**
 * 单元库树纯函数：UnitCatalog 目录 → antd Tree 数据（M2 浏览面组装层）。
 *
 * 输入:  GET /api/units 的 UnitMetaEntry[]（生成物类型透传）+搜索词
 *        （unit_id/name_zh 子串）+叶节点 key
 * 输出:  LibraryTreeNode[]（四线分组+未知线「其他」防御组+「内置节点」组
 *        排末——组标题「中文名 (N)」计数随过滤更新）；过滤副本（空组剔除、
 *        计数=过滤后）；叶 key 反查 entry（非叶/未命中=null）
 *
 * 规格说明（M2 批，简报 §一.5/§一.6/§三；设计真源
 *   reports/units-browser-design.md）：
 *   - 分组序=BUSINESS_LINE_ZH 声明序（municipal/conveyance/mine_water/
 *     sludge）→未知线「其他」→「内置节点」末位；kind=builtin 一律归
 *     内置组（即使声明 business_line——现网 4 内置不落业务线组）；
 *   - 组内序=服务端既有序（unit_id 序——透传不重排）；
 *   - 空目录=空数组（组标题全由数据驱动——空线不建组零噪声）；
 *   - 过滤=双侧 toLowerCase 子串（unit_id/name_zh）；空/纯空白=原样
 *     分组结构；无命中=空数组；
 *   - 纯函数零 React 零 antd 依赖——node 直测（app 层 projectParam 形态）。
 */
import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";

/** 四线中文名映射（展示层常量，非业务复制——分组标题翻译）。 */
export const BUSINESS_LINE_ZH: Record<string, string> = {
  municipal: "市政污水",
  conveyance: "输送提升",
  mine_water: "矿井水",
  sludge: "污泥处理",
};

/** antd Tree 数据节点(结构面只依赖 title/key/children 三键)。 */
export interface LibraryTreeNode {
  title: string;
  key: string;
  children: LibraryTreeNode[];
}

/** 组节点 key 前缀（与叶 key=unit_id 区分——findUnitByNodeKey 非叶判据）。 */
const GROUP_KEY_PREFIX = "group:";

/** 内置组（kind=builtin 归属——恒排末位）。 */
const BUILTIN_GROUP_KEY = "group:builtin";
const BUILTIN_GROUP_TITLE = "内置节点";

/** 未知线防御组（business_line 映射外兜底——现网 36 条无此面）。 */
const OTHER_GROUP_KEY = "group:other";
const OTHER_GROUP_TITLE = "其他";

/** 组标题尾缀计数「 (N)」剥离（过滤后按剩余叶数重算）。 */
const GROUP_COUNT_SUFFIX = / \(\d+\)$/;

/** 组节点骨架（children 由装填方 push）。 */
function groupNode(key: string, title: string): LibraryTreeNode {
  return { title, key, children: [] };
}

/** 叶节点（title=显示名 name_zh，key=unit_id——零推导直出）。 */
function leafNode(unit: UnitMetaEntry): LibraryTreeNode {
  return { title: unit.name_zh, key: unit.unit_id, children: [] };
}

/** 组标题计数形态「基名 (N)」。 */
function withCount(baseTitle: string, count: number): string {
  return `${baseTitle} (${count})`;
}

/** 目录→树:四线分组(business_line 序=municipal/conveyance/mine_water/sludge)
 * +未知线「其他」防御组+「内置节点」组排末(kind=builtin 一律归此组);
 * 组内序=服务端既有序(unit_id 序——透传不重排);组标题含计数「中文名 (N)」。 */
export function buildLibraryTree(
  units: readonly UnitMetaEntry[],
): LibraryTreeNode[] {
  if (units.length === 0) {
    return [];
  }
  // 四线组按映射声明序预建（与数据出现序无关——组序钉死）
  const lineGroups = new Map<string, LibraryTreeNode>();
  for (const [line, title] of Object.entries(BUSINESS_LINE_ZH)) {
    lineGroups.set(line, groupNode(`${GROUP_KEY_PREFIX}${line}`, title));
  }
  const otherGroup = groupNode(OTHER_GROUP_KEY, OTHER_GROUP_TITLE);
  const builtinGroup = groupNode(BUILTIN_GROUP_KEY, BUILTIN_GROUP_TITLE);

  for (const unit of units) {
    if (unit.kind === "builtin") {
      builtinGroup.children.push(leafNode(unit));
      continue;
    }
    const group = lineGroups.get(unit.business_line);
    if (group !== undefined) {
      group.children.push(leafNode(unit));
    } else {
      otherGroup.children.push(leafNode(unit));
    }
  }

  // 空线不建组（数据驱动零噪声）；计数=装填后叶数
  const nodes = [...lineGroups.values(), otherGroup, builtinGroup].filter(
    (group) => group.children.length > 0,
  );
  for (const group of nodes) {
    group.title = withCount(group.title, group.children.length);
  }
  return nodes;
}

/** 过滤:query 空/纯空白=原样返回同一分组结构;否则 unit_id/name_zh 子串
 * (大小写不敏感)匹配,空组剔除,计数=过滤后。 */
export function filterLibraryTree(
  nodes: readonly LibraryTreeNode[],
  query: string,
): LibraryTreeNode[] {
  const needle = query.trim().toLowerCase();
  if (needle === "") {
    return [...nodes];
  }
  const filtered: LibraryTreeNode[] = [];
  for (const group of nodes) {
    // 叶命中面=key(unit_id)+title(name_zh) 双字段（组标题不参与匹配）
    const children = group.children.filter(
      (leaf) =>
        leaf.key.toLowerCase().includes(needle) ||
        leaf.title.toLowerCase().includes(needle),
    );
    if (children.length === 0) {
      continue;
    }
    const baseTitle = group.title.replace(GROUP_COUNT_SUFFIX, "");
    filtered.push({
      ...group,
      title: withCount(baseTitle, children.length),
      children,
    });
  }
  return filtered;
}

/** 叶节点 key 反查单元(unit_id→entry);非叶/未命中=null。 */
export function findUnitByNodeKey(
  units: readonly UnitMetaEntry[],
  key: string,
): UnitMetaEntry | null {
  if (key.startsWith(GROUP_KEY_PREFIX)) {
    return null;
  }
  return units.find((unit) => unit.unit_id === key) ?? null;
}
