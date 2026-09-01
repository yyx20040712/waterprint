/**
 * params 面纯函数单测：约束目录窄化/供选过滤/payload 三键投影（CP1 D6/D7）
 * +勾选恢复投影（CP2 D3）+本组变更合成全集（CP2 R-1/N-1）。
 *
 * 输入:  features/params/lib/constraintPicker.ts 公开符号（node 环境）
 * 输出:  断言：形状窄化（非法条目拒/目录非对象拒）/kind+unit_kinds 过滤/
 *        payload 恰三键（key/expression/source——severity 不入 worker 面）/
 *        恢复投影（value 恒 "on" 键全集+宽容面）/合成全集（跨单元键保留
 *        ——Checkbox.Group onChange 只报本组注册值的补偿面）
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

  it("R1（DS-01）：缺 kind/缺 unit_kinds/非串值 → 显式拒（禁默认值静默降级）", () => {
    const noKind = { ...ENTRY } as Record<string, unknown>;
    delete noKind["kind"];
    expect(() => narrowConstraintCatalog({ entries: [noKind] })).toThrow(/kind/);
    const noUnits = { ...ENTRY } as Record<string, unknown>;
    delete noUnits["unit_kinds"];
    expect(() => narrowConstraintCatalog({ entries: [noUnits] })).toThrow(/unit_kinds/);
    expect(() =>
      narrowConstraintCatalog({ entries: [{ ...ENTRY, expression: 1 }] }),
    ).toThrow(/expression/); // String() 强转路径封死
    expect(() =>
      narrowConstraintCatalog({ entries: [{ ...ENTRY, unit_kinds: "municipal_vxinglvchi" }] }),
    ).toThrow(/unit_kinds/);
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

// ═══ CP2（约束勾选持久化 2026-09-01 D3/D7）：恢复投影纯函数 TDD 红先——
// 动态 import 隔离红面（实现前新导出不存在，单测红不殃及全文件——UX2
// designParams.test.ts Internals 先例） ═══
describe("CP2 restoreConstraintKeys（恢复投影——design.constraint_choices→勾选 keys 全集）", () => {
  /** raw GET 体夹具（ProjectFile 节选——constraint_choices 恢复面）。 */
  const rawWith = (choices: unknown): Record<string, unknown> => ({
    format_version: "1.0",
    design: { nodes: {}, constraint_choices: choices },
    metadata: {},
    view: {},
  });

  it("value 恒 \"on\" 的键 → 勾选 keys 全集（含 kb 外死键——供选面∩过滤归显示/提交面）", async () => {
    const { restoreConstraintKeys } = await import("./constraintPicker");
    expect(
      restoreConstraintKeys(
        rawWith({
          "vxinglvchi.v_filter_band": "on",
          "dead.key": "on",
          "future.tier": "later",
        }),
      ),
    ).toEqual(["vxinglvchi.v_filter_band", "dead.key"]);
  });

  it("空 choices → []；非 \"on\" 值键不恢复（最小诚实语义——档位值属扩展位）", async () => {
    const { restoreConstraintKeys } = await import("./constraintPicker");
    expect(restoreConstraintKeys(rawWith({}))).toEqual([]);
    expect(restoreConstraintKeys(rawWith({ "vxinglvchi.v_filter_band": "off" }))).toEqual([]);
  });

  it("宽容面：缺键/非对象/design 非 record/体异形 → []（恢复不炸渲染——rawCheckedUnits 同口径）", async () => {
    const { restoreConstraintKeys } = await import("./constraintPicker");
    expect(restoreConstraintKeys(rawWith(undefined))).toEqual([]);
    expect(restoreConstraintKeys(rawWith("on"))).toEqual([]);
    expect(restoreConstraintKeys(rawWith(["vxinglvchi.v_filter_band"]))).toEqual([]);
    expect(restoreConstraintKeys({ format_version: "1.0", design: [] })).toEqual([]);
    expect(restoreConstraintKeys(null)).toEqual([]);
    expect(restoreConstraintKeys({ format_version: "1.0" })).toEqual([]);
  });
});

