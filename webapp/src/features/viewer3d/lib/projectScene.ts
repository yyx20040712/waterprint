/**
 * 投影层纯函数：SceneResponse JSON → 渲染描述对象（组件薄壳的唯一数据源）。
 *
 * 输入:  SceneResponse（/api/scene 响应——orval 生成类型，scene_version 门
 *        在此校验；AUDIT2 FIX1 C-1 契约由 SceneGraph 更名+stale 旗标——
 *        stale 消费归 viewer3dPane 呈现面，投影层零消费零推导维持）
 * 输出:  RenderScene（solids/waters/internals 三组渲染描述+root 序——零色值零业务推导）
 *
 * 规格说明（FE1 D4；core scene.py R4 唯一版本读取口）：
 *   - SCENE_VERSION 门：非 "waterprint-scene-1/y-up/m" 显式拒（原因附
 *     实际值与期望值——坐标约定/单位漂移前置到投影边界）；
 *   - 五 kind 完备：box/cylinder/plane/extrusion/water_surface 全映射，
 *     未知 kind 显式拒（原因含 kind 与 node_id）；
 *   - instance_count>1 摆置：近方阵（cols=ceil(sqrt(n))、rows=ceil(n/cols)）、
 *     步距=原型图元自身 dims（length→X、width→Z）——类型化摆放
 *     （摆放不计数：计数唯一真源=结果字段，README 硬规则 4）；
 *   - 语义 token 透传（色值归组件层——渲染描述禁出现 color/material）；
 *   - root 序与 nodes 索引一致性：悬空 id 拒；
 *   - 零业务计算/零业务几何推导：只消费 dims/position/instance_count/
 *     semantic（children v1 平铺不出现——core build_scene 产平表）；
 *   - 非默认变换显式拒（FE1 M1）：rotation≠(0,0,0)/scale≠(1,1,1) 即
 *     SceneProjectionError（core v1 恒默认值——门先立，勿静默丢勿消费）。
 */
import type { SceneResponse } from "../../../shared/api/generated/model";

export const RENDER_SCENE_VERSION = "waterprint-scene-1/y-up/m";

const KNOWN_KINDS = new Set(["box", "cylinder", "plane", "water_surface", "extrusion"]);
const WATER_KIND = "water_surface";

export type Vec3 = [number, number, number];

/** 渲染描述节点（摆置=InstancedMesh 数据前提；dims 逐键透传）。 */
export type RenderNode = {
  id: string;
  kind: string;
  semantic: string;
  position: Vec3;
  dims: Record<string, number>;
  instanceCount: number;
  placements: Vec3[];
};

/** 渲染场景（三组+root 序——组件按组挂材质/图元策略）。 */
export type RenderScene = {
  sceneVersion: string;
  conditionKey: string;
  root: string[];
  solids: RenderNode[];
  waters: RenderNode[];
  internals: RenderNode[];
};

/** 投影非法（版本漂移/未知 kind/root 悬空）——渲染层显式拒。 */
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
  for (const node of scene.nodes) {
    const kind = node.primitive.kind;
    if (!KNOWN_KINDS.has(kind)) {
      throw new SceneProjectionError(
        `未知图元 kind：${kind}（节点 ${node.node_id}——合法面 `
          + `${[...KNOWN_KINDS].join("/")}，core pools.py 图元域外）`,
      );
    }
    const position: Vec3 = node.position ?? [0, 0, 0];
    // FE1 M1 非默认变换门：v1 渲染器零变换消费（core v1 恒默认值）——
    // 静默丢弃即失真，显式拒（原因含节点 id 与实际值）。
    const rotation = node.rotation ?? [0, 0, 0];
    if (rotation[0] !== 0 || rotation[1] !== 0 || rotation[2] !== 0) {
      throw new SceneProjectionError(
        `非默认变换拒渲染：节点 ${node.node_id} rotation=(${rotation.join(",")})`
          + "——v1 渲染器只支持默认变换（core v1 恒 (0,0,0)），静默丢弃即失真",
      );
    }
    const scale = node.scale ?? [1, 1, 1];
    if (scale[0] !== 1 || scale[1] !== 1 || scale[2] !== 1) {
      throw new SceneProjectionError(
        `非默认变换拒渲染：节点 ${node.node_id} scale=(${scale.join(",")})`
          + "——v1 渲染器只支持默认变换（core v1 恒 (1,1,1)），静默丢弃即失真",
      );
    }
    const instanceCount = node.instance_count ?? 1;
    const rendered: RenderNode = {
      id: node.node_id,
      kind,
      semantic: node.semantic,
      position,
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
  return {
    sceneVersion: scene.scene_version,
    conditionKey: scene.condition_key,
    root: scene.root,
    solids,
    waters,
    internals,
  };
}
