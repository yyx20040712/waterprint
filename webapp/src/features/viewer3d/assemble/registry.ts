/**
 * 模板族 registry（spec.md §9 schema v1 草案实装——批3 主体）。
 *
 * 输入:  registry.json（数据真源——check_templates.mjs 语法/资产在场门
 *        的校验对象）+unit_id（场景图节点 id 首段）
 * 输出:  FamilyEntry（typed）+familyForUnit 查询+READY 守卫
 *
 * 规格说明（spec §9；§11 P2/P6/P7 裁定落位）：
 *   - 键=unit_id（kindAliases=多对一扩位[P6 污泥族合并形，本批留空]）；
 *   - dimSource.primitiveKind：声明的池体图元 kind（cylinder/box——
 *     sceneDimsToTarget 轴对应消费面；单元多 solids 时以本 kind 节点
 *     为模板取数位，其余构型件由模板整族承载）；
 *   - templateSize：壳 AABB 米数（CI 对拍 shell 组 AABB——§2/§8）；
 *   - ratioDomain：P2 签核初始域（辐流 L/H∈[4,14]；试点后收紧）；
 *   - equipment.actualFactor：×场景 dim（主轴 L=diameter）派生 actual
 *     （§5 数据链：u=actual/templateFeature 等比保圆）；
 *   - instanceSpacing：P5 签核常量表（栏杆立柱 1.5m——P7 裁定下仅作
 *     布点间距语义，数量恒由场景图 instance_count 提供，禁推导）；
 *   - status：ready=资产在场；pending=缺资产合法降级（装配器走原语
 *     渲染 PoolBox，不挂 fallbackLog——合法态非缺陷）。
 */

import raw from "./registry.json";
import type { InstanceMode } from "./instanceLayout";
import type { RatioDomainEntry, TemplateSize } from "./types";

/** equipment 条目（§9；anchor 缺省 aabb_min）。 */
export type EquipmentEntry = {
  readonly templateFeature: number;
  readonly actualFactor: number;
  readonly anchor?: "pool_center_bottom" | "aabb_min";
};

/** registry 家族条目（§9 schema v1——json 数据的 typed 视图）。 */
export type FamilyEntry = {
  readonly family: string;
  readonly prefix: string;
  readonly glb: string;
  readonly thumb: string;
  readonly dimSource: { readonly primitiveKind: "cylinder" | "box" };
  readonly templateSize: TemplateSize;
  readonly ratioDomain: readonly RatioDomainEntry[];
  readonly equipment: Readonly<Record<string, EquipmentEntry>>;
  readonly instanceSpacing: Readonly<Record<string, number | null>>;
  /** inst 组布局模式（段二 box 族——缺省 ring=辐流立柱零改；
   *  模式语义=位置推导面，数量恒由场景图 instance_count 提供[P7]。 */
  readonly instanceModes?: Readonly<Record<string, InstanceMode>>;
  readonly badges: { readonly poolCount: boolean; readonly maintenanceNA: boolean };
  readonly status: "ready" | "pending";
  /** 五步门机器面（宪法 §0.1 视觉资产批）：资产构建日期+三段流审查
   *  日期（check_templates.mjs 断言 designReview≥built+报告在场）。 */
  readonly built?: string;
  readonly designReview?: string;
};

type RegistryFile = {
  readonly version: number;
  readonly families: Readonly<Record<string, FamilyEntry>>;
};

const REGISTRY = raw as RegistryFile;

/** 全部条目（只读视图——check_templates/测试消费）。 */
export function registryEntries(): Readonly<Record<string, FamilyEntry>> {
  return REGISTRY.families;
}

/** unit_id → 条目（无条目=null——装配器走原语渲染，非缺陷）。 */
export function familyForUnit(unitId: string): FamilyEntry | null {
  return REGISTRY.families[unitId] ?? null;
}

/** 资产就绪守卫（pending=合法降级位——调用方不渲染模板且不登记）。 */
export function isReady(entry: FamilyEntry): boolean {
  return entry.status === "ready";
}
