/**
 * 参数面板纯函数测试：窄化门/draft 归一/脏比较/目录索引/假设合成行（D8 TDD）。
 *
 * 输入:  designParams 五纯函数（node 环境——零 antd/react-query import 链）
 * 输出:  纯函数契约断言（版本轻门/形状逐类拒/非数值 draft null 禁提交/
 *        脏比较无空写/units 索引含 builtin/假设 DEFAULTS∪overrides 覆盖标记）
 *
 * 规格说明（FE5 批 6b 段三，D1/D7/D8；夹具=golden municipal_34760 内联
 * 节选——inlet（内置 kind+数值参数）+sludge_hebing（六参数覆盖）+
 * municipal_aao（空参数节点），core/tests/golden/golden_data 原样值）：
 *   - 负例族逐类断言错误消息带键定位（呈现面可反查）；
 *   - D7 draft 归一：string→number|null（空/非数/非有限=null 禁提交）；
 *   - 脏比较基准=当前有效值（design 覆盖 ?? manifest 默认）——等值不产
 *     生空写条目（apply 合并面免 no-op 写）。
 */
import { describe, expect, it } from "vitest";

import type {
  AssumptionEntry,
  UnitMetaEntry,
} from "../../../shared/api/generated/model";
import {
  buildAssumptionRows,
  collectParamChanges,
  DesignParamsError,
  indexUnits,
  narrowDesignParams,
  normalizeDraftValue,
} from "./designParams";

/** golden municipal_34760 design 节选（三节点——原样值）。 */
const GOLDEN_EXCERPT: Record<string, unknown> = {
  design: {
    assumption_overrides: {},
    checked_units: [],
    constraint_choices: {},
    edges: [],
    influent: {},
    nodes: {
      inlet: {
        BOD5: 200.0,
        CODCR: 400.0,
        NH3N: 26.0,
        SS: 250.0,
        TN: 43.0,
        TP: 6.5,
        kind: "municipal_input",
        kz: 1.4,
        q_avg_daily: 0.4023229167,
      },
      municipal_aao: {},
      sludge_hebing: {
        ds_bio: 1928.69,
        ds_chem: 137.705,
        ds_primary: 3240.12,
        p_bio: 0.994,
        p_chem: 0.98,
        p_primary: 0.96,
      },
    },
    standard_binding: {},
  },
  format_version: "1.0",
  metadata: {},
  view: {},
};

/** 完整顶层夹具（覆盖 design/顶层键——负例逐类覆写）。 */
function fixture(
  overrides?: Partial<Record<string, unknown>>,
): Record<string, unknown> {
  return { ...GOLDEN_EXCERPT, ...overrides };
}

/** 覆写 design 子键（保持其余顶层原样）。 */
function withDesign(
  patch: Partial<Record<string, unknown>>,
): Record<string, unknown> {
  const raw = fixture();
  const design = raw["design"] as Record<string, unknown>;
  return { ...raw, design: { ...design, ...patch } };
}

/** META1 sludge_hebing manifest 参数面节选（dim/range/grid 三形态）。 */
const HEBING_META: UnitMetaEntry = {
  business_line: "sludge",
  kind: "unit",
  name_zh: "污泥合并",
  params: [
    { default: 3240.12, dim: "DIMENSIONLESS", field_id: "ds_primary" },
    { default: 0.96, dim: "DIMENSIONLESS", field_id: "p_primary" },
    { default: 2.0, dim: "DIMENSIONLESS", field_id: "ds_new", range: { max: 5, min: 0 } },
    { default: null, dim: "DIMENSIONLESS", field_id: "p_free" },
    { default: 1, dim: "DIMENSIONLESS", field_id: "g_step", grid: [0.5, 1, 2] },
  ],
  unit_id: "sludge_hebing",
};

