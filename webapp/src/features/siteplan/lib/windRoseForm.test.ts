/**
 * 风玫瑰值表单纯逻辑 vitest（B5 D5——简报 D8 逐条用例清单 1~4：node 环境
 * 先红后绿〔module 未就绪=import 解析红〕）。
 *
 * 输入:  windRoseForm 导出面（mergeWindRose——八方位表单合并写回真源）
 * 输出:  四面断言：全空无未知键→null/全空有未知键→仅未知键保留/负值
 *        NaN 过滤/部分值+未知键合并不丢
 */
import { describe, expect, it } from "vitest";

import { mergeWindRose } from "./windRoseForm";

describe("mergeWindRose 合并写回（B5 D5——未知键保留语义）", () => {
  it("八方位全空+无未知键→null（含原对象已知方位不隐式携带）", () => {
    expect(mergeWindRose(null, {})).toBeNull();
    expect(mergeWindRose(null, { N: null, NE: null, E: null, SE: null, S: null, SW: null, W: null, NW: null })).toBeNull();
    expect(mergeWindRose({ N: 1, S: 2 }, { N: null, S: null })).toBeNull(); // 八方位值只出自表单
  });

  it("八方位全空+有未知键→仅未知键保留（不置 null）", () => {
    expect(mergeWindRose({ NNW: 3, N: 1 }, {})).toEqual({ NNW: 3 });
    expect(
      mergeWindRose({ NNW: 0.5, E: 9 }, { N: null, NE: null, E: null, SE: null, S: null, SW: null, W: null, NW: null }),
    ).toEqual({ NNW: 0.5 });
  });

  it("负值/NaN/±Infinity 入→过滤不入写回（防御直通）", () => {
    expect(mergeWindRose(null, { N: -2, S: Number.NaN, E: Number.POSITIVE_INFINITY })).toBeNull();
    expect(mergeWindRose(null, { N: -2, W: 4 })).toEqual({ W: 4 }); // 非法项剔除、合法项保留
  });

  it("部分方位值+未知键→合并写回未知键不丢", () => {
    expect(mergeWindRose({ NNW: 0.5, N: 9 }, { N: 2, S: 3, E: null })).toEqual({
      NNW: 0.5,
      N: 2,
      S: 3,
    });
  });
});
