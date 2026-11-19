/**
 * v4 导航 URL 参数纯函数单测（B1 骨架批六功能区→b2 壳重组批 2026-11-19
 * 八入口重写：新值域+deliverables 子页+旧值兼容表〔v4 六 zone 值+旧十值
 * 两代〕+?node= 独立通道+初值四级解析〔node→process/task·enum→
 * parameters/缺省 workbench〕）。
 *
 * 输入:  zoneParam.ts 的 parseTabParam/withTabParam/parseNodeParam/
 *        withNodeParam/initialNavTarget（node 环境——纯函数面）
 * 输出:  断言族：①新值域（八键裸值/deliverables 三子页/非法值 null——
 *        坏值/错配子页/三段）②旧值兼容表逐行（两代 20 行——v4 zone 值
 *        9+legacy 十一值）③withTabParam 序列化（裸键/带子页/他键
 *        原序保留）④?node= 独立通道（parse/with/clear 语义+他键保留）
 *        ⑤initialNavTarget 四级解析（合法→node 深链→task/enum 深链→
 *        缺省 workbench）
 *
 * 规格说明（b2 任务书——URL 迁移映射逐行对账）：
 *   - 新值域语法=<nav> 或 deliverables.<subpage>（sheets/siteplan/
 *     report——子页挂错入口=非法）；新值域优先于兼容表；
 *   - 兼容映射在解析期单点收口（mount 不改写地址栏——parse 恒纯读）：
 *     projects→workbench；design 族→process/analysis；network→
 *     workbench；drafting 族/report→deliverables 族；solutions→
 *     parameters；studio.compare→compare；studio.cost/trust/elevation
 *     →analysis；canvas/studio 族/opsdebug→process；
 *   - with 族只动本键他键原序保留（UX1 D2 承袭公式）；产出无 "?" 前缀
 *    查询串（拼接面在消费方）；
 *   - ?node= 为对象选中真相（独立键读写互不覆盖——ENG5 D6 双轨形承袭：
 *     node/task/enum 三键各自独立）；null 语义=未选与移除统一；
 *   - initialNavTarget 四级：?tab= 合法〔含兼容归一〕→用之；无 ?tab=
 *    但有 ?node=→process；有 ?task=/?enum=→parameters；缺省 workbench
 *    （新壳着陆页——旧缺省 design 的迁移映射见兼容表）。
 */
import { describe, expect, it } from "vitest";

import {
  initialNavTarget,
  parseNodeParam,
  parseTabParam,
  withNodeParam,
  withTabParam,
  type NavTarget,
} from "./zoneParam";

describe("b2 八入口值域（新值语法）", () => {
  it("八键裸值直通（deliverables 不带子面=子页缺省 sheets）", () => {
    expect(parseTabParam("?tab=workbench")).toEqual({ nav: "workbench" });
    expect(parseTabParam("?tab=process")).toEqual({ nav: "process" });
    expect(parseTabParam("?tab=parameters")).toEqual({ nav: "parameters" });
    expect(parseTabParam("?tab=analysis")).toEqual({ nav: "analysis" });
    expect(parseTabParam("?tab=compare")).toEqual({ nav: "compare" });
    expect(parseTabParam("?tab=deliverables")).toEqual({ nav: "deliverables" });
    expect(parseTabParam("?tab=viewer3d")).toEqual({ nav: "viewer3d" });
    expect(parseTabParam("?tab=ai")).toEqual({ nav: "ai" });
  });

  it("deliverables 三子页合法形（sheets/siteplan/report）", () => {
    expect(parseTabParam("?tab=deliverables.sheets")).toEqual({
      nav: "deliverables",
      subpage: "sheets",
    });
    expect(parseTabParam("?tab=deliverables.siteplan")).toEqual({
      nav: "deliverables",
      subpage: "siteplan",
    });
    expect(parseTabParam("?tab=deliverables.report")).toEqual({
      nav: "deliverables",
      subpage: "report",
    });
  });

  it("非法值 null 族（坏值/子页挂错入口/三段/空值/缺键）", () => {
    expect(parseTabParam("?tab=design")).not.toBeNull(); // 兼容表命中（下述）
    expect(parseTabParam("?tab=nosuch")).toBeNull();
    expect(parseTabParam("?tab=analysis.sheets")).toBeNull(); // 子页挂错入口
    expect(parseTabParam("?tab=deliverables.nosuch")).toBeNull();
    expect(parseTabParam("?tab=process.canvas")).toBeNull();
    expect(parseTabParam("?tab=design.canvas.extra")).toBeNull(); // 三段
    expect(parseTabParam("?tab=")).toBeNull();
    expect(parseTabParam("?node=municipal_aao")).toBeNull(); // 缺 tab 键
    expect(parseTabParam("")).toBeNull();
  });
});

