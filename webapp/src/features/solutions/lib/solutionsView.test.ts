/**
 * solutions 纯函数测试：窄化门/列模型/apply 载荷/排序选项（D4/D5/D6/D9 TDD）。
 *
 * 输入:  solutionsView 四纯函数族（node 环境——零 antd/react-query import 链）
 * 输出:  纯函数契约断言（SolutionPage 顶层逐类拒负例族/列模型 kind 分类与
 *        响应序/apply 载荷仅投影 grid 字段/sort 选项=columns 白名单）
 *
 * 规格说明（FE6 批 6b 段四，D4/D5/D6/D7；夹具=golden aao 枚举内联——
 * columns 构造序 grid→dim 输出→margin_min/nan_flag/condition_key（冻结 §一），
 * rows 5 行=grid [2,3,4,5,6]（units_lib/municipal/aao/manifest.py:238），
 * margin_min 恒降序（服务端 ascending=False——前端直显不重排））：
 *   - 行值域=number|string|boolean|null（nan_flag 布尔列服务端原样下发——
 *     D4「三类」笔误记档，以服务端 pd.isna 面为准四类）；
 *   - 负例族逐类断言 SolutionsViewError 消息带键定位（呈现面可反查）；
 *   - apply 载荷=grid 字段投影（dim 输出不可应用——ADR-005 单单元语义）。
 */
import { describe, expect, it } from "vitest";

import {
  buildApplyPayload,
  buildSortOptions,
  buildTableColumns,
  narrowSolutionPage,
  SolutionsViewError,
} from "./solutionsView";

/** golden aao 枚举分页夹具（形状照冻结 §一；volume=dim 输出示意列）。 */
const GOLDEN_PAGE: Record<string, unknown> = {
  task_id: "enum-aao-001",
  page: 1,
  size: 50,
  total: 5,
  sort: "margin_min",
  columns: ["n", "volume", "margin_min", "nan_flag", "condition_key"],
  rows: [
    {
      n: 6,
      volume: 12480,
      margin_min: 0.22,
      nan_flag: false,
      condition_key: "baseline:design",
    },
    {
      n: 5,
      volume: 10400,
      margin_min: 0.08,
      nan_flag: false,
      condition_key: "baseline:design",
    },
    {
      n: 4,
      volume: 8320,
      margin_min: null,
      nan_flag: true,
      condition_key: "baseline:design",
    },
    {
      n: 3,
      volume: 6240,
      margin_min: -0.05,
      nan_flag: false,
      condition_key: "baseline:design",
    },
    {
      n: 2,
      volume: 4160,
      margin_min: -0.31,
      nan_flag: false,
      condition_key: "baseline:design",
    },
  ],
};

/** 覆写夹具单键（保持其余顶层原样——负例逐类覆写）。 */
function fixture(
  patch: Partial<Record<string, unknown>>,
): Record<string, unknown> {
  return { ...GOLDEN_PAGE, ...patch };
}

/** 断言窄化拒并带键定位。 */
function expectReject(raw: unknown, fragment: string): void {
  expect(() => narrowSolutionPage(raw)).toThrow(SolutionsViewError);
  expect(() => narrowSolutionPage(raw)).toThrow(fragment);
}

describe("narrowSolutionPage（D4 弱类型行窄化门）", () => {
  it("golden 夹具直通（七字段全量保序保值）", () => {
    const view = narrowSolutionPage(GOLDEN_PAGE);
    expect(view.task_id).toBe("enum-aao-001");
    expect(view.page).toBe(1);
    expect(view.size).toBe(50);
    expect(view.total).toBe(5);
    expect(view.sort).toBe("margin_min");
    expect(view.columns).toEqual([
      "n",
      "volume",
      "margin_min",
      "nan_flag",
      "condition_key",
    ]);
    expect(view.rows).toHaveLength(5);
    expect(view.rows[0]).toEqual({
      n: 6,
      volume: 12480,
      margin_min: 0.22,
      nan_flag: false,
      condition_key: "baseline:design",
    });
  });

  it("行值域四类宽容（null/boolean/string/number 并存行合法）", () => {
    const view = narrowSolutionPage(
      fixture({
        rows: [{ n: 4, margin_min: null, nan_flag: true, condition_key: "k" }],
      }),
    );
    expect(view.rows[0]?.margin_min).toBeNull();
    expect(view.rows[0]?.nan_flag).toBe(true);
  });

  it("负例：非对象拒（数组/null/原始值）", () => {
    expectReject([1, 2], "对象");
    expectReject(null, "对象");
    expectReject("page", "对象");
  });

  it("负例：task_id 非 string / page 非正整数 逐类拒（带键定位）", () => {
    expectReject(fixture({ task_id: 42 }), "task_id");
    expectReject(fixture({ page: 0 }), "page");
    expectReject(fixture({ page: 1.5 }), "page");
    expectReject(fixture({ size: 0 }), "size");
    expectReject(fixture({ total: -1 }), "total");
    expectReject(fixture({ sort: null }), "sort");
  });

  it("负例：columns 空/含非 string 拒（轻门=非空 string[]）", () => {
    expectReject(fixture({ columns: [] }), "columns");
    expectReject(fixture({ columns: ["n", 3] }), "columns[1]");
    expectReject(fixture({ columns: "n" }), "columns");
  });

  it("负例：rows 非数组/行非对象/行值域四类外（数组/对象值）拒", () => {
    expectReject(fixture({ rows: {} }), "rows");
    expectReject(fixture({ rows: [42] }), "rows[0]");
    expectReject(
      fixture({ rows: [{ n: [2], margin_min: 0.1 }] }),
      "rows[0].n",
    );
    expectReject(
      fixture({ rows: [{ n: { v: 2 }, margin_min: 0.1 }] }),
      "rows[0].n",
    );
  });
});

