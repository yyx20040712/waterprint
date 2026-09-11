/**
 * canvasStore 编辑会话流转测试（P0-3——骨架条款兑现面）。
 *
 * 输入:  useCanvasStore 状态+actions（zustand getState 直驱——React 面
 *        由组件/E2E 承接）
 * 输出:  断言：beginEdit 快照摄入/同项目幂等/异项目顶替；addUnit 与
 *        dirty 派生；markSaved 自清；endEdit 归空；position 不致 dirty
 */
import { beforeEach, describe, expect, it } from "vitest";

import { useCanvasStore } from "./canvasStore";

/** 最小 raw 快照（design 四面+空 view——schema 其余面非本 store 消费）。 */
function raw(): Record<string, unknown> {
  return {
    format_version: "3.0",
    design: {
      nodes: { inlet: { kind: "municipal_input", q_avg_daily: 0.4, kz: 1.4 } },
      edges: [],
      site: { structures: {} },
      checked_units: [],
    },
    view: {},
    metadata: { project_id: "p1", content_hash: "h0" },
  };
}

const store = () => useCanvasStore.getState();

beforeEach(() => {
  useCanvasStore.getState().endEdit();
});

describe("canvasStore 编辑会话流转（红线⑤ 快照隔离面）", () => {
  it("beginEdit 摄入快照；同项目重复进入=幂等续会话（草稿不覆写）", () => {
    store().beginEdit("p1", raw());
    store().addUnit("municipal_aao", "unit");
    const draftBefore = useCanvasStore.getState().session?.draft;
    store().beginEdit("p1", raw()); // 同项目二连击（双击编辑钮面）
    expect(useCanvasStore.getState().session?.draft).toBe(draftBefore);
  });
  it("异项目 beginEdit=新会话顶替（单会话制——不跨项目残留）", () => {
    store().beginEdit("p1", raw());
    store().addUnit("municipal_aao", "unit");
    store().beginEdit("p2", raw());
    const session = useCanvasStore.getState().session;
    expect(session?.projectId).toBe("p2");
    expect(Object.keys(session?.draft.nodes ?? {})).toEqual(["inlet"]);
  });
  it("addUnit→dirty 派生 true；markSaved→四面引用复归 dirty 自清", () => {
    store().beginEdit("p1", raw());
    expect(useCanvasStore.getState().session?.draft.nodes).toEqual(
      useCanvasStore.getState().session?.base.nodes,
    );
    store().addUnit("municipal_aao", "unit");
    const session = useCanvasStore.getState().session;
    expect(session?.draft.nodes).not.toBe(session?.base.nodes);
    store().markSaved();
    const saved = useCanvasStore.getState().session;
    expect(saved?.draft.nodes).toBe(saved?.base.nodes);
  });
  it("position（视图态）不致 dirty", () => {
    store().beginEdit("p1", raw());
    store().position("inlet", { x: 5, y: 6 });
    const session = useCanvasStore.getState().session;
    expect(session?.draft.positions["inlet"]).toEqual({ x: 5, y: 6 });
    expect(session?.draft.nodes).toBe(session?.base.nodes);
  });
  it("endEdit 归空（后续动作空转不炸）", () => {
    store().beginEdit("p1", raw());
    store().endEdit();
    expect(useCanvasStore.getState().session).toBeNull();
    expect(store().addUnit("municipal_aao", "unit")).toBeNull();
    store().connect(
      { unit_id: "a", port_id: "out" },
      { unit_id: "b", port_id: "in" },
    );
    store().deleteNodes(["a"]);
    store().deleteEdge(
      { unit_id: "a", port_id: "out" },
      { unit_id: "b", port_id: "in" },
    );
    store().position("a", { x: 0, y: 0 });
    store().markSaved();
    expect(useCanvasStore.getState().session).toBeNull();
  });
  it("connect/delete 经 store 薄壳落到草稿（designWriter 通道）", () => {
    store().beginEdit("p1", raw());
    store().addUnit("municipal_aao", "unit");
    store().connect(
      { unit_id: "inlet", port_id: "out" },
      { unit_id: "municipal_aao", port_id: "in" },
    );
    expect(useCanvasStore.getState().session?.draft.edges).toEqual([
      {
        src: { unit_id: "inlet", port_id: "out" },
        dst: { unit_id: "municipal_aao", port_id: "in" },
      },
    ]);
    store().deleteNodes(["municipal_aao"]);
    expect(useCanvasStore.getState().session?.draft.edges).toEqual([]);
  });
});
