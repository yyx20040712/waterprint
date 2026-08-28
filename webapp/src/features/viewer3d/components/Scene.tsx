/**
 * R3F Canvas：灯光/相机/剖切平面 + 三组渲染器挂载（viewer3d 薄壳入口）。
 *
 * 输入:  projectId + 可选 conditionKey（useSceneQuery 数据通道→projectScene 投影）
 * 输出:  三维场景渲染容器（懒加载路由挂载点——§12.6 独立 chunk）
 *
 * 规格说明（FE1 实装 v1）：
 *   - 前端零业务几何推导（§10.5/§16 A7）：一切数据经投影层
 *     projectScene（SCENE_VERSION 门在此生效）；组件只做类型化摆放；
 *   - 剖切：store（clippingEnabled/Height）→ THREE.Plane → 材质
 *     clippingPlanes（Y-up 高度面，§12.3 view 态）；
 *   - 图层开关：水面/内部构件/标注（store 显隐——渲染密度控制）；
 *   - 性能预算 1080p ≥60fps（InstancedMesh 前提，§18.1）；
 *   - 加载/错误态薄壳呈现（WaterprintApiError.message 透出）。
 */
import { useMemo } from "react";
import * as THREE from "three";
import { Canvas } from "@react-three/fiber";

import { useSceneQuery } from "../api/useSceneQuery";
import { projectScene } from "../lib/projectScene";
import { useViewer3dStore } from "../store/viewer3dStore";
import { Annotations } from "./Annotations";
import { Internals } from "./Internals";
import { PoolBox } from "./PoolBox";
import { WaterSurface } from "./WaterSurface";

const CAMERA_PRESETS = {
  iso: [30, 25, 30] as [number, number, number],
  top: [0, 60, 1] as [number, number, number],
  side: [40, 5, 0] as [number, number, number],
};

export function Scene({
  projectId,
  conditionKey,
}: {
  projectId: string;
  conditionKey?: string;
}) {
  const query = useSceneQuery(projectId, conditionKey);
  const scene = useMemo(
    () => (query.data ? projectScene(query.data) : null),
    [query.data],
  );
  const cameraPreset = useViewer3dStore((state) => state.cameraPreset);
  const clippingEnabled = useViewer3dStore((state) => state.clippingEnabled);
  const clippingHeight = useViewer3dStore((state) => state.clippingHeight);
  const showWater = useViewer3dStore((state) => state.showWater);
  const showInternals = useViewer3dStore((state) => state.showInternals);
  const showAnnotations = useViewer3dStore((state) => state.showAnnotations);

  const clippingPlanes = useMemo(() => {
    if (!clippingEnabled) {
      return undefined;
    }
    // Y-up 高度面：保留 height 以下（法向 -Y——剖掉上方，§12.3）
    const plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), clippingHeight);
    return [plane];
  }, [clippingEnabled, clippingHeight]);

  if (query.isError) {
    return (
      <div role="alert">
        场景加载失败：{query.error instanceof Error ? query.error.message : "未知错误"}
      </div>
    );
  }
  if (!scene) {
    return <div>场景加载中…（{projectId.slice(0, 8)}）</div>;
  }
  return (
    <Canvas
      camera={{ position: CAMERA_PRESETS[cameraPreset], fov: 50 }}
      shadows
      gl={{ localClippingEnabled: clippingEnabled }}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
      {scene.solids.map((node) => (
        <PoolBox key={node.id} node={node} clippingPlanes={clippingPlanes} />
      ))}
      {showWater &&
        scene.waters.map((node) => (
          <WaterSurface key={node.id} node={node} clippingPlanes={clippingPlanes} />
        ))}
      {showInternals &&
        scene.internals.map((node) => (
          <Internals key={node.id} node={node} clippingPlanes={clippingPlanes} />
        ))}
      {showAnnotations && <Annotations nodes={scene.solids} />}
    </Canvas>
  );
}
