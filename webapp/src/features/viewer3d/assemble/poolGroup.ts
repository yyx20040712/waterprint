/**
 * 池组排布计划（S11 接线批——spec §11 裁定「数据源=params/结果面零
 * core 改」的组装层；纯数据零异常，契约病返 null 归调用方登记）。
 *
 * 输入:  registry poolGroup 声明+单元场景 dims（length/width——场景图
 *        投影产物）+池数双源（catalog default=manifest 声明面+项目
 *        design.nodes[unitId] override 自由面——弱类型窄化先例
 *        placementSummary）+场景 conditionKey（工况真源）
 * 输出:  PoolGroupPlan（nPools/nActive/单池平面/方阵间距/在用池槽位/
 *        缺位槽=missingSlotPlaceholders 产物）或 null（无声明/数据病
 *        ——调用方维持现状单份渲染+logFallback 登记）
 *
 * 规格说明（spec §11 S11；三呈裁 2026-09-13）：
 *   - 池数唯一真源=params 面（override 优先、catalog default 回退）；
 *     渲染层不推导池数（P7 同界——本层只组合）；
 *   - nActive 派生：conditionKey===`design_offline_<unit_id>` 即该单元
 *     nPools−1（ADR-007 逐单元检修敏感性——n−1 池运行），其余=nPools；
 *   - 单池平面（占位框尺寸）：cellL=dims.length 恒取；cellW 按
 *     templateScope——unit（模板含全部池，AAO 整单元）=width÷nPools
 *     （位置推导合法——铁律 3；格宽派生=施工图两系列并排惯例）、
 *     cell（模板即单池，CASS）=width 直取（呈裁③）；
 *   - spacing=max(cellL, cellW)+gap（呈裁① 长边+净距——近方阵内
 *     槽间不重叠优先；工程「一字并排心距=宽+缝」与方阵契约的差异
 *     记档：方阵=冻结契约语义，一字排翻案归 R4 core 分池排布批）；
 *   - 槽位坐标=missingSlotPlaceholders 同一冻结函数：在用槽=全槽
 *     （nActive=0 形态）切首 nActive 项——零公式复制、口径单调构。
 */
import { logFallback } from "./fallbackLog";
import { missingSlotPlaceholders, type MissingSlot } from "./missingSlots";
import type { FamilyEntry, PoolGroupEntry } from "./registry";
import type { Vec3 } from "./types";

/** 池组排布计划（渲染层只消费不推导——组装产物全数值就绪）。 */
export type PoolGroupPlan = {
  readonly templateScope: "cell" | "unit";
  readonly nPools: number;
  readonly nActive: number;
  /** 单池平面米数（占位框尺寸——模板本地系 x/z）。 */
  readonly cellL: number;
  readonly cellW: number;
  /** 方阵槽心距 m（max(格长,格宽)+gap——呈裁①）。 */
  readonly spacing: number;
  /** 在用池槽位 [0, nActive)（templateScope=cell 分池多份渲染位）。 */
  readonly activeSlots: readonly Vec3[];
  /** 缺位槽（警示占位——冻结契约产物）。 */
  readonly missing: readonly MissingSlot[];
};

/** 池组计划入参（调用方 Scene 组装——数据 hooks 产物以值传入保持纯函数）。 */
export type PoolGroupInputs = {
  readonly poolGroup: PoolGroupEntry;
  readonly unitId: string;
  readonly dims: Record<string, number>;
  /** catalog 池数默认（useUnitCatalog params countParam 键——无键=null）。 */
  readonly countDefault: number | null;
  /** 项目 override（design.nodes[unitId] 自由面——非有限正数=无效忽略）。 */
  readonly countOverride: unknown;
  readonly conditionKey: string;
};

/** 弱类型 override 窄化（有限正数才有效——自由面容病不抬错）。 */
function asFinitePositive(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 1
    ? value
    : null;
}

