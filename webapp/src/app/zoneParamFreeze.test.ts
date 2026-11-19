/**
 * G2 URL 冻结点测试（B7 收口批 2026-10-10——?tab= 值域行为级冻结；b2 壳
 * 重组批 2026-11-19 八入口重冻结：锁现状非重定义，值域语义随 b2 用户
 * 裁决〔批准稿八入口〕整体切换——旧六 zone 冻结集全体降为兼容归一族）。
 *
 * 冻结点语义申报〔头注〕：本测试=b2 主控盘存值域的契约快照（行为级
 * 冻结——非源扫描）。**值域变更=用户裁决位**：任何增删值域键、键序
 * 漂移、入口标签改动都须先经用户裁决再同步本冻结集——未同步即红即
 * 违约。兼容归一表（LEGACY_TAB_COMPAT——b2 自 LEGACY_ZONE_COMPAT 更名
 * 扩面）冻结=20 键行为断言+键集同源机检（手列冻结表↔导出常量双源
 * 集合相等）双承载。
 *
 * 输入:  zoneParam.ts 导出面（parseTabParam/NAV_KEYS/NAV_LABELS/
 *        LEGACY_TAB_COMPAT——node 环境纯函数直测，零渲染）
 * 输出:  断言族：①31 键逐一 parseTabParam(`?tab=${v}`) 恰回期望
 *        target（新值域 11 值含 deliverables 三子页+兼容归一 20 键含
 *        subpage 归一）②非法样本 null（未知裸值/空串/子页错挂
 *        analysis.sheets 等/三段以上）③导出面冻结：NAV_KEYS 键序值域
 *        恰等冻结数组+NAV_LABELS 键序恰循 NAV_KEYS 且标签值逐键冻结
 *        ④兼容表同源机检：LEGACY_TAB_COMPAT 键集恰等冻结表兼容 20
 *        键集（手列冻结表↔导出面常量双源——新增/删减兼容键即红）
 */
import { describe, expect, it } from "vitest";

import {
  LEGACY_TAB_COMPAT,
  NAV_KEYS,
  NAV_LABELS,
  parseTabParam,
  type NavTarget,
} from "./zoneParam";

/** b2 冻结集：31 键 → parse 期望终态（主控盘存 2026-11-19——增删键须
 *  用户裁决后同步本表，未同步即红）。 */
const FROZEN_KEYS: readonly { value: string; target: NavTarget }[] = [
  // ── 新值域 11 值（八入口裸值+deliverables 三子页族）──
  { value: "workbench", target: { nav: "workbench" } },
  { value: "process", target: { nav: "process" } },
  { value: "parameters", target: { nav: "parameters" } },
  { value: "analysis", target: { nav: "analysis" } },
  { value: "compare", target: { nav: "compare" } },
  { value: "deliverables", target: { nav: "deliverables" } },
  { value: "deliverables.sheets", target: { nav: "deliverables", subpage: "sheets" } },
  { value: "deliverables.siteplan", target: { nav: "deliverables", subpage: "siteplan" } },
  { value: "deliverables.report", target: { nav: "deliverables", subpage: "report" } },
  { value: "viewer3d", target: { nav: "viewer3d" } },
  { value: "ai", target: { nav: "ai" } },
  // ── 兼容归一 20 键（两代旧值→新导航——解析期单点收口）──
  // v4 六 zone 值（9 键）
  { value: "projects", target: { nav: "workbench" } },
  { value: "design", target: { nav: "process" } },
  { value: "design.canvas", target: { nav: "process" } },
  { value: "design.analysis", target: { nav: "analysis" } },
  { value: "network", target: { nav: "workbench" } },
  { value: "drafting", target: { nav: "deliverables" } },
  { value: "drafting.sheets", target: { nav: "deliverables" } },
  { value: "drafting.siteplan", target: { nav: "deliverables", subpage: "siteplan" } },
  { value: "report", target: { nav: "deliverables", subpage: "report" } },
  // legacy 槽路由期十值（11 键含 studio 族展开）
  { value: "canvas", target: { nav: "process" } },
  { value: "solutions", target: { nav: "parameters" } },
  { value: "studio", target: { nav: "process" } },
  { value: "studio.study", target: { nav: "process" } },
  { value: "studio.cost", target: { nav: "analysis" } },
  { value: "studio.compare", target: { nav: "compare" } },
  { value: "studio.trust", target: { nav: "analysis" } },
  { value: "elevation", target: { nav: "analysis" } },
  { value: "siteplan", target: { nav: "deliverables", subpage: "siteplan" } },
  { value: "studio.drawings", target: { nav: "deliverables" } },
  { value: "opsdebug", target: { nav: "process" } },
];

/** 冻结集键数恰 31（防表体行被静默增删后断言面缩水——计数本身即锚）。 */
const FROZEN_KEY_COUNT = 31;
/** 兼容归一族行数（双源键集机检切片位——表尾 20 行）。 */
const FROZEN_COMPAT_COUNT = 20;

