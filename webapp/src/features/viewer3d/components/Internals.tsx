/**
 * 重复构件渲染：InstancedMesh（曝气头/填料/滗水器——每语义组一次 draw call）。
 *
 * 输入:  RenderNode（internals 组——instance_count>1，摆置=投影层 placements）
 * 输出:  实例化图元组（单 draw call 承载数千实例）
 *
 * 规格说明（FE1 实装 v1；图元选择 dims 键驱动 FE1 M2 2026-08-28）：
 *   - 实例数是计算结果的一部分（禁前端推算数量——投影层透传
 *     instance_count，本组件只按 placements 写矩阵）；
 *   - 摆置确定性归投影层（近方阵+原型步距）；本组件零几何计算；
 *   - 图元选择由 dims 键驱动（internalsGeometry 纯函数：diameter 键在
 *     →cylinder，否则 box）——core v1 实例组恒 box（spacing 立方），
 *     非 box 图元到达时不再静默失真为盒体（M2 门）；diameter→半径=
 *     three 接口适配（PoolBox 同口径，非业务推导）；
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

/** 实例组图元描述（dims 键驱动选择——FE1 M2）。 */
export type InternalsGeometry =
  | { kind: "box"; args: [number, number, number] }
  | { kind: "cylinder"; args: [number, number, number] };

export function internalsGeometry(node: RenderNode): InternalsGeometry {
  if (node.dims["diameter"] !== undefined) {
    const radius = node.dims["diameter"] / 2; // three 接口适配（同 PoolBox 口径）
    return { kind: "cylinder", args: [radius, radius, node.dims["depth"] ?? 1] };
  }
  return {
    kind: "box",
    args: [node.dims["length"] ?? 1, node.dims["depth"] ?? 1, node.dims["width"] ?? 1],
  };
}

export function Internals({ node, clippingPlanes }: InternalsProps) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const geometry = internalsGeometry(node);

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
      {geometry.kind === "cylinder" ? (
        <cylinderGeometry args={geometry.args} />
      ) : (
        <boxGeometry args={geometry.args} />
      )}
      <meshStandardMaterial color={semanticColor(node.semantic)} clippingPlanes={clippingPlanes} />
    </instancedMesh>
  );
}
