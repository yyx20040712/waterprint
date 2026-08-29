/**
 * elevation 纯函数层：响应窄化门+四线纵断图 option 构造（projectScene 模式）。
 *
 * 输入:  /api/elevation 响应（弱类型 unknown——orval 生成类型不进门，
 *        运行期形状逐字段校验）+ElevationView 窄化产物
 * 输出:  narrowElevationResponse→ElevationView（顶层逐类+stations 十字段
 *        逐项校验，非法抛 ElevationViewError 带键定位）+buildChartOption→
 *        ProfileChartOption（四线 series 纯对象——组件薄壳唯一数据源）
 *
 * 规格说明（FE7 批 6b 段五，D5/D7）：
 *   - D7 窄化门（FE4 D6/FE5 D8/FE6 D4 门模式复用）：顶层八字段
 *     （project_id/condition_key/conditions/datum_note/stations/
 *     pump_stations/drop_warnings/warnings）逐类校验；stations 空数组拒
 *     （纵断至少一站——空纵断属服务端异形）；station 十字段
 *     （unit_id string+九数值）逐项校验；泵站五字段/警告六键（UF-17）
 *     逐项校验；非法形状抛 ElevationViewError（消息带键定位
 *     stations[i].字段——呈现面可反查）；
 *   - D7 option 纯对象：四线=地面/水面/池底/池顶（骨架「管底」措辞系
 *     笔误——ProfileStation 无管底字段，crest_elev=服务端投影池顶，
 *     README 随批勘误）；xAxis category 站位序=响应 stations 序（流程
 *     序——前端不重排）；yAxis scale:true（标高真值原点+横纵比例分设
 *     的 echarts 实现面——比例参数后端 options 面不存在，措辞修正记档）；
 *   - 语义色纪律（§19/D7）：蓝水线/棕泥线（池底）/绿地面线；池顶线=
 *     结构参考线灰+虚线（与实线水面区分——非语义色位）；色值集中
 *     ELEVATION_LINE_COLORS 一处（option 即渲染描述直入 echarts——
 *     无组件材质层，与 projectScene「零色值」口径差异记档）；
 *   - 零推导红线：series data 逐点=station 字段原值（crest 直用
 *     crest_elev 不前端重算——D5 服务端投影面）；零业务计算；
 *   - 零 echarts import（node 环境测试——option 是纯对象不触渲染器）；
 *     零运行期库 import。
 */

/** 窄化产物：纵断站位（十字段=响应 ElevationStation 形状，snake 命名透传）。 */
export type ElevationStationView = {
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

/** 窄化产物：需提升站位（五字段=响应 PumpStationEntry 形状）。 */
export type PumpStationView = {
  unit_id: string;
  static_head: number;
  total_head: number;
  design_flow: number;
  condition_key: string;
};

/** 窄化产物：core Warning 序列化形状（UF-17 六键——可选键缺省 null/[]）。 */
export type WarningView = {
  severity: string;
  source: string;
  message: string;
  param_key: string | null;
  condition_key: string | null;
  affected_unit_ids: string[];
};

/** 窄化产物（D7：elevation 消费面的唯一投影面）。 */
export type ElevationView = {
  project_id: string;
  condition_key: string;
  conditions: string[];
  datum_note: string;
  stations: ElevationStationView[];
  pump_stations: PumpStationView[];
  drop_warnings: WarningView[];
  warnings: WarningView[];
};

/** 窄化非法（顶层逐类拒/站位字段值域外）——消费面错误薄壳呈现。 */
export class ElevationViewError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ElevationViewError";
  }
}

/** 四线语义色（§19 纪律集中一处——深色主题面）。 */
export const ELEVATION_LINE_COLORS = {
  ground: "#52c41a", // 绿地面线（§19）
  water: "#1677ff", // 蓝水线（§19）
  floor: "#8b4513", // 棕泥线=池底（§19）
  crest: "#8c8c8c", // 池顶=结构参考线（灰+虚线，非语义色位）
} as const;

