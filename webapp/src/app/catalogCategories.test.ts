/**
 * 分级目录映射纯函数单测（B1 骨架批 2026-10-09——36 单元×5 一级类+结构
 * 节点尾组——任务书 §二.④ 覆盖核验表逐行对账；本件在 app 层因需对账
 * features/canvas thumbnailGlyph 键集——features 禁 import app 分层红线）。
 *
 * 输入:  catalogCategories.ts 的 CATALOG_CATEGORIES/categoryOfUnit/
 *        buildCatalogGroups+features/canvas/components/thumbnailGlyph 的
 *        THUMBNAIL_GLYPH_KINDS（node 环境——纯函数面）
 * 输出:  断言族：①映射表全域（36 unit_id 恰一次全覆盖+六类计数
 *        11/3/3/8/7/4+类序）②buildCatalogGroups（服务端序保持+组恒六+
 *        未映射 id 跳过——扩值维护面显式记档）③缩略图键集对账
 *        （THUMBNAIL_GLYPH_KINDS 与映射表全域双向恒等——DoD §四.5
 *        「目录全量×键集对账」）
 *
 * 规格说明（B1 任务书 §二.④ 依据）：
 *   - 五一级类映射（矿井水/污泥=业务线直映；市政+输送 17 件按处理工程
 *     阶段划级；builtin 4 件=画布结构节点目录尾组保持可达）；
 *   - 二级目录=组内具体工艺（unit name_zh 直出，服务端序）；
 *   - 键集对账防两向漏：新 unit 漏登记目录=amount 侧红；glyph 漏绘=
 *     kinds 侧红（双向恰等断言）。
 */
import { describe, expect, it } from "vitest";

import {
  buildCatalogGroups,
  CATALOG_CATEGORIES,
  categoryOfUnit,
  type CatalogGroupUnit,
} from "./catalogCategories";
import { THUMBNAIL_GLYPH_KINDS } from "../features/canvas/components/thumbnailGlyph";

/** 目录夹具条目最小面（UnitMetaEntry 消费字段子集——形态对齐生成类型）。 */
function unit(unitId: string, nameZh: string, kind: "unit" | "builtin" = "unit"): CatalogGroupUnit & {
  business_line: string;
} {
  const line = unitId.startsWith("mine_water")
    ? "mine_water"
    : unitId.startsWith("sludge")
      ? "sludge"
      : unitId.startsWith("conveyance")
        ? "conveyance"
        : "municipal";
  return { unit_id: unitId, name_zh: nameZh, kind, business_line: line };
}

/** 全量 36 件夹具（服务端序=unit_id 字典序+内置排末——真实目录实dump 形状）。 */
const FIXTURE_36 = [
  unit("conveyance_jipeishuijing", "集配水井"),
  unit("conveyance_jishuijing", "集水井"),
  unit("conveyance_peishuijing", "配水井"),
  unit("conveyance_peishuiqu", "配水渠"),
  unit("mine_water_chenshachi", "平流沉砂池"),
  unit("mine_water_cifenli", "磁分离"),
  unit("mine_water_gaomidu", "高密沉淀"),
  unit("mine_water_input", "矿井水输入"),
  unit("mine_water_ningjiao", "混凝反应"),
  unit("mine_water_tiaojiechi", "调节池"),
  unit("mine_water_vxinglvchi", "V型滤池"),
  unit("mine_water_ziwai", "紫外消毒"),
  unit("municipal_aao", "AAO 生物池"),
  unit("municipal_bashi_jiliangcao", "巴歇尔计量槽"),
  unit("municipal_cass", "CASS 生物池"),
  unit("municipal_chenshachi", "旋流沉砂池"),
  unit("municipal_chuchenchi", "辐流初沉池"),
  unit("municipal_cugeshan", "粗格栅"),
  unit("municipal_erchunchi", "辐流二沉池"),
  unit("municipal_gaomidu", "高密沉淀池"),
  unit("municipal_tiaojiechi", "调节池"),
  unit("municipal_vxinglvchi", "V型滤池"),
  unit("municipal_wushui_tisheng", "污水提升泵房"),
  unit("municipal_xigeshan", "细格栅"),
  unit("municipal_ziwai", "紫外消毒"),
  unit("sludge_bengzhan", "污泥泵站"),
  unit("sludge_ganhua", "污泥干化"),
  unit("sludge_hebing", "污泥合并"),
  unit("sludge_nongsuo", "污泥浓缩"),
  unit("sludge_shusong", "污泥输送"),
  unit("sludge_tuoshui", "污泥脱水"),
  unit("sludge_xiaohua", "污泥消化"),
  unit("municipal_input", "市政输入", "builtin"),
  unit("junction", "汇流", "builtin"),
  unit("quality_edit", "水质编辑", "builtin"),
  unit("recycle_junction", "回流转换", "builtin"),
];

