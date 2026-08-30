/**
 * DXF→SVG 场景投影层（纯函数，Ruling B 前端渲染路径核心）：dxf-parser
 * 解析产物 → 渲染模型（write_dxf 六 kind 翻译面恒覆盖，未知实体不解不炸）。
 *
 * 输入:  DXF 文本字符串（导出 blob.text() 产物——useExportDxf 成功面喂入）
 * 输出:  projectDxf→SvgScene{width,height,items}（path/text/solid 三类
 *        渲染模型——DxfSvg 薄壳消费）；解析抛错（含空串/残件）包
 *        DxfSceneError（中文消息含原始 error.message）
 *
 * 规格说明（B 批 D2；签名冻结——简报 §三逐字）：
 *   - 坐标系：DXF Y 向上/SVG Y 向下——y'=maxY−y 顶翻；extents=全部图元
 *     min/max+两侧 5% 边距（显示层常量）；x'=x−minX+5%·spanX；
 *   - 展开：LWPOLYLINE→path（逐点折线）；TEXT→text（startPoint/textHeight/
 *     text——高度字段实锚 textHeight）；DIMENSION→按 block 名进 blocks
 *     展开匿名块（LINE→path/MTEXT→text[position/height]/INSERT→目标块
 *     SOLID 四点施变换 p'=position+R(rotation°)·(scale·v)→solid/POINT 跳过
 *     ——辅助点非图面）；其余实体类型跳过（诚实面：未知不解不炸）；
 *   - 图层色=layer 表 colorIndex 经 ACI 1-7 显示层常量映射（7→#303030
 *     白线浅底不可见深灰适配）；表缺层/无 colorIndex/值域外→#6b6b6b 兜底；
 *   - 文字尺寸=max(dxf 高度, 图幅跨度/60)（几何线稿 1:1、文字按图幅放大
 *     ——可读性显示层裁量）；线型 v1 恒实线（dxf-parser 线型表 DASHED
 *     缺失=解析器局限，E 冻结 §三——诚实注记不遮蔽）；
 *   - 退化防御：空实体/零跨度→对应维 1（不除零不炸）；
 *   - 禁止事项：零 antd/除 dxf-parser 外零运行期库；解析产物一律 unknown
 *     窄化（禁 any——运行期 tables 可缺[mini fixture 实证]，.d.ts 必有性
 *     不可信）；node 环境可测（drawingsView 同族纯函数面）。
 */
import DxfParser from "dxf-parser";

/** 折线渲染模型（LWPOLYLINE/块内 LINE）。 */
export type SvgPathItem = { kind: "path"; d: string; color: string };

/** 文字渲染模型（TEXT/MTEXT——色恒深灰见 D8，模型不带色字段）。 */
export type SvgTextItem = {
  kind: "text";
  x: number;
  y: number;
  text: string;
  fontSize: number;
};

/** 填充多边形渲染模型（INSERT→箭头块 SOLID）。 */
export type SvgSolidItem = { kind: "solid"; points: string; color: string };

export type SvgItem = SvgPathItem | SvgTextItem | SvgSolidItem;

/** 场景模型（viewBox 尺寸+图元清单——DxfSvg 唯一数据源）。 */
export type SvgScene = { width: number; height: number; items: SvgItem[] };

/** 投影失败（解析抛错/残件——消费面 sceneError 降级注记）。 */
export class DxfSceneError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DxfSceneError";
  }
}

/** 边距比例（显示层常量：两侧各 5% 图幅——简报 D2 ④）。 */
const MARGIN_RATIO = 0.05;

/** 文字可读性放大分母（图幅跨度/60——显示层裁量，README 注记）。 */
const FONT_SPAN_DIVISOR = 60;

/** ACI 1-7 显示层常量映射（7→深灰：白线浅底不可见适配——简报 D2 ⑤）。 */
const ACI_COLORS: Readonly<Record<number, string>> = {
  1: "#ff0000",
  2: "#ffff00",
  3: "#00ff00",
  4: "#00ffff",
  5: "#0000ff",
  6: "#ff00ff",
  7: "#303030",
};

/** 缺层/值域外中性兜底色。 */
const FALLBACK_COLOR = "#6b6b6b";

/** 度→弧度（INSERT rotation 单位换算——dxf-parser 产度数）。 */
const DEG_TO_RAD = Math.PI / 180;

/** 中间几何（归一前原始 DXF 坐标——extents 两阶段必需）。 */
type RawPath = { kind: "path"; pts: { x: number; y: number }[]; color: string };
type RawText = { kind: "text"; x: number; y: number; text: string; height: number };
type RawSolid = { kind: "solid"; pts: { x: number; y: number }[]; color: string };
type RawItem = RawPath | RawText | RawSolid;

/** 窄化工具：plain object（非 null 非数组——isRecord 先例同款）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 窄化工具：有限数值（NaN/Infinity 拒——防坐标污染 extents）。 */
function readNum(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : null;
}

