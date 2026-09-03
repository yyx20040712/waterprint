/**
 * 道路/走廊条带渲染器：分段四边形 mesh（roads+corridors 双 semantic 单文件）。
 *
 * 输入:  RouteNode[]（投影层产出——世界水平面角点序 [[x, z], …]，每 4 点
 *        一段环序四边形；角点已由 core strip 装配预计算、投影层解码换轴
 *        ——组件层零业务几何，只做类型化三角拼合）
 * 输出:  R3F mesh 组（road/corridor 按 semantic 前缀 kind 查真源表分色
 *        water/power/gas/comm，未知 kind 灰阶兜底——SC1 起与 siteplan
 *        同源消费 shared/ui/semanticColors.ts，字面平行拷贝已收编）
 *
 * 规格说明（L6 roads/corridors 3D 图元批 2026-09-04；SC1 语义色真源化）：
 *   - 每条 strip 一个 mesh：BufferGeometry 逐段双三角 [(0,1,2),(0,2,3)]
 *     偏移索引（4N 角点→2N 三角）；角点已由 core strip 装配预计算、投影
 *     层解码换轴——组件层零业务几何，只做类型化三角拼合）；
 *   - 分层抬升 STRIP_LIFT_Y=0.01（地面 0<条带 0.01<红线 0.02——避免与
 *     boundary/地面图元同面共面深度冲突；渲染层类型化处理非业务推导）；
 *   - 色值经 shared/ui/semanticColors 真源查表（SC1 收编原字面平行
 *     拷贝）：road→road 键、corridor kind→corridor_{kind} 键、
 *     未知 kind→corridor_fallback 键（2D 同键同值零漂移）；
 *   - semantic 解析（"site_corridor:"+kind 前缀查表——core 开放 str 装不
 *     进 dims[值域恒 float]，semantic 拼接是唯一可复原通道）；
 *   - 材质不受光（meshBasicMaterial——条带为图示语义非实体，同红线纪律）。
 */
import { useEffect, useMemo } from "react";
import * as THREE from "three";

import { SEMANTIC_COLORS, semanticColor } from "../../../shared/ui/semanticColors";

import type { RouteNode } from "../lib/projectScene";

/** 条带分层抬升（米）：地面 0<条带 0.01<红线 0.02。 */
const STRIP_LIFT_Y = 0.01;
const ROAD_SEMANTIC = "site_road";
const CORRIDOR_SEMANTIC_PREFIX = "site_corridor:";
/** corridor kind → 语义色真源键前缀（corridor_water 等 4 键+fallback）。 */
const CORRIDOR_TOKEN_PREFIX = "corridor_";

/** semantic → 色值（road 恒灰；corridor 前缀解析 kind 查表；未知兜底灰）。 */
function stripColor(semantic: string): string {
  if (semantic === ROAD_SEMANTIC) {
    return semanticColor("road");
  }
  if (semantic.startsWith(CORRIDOR_SEMANTIC_PREFIX)) {
    const token = CORRIDOR_TOKEN_PREFIX + semantic.slice(CORRIDOR_SEMANTIC_PREFIX.length);
    // 未知 kind→corridor_fallback（#8c8c8c——2D 同键同值；非真源表外的
    // FALLBACK_COLOR，两灰阶值不同不可混）。
    return token in SEMANTIC_COLORS ? semanticColor(token) : semanticColor("corridor_fallback");
  }
  return semanticColor("corridor_fallback");
}

/** 逐段双三角 BufferGeometry：4N 角点（环序）→ 2N 三角索引偏移。 */
function stripGeometry(
  points: ReadonlyArray<[number, number]>,
  liftY: number,
): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  const vertices: number[] = [];
  for (const [x, z] of points) {
    vertices.push(x, liftY, z);
  }
  const indices: number[] = [];
  for (let segment = 0; segment < points.length / 4; segment += 1) {
    const base = segment * 4;
    indices.push(base, base + 1, base + 2, base, base + 2, base + 3);
  }
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  return geometry;
}

function StripMesh({ route }: { route: RouteNode }) {
  // liftY 可选覆盖（缺省=STRIP_LIFT_Y 分层常量——投影层零业务值注入）
  const liftY = route.liftY ?? STRIP_LIFT_Y;
  const geometry = useMemo(
    () => stripGeometry(route.points, liftY),
    [route.points, liftY],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <mesh geometry={geometry}>
      <meshBasicMaterial color={stripColor(route.semantic)} side={THREE.DoubleSide} />
    </mesh>
  );
}

export function SiteRoutes({ routes }: { routes: RouteNode[] }) {
  return (
    <>
      {routes.map((route) => (
        <StripMesh key={route.node_id} route={route} />
      ))}
    </>
  );
}