/** 导出面入口声明序冻结（窄导航轨条目序单源——键序漂移即红）。 */
const FROZEN_NAV_ORDER: readonly string[] = [
  "workbench",
  "process",
  "parameters",
  "analysis",
  "compare",
  "deliverables",
  "viewer3d",
  "ai",
];

/** 入口中文标签冻结（窄导航轨/状态条单源——改标签=用户裁决位）。 */
const FROZEN_LABELS: Readonly<Record<string, string>> = {
  workbench: "工作台",
  process: "工艺",
  parameters: "参数方案",
  analysis: "分析",
  compare: "工况",
  deliverables: "图纸报告",
  viewer3d: "三维",
  ai: "AI 助手",
};

describe("G2 ?tab= 八入口值域冻结点（b2 重冻结——行为级契约快照）", () => {
  it(`冻结集计数恰 ${FROZEN_KEY_COUNT} 键（表体行增删即红——断言面完整性锚）`, () => {
    expect(FROZEN_KEYS.length).toBe(FROZEN_KEY_COUNT);
  });

  it("31 键逐一 parseTabParam(`?tab=${v}`) 恰回期望 target（含兼容归一 subpage）", () => {
    for (const { value, target } of FROZEN_KEYS) {
      expect(parseTabParam(`?tab=${value}`)).toEqual(target);
    }
  });

  it("非法样本 null：未知裸值/空串/子页错挂（analysis.sheets 等）/三段以上", () => {
    // 未知裸值（表外新键=非法——值域扩键须用户裁决+同步冻结集）
    expect(parseTabParam("?tab=badvalue")).toBeNull();
    expect(parseTabParam("?tab=process2")).toBeNull();
    // 空串/缺键
    expect(parseTabParam("?tab=")).toBeNull();
    expect(parseTabParam("")).toBeNull();
    expect(parseTabParam("?project=p1")).toBeNull();
    // 子页错挂（sheets 挂 analysis/canvas 挂 deliverables/子页挂无子页入口）
    expect(parseTabParam("?tab=analysis.sheets")).toBeNull();
    expect(parseTabParam("?tab=process.canvas")).toBeNull();
    expect(parseTabParam("?tab=deliverables.canvas")).toBeNull();
    expect(parseTabParam("?tab=workbench.sheets")).toBeNull();
    expect(parseTabParam("?tab=ai.report")).toBeNull();
    expect(parseTabParam("?tab=deliverables.badsub")).toBeNull();
    // 三段以上
    expect(parseTabParam("?tab=a.b.c")).toBeNull();
    expect(parseTabParam("?tab=deliverables.sheets.x")).toBeNull();
  });

  it("导出面冻结：NAV_KEYS 键序值域恰等冻结数组（增删入口/键序漂移即红）", () => {
    expect([...NAV_KEYS]).toEqual(FROZEN_NAV_ORDER);
  });

  it("导出面冻结：NAV_LABELS 键序恰循 NAV_KEYS+标签值逐键冻结", () => {
    expect(Object.keys(NAV_LABELS)).toEqual(FROZEN_NAV_ORDER);
    expect(NAV_LABELS).toEqual(FROZEN_LABELS);
  });

  it("冻结键集完备性：NAV_KEYS 全体裸值+deliverables 子页族全体双段键均在冻结表（冻结表缺行即红）", () => {
    const frozenValues = new Set(FROZEN_KEYS.map((row) => row.value));
    for (const nav of NAV_KEYS) {
      if (!frozenValues.has(nav)) {
        throw new Error(`入口 ${nav} 裸值缺席冻结表（表体与导出面不同步）`);
      }
    }
    for (const sub of ["deliverables.sheets", "deliverables.siteplan", "deliverables.report"]) {
      if (!frozenValues.has(sub)) {
        throw new Error(`子页键 ${sub} 缺席冻结表（表体与导出面不同步）`);
      }
    }
  });

  it(`兼容表同源机检：LEGACY_TAB_COMPAT 键集恰等冻结表兼容 ${FROZEN_COMPAT_COUNT} 键集（手列冻结表↔导出常量双源——增删兼容键即红）`, () => {
    // 双源集合相等双向锁：新增兼容键漏同步冻结表 / 删减兼容键漏清冻结
    // 表行，任一侧漂移即红（键序不作断言面——集合语义，sort 归一比对）。
    const frozenCompatKeys = FROZEN_KEYS.slice(
      FROZEN_KEYS.length - FROZEN_COMPAT_COUNT,
    ).map((row) => row.value);
    expect(frozenCompatKeys).toHaveLength(FROZEN_COMPAT_COUNT);
    const exportedKeys = Object.keys(LEGACY_TAB_COMPAT);
    expect(exportedKeys.sort()).toEqual([...frozenCompatKeys].sort());
  });
});