// ═══ CP2 R-1（N-1 跨单元勾选覆盖 2026-09-01）：本组变更合成全集纯函数
// TDD 红先——动态 import 隔离红面。根因=antd Checkbox.Group onChange(values)
// 只报本组（当前供选面）注册值，挂载方须合成全集再持久（跨单元键保留）。 ═══
describe("CP2 R-1 mergeGroupSelection（本组变更合成全集——跨单元键保留）", () => {
  const VX1 = "vxinglvchi.v_filter_band";
  const VX2 = "vxinglvchi.v_forced_band";
  const GAN = "ganhua.moisture_out_band";
  const VX_GROUP = [VX1, VX2];
  const GAN_GROUP = [GAN];

  it("他组勾选：跨单元键保留+本组键并入（G4-2 断言面——PUT 全集含两键）", async () => {
    const { mergeGroupSelection } = await import("./constraintPicker");
    expect(mergeGroupSelection([VX1], GAN_GROUP, [GAN])).toEqual([VX1, GAN]);
  });

  it("他组解勾：本组删键不动跨单元键（G4-3 切回再现的合成面前提）", async () => {
    const { mergeGroupSelection } = await import("./constraintPicker");
    expect(mergeGroupSelection([VX1, GAN], GAN_GROUP, [])).toEqual([VX1]);
    expect(mergeGroupSelection([VX1, GAN], VX_GROUP, [VX1, VX2])).toEqual([
      GAN,
      VX1,
      VX2,
    ]);
  });

  it("本组增删替换：非本组键原样，本组面=nextKeys（增/删/换均生效）", async () => {
    const { mergeGroupSelection } = await import("./constraintPicker");
    // 本组增（VX1→VX1+VX2）；本组换（VX1+VX2→VX2）；死键跨组保留
    expect(mergeGroupSelection([VX1, "dead.key"], VX_GROUP, [VX1, VX2])).toEqual([
      "dead.key",
      VX1,
      VX2,
    ]);
    expect(mergeGroupSelection(["dead.key", VX1, VX2], VX_GROUP, [VX2])).toEqual([
      "dead.key",
      VX2,
    ]);
  });

  it("次序稳定：保留键按 totalKeys 序+nextKeys 按其序追加；同输入两次调用相等", async () => {
    const { mergeGroupSelection } = await import("./constraintPicker");
    const once = mergeGroupSelection(["b.key", "a.key"], GAN_GROUP, [GAN, "c.key"]);
    expect(once).toEqual(["b.key", "a.key", GAN, "c.key"]);
    expect(mergeGroupSelection(["b.key", "a.key"], GAN_GROUP, [GAN, "c.key"])).toEqual(
      once,
    );
  });

  it("去重：nextKeys 重复/与保留键重叠 → 单次出现（防御面）", async () => {
    const { mergeGroupSelection } = await import("./constraintPicker");
    expect(mergeGroupSelection(["a.key"], GAN_GROUP, [GAN, GAN])).toEqual([
      "a.key",
      GAN,
    ]);
    expect(mergeGroupSelection(["a.key", GAN], GAN_GROUP, [GAN])).toEqual([
      "a.key",
      GAN,
    ]);
  });

  it("空组边界（group=[]——单元未选面）：totalKeys 原样∪nextKeys；空全集直通 nextKeys", async () => {
    const { mergeGroupSelection } = await import("./constraintPicker");
    expect(mergeGroupSelection(["a.key", "b.key"], [], ["c.key"])).toEqual([
      "a.key",
      "b.key",
      "c.key",
    ]);
    expect(mergeGroupSelection([], GAN_GROUP, [GAN])).toEqual([GAN]);
    expect(mergeGroupSelection([], [], [])).toEqual([]);
  });
});
