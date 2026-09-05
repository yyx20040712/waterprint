/**
 * 布置编辑器纯函数层：design.site 窄化（D6 轻门）+scene 足迹投影+PUT 载荷
 * +网点/旋转吸附（组件薄壳——几何原语已迁 lib/siteGeometry.ts，SPC2 笔④
 * 顶格减压：OBB 净距/测距/点在多边形族全在 siteGeometry）。
 *
 * 输入:  readProject 弱类型 design 容器（site 键形状门在此收口）+SceneResponse
 *        （GET /api/scene/{project_id} 既有端点——足迹唯一数据源，零新端点）
 * 输出:  narrowSiteDesign 窄化产物/projectSite 渲染模型/withSite PUT 载荷/
 *        snapToGrid/snapRotation（非法形状抛 SiteProjectionError
 *        ——错误消息带键/索引定位，呈现层可反查不白屏）
 *
 * 规格说明（M3 批 L2a，简报 §一预裁决 1/5/6/7——详面见本 feature README；
 *   类型面=core project_schema.py SiteDesign 的 TS 消费面镜像，真源在 core）：
 *   - D6 轻形状门（projectFlow 同构）：structures/roads/corridors/options
 *     逐类逐键形状拒；boundary（L4a 红线）形状门+≥3 点门（core validator
 *     镜像——空=未划界合法）；未知键透传不拒（server strict Pydantic 面是
 *     唯一语义门——gt/min_length 等语义约束零复制）；缺 site 键=全默认态
 *     （core SiteDesign default_factory 同象）；缺 design.nodes → 拒（待摆区面）；
 *   - 足迹（footprint w/h，米）投影自 scene 节点 primitive dims——键解释镜像
 *     viewer3d 渲染器消费面（PoolBox.tsx：box/plane/extrusion 用 length×width
 *     同对键、cylinder 用 diameter 键——同源所见即所得非业务复制）；节点按
 *     node_id 前缀（core scene.py "{unit_id}::{semantic}"）匹配；children
 *     递归聚合包围盒+instance_count>1 近方阵（projectScene placementsOf 同构）；
 *     无水平键图元不计入；scene=null/未命中 → footprint=null（示意矩形归
 *     组件层未计算态渲染，尺寸不出本函数——R3 落盘红线）；
 *   - withSite 结构化替换（withConstraintChoices 同构禁散拼）：仅替换
 *     design.site，其余顶层/design 键原样回传（深层引用相等）；
 *   - snapToGrid：开=round(v/grid)*grid；关=原值；恒 1e-9 舍入防浮尾；
 *     grid 非正数=防御直通。snapRotation：90° 档位（free=true→1° 舍入）
 *     +归一 [0,360)——确定性零随机；
 *   - measureToNearest（SPC2 笔④迁 lib/siteGeometry.ts）：净距=OBB 点-边
 *     枚举精确距（core spacing 同式镜像——编辑辅助非校核裁判，防火间距
 *     校核归 server）；footprint null 者净距=null（不猜）；序=中心距升序、
 *     同距 unitId 字典序；自身排除（防御面）；
 *   - 零运行期库 import（zustand/antd 不进本文件——node 测试直跑）。
 */
import type { Node, SceneResponse } from "../../../shared/api/generated/model";

/** core SitePlanOptions.coord_grid 默认（project_schema.py 同值镜像——测试锚）。 */
export const DEFAULT_COORD_GRID = 10.0;

// ── 类型面（core project_schema.py SiteDesign 的 TS 消费面镜像——真源在 core） ──

/** core SitePoint 镜像（米；X 东 Y 北）。 */
export type SitePoint = { x: number; y: number };

/** core StructurePlacement 镜像（只存变换——R3 轮廓禁落盘）。 */
export type StructurePlacement = {
  x: number;
  y: number;
  rotation: number;
  ground_elevation: number | null;
};

/** core Road 镜像（中心折线+宽度）。 */
export type RoadShape = { centerline: SitePoint[]; width_m: number };

/** core Corridor 镜像（+kind 开放 str——语义面 GR-21 归 core）。 */
export type CorridorShape = { centerline: SitePoint[]; width_m: number; kind: string };

/** core SitePlanOptions 镜像。 */
export type SiteOptionsShape = {
  coord_grid: number;
  wind_rose: Record<string, number> | null;
};

/** core SiteDesign 镜像（narrowSiteDesign 归一产物=PUT 全键面）。 */
export type SiteDesignShape = {
  structures: Record<string, StructurePlacement>;
  roads: RoadShape[];
  corridors: CorridorShape[];
  /** core boundary 镜像（L4a 红线）：空=未划界；非空 ≥3 点闭合顶点序。 */
  boundary: SitePoint[];
  options: SiteOptionsShape;
};

