/**
 * 投影层纯函数：SceneResponse JSON → 渲染描述对象（组件薄壳的唯一数据源）。
 *
 * 输入:  SceneResponse（/api/scene 响应——orval 生成类型，scene_version 门
 *        在此校验；AUDIT2 FIX1 C-1 契约由 SceneGraph 更名+stale 旗标——
 *        stale 消费归 viewer3dPane 呈现面，投影层零消费零推导维持）
 * 输出:  RenderScene（solids/waters/internals/boundaries/routes 五组渲染
 *        描述+root 序+bounds 全 placements∪红线∪条带角点 AABB——UX2 D5
 *        取景自适应数据锚；零色值零业务推导）
 *
 * 规格说明（FE1 D4；core scene.py R4 唯一版本读取口；UX2 D5 bounds 聚合；
 *   L5b 总装模式 2026-09-03；L5R 换轴收编 G1-01 同窗；L6 条带 2026-09-04）：
 *   - SCENE_VERSION 门：非 "waterprint-scene-4/z-up/m" 显式拒（原因附
 *     实际值与期望值——坐标约定/单位漂移前置到投影边界；L7 core 步进
 *     -4=AAO 容积法池体图元入场景（新单元产图元=语义变即步进），双端
 *     同窗；L6 -3=roads/corridors strip 图元收编；L5R 轴标签就地勘正
 *     ——存储恒 z-up，步进时误记 y-up 系 G1-01 根因）；
 *   - 换轴（L5R 唯一换轴点）：core 场景图存储 Z-up（X 东 Y 北 Z 标高
 *     ——DXF/IFC/SitePoint 同族），three 渲染 Y-up（X 东 Y 上 Z 南）；
 *     position 保手性映射 (x, z, −y)（det=+1——平面旋转角不变；镜像
 *     [x,z,y] 会使 rz 视觉反向，A 二审矩阵+数值实证弃用）；rotation
 *     (0,0,rz)→(0,rz,0)（绕世界竖轴——rx/ry 非零=core 契约漂移显式拒）；
 *     红线/条带平面点 y→世界 z 取负；bounds 同源换算。组件层零轴知识；
 *   - 七 kind 完备：box/cylinder/plane/extrusion/water_surface/polyline/
 *     strip 全映射，未知 kind 显式拒（原因含 kind 与 node_id）；
 *   - instance_count>1 摆置：近方阵（cols=ceil(sqrt(n))、rows=ceil(n/cols)）、
 *     步距=原型图元自身 dims（length→X、width→Z）——类型化摆放
 *     （摆放不计数：计数唯一真源=结果字段，README 硬规则 4）；
 *   - 语义 token 透传（色值归组件层——渲染描述禁出现 color/material）；
 *   - root 序与 nodes 索引一致性：悬空 id 拒；
 *   - 零业务计算/零业务几何推导：只消费 dims/position/rotation/
 *     instance_count/semantic（children v1 平铺不出现——core build_scene
 *     产平表）；条带角点 core 预计算直解码（宽度消费归 core）；
 *   - 变换门（FE1 M1→L5b 收窄→L5R 单轴收编）：rotation 仅放行平面旋转
 *     rz（core 契约恒 (0,0,rz)——rz→three Y 轴透传，rx/ry 非零拒）；
 *     scale 仍拒非默认（门收窄不撤——R3F scale 消费面未开，静默丢弃
 *     即失真）；
 *   - 总装红线（L5b）：kind=polyline（semantic="site_boundary"）归
 *     boundaries 组，core 压平顶点键 x{i}/y{i} 按索引序解码并换轴为
 *     世界水平面点（闭合段末点→首点归渲染层补——core 顶点序即权威）；
 *   - 条带图元（L6）：kind=strip（semantic=site_road / site_corridor:{kind}）
 *     归 routes 第五组，core 压平角点键 x{i}/y{i} 按索引序解码并换轴为
 *     世界水平面点（每 4 点一段环序四边形，段数=点数/4——角点 core
 *     _strip_node 预计算）；全部角点计入 bounds（取景覆盖）。
 */
import type { SceneResponse } from "../../../shared/api/generated/model";

export const RENDER_SCENE_VERSION = "waterprint-scene-5/z-up/m";

const KNOWN_KINDS = new Set([
  "box",
  "cylinder",
  "plane",
  "water_surface",
  "extrusion",
  "polyline",
  "strip",
]);
const WATER_KIND = "water_surface";
const BOUNDARY_KIND = "polyline";
const STRIP_KIND = "strip";

export type Vec3 = [number, number, number];

/** 渲染描述节点（摆置=InstancedMesh 数据前提；dims 逐键透传；rotation=three Y 轴弧度）。 */
export type RenderNode = {
  id: string;
  kind: string;
  semantic: string;
  position: Vec3;
  /** L5R 换轴后形态 (0, rz, 0)——绕世界竖轴（Y-up），core (0,0,rz) 契约换算。 */
  rotation: Vec3;
  dims: Record<string, number>;
  instanceCount: number;
  placements: Vec3[];
};

/** 红线渲染描述（世界水平面点序 [x, z] 对——L5R 换轴后坐标，z=−core_y；
 *  贴地微抬归组件层；闭合段渲染层补）。 */
export type BoundaryNode = {
  id: string;
  semantic: string;
  points: Array<[number, number]>;
};

/** 条带渲染描述（L6）：世界水平面角点序 [x, z]——每 4 点一段环序四边形
 *  （段数=points.length/4，角点 core _strip_node 预计算并已在投影层解码
 *  换轴，z=−core_y）；liftY 分层抬升可选（缺省归组件层本地常量）。 */
export type RouteNode = {
  node_id: string;
  semantic: string;
  points: ReadonlyArray<[number, number]>;
  liftY?: number;
};

