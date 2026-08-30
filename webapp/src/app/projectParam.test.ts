/**
 * app 地基纯函数单测：URL project/task/tab 参数解析/合成（D5 单一真相+
 * deep-link+UX1 S4 路由态）。
 *
 * 输入:  projectParam.ts 的 parseProjectParam/withProjectParam/tabParam
 *        两函数（node 环境）
 * 输出:  断言：缺失→null/空串→null/合法值回读/多参数保留/编码字符往返/
 *        tab 非法值→null（ROUTES 成员校验）
 *
 * 规格说明（FE3 批 6b 段一，D6-②；UX1 批 D2 增 tab 组）：
 *   - parse 入参形态=location.search 原样（含 "?" 前缀——URLSearchParams
 *     忽略首 "?"）；withProjectParam 产出无 "?" 前缀查询串（replaceState
 *     的 pathname 拼接面在 viewer3dPane，本函数保持纯字符串进出）；
 *   - 「不清其余参数」：withProjectParam 只动 project 键，他键原序保留；
 *   - null 语义统一=未选与移除（合法值缺省同走 null，不引入第二空态）；
 *   - UX1 D2 tab 组：parseTabParam=ROUTES 成员校验（非法值 null——
 *     冻结面外不造路由）；withTabParam 只动 tab 键（与既有「他键保留」
 *     公式互证——tab 键自 FE3 起即作测试道具透传，生产消费自 UX1 起）。
 */
import { describe, expect, it } from "vitest";

import {
  clearTaskParam,
  normalizeProjectId,
  parseProjectParam,
  parseTabParam,
  parseTaskParam,
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

describe("tabParam 两函数（UX1 S4——?tab= 路由态进 URL）", () => {
  it("parseTabParam：合法值回读（ROUTES 六成员——? 前缀与裸 search 两形态）", () => {
    expect(parseTabParam("?tab=drawings")).toBe("drawings");
    expect(parseTabParam("tab=cost")).toBe("cost");
    expect(parseTabParam("?tab=canvas")).toBe("canvas");
  });

  it("parseTabParam：非法值/缺失/空串 → null（ROUTES 成员外不造路由）", () => {
    expect(parseTabParam("?tab=bogus")).toBeNull();
    expect(parseTabParam("")).toBeNull();
    expect(parseTabParam("?")).toBeNull();
    expect(parseTabParam("?tab=")).toBeNull();
    expect(parseTabParam("?project=p1")).toBeNull();
  });

  it("withTabParam：新增 tab 不清其余参数（project/task 他键原序保留）", () => {
    const search = withTabParam("?project=p1&cond=design", "solutions");
    expect(search).toBe("project=p1&cond=design&tab=solutions");
  });

  it("withTabParam：已存在 tab 时替换该键（覆盖旧值——他参数不动）", () => {
    const search = withTabParam("?tab=canvas&project=p1", "cost");
    expect(search).toBe("tab=cost&project=p1");
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
