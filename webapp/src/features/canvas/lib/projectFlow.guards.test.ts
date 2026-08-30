/**
 * projectFlow 窄化门守卫负例（AUDIT2 FIX2 I-8 独立件）。
 *
 * 输入:  自构最小 design 夹具（与 projectFlow.test.ts tinyFixture 同形——
 *        该文件 500 行预算守恒，新增负例独立成件不回灌）
 * 输出:  守卫拒断言（探针 2026-08-30 已证实现真拒——此处正式入册）
 */
import { describe, expect, it } from "vitest";

import { ProjectFlowError, projectFlow } from "./projectFlow";

/** 双节点小夹具（a→a 自环边——projectFlow.test.ts tinyFixture 同形）。 */
function tinyFixture(overrides?: Partial<Record<string, unknown>>): Record<string, unknown> {
  return {
    format_version: "1.0",
    design: {
      nodes: { a: { kind: "municipal_aao" } },
      edges: [{ src: { unit_id: "a", port_id: "out0" }, dst: { unit_id: "a", port_id: "in0" } }],
    },
    ...overrides,
  };
}

describe("AUDIT2 I-8 projectFlow 未测守卫", () => {
  it("design 本体非对象拒", () => {
    expect(() => projectFlow(tinyFixture({ design: [] }) as never)).toThrow(ProjectFlowError);
  });

  it("边元素非对象拒（edges:[42]）", () => {
    expect(() =>
      projectFlow(tinyFixture({ design: { edges: [42], nodes: {} } }) as never),
    ).toThrow(ProjectFlowError);
  });

  it("端点非对象拒（src:7）", () => {
    expect(() =>
      projectFlow(
        tinyFixture({ design: { edges: [{ src: 7, dst: "a" }], nodes: {} } }) as never,
      ),
    ).toThrow(ProjectFlowError);
  });

  it("缺 dst 端点拒（同分支——只测过缺 src）", () => {
    expect(() =>
      projectFlow(tinyFixture({ design: { edges: [{ src: "a" }], nodes: {} } }) as never),
    ).toThrow(ProjectFlowError);
  });
});
