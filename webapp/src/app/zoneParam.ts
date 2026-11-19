/**
 * v4 壳导航 URL 参数纯函数（B1 骨架批六功能区→b2 壳重组批 2026-11-19
 * 八入口导航：窄导航轨键值域+deliverables 子页+旧值兼容表〔v4 六 zone
 * 值+旧十值〕+?node= 独立通道；值域变更=用户裁决〔批准稿 frontend-
 * redesign index.html/workbench.html 八入口序〕，沿革沿 zoneParam 名）。
 *
 * 输入:  查询串（location.search 原样或裸 search）+ 目标导航（或 node 值）
 * 输出:  parseTabParam → NavTarget（八键+deliverables 子页+兼容归一）或
 *        null；withTabParam → 写入 tab 键的新查询串；parseNodeParam/
 *        withNodeParam → ?node= 独立通道读写；initialNavTarget → 初值
 *        四级解析（合法 tab→node 深链→task/enum 深链→缺省 workbench）
 *
 * 规格说明（b2 壳重组批——批准稿 workbench.html 八入口序）：
 *   - 八入口键=workbench 工作台/process 工艺/parameters 参数方案/
 *     analysis 分析/compare 工况/deliverables 图纸报告/viewer3d 三维/
 *     ai AI 助手；子页仅 deliverables 可带（sheets 图纸库缺省/siteplan
 *     厂区总平面/report 计算说明——deliverables 三面合一），挂错入口=
 *     非法；三段以上 null；
 *   - 兼容归一=解析期单点收口（新值域优先于兼容表；mount 不改写地址栏
 *     ——旧值留 URL 至下次切换，M1 边缘语义 a 同口径；本文件纯读恒不
 *     改 URL）：
 *     projects→workbench；design〔.canvas〕→process（旧 design 区画布
 *     子页=新工艺入口）；design.analysis→analysis；network→workbench
 *     （旧管网占位区退役——「规划中」诚实说明面迁工作台，不设伪入口）；
 *     drafting〔.sheets〕→deliverables；drafting.siteplan→
 *     deliverables.siteplan；report→deliverables.report；canvas/
 *     solutions/studio/studio.study→process/parameters/process/process
 *     （solutions=方案面归参数方案）；studio.cost/studio.trust/
 *     elevation→analysis（概算/可信度/高程纵断=分析视图——W2 定名消歧
 *     沿承）；studio.compare→compare（工况对比=独立工况入口）；
 *     siteplan→deliverables.siteplan；studio.drawings→deliverables；
 *     opsdebug→process（视图不变语义沿 M1 口径）；
 *   - 双写主从：?node= 为对象选中真相（独立键读写互不覆盖——ENG5 D6
 *     双轨形承袭：node/task/enum 三键各自独立）；?tab= 仅导航级投影；
 *   - 初值四级：?tab= 合法〔含兼容归一〕→用之；无 ?tab= 但有 ?node=
 *     →process（画布选中语境）；有 ?task=/?enum=→parameters（方案/
 *     联合卡消费面）；缺省 workbench（新壳着陆=工作台——首屏答「当前
 *     哪个项目、下一步去哪」，旧缺省 design 迁移映射=process）；
 *   - 产出无 "?" 前缀查询串（replaceState 拼接面在消费方——projectParam
 *     同族口径）。
 */
import { parseEnumParam, parseTaskParam } from "./projectParam";

/** 八入口导航键（b2 壳重组——批准稿八入口序真源）。 */
export type NavKey =
  | "workbench"
  | "process"
  | "parameters"
  | "analysis"
  | "compare"
  | "deliverables"
  | "viewer3d"
  | "ai";

/** deliverables 子页（图纸库=缺省/厂区总平面/计算说明——三面合一入口）。 */
export type DeliverablesSubpage = "sheets" | "siteplan" | "report";

/** ?tab= 解析终态：subpage 仅 deliverables 可带（parse 已归一）。 */
export type NavTarget =
  | { nav: "deliverables"; subpage?: DeliverablesSubpage }
  | {
      nav:
        | "workbench"
        | "process"
        | "parameters"
        | "analysis"
        | "compare"
        | "viewer3d"
        | "ai";
    };

/** 导航键声明序（窄导航轨条目序单源——工作台→AI 助手）。 */
export const NAV_KEYS: readonly NavKey[] = [
  "workbench",
  "process",
  "parameters",
  "analysis",
  "compare",
  "deliverables",
  "viewer3d",
  "ai",
];