/**
 * 项目 override 提取（弱类型窄化——placementSummary 同款纪律）：
 * design.nodes[unitId][countParam] 自由面值（非对象链/缺键=undefined）。
 */
export function nodeParamOverride(
  projectDetail: unknown,
  unitId: string,
  countParam: string,
): unknown {
  if (typeof projectDetail !== "object" || projectDetail === null) {
    return undefined;
  }
  const design = (projectDetail as Record<string, unknown>)["design"];
  if (typeof design !== "object" || design === null) {
    return undefined;
  }
  const nodes = (design as Record<string, unknown>)["nodes"];
  if (typeof nodes !== "object" || nodes === null) {
    return undefined;
  }
  const node = (nodes as Record<string, unknown>)[unitId];
  if (typeof node !== "object" || node === null) {
    return undefined;
  }
  return (node as Record<string, unknown>)[countParam];
}

/** 分池帽盖尺寸 ε（米——帽盖边缘与壳剖面轮廓的防 z-fight 余量）。 */
export const POOL_CAP_EPS = 0.05;

/**
 * 分池剖切帽盖边长（A-1 否决+A4+ε 方案）：
 * max(cellL, cellW)+ε——正方形帽盖 ≥max 边即覆盖本池 L×W 剖面足迹、
 * 且恒 < spacing（spacing=max(L,W)+gap，gap>ε 契约闸）不越邻槽。
 * 现行 capQuadFor 的 diag×1.1 过幅在分池槽距下被保覆盖下钳顶掉
 * （0.95×spacing<diag）——分池路径以本值覆盖（TemplateCap 可选 prop）。
 */
export function poolCapSize(cellL: number, cellW: number): number {
  return Math.max(cellL, cellW) + POOL_CAP_EPS;
}

export function poolGroupPlan(inputs: PoolGroupInputs): PoolGroupPlan | null {
  const { poolGroup, unitId, dims, countDefault, countOverride, conditionKey } =
    inputs;
  const override = asFinitePositive(countOverride);
  const fallback = asFinitePositive(countDefault);
  const rawPools = override ?? fallback;
  if (rawPools === null) {
    return null;
  }
  const nPools = Math.floor(rawPools);
  if (nPools < 1) {
    return null;
  }
  const cellL = dims["length"] ?? Number.NaN;
  const rawWidth = dims["width"] ?? Number.NaN;
  if (!Number.isFinite(cellL) || !Number.isFinite(rawWidth) || cellL <= 0 || rawWidth <= 0) {
    return null;
  }
  // 呈裁③：unit 域格宽=池组宽÷池数（模板含全部池）；cell 域直取单池宽
  const cellW =
    poolGroup.templateScope === "unit" ? rawWidth / nPools : rawWidth;
  if (!Number.isFinite(cellW) || cellW <= 0) {
    return null;
  }
  const gap = poolGroup.gap;
  if (!Number.isFinite(gap) || gap <= POOL_CAP_EPS) {
    return null; // 门一 W-2：gap≤ε 时帽盖越邻槽（poolCapSize 恒<spacing 的充要）
  }
  const spacing = Math.max(cellL, cellW) + gap;
  // ADR-007：design_offline_<unit_id> 即该单元 n−1 池运行；其余工况全池
  const offline = conditionKey === `design_offline_${unitId}`;
  const nActive = offline ? Math.max(0, nPools - 1) : nPools;
  // 在用槽=全槽（nActive=0 形态取 [0, nPools)）切首 nActive 项——与
  // 缺位槽同一冻结函数同一坐标系（池组中心=单元 origin）
  const allSlots = missingSlotPlaceholders(nPools, 0, spacing);
  const activeSlots = allSlots
    .slice(0, nActive)
    .map((slot) => slot.position);
  const missing = missingSlotPlaceholders(nPools, nActive, spacing);
  return {
    templateScope: poolGroup.templateScope,
    nPools,
    nActive,
    cellL,
    cellW,
    spacing,
    activeSlots,
    missing,
  };
}