/** META1 municipal_input builtin 投影节选（default 全 null——D1）。 */
const INPUT_META: UnitMetaEntry = {
  business_line: "municipal",
  kind: "builtin",
  name_zh: "市政进水",
  params: [
    { default: null, dim: "FLOW", field_id: "q_avg_daily" },
    { default: null, dim: "DIMENSIONLESS", field_id: "kz" },
    { default: null, dim: "CONCENTRATION", field_id: "BOD5" },
  ],
  unit_id: "municipal_input",
};

/** 假设 registry 三条节选（首条 safety.superheight 同序面）。 */
const ASSUMPTIONS: AssumptionEntry[] = [
  {
    default: 0.3,
    dim: "LENGTH",
    key: "safety.superheight",
    note: "超高 0.3 m",
    source: "GB 50014-2021",
    tuning_direction: "up",
  },
  {
    default: 1.4,
    dim: "DIMENSIONLESS",
    key: "influent.kz",
    note: "总变化系数",
    source: "GB 50014-2021",
    tuning_direction: "up",
  },
  {
    default: 0.6,
    dim: "DIMENSIONLESS",
    key: "sludge.wsl_ratio",
    note: "泥龄比",
    source: "手册",
    tuning_direction: "down",
  },
];

describe("narrowDesignParams（D8 窄化门）", () => {
  it("golden 节选窄化：数值参数收集+kind 元数据面+空假设覆盖", () => {
    const narrowed = narrowDesignParams(fixture());
    expect(narrowed.nodeParams["sludge_hebing"]).toEqual({
      ds_bio: 1928.69,
      ds_chem: 137.705,
      ds_primary: 3240.12,
      p_bio: 0.994,
      p_chem: 0.98,
      p_primary: 0.96,
    });
    expect(narrowed.nodeParams["inlet"]!["q_avg_daily"]).toBe(0.4023229167);
    expect(narrowed.nodeParams["municipal_aao"]).toEqual({});
    expect(narrowed.nodeKinds["inlet"]).toBe("municipal_input");
    expect(narrowed.nodeKinds["municipal_aao"]).toBeNull();
    expect(narrowed.assumptionOverrides).toEqual({});
  });

  it("assumption_overrides 数值覆盖窄化（含整数值）", () => {
    const raw = withDesign({
      assumption_overrides: { "influent.kz": 1.5, "safety.superheight": 1 },
    });
    expect(narrowDesignParams(raw).assumptionOverrides).toEqual({
      "influent.kz": 1.5,
      "safety.superheight": 1,
    });
  });

  it("宽容面：节点非数值参数值略过+kind 非字符串归 null", () => {
    const raw = withDesign({
      nodes: {
        j1: { flow: "large", kind: 42, ratio: 0.5, on: true },
      },
    });
    const narrowed = narrowDesignParams(raw);
    expect(narrowed.nodeParams["j1"]).toEqual({ ratio: 0.5 });
    expect(narrowed.nodeKinds["j1"]).toBeNull();
  });

  it("缺 assumption_overrides 键宽容为空覆盖（可选面）", () => {
    const raw = withDesign({ assumption_overrides: undefined });
    const design = raw["design"] as Record<string, unknown>;
    delete design["assumption_overrides"];
    expect(narrowDesignParams(raw).assumptionOverrides).toEqual({});
  });

  it("负例族：版本门/design/nodes/节点值逐类显式拒", () => {
    expect(() => narrowDesignParams(fixture({ format_version: 1.0 }))).toThrow(
      DesignParamsError,
    );
    expect(() => narrowDesignParams(fixture({ design: [] }))).toThrow(
      /design 须为对象/,
    );
    expect(() => narrowDesignParams(withDesign({ nodes: [] }))).toThrow(
      /design\.nodes 须为对象/,
    );
    expect(() => narrowDesignParams(withDesign({ nodes: { j1: 42 } }))).toThrow(
      /design\.nodes\[j1\] 须为对象/,
    );
  });

  it("负例族：assumption_overrides 形状与非数值逐类显式拒", () => {
    expect(() =>
      narrowDesignParams(withDesign({ assumption_overrides: [] })),
    ).toThrow(/assumption_overrides 须为对象/);
    expect(() =>
      narrowDesignParams(
        withDesign({ assumption_overrides: { "influent.kz": "1.5" } }),
      ),
    ).toThrow(/assumption_overrides\[influent\.kz\] 须为数值/);
  });
});

