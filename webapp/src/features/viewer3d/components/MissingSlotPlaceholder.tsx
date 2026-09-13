/**
 * 检修缺位警示占位（S11 接线批——spec §11 渲染层警示占位）。
 *
 * 输入:  缺位槽 position（模板本地系池底平面轮廓中心 [x, 0, z]——冻结
 *        契约产物）+单池平面米数（cellL/cellW——poolGroupPlan 组装）+
 *        剖切平面组（可选——警示面与场景剖切一致）
 * 输出:  虚线矩形框（lineLoop+lineDashedMaterial）+半透明警示面
 *        （maintenance 语义色——SC1 真源表新键）
 *
 * 规格说明（S11 裁定文字「半透明轮廓/虚线框」；SiteBoundary 贴地微抬
 *   先例）：
 *   - 虚线=图示语义（非实体轮廓）：lineDashedMaterial 需
 *     computeLineDistances（R3F lineLoop 语义下由 ref effect 补）；
 *   - 半透明面 y=池底平面+微抬 0.02（红线贴地先例——防与池底/地面
 *     深度冲突）；depthWrite=false 防半透明排序污池壁；
 *   - 剖切面随 props 挂（低剖切高时警示面同剖——场景一致性）；
 *   - 组件薄壳零业务推导：尺寸/位置全由 poolGroupPlan 数值直喂。
 */
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";

import type { Vec3 } from "../assemble/types";

/** 贴地微抬（米）——SiteBoundary 同款（红线贴地先例）。 */
const PLACEHOLDER_LIFT_Y = 0.02;
/** 虚线段长/隙（米——警示框视认档，非工程标注）。 */
const DASH_SIZE = 1.5;
/** 半透明警示面不透明度（图示档——不遮占位下的池底/地面细节）。 */
const FACE_OPACITY = 0.25;

type MissingSlotPlaceholderProps = {
  readonly position: Vec3;
  readonly cellL: number;
  readonly cellW: number;
  readonly clippingPlanes?: THREE.Plane[];
};

export function MissingSlotPlaceholder({
  position,
  cellL,
  cellW,
  clippingPlanes,
}: MissingSlotPlaceholderProps) {
  const lineRef = useRef<THREE.LineLoop>(null);
  const points = useMemo(
    () => [
      new THREE.Vector3(-cellL / 2, 0, -cellW / 2),
      new THREE.Vector3(cellL / 2, 0, -cellW / 2),
      new THREE.Vector3(cellL / 2, 0, cellW / 2),
      new THREE.Vector3(-cellL / 2, 0, cellW / 2),
    ],
    [cellL, cellW],
  );
  const geometry = useMemo(
    () => new THREE.BufferGeometry().setFromPoints(points),
    [points],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  // lineDashedMaterial 契约：挂载后须 computeLineDistances 虚线才显
  useEffect(() => {
    lineRef.current?.computeLineDistances();
  }, [geometry]);
  const y = position[1] + PLACEHOLDER_LIFT_Y;
  return (
    <group position={[position[0], y, position[2]]}>
      <lineLoop ref={lineRef} geometry={geometry}>
        <lineDashedMaterial
          color={semanticColor("maintenance")}
          dashSize={DASH_SIZE}
          gapSize={DASH_SIZE}
          clippingPlanes={clippingPlanes ?? null}
        />
      </lineLoop>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[cellL, cellW]} />
        <meshBasicMaterial
          color={semanticColor("maintenance")}
          transparent
          opacity={FACE_OPACITY}
          depthWrite={false}
          clippingPlanes={clippingPlanes ?? null}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}