/** Scene 组装入参形态（claimTemplateUnits 产物+catalog/详情弱类型值——
 *  结构化零跨层依赖；数据 hooks 产物以值传入保持纯函数）。 */
export type PoolClaim = {
  readonly entry: FamilyEntry;
  readonly dimNode: { readonly dims: Record<string, number> };
};

/** catalog 单元条目结构（UnitMetaEntry 兼容面——params 池数默认源）。 */
export type PoolUnitMeta = {
  readonly unit_id: string;
  readonly params?: ReadonlyArray<{
    readonly field_id: string;
    readonly default?: number | null;
  }> | null;
};

/**
 * 池组计划批组装（Scene useMemo 体——500 行预算门抽离）：逐 claim 声明
 * 池组者组装计划；数据病=null+logFallback 登记（现状单份渲染——两层
 * 分工先例：不渲染不抬错）。catalog 未就绪=空表（渲染层零占位零分池）。
 */
export function buildPoolPlans(
  claims: ReadonlyMap<string, PoolClaim>,
  units: readonly PoolUnitMeta[] | undefined,
  projectDetail: unknown,
  conditionKey: string,
): Map<string, PoolGroupPlan> {
  const plans = new Map<string, PoolGroupPlan>();
  if (units === undefined) {
    // 门一 W-4：catalog 未就绪/查询失败——登记（到达后重渲染齐现）
    logFallback(
      "pool_group",
      "catalog_unavailable",
      "单元目录未就绪——池组占位/分池/徽标暂不渲染",
    );
    return plans;
  }
  for (const [unitId, claim] of claims) {
    const declaration = claim.entry.poolGroup;
    if (declaration === undefined) {
      continue;
    }
    const meta = units.find((unit) => unit.unit_id === unitId);
    const countDefault =
      meta?.params?.find((param) => param.field_id === declaration.countParam)
        ?.default ?? null;
    const plan = poolGroupPlan({
      poolGroup: declaration,
      unitId,
      dims: claim.dimNode.dims,
      countDefault,
      countOverride: nodeParamOverride(
        projectDetail,
        unitId,
        declaration.countParam,
      ),
      conditionKey,
    });
    if (plan === null) {
      logFallback(
        unitId,
        "pool_group_data_missing",
        `${declaration.countParam}——catalog/override 双源不可得或 dims 病`,
      );
      continue;
    }
    plans.set(unitId, plan);
  }
  return plans;
}

/** 池组徽标（badges.poolCount/maintenanceNA 消费）：poolCount=true 且
 *  池数≥2 挂 ×n；检修工况（ADR-007）附 nActive/nPools；maintenanceNA=
 *  true 的族零徽标（NA=检修占位语义不可用——三族现状恒 false）。
 *  plan 缺席（数据病/catalog 未就绪）=零徽标（门一 W-3：池数未知时
 *  不得伪造「×n（k/n 检修中）」——Annotations「未收录=零徽标」同口径）。 */
export type PoolBadge = {
  readonly count: number;
  readonly active: number;
  readonly offline: boolean;
};

export function buildPoolBadges(
  claims: ReadonlyMap<string, PoolClaim>,
  plans: ReadonlyMap<string, PoolGroupPlan>,
  conditionKey: string,
): Record<string, PoolBadge> {
  const badges: Record<string, PoolBadge> = {};
  for (const [unitId, claim] of claims) {
    if (!claim.entry.badges.poolCount) {
      continue;
    }
    if (claim.entry.badges.maintenanceNA) {
      continue; // NA 族零徽标
    }
    const plan = plans.get(unitId);
    if (plan === undefined) {
      continue; // 数据病零徽标（不捏造池数）
    }
    const offline = conditionKey === `design_offline_${unitId}`;
    if (plan.nPools < 2 && !offline) {
      continue;
    }
    badges[unitId] = {
      count: plan.nPools,
      active: plan.nActive,
      offline,
    };
  }
  return badges;
}
