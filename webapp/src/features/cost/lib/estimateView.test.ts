/**
 * 投影层纯函数测试：cost 响应窄化门+分级表行模型构造（node 环境）。
 *
 * 输入:  estimateView 纯函数（node 环境——零 antd import，先红后绿）
 * 输出:  投影契约断言（窄化门逐类拒带键定位/分级行序/小计行族/
 *        展开溯源面/指标 status 域与 checked 面）
 */
import { describe, expect, it } from "vitest";

import {
  CostViewError,
  buildTableRows,
  narrowCostResponse,
  type CostView,
} from "./estimateView";

type FixtureRow = {
  price_key: string;
  name_zh: string;
  unit: string;
  quantity: number;
  unit_price: number;
  amount: number;
  source_field_ids: string[];
  source: string;
};

type FixtureFeeLine = {
  fee_key: string;
  rate: number;
  base: string;
  base_amount: number;
  amount: number;
  source: string;
};

type Fixture = {
  project_id: string;
  condition_key: string;
  conditions: string[];
  price_data_version: string;
  design_scale: number;
  sheet: {
    detail_rows: FixtureRow[];
    measure: FixtureFeeLine[];
    indirect: FixtureFeeLine[];
    reserve: FixtureFeeLine[];
    tax: FixtureFeeLine[];
    detail_subtotal: number;
    equipment_subtotal: number;
    construction_subtotal: number;
    subtotal: number;
    reserve_subtotal: number;
    grand_total: number;
    repro: { design_hash: string; engine_version: string; data_version: string };
    condition_key: string;
  };
  indicators: {
    readings: {
      indicator_key: string;
      value: number;
      band: { min: number; max: number };
      status: string;
      reason: string;
    }[];
    checked: boolean;
  };
};

/** 单笔明细夹具（量×单价=金额自洽）。 */
function rowFixture(
  priceKey: string,
  nameZh: string,
  unit: string,
  quantity: number,
  unitPrice: number,
  fields: string[],
): FixtureRow {
  return {
    price_key: priceKey,
    name_zh: nameZh,
    unit,
    quantity,
    unit_price: unitPrice,
    amount: quantity * unitPrice,
    source_field_ids: fields,
    source: "2019 黑龙江建筑工程计价定额（测试夹具）",
  };
}

/** 费行夹具（基数×费率=金额自洽）。 */
function feeFixture(
  feeKey: string,
  rate: number,
  base: string,
  baseAmount: number,
): FixtureFeeLine {
  return {
    fee_key: feeKey,
    rate,
    base,
    base_amount: baseAmount,
    amount: baseAmount * rate,
    source: "T/BCEBCA 1-2023（测试夹具）",
  };
}

/**
 * 内联夹具：golden 真值同构形态（747.8 万元量级自由构造——二审复算
 * grand_total=7,478,090.21 元=747.81 万元[R6 修正：原注释 1,190.86 万
 * 失真]；服务端 CASS 同款结构 3 明细+四桶 1/4/1/1，数字自洽非锚真值）。
 */
function costFixture(): Fixture {
  const rows = [
    rowFixture(
      "concrete_c30_floor",
      "C30 抗渗混凝土底板",
      "m3",
      3476.07,
      680.0,
      ["municipal_cass.v_pool"],
    ),
    rowFixture(
      "rebar_hp300",
      "HPB300 钢筋",
      "t",
      174.0,
      4600.0,
      ["municipal_cass.rebar"],
    ),
    rowFixture(
      "blower_roots",
      "罗茨风机",
      "台",
      3,
      120000.0,
      ["municipal_cass.n_blowers"],
    ),
  ];
  const measure = [feeFixture("rate.measure", 0.02, "detail_subtotal", 11283907.4)];
  const indirect = [
    feeFixture("rate.install", 0.15, "equipment_subtotal", 360000.0),
    feeFixture("rate.manage", 0.05, "construction_subtotal", 11509644.6),
    feeFixture("rate.design", 0.03, "construction_subtotal", 11509644.6),
    feeFixture("rate.supervise", 0.02, "construction_subtotal", 11509644.6),
  ];
  const reserve = [feeFixture("rate.reserve", 0.1, "subtotal", 12680000.0)];
  const tax = [feeFixture("rate.tax", 0.09, "subtotal + reserve_subtotal", 13948000.0)];
  const detailSubtotal = rows.reduce((sum, row) => sum + row.amount, 0);
  const equipmentSubtotal = rows[2]!.amount;
  const measureSum = measure.reduce((sum, line) => sum + line.amount, 0);
  const constructionSubtotal = detailSubtotal + measureSum;
  const indirectSum = indirect.reduce((sum, line) => sum + line.amount, 0);
  const subtotal = constructionSubtotal + indirectSum;
  const reserveSubtotal = reserve.reduce((sum, line) => sum + line.amount, 0);
  const taxSum = tax.reduce((sum, line) => sum + line.amount, 0);
  return {
    project_id: "p-fe8",
    condition_key: "design",
    conditions: ["avg", "design"],
    price_data_version: "1.0.0",
    design_scale: 34760.7,
    sheet: {
      detail_rows: rows,
      measure,
      indirect,
      reserve,
      tax,
      detail_subtotal: detailSubtotal,
      equipment_subtotal: equipmentSubtotal,
      construction_subtotal: constructionSubtotal,
      subtotal,
      reserve_subtotal: reserveSubtotal,
      grand_total: subtotal + reserveSubtotal + taxSum,
      repro: {
        design_hash: "5b589e43",
        engine_version: "waterprint-server 0.1.0",
        data_version: "2026-08",
      },
      condition_key: "design",
    },
    indicators: {
      readings: [
        {
          indicator_key: "indicator.unit_cost",
          value: 342.58,
          band: { min: 3000, max: 5000 },
          status: "WARN",
          reason: "指标 indicator.unit_cost 值 342.58 低于经验带下限（测试夹具）",
        },
      ],
      checked: true,
    },
  };
}

