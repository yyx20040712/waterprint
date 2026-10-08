/**
 * 分级目录映射纯函数（B1 骨架批 2026-10-09——右键二级目录数据面：36 单元
 * ×5 一级类+结构节点尾组；任务书 §二.④ 覆盖核验表单源）。
 *
 * 输入:  /api/units 目录条目（unit_id/name_zh/kind——服务端序）+本件映射表
 * 输出:  CATALOG_CATEGORIES（六类声明序）/categoryOfUnit（unit_id→一级类
 *        或 null）/buildCatalogGroups（目录→六组分级分组——组内服务端序
 *        保持+name_zh 直出）
 *
 * 规格说明（B1 任务书 §二.④——依据 v4 wireframe 屏 2 五类形）：
 *   - 五一级类映射：矿井水/污泥=业务线直映（8/7 恰等）；市政+输送 17 件
 *     按处理工程阶段划级（格栅/沉砂/初沉/调节/提升/计量=一级；生物池/
 *     二沉=二级；高密/滤池/消毒=深度）；builtin 4 件=画布结构节点，目录
 *     尾组保持可达（现行库内置组语义承袭）；
 *   - 二级目录=组内具体工艺（unit name_zh 直出，服务端序）；
 *   - 未映射 unit_id 跳过（新单元入目录须同步本表——对账测试=app 层
 *     catalogCategories.test 全量对账；漏登记=目录缺席红）；
 *   - 纯函数零 React 依赖（node 直测；消费面=shellV4/hierarchicalCatalog）。
 */

/** 一级类标识（组键——声明序即目录序）。 */
export type CatalogCategoryId =
  | "primary"
  | "secondary"
  | "advanced"
  | "mine"
  | "sludge"
  | "structure";

/** 一级类声明（label=目录一级标题）。 */
export interface CatalogCategoryDecl {
  id: CatalogCategoryId;
  label: string;
}

/** 六类声明序（一级处理→…→结构节点尾组——§二.④ 表序）。 */
export const CATALOG_CATEGORIES: readonly CatalogCategoryDecl[] = [
  { id: "primary", label: "一级处理" },
  { id: "secondary", label: "二级处理" },
  { id: "advanced", label: "深度处理" },
  { id: "mine", label: "矿井水处理" },
  { id: "sludge", label: "污泥处理" },
  { id: "structure", label: "结构节点" },
];

/** unit_id→一级类映射（§二.④ 表逐行——36 键全域恰一次）。 */
const UNIT_CATEGORY: Readonly<Record<string, CatalogCategoryId>> = {
  // 一级处理（11）
  municipal_cugeshan: "primary",
  municipal_xigeshan: "primary",
  municipal_chenshachi: "primary",
  municipal_chuchenchi: "primary",
  municipal_tiaojiechi: "primary",
  municipal_wushui_tisheng: "primary",
  municipal_bashi_jiliangcao: "primary",
  conveyance_jishuijing: "primary",
  conveyance_peishuijing: "primary",
  conveyance_jipeishuijing: "primary",
  conveyance_peishuiqu: "primary",
  // 二级处理（3）
  municipal_aao: "secondary",
  municipal_cass: "secondary",
  municipal_erchunchi: "secondary",
  // 深度处理（3）
  municipal_gaomidu: "advanced",
  municipal_vxinglvchi: "advanced",
  municipal_ziwai: "advanced",
  // 矿井水处理（8——业务线直映）
  mine_water_input: "mine",
  mine_water_tiaojiechi: "mine",
  mine_water_chenshachi: "mine",
  mine_water_ningjiao: "mine",
  mine_water_cifenli: "mine",
  mine_water_gaomidu: "mine",
  mine_water_vxinglvchi: "mine",
  mine_water_ziwai: "mine",
  // 污泥处理（7——业务线直映）
  sludge_bengzhan: "sludge",
  sludge_nongsuo: "sludge",
  sludge_hebing: "sludge",
  sludge_xiaohua: "sludge",
  sludge_tuoshui: "sludge",
  sludge_ganhua: "sludge",
  sludge_shusong: "sludge",
  // 结构节点（4——builtin 尾组）
  municipal_input: "structure",
  junction: "structure",
  quality_edit: "structure",
  recycle_junction: "structure",
};

/** unit_id→一级类（未映射→null）。 */
export function categoryOfUnit(unitId: string): CatalogCategoryId | null {
  return UNIT_CATEGORY[unitId] ?? null;
}

/** 目录条目消费面（UnitMetaEntry 子集——buildCatalogGroups 输入形态）。 */
export interface CatalogUnitEntry {
  unit_id: string;
  name_zh: string;
  kind: "unit" | "builtin";
}

/** 分级组（组内条目=服务端序保持）。 */
export interface CatalogGroup {
  category: CatalogCategoryDecl;
  units: CatalogUnitEntry[];
}

/**
 * 目录→六组分级分组：按映射表分桶（组内输入序保持=服务端序）；六组恒
 * 在场（空目录面组结构稳定——渲染面无跳变）；未映射 id 跳过（扩值维护
 * 面见头注）。
 */
export function buildCatalogGroups(
  units: readonly CatalogUnitEntry[],
): CatalogGroup[] {
  const buckets = new Map<CatalogCategoryId, CatalogUnitEntry[]>(
    CATALOG_CATEGORIES.map((category) => [category.id, []]),
  );
  for (const entry of units) {
    const categoryId = UNIT_CATEGORY[entry.unit_id];
    if (categoryId === undefined) {
      continue; // 未映射不入目录（新单元须同步映射表——对账测试守卫）
    }
    buckets.get(categoryId)?.push({
      unit_id: entry.unit_id,
      name_zh: entry.name_zh,
      kind: entry.kind,
    });
  }
  return CATALOG_CATEGORIES.map((category) => ({
    category,
    units: buckets.get(category.id) ?? [],
  }));
}
