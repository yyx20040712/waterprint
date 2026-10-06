/**
 * app 地基纯函数单测：URL project/task/tab 参数解析/合成（D5 单一真相+
 * deep-link+UX1 S4 路由态；M1 批 A 级全文改写——?tab= 两级值域+兼容映射）。
 *
 * 输入:  projectParam.ts 的 project/task/enum 族函数（零改承袭）+tabParam
 *        两函数两级形态（parseTabParam → TabTarget | null；withTabParam ←
 *        TabTarget）+router.tsx 的 SLOTS/STUDIO_SUBFACES 常量（node 环境）
 * 输出:  断言族：①值域（四裸槽/studio→study 归一/studio.X 双段五子面/
 *        非法值 null——badvalue/studio.badsub/canvas.study/三段）②兼容映射
 *        全表十行（旧十值→目标 TabTarget 逐行——mapping-2b4 §B 表逐字）
 *        ③边缘语义 b（studio 无子面默认 study）④withTabParam 两级序列化
 *        （裸槽/复合/他键原序保留透传）⑤project/task/enum 族既有断言
 *        零改保留
 *
 * 规格说明（FE3 批 6b 段一，D6-②；UX1 批 D2；M1 批 2026-10-06 mapping-2b4
 *   §B/§C——A 级随迁全文改写；旧「ROUTES 六成员」用例名措辞陈旧勘正随
 *   改写吸收〔probe K8 注记〕，新断言族=SLOTS/STUDIO_SUBFACES 全成员）：
 *   - parse 入参形态=location.search 原样（含 "?" 前缀——URLSearchParams
 *     忽略首 "?"）；with 族产出无 "?" 前缀查询串（replaceState 的 pathname
 *     拼接面在消费方，本函数保持纯字符串进出）；
 *   - 「不清其余参数」：with 族只动本键，他键原序保留（FE3 起锁定公式，
 *     tab 键透传语义同锁）；
 *   - null 语义统一=未选与移除（合法值缺省同走 null，不引入第二空态）；
 *   - M1 两级值域：?tab=<槽> 或 ?tab=studio.<子面>（点分复合——R-D2
 *     命名空间原则）；兼容归一=解析期单点收口（旧十值映射），新值域
 *     优先于兼容表（防未来扩值歧义）；边缘语义 a/b 的地址栏不改写面在
 *     App mount 侧（parse 恒不改 URL——本文件纯函数面）。
 */
import { describe, expect, it } from "vitest";

import { SLOTS, STUDIO_SUBFACES } from "./router";
import {
  clearEnumParam,
  clearTaskParam,
  normalizeProjectId,
  parseEnumParam,
  parseProjectParam,
  parseTabParam,
  parseTaskParam,
  withEnumParam,
  withProjectParam,
  withTabParam,
  withTaskParam,
} from "./projectParam";

describe("parseProjectParam（初值直读 location.search）", () => {
  it("缺失 → null（空串/裸 ?/他参数形态）", () => {
    expect(parseProjectParam("")).toBeNull();
    expect(parseProjectParam("?")).toBeNull();
    expect(parseProjectParam("?tab=canvas")).toBeNull();
  });

  it("空串 → null（?project= 视同未选）", () => {
    expect(parseProjectParam("?project=")).toBeNull();
  });

  it("合法值回读（? 前缀与裸 search 两形态同值）", () => {
    expect(parseProjectParam("?project=wp-2026-a1")).toBe("wp-2026-a1");
    expect(parseProjectParam("project=wp-2026-a1")).toBe("wp-2026-a1");
  });

  it("多参数中定位 project（他参数不干扰）", () => {
    expect(parseProjectParam("?tab=canvas&project=p1&x=2")).toBe("p1");
  });

  it("编码字符往返：withProjectParam 编码 → parseProjectParam 解码", () => {
    const id = "池 a/中-1";
    const search = withProjectParam("", id);
    expect(parseProjectParam(`?${search}`)).toBe(id);
  });
});