/** 足迹（米）：w=东西 X、h=南北 Y（core SitePoint 惯例）。 */
export type StructureFootprint = { w: number; h: number };

/** 已摆构筑物（渲染/测距消费面——footprint null=未计算示意态）。 */
export type PlacedStructure = {
  unitId: string;
  x: number;
  y: number;
  rotation: number;
  groundElevation: number | null;
  footprint: StructureFootprint | null;
};

/** 投影产物（SiteCanvas/PendingPanel 唯一数据源——组件零推导）。 */
export type SiteModel = {
  /** unitId 字典序（确定性渲染序）。 */
  structures: PlacedStructure[];
  /** design.nodes 全键集（字典序——待摆区=组件层减 draft 编辑键集现算）。 */
  designUnitIds: string[];
  roads: RoadShape[];
  corridors: CorridorShape[];
  options: SiteOptionsShape;
};

/** 投影非法（形状逐类拒/容器异形）——渲染层显式拒（错误薄壳呈现）。 */
export class SiteProjectionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SiteProjectionError";
  }
}

// ── 窄化工具（projectFlow 同构三件+数值字段辅助） ──

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 有限数值判定（bool 排除——typeof boolean 先于 number）。 */
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function reject(message: string): never {
  throw new SiteProjectionError(message);
}

function show(value: unknown): string {
  return JSON.stringify(value) ?? "undefined";
}

/** 有限数值字段窄化（非数/缺键=拒——消息带字段全路径）。 */
function numberField(
  source: Record<string, unknown>,
  key: string,
  path: string,
): number {
  const value = source[key];
  if (!isFiniteNumber(value)) {
    reject(`${path} 须为有限数值：得到 ${show(value)}`);
  }
  return value;
}

function narrowPlacement(raw: unknown, unitId: string): StructurePlacement {
  const path = `design.site.structures[${unitId}]`;
  if (!isRecord(raw)) {
    reject(`${path} 须为对象（x/y/rotation/ground_elevation）：得到 ${show(raw)}`);
  }
  const rotationRaw = raw["rotation"];
  const elevationRaw = raw["ground_elevation"];
  const rotation =
    rotationRaw === undefined ? 0.0 : numberField(raw, "rotation", `${path}.rotation`);
  const ground = elevationRaw === undefined || elevationRaw === null ? null
    : numberField(raw, "ground_elevation", `${path}.ground_elevation`);
  return {
    x: numberField(raw, "x", `${path}.x`),
    y: numberField(raw, "y", `${path}.y`),
    rotation,
    ground_elevation: ground,
  };
}

/** 点窄化（x/y 有限数值——centerline/boundary 共用）。 */
function narrowPoint(raw: unknown, path: string): SitePoint {
  if (!isRecord(raw)) {
    reject(`${path} 须为对象（x/y 米）：得到 ${show(raw)}`);
  }
  return { x: numberField(raw, "x", `${path}.x`), y: numberField(raw, "y", `${path}.y`) };
}

function narrowCenterline(raw: unknown, label: string): SitePoint[] {
  if (!Array.isArray(raw)) {
    reject(`${label}.centerline 须为数组（≥2 点——长度语义门在 server）：得到 ${show(raw)}`);
  }
  return raw.map((point, index) => narrowPoint(point, `${label}.centerline[${index}]`));
}

function narrowRoad(raw: unknown, index: number): RoadShape {
  const label = `design.site.roads[${index}]`;
  if (!isRecord(raw)) {
    reject(`${label} 须为对象（centerline/width_m）：得到 ${show(raw)}`);
  }
  return {
    centerline: narrowCenterline(raw["centerline"], label),
    width_m: numberField(raw, "width_m", `${label}.width_m`),
  };
}

function narrowCorridor(raw: unknown, index: number): CorridorShape {
  const label = `design.site.corridors[${index}]`;
  if (!isRecord(raw)) {
    reject(`${label} 须为对象（centerline/width_m/kind）：得到 ${show(raw)}`);
  }
  const kindRaw = raw["kind"];
  if (typeof kindRaw !== "string") {
    reject(`${label}.kind 须为字符串：得到 ${show(kindRaw)}`);
  }
  return {
    centerline: narrowCenterline(raw["centerline"], label),
    width_m: numberField(raw, "width_m", `${label}.width_m`),
    kind: kindRaw,
  };
}

/** 数组容器窄化（缺省宽容 []；非数组=拒——消息带容器路径）。 */
function narrowList<T>(
  raw: unknown,
  label: string,
  narrow: (element: unknown, index: number) => T,
): T[] {
  if (!Array.isArray(raw)) {
    reject(`${label} 须为数组：得到 ${show(raw)}`);
  }
  return raw.map(narrow);
}

