/**
 * G2 URL 冻结点测试（B7 收口批 2026-10-10——?tab= 值域行为级冻结：锁
 * 现状非重定义，值域语义零改；plan §十二 B7 DoD「?tab= 冻结点」）。
 *
 * 冻结点语义申报〔头注〕：本测试=B7 主控盘存值域的契约快照（行为级
 * 冻结——非源扫描）。**值域变更=用户裁决位**：任何增删值域键、键序
 * 漂移、zone 标签改动都须先经用户裁决再同步本冻结集——未同步即红即
 * 违约。兼容归一表（LEGACY_ZONE_COMPAT）为模块私有面，其冻结经 11
 * 键行为断言承载（表内键逐一断言 parse 语义；表外新键=非法样本面
 * null 断言族锁边界）。
 *
 * 输入:  zoneParam.ts 导出面（parseZoneParam/V4_ZONES/V4_ZONE_LABELS
 *        ——node 环境纯函数直测，零渲染）
 * 输出:  断言族：①21 键逐一 parseZoneParam(`?tab=${v}`) 恰回期望
 *        target（新值域 10 值含双段子页+兼容归一 11 键含 subpage 归一）
 *        ②非法样本 null（未知裸值/空串/子页错挂 design.sheets 等/三段
 *        以上）③导出面冻结：V4_ZONES 键序值域恰等冻结数组+
 *        V4_ZONE_LABELS 键序恰循 V4_ZONES 且标签值逐键冻结
 */
import { describe, expect, it } from "vitest";

import {
  parseZoneParam,
  V4_ZONE_LABELS,
  V4_ZONES,
  type V4ZoneTarget,
} from "./zoneParam";

/** B7 冻结集：21 键 → parse 期望终态（主控盘存 2026-10-10——增删键须
 *  用户裁决后同步本表，未同步即红）。 */
const FROZEN_KEYS: readonly { value: string; target: V4ZoneTarget }[] = [
  // ── 新值域 10 值（六 zone 裸值+design/drafting 两子页族）──
  { value: "projects", target: { zone: "projects" } },
  { value: "design", target: { zone: "design" } },
  { value: "design.canvas", target: { zone: "design", subpage: "canvas" } },
  { value: "design.analysis", target: { zone: "design", subpage: "analysis" } },
  { value: "drafting", target: { zone: "drafting" } },
  { value: "drafting.sheets", target: { zone: "drafting", subpage: "sheets" } },
  { value: "drafting.siteplan", target: { zone: "drafting", subpage: "siteplan" } },
  { value: "network", target: { zone: "network" } },
  { value: "viewer3d", target: { zone: "viewer3d" } },
  { value: "report", target: { zone: "report" } },
  // ── 兼容归一 11 键（旧值→新值——解析期单点收口）──
  { value: "canvas", target: { zone: "design" } },
  { value: "solutions", target: { zone: "design" } },
  { value: "studio", target: { zone: "design" } },
  { value: "studio.study", target: { zone: "design" } },
  { value: "studio.cost", target: { zone: "design", subpage: "analysis" } },
  { value: "studio.compare", target: { zone: "design", subpage: "analysis" } },
  { value: "studio.trust", target: { zone: "design", subpage: "analysis" } },
  { value: "elevation", target: { zone: "design", subpage: "analysis" } },
  { value: "siteplan", target: { zone: "drafting", subpage: "siteplan" } },
  { value: "studio.drawings", target: { zone: "drafting" } },
  { value: "opsdebug", target: { zone: "design" } },
];

/** 冻结集键数恰 21（防表体行被静默增删后断言面缩水——计数本身即锚）。 */
const FROZEN_KEY_COUNT = 21;

/** 导出面 zone 声明序冻结（zone-band 页签序单源——键序漂移即红）。 */
const FROZEN_ZONE_ORDER: readonly string[] = [
  "projects",
  "design",
  "network",
  "drafting",
  "viewer3d",
  "report",
];

/** zone 中文标签冻结（状态条/页签单源——改标签=用户裁决位）。 */
const FROZEN_LABELS: Readonly<Record<string, string>> = {
  projects: "项目",
  design: "污水厂设计",
  network: "管网系统",
  drafting: "工程制图",
  viewer3d: "三维示意",
  report: "计算说明",
};

describe("G2 ?tab= 值域冻结点（B7——行为级契约快照）", () => {
  it("冻结集计数恰 21 键（表体行增删即红——断言面完整性锚）", () => {
    expect(FROZEN_KEYS.length).toBe(FROZEN_KEY_COUNT);
  });

  it("21 键逐一 parseZoneParam(`?tab=${v}`) 恰回期望 target（含兼容归一 subpage）", () => {
    for (const { value, target } of FROZEN_KEYS) {
      expect(parseZoneParam(`?tab=${value}`)).toEqual(target);
    }
  });

  it("非法样本 null：未知裸值/空串/子页错挂（design.sheets 等）/三段以上", () => {
    // 未知裸值（表外新键=非法——值域扩键须用户裁决+同步冻结集）
    expect(parseZoneParam("?tab=badvalue")).toBeNull();
    expect(parseZoneParam("?tab=design2")).toBeNull();
    // 空串/缺键
    expect(parseZoneParam("?tab=")).toBeNull();
    expect(parseZoneParam("")).toBeNull();
    expect(parseZoneParam("?project=p1")).toBeNull();
    // 子页错挂（sheets 挂 design/canvas 挂 drafting/子页挂无子页 zone）
    expect(parseZoneParam("?tab=design.sheets")).toBeNull();
    expect(parseZoneParam("?tab=design.siteplan")).toBeNull();
    expect(parseZoneParam("?tab=drafting.canvas")).toBeNull();
    expect(parseZoneParam("?tab=projects.canvas")).toBeNull();
    expect(parseZoneParam("?tab=network.sheets")).toBeNull();
    expect(parseZoneParam("?tab=design.badsub")).toBeNull();
    // 三段以上
    expect(parseZoneParam("?tab=a.b.c")).toBeNull();
    expect(parseZoneParam("?tab=design.canvas.x")).toBeNull();
  });

  it("导出面冻结：V4_ZONES 键序值域恰等冻结数组（增删 zone/键序漂移即红）", () => {
    expect([...V4_ZONES]).toEqual(FROZEN_ZONE_ORDER);
  });

  it("导出面冻结：V4_ZONE_LABELS 键序恰循 V4_ZONES+标签值逐键冻结", () => {
    expect(Object.keys(V4_ZONE_LABELS)).toEqual(FROZEN_ZONE_ORDER);
    expect(V4_ZONE_LABELS).toEqual(FROZEN_LABELS);
  });

  it("冻结键集完备性：V4_ZONES 全体裸值+两子页族全体双段键均在冻结表（冻结表缺行即红）", () => {
    const frozenValues = new Set(FROZEN_KEYS.map((row) => row.value));
    for (const zone of V4_ZONES) {
      if (!frozenValues.has(zone)) {
        throw new Error(`zone ${zone} 裸值缺席冻结表（表体与导出面不同步）`);
      }
    }
    for (const sub of ["design.canvas", "design.analysis", "drafting.sheets", "drafting.siteplan"]) {
      if (!frozenValues.has(sub)) {
        throw new Error(`子页键 ${sub} 缺席冻结表（表体与导出面不同步）`);
      }
    }
  });
});
