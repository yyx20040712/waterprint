/**
 * cost 纯函数层：响应窄化门+分级汇总表行模型构造（profileChart 模式）。
 *
 * 输入:  /api/cost 响应（弱类型 unknown——orval 生成类型不进门，运行期
 *        形状逐字段校验）+CostView 窄化产物
 * 输出:  narrowCostResponse→CostView（顶层逐类+sheet 数值族/明细九字段/
 *        四费桶六字段/三元组/指标五键逐项校验，非法抛 CostViewError 带
 *        键定位）+buildTableRows→EstimateTableRow[]（分级行模型——组件
 *        薄壳唯一数据源）
 *
 * 规格说明（FE8 批 6b 段六，D4~D7）：
 *   - D7 窄化门（FE4/FE5/FE6/FE7 门模式第五例）：顶层七字段
 *     （project_id/condition_key/conditions/price_data_version/
 *     design_scale/sheet/indicators）逐类校验；conditions 元素空串拒；
 *     sheet 六数值族（小计族+grand_total）NaN/Infinity/bool 拒；
 *     detail_rows 九字段（含 name_zh 中文列名——服务端单一真源直投）；
 *     四费桶 FeeLine 六字段；repro 三元组完整面；indicators status 域
 *     {OK,WARN}（core indicators 冻结面——超域/小写变体拒，防异常级串
 *     直入语义色映射）+checked 布尔+band {min,max} 有限且 min<max；
 *   - buildTableRows 分级行序=服务端装配序（D5「行序=服务端序」的行模型
 *     落点）：明细行（服务端序）→分部分项小计→设备费小计（信息行）→
 *     措施行→建安小计→间接行→小计→预备行→预备小计→税行→总投资；
 *     小计行族五键+grand 高亮面（kind=subtotal/grand——组件按 kind 上
 *     行样式，金额 tabular-nums 右对齐）；零推导红线：金额全部原值
 *     透传不重算（分级自洽是服务端契约）；
 *   - 每笔溯源（M4「任一数字可回溯」前端落点）：detail 行挂 trace
 *     {price_key, source_field_ids, unit_price, repro 串}——展开行
 *     呈现面；repro 串=三元组拼接（深链 calcbook 挂账 M4④——面板只
 *     显示 repro 字符串）；
 *   - 桶名常量（措施费/间接费/预备费/税费）：core estimate.BUCKETS 四桶
 *     冻结概念的显示层名（非数据翻译——fee_key 字段 ID 原样透传）；
 *   - 零 antd import（node 环境测试）；零运行期库 import。
 */

/** 窄化产物：单笔分部分项（九字段=响应 EstimateRow 形状，snake 透传）。 */
export type EstimateRowView = {
  price_key: string;
  name_zh: string;
  unit: string;
  quantity: number;
  unit_price: number;
  amount: number;
  source_field_ids: string[];
  source: string;
};

/** 窄化产物：单笔费用行（六字段=响应 FeeLine 形状）。 */
export type FeeLineView = {
  fee_key: string;
  rate: number;
  base: string;
  base_amount: number;
  amount: number;
  source: string;
};

/** 窄化产物：指标单项（band 嵌套 {min,max}——D4 形状）。 */
export type IndicatorReadingView = {
  indicator_key: string;
  value: number;
  band: { min: number; max: number };
  status: string;
  reason: string;
};

/** 窄化产物（D7：cost 消费面的唯一投影面）。 */
export type CostView = {
  project_id: string;
  condition_key: string;
  conditions: string[];
  /** 结果集过期旗标（AUDIT2 FIX1 C-1 服务端字段——缺省容忍 false 向后兼容）。 */
  stale: boolean;
  price_data_version: string;
  design_scale: number;
  sheet: {
    detail_rows: EstimateRowView[];
    measure: FeeLineView[];
    indirect: FeeLineView[];
    reserve: FeeLineView[];
    tax: FeeLineView[];
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
    readings: IndicatorReadingView[];
    checked: boolean;
  };
};

/** 表行类别（组件渲染分面：明细/费用/小计/总投资——小计族+grand 高亮）。 */
export type EstimateRowKind = "detail" | "fee" | "subtotal" | "grand";