/** 纵断图 option（纯对象——结构面按 echarts LineChart 消费子集声明）。 */
export type ProfileChartOption = {
  tooltip: { trigger: string };
  legend: { data: string[] };
  grid: { left: number; right: number; top: number; bottom: number };
  xAxis: { type: string; data: string[]; name: string };
  yAxis: { type: string; scale: boolean; name: string };
  series: {
    name: string;
    type: string;
    data: number[];
    color?: string;
    lineStyle?: { type?: string; width?: number };
  }[];
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 有限数值判定（bool 排除——typeof boolean 先于 number 面）。 */
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function reject(message: string): never {
  throw new ElevationViewError(message);
}

/** 顶层字符串字段校验（空串拒——键名进消息定位）。 */
function requireString(raw: Record<string, unknown>, key: string): string {
  const value = raw[key];
  if (typeof value !== "string" || value === "") {
    reject(`${key} 须为非空字符串：得到 ${JSON.stringify(value) ?? "undefined"}`);
  }
  return value;
}

/** 数组字段提取（非数组拒——键名进消息定位）。 */
function requireArray(raw: Record<string, unknown>, key: string): unknown[] {
  const value = raw[key];
  if (!Array.isArray(value)) {
    reject(`${key} 须为数组：得到 ${JSON.stringify(value) ?? "undefined"}`);
  }
  return value;
}

/** 站位数值字段名序（校验与投影共用——十字段面单源）。 */
const STATION_NUMBER_KEYS = [
  "water_level",
  "floor_elev",
  "ground_elev",
  "bury_depth",
  "freeboard",
  "water_depth",
  "loss_in",
  "design_flow",
  "crest_elev",
] as const;

/** 警告六键窄化（UF-17——可选键缺省 null/[]）。 */
function narrowWarning(raw: unknown, face: string, index: number): WarningView {
  if (!isRecord(raw)) {
    reject(`${face}[${index}] 须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const severity = raw["severity"];
  if (typeof severity !== "string" || severity === "") {
    reject(`${face}[${index}].severity 须为非空字符串`);
  }
  const source = raw["source"];
  if (typeof source !== "string" || source === "") {
    reject(`${face}[${index}].source 须为非空字符串`);
  }
  const message = raw["message"];
  if (typeof message !== "string" || message === "") {
    reject(`${face}[${index}].message 须为非空字符串`);
  }
  const paramKey = raw["param_key"];
  if (paramKey !== undefined && paramKey !== null && typeof paramKey !== "string") {
    reject(`${face}[${index}].param_key 须为字符串或 null`);
  }
  const conditionKey = raw["condition_key"];
  if (
    conditionKey !== undefined &&
    conditionKey !== null &&
    typeof conditionKey !== "string"
  ) {
    reject(`${face}[${index}].condition_key 须为字符串或 null`);
  }
  const affected = raw["affected_unit_ids"] ?? [];
  if (
    !Array.isArray(affected) ||
    !affected.every((unit) => typeof unit === "string")
  ) {
    reject(`${face}[${index}].affected_unit_ids 须为字符串数组`);
  }
  return {
    severity,
    source,
    message,
    param_key: paramKey ?? null,
    condition_key: conditionKey ?? null,
    affected_unit_ids: affected as string[],
  };
}

/**
 * D7 窄化门：/api/elevation 弱类型响应 → ElevationView（逐类逐字段拒）。
 */
export function narrowElevationResponse(raw: unknown): ElevationView {
  if (!isRecord(raw)) {
    reject(`elevation 响应须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const projectId = requireString(raw, "project_id");
  const conditionKey = requireString(raw, "condition_key");
  const datumNote = requireString(raw, "datum_note");
  const conditionsRaw = requireArray(raw, "conditions");
  if (conditionsRaw.length === 0 || !conditionsRaw.every(isString)) {
    reject("conditions 须为非空字符串数组（工况索引面——D9）");
  }
  const stationsRaw = requireArray(raw, "stations");
  if (stationsRaw.length === 0) {
    reject("stations 须为非空数组（纵断至少一站——空纵断属服务端异形）");
  }
  const stations: ElevationStationView[] = stationsRaw.map((entry, index) => {
    if (!isRecord(entry)) {
      reject(`stations[${index}] 须为对象：得到 ${JSON.stringify(entry) ?? "undefined"}`);
    }
    const unitId = entry["unit_id"];
    if (typeof unitId !== "string" || unitId === "") {
      reject(`stations[${index}].unit_id 须为非空字符串`);
    }
    for (const key of STATION_NUMBER_KEYS) {
      if (!isFiniteNumber(entry[key])) {
        reject(
          `stations[${index}].${key} 须为有限数值：得到 ${JSON.stringify(entry[key]) ?? "undefined"}`,
        );
      }
    }
    return {
      unit_id: unitId,
      water_level: entry["water_level"] as number,
      floor_elev: entry["floor_elev"] as number,
      ground_elev: entry["ground_elev"] as number,
      bury_depth: entry["bury_depth"] as number,
      freeboard: entry["freeboard"] as number,
      water_depth: entry["water_depth"] as number,
      loss_in: entry["loss_in"] as number,
      design_flow: entry["design_flow"] as number,
      crest_elev: entry["crest_elev"] as number,
    };
  });
  const pumpsRaw = requireArray(raw, "pump_stations");
  const pumpStations: PumpStationView[] = pumpsRaw.map((entry, index) => {
    if (!isRecord(entry)) {
      reject(`pump_stations[${index}] 须为对象：得到 ${JSON.stringify(entry) ?? "undefined"}`);
    }
    const unitId = entry["unit_id"];
    if (typeof unitId !== "string" || unitId === "") {
      reject(`pump_stations[${index}].unit_id 须为非空字符串`);
    }
    const condition = entry["condition_key"];
    if (typeof condition !== "string" || condition === "") {
      reject(`pump_stations[${index}].condition_key 须为非空字符串`);
    }
    for (const key of ["static_head", "total_head", "design_flow"] as const) {
      if (!isFiniteNumber(entry[key])) {
        reject(
          `pump_stations[${index}].${key} 须为有限数值：得到 ${JSON.stringify(entry[key]) ?? "undefined"}`,
        );
      }
    }
    return {
      unit_id: unitId,
      static_head: entry["static_head"] as number,
      total_head: entry["total_head"] as number,
      design_flow: entry["design_flow"] as number,
      condition_key: condition,
    };
  });
  const dropWarnings = requireArray(raw, "drop_warnings").map((entry, index) =>
    narrowWarning(entry, "drop_warnings", index),
  );
  const warnings = requireArray(raw, "warnings").map((entry, index) =>
    narrowWarning(entry, "warnings", index),
  );
  return {
    project_id: projectId,
    condition_key: conditionKey,
    conditions: conditionsRaw as string[],
    datum_note: datumNote,
    stations,
    pump_stations: pumpStations,
    drop_warnings: dropWarnings,
    warnings,
  };
}

/** string 判定（conditions 数组元素面——命名避免与 requireString 混淆）。 */
function isString(value: unknown): value is string {
  return typeof value === "string";
}

/**
 * D7 四线纵断 option：ElevationView → echarts LineChart 纯对象（零推导）。
 */
export function buildChartOption(view: ElevationView): ProfileChartOption {
  const unitIds = view.stations.map((station) => station.unit_id);
  const lineOf = (
    name: string,
    field: (station: ElevationStationView) => number,
    color: string,
    dashed: boolean,
  ) => ({
    name,
    type: "line",
    data: view.stations.map(field),
    color,
    lineStyle: dashed ? { type: "dashed", width: 2 } : { width: 2 },
  });
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["地面线", "水面线", "池底线", "池顶线"] },
    grid: { left: 48, right: 24, top: 32, bottom: 48 },
    xAxis: { type: "category", data: unitIds, name: "单元" },
    yAxis: { type: "value", scale: true, name: "标高（m）" },
    series: [
      lineOf("地面线", (s) => s.ground_elev, ELEVATION_LINE_COLORS.ground, false),
      lineOf("水面线", (s) => s.water_level, ELEVATION_LINE_COLORS.water, false),
      lineOf("池底线", (s) => s.floor_elev, ELEVATION_LINE_COLORS.floor, false),
      lineOf("池顶线", (s) => s.crest_elev, ELEVATION_LINE_COLORS.crest, true),
    ],
  };
}