describe("withProjectParam（replaceState 同步面）", () => {
  it("新增 project 不清其余参数（他键原序保留）", () => {
    const search = withProjectParam("?tab=canvas&cond=design", "p1");
    expect(search).toBe("tab=canvas&cond=design&project=p1");
  });

  it("已存在 project 时替换该键（他参数不动）", () => {
    const search = withProjectParam("?project=old&tab=canvas", "new");
    expect(search).toBe("project=new&tab=canvas");
  });

  it("null → 移除 project 键（其余保留）", () => {
    const search = withProjectParam("?project=p1&tab=canvas", null);
    expect(search).toBe("tab=canvas");
    expect(parseProjectParam(`?${search}`)).toBeNull();
  });

  it("编码字符：特殊字符百分号编码进查询串（deep-link URL 安全）", () => {
    expect(withProjectParam("", "池 a/中-1")).toBe(
      "project=%E6%B1%A0+a%2F%E4%B8%AD-1",
    );
  });

  it("HC25-F4：切项目剔除 enum/task 两键（任务 id 无项目分区——旧项目深链不残留）", () => {
    const search = withProjectParam(
      "?project=old&enum=e-1&task=t-1&tab=canvas",
      "new",
    );
    expect(search).toBe("project=new&tab=canvas");
    expect(parseEnumParam(`?${search}`)).toBeNull();
    expect(parseTaskParam(`?${search}`)).toBeNull();
  });

  it("HC25-F4：剔除面恰两键——其余键（tab 等）保留；无两键时语义不动", () => {
    expect(withProjectParam("?project=p1&tab=canvas&cond=design", "p2")).toBe(
      "project=p2&tab=canvas&cond=design",
    );
    expect(withProjectParam("?enum=e-1&task=t-1", "p1")).toBe("project=p1");
    expect(withProjectParam("?project=p1&enum=e-1&task=t-1&tab=x", null)).toBe(
      "tab=x",
    );
  });
});

describe("taskParam 三函数（FE6 D3——?task= 与 ?project= 双参共存）", () => {
  it("parseTaskParam：缺失/空串 → null（他参数不干扰）", () => {
    expect(parseTaskParam("")).toBeNull();
    expect(parseTaskParam("?project=p1")).toBeNull();
    expect(parseTaskParam("?task=")).toBeNull();
    expect(parseTaskParam("?tab=canvas")).toBeNull();
  });

  it("parseTaskParam：合法值回读（? 前缀与裸 search 两形态）", () => {
    expect(parseTaskParam("?task=t-abc-1")).toBe("t-abc-1");
    expect(parseTaskParam("task=t-abc-1")).toBe("t-abc-1");
  });

  it("parseTaskParam：与 ?project= 共存互不干扰", () => {
    expect(parseTaskParam("?project=p1&task=t-1")).toBe("t-1");
    expect(parseProjectParam("?project=p1&task=t-1")).toBe("p1");
  });

  it("withTaskParam：新增 task 不清 project（他键保留）", () => {
    expect(withTaskParam("?project=p1", "t-1")).toBe("project=p1&task=t-1");
  });

  it("withTaskParam：已存在 task 时替换（project 不动）", () => {
    expect(withTaskParam("?project=p1&task=old", "new")).toBe(
      "project=p1&task=new",
    );
  });

  it("withTaskParam：null/空串 → 移除 task 键", () => {
    expect(withTaskParam("?project=p1&task=t-1", null)).toBe("project=p1");
    expect(withTaskParam("?project=p1&task=t-1", "")).toBe("project=p1");
  });

  it("clearTaskParam：显式移除 task（project 与他键原样保留）", () => {
    expect(clearTaskParam("?project=p1&task=t-1&x=2")).toBe("project=p1&x=2");
    expect(clearTaskParam("?task=t-1")).toBe("");
  });

  it("回写-回读往返：withTaskParam → parseTaskParam 同值", () => {
    const search = withTaskParam("?project=p1", "enum-42");
    expect(parseTaskParam(`?${search}`)).toBe("enum-42");
  });
});

describe("值域常量（M1——SLOTS/STUDIO_SUBFACES 全成员冻结面）", () => {
  it("SLOTS 五槽次序=canvas(默认)/siteplan/viewer3d/elevation/studio（draft-ia-v3 B-1 逐字）", () => {
    expect(SLOTS).toEqual([
      "canvas",
      "siteplan",
      "viewer3d",
      "elevation",
      "studio",
    ]);
  });

  it("STUDIO_SUBFACES 五子面（仅 studio 槽可带——点分复合命名空间）", () => {
    expect(STUDIO_SUBFACES).toEqual([
      "study",
      "drawings",
      "cost",
      "compare",
      "trust",
    ]);
  });
});