/** design.site 窄化（D6 轻门）：undefined=默认态；逐类拒带定位；未知键透传。 */
export function narrowSiteDesign(raw: unknown): SiteDesignShape {
  if (raw === undefined) {
    return {
      structures: {},
      roads: [],
      corridors: [],
      boundary: [],
      options: { coord_grid: DEFAULT_COORD_GRID, wind_rose: null },
    };
  }
  if (!isRecord(raw)) {
    reject(`design.site 须为对象（缺省=全默认态）：得到 ${show(raw)}`);
  }
  const structures: Record<string, StructurePlacement> = {};
  const structuresRaw = raw["structures"];
  if (structuresRaw !== undefined) {
    if (!isRecord(structuresRaw)) {
      reject(`design.site.structures 须为对象（unit_id→摆放变换）：得到 ${show(structuresRaw)}`);
    }
    for (const [unitId, placement] of Object.entries(structuresRaw)) {
      structures[unitId] = narrowPlacement(placement, unitId);
    }
  }
  const roadsRaw = raw["roads"];
  const roads =
    roadsRaw === undefined ? [] : narrowList(roadsRaw, "design.site.roads", narrowRoad);
  const corridorsRaw = raw["corridors"];
  const corridors =
    corridorsRaw === undefined
      ? []
      : narrowList(corridorsRaw, "design.site.corridors", narrowCorridor);
  // L4a 红线：缺省宽容 []；非数组或 1/2 点=拒（core ≥3 点 validator 镜像——空=未划界合法）
  const boundaryRaw = raw["boundary"];
  let boundary: SitePoint[] = [];
  if (boundaryRaw !== undefined) {
    if (!Array.isArray(boundaryRaw) || boundaryRaw.length === 1 || boundaryRaw.length === 2) {
      reject(`design.site.boundary 须为数组（空或 ≥3 点闭合顶点序）：得到 ${show(boundaryRaw)}`);
    }
    boundary = boundaryRaw.map((point, index) => narrowPoint(point, `design.site.boundary[${index}]`));
  }
  let options: SiteOptionsShape = { coord_grid: DEFAULT_COORD_GRID, wind_rose: null };
  const optionsRaw = raw["options"];
  if (optionsRaw !== undefined) {
    if (!isRecord(optionsRaw)) {
      reject(`design.site.options 须为对象：得到 ${show(optionsRaw)}`);
    }
    const coordRaw = optionsRaw["coord_grid"];
    const windRaw = optionsRaw["wind_rose"];
    let windRose: Record<string, number> | null = null;
    if (windRaw !== undefined && windRaw !== null) {
      if (!isRecord(windRaw)) {
        reject(`design.site.options.wind_rose 须为对象或 null：得到 ${show(windRaw)}`);
      }
      windRose = {};
      for (const [key, value] of Object.entries(windRaw)) {
        windRose[key] = numberField(windRaw, key, `design.site.options.wind_rose[${key}]`);
      }
    }
    options = {
      coord_grid:
        coordRaw === undefined
          ? DEFAULT_COORD_GRID
          : numberField(optionsRaw, "coord_grid", "design.site.options.coord_grid"),
      wind_rose: windRose,
    };
  }
  return { structures, roads, corridors, boundary, options };
}

/** 近方阵摆置（projectScene 同构；L5R N-1：core z-up 平面取 (x,y) 槽——[2]=标高，v1 局部 XY 恒 0 下尺寸不变勘正堵雷）。 */
function placementsOf(
  position: [number, number, number] | undefined,
  count: number,
  dims: Record<string, number>,
): Array<[number, number]> {
  const origin: [number, number] = [position?.[0] ?? 0, position?.[1] ?? 0];
  if (count <= 1) {
    return [origin];
  }
  const cols = Math.ceil(Math.sqrt(count));
  const stepX = dims["length"] ?? 0; // 步距=原型自身占位（缺键=0 重叠——数据面负责）
  const stepZ = dims["width"] ?? 0;
  const placed: Array<[number, number]> = [];
  for (let index = 0; index < count; index += 1) {
    placed.push([
      origin[0] + (index % cols) * stepX,
      origin[1] + Math.floor(index / cols) * stepZ,
    ]);
  }
  return placed;
}

