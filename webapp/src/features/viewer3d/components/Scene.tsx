/**
 * R3F Canvas：灯光/相机/剖切平面 + 三组渲染器挂载（viewer3d 薄壳入口）。
 *
 * 输入:  projectId + 可选 conditionKey（useSceneQuery 数据通道→projectScene 投影）
 * 输出:  三维场景渲染容器（懒加载路由挂载点——§12.6 独立 chunk）
 *
 * 规格说明（FE1 实装 v1；R2 C2 围栏 2026-08-28）：
 *   - 前端零业务几何推导（§10.5/§16 A7）：一切数据经投影层
 *     projectScene（SCENE_VERSION 门在此生效）；组件只做类型化摆放；
 *   - 渲染期围栏（R2 C2）：投影层三类显式拒（版本门/未知 kind/root
 *     悬空）在 useMemo 内 try/catch 落错误薄壳（呈现 SceneProjectionError
 *     原因文本，不白屏——ErrorBoundary 未挂载现状下唯一围栏）；
 *   - 剖切：store（clippingEnabled/Height）→ THREE.Plane → 材质
 *     clippingPlanes（Y-up 高度面，§12.3 view 态）；
 *   - UX2 D5 取景自适应：机位=preset 方向归一×（对角线×1.5）+bounds
 *     中心（投影层 bounds 全 placements AABB——机位薄壳不测，app 层
 *     惯例；空场景回退原绝对坐标；fov 50 不变）；
 *   - 图层开关：水面/内部构件/标注（store 显隐——渲染密度控制）；
 *   - 性能预算 1080p ≥60fps（InstancedMesh 前提，§18.1）；
 *   - 加载/错误态薄壳呈现（WaterprintApiError.message 透出）；UX1 D5：
 *     404 领域码门控附引导——仅 code==="SceneSourceNotFoundError"（无
 *     最近完成结果集——server scene.py 404 面实锚）附「先提交计算」
 *     hint（elevation/cost/drawings 族同模式同源）；网络错/其他错不挂
 *     （I-3 分级口径——禁误导引导）。
 */
import { useMemo } from "react";
import * as THREE from "three";
import { Canvas } from "@react-three/fiber";

import { useSceneQuery } from "../api/useSceneQuery";
import { WaterprintApiError } from "../../../shared/api/http";
import {
  SceneProjectionError,
  projectScene,
  type RenderScene,
} from "../lib/projectScene";
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

/**
 * UX2 D5 取景自适应机位：preset 方向向量归一化×（对角线长×1.5）+
 * bounds 中心（三 preset 方向语义保持——iso 斜视/top 近俯视微倾防正射
 * 退化/side 侧视；fov 50 不变；固定机位不随场景尺度的 FE3 质量观察①
 * 收口）。空场景（bounds=null）回退原绝对坐标——零场景零尺度基准。
 */
function cameraPosition(
  preset: keyof typeof CAMERA_PRESETS,
  scene: RenderScene,
): [number, number, number] {
  const direction = CAMERA_PRESETS[preset];
  const bounds = scene.bounds;
  if (bounds === null) {
    return direction;
  }
  const center: [number, number, number] = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
  const length = Math.hypot(direction[0], direction[1], direction[2]);
  const unit: [number, number, number] =
    length > 0
      ? [direction[0] / length, direction[1] / length, direction[2] / length]
      : [0, 1, 0];
  const diagonal = Math.hypot(
    bounds.max[0] - bounds.min[0],
    bounds.max[1] - bounds.min[1],
    bounds.max[2] - bounds.min[2],
  );
  const distance = diagonal * 1.5;
  return [
    center[0] + unit[0] * distance,
    center[1] + unit[1] * distance,
    center[2] + unit[2] * distance,
  ];
}

/** 404 引导（无最近完成结果集——先提交计算；UX1 D5 与 elevation/cost/
 * drawings 族 NO_CALC_HINT 同模式同源，尾词随三维面板）。 */
const NO_CALC_HINT =
  "——请先提交计算（POST /api/calc/run）完成后再回本标签查看三维场景。";

export function Scene({
  projectId,
  conditionKey,
}: {
  projectId: string;
  conditionKey?: string;
}) {
  const query = useSceneQuery(projectId, conditionKey);
  // R2 C2 渲染期围栏：投影层显式拒（版本门/未知 kind/root 悬空）在此
  // 收编——落错误态薄壳（fetch 面 isError 之外的第二个错误出口，不白屏）。
  const projection = useMemo<{
    scene: RenderScene | null;
    error: SceneProjectionError | null;
  }>(() => {
    if (!query.data) {
      return { scene: null, error: null };
    }
    try {
      return { scene: projectScene(query.data), error: null };
    } catch (error) {
      return {
        scene: null,
        error:
          error instanceof SceneProjectionError
            ? error
            : new SceneProjectionError(String(error)),
      };
    }
  }, [query.data]);
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
        {/* UX1 D5：仅 404 无最近完成结果集面附引导（code 门控）——网络错/
            其他错不挂误导 hint（I-3 分级口径） */}
        {query.error instanceof WaterprintApiError &&
        query.error.code === "SceneSourceNotFoundError"
          ? NO_CALC_HINT
          : null}
      </div>
    );
  }
  if (projection.error) {
    return (
      <div role="alert">
        场景投影失败：{projection.error.message}
      </div>
    );
  }
  const scene = projection.scene;
  if (!scene) {
    return <div>场景加载中…（{projectId.slice(0, 8)}）</div>;
  }
  return (
    <>
      {/* AUDIT2 FIX2（C-1 闭环）：结果集过期显式提示（服务端 stale 旗标）——
          fragment 同级横幅，Canvas 父子关系与尺寸零扰动。 */}
      {query.data?.stale ? (
        <div
          role="status"
          style={{ padding: "4px 8px", color: "#d48806", fontSize: 12 }}
        >
          设计已修改但未重算——本场景基于旧结果集（重新提交计算后刷新）
        </div>
      ) : null}
      <Canvas
        camera={{ position: cameraPosition(cameraPreset, scene), fov: 50 }}
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
    </>
  );
}