describe("narrowCostResponse 窄化门", () => {
  it("合例：全字段保真窄化（顶层+sheet 数值族+指标面）", () => {
    const view = narrowCostResponse(costFixture());
    expect(view.project_id).toBe("p-fe8");
    expect(view.condition_key).toBe("design");
    expect(view.conditions).toEqual(["avg", "design"]);
    expect(view.price_data_version).toBe("1.0.0");
    expect(view.design_scale).toBeCloseTo(34760.7, 6);
    expect(view.sheet.grand_total).toBeCloseTo(
      view.sheet.subtotal +
        view.sheet.reserve_subtotal +
        view.sheet.tax.reduce((sum, line) => sum + line.amount, 0),
      6,
    ); // 分级自洽（grand=subtotal+reserve+Σtax——服务端契约形态）
    expect(view.sheet.detail_rows).toHaveLength(3);
    expect(view.sheet.detail_rows[0]!.name_zh).toBe("C30 抗渗混凝土底板");
    expect(view.sheet.repro.data_version).toBe("2026-08");
    expect(view.indicators.checked).toBe(true);
    expect(view.indicators.readings[0]!.status).toBe("WARN");
  });

  it("顶层非对象拒（消息带定位）", () => {
    expect(() => narrowCostResponse(null)).toThrow(CostViewError);
    expect(() => narrowCostResponse("cost")).toThrow(/对象/);
  });

  it("顶层字符串字段空串拒（project_id/condition_key/price_data_version）", () => {
    for (const key of ["project_id", "condition_key", "price_data_version"]) {
      const bad = { ...costFixture(), [key]: "" } as unknown;
      expect(() => narrowCostResponse(bad), key).toThrow(CostViewError);
    }
  });

  it("conditions 空数组拒+元素空串拒（工况索引面）", () => {
    const empty = { ...costFixture(), conditions: [] } as unknown;
    expect(() => narrowCostResponse(empty)).toThrow(/conditions/);
    const blank = { ...costFixture(), conditions: ["design", ""] } as unknown;
    expect(() => narrowCostResponse(blank)).toThrow(/conditions/);
  });

  it("design_scale NaN/Infinity/bool 拒（数值域门）", () => {
    for (const evil of [Number.NaN, Number.POSITIVE_INFINITY, true]) {
      const bad = { ...costFixture(), design_scale: evil } as unknown;
      expect(() => narrowCostResponse(bad), `design_scale=${String(evil)}`).toThrow(
        CostViewError,
      );
    }
  });

  it("sheet 小计数值族缺键/NaN 拒（grand_total 等）", () => {
    const missing = costFixture();
    delete (missing.sheet as Record<string, unknown>).grand_total;
    expect(() => narrowCostResponse(missing)).toThrow(/grand_total/);
    const nan = costFixture();
    nan.sheet.subtotal = Number.NaN;
    expect(() => narrowCostResponse(nan)).toThrow(/subtotal/);
  });

  it("detail_rows 非数组拒+行缺 name_zh 拒+source_field_ids 空拒", () => {
    const notArray = costFixture();
    (notArray.sheet as unknown as Record<string, unknown>).detail_rows = {};
    expect(() => narrowCostResponse(notArray)).toThrow(/detail_rows/);
    const noName = costFixture();
    delete (noName.sheet.detail_rows[0] as Record<string, unknown>).name_zh;
    expect(() => narrowCostResponse(noName)).toThrow(/name_zh/);
    const noFields = costFixture();
    noFields.sheet.detail_rows[1]!.source_field_ids = [];
    expect(() => narrowCostResponse(noFields)).toThrow(/source_field_ids/);
  });

  it("四费桶行缺 source 拒+rate NaN 拒（逐桶逐键定位）", () => {
    const noSource = costFixture();
    delete (noSource.sheet.indirect[0] as Record<string, unknown>).source;
    expect(() => narrowCostResponse(noSource)).toThrow(/indirect\[0\]\.source/);
    const badRate = costFixture();
    badRate.sheet.tax[0]!.rate = Number.NaN;
    expect(() => narrowCostResponse(badRate)).toThrow(/tax\[0\]\.rate/);
  });

  it("repro 缺 data_version 拒（三元组完整面）", () => {
    const bad = costFixture();
    delete (bad.sheet.repro as Record<string, unknown>).data_version;
    expect(() => narrowCostResponse(bad)).toThrow(/data_version/);
  });

  it("indicators status 超域拒+小写变体拒（{OK,WARN} 冻结面）", () => {
    for (const evil of ["ERROR", "warn"]) {
      const bad = costFixture();
      bad.indicators.readings[0]!.status = evil;
      expect(() => narrowCostResponse(bad), `status=${evil}`).toThrow(/status/);
    }
  });

  it("indicators checked 非布尔拒+band 缺 min 拒+band min>=max 拒", () => {
    const notBool = costFixture();
    (notBool.indicators as unknown as Record<string, unknown>).checked = "yes";
    expect(() => narrowCostResponse(notBool)).toThrow(/checked/);
    const noMin = costFixture();
    delete (noMin.indicators.readings[0]!.band as Record<string, unknown>).min;
    expect(() => narrowCostResponse(noMin)).toThrow(/band/);
    const inverted = costFixture();
    inverted.indicators.readings[0]!.band = { min: 5000, max: 3000 };
    expect(() => narrowCostResponse(inverted)).toThrow(/band/);
  });
});

