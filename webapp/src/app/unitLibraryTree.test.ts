/**
 * 单元库树纯函数单测：四线分组/内置排末/搜索过滤/叶 key 反查（M2 浏览面）。
 *
 * 输入:  unitLibraryTree.ts 的 buildLibraryTree/filterLibraryTree/
 *        findUnitByNodeKey 三函数（node 环境——自制目录样例，形态对齐
 *        现网 36 条：四线各≥1+builtin≥2）
 * 输出:  断言：组序=映射序+内置末+未知线「其他」防御；组标题计数形态；
 *        builtin 不落业务线组；组内序透传不重排；空目录=空数组；过滤
 *        空串原样/name_zh 与 unit_id 子串命中/大小写不敏感/空组剔除/
 *        无命中空数组；叶命中引用相等/组 key 与未命中 null
 *
 * 规格说明（M2 批，简报 §四；app 层既有形态=projectParam.test.ts——
 *   纯函数 node 直测，组件薄壳不进 vitest 零 jsdom 红线）：
 *   - 样例 fixture 自制非录制：树结构面只依赖 unit_id/name_zh/
 *     business_line/kind 四字段（params/ports 属 Drawer 详情面非树面）；
 *   - 空目录钉死=空数组（简报 §四.3 定稿——零噪声，组标题全由数据
 *     驱动，空线不建组）；
 *   - 过滤空串钉死=深度相等（防实现绑引用——同一引用或等值副本皆过）。
 */
import { describe, expect, it } from "vitest";

import type { UnitMetaEntry } from "../shared/api/generated/model/unitMetaEntry";
import type { UnitMetaEntryKind } from "../shared/api/generated/model/unitMetaEntryKind";
import {
  buildLibraryTree,
  filterLibraryTree,
  findUnitByNodeKey,
} from "./unitLibraryTree";

/** 目录样例工厂（必填字段直给——kind 缺省 unit）。 */
function makeUnit(
  unit_id: string,
  name_zh: string,
  business_line: string,
  kind: UnitMetaEntryKind = "unit",
): UnitMetaEntry {
  return { unit_id, name_zh, business_line, kind };
}

/** 形态对齐现网 36 条的自制样例（四线各≥1+builtin≥2——builtin 两件
 * 刻意声明不同业务线：钉「builtin 一律归内置组」防御面）。 */
const CATALOG: readonly UnitMetaEntry[] = [
  makeUnit("municipal.a2o", "AAO 生物池", "municipal"),
  makeUnit("municipal.primary_clarifier", "初沉池", "municipal"),
  makeUnit("conveyance.lift_station", "提升泵站", "conveyance"),
  makeUnit("mine_water.dmf", "DMF 过滤器", "mine_water"),
  makeUnit("sludge.thickener", "污泥浓缩池", "sludge"),
  makeUnit("municipal_input", "市政进水", "municipal", "builtin"),
  makeUnit("junction", "汇合节点", "conveyance", "builtin"),
];

