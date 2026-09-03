/**
 * 道路/走廊条带渲染器：分段四边形 mesh（roads+corridors 双 semantic 单文件）。
 *
 * 输入:  RouteNode[]（投影层产出——世界水平面角点序 [[x, z], …]，每 4 点
 *        一段环序四边形；角点已由 core strip 装配预计算、投影层解码换轴
 *        ——组件层零业务几何，只做类型化三角拼合）
 * 输出:  R3F mesh 组（road=#6b6f76 灰、corridor 按 semantic 前缀 kind 查表
 *        分色 water/power/gas/comm，未知 kind 灰阶兜底——siteplan
 *        SiteCanvas 色值字面平行，feature 互不 import 门禁禁跨片引用）
 *
 * 规格说明（L6 roads/corridors 3D 图元批 2026-09-04）：
 *   - 每条 strip 一个 mesh：BufferGeometry 逐段双三角 [(0,1,2),(0,2,3)]
 *     偏移索引（4N 角点→2N 三角）；DoubleSide 防绕序（环序方向不保证
 *     面向相机——双面材质免背面剔除）；
 *   - 分层抬升 STRIP_LIFT_Y=0.01（地面 0<条带 0.01<红线 0.02——避免与
 *     boundary/地面图元同面共面深度冲突；渲染层类型化处理非业务推导）；
 *   - 色值本地常量（沿 SiteBoundary BOUNDARY_COLOR 字面平行先例——
 *     组件间不引色表）：ROAD_COLOR=siteplan COLOR_ROAD 同色、
 *     CORRIDOR_KIND_COLORS=siteplan CORRIDOR_COLORS 字面平行、
 *     未知 kind→CORRIDOR_FALLBACK_COLOR（2D 默认色平行）；
 *   - semantic 解析（"site_corridor:"+kind 前缀查表——core 开放 str 装不
 *     进 dims[值域恒 float]，semantic 拼接是唯一可复原通道）；
 *   - 材质不受光（meshBasicMaterial——条带为图示语义非实体，同红线纪律）。
 */
import { useEffect, useMemo } from "react";
import * as THREE from "three";

import type { RouteNode } from "../lib/projectScene";

/** siteplan COLOR_ROAD 同色先例（字面平行——跨 feature 引用被门禁禁）。 */
const ROAD_COLOR = "#6b6f76";
/** siteplan CORRIDOR_COLORS 字面平行（kind→色值）。 */
const CORRIDOR_KIND_COLORS: Record<string, string> = {
  water: "#2f7fd1",
  power: "#f2a93b",
  gas: "#3fa34d",
  comm: "#9a6dd7",
};
/** 未知 corridor kind 灰阶兜底（siteplan 2D 默认色平行）。 */
const CORRIDOR_FALLBACK_COLOR = "#8c8c8c";
/** 条带分层抬升（米）：地面 0<条带 0.01<红线 0.02。 */
const STRIP_LIFT_Y = 0.01;
const ROAD_SEMANTIC = "site_road";
const CORRIDOR_SEMANTIC_PREFIX = "site_corridor:";

/** semantic → 色值（road 恒灰；corridor 前缀解析 kind 查表；未知兜底灰）。 */
function stripColor(semantic: string): string {
  if (semantic === ROAD_SEMANTIC) {
    return ROAD_COLOR;
  }
  if (semantic.startsWith(CORRIDOR_SEMANTIC_PREFIX)) {
    const kind = semantic.slice(CORRIDOR_SEMANTIC_PREFIX.length);
    return CORRIDOR_KIND_COLORS[kind] ?? CORRIDOR_FALLBACK_COLOR;
  }
  return CORRIDOR_FALLBACK_COLOR;
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
