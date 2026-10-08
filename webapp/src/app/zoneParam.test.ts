/**
 * v4 zone URL 参数纯函数单测（B1 骨架批 2026-10-09——?ia=v4 特性开关下
 * 六功能区+子页两级值域+旧十值兼容表+?node= 独立通道）。
 *
 * 输入:  zoneParam.ts 的 parseZoneParam/withZoneParam/parseNodeParam/
 *        withNodeParam/parseIaParam/initialZoneTarget（node 环境——纯函数面）
 * 输出:  断言族：①新值域（六 zone 裸值/design 与 drafting 双段子页/非法值
 *        null——坏值/错配子页/三段）②旧值兼容表逐行（十二行——旧十值含
 *        studio 族展开形）③withZoneParam 序列化（裸 zone/带子页/他键原序
 *        保留）④?node= 独立通道（parse/with/clear 语义+他键保留）⑤?ia=
 *        开关（v4/其余 null）⑥initialZoneTarget 三级解析（合法→深链→缺省
 *        design）
 *
 * 规格说明（B1 任务书 §二.① URL 映射表——逐行对账）：
 *   - 新值域语法=<zone> 或 <zone>.<subpage>（点分复合——design.subpage∈
 *     {canvas,analysis}、drafting.subpage∈{sheets,siteplan}；子页挂错
 *     zone=非法）；新值域优先于兼容表；
 *   - 兼容映射在解析期单点收口（mount 不改写地址栏——parse 恒纯读）：
 *     canvas/solutions/studio/studio.study→design；studio.cost/compare/
 *     trust/elevation→design.analysis（高程纵断=分析视图——定名消歧 W2）；
 *     siteplan→drafting.siteplan；studio.drawings→drafting；opsdebug→
 *     design（视图不变语义沿 M1 口径）；viewer3d→viewer3d（同名直通）；
 *   - with 族只动本键他键原序保留（UX1 D2 承袭公式）；产出无 "?" 前缀
 *     查询串（拼接面在消费方）；
 *   - ?node= 为对象选中真相（独立键读写互不覆盖——ENG5 D6 双轨形承袭：
 *     node/task/enum 三键各自独立）；null 语义=未选与移除统一；
 *   - initialZoneTarget 三级：?tab= 合法〔含兼容归一〕→用之；无 ?tab=
 *     但有 ?node=/?task=/?enum=→design（深链意图——M1 边缘语义 c 对称）；
 *     缺省 design（新壳默认区≠canvas 裸值）。
 */
import { describe, expect, it } from "vitest";

import {
  initialZoneTarget,
  parseIaParam,
  parseNodeParam,
  parseZoneParam,
  withNodeParam,
  withZoneParam,
  type V4ZoneTarget,
} from "./zoneParam";

describe("B1 v4 zone 值域（新值两级语法）", () => {
  it("六 zone 裸值直通（design/drafting 不带子面=子页缺省）", () => {
    expect(parseZoneParam("?tab=projects")).toEqual({ zone: "projects" });
    expect(parseZoneParam("?tab=design")).toEqual({ zone: "design" });
    expect(parseZoneParam("?tab=network")).toEqual({ zone: "network" });
    expect(parseZoneParam("?tab=drafting")).toEqual({ zone: "drafting" });
    expect(parseZoneParam("?tab=viewer3d")).toEqual({ zone: "viewer3d" });
    expect(parseZoneParam("?tab=report")).toEqual({ zone: "report" });
  });

  it("design/drafting 双段子页合法形（design.canvas/analysis+drafting.sheets/siteplan）", () => {
    expect(parseZoneParam("?tab=design.canvas")).toEqual({
      zone: "design",
      subpage: "canvas",
    });
    expect(parseZoneParam("?tab=design.analysis")).toEqual({
      zone: "design",
      subpage: "analysis",
    });
    expect(parseZoneParam("?tab=drafting.sheets")).toEqual({
      zone: "drafting",
      subpage: "sheets",
    });
    expect(parseZoneParam("?tab=drafting.siteplan")).toEqual({
      zone: "drafting",
      subpage: "siteplan",
    });
  });

  it("非法值 null（未知裸值/子页挂错 zone/三段以上/空值）", () => {
    expect(parseZoneParam("?tab=badvalue")).toBeNull();
    expect(parseZoneParam("?tab=projects.canvas")).toBeNull();
    expect(parseZoneParam("?tab=network.sheets")).toBeNull();
    expect(parseZoneParam("?tab=design.badsub")).toBeNull();
    expect(parseZoneParam("?tab=drafting.analysis")).toBeNull();
    expect(parseZoneParam("?tab=a.b.c")).toBeNull();
    expect(parseZoneParam("")).toBeNull();
    expect(parseZoneParam("?project=p1")).toBeNull();
  });
});

