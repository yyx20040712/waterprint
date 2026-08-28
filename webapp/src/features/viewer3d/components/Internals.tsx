/**
 * 重复构件渲染：InstancedMesh（曝气头/填料/滗水器——每语义组一次 draw call）。
 *
 * 输入:  RenderNode（internals 组——instance_count>1，摆置=投影层 placements）
 * 输出:  实例化图元组（单 draw call 承载数千实例）
 *
 * 规格说明（FE1 实装 v1）：
 *   - 实例数是计算结果的一部分（禁前端推算数量——投影层透传
 *     instance_count，本组件只按 placements 写矩阵）；
 *   - 摆置确定性归投影层（近方阵+原型步距）；本组件零几何计算；
 *   - 色值经 semanticColor 查表（§19.3 语义色纪律）。
 */
import { useLayoutEffect, useRef } from "react";
import * as THREE from "three";

import type { RenderNode } from "../lib/projectScene";
import { semanticColor } from "./PoolBox";

type InternalsProps = {
  node: RenderNode;
  clippingPlanes?: THREE.Plane[];
};

export function Internals({ node, clippingPlanes }: InternalsProps) {
  const meshRef = useRef<THREE.InstancedMesh>(null);

  useLayoutEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) {
      return;
    }
    const matrix = new THREE.Matrix4();
    node.placements.forEach((placement, index) => {
      matrix.setPosition(placement[0], placement[1], placement[2]);
      mesh.setMatrixAt(index, matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
  }, [node.placements]);

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, node.instanceCount]}
      castShadow
      receiveShadow
    >
      <boxGeometry
        args={[node.dims["length"] ?? 1, node.dims["depth"] ?? 1, node.dims["width"] ?? 1]}
      />
      <meshStandardMaterial color={semanticColor(node.semantic)} clippingPlanes={clippingPlanes} />
    </instancedMesh>
  );
}