/** 任务书 §二.④ 表（unit_id→一级类——逐行誊录对账源）。 */
const EXPECTED_CATEGORY: Record<string, string> = {
  municipal_cugeshan: "一级处理",
  municipal_xigeshan: "一级处理",
  municipal_chenshachi: "一级处理",
  municipal_chuchenchi: "一级处理",
  municipal_tiaojiechi: "一级处理",
  municipal_wushui_tisheng: "一级处理",
  municipal_bashi_jiliangcao: "一级处理",
  conveyance_jishuijing: "一级处理",
  conveyance_peishuijing: "一级处理",
  conveyance_jipeishuijing: "一级处理",
  conveyance_peishuiqu: "一级处理",
  municipal_aao: "二级处理",
  municipal_cass: "二级处理",
  municipal_erchunchi: "二级处理",
  municipal_gaomidu: "深度处理",
  municipal_vxinglvchi: "深度处理",
  municipal_ziwai: "深度处理",
  mine_water_input: "矿井水处理",
  mine_water_tiaojiechi: "矿井水处理",
  mine_water_chenshachi: "矿井水处理",
  mine_water_ningjiao: "矿井水处理",
  mine_water_cifenli: "矿井水处理",
  mine_water_gaomidu: "矿井水处理",
  mine_water_vxinglvchi: "矿井水处理",
  mine_water_ziwai: "矿井水处理",
  sludge_bengzhan: "污泥处理",
  sludge_nongsuo: "污泥处理",
  sludge_hebing: "污泥处理",
  sludge_xiaohua: "污泥处理",
  sludge_tuoshui: "污泥处理",
  sludge_ganhua: "污泥处理",
  sludge_shusong: "污泥处理",
  municipal_input: "结构节点",
  junction: "结构节点",
  quality_edit: "结构节点",
  recycle_junction: "结构节点",
};

describe("B1 分级目录映射表全域（§二.④ 表对账）", () => {
  it("36 unit_id 恰一次全覆盖（映射表键集=任务书表键集，无缺无重）", () => {
    const tableIds = Object.keys(EXPECTED_CATEGORY);
    expect(tableIds).toHaveLength(36);
    for (const [unitId, label] of Object.entries(EXPECTED_CATEGORY)) {
      const categoryId = categoryOfUnit(unitId);
      expect(categoryId, `${unitId} 未入映射表`).not.toBeNull();
      const matched = CATALOG_CATEGORIES.find(
        (category) => category.id === categoryId,
      );
      expect(matched?.label, `${unitId} 类名应=${label}`).toBe(label);
    }
  });

  it("未知 unit_id → null（未映射不入目录——扩值须同步本表）", () => {
    expect(categoryOfUnit("unknown_unit")).toBeNull();
  });

  it("类序=一级处理→二级处理→深度处理→矿井水处理→污泥处理→结构节点（尾组）", () => {
    expect(CATALOG_CATEGORIES.map((category) => category.label)).toEqual([
      "一级处理",
      "二级处理",
      "深度处理",
      "矿井水处理",
      "污泥处理",
      "结构节点",
    ]);
  });
});

describe("B1 buildCatalogGroups（目录→分级分组）", () => {
  it("全量对账：36 件恰一次分组+各组计数 11/3/3/8/7/4", () => {
    const groups = buildCatalogGroups(FIXTURE_36);
    expect(groups).toHaveLength(6);
    const byLabel = new Map(
      groups.map((group) => [group.category.label, group.units]),
    );
    const counts: Record<string, number> = {
      "一级处理": 11,
      "二级处理": 3,
      "深度处理": 3,
      "矿井水处理": 8,
      "污泥处理": 7,
      "结构节点": 4,
    };
    for (const [label, count] of Object.entries(counts)) {
      expect(byLabel.get(label), `${label} 组缺席`).toHaveLength(count);
    }
    // 恰一次：全部条目并集=36 件夹具且无重复
    const all = groups.flatMap((group) => group.units.map((u) => u.unit_id));
    expect(all).toHaveLength(36);
    expect(new Set(all).size).toBe(36);
    expect(new Set(all)).toEqual(new Set(Object.keys(EXPECTED_CATEGORY)));
  });

  it("组内服务端序保持+name_zh/kind 直出（二级目录=具体工艺中文名）", () => {
    const groups = buildCatalogGroups(FIXTURE_36);
    const secondary = groups.find(
      (group) => group.category.label === "二级处理",
    );
    expect(secondary?.units.map((u) => u.name_zh)).toEqual([
      "AAO 生物池",
      "CASS 生物池",
      "辐流二沉池",
    ]);
    const structure = groups.find(
      (group) => group.category.label === "结构节点",
    );
    expect(structure?.units.every((u) => u.kind === "builtin")).toBe(true);
  });

  it("空输入→六组恒在场（空目录面组结构稳定）+未映射 id 跳过", () => {
    expect(buildCatalogGroups([]).map((g) => g.units.length)).toEqual([
      0, 0, 0, 0, 0, 0,
    ]);
    const groups = buildCatalogGroups([unit("future_unit", "未来单元")]);
    expect(groups.flatMap((g) => g.units)).toHaveLength(0);
  });
});

describe("B1 缩略图键集对账（DoD §四.5——目录全量×glyph 键集双向恒等）", () => {
  it("THUMBNAIL_GLYPH_KINDS 与映射表全域双向恰等（漏登记/漏绘两向皆红）", () => {
    const tableIds = Object.keys(EXPECTED_CATEGORY).sort();
    const glyphKinds = [...THUMBNAIL_GLYPH_KINDS].sort();
    expect(glyphKinds).toHaveLength(36);
    expect(new Set(glyphKinds).size).toBe(36);
    expect(glyphKinds).toEqual(tableIds);
  });
});
