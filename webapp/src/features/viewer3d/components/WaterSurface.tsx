/**
 * 水面渲染：半透明盒体 + 透明度脉动动画（零 CPU 物理，§10.5）。
 *
 * 输入:  RenderNode（water_surface 组——投影层已分流；L5b 起 rotation
 *        弧度直消费——core 装配层已换算）
 * 输出:  动画水面组件（useFrame 时间函数）
 *
 * 规格说明（FE1 实装 v1）：
 *   - 动画零 CPU 物理（shader 时间函数同族——v1 以 material.opacity
 *     脉动承载，UV 偏移流纹归后续增强批）；
 *   - 色值经 semanticColor（蓝水线 §19.3——SC1 起真源=shared/ui/
 *     semanticColors.ts）；dims 直读零推导；
 *   - 真圆水面（SC1 L5R-A01）：dims 含 diameter 键→cylinderGeometry
 *     真圆盘（径向 48 段：弦高误差≈0.11%d 肉眼不可辨，<24 棱线可见）；
 *     否则 boxGeometry 旧径（box 池 length×width——diameter→radius=
 *     three 接口适配，非业务推导）；
 *   - 剖切平面随 props（store → Scene → 材质）。
 */
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";

import type { RenderNode } from "../lib/projectScene";

const BASE_OPACITY = 0.55;
const PULSE_AMPLITUDE = 0.08;
const PULSE_SPEED = 1.5;

type WaterSurfaceProps = {
  node: RenderNode;
  clippingPlanes?: THREE.Plane[];
};

export function WaterSurface({ node, clippingPlanes }: WaterSurfaceProps) {
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.opacity =
        BASE_OPACITY + PULSE_AMPLITUDE * Math.sin(state.clock.elapsedTime * PULSE_SPEED);
    }
  });

  const diameter = node.dims["diameter"]; // SC1 真圆：cylinder 池水面足迹键
  return (
    <mesh position={node.position} rotation={node.rotation}>
      {diameter !== undefined ? (
        <cylinderGeometry args={[diameter / 2, diameter / 2, node.dims["depth"] ?? 1, 48]} />
      ) : (
        <boxGeometry
          args={[node.dims["length"] ?? 1, node.dims["depth"] ?? 1, node.dims["width"] ?? 1]}
        />
      )}
      <meshStandardMaterial
        ref={materialRef}
        color={semanticColor("water_surface")}
        transparent
        opacity={BASE_OPACITY}
        depthWrite={false}
        clippingPlanes={clippingPlanes}
      />
    </mesh>
  );
}
