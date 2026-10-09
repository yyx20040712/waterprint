/**
 * v4 方案偏差重排纯函数测试（B2 结果与方案批——数据流②：调左栏参数→
 * 方案卡按与当前参数偏差重排+Δ徽标随动；零 jsdom 红线 node 直测）。
 *
 * 输入:  buildSolutionCards 夹具（grid 字段/方案行/当前参数三变量面）
 * 输出:  断言族：①卡模型（S 编号/参数摘要/★推荐=服务端首位）②偏差口径
 *        =方案值−当前值（Δ 徽标文本=键名+差值——wireframe「ΔSRT 2d」形）
 *        ③重排=偏差和升序（tie=服务端序）④无偏差卡零 Δ 徽标 ⑤当前值
 *        缺席字段不入偏差面（无可比基线）⑥重排确定性（同输入双跑同序）
 */
import { describe, expect, it } from "vitest";

import { buildSolutionCards } from "./solutionDeviation";
import type { GridField } from "../../features/solutions/lib/solutionsFields";
import type { SolutionRow } from "../../features/solutions/lib/solutionsView";

const GRID: GridField[] = [
  { key: "srt", dim: "TIME_H", label_zh: "污泥龄" },
  { key: "n", dim: "DIMENSIONLESS", label_zh: "系列数" },
];

const row = (srt: number, n: number): SolutionRow => ({ srt, n, margin_min: 0.5 });

describe("buildSolutionCards（数据流②偏差重排）", () => {
  it("卡模型：S 编号+参数摘要+★推荐=服务端排序首位", () => {
    const cards = buildSolutionCards([row(12, 3), row(10, 2)], GRID, { srt: 12, n: 3 });
    expect(cards.length).toBe(2);
    const recommended = cards.find((c) => c.recommended);
    expect(recommended?.serverRank).toBe(1); // ★=服务端序首位（重排不改归属）
    expect(cards.some((c) => c.no === "S01")).toBe(true); // S 编号=服务端序补零
    expect(cards.every((c) => c.summary.length > 0)).toBe(true); // 参数摘要非空
  });

  it("偏差口径=方案值−当前值（Δ 徽标文本=键名+差值）", () => {
    const cards = buildSolutionCards([row(14, 3)], GRID, { srt: 12, n: 3 });
    const card = cards[0]!;
    const srt = card.deviations.find((d) => d.key === "srt");
    expect(srt?.diff).toBe(2); // 14−12
    expect(card.deviationTexts.some((t) => t.includes("srt") && t.includes("2"))).toBe(
      true,
    );
    expect(card.deviations.find((d) => d.key === "n")).toBeUndefined(); // 同值无偏差
  });

  it("重排=偏差和升序（tie=服务端序）；★归属不动", () => {
    const cards = buildSolutionCards(
      [row(12, 3), row(14, 3), row(16, 3)],
      GRID,
      { srt: 15, n: 3 },
    );
    // 偏差 |12−15|=3/|14−15|=1/|16−15|=1 → 升序 [1,1,3]，tie=服务端序
    expect(cards.map((c) => c.serverRank)).toEqual([2, 3, 1]);
    expect(cards[0]?.recommended).toBe(false); // ★=serverRank 1 归属卡（现末位）
    expect(cards[2]?.recommended).toBe(true);
  });

  it("当前值缺席字段不入偏差面（无可比基线——空变更卡列首）", () => {
    const cards = buildSolutionCards([row(12, 3)], GRID, {});
    expect(cards[0]?.deviations).toEqual([]);
    expect(cards[0]?.deviationSum).toBe(0);
  });

  it("同输入双跑同序（确定性）", () => {
    const rows = [row(12, 3), row(10, 2), row(14, 4)];
    const a = buildSolutionCards(rows, GRID, { srt: 11, n: 3 });
    const b = buildSolutionCards(rows, GRID, { srt: 11, n: 3 });
    expect(a.map((c) => c.no)).toEqual(b.map((c) => c.no));
  });
});

describe("tie-break 锚定（B2 R4 核实项——ds 图3 误读驳回的证据面）", () => {
  it("等偏差和并列=服务端序稳定（★首位排前——重排不架空服务端序）", () => {
    // 构造真并列：current {srt:13,n:2}——S01{srt12,n3} 偏差 1+1=2、
    // S02{srt14,n1} 偏差 1+1=2（等和）→ tie-break=serverRank 升序
    const cards = buildSolutionCards(
      [row(12, 3), row(14, 1)],
      GRID,
      { srt: 13, n: 2 },
    );
    expect(cards.length).toBe(2);
    expect(cards[0]?.no).toBe("S01"); // 服务端序首位（★推荐卡）列首
    expect(cards[0]?.recommended).toBe(true);
    expect(cards[1]?.no).toBe("S02");
    expect(cards[1]?.recommended).toBe(false);
    // 双方偏差和相等（真并列非近似）：|12−13|+|3−2|=2、|14−13|+|1−2|=2
    expect(cards[0]?.deviationSum).toBe(cards[1]?.deviationSum);
    expect(cards[0]?.deviationSum).toBe(2);
  });
});
