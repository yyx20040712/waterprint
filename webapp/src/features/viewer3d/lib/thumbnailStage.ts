/**
 * 节点 3D 缩略图纯函数层（C2-thumb V1/V2——task-C2-thumb-plan.md）。
 *
 * 输入:  RenderScene solids/internals（projectScene 投影产出——与
 *        Scene.tsx 同函数同数据）+projectId/conditionKey/sceneVersion
 * 输出:  单元构型分组（unit:: 前缀）/单元自身 AABB/取景机位派生（iso
 *        俯角 30/距离=对角线×1.25——C2-3d V4 冻结系数复用）/缓存键/
 *        半剖切面（C2-visual T1 纵向对角剖）
 *
 * 规格说明（C2 二期第六子面 2026-09-11——在册推荐案 R3F 离屏 sprite）：
 *   - 单元构型=按 RenderNode.id 首段分组（`{unit_id}::{part}` 形态
 *     ——scene API 实锚；一单元可多构型件[浓缩池 pool_wall+channel]
 *     全收+`pipe::` 场景级件排除；waters 不入[呈裁③ 推荐——96px 小图
 *     半透明水面成噪点]）；
 *   - AABB 近似=placement 中心±kind 半尺寸（box/plane=length×width 水平
 *     半幅+depth 竖半高/cylinder=diameter 圆外接方半幅——保守外接：取景
 *     距离按外接盒派生必含构型，无需精确几何）；
 *   - 取景=C2-3d V4 冻结口径（iso 俯角 30[方向向量 (30,30,30) 同值]/
 *     距离=单元对角线×1.25/fov 50）——系数/方向与 Scene.tsx 常量同值
 *     双源注记（改取景须两处联动——R-G3 清单同族）；
 *   - 缓存键=projectId+conditionKey+sceneVersion（在册「缓存键=unit_id」
 *     =Map 内层键语义——场景变（任一组成变）整批失效重渲）。
 */
import type { RenderNode, RenderScene, Vec3 } from "./projectScene";

/** 单元构型组（unit_id=design.nodes 键——`unit::` 前缀剥除）。 */
export type UnitConstructs = ReadonlyMap<string, readonly RenderNode[]>;

/** C2-3d V4 取景冻结值（Scene.tsx CAMERA_PRESETS.iso 同值双源）。30=方向
 * 分量值非俯角（(30,30,30) 与水平面夹角≈35.26°——GD-N-06 措辞澄清：
 * 与 Scene.tsx 逐分量同值即取景同源，改取景须两处联动）。 */
const ISO_DIRECTION: readonly [number, number, number] = [30, 30, 30];
const DISTANCE_FACTOR = 1.25;

/** 按单元分组构型（solids+internals 全收；waters 不入本组——改经
 * groupUnitWaters 独立分组[C2-visual T2 呈裁③ 复核推翻原「噪点」判断]）。
 * 判据=node_id 首段（`{unit_id}::{part}` 形态
 * ——scene API 实锚 2026-09-11：单元构型件=municipal_aao::pool_wall 等；
 * `pipe::` 场景级件排除）。
 * C2-visual T2（呈裁③ 复核推翻）：waters 改入缩略图（半剖语境水面成
 * 剖面语义可辨非噪点）——独立分组函数 groupUnitWaters（`{unit}::
 * water_surface` 形态[core pools.py water_surface_node 实锚]，渲染层
 * WaterSurface 半透明材质承载——本函数仍零材质判断）。 */
export function groupUnitConstructs(scene: RenderScene): UnitConstructs {
  const groups = new Map<string, RenderNode[]>();
  for (const node of [...scene.solids, ...scene.internals]) {
    const sep = node.id.indexOf("::");
    if (sep <= 0) {
      continue; // 裸 id/空首段不属单元构型（防御位——现载荷全带 ::）
    }
    const unitId = node.id.slice(0, sep);
    if (unitId === "pipe") {
      continue; // 管廊场景级件（C2-3d V5）不属单元构型
    }
    const bucket = groups.get(unitId);
    if (bucket === undefined) {
      groups.set(unitId, [node]);
    } else {
      bucket.push(node);
    }
  }
  return groups;
}

/** 按单元分组水面（C2-visual T2——`{unit}::water_surface` 形态独立分组；
 * solids/internals 不入，pipe 无水面天然排除。分组判据=node_id 首段
 * [依赖 waters 组契约=仅 water_surface 件——GV-05 R 轮口径记档；未来
 * waters 组扩件类时此处静默混入，扩类先复核本函数]）。 */
