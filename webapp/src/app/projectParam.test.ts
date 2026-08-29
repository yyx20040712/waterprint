/**
 * app 地基纯函数单测：URL project 参数解析/合成（D5 单一真相+deep-link）。
 *
 * 输入:  projectParam.ts 的 parseProjectParam/withProjectParam（node 环境）
 * 输出:  断言：缺失→null/空串→null/合法值回读/多参数保留/编码字符往返
 *
 * 规格说明（FE3 批 6b 段一，D6-②）：
 *   - parse 入参形态=location.search 原样（含 "?" 前缀——URLSearchParams
 *     忽略首 "?"）；withProjectParam 产出无 "?" 前缀查询串（replaceState
 *     的 pathname 拼接面在 viewer3dPane，本函数保持纯字符串进出）；
 *   - 「不清其余参数」：withProjectParam 只动 project 键，他键原序保留；
 *   - null 语义统一=未选与移除（合法值缺省同走 null，不引入第二空态）。
 */
import { describe, expect, it } from "vitest";

import {
  normalizeProjectId,
  parseProjectParam,
  withProjectParam,
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