describe("buildTableColumns（D5 动态列模型——响应序直传）", () => {
  it("golden columns 五列分类：grid→margin→flag→text（构造序=响应序）", () => {
    const models = buildTableColumns(
      narrowSolutionPage(GOLDEN_PAGE).columns,
      ["n"],
    );
    expect(models.map((m) => m.key)).toEqual([
      "n",
      "volume",
      "margin_min",
      "nan_flag",
      "condition_key",
    ]);
    const byKey = new Map(models.map((m) => [m.key, m]));
    expect(byKey.get("n")).toMatchObject({ kind: "grid", numeric: true, applicable: true });
    expect(byKey.get("volume")).toMatchObject({ kind: "dim", numeric: true, applicable: false });
    expect(byKey.get("margin_min")).toMatchObject({ kind: "margin", numeric: true, applicable: false });
    expect(byKey.get("nan_flag")).toMatchObject({ kind: "flag", numeric: false, applicable: false });
    expect(byKey.get("condition_key")).toMatchObject({ kind: "text", numeric: false, applicable: false });
  });

  it("gridFields 空→全列 applicable=false（无应用标识列）", () => {
    const models = buildTableColumns(["n", "margin_min"], []);
    expect(models.every((m) => !m.applicable)).toBe(true);
    expect(models.find((m) => m.key === "n")?.kind).toBe("dim");
  });

  it("固定列名即使重复出现在 gridFields 也不改变 margin/flag 分类", () => {
    const models = buildTableColumns(["margin_min"], ["margin_min"]);
    expect(models[0]).toMatchObject({ kind: "margin", applicable: false });
  });
});

describe("buildApplyPayload（D6 grid 字段投影——dim 输出不可应用）", () => {
  const row = narrowSolutionPage(GOLDEN_PAGE).rows[0] ?? {};

  it("golden 行 n=6 → params 只含 grid 字段（volume/margin_min 不进）", () => {
    const payload = buildApplyPayload(row, ["n"], "p-1", "municipal_aao");
    expect(payload).toEqual({
      project_id: "p-1",
      unit_id: "municipal_aao",
      params: { n: 6 },
    });
  });

  it("多 grid 字段全投影（按 gridFields 序）", () => {
    const payload = buildApplyPayload(
      { n: 4, cycle_t: 6.5, margin_min: 0.1 },
      ["n", "cycle_t"],
      "p-1",
      "municipal_aao",
    );
    expect(payload.params).toEqual({ n: 4, cycle_t: 6.5 });
  });

  it("grid 值非数值（null/string/boolean）跳过不进 params", () => {
    const payload = buildApplyPayload(
      { n: null, cycle_t: "4", ok: true },
      ["n", "cycle_t", "ok"],
      "p-1",
      "municipal_aao",
    );
    expect(payload.params).toEqual({});
  });

  it("gridFields 空 → 空 params（合法载荷——服务端 design_changed=false 面）", () => {
    const payload = buildApplyPayload(row, [], "p-1", "municipal_aao");
    expect(payload).toEqual({
      project_id: "p-1",
      unit_id: "municipal_aao",
      params: {},
    });
  });
});

describe("buildSortOptions（D9 排序选项=响应 columns 白名单）", () => {
  it("golden columns → 选项序同响应序（value=label=列名）", () => {
    expect(buildSortOptions(narrowSolutionPage(GOLDEN_PAGE).columns)).toEqual([
      { value: "n", label: "n" },
      { value: "volume", label: "volume" },
      { value: "margin_min", label: "margin_min" },
      { value: "nan_flag", label: "nan_flag" },
      { value: "condition_key", label: "condition_key" },
    ]);
  });

  it("空 columns → 空选项（表未挂载面）", () => {
    expect(buildSortOptions([])).toEqual([]);
  });
});


// ═══ AUDIT2 FIX2 I-8：未测负例形状入册（探针 2026-08-30 已证实现真拒） ═══
describe("AUDIT2 I-8 solutionsView 未测负例形状", () => {
  it("行值 NaN 拒（头注承诺非有限数按非法拒）", () => {
    expect(() =>
      narrowSolutionPage(
        fixture({ rows: [{ n: Number.NaN, margin_min: 0.1, condition_key: "k" }] }),
      ),
    ).toThrow(SolutionsViewError);
  });
  it("task_id 空串拒", () => {
    expect(() => narrowSolutionPage(fixture({ task_id: "" }))).toThrow(
      SolutionsViewError,
    );
  });
});
