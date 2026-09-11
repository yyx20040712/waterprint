/**
 * 职责：trimFloatNoise 纯函数测试（F8——C2-visual 批：浮点噪声归一）。
 *
 * 输入:  trimFloatNoise（number→12 位有效数字串——draft/显示双通道消费）
 * 输出:  尾差收口/长尾保真/零扰动/非有限诚实直出四族断言
 */
import { describe, expect, it } from "vitest";

import { trimFloatNoise } from "./designParams";

// ═══ F8（C2-visual 批）：浮点噪声归一——18 位尾差显示根除 ═══
describe("trimFloatNoise（F8 浮点显示归一）", () => {
  it("二进制尾差面收口（0.009999999999999998→0.01）", () => {
    expect(trimFloatNoise(0.009999999999999998)).toBe("0.01");
  });

  it("长尾有效值保真（266.13660939704994→266.136609397）", () => {
    expect(trimFloatNoise(266.13660939704994)).toBe("266.136609397");
  });

  it("整数与短小数零扰动", () => {
    expect(trimFloatNoise(8)).toBe("8");
    expect(trimFloatNoise(1.5)).toBe("1.5");
    expect(trimFloatNoise(0)).toBe("0");
  });

  it("非有限值诚实直出（Infinity/NaN 不抛错）", () => {
    expect(trimFloatNoise(Number.POSITIVE_INFINITY)).toBe("Infinity");
    expect(trimFloatNoise(Number.NaN)).toBe("NaN");
  });
});