describe("M2 buildLibraryTree（目录→四线分组树+内置排末）", () => {
  it("组序=四线映射序+「内置节点」排末（与数据出现序无关）", () => {
    const nodes = buildLibraryTree([...CATALOG].reverse());
    expect(nodes.map((node) => node.key)).toEqual([
      "group:municipal",
      "group:conveyance",
      "group:mine_water",
      "group:sludge",
      "group:builtin",
    ]);
  });

  it("组标题=「中文名 (N)」计数形态（叶数直数）", () => {
    const nodes = buildLibraryTree(CATALOG);
    expect(nodes.map((node) => node.title)).toEqual([
      "市政污水 (2)",
      "输送提升 (1)",
      "矿井水 (1)",
      "污泥处理 (1)",
      "内置节点 (2)",
    ]);
  });

  it("kind=builtin 一律归内置组——不落业务线组（即使声明 business_line）", () => {
    const nodes = buildLibraryTree(CATALOG);
    const municipal = nodes.find((node) => node.key === "group:municipal");
    const builtin = nodes.find((node) => node.key === "group:builtin");
    expect(municipal?.children.map((leaf) => leaf.key)).toEqual([
      "municipal.a2o",
      "municipal.primary_clarifier",
    ]);
    expect(builtin?.children.map((leaf) => leaf.key)).toEqual([
      "municipal_input",
      "junction",
    ]);
  });

  it("组内序=服务端既有序（透传不重排——倒序入参保持倒序）", () => {
    const nodes = buildLibraryTree([...CATALOG].reverse());
    const municipal = nodes.find((node) => node.key === "group:municipal");
    expect(municipal?.children.map((leaf) => leaf.key)).toEqual([
      "municipal.primary_clarifier",
      "municipal.a2o",
    ]);
  });

  it("未知 business_line →「其他」组防御（序=四线后、内置前）", () => {
    const nodes = buildLibraryTree([
      ...CATALOG,
      makeUnit("future.desal", "海水淡化单元", "desalination"),
    ]);
    expect(nodes.map((node) => node.key)).toEqual([
      "group:municipal",
      "group:conveyance",
      "group:mine_water",
      "group:sludge",
      "group:other",
      "group:builtin",
    ]);
    expect(nodes[4]?.title).toBe("其他 (1)");
  });

  it("空 units → 空数组（零噪声——组标题全由数据驱动）", () => {
    expect(buildLibraryTree([])).toEqual([]);
  });
});

describe("M2 filterLibraryTree（unit_id/name_zh 子串过滤）", () => {
  it("空串/纯空白 → 原样（深度相等——防实现绑引用）", () => {
    const tree = buildLibraryTree(CATALOG);
    expect(filterLibraryTree(tree, "")).toEqual(tree);
    expect(filterLibraryTree(tree, "   ")).toEqual(tree);
  });

  it("命中 name_zh：空组剔除+计数=过滤后", () => {
    const filtered = filterLibraryTree(buildLibraryTree(CATALOG), "污泥");
    expect(filtered.map((node) => node.key)).toEqual(["group:sludge"]);
    expect(filtered[0]?.title).toBe("污泥处理 (1)");
    expect(filtered[0]?.children.map((leaf) => leaf.key)).toEqual([
      "sludge.thickener",
    ]);
  });

  it("命中 unit_id：子串匹配+同组多命中计数=过滤后", () => {
    const one = filterLibraryTree(buildLibraryTree(CATALOG), "lift");
    expect(one.map((node) => node.key)).toEqual(["group:conveyance"]);
    expect(one[0]?.children.map((leaf) => leaf.key)).toEqual([
      "conveyance.lift_station",
    ]);
    const both = filterLibraryTree(buildLibraryTree(CATALOG), "municipal.");
    expect(both.map((node) => node.key)).toEqual(["group:municipal"]);
    expect(both[0]?.title).toBe("市政污水 (2)");
  });

  it("大小写不敏感：大写搜索词命中小写 unit_id（name_zh 不含该串）", () => {
    const filtered = filterLibraryTree(buildLibraryTree(CATALOG), "A2O");
    expect(filtered.map((node) => node.key)).toEqual(["group:municipal"]);
    expect(filtered[0]?.children.map((leaf) => leaf.key)).toEqual([
      "municipal.a2o",
    ]);
  });

  it("无命中 → 空数组", () => {
    expect(filterLibraryTree(buildLibraryTree(CATALOG), "不存在的单元")).toEqual(
      [],
    );
  });
});

describe("M2 findUnitByNodeKey（叶 key 反查 entry）", () => {
  it("叶命中：unit_id → 同一 entry（引用相等）", () => {
    const thickener = CATALOG.find(
      (unit) => unit.unit_id === "sludge.thickener",
    );
    expect(thickener).toBeDefined();
    expect(findUnitByNodeKey(CATALOG, "sludge.thickener")).toBe(thickener);
  });

  it("组 key → null；未命中 key → null", () => {
    expect(findUnitByNodeKey(CATALOG, "group:municipal")).toBeNull();
    expect(findUnitByNodeKey(CATALOG, "no.such.unit")).toBeNull();
  });
});