describe("B1 v4 zone 兼容映射（旧十值→新值——任务书 §二.① 表逐行）", () => {
  const rows: { old: string; target: V4ZoneTarget }[] = [
    { old: "canvas", target: { zone: "design" } },
    { old: "solutions", target: { zone: "design" } },
    { old: "studio", target: { zone: "design" } },
    { old: "studio.study", target: { zone: "design" } },
    { old: "studio.cost", target: { zone: "design", subpage: "analysis" } },
    { old: "studio.compare", target: { zone: "design", subpage: "analysis" } },
    { old: "studio.trust", target: { zone: "design", subpage: "analysis" } },
    { old: "elevation", target: { zone: "design", subpage: "analysis" } },
    { old: "siteplan", target: { zone: "drafting", subpage: "siteplan" } },
    { old: "studio.drawings", target: { zone: "drafting" } },
    { old: "viewer3d", target: { zone: "viewer3d" } },
    { old: "opsdebug", target: { zone: "design" } },
  ];

  it.each(rows)("旧值 $old → 归一目标", ({ old, target }) => {
    expect(parseZoneParam(`?project=p1&tab=${old}`)).toEqual(target);
  });

  it("新值域优先于兼容表（未来扩值歧义防线——canvas 不会先命中 design 槽）", () => {
    // canvas 在新值域非 zone 成员——必经兼容表；design 为新值域成员即使
    // 兼容表未来扩 design 键也以新值域直读为准（此处以 studio 族例证：
    // studio.* 双段先走新值域校验失败再落兼容表命中）
    expect(parseZoneParam("?tab=studio.cost")).toEqual({
      zone: "design",
      subpage: "analysis",
    });
  });
});

describe("B1 withZoneParam 序列化（只动 tab 键——他键原序保留）", () => {
  it("裸 zone 与带子页两形", () => {
    expect(withZoneParam("?project=p1", { zone: "design" })).toBe(
      "project=p1&tab=design",
    );
    expect(
      withZoneParam("?project=p1", { zone: "design", subpage: "analysis" }),
    ).toBe("project=p1&tab=design.analysis");
    expect(
      withZoneParam("", { zone: "drafting", subpage: "siteplan" }),
    ).toBe("tab=drafting.siteplan");
    expect(withZoneParam("?project=p1", { zone: "viewer3d" })).toBe(
      "project=p1&tab=viewer3d",
    );
  });

  it("他键原序保留+tab 键覆写（project/node/task/enum 不动）", () => {
    expect(
      withZoneParam("?project=p1&node=u1&tab=design", { zone: "network" }),
    ).toBe("project=p1&node=u1&tab=network");
    expect(
      withZoneParam("?task=t1&project=p1", { zone: "design", subpage: "canvas" }),
    ).toBe("task=t1&project=p1&tab=design.canvas");
  });
});

describe("B1 ?node= 独立通道（对象选中真相——与 task/enum 互不覆盖）", () => {
  it("parse/with/clear 三态（null 语义=未选与移除统一）", () => {
    expect(parseNodeParam("?node=u1")).toBe("u1");
    expect(parseNodeParam("?project=p1")).toBeNull();
    expect(parseNodeParam("?node=")).toBeNull();
    expect(withNodeParam("?project=p1", "u1")).toBe("project=p1&node=u1");
    expect(withNodeParam("?project=p1&node=u1", null)).toBe("project=p1");
    // 已有键覆写+他键原序保留
    expect(withNodeParam("?node=u1&task=t1", "u2")).toBe("node=u2&task=t1");
  });
});

describe("B1 ?ia= 特性开关", () => {
  it("v4 识别+其余值/null 关闭（缺省=M1 现行壳）", () => {
    expect(parseIaParam("?ia=v4")).toBe("v4");
    expect(parseIaParam("?ia=v3")).toBeNull();
    expect(parseIaParam("?project=p1")).toBeNull();
    expect(parseIaParam("")).toBeNull();
  });
});

describe("B1 initialZoneTarget 三级解析", () => {
  it("①?tab= 合法（含兼容归一）→用之 ②深链→design ③缺省 design", () => {
    expect(initialZoneTarget("?tab=drafting.siteplan")).toEqual({
      zone: "drafting",
      subpage: "siteplan",
    });
    expect(initialZoneTarget("?tab=elevation")).toEqual({
      zone: "design",
      subpage: "analysis",
    });
    expect(initialZoneTarget("?node=u1")).toEqual({ zone: "design" });
    expect(initialZoneTarget("?task=t1")).toEqual({ zone: "design" });
    expect(initialZoneTarget("?enum=e1")).toEqual({ zone: "design" });
    expect(initialZoneTarget("?project=p1")).toEqual({ zone: "design" });
    expect(initialZoneTarget("")).toEqual({ zone: "design" });
  });
});
