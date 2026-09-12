/**
 * 比例域降级判定冻结单测（assemble/spec.md §6 机器锚——批3 首件）。
 *
 * 输入:  deviation 纯函数+冻结域例（AAO 廊道 L_over_W 草案域 [6,15]——
 *        P2 呈裁初始值，判机制非判数值）
 * 输出:  域内/闭域边界恰等 ok/出域 fallback 明细（key/ratio/domain 数值
 *        精确）/非正尺寸/多条目遍历/空声明表无约束断言
 */

import { describe, expect, it } from "vitest";

import { deviation } from "./deviation";
import type { RatioDomainEntry } from "./types";

/** 冻结域例：AAO 廊道长宽比草案域 [6,15]（典型 60/12=5…草案按典型 ±50%
 *  标定演算取 [6,15]——P2 呈裁项，本测试冻机制不裁数值）。 */
const L_OVER_W: readonly RatioDomainEntry[] = [
  { key: "L_over_W", numerator: "L", denominator: "W", min: 6, max: 15 },
];

describe("deviation 比例域判定（spec §6）", () => {
  it("域内（L/W=10）ok", () => {
    expect(deviation({ L: 100, W: 10, H: 5 }, L_OVER_W)).toEqual({ ok: true });
  });

  it("闭域边界恰等下界（L/W=6）ok", () => {
    expect(deviation({ L: 60, W: 10, H: 5 }, L_OVER_W)).toEqual({ ok: true });
  });

  it("闭域边界恰等上界（L/W=15）ok", () => {
    expect(deviation({ L: 150, W: 10, H: 5 }, L_OVER_W)).toEqual({ ok: true });
  });

  it("出域低于下界（L/W=5.9）：fallback 携 key/ratio/domain 数值精确", () => {
    expect(deviation({ L: 59, W: 10, H: 5 }, L_OVER_W)).toEqual({
      ok: false,
      reason: "ratio_out_of_domain",
      key: "L_over_W",
      ratio: 5.9,
      domain: [6, 15],
    });
  });

  it("出域高于上界（L/W=20——Kimi §6.4 极端矩阵「出域回退」工况）", () => {
    const result = deviation({ L: 200, W: 10, H: 5 }, L_OVER_W);
    expect(result).toEqual({
      ok: false,
      reason: "ratio_out_of_domain",
      key: "L_over_W",
      ratio: 20,
      domain: [6, 15],
    });
  });

  it("非正尺寸（H=0/L=−1）→nonpositive_dim 携维名", () => {
    expect(deviation({ L: 60, W: 10, H: 0 }, L_OVER_W)).toEqual({
      ok: false,
      reason: "nonpositive_dim",
      dim: "H",
    });
    expect(deviation({ L: -1, W: 10, H: 5 }, L_OVER_W)).toEqual({
      ok: false,
      reason: "nonpositive_dim",
      dim: "L",
    });
  });

  it("多条目遍历：首条域内次条出域→报次条 key（非静默跳过）", () => {
    const domain: readonly RatioDomainEntry[] = [
      { key: "L_over_W", numerator: "L", denominator: "W", min: 6, max: 15 },
      { key: "D_over_H", numerator: "L", denominator: "H", min: 4, max: 14 },
    ];
    // L/W=10 域内；L/H=100/4=25 出 D_over_H 域
    const result = deviation({ L: 100, W: 10, H: 4 }, domain);
    expect(result.ok).toBe(false);
    if (!result.ok && result.reason === "ratio_out_of_domain") {
      expect(result.key).toBe("D_over_H");
      expect(result.ratio).toBe(25);
    }
  });

  it("空声明表=无约束 ok（registry 可选面）", () => {
    expect(deviation({ L: 1, W: 1, H: 1 }, [])).toEqual({ ok: true });
  });
});
