/**
 * 布置编辑器 store 测试：zustand node 直测首例（FE6 口径——零 DOM 依赖）。
 *
 * 输入:  useSiteplanStore（zustand create——getState/setState/actions 纯转移面）
 * 输出:  契约断言（初始态/pan/zoom 夹紧/snap·grid 开关/selection/tool 切换清
 *        折线/pending 序列机：加点/弹出/重置/取消清空）
 */
import { beforeEach, describe, expect, it } from "vitest";

import { useSiteplanStore } from "./siteplanStore";

/** 每用例复位全态（actions 稳定引用不重置——setState 偏量合并）。 */
function reset() {
  useSiteplanStore.setState({
    pan: { x: 0, y: 0 },
    zoom: 1,
    snapEnabled: true,
    showGrid: true,
    selection: null,
    tool: "select",
    pendingPoints: [],
  });
}

beforeEach(reset);

describe("siteplanStore（view 态纯转移——业务数据零入 store）", () => {
  it("初始态：pan 原点/zoom 1/snap 开/网格开/无选中/select 工具/零折线点", () => {
    const state = useSiteplanStore.getState();
    expect(state.pan).toEqual({ x: 0, y: 0 });
    expect(state.zoom).toBe(1);
    expect(state.snapEnabled).toBe(true);
    expect(state.showGrid).toBe(true);
    expect(state.selection).toBeNull();
    expect(state.tool).toBe("select");
    expect(state.pendingPoints).toEqual([]);
  });

  it("setPan 整体替换视口平移", () => {
    useSiteplanStore.getState().setPan({ x: -40, y: 120 });
    expect(useSiteplanStore.getState().pan).toEqual({ x: -40, y: 120 });
  });

  it("setZoom/zoomBy 夹紧 [0.1, 10]", () => {
    const { setZoom, zoomBy } = useSiteplanStore.getState();
    setZoom(2.5);
    expect(useSiteplanStore.getState().zoom).toBe(2.5);
    setZoom(0.01);
    expect(useSiteplanStore.getState().zoom).toBe(0.1);
    setZoom(99);
    expect(useSiteplanStore.getState().zoom).toBe(10);
    reset();
    zoomBy(1.2);
    expect(useSiteplanStore.getState().zoom).toBeCloseTo(1.2, 10);
    zoomBy(1000);
    expect(useSiteplanStore.getState().zoom).toBe(10);
    zoomBy(0.0001);
    expect(useSiteplanStore.getState().zoom).toBe(0.1);
  });

  it("toggleSnap/toggleGrid 翻转", () => {
    const { toggleSnap, toggleGrid } = useSiteplanStore.getState();
    toggleSnap();
    toggleGrid();
    const state = useSiteplanStore.getState();
    expect(state.snapEnabled).toBe(false);
    expect(state.showGrid).toBe(false);
  });

  it("setSelection 设置/清除（structure id 面+road/corridor index 面）", () => {
    const { setSelection } = useSiteplanStore.getState();
    setSelection({ kind: "structure", id: "tank" });
    expect(useSiteplanStore.getState().selection).toEqual({ kind: "structure", id: "tank" });
    setSelection({ kind: "corridor", index: 2 });
    expect(useSiteplanStore.getState().selection).toEqual({ kind: "corridor", index: 2 });
    setSelection(null);
    expect(useSiteplanStore.getState().selection).toBeNull();
  });

  it("setTool 切换并取消绘制中折线（pendingPoints 清空）", () => {
    const { setTool, appendPending } = useSiteplanStore.getState();
    setTool("road");
    appendPending({ x: 10, y: 10 });
    expect(useSiteplanStore.getState().pendingPoints).toHaveLength(1);
    useSiteplanStore.getState().setTool("select");
    const state = useSiteplanStore.getState();
    expect(state.tool).toBe("select");
    expect(state.pendingPoints).toEqual([]);
  });

  it("pending 序列机：加点/弹出（空表弹出=no-op）/重置/取消清空", () => {
    const { appendPending, popPending, resetPending, discardPending } =
      useSiteplanStore.getState();
    appendPending({ x: 0, y: 0 });
    appendPending({ x: 10, y: 0 });
    appendPending({ x: 10, y: 20 });
    expect(useSiteplanStore.getState().pendingPoints).toEqual([
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 10, y: 20 },
    ]);
    popPending();
    expect(useSiteplanStore.getState().pendingPoints).toEqual([
      { x: 0, y: 0 },
      { x: 10, y: 0 },
    ]);
    discardPending();
    expect(useSiteplanStore.getState().pendingPoints).toEqual([]);
    popPending(); // 空表弹出=no-op（不炸不造负索引）
    expect(useSiteplanStore.getState().pendingPoints).toEqual([]);
    resetPending([
      { x: 1, y: 2 },
      { x: 3, y: 4 },
    ]);
    expect(useSiteplanStore.getState().pendingPoints).toEqual([
      { x: 1, y: 2 },
      { x: 3, y: 4 },
    ]);
  });
});
