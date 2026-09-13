/**
 * 检修缺位占位冻结单测（assemble/spec.md §11 S11 机器锚——批3 段三）。
 *
 * 输入:  missingSlotPlaceholders 纯函数+冻结算例（近方阵居中口径——
 *        cols=ceil(sqrt(nPools)) 行主序、中心对齐）
 * 输出:  正常工况无缺位/尾槽缺位索引与坐标数值精确/全停单池/契约病
 *        五族（非有限/nPools<1/nActive<0/spacing≤0/nActive≥nPools）/
 *        −0 归一断言
 */

import { describe, expect, it } from "vitest";

import { missingSlotPlaceholders } from "./missingSlots";

describe("missingSlotPlaceholders 缺位占位（spec §11 S11）", () => {
  it("正常工况（nActive=nPools）无缺位", () => {
    expect(missingSlotPlaceholders(4, 4, 8)).toEqual([]);
  });

  it("n−1 检修（4 池 3 用）：尾槽 index=3，近方阵 2×2 第 4 槽坐标精确", () => {
    // cols=2、rows=2；index 3=(row1,col1)→(+spacing/2, 0, +spacing/2)
    expect(missingSlotPlaceholders(4, 3, 8)).toEqual([
      { index: 3, position: [4, 0, 4] },
    ]);
  });

  it("6 池 4 用（cols=3 两行）：缺位 2 槽 index 4/5 坐标精确", () => {
    // cols=3、rows=2；index 4=(1,1)/5=(1,2)→(+0,+spacing) 与 (+spacing,+spacing)
    expect(missingSlotPlaceholders(6, 4, 5)).toEqual([
      { index: 4, position: [0, 0, 2.5] },
      { index: 5, position: [5, 0, 2.5] },
    ]);
  });

  it("单池全停（1 池 0 用）：index=0 原点槽", () => {
    expect(missingSlotPlaceholders(1, 0, 6)).toEqual([
      { index: 0, position: [0, 0, 0] },
    ]);
  });

  it("奇数池 5 用 3（cols=3 两行）：缺位 3/4 末行左对齐 cols 网格", () => {
    // cols=3、rows=2；缺位 index 3=(1,0)/4=(1,1)→(−spacing, 0) 与 (0, 0)
    // ——末行不二次居中（槽位锚 cols 网格左对齐——工程语义最小承诺，
    // 与在用池前填同口径；门一 P2-3 口径注记）
    expect(missingSlotPlaceholders(5, 3, 10)).toEqual([
      { index: 3, position: [-10, 0, 5] },
      { index: 4, position: [0, 0, 5] },
    ]);
  });

  it("契约病五族零异常空返（登记归调用方——deviation 两层分工先例）", () => {
    expect(missingSlotPlaceholders(Number.NaN, 1, 8)).toEqual([]);
    expect(missingSlotPlaceholders(4, Number.POSITIVE_INFINITY, 8)).toEqual([]);
    expect(missingSlotPlaceholders(0, 0, 8)).toEqual([]);
    expect(missingSlotPlaceholders(4, -1, 8)).toEqual([]);
    expect(missingSlotPlaceholders(4, 3, 0)).toEqual([]);
  });

  it("nActive≥nPools（含数据病越界+floor 后越界）空返", () => {
    expect(missingSlotPlaceholders(4, 5, 8)).toEqual([]);
    expect(missingSlotPlaceholders(4.5, 4.2, 8)).toEqual([]);
  });

  it("小数入参 floor 口径（4.9 池 2.7 用=4 池 2 用）", () => {
    expect(missingSlotPlaceholders(4.9, 2.7, 8)).toEqual(
      missingSlotPlaceholders(4, 2, 8),
    );
  });

  it("中心槽坐标恰 +0（Object.is 面区分——防御位，门一 P2-2 记档不可达）", () => {
    // sqrt(2)≈1.414→cols=2、rows=1；index 1=(0,1)→(+spacing/2, 0, 0)——
    // z 居中因子 (row−(rows−1)/2)=0；spacing>0 契约闸下 −0 数学不可达
    // （整数差×正数恒非 −0），z0 归一为防御位（先例同构，无害保留）
    const slots = missingSlotPlaceholders(2, 1, 8);
    const slot = slots[0];
    expect(slot).toEqual({ index: 1, position: [4, 0, 0] });
    if (slot !== undefined) {
      expect(Object.is(slot.position[2], 0)).toBe(true);
    }
  });
});
