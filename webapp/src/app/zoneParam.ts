/**
 * v4 zone URL 参数纯函数（B1 骨架批 2026-10-09——?ia=v4 特性开关下六功能
 * 区+子页两级值域+旧十值兼容表+?node= 独立通道；projectParam 同族形）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标 zone（或 node 值）
 * 输出:  parseZoneParam → V4ZoneTarget（两级值域+兼容归一）或 null；
 *        withZoneParam → 写入 tab 键的新查询串；parseNodeParam/withNodeParam
 *        → ?node= 独立通道读写；parseIaParam → "v4" | null（特性开关）；
 *        initialZoneTarget → 初值三级解析
 *
 * 规格说明（B1 任务书 §二.① URL 映射表——单源）：
 *   - 新值域语法=?tab=<zone> 或 <zone>.<subpage>（点分复合——子页仅
 *     design（canvas/analysis）与 drafting（sheets/siteplan）两 zone 可带，
 *     挂错 zone=非法；三段以上 null）；六 zone=projects/design/network/
 *     drafting/viewer3d/report；
 *   - 兼容归一=解析期单点收口（新值域优先于兼容表——防未来扩值歧义）：
 *     canvas/solutions/studio/studio.study/opsdebug→design；studio.cost/
 *     compare/trust/elevation→design.analysis（高程纵断=分析视图——定名
 *     消歧 W2）；siteplan→drafting.siteplan；studio.drawings→drafting；
 *     viewer3d→viewer3d（同名直通经新值域命中，不入表）；
 *   - mount 不改写地址栏（兼容值留 URL 至下次切 zone——M1 边缘语义 a
 *     同口径；本文件纯读恒不改 URL）；
 *   - 双写主从：?node= 为对象选中真相（独立键读写互不覆盖——ENG5 D6
 *     双轨形承袭：node/task/enum 三键各自独立）；?tab= 仅 zone 级投影；
 *   - 初值三级：?tab= 合法〔含兼容归一〕→用之；无 ?tab= 但有 ?node=/
 *     ?task=/?enum=→design（深链意图——M1 边缘语义 c 对称）；缺省
 *     design（新壳默认区≠canvas 裸值——design.zone 为着陆常态）；
 *   - 产出无 "?" 前缀查询串（replaceState 拼接面在消费方——projectParam
 *     同族口径）。
 */

/** v4 六功能区（任务书 §二.① zone 值域）。 */
export type V4Zone =
  | "projects"
  | "design"
  | "network"
  | "drafting"
  | "viewer3d"
  | "report";

/** design 子页（工艺画布=缺省/分析表）。 */
export type DesignSubpage = "canvas" | "analysis";
/** drafting 子页（图纸库=缺省/厂区总平面布置编辑面——v4-2 终裁归制图域）。 */
export type DraftingSubpage = "sheets" | "siteplan";

/** ?tab= 解析终态：subpage 仅 design/drafting 可带（parse 已归一）。 */
export type V4ZoneTarget =
  | { zone: "design"; subpage?: DesignSubpage }
  | { zone: "drafting"; subpage?: DraftingSubpage }
  | { zone: "projects" | "network" | "viewer3d" | "report" };

/** zone 声明序（zone-band 页签序单源——项目→计算说明）。 */
export const V4_ZONES: readonly V4Zone[] = [
  "projects",
  "design",
  "network",
  "drafting",
  "viewer3d",
  "report",
];

/** zone 中文名（状态条/页签单源——回炉 R11：自 shellV4 迁入断环
 *  〔shellV4↔zoneBand 循环 import 根治——V4Zone 真源同件〕）。 */
export const V4_ZONE_LABELS: Record<V4Zone, string> = {
  projects: "项目",
  design: "污水厂设计",
  network: "管网系统",
  drafting: "工程制图",
  viewer3d: "三维示意",
  report: "计算说明",
};

