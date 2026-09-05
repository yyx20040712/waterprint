/**
 * vertexEditing 纯函数测试：红线顶点命中/线段投影/增删移点/吸附（node
 * 环境——B4 笔③ 先红后绿）。
 *
 * 输入:  vertexEditing 纯函数族+sameSite（dirty 深比较真源——拒删不变性
 *        组合断言用）+projectSite.SitePoint 类型面
 * 输出:  契约断言（顶点命中内外/半径防御/最近优先；线段投影 clamp/零长/
 *        闭合 wrap 段；nearestSegmentIndex；insertVertex 索引位/wrap 尾插/
 *        非法直通；removeVertex 删至 3 合法/3 点拒删 null+不变性/非法索引
 *        直通；moveVertex immutable；snapVertexPoint 双轴吸附；拒删 dirty
 *        不翻转/增点 dirty 翻转[简报 R5 数据流面]）
 */
import { describe, expect, it } from "vitest";

import { sameSite } from "./siteDraftDiff";
import type { SiteDesignShape, SitePoint } from "./projectSite";
import {
  BOUNDARY_MIN_VERTICES,
  insertVertex,
  moveVertex,
  nearestSegmentIndex,
  removeVertex,
  segmentProjection,
  snapVertexPoint,
  vertexHitIndex,
} from "./vertexEditing";

/** 四点矩形红线（逆时针——值无所谓，几何判定面）。 */
const QUAD: SitePoint[] = [
  { x: 0, y: 0 },
  { x: 10, y: 0 },
  { x: 10, y: 10 },
  { x: 0, y: 10 },
];

function shapeOf(boundary: SitePoint[]): SiteDesignShape {
  return {
    structures: {},
    roads: [],
    corridors: [],
    boundary,
    options: { coord_grid: 10.0, wind_rose: null },
  };
}

describe("vertexHitIndex（顶点命中——最近优先，半径外/非法半径=-1）", () => {
  it("半径内命中返索引；半径外=-1；hitRadius 非正=防御 -1", () => {
    expect(vertexHitIndex(QUAD, { x: 0.4, y: 0.3 }, 1.0)).toBe(0);
    expect(vertexHitIndex(QUAD, { x: 5, y: 5 }, 1.0)).toBe(-1);
    expect(vertexHitIndex(QUAD, { x: 0, y: 0 }, 0)).toBe(-1);
    expect(vertexHitIndex(QUAD, { x: 0, y: 0 }, -1)).toBe(-1);
  });

  it("两顶点同入半径=取最近（命中歧义确定性）", () => {
    const dense: SitePoint[] = [{ x: 0, y: 0 }, { x: 0.5, y: 0 }, { x: 30, y: 30 }];
    expect(vertexHitIndex(dense, { x: 0.4, y: 0 }, 1.0)).toBe(1); // 距 0.1<0.4
  });
});

describe("segmentProjection（线段投影落点——clamp[0,1]+闭合 wrap 段）", () => {
  it("中点投影 t=0.5；超端点钳 t=1；零长段=起点直通", () => {
    const mid = segmentProjection(QUAD, { x: 5, y: 3 }, 0); // 段 0:(0,0)-(10,0)
    expect(mid).toEqual({ x: 5, y: 0, t: 0.5 });
    const past = segmentProjection(QUAD, { x: 15, y: 3 }, 0);
    expect(past).toEqual({ x: 10, y: 0, t: 1 });
    const degenerate = segmentProjection([{ x: 2, y: 2 }, { x: 2, y: 2 }], { x: 9, y: 9 }, 0);
    expect(degenerate).toEqual({ x: 2, y: 2, t: 0 });
  });

  it("闭合 wrap 段（segIndex=n-1 → 末点-首点段）投影", () => {
    const wrap = segmentProjection(QUAD, { x: -3, y: 5 }, 3); // 段 3:(0,10)-(0,0)
    expect(wrap).toEqual({ x: 0, y: 5, t: 0.5 });
  });

  it("R 轮 G1-02:非法 segIndex 返 null 不抛(整数/范围守卫——零抛错口径收口)", () => {
    expect(segmentProjection(QUAD, { x: 5, y: 5 }, -1)).toBeNull();
    expect(segmentProjection(QUAD, { x: 5, y: 5 }, 4)).toBeNull();
    expect(segmentProjection(QUAD, { x: 5, y: 5 }, 1.5)).toBeNull();
  });
});