/** 导航键中文名（窄导航轨/状态条单源）。 */
export const NAV_LABELS: Record<NavKey, string> = {
  workbench: "工作台",
  process: "工艺",
  parameters: "参数方案",
  analysis: "分析",
  compare: "工况",
  deliverables: "图纸报告",
  viewer3d: "三维",
  ai: "AI 助手",
};

/** deliverables 子页合法值（parse 双段校验源）。 */
const DELIVERABLES_SUBPAGES: readonly string[] = [
  "sheets",
  "siteplan",
  "report",
];

/** 兼容归一表（旧值→新导航——新值域优先；viewer3d 同名直通不入表）。
 *  旧值两代：v4 六 zone 值〔projects/design 族/network/drafting 族/
 *  report〕+更早十值〔canvas/solutions/studio 族/elevation/siteplan/
 *  opsdebug〕。导出面供 zoneParamFreeze.test 键集同源断言消费。 */
export const LEGACY_TAB_COMPAT: Readonly<Record<string, NavTarget>> = {
  // v4 六 zone 值（b1 及以前 ?tab= 深链）
  projects: { nav: "workbench" },
  design: { nav: "process" },
  "design.canvas": { nav: "process" },
  "design.analysis": { nav: "analysis" },
  network: { nav: "workbench" }, // 旧管网占位区退役——规划中说明面在工作台
  drafting: { nav: "deliverables" },
  "drafting.sheets": { nav: "deliverables" },
  "drafting.siteplan": { nav: "deliverables", subpage: "siteplan" },
  report: { nav: "deliverables", subpage: "report" },
  // 更早十值（legacy 槽路由期）
  canvas: { nav: "process" },
  solutions: { nav: "parameters" }, // 方案面归参数方案入口
  studio: { nav: "process" },
  "studio.study": { nav: "process" },
  "studio.cost": { nav: "analysis" },
  "studio.compare": { nav: "compare" },
  "studio.trust": { nav: "analysis" },
  elevation: { nav: "analysis" }, // 高程纵断=分析视图（W2 消歧沿承）
  siteplan: { nav: "deliverables", subpage: "siteplan" },
  "studio.drawings": { nav: "deliverables" },
  opsdebug: { nav: "process" }, // 视图不变语义沿 M1 口径
};

/** ?tab= 两级解析（新值域→兼容表；任一不合法→null）。 */
export function parseTabParam(search: string): NavTarget | null {
  const value = new URLSearchParams(search).get("tab");
  if (value === null || value === "") {
    return null;
  }
  const parts = value.split(".");
  if (parts.length === 1) {
    if ((NAV_KEYS as readonly string[]).includes(value)) {
      return { nav: value as NavKey };
    }
    return LEGACY_TAB_COMPAT[value] ?? null;
  }
  if (parts.length === 2) {
    const [head, sub] = [parts[0] ?? "", parts[1] ?? ""];
    if (head === "deliverables" && DELIVERABLES_SUBPAGES.includes(sub)) {
      return { nav: "deliverables", subpage: sub as DeliverablesSubpage };
    }
    return LEGACY_TAB_COMPAT[value] ?? null;
  }
  return null;
}

/** 回写 tab 键（只动 tab——project/node/task 等他键原序保留；带子页→
 *  <nav>.<subpage>，否则裸 nav 值）。 */
export function withTabParam(search: string, target: NavTarget): string {
  const params = new URLSearchParams(search);
  const sub =
    "subpage" in target ? (target as { subpage?: string }).subpage : undefined;
  params.set("tab", sub === undefined ? target.nav : `${target.nav}.${sub}`);
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

/** 初值四级解析（合法 tab→node 深链 process→task/enum 深链 parameters
 *  →缺省 workbench——mount 不改写地址栏）。b1 及以前深链层/缺省层同落
 *  design 已坍缩；b2 拆分后三层各归其主（node=画布选中语境/task·enum=
 *  方案与任务消费面），语义在位非新增。 */
export function initialNavTarget(search: string): NavTarget {
  const target = parseTabParam(search);
  if (target !== null) {
    return target;
  }
  if (parseNodeParam(search) !== null) {
    return { nav: "process" };
  }
  if (parseTaskParam(search) !== null || parseEnumParam(search) !== null) {
    return { nav: "parameters" };
  }
  return { nav: "workbench" };
}
