/**
 * projectCreate 纯函数测试（P0-1——F1/F3/F4-文案面）。
 *
 * 输入:  normalizeProjectName/projectOptionLabel/parseProjectJson 纯函数
 * 输出:  名称校验（strip/空/超长）+下拉 label 格式（名称 (id8)/无名回退
 *        全 id）+导入解析判别联合（对象通过/非对象拒/非法 JSON 用户语）
 */
import { describe, expect, it } from "vitest";

import {
  PROJECT_NAME_MAX,
  normalizeProjectName,
  parseProjectJson,
  projectOptionLabel,
} from "./projectCreate";

describe("normalizeProjectName（与 core ViewState.name 同口径）", () => {
  it("正常名称通过（trim 后非空且 ≤100）", () => {
    expect(normalizeProjectName("城市污水处理厂一期")).toEqual({
      name: "城市污水处理厂一期",
      valid: true,
    });
  });

  it("首尾空白剥除后再判（全空白=无效）", () => {
    expect(normalizeProjectName("  印染园区改扩建  ")).toEqual({
      name: "印染园区改扩建",
      valid: true,
    });
    expect(normalizeProjectName("   ")).toEqual({ name: "", valid: false });
  });

  it("超 100 字符无效（core schema 同限——FE 前置拦截）", () => {
    const long = "名".repeat(PROJECT_NAME_MAX + 1);
    expect(normalizeProjectName(long).valid).toBe(false);
    // 恰 100（上限含）有效
    expect(normalizeProjectName("名".repeat(PROJECT_NAME_MAX)).valid).toBe(true);
  });
});

describe("projectOptionLabel（F3 显示面——名称 (id 前 8)）", () => {
  it("有名=「名称 (id 前 8)」", () => {
    expect(projectOptionLabel("一期工程", "ab12cd34ef56.wp")).toBe(
      "一期工程 (ab12cd34)",
    );
  });

  it("无名（历史项目）=回退全 id（裸 hex 诚实显示——含 .wp 尾缀原样）", () => {
    expect(projectOptionLabel("", "ab12cd34ef56wp.json")).toBe("ab12cd34ef56wp.json");
    expect(projectOptionLabel("  ", "ab12cd34ef56")).toBe("ab12cd34ef56");
  });

  it("id=null 守备面=名称裸值（列表契约 id 恒非空实际不可达）", () => {
    expect(projectOptionLabel("名称", null)).toBe("名称");
  });
});

describe("parseProjectJson（导入面——结构校验归 server 422）", () => {
  it("合法 JSON 对象通过（原样载荷透传）", () => {
    const parsed = parseProjectJson('{"format_version":"3.0","design":{}}');
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(parsed.project).toEqual({ format_version: "3.0", design: {} });
    }
  });

  it("非对象顶层（数组/字符串/数字）拒+用户语", () => {
    expect(parseProjectJson("[1,2]").ok).toBe(false);
    expect(parseProjectJson('"text"').ok).toBe(false);
    expect(parseProjectJson("42").ok).toBe(false);
    const arrayResult = parseProjectJson("[]");
    expect(arrayResult.ok).toBe(false);
    if (!arrayResult.ok) {
      expect(arrayResult.error).toContain("JSON 对象");
    }
  });

  it("非法 JSON=parse 错误用户语透出", () => {
    const result = parseProjectJson("{not json");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toContain("不是合法 JSON");
    }
  });
});