describe("nearestSegmentIndex（增点路由——点最近段索引；空=-1）", () => {
  it("点近段 1（右边）而非段 0（底边）", () => {
    expect(nearestSegmentIndex(QUAD, { x: 9, y: 4 })).toBe(1);
    expect(nearestSegmentIndex(QUAD, { x: 4, y: -1 })).toBe(0);
  });

  it("空数组/孤立点=-1（无段可投）", () => {
    expect(nearestSegmentIndex([], { x: 0, y: 0 })).toBe(-1);
    expect(nearestSegmentIndex([{ x: 0, y: 0 }], { x: 1, y: 1 })).toBe(-1);
  });
});

describe("insertVertex（immutable 插入——segIndex+1 位；wrap 段=尾插）", () => {
  it("段 0 增点=索引 1 位；原数组零突变；新数组引用", () => {
    const next = insertVertex(QUAD, 0, { x: 5, y: 0 });
    expect(next.map((p) => [p.x, p.y])).toEqual([
      [0, 0], [5, 0], [10, 0], [10, 10], [0, 10],
    ]);
    expect(next).not.toBe(QUAD);
    expect(QUAD).toHaveLength(4);
  });

  it("wrap 段增点=尾插（末点-首点之间=数组尾）；非法 segIndex=原数组直通", () => {
    const wrapped = insertVertex(QUAD, 3, { x: 0, y: 5 });
    expect(wrapped.map((p) => [p.x, p.y])).toEqual([
      [0, 0], [10, 0], [10, 10], [0, 10], [0, 5],
    ]);
    expect(insertVertex(QUAD, 4, { x: 0, y: 0 })).toBe(QUAD);
    expect(insertVertex(QUAD, -1, { x: 0, y: 0 })).toBe(QUAD);
  });
});

describe("removeVertex（删至 <3=拒删 null——简报 R1 拒删语义；非法索引=直通）", () => {
  it("四点删一=三点合法（immutable 余项前移）", () => {
    const next = removeVertex(QUAD, 1);
    expect(next).not.toBeNull();
    expect(next!.map((p) => [p.x, p.y])).toEqual([[0, 0], [10, 10], [0, 10]]);
    expect(QUAD).toHaveLength(4); // 原数组零突变
  });

  it("三点再删=拒删 null（len-1<BOUNDARY_MIN_VERTICES）+原数组不变性", () => {
    const tri = QUAD.slice(0, 3);
    expect(BOUNDARY_MIN_VERTICES).toBe(1 + 2); // core site_plan.py 同值镜像锚
    expect(removeVertex(tri, 0)).toBeNull();
    expect(tri).toHaveLength(3); // 拒删不变性
  });

  it("非法索引=原数组直通（非拒删——调用侧不提示）", () => {
    expect(removeVertex(QUAD, 4)).toBe(QUAD);
    expect(removeVertex(QUAD, -1)).toBe(QUAD);
  });
});

describe("moveVertex/snapVertexPoint（immutable 移点+吸附归本层[简报 R5]）", () => {
  it("moveVertex 替换索引位 immutable；非法索引=原数组直通", () => {
    const next = moveVertex(QUAD, 2, { x: 12, y: 11 });
    expect(next[2]).toEqual({ x: 12, y: 11 });
    expect(next).not.toBe(QUAD);
    expect(QUAD[2]).toEqual({ x: 10, y: 10 });
    expect(moveVertex(QUAD, 9, { x: 0, y: 0 })).toBe(QUAD);
  });

  it("snapVertexPoint 开=双轴网点吸附/关=1e-9 除尘直通", () => {
    expect(snapVertexPoint({ x: 13.6, y: -7.2 }, 10, true)).toEqual({ x: 10, y: -10 });
    expect(snapVertexPoint({ x: 0.1 + 0.2, y: 1.05 }, 10, false)).toEqual({ x: 0.3, y: 1.05 });
  });
});

describe("dirty 组合（简报 R5——sameSite 深比较真源面）", () => {
  it("拒删（null）→draft 不变=dirty 不翻转；增点→dirty 翻转", () => {
    const loaded = shapeOf(QUAD);
    // 拒删分支：调用侧收 null 不 setDraft——draft 引用不变，sameSite 恒同
    expect(sameSite(shapeOf(QUAD), loaded)).toBe(true);
    const inserted = insertVertex(QUAD, 0, { x: 5, y: 0 });
    expect(sameSite(shapeOf(inserted), loaded)).toBe(false);
    const moved = moveVertex(QUAD, 0, { x: 1, y: 0 });
    expect(sameSite(shapeOf(moved), loaded)).toBe(false);
  });
});
