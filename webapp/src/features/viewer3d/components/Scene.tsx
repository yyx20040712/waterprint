/**
 * R3F Canvas：灯光/相机/剖切平面 + 四组渲染器挂载（viewer3d 薄壳入口）。
 *
 * 输入:  projectId + 可选 conditionKey（useSceneQuery 数据通道→projectScene 投影）
 *        + store view 态（cameraPreset——漫游 preset 的唯一驱动源）
 * 输出:  三维场景渲染容器（懒加载路由挂载点——§12.6 独立 chunk；OrbitControls
 *        漫游（L5b）——拖拽旋转/滚轮缩放/右键平移）
 *
 * 规格说明（FE1 实装 v1；R2 C2 围栏 2026-08-28；L5b 总装+漫游 2026-09-03）：
 *   - 前端零业务几何推导（§10.5/§16 A7）：一切数据经投影层
 *     projectScene（SCENE_VERSION 门在此生效）；组件只做类型化摆放；
 *   - 渲染期围栏（R2 C2）：投影层四类显式拒（版本门/未知 kind/root
 *     悬空/红线顶点不完整）在 useMemo 内 try/catch 落错误薄壳（呈现
 *     SceneProjectionError 原因文本，不白屏——ErrorBoundary 未挂载现状下
 *     唯一围栏）；
 *   - 剖切：store（clippingEnabled/Height）→ THREE.Plane → 材质
 *     clippingPlanes（Y-up 高度面，§12.3 view 态）；
 *   - UX2 D5 取景自适应：机位=preset 方向归一×（对角线×1.5）+bounds
 *     中心（投影层 bounds 全 placements∪红线顶点 AABB——机位薄壳不测，
 *     app 层惯例；空场景回退原绝对坐标；fov 50 不变）；
 *   - 漫游（L5b 预裁 6）：OrbitControls 挂载（three 包内 examples/jsm——
 *     零新 npm 依赖）+三 preset 并存：preset 点击=设相机 position+target
 *     一次（CameraRig effect），用户随后可自由拖拽/缩放/平移（controls
 *     内部态不入 store——纯 view 态纪律 §12.3 零新增字段）；
 *   - preset 按钮面（ENG6）：Canvas 前兄弟按钮组（stale 横幅同形态）
 *     驱动 store.cameraPreset——当前 preset=primary 高亮（siteplan 工具栏
 *     先例）；四字标签避 antd 两字插空格坑（教训 24）；
 *   - 图层开关：水面/内部构件/标注（store 显隐——渲染密度控制）；
 *   - 总装红线（L5b）：boundaries 组挂 SiteBoundary（闭合折线——core
 *     顶点序即权威，闭合段渲染层补）；
 *   - 性能预算 1080p ≥60fps（InstancedMesh 前提，§18.1）；
 *   - 加载/错误态薄壳呈现（WaterprintApiError.message 透出）；UX1 D5：
 *     404 领域码门控附引导——仅 code==="SceneSourceNotFoundError"（无
 *     最近完成结果集——server scene.py 404 面实锚）附「先提交计算」
 *     hint（elevation/cost/drawings 族同模式同源）；网络错/其他错不挂
 *     （I-3 分级口径——禁误导引导）。
 */
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Canvas, extend, useThree, type ThreeElement } from "@react-three/fiber";
import { Button, Space } from "antd";

import { useSceneQuery } from "../api/useSceneQuery";
import { WaterprintApiError } from "../../../shared/api/http";
import {
  SceneProjectionError,
  projectScene,
  type RenderScene,
} from "../lib/projectScene";
import { useViewer3dStore, type CameraPreset } from "../store/viewer3dStore";
import { Annotations } from "./Annotations";
import { Internals } from "./Internals";
import { PoolBox } from "./PoolBox";
import { SiteBoundary } from "./SiteBoundary";
import { SiteRoutes } from "./SiteRoutes";
import { WaterSurface } from "./WaterSurface";