describe("normalizeDraftValue（D7 draft 归一）", () => {
  it("数值串归一（含空白/科学计数/负数）", () => {
    expect(normalizeDraftValue("0.994")).toBe(0.994);
    expect(normalizeDraftValue(" 1.5 ")).toBe(1.5);
    expect(normalizeDraftValue("1e2")).toBe(100);
    expect(normalizeDraftValue("-3.25")).toBe(-3.25);
  });
  it("空/非数/非有限一律 null（禁提交态）", () => {
    expect(normalizeDraftValue("")).toBeNull();
    expect(normalizeDraftValue("   ")).toBeNull();
    expect(normalizeDraftValue("abc")).toBeNull();
    expect(normalizeDraftValue("1,5")).toBeNull();
    expect(normalizeDraftValue("Infinity")).toBeNull();
  });
});

describe("collectParamChanges（D5 脏比较+payload 收集）", () => {
  const hebingValues = {
    ds_primary: 3240.12,
    p_primary: 0.96,
  } as const;

  it("未编辑字段不进 payload；等值编辑不产空写", () => {
    const result = collectParamChanges(
      HEBING_META.params ?? [],
      hebingValues,
      { ds_primary: "3240.12" },
    );
    expect(result.changes).toEqual({});
    expect(result.invalidFields).toEqual([]);
  });

  it("差异编辑进 payload（JSON 浮点形态保真）", () => {
    const result = collectParamChanges(
      HEBING_META.params ?? [],
      hebingValues,
      { ds_primary: "4000.5", p_primary: "0.97" },
    );
    expect(result.changes).toEqual({ ds_primary: 4000.5, p_primary: 0.97 });
  });

  it("无 design 值时与 manifest 默认等值=不产空写；有差异才写", () => {
    const result = collectParamChanges(HEBING_META.params ?? [], {}, {
      ds_new: "2",
      p_free: "0.9",
    });
    expect(result.changes).toEqual({ p_free: 0.9 });
  });

  it("null 禁提交：非数值/空 draft 收进 invalidFields 不进 payload", () => {
    const result = collectParamChanges(
      HEBING_META.params ?? [],
      hebingValues,
      { ds_primary: "abc", p_primary: "" },
    );
    expect(result.changes).toEqual({});
    expect(result.invalidFields).toEqual(["ds_primary", "p_primary"]);
  });

  it("builtin 面（default 全 null）：任意有效数值即变更", () => {
    const result = collectParamChanges(INPUT_META.params ?? [], {}, {
      q_avg_daily: "0.5",
    });
    expect(result.changes).toEqual({ q_avg_daily: 0.5 });
  });
});

describe("indexUnits（META1 目录索引）", () => {
  it("unit 与 builtin 双面可查（builtin 键=kind 值）+未登记键 undefined", () => {
    const index = indexUnits([HEBING_META, INPUT_META]);
    expect(index.get("sludge_hebing")).toBe(HEBING_META);
    expect(index.get("municipal_input")).toBe(INPUT_META);
    expect(index.get("inlet")).toBeUndefined();
  });

  it("空目录索引空查不炸", () => {
    expect(indexUnits([]).size).toBe(0);
  });
});