/** design/drafting 子页合法值（parse 双段校验源）。 */
const DESIGN_SUBPAGES: readonly string[] = ["canvas", "analysis"];
const DRAFTING_SUBPAGES: readonly string[] = ["sheets", "siteplan"];

/** 兼容归一表（旧十值→新值——新值域优先；viewer3d 同名直通不入表）。 */
const LEGACY_ZONE_COMPAT: Readonly<Record<string, V4ZoneTarget>> = {
  canvas: { zone: "design" },
  solutions: { zone: "design" },
  studio: { zone: "design" },
  "studio.study": { zone: "design" },
  "studio.cost": { zone: "design", subpage: "analysis" },
  "studio.compare": { zone: "design", subpage: "analysis" },
  "studio.trust": { zone: "design", subpage: "analysis" },
  elevation: { zone: "design", subpage: "analysis" }, // 高程纵断=分析视图（W2 消歧）
  siteplan: { zone: "drafting", subpage: "siteplan" },
  "studio.drawings": { zone: "drafting" },
  opsdebug: { zone: "design" }, // 视图不变语义沿 M1 口径
};

/** ?tab= 两级解析（新值域→兼容表；任一不合法→null）。 */
export function parseZoneParam(search: string): V4ZoneTarget | null {
  const value = new URLSearchParams(search).get("tab");
  if (value === null || value === "") {
    return null;
  }
  const parts = value.split(".");
  if (parts.length === 1) {
    if ((V4_ZONES as readonly string[]).includes(value)) {
      return { zone: value as V4Zone };
    }
    return LEGACY_ZONE_COMPAT[value] ?? null;
  }
  if (parts.length === 2) {
    const [head, sub] = [parts[0] ?? "", parts[1] ?? ""];
    if (head === "design" && DESIGN_SUBPAGES.includes(sub)) {
      return { zone: "design", subpage: sub as DesignSubpage };
    }
    if (head === "drafting" && DRAFTING_SUBPAGES.includes(sub)) {
      return { zone: "drafting", subpage: sub as DraftingSubpage };
    }
    return LEGACY_ZONE_COMPAT[value] ?? null;
  }
  return null;
}

/** 回写 tab 键（只动 tab——project/node/task 等他键原序保留；带子页→
 *  <zone>.<subpage>，否则裸 zone 值）。 */
export function withZoneParam(search: string, target: V4ZoneTarget): string {
  const params = new URLSearchParams(search);
  const sub =
    "subpage" in target ? (target as { subpage?: string }).subpage : undefined;
  params.set("tab", sub === undefined ? target.zone : `${target.zone}.${sub}`);
  return params.toString();
}

/** ?node= 直读（对象选中真相——与 task/enum 各自独立）。 */
export function parseNodeParam(search: string): string | null {
  const value = new URLSearchParams(search).get("node");
  return value === null || value === "" ? null : value;
}

/** 回写/移除 node 键（只动 node——task/enum/project 等他键原序保留）。 */
export function withNodeParam(search: string, nodeId: string | null): string {
  const params = new URLSearchParams(search);
  if (nodeId === null || nodeId === "") {
    params.delete("node");
  } else {
    params.set("node", nodeId);
  }
  return params.toString();
}

/** ?ia= 特性开关（"v4"=新壳；其余/缺失=M1 现行壳）。 */
export function parseIaParam(search: string): "v4" | null {
  const value = new URLSearchParams(search).get("ia");
  return value === "v4" ? "v4" : null;
}

/** 初值三级解析（合法 tab→深链 design→缺省 design——mount 不改写）。
 *  v4 深链层（?node=/?task=/?enum= 无 ?tab=→design）与缺省层同落 design
 *  （新壳默认区≠canvas 裸值——M1 边缘语义 c 对称形在此坍缩为同值；两层
 *  语义保留注记=未来缺省层改值时深链层须独立求值）。 */
export function initialZoneTarget(search: string): V4ZoneTarget {
  const target = parseZoneParam(search);
  if (target !== null) {
    return target;
  }
  return { zone: "design" };
}