describe("parseTabParam 两级解析（M1——?tab=<槽> 或 studio.<子面>）", () => {
  it("四非 studio 槽单值合法 → {slot}（subface 缺席）", () => {
    expect(parseTabParam("?tab=canvas")).toEqual({ slot: "canvas" });
    expect(parseTabParam("tab=siteplan")).toEqual({ slot: "siteplan" });
    expect(parseTabParam("?tab=viewer3d")).toEqual({ slot: "viewer3d" });
    expect(parseTabParam("?tab=elevation")).toEqual({ slot: "elevation" });
  });

  it("边缘语义 b：?tab=studio 无子面 → 默认子面 study（归一恒带 subface）", () => {
    expect(parseTabParam("?tab=studio")).toEqual({
      slot: "studio",
      subface: "study",
    });
  });

  it("studio.X 双段五子面全成员合法（? 前缀与裸 search 两形态）", () => {
    for (const subface of STUDIO_SUBFACES) {
      expect(parseTabParam(`?tab=studio.${subface}`)).toEqual({
        slot: "studio",
        subface,
      });
    }
    expect(parseTabParam("tab=studio.cost")).toEqual({
      slot: "studio",
      subface: "cost",
    });
  });

  it("非法值 → null：未知槽/非法子面/非 studio 槽带子面/三段以上", () => {
    expect(parseTabParam("?tab=badvalue")).toBeNull();
    expect(parseTabParam("?tab=studio.badsub")).toBeNull();
    expect(parseTabParam("?tab=canvas.study")).toBeNull();
    expect(parseTabParam("?tab=studio.study.x")).toBeNull();
    expect(parseTabParam("?tab=a.b.c")).toBeNull();
    expect(parseTabParam("?tab=studio.")).toBeNull();
  });

  it("缺失/空串 → null（冻结面外不造路由——他参数不干扰）", () => {
    expect(parseTabParam("")).toBeNull();
    expect(parseTabParam("?")).toBeNull();
    expect(parseTabParam("?tab=")).toBeNull();
    expect(parseTabParam("?project=p1")).toBeNull();
  });
});

describe("兼容映射全表十行（M1——旧十值→两级值域，解析期单点归一）", () => {
  it("canvas/siteplan/viewer3d/elevation 同名直通（新旧同形——新值域优先）", () => {
    expect(parseTabParam("?tab=canvas")).toEqual({ slot: "canvas" });
    expect(parseTabParam("?tab=siteplan")).toEqual({ slot: "siteplan" });
    expect(parseTabParam("?tab=viewer3d")).toEqual({ slot: "viewer3d" });
    expect(parseTabParam("?tab=elevation")).toEqual({ slot: "elevation" });
  });

  it("solutions → studio.study（?task= 语义重定向随 M6/M7 批）", () => {
    expect(parseTabParam("?tab=solutions")).toEqual({
      slot: "studio",
      subface: "study",
    });
  });

  it("drawings/cost/compare/trust → studio.同名（四行逐行）", () => {
    expect(parseTabParam("?tab=drawings")).toEqual({
      slot: "studio",
      subface: "drawings",
    });
    expect(parseTabParam("?tab=cost")).toEqual({
      slot: "studio",
      subface: "cost",
    });
    expect(parseTabParam("?tab=compare")).toEqual({
      slot: "studio",
      subface: "compare",
    });
    expect(parseTabParam("?tab=trust")).toEqual({
      slot: "studio",
      subface: "trust",
    });
  });

  it("opsdebug → canvas（视图不变——地址栏不改写面在 App mount 侧）", () => {
    expect(parseTabParam("?tab=opsdebug")).toEqual({ slot: "canvas" });
  });

  it("新值域优先于兼容表（同形值先查 SLOTS/子面面再查兼容表）", () => {
    // 十旧值与五槽值域重叠恰四值（canvas/siteplan/viewer3d/elevation）
    // ——新旧重叠值同形直通（次序锁=LEGACY_TAB_COMPAT 在 SLOTS 之后
    // 单点——projectParam.ts 实现序）
    expect(parseTabParam("?tab=studio.study")).toEqual({
      slot: "studio",
      subface: "study",
    });
    expect(parseTabParam("?tab=solutions")).toEqual({
      slot: "studio",
      subface: "study",
    });
  });
});