describe("buildAssumptionRows（假设合成行——DEFAULTS∪overrides）", () => {
  it("无覆盖：registry 序全行默认值+覆盖标记全 false", () => {
    const rows = buildAssumptionRows(ASSUMPTIONS, {});
    expect(rows).toHaveLength(3);
    expect(rows[0]!).toMatchObject({
      defaultValue: 0.3,
      key: "safety.superheight",
      overridden: false,
      value: 0.3,
    });
    expect(rows.map((row) => row.key)).toEqual([
      "safety.superheight",
      "influent.kz",
      "sludge.wsl_ratio",
    ]);
  });

  it("覆盖优先：值换新+标记 true；目录外覆盖键追加成行（∪语义）", () => {
    const rows = buildAssumptionRows(ASSUMPTIONS, {
      "influent.kz": 1.6,
      "custom.extra": 2,
    });
    const kz = rows.find((row) => row.key === "influent.kz");
    expect(kz).toMatchObject({ defaultValue: 1.4, overridden: true, value: 1.6 });
    const extra = rows.find((row) => row.key === "custom.extra");
    expect(extra).toMatchObject({
      defaultValue: null,
      overridden: true,
      value: 2,
    });
    expect(rows).toHaveLength(4);
  });
});


// ═══ AUDIT2 FIX2 I-8：未测负例形状入册（探针 2026-08-30 已证实现真拒） ═══
describe("AUDIT2 I-8 designParams 未测负例形状", () => {
  it("overrides 值 NaN 拒", () => {
    expect(() =>
      narrowDesignParams({
        format_version: "1.0",
        design: { nodes: {}, assumption_overrides: { k: Number.NaN } },
      }),
    ).toThrow();
  });
  it("overrides 值 bool 拒", () => {
    expect(() =>
      narrowDesignParams({
        format_version: "1.0",
        design: { nodes: {}, assumption_overrides: { k: true } },
      }),
    ).toThrow();
  });
});

// ═══ UX2 U1（假设覆盖编辑 2026-08-30）：纯函数面 TDD 红先——动态 import
// 隔离红面（实现前新导出不存在——单测红不殃及全文件，Internals 先例） ═══
describe("UX2 collectAssumptionEdits（假设编辑收集——D1 面板级一次 PUT）", () => {
  /** 覆盖态夹具：kz 覆盖 1.6+目录外 custom.extra=2（∪语义四行）。 */
  const rows = () =>
    buildAssumptionRows(ASSUMPTIONS, { "influent.kz": 1.6, "custom.extra": 2 });

  it("零编辑：覆盖行原样全量保留+changed=false（未覆盖行不产键）", async () => {
    const { collectAssumptionEdits } = await import("./designParams");
    const edits = collectAssumptionEdits(rows(), {}, {});
    expect(edits.overrides).toEqual({ "influent.kz": 1.6, "custom.extra": 2 });
    expect(edits.invalidKeys).toEqual([]);
    expect(edits.changed).toBe(false);
  });

  it("目录内行编辑改值→覆盖更新；draft=默认值等值→不产覆盖（免空写）", async () => {
    const { collectAssumptionEdits } = await import("./designParams");
    const edits = collectAssumptionEdits(rows(), { "safety.superheight": 0.5 }, {});
    expect(edits.overrides).toEqual({
      "influent.kz": 1.6,
      "custom.extra": 2,
      "safety.superheight": 0.5,
    });
    expect(edits.changed).toBe(true);
    const equal = collectAssumptionEdits(rows(), { "sludge.wsl_ratio": 0.6 }, {});
    expect(equal.overrides).not.toHaveProperty("sludge.wsl_ratio");
    expect(equal.changed).toBe(false);
  });

  it("已覆盖行 draft 改回默认值=回落 DEFAULTS（覆盖删键，changed=true）", async () => {
    const { collectAssumptionEdits } = await import("./designParams");
    const edits = collectAssumptionEdits(rows(), { "influent.kz": 1.4 }, {});
    expect(edits.overrides).not.toHaveProperty("influent.kz");
    expect(edits.changed).toBe(true);
  });

  it("恢复默认：目录内覆盖行删键回落 DEFAULTS；目录外键=删行", async () => {
    const { collectAssumptionEdits } = await import("./designParams");
    const edits = collectAssumptionEdits(
      rows(),
      {},
      { "influent.kz": true, "custom.extra": true },
    );
    expect(edits.overrides).toEqual({});
    expect(edits.changed).toBe(true);
    // 未覆盖行恢复默认=no-op（无变更不产空 PUT）
    const noop = collectAssumptionEdits(rows(), {}, { "sludge.wsl_ratio": true });
    expect(noop.changed).toBe(false);
  });

  it("无效 draft（null/NaN/Infinity）进 invalidKeys 禁提交；其余行有效编辑照常收集", async () => {
    const { collectAssumptionEdits } = await import("./designParams");
    const edits = collectAssumptionEdits(
      rows(),
      { "influent.kz": null, "safety.superheight": 0.5 },
      {},
    );
    expect(edits.invalidKeys).toEqual(["influent.kz"]);
    expect(edits.overrides["safety.superheight"]).toBe(0.5);
    expect(collectAssumptionEdits(rows(), { "influent.kz": Number.NaN }, {}).invalidKeys).toEqual([
      "influent.kz",
    ]);
    expect(
      collectAssumptionEdits(rows(), { "influent.kz": Number.POSITIVE_INFINITY }, {})
        .invalidKeys,
    ).toEqual(["influent.kz"]);
  });

  it("目录外键编辑有效值写入 overrides（∪行可编辑面）", async () => {
    const { collectAssumptionEdits } = await import("./designParams");
    const edits = collectAssumptionEdits(rows(), { "custom.extra": 3 }, {});
    expect(edits.overrides["custom.extra"]).toBe(3);
    expect(edits.changed).toBe(true);
  });
});