describe("buildTableRows 分级行模型", () => {
  it("行序=服务端装配序：明细→分部分项小计→设备小计→措施→建安小计→间接→小计→预备→预备小计→税→总投资", () => {
    const view = narrowCostResponse(costFixture());
    const rows = buildTableRows(view);
    expect(rows.map((row) => row.key)).toEqual([
      "detail:concrete_c30_floor",
      "detail:rebar_hp300",
      "detail:blower_roots",
      "subtotal:detail_subtotal",
      "subtotal:equipment_subtotal",
      "fee:measure:rate.measure",
      "subtotal:construction_subtotal",
      "fee:indirect:rate.install",
      "fee:indirect:rate.manage",
      "fee:indirect:rate.design",
      "fee:indirect:rate.supervise",
      "subtotal:subtotal",
      "fee:reserve:rate.reserve",
      "subtotal:reserve_subtotal",
      "fee:tax:rate.tax",
      "grand:grand_total",
    ]);
  });

  it("小计行族金额逐级保真+kind 高亮面（subtotal/grand）", () => {
    const view = narrowCostResponse(costFixture());
    const rows = buildTableRows(view);
    const byKey = new Map(rows.map((row) => [row.key, row]));
    expect(byKey.get("subtotal:detail_subtotal")?.amount).toBeCloseTo(
      view.sheet.detail_subtotal,
      6,
    );
    expect(byKey.get("subtotal:grand_total" in byKey ? "x" : "grand:grand_total")?.kind).toBe("grand");
    expect(byKey.get("grand:grand_total")?.amount).toBeCloseTo(view.sheet.grand_total, 6);
    expect(rows.filter((row) => row.kind === "subtotal")).toHaveLength(5);
    expect(rows.filter((row) => row.kind === "fee")).toHaveLength(7); // 措施1+间接4+预备1+税1
  });

  it("detail 行逐笔保真+展开溯源面（price_key/source_field_ids/unit_price/repro 串）", () => {
    const view = narrowCostResponse(costFixture());
    const rows = buildTableRows(view);
    const first = rows[0];
    expect(first?.kind).toBe("detail");
    expect(first?.label).toBe("C30 抗渗混凝土底板");
    expect(first?.amount).toBeCloseTo(3476.07 * 680.0, 6);
    expect(first?.trace).toEqual({
      price_key: "concrete_c30_floor",
      source_field_ids: ["municipal_cass.v_pool"],
      unit_price: 680.0,
      repro: "5b589e43 | waterprint-server 0.1.0 | 2026-08",
    });
  });

  it("fee 行挂桶名（措施/间接/预备/税）+费率与基数透传", () => {
    const view = narrowCostResponse(costFixture());
    const rows = buildTableRows(view);
    const install = rows.find((row) => row.key === "fee:indirect:rate.install");
    expect(install?.bucket).toBe("间接费");
    expect(install?.amount).toBeCloseTo(360000.0 * 0.15, 6);
    const taxLine = rows.find((row) => row.key === "fee:tax:rate.tax");
    expect(taxLine?.bucket).toBe("税费");
  });

  it("R5（zM-3）：fee 行 rate 全数透传+detail/小计行不挂费率（费率列数据面）", () => {
    const view = narrowCostResponse(costFixture());
    const rows = buildTableRows(view);
    const feeRows = rows.filter((row) => row.kind === "fee");
    // 逐行 rate 透传（费桶构成=费率×基数 UI 可见前提——行模型已挂载面）
    expect(feeRows.map((row) => row.rate)).toEqual([0.02, 0.15, 0.05, 0.03, 0.02, 0.1, 0.09]);
    // 基数 DSL 字符串直投（FeeLineView 面——窄化产物保真）
    expect(view.sheet.indirect[0]!.base).toBe("equipment_subtotal");
    expect(view.sheet.tax[0]!.base).toBe("subtotal + reserve_subtotal");
    // 非费行不挂费率（detail/小计/grand 留空——EstimateTable 费率列空白面）
    expect(
      rows.filter((row) => row.kind !== "fee").every((row) => row.rate === undefined),
    ).toBe(true);
  });

  it("checked:false 未校核面如实透传（空 readings 合法）", () => {
    const fixture = costFixture();
    fixture.indicators = { readings: [], checked: false };
    const view: CostView = narrowCostResponse(fixture);
    expect(view.indicators.readings).toEqual([]);
    expect(view.indicators.checked).toBe(false);
    expect(buildTableRows(view)).toHaveLength(16); // 行模型不受指标面影响
  });
});