// L5b 漫游：three 包内 OrbitControls 经 extend 注册为 R3F 元素——
// 零新 npm 依赖（预裁 6）；类型经 ThreeElements 声明合并进 R3F 命名空间
// （makeDefault=R3F 运行时通用 prop——置入 state.controls 供 CameraRig 取）。
extend({ OrbitControls });
declare module "@react-three/fiber" {
  interface ThreeElements {
    orbitControls: ThreeElement<typeof OrbitControls> & { makeDefault?: boolean };
  }
}

const CAMERA_PRESETS = {
  iso: [30, 25, 30] as [number, number, number],
  top: [0, 60, 1] as [number, number, number],
  side: [40, 5, 0] as [number, number, number],
};

/** 画布高度：视口减页头/页签/内边距铬件（L5R 探针 B2 修复——R3F Canvas
 *  无内在尺寸，父链 auto 高度下塌缩 150px；SVG viewBox 自适应族不同）。 */
const CANVAS_HEIGHT = "calc(100vh - 220px)";
const CANVAS_MIN_HEIGHT = 420;

/** 取景中心（bounds AABB 中心；空场景=原点——零场景零尺度基准）。 */
function sceneCenter(scene: RenderScene): [number, number, number] {
  const bounds = scene.bounds;
  if (bounds === null) {
    return [0, 0, 0];
  }
  return [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
}

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
  const center = sceneCenter(scene);
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

/**
 * 相机漫游座（L5b）：OrbitControls 常驻挂载（makeDefault——state.controls
 * 可达）+preset 点击=设相机 position+target 一次（effect 依赖仅
 * preset/scene/controls 引用——用户随后拖拽/缩放/平移不重置机位）。
 */
function CameraRig({ preset, scene }: { preset: CameraPreset; scene: RenderScene }) {
  const camera = useThree((state) => state.camera);
  const gl = useThree((state) => state.gl);
  const controls = useThree((state) => state.controls) as OrbitControls | null;
  useEffect(() => {
    const position = cameraPosition(preset, scene);
    const center = sceneCenter(scene);
    camera.position.set(position[0], position[1], position[2]);
    if (controls !== null) {
      controls.target.set(center[0], center[1], center[2]);
      controls.update();
    } else {
      camera.lookAt(center[0], center[1], center[2]);
    }
  }, [preset, scene, camera, controls]);
  return <orbitControls args={[camera, gl.domElement]} makeDefault />;
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
  const setCameraPreset = useViewer3dStore((state) => state.setCameraPreset);
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
      {/* ENG6 preset 按钮面：Canvas 前兄弟元素（stale 横幅同形态）——点击
          驱动 store.cameraPreset（CameraRig effect 负责落机位一次）；当前
          preset=primary（siteplan 工具栏先例）；四字标签避 antd 两字
          插空格坑（教训 24）。 */}
      <Space size="small" wrap style={{ padding: "4px 0" }}>
        {(
          [
            ["iso", "等轴视角"],
            ["top", "俯视视角"],
            ["side", "侧视视角"],
          ] as const
        ).map(([value, label]) => (
          <Button
            key={value}
            size="small"
            type={cameraPreset === value ? "primary" : "default"}
            onClick={() => setCameraPreset(value)}
          >
            {label}
          </Button>
        ))}
      </Space>
      <Canvas
        camera={{ position: cameraPosition(cameraPreset, scene), fov: 50 }}
        shadows
        gl={{ localClippingEnabled: clippingEnabled }}
        style={{ height: CANVAS_HEIGHT, minHeight: CANVAS_MIN_HEIGHT }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
        <CameraRig preset={cameraPreset} scene={scene} />
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
        <SiteRoutes routes={scene.routes} />
        {scene.boundaries.map((node) => (
          <SiteBoundary key={node.id} node={node} />
        ))}
        {showAnnotations && <Annotations nodes={scene.solids} />}
      </Canvas>
    </>
  );
}
