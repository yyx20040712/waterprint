/**
 * designWriter 纯函数测试（P0-3——task-c2-edit-plan §四 vitest 面）。
 *
 * 输入:  designWriter 六纯函数（本地 fixture 草稿）
 * 输出:  断言：加单元（零默认填充锁③）/多实例 `_2` 派生③/连线追加与
 *        同对幂等/删除级联（边+site.structures+checked_units）/删边/
 *        会话布局合成（兜底>持久>会话三级）
 */
import { describe, expect, it } from "vitest";

import {
  addUnit,
  connectEdge,
  deleteEdge,
  deleteNodes,
  draftViewLayout,
  nextInstanceId,
  setPosition,
  type DesignDraft,
} from "./designWriter";

/** 最小草稿工厂（双节点+一边+site 一摆放+受检一条）。 */
function draft(): DesignDraft {
  return {
    nodes: {
      inlet: { kind: "municipal_input", q_avg_daily: 0.4, kz: 1.4 },
      municipal_aao: { n: 2 },
    },
    edges: [
      {
        src: { unit_id: "inlet", port_id: "out" },
        dst: { unit_id: "municipal_aao", port_id: "in" },
      },
    ],
    siteStructures: { municipal_aao: { x: 70, y: -50, rotation: 0 } },
    checkedUnits: ["municipal_aao"],
    positions: {},
  };
}

describe("nextInstanceId（呈裁③ 甲案 `_2` 后缀递增）", () => {
  it("首例无后缀直用", () => {
    expect(nextInstanceId({}, "municipal_aao")).toBe("municipal_aao");
  });
  it("已占用→_2；_2 亦占→_3 顺延", () => {
    expect(nextInstanceId({ municipal_aao: {} }, "municipal_aao")).toBe(
      "municipal_aao_2",
    );
    expect(
      nextInstanceId({ municipal_aao: {}, municipal_aao_2: {} }, "municipal_aao"),
    ).toBe("municipal_aao_3");
  });
});

describe("addUnit（红线③ 零默认值填充）", () => {
  it("包单元=空参 {} 原样（快照锁——严禁 TS 侧补默认成第二业务源）", () => {
    const { draft: next, nodeId } = addUnit(draft(), "municipal_cass", "unit");
    expect(nodeId).toBe("municipal_cass");
    expect(next.nodes["municipal_cass"]).toEqual({});
  });
  it("包单元单实例闸（引擎 v1——node_id=注册表键精确匹配，再加=拒）", () => {
    const base = draft();
    const { draft: next, nodeId } = addUnit(base, "municipal_aao", "unit");
    expect(nodeId).toBeNull();
    expect(next).toBe(base); // 草稿原引用（零变更）
  });
  it("内置单元={kind} 结构元数据（装配口径 D5）+多实例 `_2` 全支持", () => {
    const once = addUnit(draft(), "junction", "builtin");
    expect(once.nodeId).toBe("junction");
    expect(once.draft.nodes["junction"]).toEqual({ kind: "junction" });
    const twice = addUnit(once.draft, "junction", "builtin");
    expect(twice.nodeId).toBe("junction_2");
    expect(twice.draft.nodes["junction_2"]).toEqual({ kind: "junction" });
  });
  it("原草稿不可变（旁路零突变）", () => {
    const base = draft();
    addUnit(base, "municipal_cass", "unit");
    expect(Object.keys(base.nodes)).toEqual(["inlet", "municipal_aao"]);
  });
});

describe("connectEdge（追加+同对幂等）", () => {
  it("追加蛇键原生形态 {src:{unit_id,port_id}}", () => {
    const next = connectEdge(
      draft(),
      { unit_id: "municipal_aao", port_id: "out" },
      { unit_id: "municipal_cass", port_id: "in" },
    );
    expect(next.edges).toHaveLength(2);
    expect(next.edges[1]).toEqual({
      src: { unit_id: "municipal_aao", port_id: "out" },
      dst: { unit_id: "municipal_cass", port_id: "in" },
    });
  });
  it("同对重复=幂等返回原草稿引用（平行边不产生）", () => {
    const base = draft();
    const next = connectEdge(
      base,
      { unit_id: "inlet", port_id: "out" },
      { unit_id: "municipal_aao", port_id: "in" },
    );
    expect(next).toBe(base);
  });
});

describe("deleteNodes（级联清——设计书 §一.3/D3 悬空防线）", () => {
  it("节点删→所连边级联清+site.structures 键清+checked_units 条清+拖拽位清", () => {
    const withPos = setPosition(draft(), "municipal_aao", { x: 1, y: 2 });
    const next = deleteNodes(withPos, ["municipal_aao"]);
    expect(Object.keys(next.nodes)).toEqual(["inlet"]);
    expect(next.edges).toHaveLength(0);
    expect(next.siteStructures).toEqual({});
    expect(next.checkedUnits).toEqual([]);
    expect(next.positions).toEqual({});
  });
  it("非触边保留（他节点间边不受累）", () => {
    const base: DesignDraft = {
      ...draft(),
      nodes: {
        ...draft().nodes,
        municipal_cass: {},
        municipal_erchunchi: {},
      },
      edges: [
        ...draft().edges,
        {
          src: { unit_id: "municipal_cass", port_id: "out" },
          dst: { unit_id: "municipal_erchunchi", port_id: "in" },
        },
      ],
    };
    const next = deleteNodes(base, ["municipal_cass"]);
    expect(next.edges).toEqual([
      {
        src: { unit_id: "inlet", port_id: "out" },
        dst: { unit_id: "municipal_aao", port_id: "in" },
      },
    ]);
  });
});

describe("deleteEdge（端点对判据）", () => {
  it("端点四值匹配移除", () => {
    const next = deleteEdge(
      draft(),
      { unit_id: "inlet", port_id: "out" },
      { unit_id: "municipal_aao", port_id: "in" },
    );
    expect(next.edges).toHaveLength(0);
  });
});

describe("draftViewLayout（兜底>持久>会话三级合成）", () => {
  it("新节点缺位=兜底派生（全覆盖喂投影 readLayout 采纳门）", () => {
    const layout = draftViewLayout(
      ["inlet", "municipal_aao"],
      [{ src: "inlet", dst: "municipal_aao" }],
      {},
      {},
    );
    expect(layout["inlet"]!.x).toBeLessThan(layout["municipal_aao"]!.x);
    expect(Object.keys(layout)).toHaveLength(2);
  });
  it("持久位（baseLayout 条目）覆盖兜底；会话拖拽位覆盖持久位", () => {
    const layout = draftViewLayout(
      ["inlet", "municipal_aao"],
      [],
      { inlet: { x: 11, y: 22 } },
      { inlet: { x: 99, y: 88 } },
    );
    expect(layout["inlet"]).toEqual({ x: 99, y: 88 });
    const onlyBase = draftViewLayout(
      ["inlet"],
      [],
      { inlet: { x: 11, y: 22 } },
      {},
    );
    expect(onlyBase["inlet"]).toEqual({ x: 11, y: 22 });
  });
  it("非法持久条目忽略走兜底（窄化门同 projectFlow.readLayout 判据）", () => {
    const layout = draftViewLayout(["inlet"], [], { inlet: { x: "bad" } }, {});
    expect(typeof layout["inlet"]!.x).toBe("number");
  });
});
