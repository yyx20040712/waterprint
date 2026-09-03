/**
 * 投影层纯函数：SceneResponse JSON → 渲染描述对象（组件薄壳的唯一数据源）。
 *
 * 输入:  SceneResponse（/api/scene 响应——orval 生成类型，scene_version 门
 *        在此校验；AUDIT2 FIX1 C-1 契约由 SceneGraph 更名+stale 旗标——
 *        stale 消费归 viewer3dPane 呈现面，投影层零消费零推导维持）
 * 输出:  RenderScene（solids/waters/internals/boundaries 四组渲染描述+root 序
 *        +bounds 全 placements∪红线顶点 AABB——UX2 D5 取景自适应数据锚；
 *        零色值零业务推导）
 *
 * 规格说明（FE1 D4；core scene.py R4 唯一版本读取口；UX2 D5 bounds 聚合；
 *   L5b 总装模式 2026-09-03）：
 *   - SCENE_VERSION 门：非 "waterprint-scene-2/y-up/m" 显式拒（原因附
 *     实际值与期望值——坐标约定/单位漂移前置到投影边界；L5a core 步进
 *     -2=site 摆放+rotation 放行，双端同窗）；
 *   - 六 kind 完备：box/cylinder/plane/extrusion/water_surface/polyline
 *     全映射，未知 kind 显式拒（原因含 kind 与 node_id）；
 *   - instance_count>1 摆置：近方阵（cols=ceil(sqrt(n))、rows=ceil(n/cols)）、
 *     步距=原型图元自身 dims（length→X、width→Z）——类型化摆放
 *     （摆放不计数：计数唯一真源=结果字段，README 硬规则 4）；
 *   - 语义 token 透传（色值归组件层——渲染描述禁出现 color/material）；
 *   - root 序与 nodes 索引一致性：悬空 id 拒；
 *   - 零业务计算/零业务几何推导：只消费 dims/position/rotation/
 *     instance_count/semantic（children v1 平铺不出现——core build_scene
 *     产平表）；
 *   - 变换门（FE1 M1→L5b 收窄）：rotation 放行透传（R3F rotation 属性
 *     直消费弧度——度→弧度换算归 core 装配层，前端零业务几何）；scale
 *     仍拒非默认（门收窄不撤——R3F scale 消费面未开，静默丢弃即失真）；
 *   - 总装红线（L5b）：kind=polyline（semantic="site_boundary"）归
 *     boundaries 组，core 压平顶点键 x{i}/y{i} 按索引序解码为平面点序
 *     （闭合段末点→首点归渲染层补——core 顶点序即权威）。
 */
import type { SceneResponse } from "../../../shared/api/generated/model";

export const RENDER_SCENE_VERSION = "waterprint-scene-2/y-up/m";

const KNOWN_KINDS = new Set([
  "box",
  "cylinder",
  "plane",
  "water_surface",
  "extrusion",
  "polyline",
]);
const WATER_KIND = "water_surface";
const BOUNDARY_KIND = "polyline";

export type Vec3 = [number, number, number];

/** 渲染描述节点（摆置=InstancedMesh 数据前提；dims 逐键透传；rotation 弧度直透传）。 */
export type RenderNode = {
  id: string;
  kind: string;
  semantic: string;
  position: Vec3;
  /** L5b 放行透传（R3F 直消费弧度——core 装配层已换算，投影层零换算）。 */
  rotation: Vec3;
  dims: Record<string, number>;
  instanceCount: number;
  placements: Vec3[];
};

/** 红线渲染描述（平面点序 [x, y] 对——世界 XZ 映射归组件层；闭合段渲染层补）。 */
export type BoundaryNode = {
  id: string;
  semantic: string;
  points: Array<[number, number]>;
};

/** 全 placements∪红线顶点轴对齐包围盒（UX2 D5 取景自适应的数据锚）。 */
export type SceneBounds = {
  min: Vec3;
  max: Vec3;
};

/** 渲染场景（四组+root 序+bounds 聚合——组件按组挂材质/图元策略）。 */
export type RenderScene = {
  sceneVersion: string;
  conditionKey: string;
  root: string[];
  solids: RenderNode[];
  waters: RenderNode[];
  internals: RenderNode[];
  /** 总装红线（L5b：polyline 独立组——池体/水面/构件三组不污染）。 */
  boundaries: BoundaryNode[];
  /** 全 placements∪红线顶点 AABB（空场景=null——机位回退）。 */
  bounds: SceneBounds | null;
};

/** 投影非法（版本漂移/未知 kind/root 悬空/红线顶点不完整）——渲染层显式拒。 */
export class SceneProjectionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SceneProjectionError";
  }
}

function placementsOf(origin: Vec3, count: number, dims: Record<string, number>): Vec3[] {
  if (count <= 1) {
    return [origin];
  }
  const cols = Math.ceil(Math.sqrt(count));
  const stepX = dims["length"] ?? 0; // 步距=原型自身占位（缺键=0 重叠——数据面负责）
  const stepZ = dims["width"] ?? 0;
  const placed: Vec3[] = [];
  for (let index = 0; index < count; index += 1) {
    const column = index % cols;
    const row = Math.floor(index / cols);
    placed.push([origin[0] + column * stepX, origin[1], origin[2] + row * stepZ]);
  }
  return placed;
}