/** 单节点水平占位（w/h 米——键解释镜像 PoolBox；无水平键图元=null 不计入）。 */
function nodeExtent(
  node: Node,
): { w: number; h: number; placements: Array<[number, number]> } | null {
  const dims = node.primitive.dims;
  const kind = node.primitive.kind;
  let w: number | undefined;
  let h: number | undefined;
  if (kind === "box" || kind === "plane" || kind === "extrusion") {
    w = dims["length"]; // PoolBox boxGeometry 同对键（length×width——水平面）
    h = dims["width"];
  } else if (kind === "cylinder") {
    w = dims["diameter"]; // PoolBox cylinderGeometry 键（径向对称）
    h = dims["diameter"];
  } else {
    return null; // water_surface 等：dims 无水平键（level/freeboard）——不计入
  }
  if (!isFiniteNumber(w) || !isFiniteNumber(h)) {
    return null; // 键缺=数据面无此占位（PoolBox ??1 是渲染占位——足迹不猜）
  }
  return { w, h, placements: placementsOf(node.position, node.instance_count ?? 1, dims) };
}

/** children 递归展开（v1 core 产平表——消费面按 schema 容错展开）。 */
function flatten(nodes: readonly Node[]): Node[] {
  const out: Node[] = [];
  for (const node of nodes) {
    out.push(node);
    if (node.children !== undefined && node.children.length > 0) {
      out.push(...flatten(node.children));
    }
  }
  return out;
}

/** 足迹聚合：unit 匹配节点（node_id 前缀）水平占位包围盒；无贡献节点=null。 */
function footprintOfUnit(scene: SceneResponse, unitId: string): StructureFootprint | null {
  let minX = Infinity;
  let maxX = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;
  for (const node of flatten(scene.nodes)) {
    if (!node.node_id.startsWith(`${unitId}::`)) {
      continue; // core scene.py node_id="{unit_id}::{semantic}"——前缀匹配
    }
    const extent = nodeExtent(node);
    if (extent === null) {
      continue;
    }
    for (const [cx, cz] of extent.placements) {
      minX = Math.min(minX, cx - extent.w / 2);
      maxX = Math.max(maxX, cx + extent.w / 2);
      minZ = Math.min(minZ, cz - extent.h / 2);
      maxZ = Math.max(maxZ, cz + extent.h / 2);
    }
  }
  if (minX === Infinity) {
    return null; // 未命中（无水平图元）→ 示意矩形态（组件层渲染——禁落盘）
  }
  return { w: dust(maxX - minX), h: dust(maxZ - minZ) };
}

/** 投影：site+scene+design.nodes → SiteModel（scene 未命中 footprint=null）。 */
export function projectSite(
  design: Record<string, unknown>,
  scene: SceneResponse | null,
): SiteModel {
  const nodesRaw = design["nodes"];
  if (!isRecord(nodesRaw)) {
    reject(
      `design.nodes 须为对象（unit_id→参数 dict——待摆区数据面）：得到 ${show(nodesRaw)}`,
    );
  }
  const site = narrowSiteDesign(design["site"]);
  const unitIds = Object.keys(nodesRaw).sort();
  const structures: PlacedStructure[] = Object.keys(site.structures)
    .sort()
    .map((unitId) => {
      const placement = site.structures[unitId] as StructurePlacement;
      return {
        unitId,
        x: placement.x,
        y: placement.y,
        rotation: placement.rotation,
        groundElevation: placement.ground_elevation,
        footprint: scene === null ? null : footprintOfUnit(scene, unitId),
      };
    });
  return {
    structures,
    designUnitIds: unitIds,
    roads: site.roads,
    corridors: site.corridors,
    options: site.options,
  };
}

/** PUT 载荷：仅替换 design.site，其余原样回传（禁散拼）。 */
export function withSite(
  raw: Record<string, unknown>,
  site: SiteDesignShape,
): Record<string, unknown> {
  const design = raw["design"];
  if (!isRecord(design)) {
    reject(`PUT 载荷构造：原始体 design 须为对象：得到 ${show(design)}`);
  }
  return { ...raw, design: { ...design, site } };
}

/** 1e-9 舍入防浮尾（显示/落盘两面的统一除尘）。 */
function dust(value: number): number {
  return Math.round(value * 1e9) / 1e9;
}

/** 网点吸附：开=round(v/grid)*grid；关=原值；grid 非正数=防御直通。 */
export function snapToGrid(value: number, grid: number, enabled: boolean): number {
  if (!Number.isFinite(value)) {
    return value; // 数据面负责（NaN 透传不掩盖）
  }
  if (enabled && Number.isFinite(grid) && grid > 0) {
    return dust(Math.round(value / grid) * grid);
  }
  return dust(value);
}

/** 旋转吸附：默认 90° 档位；free=true→1° 舍入；归一 [0,360)。 */
export function snapRotation(deg: number, free: boolean): number {
  if (!Number.isFinite(deg)) {
    return deg;
  }
  const raw = free ? Math.round(deg) : Math.round(deg / 90) * 90;
  return ((raw % 360) + 360) % 360;
}