// ═══ AUDIT2 FIX2 I-8：未测负例形状入册（探针 2026-08-30 已证实现真拒） ═══
describe("AUDIT2 I-8 estimateView 未测负例形状", () => {
  const bad = (mutate: (v: Record<string, unknown>) => void): unknown => {
    const value = JSON.parse(JSON.stringify(costFixture())) as Record<string, unknown>;
    mutate(value);
    return value;
  };
  it("空 detail_rows 拒（FE8 空数组口径同型——服务端异形）", () => {
    const v = bad((x) => {
      (x.sheet as Record<string, unknown>).detail_rows = [];
    });
    expect(() => narrowCostResponse(v)).toThrow(/detail_rows/);
  });
  it("conditions 非数组拒", () => {
    expect(() => narrowCostResponse(bad((x) => { x.conditions = "avg"; }))).toThrow();
  });
  it("sheet 非对象拒", () => {
    expect(() => narrowCostResponse(bad((x) => { x.sheet = []; }))).toThrow();
  });
  it("readings[i].value NaN 拒", () => {
    const v = bad((x) => {
      x.indicators = {
        checked: true,
        readings: [{ name_zh: "x", value: Number.NaN, band: { min: 0, max: 1 }, status: "OK", reason: "r" }],
      };
    });
    expect(() => narrowCostResponse(v)).toThrow();
  });
  it("detail 行 amount NaN 拒", () => {
    const v = bad((x) => {
      const rows = (x.sheet as Record<string, unknown>).detail_rows as Record<string, unknown>[];
      rows[0]!.amount = Number.NaN;
    });
    expect(() => narrowCostResponse(v)).toThrow();
  });
  it("费桶非数组拒", () => {
    const v = bad((x) => {
      (x.sheet as Record<string, unknown>).measure = "x";
    });
    expect(() => narrowCostResponse(v)).toThrow();
  });
});


// ═══ AUDIT2 FIX2（C-1 闭环）：stale 旗标透传 ═══
describe("AUDIT2 stale 旗标透传", () => {
  it("缺省（字段缺席）→ false 向后兼容", () => {
    const raw = JSON.parse(JSON.stringify(costFixture())) as Record<string, unknown>;
    delete raw.stale;
    expect(narrowCostResponse(raw).stale).toBe(false);
  });
  it("stale=true 透传（改档不重算面——pane 横幅消费）", () => {
    const raw = { ...(costFixture() as object), stale: true } as unknown;
    expect(narrowCostResponse(raw).stale).toBe(true);
  });
});
