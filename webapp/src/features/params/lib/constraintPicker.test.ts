/**
 * params 面纯函数单测：约束目录窄化/供选过滤/payload 三键投影（CP1 D6/D7）。
 *
 * 输入:  features/params/lib/constraintPicker.ts 公开符号（node 环境）
 * 输出:  断言：形状窄化（非法条目拒/目录非对象拒）/kind+unit_kinds 过滤/
 *        payload 恰三键（key/expression/source——severity 不入 worker 面）
 */
import { describe, expect, it } from "vitest";

import {
  filterSelectable,
  narrowConstraintCatalog,
  toPayloadItems,
} from "./constraintPicker";

const ENTRY = {
  key: "vxinglvchi.v_filter_band",
  kind: "enumeration_filter",
  unit_kinds: ["municipal_vxinglvchi"],
  label: "V型滤池正常滤速带（v_filter_act）",
  expression: "v_filter_act >= 7.0 and v_filter_act <= 10.0",
  source: "GB 50013-2018 §9.5；起草表待追认",
  severity: "WARN",
  value_basis: "factor… ——AI 起草待追认",
};

const EFFLUENT = {
  key: "gb18918.level_a.bod5",
  kind: "effluent_standard",
  unit_kinds: [],
  label: "GB 18918-2002 一级A 出水 BOD5 ≤10 mg/L",
  expression: "BOD5_out <= 10.0",
  source: "GB 18918-2002 表1；AI 起草待追认——参考面",
  severity: "WARN",
  value_basis: "国标限值直录——AI 起草待追认",
};

const CATALOG = { entries: [ENTRY, EFFLUENT] };

describe("narrowConstraintCatalog（目录形状窄化门）", () => {
  it("合法目录逐条投影（八键面原样）", () => {
    const view = narrowConstraintCatalog(CATALOG);
    expect(view).toHaveLength(2);
    expect(view[0]).toEqual(ENTRY);
  });

  it("目录非对象/entries 非数组 → 抛 Error（窄化门纪律）", () => {
    expect(() => narrowConstraintCatalog(null)).toThrow();
    expect(() => narrowConstraintCatalog({ entries: "nope" })).toThrow();
  });

  it("条目缺键/键型非法 → 抛 Error（含 key 定位）", () => {
    const bad = { entries: [{ ...ENTRY, key: "", expression: 1 }] };
    expect(() => narrowConstraintCatalog(bad)).toThrow(/约束目录/);
    const missing = { entries: [{ kind: "enumeration_filter" }] };
    expect(() => narrowConstraintCatalog(missing)).toThrow();
  });

  it("kind 越界 → 拒（枚举面锁定两类）", () => {
    const bad = { entries: [{ ...ENTRY, kind: "hard" }] };
    expect(() => narrowConstraintCatalog(bad)).toThrow();
  });
});

describe("filterSelectable（供选过滤=kind+unit_kinds 双门）", () => {
  it("仅 enumeration_filter 且 unit_kinds 含目标单元者供选", () => {
    const view = narrowConstraintCatalog(CATALOG);
    const selectable = filterSelectable(view, "municipal_vxinglvchi");
    expect(selectable.map((e) => e.key)).toEqual(["vxinglvchi.v_filter_band"]);
  });

  it("单元不匹配 → 空（effluent 恒不供选——unit_kinds 空表）", () => {
    const view = narrowConstraintCatalog(CATALOG);
    expect(filterSelectable(view, "sludge_tuoshui")).toEqual([]);
  });

  it("unitId null → 空（未选单元不供选）", () => {
    const view = narrowConstraintCatalog(CATALOG);
    expect(filterSelectable(view, null)).toEqual([]);
  });
});

describe("toPayloadItems（枚举 payload 三键投影）", () => {
  it("选中集 → 恰三键 items（key/expression/source——severity 不入）", () => {
    const view = narrowConstraintCatalog(CATALOG);
    const items = toPayloadItems(view, ["vxinglvchi.v_filter_band"]);
    expect(items).toEqual([
      {
        key: "vxinglvchi.v_filter_band",
        expression: "v_filter_act >= 7.0 and v_filter_act <= 10.0",
        source: "GB 50013-2018 §9.5；起草表待追认",
      },
    ]);
  });

  it("未知 key 静默滤除（目录刷新竞态防御——不构造半载荷）", () => {
    const view = narrowConstraintCatalog(CATALOG);
    expect(toPayloadItems(view, ["nope"])).toEqual([]);
  });

  it("空选中 → 空 items（options null 面由调用方判）", () => {
    const view = narrowConstraintCatalog(CATALOG);
    expect(toPayloadItems(view, [])).toEqual([]);
  });
});