/**
 * 红线顶点序解码（L5b）：core 压平键 x{i}/y{i} 按索引序重建平面点序——
 * 纯格式解码零业务推导；奇偶缺口/杂键=场景图损坏显式拒（顶点数 ≥3 面
 * 由 core validator 把守，本层零重复校验）。
 */
function boundaryPointsOf(nodeId: string, dims: Record<string, number>): Array<[number, number]> {
  const points: Array<[number, number]> = [];
  let index = 0;
  for (;;) {
    const x = dims[`x${index}`];
    const y = dims[`y${index}`];
    if (x === undefined || y === undefined) {
      break;
    }
    points.push([x, y]);
    index += 1;
  }
  if (index === 0 || index * 2 !== Object.keys(dims).length) {
    throw new SceneProjectionError(
      `红线顶点序不完整：节点 ${nodeId} 解码 ${index} 点（压平键 x{i}/y{i} `
        + "奇偶缺口或杂键——core 压平编码损坏，拒绝渲染）",
    );
  }
  return points;
}

/**
 * UX2 D5 bounds 聚合：solids+waters+internals 全 placements∪boundaries 红线
 * 顶点（世界 y=0）的 AABB（取景自适应的数据锚——机位薄壳消费；L5b 起红线
 * 顶点计入（总装取景覆盖红线外框）；空集=null 显式缺省禁伪盒）。
 */
function boundsOfPoints(points: Iterable<Vec3>): SceneBounds | null {
  let min: Vec3 | null = null;
  let max: Vec3 | null = null;
  for (const [x, y, z] of points) {
    if (min === null || max === null) {
      min = [x, y, z];
      max = [x, y, z];
      continue;
    }
    if (x < min[0]) {
      min[0] = x;
    }
    if (y < min[1]) {
      min[1] = y;
    }
    if (z < min[2]) {
      min[2] = z;
    }
    if (x > max[0]) {
      max[0] = x;
    }
    if (y > max[1]) {
      max[1] = y;
    }
    if (z > max[2]) {
      max[2] = z;
    }
  }
  return min !== null && max !== null ? { min, max } : null;
}

export function projectScene(scene: SceneResponse): RenderScene {
  if (scene.scene_version !== RENDER_SCENE_VERSION) {
    throw new SceneProjectionError(
      `场景版本不兼容：${scene.scene_version ?? "(缺失)"}（渲染器唯一支持 `
        + `${RENDER_SCENE_VERSION}——core scene.py R4 坐标/单位约定漂移，拒绝渲染）`,
    );
  }
  const knownIds = new Set(scene.nodes.map((node) => node.node_id));
  for (const id of scene.root) {
    if (!knownIds.has(id)) {
      throw new SceneProjectionError(
        `root 悬空 id：${id} 不在 nodes 索引（场景图损坏——root 序与节点表一致性破坏）`,
      );
    }
  }
  const solids: RenderNode[] = [];
  const waters: RenderNode[] = [];
  const internals: RenderNode[] = [];
  const boundaries: BoundaryNode[] = [];
  for (const node of scene.nodes) {
    const kind = node.primitive.kind;
    if (!KNOWN_KINDS.has(kind)) {
      throw new SceneProjectionError(
        `未知图元 kind：${kind}（节点 ${node.node_id}——合法面 `
          + `${[...KNOWN_KINDS].join("/")}，core pools.py 图元域外）`,
      );
    }
    const position: Vec3 = node.position ?? [0, 0, 0];
    // 变换门（FE1 M1→L5b 收窄）：rotation 放行弧度直透传（R3F 直消费）；
    // scale 仍拒非默认（R3F scale 消费面未开，静默丢弃即失真——原因含
    // 节点 id 与实际值）。
    const rotation: Vec3 = node.rotation ?? [0, 0, 0];
    const scale = node.scale ?? [1, 1, 1];
    if (scale[0] !== 1 || scale[1] !== 1 || scale[2] !== 1) {
      throw new SceneProjectionError(
        `非默认变换拒渲染：节点 ${node.node_id} scale=(${scale.join(",")})`
          + "——R3F scale 消费面未开（core 恒 (1,1,1)），静默丢弃即失真",
      );
    }
    if (kind === BOUNDARY_KIND) {
      boundaries.push({
        id: node.node_id,
        semantic: node.semantic,
        points: boundaryPointsOf(node.node_id, node.primitive.dims),
      });
      continue;
    }
    const instanceCount = node.instance_count ?? 1;
    const rendered: RenderNode = {
      id: node.node_id,
      kind,
      semantic: node.semantic,
      position,
      rotation,
      dims: node.primitive.dims,
      instanceCount,
      placements: placementsOf(position, instanceCount, node.primitive.dims),
    };
    if (kind === WATER_KIND) {
      waters.push(rendered);
    } else if (instanceCount > 1) {
      internals.push(rendered);
    } else {
      solids.push(rendered);
    }
  }
  const boundPoints: Vec3[] = [
    ...[...solids, ...waters, ...internals].flatMap((node) => node.placements),
    ...boundaries.flatMap((boundary) =>
      boundary.points.map(([x, y]): Vec3 => [x, 0, y]),
    ),
  ];
  return {
    sceneVersion: scene.scene_version,
    conditionKey: scene.condition_key,
    root: scene.root,
    solids,
    waters,
    internals,
    boundaries,
    bounds: boundsOfPoints(boundPoints),
  };
}
