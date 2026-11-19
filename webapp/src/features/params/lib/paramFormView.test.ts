/**
 * paramFormView 纯函数测试（F5 批 2026-11-20）：必填门判定族
 * （effectiveRequiredValue/missingRequiredFields——审计 F5 提交门前置）
 * +迁驻原语回归锚（draftValueOf/normalizeDraftText/metaTooltipText——
 * 自 ParamForm 迁驻行为零变证面）。
 *
 * 输入:  构造 ParamEntry 夹具（required 面）+design 值+草稿
 * 输出:  断言族：有效值回退序（草稿→design→default）/必填缺失清单
 *        （required-only/草稿清空/非数草稿/非必填不进门）/归一原语恒等
 */
import { describe, expect, it } from "vitest";

import {
  draftValueOf,
  effectiveRequiredValue,
  metaTooltipText,
  missingRequiredFields,
  normalizeDraftText,
} from "./paramFormView";
import type { ParamEntry } from "../../../shared/api/generated/model";

/** 进水面夹具（目录第七字段 required 形态——服务端 builtin 投影镜像）。 */
const Q_ENTRY: ParamEntry = {
  field_id: "q_avg_daily",
  dim: "FLOW",
  default: null,
  range: null,
  grid: null,
  label_zh: "平均日流量",
  required: true,
};
const KZ_ENTRY: ParamEntry = {
  field_id: "kz",
  dim: "DIMENSIONLESS",
  default: null,
  range: null,
  grid: null,
  label_zh: "总变化系数",
  required: true,
};
const SS_ENTRY: ParamEntry = {
  field_id: "SS",
  dim: "CONCENTRATION",
  default: null,
  range: null,
  grid: null,
  label_zh: "SS 浓度",
  required: false,
};
const INLET_PARAMS = [Q_ENTRY, KZ_ENTRY, SS_ENTRY];

describe("effectiveRequiredValue（F5 必填有效值——回退序 草稿→design→default）", () => {
  it("三态全缺=null（新项目进水空态——审计 F5 复现面）", () => {
    expect(effectiveRequiredValue(Q_ENTRY, {}, {})).toBeNull();
  });

  it("design 覆盖在场面=直取（草稿缺席）", () => {
    expect(effectiveRequiredValue(Q_ENTRY, { q_avg_daily: 34760.7 }, {})).toBe(34760.7);
  });

  it("草稿在场优先于 design（可解析数）", () => {
    expect(
      effectiveRequiredValue(Q_ENTRY, { q_avg_daily: 34760.7 }, { q_avg_daily: "4" }),
    ).toBe(4);
  });

  it("草稿清空/非数=null 缺失态（不以旧值顶替用户清空）", () => {
    expect(
      effectiveRequiredValue(Q_ENTRY, { q_avg_daily: 34760.7 }, { q_avg_daily: "" }),
    ).toBeNull();
    expect(
      effectiveRequiredValue(KZ_ENTRY, { kz: 1.4 }, { kz: "abc" }),
    ).toBeNull();
  });

  it("default 兜底（required 面现值恒 null——回退序完备性）", () => {
    const withDefault = { ...Q_ENTRY, default: 100 };
    expect(effectiveRequiredValue(withDefault, {}, {})).toBe(100);
  });
});

describe("missingRequiredFields（F5 提交门判据——required-only 清单）", () => {
  it("新项目空态：恰缺 q/kz 两必填（指标非必填不进门）", () => {
    const missing = missingRequiredFields(INLET_PARAMS, {}, {});
    expect(missing.map((e) => e.field_id)).toEqual(["q_avg_daily", "kz"]);
  });

  it("只填平均日流量（审计复现态）：缺 kz 单项", () => {
    const missing = missingRequiredFields(INLET_PARAMS, {}, { q_avg_daily: "4" });
    expect(missing.map((e) => e.field_id)).toEqual(["kz"]);
  });

  it("必填补齐：空清单（门可通过）", () => {
    expect(
      missingRequiredFields(INLET_PARAMS, {}, { q_avg_daily: "4", kz: "1.4" }),
    ).toEqual([]);
  });

  it("design 已存值（历史项目重开）：无缺失", () => {
    expect(
      missingRequiredFields(INLET_PARAMS, { q_avg_daily: 34760.7, kz: 1.4 }, {}),
    ).toEqual([]);
  });

  it("非必填条目永不进门（无值/非数草稿均不拦提交）", () => {
    expect(missingRequiredFields([SS_ENTRY], {}, { SS: "abc" })).toEqual([]);
  });

  it("required 缺席（旧目录形态）＝非必填同判（向后兼容）", () => {
    const legacy = { ...Q_ENTRY } as ParamEntry;
    delete (legacy as Partial<ParamEntry>).required;
    expect(missingRequiredFields([legacy], {}, {})).toEqual([]);
  });
});

describe("迁驻原语回归锚（自 ParamForm 迁驻——行为零变）", () => {
  it("draftValueOf：number→trimFloatNoise 串/null/空串→空串/串原样", () => {
    expect(draftValueOf(0.30000000000000004)).toBe("0.3");
    expect(draftValueOf(null)).toBe("");
    expect(draftValueOf("")).toBe("");
    expect(draftValueOf("abc")).toBe("abc");
  });

  it("normalizeDraftText：可解析归一/非数原样（诚实拒路径）", () => {
    expect(normalizeDraftText("0.30000000000000004")).toBe("0.3");
    expect(normalizeDraftText("abc")).toBe("abc");
    expect(normalizeDraftText("")).toBe("");
  });

  it("metaTooltipText：dim+默认+field_id 拼接（含 required 面新字段零扰动）", () => {
    expect(metaTooltipText({ ...Q_ENTRY, default: 100, range: { min: 1, max: 5 } })).toBe(
      "流量 m³/d · 默认 100 · 范围 [1, 5] · field_id: q_avg_daily",
    );
  });
});
