/**
 * 重复构件渲染：InstancedMesh（曝气头/填料/滗水器——每语义组一次 draw call）。
 *
 * 输入:  RenderNode（internals 组——instance_count>1，摆置=投影层 placements；
 *        L5b 起 rotation 弧度逐实例消费——core 装配层已换算）
 * 输出:  实例化图元组（单 draw call 承载数千实例）
 *
 * 规格说明（FE1 实装 v1；图元选择 dims 键驱动 FE1 M2 2026-08-28）：
 *   - 实例数是计算结果的一部分（禁前端推算数量——投影层透传
 *     instance_count，本组件只按 placements 写矩阵）；
 *   - 摆置确定性归投影层（近方阵+原型步距）；本组件零几何计算；
 *   - 旋转消费（L5b）：逐实例矩阵 compose（位置=placement、姿态=
 *     node.rotation 欧拉→四元数）；方阵网格方向恒世界轴（与 core 装配
 *     层加法摆放同口径——非零局部 XY 的旋转矩阵化升级归挂账）；
 *   - 图元选择由 dims 键驱动（internalsGeometry 纯函数：diameter 键在
 *     →cylinder，否则 box）——core v1 实例组恒 box（spacing 立方），
 *     非 box 图元到达时不再静默失真为盒体（M2 门）；diameter→半径=
 *     three 接口适配（PoolBox 同口径，非业务推导）；
 *   - 色值经 semanticColor 查表（§19.3 语义色纪律——SC1 起真源=
 *     shared/ui/semanticColors.ts）。
 */
import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";

import type { RenderNode } from "../lib/projectScene";

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

  // L5b：逐实例姿态（node.rotation 欧拉弧度→四元数——compose 用，零换算）
  const quaternion = useMemo(
    () =>
      new THREE.Quaternion().setFromEuler(
        new THREE.Euler(node.rotation[0], node.rotation[1], node.rotation[2]),
      ),
    [node.rotation],
  );

  useLayoutEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) {
      return;
    }
    const matrix = new THREE.Matrix4();
    const translation = new THREE.Vector3();
    const scale = new THREE.Vector3(1, 1, 1);
    node.placements.forEach((placement, index) => {
      translation.set(placement[0], placement[1], placement[2]);
      matrix.compose(translation, quaternion, scale);
      mesh.setMatrixAt(index, matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
  }, [node.placements, quaternion]);

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
