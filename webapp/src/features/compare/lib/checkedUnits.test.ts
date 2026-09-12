/**
 * checkedUnits 纯函数测试（P2 第三批 ADR-018 D4）：可勾全集/恢复投影/
 * PUT 载荷构造。
 *
 * 输入:  features/params/lib/checkedUnits 公开符号（node 纯函数）
 * 输出:  内置节点排除+字典序+幽灵勾选过滤+结构化替换断言组
 *        （withConstraintChoices 镜像——CP2 样板同构面）
 */
import { describe, expect, it } from "vitest";

import { checkableUnits, restoreCheckedKeys, withCheckedUnits } from "./checkedUnits";

/** 项目 raw fixture：两工艺单元+内置 inlet/junction（可勾面排除）。 */
const RAW = {
  format_version: "1.0",
  design: {
    nodes: {
      inlet: { kind: "municipal_input", q_avg_daily: 0.4 },
      junction_1: { kind: "junction" },
      municipal_aao: {},
      municipal_cass: { n_pool: 3.0 },
    },
    edges: [],
    checked_units: ["municipal_cass"],
  },
  view: { name: "一期" },
  metadata: {},
};

describe("checkableUnits 可勾全集", () => {
  it("内置四 kind 排除+字典序", () => {
    expect(checkableUnits(RAW)).toEqual(["municipal_aao", "municipal_cass"]);
  });

  it("异形 raw 宽容空集（面板空态呈现）", () => {
    expect(checkableUnits(null)).toEqual([]);
    expect(checkableUnits({ design: {} })).toEqual([]);
  });
});

describe("restoreCheckedKeys 恢复投影", () => {
  it("raw 勾选∩可勾全集（呈现序=字典序）", () => {
    expect(restoreCheckedKeys(RAW)).toEqual(["municipal_cass"]);
  });

  it("幽灵勾选过滤：已删单元的残留键不呈现（designWriter 级联后二道防线）", () => {
    const ghost = {
      design: { nodes: { municipal_aao: {} }, checked_units: ["municipal_aao", "deleted_unit"] },
    };
    expect(restoreCheckedKeys(ghost)).toEqual(["municipal_aao"]);
  });
});

describe("withCheckedUnits PUT 载荷构造", () => {
  it("仅替换 design.checked_units——其余顶层/design 键原样（结构化替换）", () => {
    const next = withCheckedUnits(RAW, ["municipal_aao", "municipal_cass"]);
    expect(next).not.toBe(RAW);
    expect((next["design"] as Record<string, unknown>)["checked_units"]).toEqual([
      "municipal_aao",
      "municipal_cass",
    ]);
    // 原样回传面：nodes/edges/view/metadata 不动
    expect((next["design"] as Record<string, unknown>)["nodes"]).toBe(RAW.design.nodes);
    expect(next["view"]).toBe(RAW.view);
  });

  it("空 keys 回空数组=全解勾（全量替换语义）", () => {
    const next = withCheckedUnits(RAW, []);
    expect((next["design"] as Record<string, unknown>)["checked_units"]).toEqual([]);
  });

  it("异形 raw 拒（Error——禁带病 PUT）", () => {
    expect(() => withCheckedUnits("not-an-object", [])).toThrow(/工况校核载荷非法/);
    expect(() => withCheckedUnits({ design: "bad" }, [])).toThrow(/design/);
  });
});