describe("withTabParam 两级序列化（UX1 S4 承袭——只动 tab 键）", () => {
  it("裸槽值：target 无 subface → tab=<槽>", () => {
    expect(withTabParam("", { slot: "canvas" })).toBe("tab=canvas");
    expect(withTabParam("?project=p1", { slot: "viewer3d" })).toBe(
      "project=p1&tab=viewer3d",
    );
  });

  it("复合值：studio 子面 → tab=studio.<子面>", () => {
    expect(withTabParam("", { slot: "studio", subface: "drawings" })).toBe(
      "tab=studio.drawings",
    );
    expect(withTabParam("?project=p1", { slot: "studio", subface: "trust" })).toBe(
      "project=p1&tab=studio.trust",
    );
  });

  it("已存在 tab 时替换该键（覆盖旧值——他参数不动）", () => {
    expect(
      withTabParam("?tab=canvas&project=p1", { slot: "studio", subface: "cost" }),
    ).toBe("tab=studio.cost&project=p1");
  });

  it("他键原序保留透传（project/task/enum——FE3 已锁语义同锁）", () => {
    expect(
      withTabParam("?project=p1&task=t-1&enum=e-1", { slot: "canvas" }),
    ).toBe("project=p1&task=t-1&enum=e-1&tab=canvas");
  });

  it("回写-回读往返：withTabParam → parseTabParam 同值（归一形态）", () => {
    expect(
      parseTabParam(
        `?${withTabParam("?project=p1", { slot: "studio", subface: "trust" })}`,
      ),
    ).toEqual({ slot: "studio", subface: "trust" });
    expect(parseTabParam(`?${withTabParam("?task=t-1", { slot: "elevation" })}`)).toEqual(
      { slot: "elevation" },
    );
  });
});

describe("normalizeProjectId（R2/一审 M-2——.wp 尾缀归一）", () => {
  it("带 .wp 尾缀归一：列表 id → 裸 id（与 Select 选项路径同源）", () => {
    expect(normalizeProjectId("88c6bdfba89844c7.wp")).toBe(
      "88c6bdfba89844c7",
    );
  });

  it("裸 id 不动（幂等——已归一值再过不变形）", () => {
    expect(normalizeProjectId("wp-2026-a1")).toBe("wp-2026-a1");
  });
});

describe("enumParam（ENG5 D6：?enum= 枚举任务轨——与 ?task= 双参并存互不覆盖）", () => {
  it("parseEnumParam：缺失/空串 → null（task/tab 他参数不干扰）", () => {
    expect(parseEnumParam("")).toBeNull();
    expect(parseEnumParam("?project=p1")).toBeNull();
    expect(parseEnumParam("?enum=")).toBeNull();
    expect(parseEnumParam("?task=t-1&tab=solutions")).toBeNull();
  });

  it("parseEnumParam：合法值回读（? 前缀与裸 search 两形态）", () => {
    expect(parseEnumParam("?enum=e-abc-1")).toBe("e-abc-1");
    expect(parseEnumParam("enum=e-abc-1")).toBe("e-abc-1");
  });

  it("parseEnumParam：与 ?task=/?project= 共存互不干扰（两轨并存）", () => {
    expect(parseEnumParam("?project=p1&task=t-1&enum=e-1")).toBe("e-1");
    expect(parseTaskParam("?project=p1&task=t-1&enum=e-1")).toBe("t-1");
  });

  it("withEnumParam：新增 enum 不清 task/project（他键保留）", () => {
    expect(withEnumParam("?project=p1&task=t-1", "e-1")).toBe(
      "project=p1&task=t-1&enum=e-1",
    );
  });

  it("withEnumParam：已存在 enum 时替换（task 不动——互不覆盖）", () => {
    expect(withEnumParam("?task=t-1&enum=old", "new")).toBe("task=t-1&enum=new");
  });

  it("withEnumParam：null/空串 → 移除 enum 键（他键保留）", () => {
    expect(withEnumParam("?project=p1&enum=e-1&task=t-1", null)).toBe(
      "project=p1&task=t-1",
    );
    expect(withEnumParam("?enum=e-1", "")).toBe("");
  });

  it("clearEnumParam：显式移除 enum（task 与他键原样保留）", () => {
    expect(clearEnumParam("?enum=e-1&task=t-1&x=2")).toBe("task=t-1&x=2");
    expect(clearEnumParam("?enum=e-1")).toBe("");
  });

  it("回写-回读往返：withEnumParam → parseEnumParam 同值", () => {
    expect(parseEnumParam(`?${withEnumParam("?project=p1", "e-9")}`)).toBe("e-9");
  });

  it("双轨独立往返：enum 回写不动 task 轨，task 回写不动 enum 轨", () => {
    const both = withEnumParam("?task=t-1", "e-1");
    expect(parseTaskParam(`?${both}`)).toBe("t-1");
    const afterTask = withTaskParam(`?${both}`, "t-2");
    expect(parseEnumParam(`?${afterTask}`)).toBe("e-1");
    expect(parseTaskParam(`?${afterTask}`)).toBe("t-2");
  });
});