/** 窄化工具：{x,y} 点（缺一/非有限即 null）。 */
function readPoint(value: unknown): { x: number; y: number } | null {
  if (!isRecord(value)) {
    return null;
  }
  const x = readNum(value["x"]);
  const y = readNum(value["y"]);
  return x === null || y === null ? null : { x, y };
}

/** 窄化工具：点列（逐点窄化，坏点整列拒）。 */
function readPoints(value: unknown): { x: number; y: number }[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  const pts: { x: number; y: number }[] = [];
  for (const raw of value) {
    const pt = readPoint(raw);
    if (pt === null) {
      return null;
    }
    pts.push(pt);
  }
  return pts;
}

/** 图层色：layer 表 colorIndex 经 ACI 1-7 映射，缺层/值域外兜底。 */
function layerColor(layerTable: unknown, layerName: unknown): string {
  if (!isRecord(layerTable) || typeof layerName !== "string") {
    return FALLBACK_COLOR;
  }
  const entry = layerTable[layerName];
  if (!isRecord(entry)) {
    return FALLBACK_COLOR;
  }
  const idx = readNum(entry["colorIndex"]);
  if (idx === null || !Number.isInteger(idx)) {
    return FALLBACK_COLOR;
  }
  return ACI_COLORS[idx] ?? FALLBACK_COLOR;
}

/** INSERT 点变换：p'=position+R(rotation°)·(scale·v)。 */
function transformPoint(
  vertex: { x: number; y: number },
  insert: Record<string, unknown>,
): { x: number; y: number } | null {
  const position = readPoint(insert["position"]);
  if (position === null) {
    return null;
  }
  const xScale = readNum(insert["xScale"]) ?? 1;
  const yScale = readNum(insert["yScale"]) ?? 1;
  const rotationDeg = readNum(insert["rotation"]) ?? 0;
  const rad = rotationDeg * DEG_TO_RAD;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const lx = vertex.x * xScale;
  const ly = vertex.y * yScale;
  return {
    x: position.x + lx * cos - ly * sin,
    y: position.y + lx * sin + ly * cos,
  };
}

/** 匿名块内 INSERT→目标块 SOLID 展开为 raw solid（其余块内类型跳过）。 */
function expandInsert(
  insert: Record<string, unknown>,
  blocks: unknown,
  layerTable: unknown,
): RawSolid[] {
  const name = insert["name"];
  if (!isRecord(blocks) || typeof name !== "string") {
    return [];
  }
  const target = blocks[name];
  if (!isRecord(target)) {
    return [];
  }
  const entities = target["entities"];
  if (!Array.isArray(entities)) {
    return [];
  }
  const color = layerColor(layerTable, insert["layer"]);
  const solids: RawSolid[] = [];
  for (const entity of entities) {
    if (!isRecord(entity) || entity["type"] !== "SOLID") {
      continue;
    }
    const pts = readPoints(entity["points"]);
    if (pts === null || pts.length < 3) {
      continue;
    }
    const transformed: { x: number; y: number }[] = [];
    for (const vertex of pts) {
      const moved = transformPoint(vertex, insert);
      if (moved === null) {
        transformed.length = 0;
        break;
      }
      transformed.push(moved);
    }
    if (transformed.length === pts.length) {
      solids.push({ kind: "solid", pts: transformed, color });
    }
  }
  return solids;
}

/** DIMENSION→匿名块展开（LINE/MTEXT/INSERT 产项，POINT 与未知跳过）。 */
function expandDimension(
  dimension: Record<string, unknown>,
  blocks: unknown,
  layerTable: unknown,
): RawItem[] {
  const blockName = dimension["block"];
  if (!isRecord(blocks) || typeof blockName !== "string") {
    return [];
  }
  const block = blocks[blockName];
  if (!isRecord(block)) {
    return [];
  }
  const entities = block["entities"];
  if (!Array.isArray(entities)) {
    return [];
  }
  const items: RawItem[] = [];
  for (const entity of entities) {
    if (!isRecord(entity)) {
      continue;
    }
    const layer = entity["layer"];
    if (entity["type"] === "LINE") {
      const pts = readPoints(entity["vertices"]);
      if (pts !== null && pts.length >= 2) {
        items.push({ kind: "path", pts, color: layerColor(layerTable, layer) });
      }
      continue;
    }
    if (entity["type"] === "MTEXT") {
      const position = readPoint(entity["position"]);
      const height = readNum(entity["height"]);
      const text = entity["text"];
      if (position !== null && height !== null && typeof text === "string") {
        items.push({
          kind: "text",
          x: position.x,
          y: position.y,
          text,
          height,
        });
      }
      continue;
    }
    if (entity["type"] === "INSERT") {
      items.push(...expandInsert(entity, blocks, layerTable));
    }
    // POINT（辅助点非图面）与其余类型跳过——未知不解不炸
  }
  return items;
}