describe("UX2 withAssumptionOverrides（PUT 载荷构造——D2 结构化替换禁散拼）", () => {
  it("仅替换 design.assumption_overrides；其余顶层/design 键原样；原体不可变", async () => {
    const { withAssumptionOverrides } = await import("./designParams");
    const raw = fixture();
    const next = withAssumptionOverrides(raw, { "influent.kz": 1.7 });
    const design = next["design"] as Record<string, unknown>;
    expect(design["assumption_overrides"]).toEqual({ "influent.kz": 1.7 });
    expect(design["nodes"]).toEqual(
      (raw["design"] as Record<string, unknown>)["nodes"],
    );
    expect(design["checked_units"]).toEqual([]);
    expect(next["format_version"]).toBe("1.0");
    expect(next["metadata"]).toEqual(raw["metadata"]);
    expect(next["view"]).toEqual(raw["view"]);
    expect(
      (raw["design"] as Record<string, unknown>)["assumption_overrides"],
    ).toEqual({}); // 纯函数：原 GET 体不被改写
  });

  it("design 缺失/非对象显式拒（原始体异形——窄化产物禁当 PUT body 的守卫）", async () => {
    const { withAssumptionOverrides } = await import("./designParams");
    expect(() => withAssumptionOverrides({ format_version: "1.0" }, {})).toThrow(
      DesignParamsError,
    );
    expect(() =>
      withAssumptionOverrides({ format_version: "1.0", design: [] }, {}),
    ).toThrow(/design/);
  });
});

describe("UX2 rawCheckedUnits（conditions 原样透传——D4 自动重算）", () => {
  it("数组原样引用；缺省/非数组=undefined（缺省语义不散拼）", async () => {
    const { rawCheckedUnits } = await import("./designParams");
    const units = ["rain", "design"];
    expect(rawCheckedUnits(withDesign({ checked_units: units }))).toBe(units);
    expect(
      rawCheckedUnits(withDesign({ checked_units: undefined })),
    ).toBeUndefined();
    expect(rawCheckedUnits(withDesign({ checked_units: "all" }))).toBeUndefined();
  });
});
