/**
 * 摆放态汇总（F9——C2-visual 批）：三维场景已布置单元计数与横幅判据。
 *
 * 输入:  RenderScene（viewer3d 投影产物）+项目详情弱类型载荷
 *        （design.nodes 键集——shared orval 弱类型 dict）
 * 输出:  countPlacedUnits（scene solids/internals/waters 单元组在场数
 *        ——首段去重）+designNodesCount（design.nodes 可布置键数——内置
 *        kind 节点排除+窄化防御）+siteStructuresCount（structures 键数）+
 *        placementSummary（{placed,total} 横幅判据——兜底满场[structures
 *        空]/全覆盖[placed>=total]/不可达 均返 null 不挂）
 *
 * 规格说明（task-c2-visual-plan §三 F9——op-chain-fix-plan §四）：
 *   - 根因面=走查 F9：site 混合摆放态三维骤降（19 构筑物+16 管→1+0）
 *     ——core build_scene 仅收 site.structures 已布置单元（诚实语义），
 *     无解释面致观感「三维坏了」；
 *   - 横幅判据=site.structures 非空 且 N（scene 单元组在场数）<M
 *     （design.nodes 可布置总数）——structures 空=core 兜底满场布局
 *     全量入图不挂（E1 实测勘正：以 placed<total 单判会在兜底态因
 *     无几何单元常态误报）；管廊随构物不单独计数；
 *   - 弱类型窄化：design.nodes 非对象/详情未就绪=null（横幅不挂——
 *     数据面故障不误导，与 NO_CALC_HINT I-3 分级口径同精神）；
 *   - placed 计数口径=solids+internals+waters 的 `node_id` 首段去重
 *     （`pipe::` 场景级件排除——groupUnitConstructs 同判据；水域件
 *     `{unit}::water_surface` 亦带首段，与构物同单元不重复计）。
 */
import type { RenderScene } from "./projectScene";

/** scene 在场单元数（solids+internals+waters 首段去重——pipe 排除）。 */
export function countPlacedUnits(scene: RenderScene): number {
  const units = new Set<string>();
  for (const node of [
    ...scene.solids,
    ...scene.internals,
    ...scene.waters,
  ]) {
    const sep = node.id.indexOf("::");
    if (sep <= 0) {
      continue;
    }
    const unitId = node.id.slice(0, sep);
    if (unitId === "pipe") {
      continue;
    }
    units.add(unitId);
  }
  return units.size;
}

/** 可布置单元总数窄化（弱类型 dict——design.nodes 值对象中带 kind 字符串
 * 键者=内置节点[inlet/junction 族，无几何永不入图]排除；非对象=null）。 */
export function designNodesCount(projectDetail: unknown): number | null {
  if (typeof projectDetail !== "object" || projectDetail === null) {
    return null;
  }
  const design = (projectDetail as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return null;
  }
  const nodes = (design as Record<string, unknown>)["nodes"];
  if (typeof nodes !== "object" || nodes === null || Array.isArray(nodes)) {
    return null; // nodes 契约=dict（数组/原始值=形状异常不可达）
  }
  let count = 0;
  for (const node of Object.values(nodes as Record<string, unknown>)) {
    if (typeof node !== "object" || node === null) {
      continue;
    }
    // designWriter.addUnit 契约：包单元={}（或 params 面）/内置={kind}
    if (typeof (node as Record<string, unknown>)["kind"] === "string") {
      continue; // 内置节点（无几何——core build_scene 恒不收）
    }
    count += 1;
  }
  return count;
}

/** 摆放态横幅判据（GV-01 R 轮：placed<total 判据收进本函数——全覆盖
 * 返 null）：site.structures 空=core 兜底满场布局（全部可布置单元自动
 * 入图）不挂；非空（摆放进行中）且 placed<total=返回计数对（挂横幅）；
 * 全覆盖或任一不可达=null（消费点仅判非空即挂）。 */
export function placementSummary(
  scene: RenderScene,
  projectDetail: unknown,
): { placed: number; total: number } | null {
  const total = designNodesCount(projectDetail);
  if (total === null) {
    return null;
  }
  const structures = siteStructuresCount(projectDetail);
  if (structures === null || structures === 0) {
    return null; // 兜底满场（未开始摆放）——三维全量呈现无解释需求
  }
  const placed = countPlacedUnits(scene);
  if (placed >= total) {
    return null; // 摆放全覆盖——无解释需求
  }
  return { placed, total };
}

/** site.structures 键数窄化（弱类型——非对象=unreachable null）。 */
export function siteStructuresCount(projectDetail: unknown): number | null {
  if (typeof projectDetail !== "object" || projectDetail === null) {
    return null;
  }
  const design = (projectDetail as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return null;
  }
  const site = (design as Record<string, unknown>)["site"];
  if (typeof site !== "object" || site === null || Array.isArray(site)) {
    return null;
  }
  const structures = (site as Record<string, unknown>)["structures"];
  if (
    typeof structures !== "object" ||
    structures === null ||
    Array.isArray(structures)
  ) {
    return null;
  }
  return Object.keys(structures).length;
}
