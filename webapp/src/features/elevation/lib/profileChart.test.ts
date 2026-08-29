/**
 * 投影层纯函数测试：elevation 响应窄化门+纵断图 option 构造（node 环境）。
 *
 * 输入:  profileChart 纯函数（node 环境——零 echarts import，先红后绿）
 * 输出:  投影契约断言（窄化门逐类拒带键定位/四线 series/语义色/yAxis 真值原点）
 */
import { describe, expect, it } from "vitest";

import {
  ELEVATION_LINE_COLORS,
  ElevationViewError,
  buildChartOption,
  narrowElevationResponse,
} from "./profileChart";

type FixtureWarning = {
  severity: string;
  source: string;
  message: string;
  param_key?: string | null;
  condition_key?: string | null;
  affected_unit_ids?: string[];
};

type FixtureStation = {
  unit_id: string;
  water_level: number;
  floor_elev: number;
  ground_elev: number;
  bury_depth: number;
  freeboard: number;
  water_depth: number;
  loss_in: number;
  design_flow: number;
  crest_elev: number;
};

type Fixture = {
  project_id: string;
  condition_key: string;
  conditions: string[];
  datum_note: string;
  stations: FixtureStation[];
  pump_stations: {
    unit_id: string;
    static_head: number;
    total_head: number;
    design_flow: number;
    condition_key: string;
  }[];
  drop_warnings: FixtureWarning[];
  warnings: FixtureWarning[];
};

function warningFixture(severity: string, unit: string): FixtureWarning {
  return {
    severity,
    source: "elevation.bury_depth.max（测试夹具）",
    message: `单元 ${unit} 测试警告`,
    param_key: null,
    condition_key: "design",
    affected_unit_ids: [unit],
  };
}

/** golden 内联夹具（三站纵断+一提升站+一跌水+两警告——字段面按 D1~D5 契约）。 */
function fixture(): Fixture {
  return {
    project_id: "demo.wp",
    condition_key: "design",
    conditions: ["avg", "design"],
    datum_note: "相对标高：进厂水面=±0.00——绝对标高输入通道未接线",
    stations: [
      {
        unit_id: "municipal_wushui_tisheng",
        water_level: 0,
        floor_elev: 0,
        ground_elev: 0,
        bury_depth: 0,
        freeboard: 0.3,
        water_depth: 0,
        loss_in: 0,
        design_flow: 0.402323,
        crest_elev: 0.3,
      },
      {
        unit_id: "municipal_chenshachi",
        water_level: 0,
        floor_elev: -1.25,
        ground_elev: 0,
        bury_depth: 1.25,
        freeboard: 0.3,
        water_depth: 1.25,
        loss_in: 0,
        design_flow: 0.402323,
        crest_elev: 0.3,
      },
      {
        unit_id: "municipal_ziwai",
        water_level: 0,
        floor_elev: -0.6,
        ground_elev: 0,
        bury_depth: 0.6,
        freeboard: 0.3,
        water_depth: 0.6,
        loss_in: 0,
        design_flow: 0.402323,
        crest_elev: 0.3,
      },
    ],
    pump_stations: [
      {
        unit_id: "municipal_chenshachi",
        static_head: 1.25,
        total_head: 1.31,
        design_flow: 0.402323,
        condition_key: "design",
      },
    ],
    drop_warnings: [
      warningFixture("WARN", "municipal_chenshachi"),
    ],
    warnings: [warningFixture("INFO", "municipal_wushui_tisheng")],
  };
}

describe("narrowElevationResponse：顶层逐类校验", () => {
  it("合法响应放行且全字段透传（snake 命名面零改写）", () => {
    const raw = fixture();
    const view = narrowElevationResponse(raw);
    expect(view.project_id).toBe("demo.wp");
    expect(view.condition_key).toBe("design");
    expect(view.conditions).toEqual(["avg", "design"]);
    expect(view.datum_note).toContain("±0.00");
    expect(view.stations).toHaveLength(3);
    expect(view.pump_stations[0]?.unit_id).toBe("municipal_chenshachi");
    expect(view.drop_warnings).toHaveLength(1);
    expect(view.warnings).toHaveLength(1);
  });

  it("非对象拒（数组/null 均拒）", () => {
    expect(() => narrowElevationResponse([fixture()])).toThrow(ElevationViewError);
    expect(() => narrowElevationResponse(null)).toThrow(ElevationViewError);
  });

  it("顶层缺 conditions/condition_key 非 string 拒且消息带键定位", () => {
    const missing = fixture() as Record<string, unknown>;
    delete missing["conditions"];
    expect(() => narrowElevationResponse(missing)).toThrow(/conditions/);
    const bad = { ...fixture(), condition_key: 7 };
    expect(() => narrowElevationResponse(bad)).toThrow(/condition_key/);
  });

  it("conditions 含非字符串拒（工况索引面 D9 前置）", () => {
    const bad = { ...fixture(), conditions: ["avg", 3] };
    expect(() => narrowElevationResponse(bad)).toThrow(/conditions/);
  });

  it("stations 非数组/空数组拒（纵断至少一站）", () => {
    expect(() => narrowElevationResponse({ ...fixture(), stations: "x" })).toThrow(
      /stations/,
    );
    expect(() => narrowElevationResponse({ ...fixture(), stations: [] })).toThrow(
      /stations/,
    );
  });
});

