/**
 * dimLabels 纯函数测试（FIX-ACC1③）：DimKey→中文量名+单位符号映射+
 * 未知枚举原样诚实呈现。
 *
 * 输入:  dimLabel(dim)（shared/dimLabels——手写显示层表，与 CANONICAL_
 *        UNITS 逐键对齐、FLOW 单键刻意分歧〔2A2 批 2026-10-05 勘正，
 *        UF-62①：原「真源镜像」短语失实〕）+dimUnit(dim, surface)
 *        （M4 D3 扩输出面语境参——UF-63 候选①：输出面 FLOW→m³/s）
 * 输出:  已知枚举→「量名 单位」（DIMENSIONLESS→仅量名）；未知→原样串；
 *        dimUnit 两语境组（输出面 FLOW 分流，其余键同值）
 */
import { describe, expect, it } from "vitest";

import { dimLabel, dimUnit } from "./dimLabels";

describe("dimLabel 量纲显示映射（FIX-ACC1③）", () => {
  it("FLOW → 流量 m³/d（进水参数面口径——内核规范 m3/s，UF-62①/UF-63 注记见 dimLabels.ts 规格说明）", () => {
    expect(dimLabel("FLOW")).toBe("流量 m³/d");
  });

  it("CONCENTRATION → 浓度 mg/L", () => {
    expect(dimLabel("CONCENTRATION")).toBe("浓度 mg/L");
  });

  it("DIMENSIONLESS → 无量纲（无单位串——不挂尾随空格）", () => {
    expect(dimLabel("DIMENSIONLESS")).toBe("无量纲");
  });

  it("十五量类全量在册（core DimKey 成员数对齐——防漏登记静默退化为原样）", () => {
    const all = [
      "FLOW",
      "FLOW_H",
      "CONCENTRATION",
      "LENGTH",
      "AREA",
      "VOLUME",
      "MASS",
      "TIME",
      "TIME_H",
      "TIME_MIN",
      "TIME_D",
      "VELOCITY",
      "POWER",
      "TEMPERATURE",
      "DIMENSIONLESS",
    ];
    for (const dim of all) {
      const label = dimLabel(dim);
      expect(label).not.toBe(dim);
      expect(label.length).toBeGreaterThan(0);
    }
  });

  it("扩档三成员（DimKey 扩成员批）：HRT h/泥龄 d/滗水 m³/h 单位符号", () => {
    expect(dimLabel("TIME_H")).toBe("时间 h");
    expect(dimLabel("TIME_D")).toBe("时间 d");
    expect(dimLabel("FLOW_H")).toBe("流量 m³/h");
    expect(dimUnit("TIME_H")).toBe("h");
    expect(dimUnit("TIME_D")).toBe("d");
    expect(dimUnit("FLOW_H")).toBe("m³/h");
  });

  it("同制补齐两成员（参数面单位批）：min 档与温度 ℃ 显示符号", () => {
    expect(dimLabel("TIME_MIN")).toBe("时间 min");
    expect(dimLabel("TEMPERATURE")).toBe("温度 ℃");
    expect(dimUnit("TIME_MIN")).toBe("min");
    expect(dimUnit("TEMPERATURE")).toBe("℃");
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

describe("dimUnit 输出面语境参数（M4 D3——UF-63 候选①清偿：输出面 FLOW 标签 m³/s）", () => {
  it("FLOW 缺省（输入面）→ m³/d（既有行为回归锁——进水参数面绑定点口径）", () => {
    expect(dimUnit("FLOW")).toBe("m³/d");
  });

  it("FLOW output 面 → m³/s（值恒内核规范 m3/s，标签面美化 m3→m³——FE 零值面换算纪律）", () => {
    expect(dimUnit("FLOW", "output")).toBe("m³/s");
  });

  it("FLOW 显式 input 面 → m³/d（两语境显式面各自锁）", () => {
    expect(dimUnit("FLOW", "input")).toBe("m³/d");
  });

  it("其余键 output 面同值（VOLUME——两语境同表同源，仅 FLOW 分流）", () => {
    expect(dimUnit("VOLUME", "output")).toBe("m³");
    expect(dimUnit("VOLUME")).toBe("m³");
  });

  it("未知枚举两语境同空串（诚实降级无单位）", () => {
    expect(dimUnit("SOMETHING_NEW", "output")).toBe("");
    expect(dimUnit("SOMETHING_NEW", "input")).toBe("");
  });
});