export function groupUnitWaters(scene: RenderScene): UnitConstructs {
  const groups = new Map<string, RenderNode[]>();
  for (const node of scene.waters) {
    const sep = node.id.indexOf("::");
    if (sep <= 0) {
      continue;
    }
    const unitId = node.id.slice(0, sep);
    const bucket = groups.get(unitId);
    if (bucket === undefined) {
      groups.set(unitId, [node]);
    } else {
      bucket.push(node);
    }
  }
  return groups;
}

/** kind 半尺寸近似（AABB 外接保守幅——box/plane/cylinder/extrusion 四 kind）。 */
function halfExtents(node: RenderNode): Vec3 {
  const length = node.dims["length"] ?? 1;
  const width = node.dims["width"] ?? 1;
  const depth = node.dims["depth"] ?? 1;
  const diameter = node.dims["diameter"] ?? 0;
  if (diameter > 0) {
    const half = diameter / 2;
    return [half, depth / 2, half];
  }
  return [length / 2, depth / 2, width / 2];
}

/** 单元构型 AABB（placements∪dims 外接——全组节点合并）。 */
export function unitBounds(nodes: readonly RenderNode[]): {
  min: Vec3;
  max: Vec3;
} | null {
  let min: Vec3 | null = null;
  let max: Vec3 | null = null;
  for (const node of nodes) {
    const half = halfExtents(node);
    for (const placement of node.placements) {
      const lo: Vec3 = [
        placement[0] - half[0],
        placement[1] - half[1],
        placement[2] - half[2],
      ];
      const hi: Vec3 = [
        placement[0] + half[0],
        placement[1] + half[1],
        placement[2] + half[2],
      ];
      if (min === null || max === null) {
        min = lo;
        max = hi;
        continue;
      }
      min = [
        Math.min(min[0], lo[0]),
        Math.min(min[1], lo[1]),
        Math.min(min[2], lo[2]),
      ];
      max = [
        Math.max(max[0], hi[0]),
        Math.max(max[1], hi[1]),
        Math.max(max[2], hi[2]),
      ];
    }
  }
  if (min === null || max === null) {
    return null; // 无摆置构型（InstancedMesh 数据前提缺失——不渲缩略图）
  }
  return { min, max };
}

/** 缩略图机位（V4 口径派生：iso 方向分量归一×对角线×1.25+AABB 中心）。 */
export function thumbCamera(bounds: { min: Vec3; max: Vec3 }): {
  center: Vec3;
  position: Vec3;
} {
  const center: Vec3 = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
  const length = Math.hypot(ISO_DIRECTION[0], ISO_DIRECTION[1], ISO_DIRECTION[2]);
  const diagonal = Math.hypot(
    bounds.max[0] - bounds.min[0],
    bounds.max[1] - bounds.min[1],
    bounds.max[2] - bounds.min[2],
  );
  const distance = Math.max(diagonal * DISTANCE_FACTOR, 4);
  return {
    center,
    position: [
      center[0] + (ISO_DIRECTION[0] / length) * distance,
      center[1] + (ISO_DIRECTION[1] / length) * distance,
      center[2] + (ISO_DIRECTION[2] / length) * distance,
    ],
  };
}

/** 缩略图缓存键（场景三组成——任一变整批失效；Map 内层键=unit_id）。 */
export function thumbCacheKey(
  projectId: string,
  conditionKey: string,
  sceneVersion: string,
): string {
  return `${projectId}:${conditionKey}:${sceneVersion}`;
}

/** 半剖切面（C2-visual T1·二轮勘正）：**纵向对角剖**——法向面向相机
 * （iso 方位 45°→剖切面 x+z=对角中面）保留远半、剖掉近半，露出横断面
 * （池壁+水体剖面+内部构件）=工程半剖读感。一轮横向剖（Y 面=水平剖
 * 去上半）观感=「开口朝上的浅池」与未剖无异（glm/ds 三段流双证）。
 * 纯数值派生（法向+常数），three 对象构造归组件层（本 lib 保持 three
 * 零依赖）；渲染层 `new THREE.Plane(normal, constant)` 直接消费——
 * 剖切语义=distanceToPoint≥0 保留（远半）。 */
export function sectionPlane(bounds: {
  min: Vec3;
  max: Vec3;
}): { normal: Vec3; constant: number } {
  const invSqrt2 = 1 / Math.SQRT2;
  const centerDiagonal =
    (bounds.min[0] + bounds.max[0] + bounds.min[2] + bounds.max[2]) / 2;
  return {
    normal: [-invSqrt2, 0, -invSqrt2],
    constant: centerDiagonal * invSqrt2,
  };
}