describe("narrowElevationResponse：站位/泵站/警告逐字段校验", () => {
  it("station 缺数值字段拒且消息定位到 stations[i].字段（crest_elev 含）", () => {
    const stations = [...fixture().stations];
    delete (stations[1] as Record<string, unknown>)["crest_elev"];
    expect(() => narrowElevationResponse({ ...fixture(), stations })).toThrow(
      /stations\[1\]\.crest_elev/,
    );
  });

  it("station unit_id 非 string 拒（带站位定位）", () => {
    const stations = [...fixture().stations];
    stations[0]!.unit_id = 42 as unknown as string;
    expect(() => narrowElevationResponse({ ...fixture(), stations })).toThrow(
      /stations\[0\]\.unit_id/,
    );
  });

  it("pump_stations 条目缺 static_head 拒且消息定位（D4 提升面）", () => {
    const pumpStations = [...fixture().pump_stations];
    delete (pumpStations[0] as Record<string, unknown>)["static_head"];
    expect(() => narrowElevationResponse({ ...fixture(), pump_stations: pumpStations })).toThrow(
      /pump_stations\[0\]\.static_head/,
    );
  });

  it("warnings 条目缺 severity 拒且消息定位（UF-17 六键面）", () => {
    const warnings = [...fixture().warnings];
    delete (warnings[0] as Record<string, unknown>)["severity"];
    expect(() => narrowElevationResponse({ ...fixture(), warnings })).toThrow(
      /warnings\[0\]\.severity/,
    );
  });

  it("同输入双跑产物逐字段相同（确定性）", () => {
    expect(narrowElevationResponse(fixture())).toEqual(narrowElevationResponse(fixture()));
  });
});

describe("buildChartOption：四线纵断 option（纯对象零 echarts import）", () => {
  it("四 series 恰合且名称序=地面/水面/池底/池顶（D5 四线）", () => {
    const option = buildChartOption(narrowElevationResponse(fixture()));
    const series = option.series as { name: string; type: string }[];
    expect(series.map((item) => item.name)).toEqual([
      "地面线",
      "水面线",
      "池底线",
      "池顶线",
    ]);
    expect(series.every((item) => item.type === "line")).toBe(true);
  });

  it("xAxis category data=响应站位序（流程序=stations 序）", () => {
    const option = buildChartOption(narrowElevationResponse(fixture()));
    expect(option.xAxis).toMatchObject({
      type: "category",
      data: [
        "municipal_wushui_tisheng",
        "municipal_chenshachi",
        "municipal_ziwai",
      ],
    });
  });

  it("yAxis scale=true（标高真值原点——不强制含 0 起点）", () => {
    const option = buildChartOption(narrowElevationResponse(fixture()));
    expect(option.yAxis).toMatchObject({ type: "value", scale: true });
  });

  it("series data 零推导逐点透传（crest 直用 crest_elev 不前端重算）", () => {
    const option = buildChartOption(narrowElevationResponse(fixture()));
    const series = option.series as { name: string; data: number[] }[];
    const ground = series.find((item) => item.name === "地面线");
    const water = series.find((item) => item.name === "水面线");
    const floor = series.find((item) => item.name === "池底线");
    const crest = series.find((item) => item.name === "池顶线");
    expect(ground?.data).toEqual([0, 0, 0]);
    expect(water?.data).toEqual([0, 0, 0]);
    expect(floor?.data).toEqual([0, -1.25, -0.6]);
    expect(crest?.data).toEqual([0.3, 0.3, 0.3]);
  });

  it("语义色纪律：水面蓝/池底棕/地面绿（§19）+池顶虚线区分", () => {
    const option = buildChartOption(narrowElevationResponse(fixture()));
    const series = option.series as {
      name: string;
      color?: string;
      lineStyle?: { type?: string };
    }[];
    const of = (name: string) => series.find((item) => item.name === name);
    expect(of("水面线")?.color).toBe(ELEVATION_LINE_COLORS.water);
    expect(of("池底线")?.color).toBe(ELEVATION_LINE_COLORS.floor);
    expect(of("地面线")?.color).toBe(ELEVATION_LINE_COLORS.ground);
    expect(of("池顶线")?.color).toBe(ELEVATION_LINE_COLORS.crest);
    expect(of("池顶线")?.lineStyle?.type).toBe("dashed");
  });

  it("tooltip 轴触发+legend 四线名齐（标高标注面）", () => {
    const option = buildChartOption(narrowElevationResponse(fixture()));
    expect(option.tooltip).toMatchObject({ trigger: "axis" });
    expect(option.legend).toMatchObject({
      data: ["地面线", "水面线", "池底线", "池顶线"],
    });
  });

  it("同输入双跑 option 逐字段相同（确定性——纯函数）", () => {
    const view = narrowElevationResponse(fixture());
    expect(buildChartOption(view)).toEqual(buildChartOption(view));
  });
});