/**
 * DXF 文本→SVG 场景模型（解析→实体展开→extents 归一三阶段纯函数）。
 */
export function projectDxf(raw: string): SvgScene {
  let dxf: unknown;
  try {
    dxf = new DxfParser().parseSync(raw);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new DxfSceneError(`DXF 解析失败：${detail}`);
  }
  if (!isRecord(dxf)) {
    // parseSync 类型签名 IDxf|null——null/异形产物防御（字符串输入常态不触发）
    throw new DxfSceneError("DXF 解析失败：解析器返回空产物");
  }
  const layerTable = unwrapLayerTable(dxf["tables"]);
  const blocks = isRecord(dxf["blocks"]) ? dxf["blocks"] : null;
  const entities = Array.isArray(dxf["entities"]) ? dxf["entities"] : [];

  // 阶段一：原始坐标展开（顶层实体——LWPOLYLINE/TEXT/DIMENSION，其余跳过）
  const rawItems: RawItem[] = [];
  for (const entity of entities) {
    if (!isRecord(entity)) {
      continue;
    }
    const layer = entity["layer"];
    if (entity["type"] === "LWPOLYLINE") {
      const pts = readPoints(entity["vertices"]);
      if (pts !== null && pts.length >= 2) {
        rawItems.push({ kind: "path", pts, color: layerColor(layerTable, layer) });
      }
      continue;
    }
    if (entity["type"] === "TEXT") {
      const start = readPoint(entity["startPoint"]);
      const height = readNum(entity["textHeight"]); // TEXT 高度字段实锚 textHeight
      const text = entity["text"];
      if (start !== null && height !== null && typeof text === "string") {
        rawItems.push({
          kind: "text",
          x: start.x,
          y: start.y,
          text,
          height,
        });
      }
      continue;
    }
    if (entity["type"] === "DIMENSION" && blocks !== null) {
      rawItems.push(...expandDimension(entity, blocks, layerTable));
    }
    // 其余实体类型跳过（write_dxf 六 kind 翻译面恒被覆盖，未知不解不炸）
  }
  if (rawItems.length === 0) {
    return { width: 1, height: 1, items: [] };
  }

  // 阶段二：extents（全部图元 min/max——空实体已在上方早退）
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const item of rawItems) {
    if (item.kind === "text") {
      minX = Math.min(minX, item.x);
      maxX = Math.max(maxX, item.x);
      minY = Math.min(minY, item.y);
      maxY = Math.max(maxY, item.y);
      continue;
    }
    for (const pt of item.pts) {
      minX = Math.min(minX, pt.x);
      maxX = Math.max(maxX, pt.x);
      minY = Math.min(minY, pt.y);
      maxY = Math.max(maxY, pt.y);
    }
  }
  const spanX = maxX - minX;
  const spanY = maxY - minY;
  const padX = spanX > 0 ? spanX * MARGIN_RATIO : 0;
  const padY = spanY > 0 ? spanY * MARGIN_RATIO : 0;
  // 跨度+两侧边距（span·(1+2·margin) 等价式——加法形态浮点尾差更稳）
  const width = spanX > 0 ? spanX + 2 * padX : 1;
  const height = spanY > 0 ? spanY + 2 * padY : 1;
  const fontSizeBase = Math.max(spanX, spanY) / FONT_SPAN_DIVISOR;

  // 阶段三：归一映射（Y 顶翻 y'=maxY−y+padY；文字尺寸可读性放大）
  const nx = (x: number): number => x - minX + padX;
  const ny = (y: number): number => maxY - y + padY;
  const items: SvgItem[] = rawItems.map((item): SvgItem => {
    if (item.kind === "text") {
      return {
        kind: "text",
        x: nx(item.x),
        y: ny(item.y),
        text: item.text,
        fontSize: Math.max(item.height, fontSizeBase),
      };
    }
    if (item.kind === "path") {
      const head = item.pts[0];
      if (head === undefined) {
        // 不可达防御（收集面已滤空折线）——窄化必经，无占位语义
        throw new DxfSceneError("DXF 解析失败：折线顶点缺失");
      }
      const d = [
        `M ${nx(head.x)},${ny(head.y)}`,
        ...item.pts.slice(1).map((pt) => `L ${nx(pt.x)},${ny(pt.y)}`),
      ].join(" ");
      return { kind: "path", d, color: item.color };
    }
    return {
      kind: "solid",
      points: item.pts.map((pt) => `${nx(pt.x)},${ny(pt.y)}`).join(" "),
      color: item.color,
    };
  });
  return { width, height, items };
}

/** tables.layer.layers 解包（运行期可缺——mini fixture 实证 tables=undefined）。 */
function unwrapLayerTable(tables: unknown): unknown {
  if (!isRecord(tables)) {
    return null;
  }
  const layer = tables["layer"];
  if (!isRecord(layer)) {
    return null;
  }
  return layer["layers"] ?? null;
}
