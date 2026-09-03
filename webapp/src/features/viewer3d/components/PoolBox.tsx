/**
 * 池体/渠道渲染器：按渲染描述生成图元（box/cylinder/plane/extrusion 四 kind 薄壳）。
 *
 * 输入:  RenderNode（投影层产出——dims/position/rotation/semantic 逐值透传；
 *        L5b 起 rotation 弧度直消费——core 装配层已换算，组件零换算）
 * 输出:  R3F 图元组（含 semanticColor 语义色查表——色值归组件层）
 *
 * 规格说明（FE1 实装 v1；L5b 总装模式 2026-09-03）：
 *   - 前端零业务几何推导（§10.5/§16 A7）：dims 键直读；唯一换算=
 *     cylinder diameter→radius（three 接口适配，非业务推导）；
 *   - 旋转消费（L5b→L5R）：box/cylinder/extrusion 的 node.rotation
 *     （换轴后 (0, rz, 0)——绕世界竖轴）直喂 R3F rotation 属性；plane 的
 *     铺地基准（绕 X −90°）与平面旋转改嵌套组合（外层 rotation=平面
 *     旋转、内层 GROUND_TILT_X 铺地——换轴后欧拉分量加法不再可分解，
 *     见 plane 分支注记）；
 *   - 语义色纪律（§19.3）：蓝水线/棕泥线/其余灰阶——一切着色经
 *     semanticColor 查表，禁散落色值；
 *   - 图元组合优先，CSG 仅限开口场景（§12.6——opening 归后续批）；
 *   - extrusion（渠道拉伸体）v1 以盒体承载（断面=width×depth、拉伸=length）。
 */
import type * as THREE from "three";

import type { RenderNode, Vec3 } from "../lib/projectScene";

/** 语义色表（token→色值唯一映射处——渲染描述只带 token）。 */
const SEMANTIC_COLORS: Record<string, string> = {
  pool_wall: "#8d99a6",
  partition: "#7a8694",
  channel: "#7f8a93",
  ground: "#cfd6dc",
  water_surface: "#2f7fd1", // 蓝水线
  sludge: "#8c5a2b", // 棕泥线
  aerator: "#d48806",
  paddle: "#d48806",
  media: "#6a7f5a",
  gate: "#5b8db8",
  pipe: "#5b8db8",
  decant: "#5b8db8",
};

const FALLBACK_COLOR = "#9aa5b1";

/** 语义 token → 色值（未登记语义=灰阶兜底——禁抛错打断渲染）。 */
export const semanticColor = (semantic: string): string =>
  SEMANTIC_COLORS[semantic] ?? FALLBACK_COLOR;

/** plane 铺地基准（绕 X −90°：XY 立面→XZ 水平面——R3F planeGeometry 形态适配）。 */
const GROUND_TILT_X = -Math.PI / 2;

type PoolBoxProps = {
  node: RenderNode;
  clippingPlanes?: THREE.Plane[];
};

export function PoolBox({ node, clippingPlanes }: PoolBoxProps) {
  const position: Vec3 = node.position;
  const common = { position, rotation: node.rotation, clippingPlanes };
  switch (node.kind) {
    case "box":
      return (
        <mesh {...common} castShadow receiveShadow>
          <boxGeometry
            args={[node.dims["length"] ?? 1, node.dims["depth"] ?? 1, node.dims["width"] ?? 1]}
          />
          <meshStandardMaterial color={semanticColor(node.semantic)} />
        </mesh>
      );
    case "cylinder": {
      const radius = (node.dims["diameter"] ?? 1) / 2; // three 接口适配（非业务推导）
      return (
        <mesh {...common} castShadow receiveShadow>
          <cylinderGeometry args={[radius, radius, node.dims["depth"] ?? 1, 32]} />
          <meshStandardMaterial color={semanticColor(node.semantic)} />
        </mesh>
      );
    }
    case "plane":
      // L5R 换轴随行：平面旋转落 Y 轴后，铺地基准与平面旋转的欧拉分量
      // 加法不再可分解（Rx(−90°)·Ry(rz)=斜坡——换轴前 rz 在 Z 槽时分量
      // 加法恰精确）；嵌套组合 Ry(rz)·Rx(−90°)（外层平面旋转、内层铺地
      // ——先铺地后平面旋转为精确形态）。
      return (
        <group position={position} rotation={node.rotation}>
          <mesh rotation={[GROUND_TILT_X, 0, 0]} receiveShadow>
            <planeGeometry args={[node.dims["length"] ?? 1, node.dims["width"] ?? 1]} />
            <meshStandardMaterial color={semanticColor(node.semantic)} />
          </mesh>
        </group>
      );
    case "extrusion":
      return (
        <mesh {...common} castShadow receiveShadow>
          <boxGeometry
            args={[node.dims["length"] ?? 1, node.dims["depth"] ?? 1, node.dims["width"] ?? 1]}
          />
          <meshStandardMaterial color={semanticColor(node.semantic)} />
        </mesh>
      );
    default:
      return null; // 投影层已拒未知 kind（防御位——类型化穷尽）
  }
}
