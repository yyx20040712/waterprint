/**
 * dimLabels 纯函数测试（FIX-ACC1③）：DimKey→中文量名+单位符号映射+
 * 未知枚举原样诚实呈现。
 *
 * 输入:  dimLabel(dim)（shared/dimLabels——CANONICAL_UNITS 真源镜像）
 * 输出:  已知枚举→「量名 单位」（DIMENSIONLESS→仅量名）；未知→原样串
 */
import { describe, expect, it } from "vitest";

import { dimLabel, dimUnit } from "./dimLabels";

describe("dimLabel 量纲显示映射（FIX-ACC1③）", () => {
  it("FLOW → 流量 m³/d（上标美化——真源 m3/d 纯展示层）", () => {
    expect(dimLabel("FLOW")).toBe("流量 m³/d");
  });

  it("CONCENTRATION → 浓度 mg/L", () => {
    expect(dimLabel("CONCENTRATION")).toBe("浓度 mg/L");
  });

  it("DIMENSIONLESS → 无量纲（无单位串——不挂尾随空格）", () => {
    expect(dimLabel("DIMENSIONLESS")).toBe("无量纲");
  });

  it("十量类全量在册（core DimKey 成员数对齐——防漏登记静默退化为原样）", () => {
    const ten = [
      "FLOW",
      "CONCENTRATION",
      "LENGTH",
      "AREA",
      "VOLUME",
      "MASS",
      "TIME",
      "VELOCITY",
      "POWER",
      "DIMENSIONLESS",
    ];
    for (const dim of ten) {
      const label = dimLabel(dim);
      expect(label).not.toBe(dim);
      expect(label.length).toBeGreaterThan(0);
    }
  });

  it("未知枚举 → 原样返回（诚实呈现不猜语义）", () => {
    expect(dimLabel("SOMETHING_NEW")).toBe("SOMETHING_NEW");
  });
});

describe("dimUnit：单位符号直取（C2-params Q4）", () => {
  it("已知枚举 → 单位符号（同表同源）", () => {
    expect(dimUnit("FLOW")).toBe("m³/d");
    expect(dimUnit("LENGTH")).toBe("m");
    expect(dimUnit("CONCENTRATION")).toBe("mg/L");
  });

  it("无量纲 → 空串（无 addon 形态）", () => {
    expect(dimUnit("DIMENSIONLESS")).toBe("");
  });

  it("未知枚举 → 空串（诚实降级无单位）", () => {
    expect(dimUnit("SOMETHING_NEW")).toBe("");
  });
});