/** 分级行模型（D5：EstimateTable 唯一数据源——金额原值透传零推导）。 */
export type EstimateTableRow = {
  key: string;
  kind: EstimateRowKind;
  label: string;
  amount: number;
  unit?: string;
  quantity?: number;
  unitPrice?: number;
  rate?: number;
  bucket?: string;
  trace?: {
    price_key: string;
    source_field_ids: string[];
    unit_price: number;
    repro: string;
  };
};

/** 窄化非法（顶层逐类拒/字段值域外/指标 status 超域）——消费面错误薄壳呈现。 */
export class CostViewError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CostViewError";
  }
}

/** 四桶键（core estimate.BUCKETS 冻结面）。 */
type BucketKey = "measure" | "indirect" | "reserve" | "tax";

/** 小计行族键（窄化数值族键的子集——行模型单源）。 */
type SubtotalKey = Exclude<(typeof SHEET_NUMBER_KEYS)[number], "grand_total">;

/** 四桶显示层名（core estimate.BUCKETS 冻结概念——非数据翻译面）。 */
const BUCKET_LABELS: Record<BucketKey, string> = {
  measure: "措施费",
  indirect: "间接费",
  reserve: "预备费",
  tax: "税费",
};

/** 小计行族标签（显示层常量——行序=core 求值序）。 */
const SUBTOTAL_LABELS: Record<SubtotalKey, string> = {
  detail_subtotal: "分部分项小计",
  equipment_subtotal: "设备费小计（信息行）",
  construction_subtotal: "建安小计",
  subtotal: "小计",
  reserve_subtotal: "预备费小计",
};

/** 小计数值族键序（窄化与行模型共用——单源）。 */
const SHEET_NUMBER_KEYS = [
  "detail_subtotal",
  "equipment_subtotal",
  "construction_subtotal",
  "subtotal",
  "reserve_subtotal",
  "grand_total",
] as const;

/** 指标状态合法域（core indicators STATUS_OK/STATUS_WARN 冻结面）。 */
const STATUS_DOMAIN: readonly string[] = ["OK", "WARN"];

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** 有限数值判定（bool 排除——typeof boolean 先于 number 面）。 */
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function reject(message: string): never {
  throw new CostViewError(message);
}