/** 全 placements∪红线顶点轴对齐包围盒（UX2 D5 取景自适应的数据锚）。 */
export type SceneBounds = {
  min: Vec3;
  max: Vec3;
};

/** 渲染场景（五组+root 序+bounds 聚合——组件按组挂材质/图元策略）。 */
export type RenderScene = {
  sceneVersion: string;
  conditionKey: string;
  root: string[];
  solids: RenderNode[];
  waters: RenderNode[];
  internals: RenderNode[];
  /** 总装红线（L5b：polyline 独立组——池体/水面/构件三组不污染）。 */
  boundaries: BoundaryNode[];
  /** 道路/走廊条带（L6：strip 第五组——roads/corridors 双 semantic 平铺）。 */
  routes: RouteNode[];
  /** 全 placements∪红线顶点 AABB（空场景=null——机位回退）。 */
  bounds: SceneBounds | null;
};

/** 投影非法（版本漂移/未知 kind/root 悬空/红线顶点不完整/条带角点不完整）
 *  ——渲染层显式拒。 */
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
 * 红线顶点序解码+换轴（L5b/L5R）：core 压平键 x{i}/y{i} 按索引序重建
 * 平面点序并换轴为世界水平面坐标 [x, z=−y]（北=−Z）——纯格式解码+唯一
 * 换轴点换算零业务推导；奇偶缺口/杂键=场景图损坏显式拒（顶点数 ≥3 面
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
    const north = -y; // 北→−Z（L5R 换轴；−0 归一同 position 面）
    points.push([x, north === 0 ? 0 : north]);
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
 * 条带角点序解码+换轴（L6，沿 boundaryPointsOf 同款）：core 压平键
 * x{i}/y{i} 按索引序重建并换轴为世界水平面坐标 [x, z=−y]（北=−Z）——
 * 每段 4 角点环序（段数=点数/4，core strip 装配预计算角点——本层零
 * 业务几何）；奇偶缺口/杂键/顶点数非 4 倍数/零点=场景图损坏显式拒。
 */
function stripPointsOf(nodeId: string, dims: Record<string, number>): ReadonlyArray<[number, number]> {
  const points: Array<[number, number]> = [];
  let index = 0;
  for (;;) {
    const x = dims[`x${index}`];
    const y = dims[`y${index}`];
    if (x === undefined || y === undefined) {
      break;
    }
    const north = -y; // 北→−Z（L5R 换轴；−0 归一同 position 面）
    points.push([x, north === 0 ? 0 : north]);
    index += 1;
  }
  if (index === 0 || index % 4 !== 0 || index * 2 !== Object.keys(dims).length) {
    throw new SceneProjectionError(
      `条带角点序不完整：节点 ${nodeId} 解码 ${index} 点（压平键 x{i}/y{i} `
        + "奇偶缺口/杂键或顶点数非 4 倍数——core strip 压平编码损坏，拒绝渲染）",
    );
  }
  return points;
}

/**
 * UX2 D5 bounds 聚合：solids+waters+internals 全 placements∪boundaries 红线
 * 顶点∪routes 条带角点（世界 y=0）的 AABB（取景自适应的数据锚——机位薄壳
 * 消费；L5b 起红线顶点计入、L6 起条带角点计入（总装取景覆盖红线/条带
 * 外框）；空集=null 显式缺省禁伪盒）。
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
  const routes: RouteNode[] = [];
  for (const node of scene.nodes) {
    const kind = node.primitive.kind;
    if (!KNOWN_KINDS.has(kind)) {
      throw new SceneProjectionError(
        `未知图元 kind：${kind}（节点 ${node.node_id}——合法面 `
          + `${[...KNOWN_KINDS].join("/")}，core pools.py 图元域外）`,
      );
    }
    // 换轴（L5R 唯一换轴点）：core Z-up（X 东 Y 北 Z 标高）→ three Y-up
    // （X 东 Y 上 Z 南）——保手性映射 (x, z, −y)：det=+1 平面旋转角不变
    // （镜像 [x,z,y] 会使 rz 视觉反向，A 二审实算弃用）。北分量取负后
    // −0 归一 +0（JS 取负零 Artifact——Object.is/序列化面区分，渲染等价）。
    const source = node.position ?? [0, 0, 0];
    const north = -source[1];
    const position: Vec3 = [source[0], source[2], north === 0 ? 0 : north];
    // 变换门（FE1 M1→L5b→L5R 单轴收编）：core 契约 rotation 恒 (0,0,rz)
    // （平面旋转——rz=绕世界竖轴）→ three Y 轴透传 (0, rz, 0)；rx/ry 非零
    // =core 契约漂移显式拒（放行即三维轴语义不明——静默丢弃更失真）；
    // scale 仍拒非默认（R3F scale 消费面未开）。
    const sourceRotation = node.rotation ?? [0, 0, 0];
    if (sourceRotation[0] !== 0 || sourceRotation[1] !== 0) {
      throw new SceneProjectionError(
        `非平面旋转拒渲染：节点 ${node.node_id} rotation=(${sourceRotation.join(",")})`
          + "——core 契约恒 (0,0,rz)（平面旋转），rx/ry 非零=场景图契约漂移",
      );
    }
    const rotation: Vec3 = [0, sourceRotation[2], 0];
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
    if (kind === STRIP_KIND) {
      routes.push({
        node_id: node.node_id,
        semantic: node.semantic,
        points: stripPointsOf(node.node_id, node.primitive.dims),
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
      boundary.points.map(([x, z]): Vec3 => [x, 0, z]),
    ),
    ...routes.flatMap((route) =>
      route.points.map(([x, z]): Vec3 => [x, 0, z]),
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
    routes,
    bounds: boundsOfPoints(boundPoints),
  };
}