describe("b2 兼容归一表（两代旧值→新导航——逐行对账）", () => {
  it("v4 六 zone 值（b1 及以前 ?tab= 深链）", () => {
    expect(parseTabParam("?tab=projects")).toEqual({ nav: "workbench" });
    expect(parseTabParam("?tab=design")).toEqual({ nav: "process" });
    expect(parseTabParam("?tab=design.canvas")).toEqual({ nav: "process" });
    expect(parseTabParam("?tab=design.analysis")).toEqual({ nav: "analysis" });
    expect(parseTabParam("?tab=network")).toEqual({ nav: "workbench" });
    expect(parseTabParam("?tab=drafting")).toEqual({ nav: "deliverables" });
    expect(parseTabParam("?tab=drafting.sheets")).toEqual({
      nav: "deliverables",
    });
    expect(parseTabParam("?tab=drafting.siteplan")).toEqual({
      nav: "deliverables",
      subpage: "siteplan",
    });
    expect(parseTabParam("?tab=report")).toEqual({
      nav: "deliverables",
      subpage: "report",
    });
  });

  it("legacy 槽路由期十值（含 studio 族展开形）", () => {
    expect(parseTabParam("?tab=canvas")).toEqual({ nav: "process" });
    expect(parseTabParam("?tab=solutions")).toEqual({ nav: "parameters" });
    expect(parseTabParam("?tab=studio")).toEqual({ nav: "process" });
    expect(parseTabParam("?tab=studio.study")).toEqual({ nav: "process" });
    expect(parseTabParam("?tab=studio.cost")).toEqual({ nav: "analysis" });
    expect(parseTabParam("?tab=studio.compare")).toEqual({ nav: "compare" });
    expect(parseTabParam("?tab=studio.trust")).toEqual({ nav: "analysis" });
    expect(parseTabParam("?tab=elevation")).toEqual({ nav: "analysis" });
    expect(parseTabParam("?tab=siteplan")).toEqual({
      nav: "deliverables",
      subpage: "siteplan",
    });
    expect(parseTabParam("?tab=studio.drawings")).toEqual({
      nav: "deliverables",
    });
    expect(parseTabParam("?tab=opsdebug")).toEqual({ nav: "process" });
  });
});

describe("b2 withTabParam 序列化", () => {
  it("裸键/带子页两形+他键原序保留", () => {
    expect(withTabParam("", { nav: "process" })).toBe("tab=process");
    expect(
      withTabParam("?project=p1&tab=analysis", { nav: "compare" }),
    ).toBe("project=p1&tab=compare");
    expect(
      withTabParam("?tab=process&node=municipal_aao", {
        nav: "deliverables",
        subpage: "report",
      }),
    ).toBe("tab=deliverables.report&node=municipal_aao");
    expect(withTabParam("?tab=x&task=t1", { nav: "workbench" })).toBe(
      "tab=workbench&task=t1",
    );
  });
});

describe("?node= 独立通道（ENG5 D6 双轨形承袭）", () => {
  it("parse/with/clear 语义+他键保留", () => {
    expect(parseNodeParam("?node=municipal_aao&tab=process")).toBe(
      "municipal_aao",
    );
    expect(parseNodeParam("?tab=process")).toBeNull();
    expect(parseNodeParam("?node=")).toBeNull();
    expect(withNodeParam("?tab=process", "municipal_aao")).toBe(
      "tab=process&node=municipal_aao",
    );
    expect(withNodeParam("?tab=process&node=old", "municipal_aao")).toBe(
      "tab=process&node=municipal_aao",
    );
    // null=解除选中剥键（task/enum 不动）
    expect(withNodeParam("?tab=process&node=old&task=t1", null)).toBe(
      "tab=process&task=t1",
    );
  });
});

describe("initialNavTarget 初值四级解析", () => {
  it("①合法 ?tab=（含兼容归一）→用之", () => {
    expect(initialNavTarget("?tab=compare")).toEqual({ nav: "compare" });
    expect(initialNavTarget("?tab=design.analysis")).toEqual({
      nav: "analysis",
    });
    expect(initialNavTarget("?tab=report")).toEqual({
      nav: "deliverables",
      subpage: "report",
    });
  });

  it("②无 ?tab= 但 ?node=→process（画布选中语境深链）", () => {
    expect(initialNavTarget("?node=municipal_aao")).toEqual({
      nav: "process",
    });
    expect(initialNavTarget("?project=p1&node=x")).toEqual({
      nav: "process",
    });
  });

  it("③无 ?tab=/node= 但 ?task=/?enum=→parameters（方案/联合卡消费面）", () => {
    expect(initialNavTarget("?task=t-1")).toEqual({ nav: "parameters" });
    expect(initialNavTarget("?enum=e-1&project=p1")).toEqual({
      nav: "parameters",
    });
  });

  it("④缺省 workbench（新壳着陆页）+非法 tab 同落缺省", () => {
    expect(initialNavTarget("")).toEqual({ nav: "workbench" });
    expect(initialNavTarget("?project=p1")).toEqual({ nav: "workbench" });
    expect(initialNavTarget("?tab=nosuch")).toEqual({ nav: "workbench" });
  });

  it("深链层与缺省层拆分自证：node 优先于 task（四级序）", () => {
    expect(initialNavTarget("?node=aao&task=t-1")).toEqual({
      nav: "process",
    });
  });
});

describe("NavTarget 类型面（编译期值域——防挂错分支回归）", () => {
  it("deliverables 子页字面量收窄（type-level via 运行时映射）", () => {
    const target: NavTarget = { nav: "deliverables", subpage: "siteplan" };
    expect("subpage" in target && target.subpage).toBe("siteplan");
  });
});