/** 顶层字符串字段校验（空串拒——键名进消息定位；label=嵌套面消息前缀）。 */
function requireString(raw: Record<string, unknown>, key: string, label = key): string {
  const value = raw[key];
  if (typeof value !== "string" || value === "") {
    reject(`${label} 须为非空字符串：得到 ${JSON.stringify(value) ?? "undefined"}`);
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

/** 三元组窄化（design_hash/engine_version/data_version 完整面）。 */
function narrowRepro(raw: Record<string, unknown>): CostView["sheet"]["repro"] {
  const repro = raw["repro"];
  if (!isRecord(repro)) {
    reject(`sheet.repro 须为对象：得到 ${JSON.stringify(repro) ?? "undefined"}`);
  }
  return {
    design_hash: requireString(repro, "design_hash"),
    engine_version: requireString(repro, "engine_version"),
    data_version: requireString(repro, "data_version"),
  };
}

/** repro 溯源串（M4④：面板只显示 repro 字符串——三元组拼接显示层）。 */
export function reproString(repro: CostView["sheet"]["repro"]): string {
  return `${repro.design_hash} | ${repro.engine_version} | ${repro.data_version}`;
}

/** 单笔明细窄化（九字段逐键——name_zh 在内）。 */
function narrowRow(raw: unknown, index: number): EstimateRowView {
  const face = `detail_rows[${index}]`;
  if (!isRecord(raw)) {
    reject(`${face} 须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const fields = raw["source_field_ids"];
  if (
    !Array.isArray(fields) ||
    fields.length === 0 ||
    !fields.every((f) => typeof f === "string" && f !== "")
  ) {
    reject(`${face}.source_field_ids 须为非空字符串数组（R3 溯源必填）`);
  }
  for (const key of ["quantity", "unit_price", "amount"] as const) {
    if (!isFiniteNumber(raw[key])) {
      reject(`${face}.${key} 须为有限数值：得到 ${JSON.stringify(raw[key]) ?? "undefined"}`);
    }
  }
  return {
    price_key: requireString(raw, "price_key", `${face}.price_key`),
    name_zh: requireString(raw, "name_zh", `${face}.name_zh`),
    unit: requireString(raw, "unit", `${face}.unit`),
    quantity: raw["quantity"] as number,
    unit_price: raw["unit_price"] as number,
    amount: raw["amount"] as number,
    source_field_ids: fields as string[],
    source: requireString(raw, "source", `${face}.source`),
  };
}

/** 单笔费用行窄化（六字段逐键——费率域有限即可，rate∈[0,1] 服务端守卫）。 */
function narrowFeeLine(raw: unknown, bucket: string, index: number): FeeLineView {
  const face = `${bucket}[${index}]`;
  if (!isRecord(raw)) {
    reject(`${face} 须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  for (const key of ["rate", "base_amount", "amount"] as const) {
    if (!isFiniteNumber(raw[key])) {
      reject(`${face}.${key} 须为有限数值：得到 ${JSON.stringify(raw[key]) ?? "undefined"}`);
    }
  }
  return {
    fee_key: requireString(raw, "fee_key", `${face}.fee_key`),
    rate: raw["rate"] as number,
    base: requireString(raw, "base", `${face}.base`),
    base_amount: raw["base_amount"] as number,
    amount: raw["amount"] as number,
    source: requireString(raw, "source", `${face}.source`),
  };
}

/** 指标单项窄化（五键+band 嵌套+status 域门）。 */
function narrowReading(raw: unknown, index: number): IndicatorReadingView {
  const face = `readings[${index}]`;
  if (!isRecord(raw)) {
    reject(`${face} 须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const status = raw["status"];
  if (typeof status !== "string" || !STATUS_DOMAIN.includes(status)) {
    // 指标 status 域={OK,WARN}（core 冻结面）——超域/小写变体拒，防
    // 异常级串直入 IndicatorsCard 语义色映射（§19.3 绿/橙纪律）
    reject(
      `${face}.status 须为 {OK,WARN} 域内字符串：得到 ${JSON.stringify(status) ?? "undefined"}`,
    );
  }
  const value = raw["value"];
  if (!isFiniteNumber(value)) {
    reject(`${face}.value 须为有限数值`);
  }
  const band = raw["band"];
  if (!isRecord(band)) {
    reject(`${face}.band 须为对象（min/max 嵌套）`);
  }
  const min = band["min"];
  const max = band["max"];
  if (!isFiniteNumber(min) || !isFiniteNumber(max) || !(min < max)) {
    reject(`${face}.band.min/max 须为有限数值且 min<max`);
  }
  return {
    indicator_key: requireString(raw, "indicator_key", `${face}.indicator_key`),
    value,
    band: { min, max },
    status,
    reason: requireString(raw, "reason", `${face}.reason`),
  };
}

/**
 * D7 窄化门：/api/cost 弱类型响应 → CostView（逐类逐字段拒）。
 */
export function narrowCostResponse(raw: unknown): CostView {
  if (!isRecord(raw)) {
    reject(`cost 响应须为对象：得到 ${JSON.stringify(raw) ?? "undefined"}`);
  }
  const projectId = requireString(raw, "project_id");
  const conditionKey = requireString(raw, "condition_key");
  const priceVersion = requireString(raw, "price_data_version");
  const designScale = raw["design_scale"];
  if (!isFiniteNumber(designScale)) {
    reject(`design_scale 须为有限数值：得到 ${JSON.stringify(designScale) ?? "undefined"}`);
  }
  const conditionsRaw = requireArray(raw, "conditions");
  if (
    conditionsRaw.length === 0 ||
    !conditionsRaw.every((key) => typeof key === "string" && key !== "")
  ) {
    reject("conditions 须为非空字符串数组（工况索引面——元素空串拒）");
  }
  const sheet = raw["sheet"];
  if (!isRecord(sheet)) {
    reject(`sheet 须为对象：得到 ${JSON.stringify(sheet) ?? "undefined"}`);
  }
  for (const key of SHEET_NUMBER_KEYS) {
    if (!isFiniteNumber(sheet[key])) {
      reject(`sheet.${key} 须为有限数值：得到 ${JSON.stringify(sheet[key]) ?? "undefined"}`);
    }
  }
  const detailRows = requireArray(sheet, "detail_rows").map((entry, index) =>
    narrowRow(entry, index),
  );
  if (detailRows.length === 0) {
    reject("sheet.detail_rows 须为非空数组（空概算属服务端异形）");
  }
  const bucketLines: Record<
    "measure" | "indirect" | "reserve" | "tax",
    FeeLineView[]
  > = {
    measure: requireArray(sheet, "measure").map((entry, index) =>
      narrowFeeLine(entry, "measure", index),
    ),
    indirect: requireArray(sheet, "indirect").map((entry, index) =>
      narrowFeeLine(entry, "indirect", index),
    ),
    reserve: requireArray(sheet, "reserve").map((entry, index) =>
      narrowFeeLine(entry, "reserve", index),
    ),
    tax: requireArray(sheet, "tax").map((entry, index) =>
      narrowFeeLine(entry, "tax", index),
    ),
  };
  const indicators = raw["indicators"];
  if (!isRecord(indicators)) {
    reject(`indicators 须为对象：得到 ${JSON.stringify(indicators) ?? "undefined"}`);
  }
  const checked = indicators["checked"];
  if (typeof checked !== "boolean") {
    reject(`indicators.checked 须为布尔：得到 ${JSON.stringify(checked) ?? "undefined"}`);
  }
  const readings = requireArray(indicators, "readings").map((entry, index) =>
    narrowReading(entry, index),
  );
  return {
    project_id: projectId,
    condition_key: conditionKey,
    conditions: conditionsRaw as string[],
    stale: raw["stale"] === true,
    price_data_version: priceVersion,
    design_scale: designScale,
    sheet: {
      detail_rows: detailRows,
      measure: bucketLines.measure,
      indirect: bucketLines.indirect,
      reserve: bucketLines.reserve,
      tax: bucketLines.tax,
      detail_subtotal: sheet["detail_subtotal"] as number,
      equipment_subtotal: sheet["equipment_subtotal"] as number,
      construction_subtotal: sheet["construction_subtotal"] as number,
      subtotal: sheet["subtotal"] as number,
      reserve_subtotal: sheet["reserve_subtotal"] as number,
      grand_total: sheet["grand_total"] as number,
      repro: narrowRepro(sheet),
      condition_key: requireString(sheet, "condition_key"),
    },
    indicators: { readings, checked },
  };
}

/** 小计行构造（金额原值透传——kind=subtotal 高亮面）。 */
function subtotalRow(key: SubtotalKey, amount: number): EstimateTableRow {
  return {
    key: `subtotal:${key}`,
    kind: "subtotal",
    label: SUBTOTAL_LABELS[key],
    amount,
  };
}

/** 费桶行族构造（桶名+费率透传——行序=桶内服务端序）。 */
function feeRows(bucket: BucketKey, lines: FeeLineView[]): EstimateTableRow[] {
  return lines.map((line) => ({
    key: `fee:${bucket}:${line.fee_key}`,
    kind: "fee" as const,
    label: line.fee_key,
    amount: line.amount,
    rate: line.rate,
    bucket: BUCKET_LABELS[bucket],
  }));
}

/**
 * D5 分级行模型：CostView.sheet → 行序=服务端装配序（零推导——金额原值）。
 */
export function buildTableRows(view: CostView): EstimateTableRow[] {
  const sheet = view.sheet;
  const repro = reproString(sheet.repro);
  return [
    ...sheet.detail_rows.map(
      (row): EstimateTableRow => ({
        key: `detail:${row.price_key}`,
        kind: "detail",
        label: row.name_zh,
        amount: row.amount,
        unit: row.unit,
        quantity: row.quantity,
        unitPrice: row.unit_price,
        trace: {
          price_key: row.price_key,
          source_field_ids: row.source_field_ids,
          unit_price: row.unit_price,
          repro,
        },
      }),
    ),
    subtotalRow("detail_subtotal", sheet.detail_subtotal),
    subtotalRow("equipment_subtotal", sheet.equipment_subtotal),
    ...feeRows("measure", sheet.measure),
    subtotalRow("construction_subtotal", sheet.construction_subtotal),
    ...feeRows("indirect", sheet.indirect),
    subtotalRow("subtotal", sheet.subtotal),
    ...feeRows("reserve", sheet.reserve),
    subtotalRow("reserve_subtotal", sheet.reserve_subtotal),
    ...feeRows("tax", sheet.tax),
    {
      key: "grand:grand_total",
      kind: "grand",
      label: "工程总投资",
      amount: sheet.grand_total,
    },
  ];
}
