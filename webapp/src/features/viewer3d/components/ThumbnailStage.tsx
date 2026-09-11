/**
 * 缩略图离屏舞台（C2-thumb V1/V2——顺序渲染队列+单帧截取）。
 *
 * 输入:  scene（RenderScene——与 Scene.tsx 同投影产出）+onReady（全批
 *        完成回调 Map<unit_id, dataURL>）
 * 输出:  隐藏 R3F Canvas（192×192=2x 物理——viewport 外定位非
 *        display:none[WebGL 零尺寸上下文风险规避]）+逐单元渲染→
 *        toDataURL→队列推进
 *
 * 规格说明（task-C2-thumb-plan.md V1/V2——在册推荐案 R3F 离屏 sprite）：
 *   - frameloop="never"：R3F 不自动渲染——Capture 内 rAF 后手动
 *     gl.render 一次即截取（确定性单帧/零持续 GPU 占用）；
 *   - 顺序队列：state index 单元指针——onCapture 推进（每 rAF 一单元，
 *     摊入交互空闲帧——19 单元全批预算 ≤350ms[设计书 V2]）；
 *   - 灯光/底色=C2-3d V2/V1 冻结口径（底色 #0b1526——Scene.tsx 同值双源；
 *     无阴影——小图阴影不可辨省 shadow map；C2-visual T4：光比 0.55/1.6
 *     独立微调[紫外消毒暗构型]——自此与主视图分源非联动）；
 *   - C2-visual 迭代（task-c2-visual-plan §二）：T1 纵向对角半剖
 *     （面向相机剖近半露横断面——二轮勘正：水平剖去上半观感=浅池
 *     与未剖无异[glm/ds 双证]）；T2 waters 半透明入图（呈裁③ 复核
 *     推翻「噪点」判断——剖切语境水体剖面蓝语义可辨+DoubleSide 内面
 *     可见）；T3 192=2x 物理（hover 大图 160 近原生——消费面
 *     UnitNode）；取景 V4 iso 30/×1.25 复用
 *     （thumbnailStage 纯函数派生）；构型渲染=PoolBox/WaterSurface 直用
 *     （构型真源单点——Scene.tsx 与缩略图同渲染器，改构型两面同步）；
 *   - 无构型单元（分组空/AABB null）不出图——UnitNode 回退象形图标
 *     （V3 回退态）；空批/全空=不挂 Canvas（零渲染开销守门）；
 *   - 本组件归 viewer3d 域（PoolBox 同域直用）——canvas 域消费经 app
 *     层组合穿线（features 互不依赖红线——libraryFocusId 先例同制）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import * as THREE from "three";

import {
  groupUnitConstructs,
  groupUnitWaters,
  hasCapWriters,
  sectionCapQuad,
  sectionPlane,
  thumbCamera,
  unitBounds,
} from "../lib/thumbnailStage";
import type { RenderNode, RenderScene, Vec3 } from "../lib/projectScene";
import { PoolBox } from "./PoolBox";
import { SectionCap } from "./SectionCap";
import { WaterSurface } from "./WaterSurface";

/** C2-3d 冻结口径（Scene.tsx 同值双源——V2 光比/V1 底色；C2-visual T4
 * 亮度微调：0.4/1.4→0.55/1.6[紫外消毒暗构型提升]——与 Scene.tsx 主视图
 * 光比自此分源[缩略图小图面独立裁量]，非联动面）。 */
const SCENE_BG = "#0b1526";
const AMBIENT_INTENSITY = 0.55;
const DIRECTIONAL_INTENSITY = 1.6;

/** 缩略图渲染边长（C2-visual T3：96→192=2x 物理——卡片 44 缩显更清晰+
 * hover 悬浮 160 近原生；顺序队列单帧成本可忽略）。逻辑=物理像素。 */
const THUMB_SIZE = 192;

/** 舞台容器（viewport 外——WebGL 上下文保真）。 */
const STAGE_STYLE: React.CSSProperties = {
  position: "fixed",
  left: -10000,
  top: 0,
  width: THUMB_SIZE,
  height: THUMB_SIZE,
  pointerEvents: "none",
};

/** Canvas 配置常量（CV-N-01 R2 轮外提——内联对象在 index 推进重渲时
 * 引用变更，R3F 视为配置漂移有相机/renderer 重建风险；fov 50=V4 取景
 * 冻结值，near/far=场景尺度域，初始 position 由 CameraRig/effect 落位）。 */
const CANVAS_CAMERA: Record<string, unknown> = {
  fov: 50,
  near: 0.1,
  far: 4000,
  position: [30, 30, 30],
};
const CANVAS_GL: Record<string, unknown> = { antialias: true, stencil: true };

/** 单单元截取器：挂载该单元构型→rAF 手动渲染→dataURL 回传。
 * C2-visual T1/T2：纵向对角半剖（sectionPlane 派生——面向相机剖近半
 * 露横断面；GV-N-02 R2 轮注释同步）+waters 半透明入图（WaterSurface
 * 复用——剖面语义水面）。 */
function Capture({
  nodes,
  waters,
  bounds,
  onCapture,
}: {
  nodes: readonly RenderNode[];
  waters: readonly RenderNode[];
  bounds: { min: Vec3; max: Vec3 };
  onCapture: (dataUrl: string) => void;
}) {
  const gl = useThree((state) => state.gl);
  const camera = useThree((state) => state.camera);
  const scene = useThree((state) => state.scene);
  const captureRef = useRef(onCapture);
  captureRef.current = onCapture;
  const cameraSpec = useMemo(() => thumbCamera(bounds), [bounds]);
  // 半剖平面（T1 二轮勘正=纵向对角剖——面向相机剖掉近半露横断面；
  // Scene.tsx §12.3 剖切先例同构消费 THREE.Plane；C2VD V1 起单实例
  // memo——SectionCap writer 与材质 clippingPlanes 同引用共享）
  const clipPlane = useMemo(() => {
    const spec = sectionPlane(bounds);
    return new THREE.Plane(
      new THREE.Vector3(spec.normal[0], spec.normal[1], spec.normal[2]),
      spec.constant,
    );
  }, [bounds]);
  const clippingPlanes = useMemo(() => [clipPlane], [clipPlane]);
  // C2VD V1 剖切帽盖面片派生（中心投影至剖切面+过幅边长——纯函数）
  const capQuad = useMemo(() => sectionCapQuad(bounds), [bounds]);
  const capped = useMemo(() => hasCapWriters(nodes), [nodes]);
  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      camera.position.set(...cameraSpec.position);
      camera.lookAt(
        cameraSpec.center[0],
        cameraSpec.center[1],
        cameraSpec.center[2],
      );
      gl.render(scene, camera);
      captureRef.current(gl.domElement.toDataURL("image/png"));
    });
    return () => cancelAnimationFrame(raf);
  }, [nodes, waters, cameraSpec, camera, gl, scene]);
  return (
    <>
      {nodes.map((node) => (
        <PoolBox key={node.id} node={node} clippingPlanes={clippingPlanes} />
      ))}
      {waters.map((node) => (
        <WaterSurface key={node.id} node={node} clippingPlanes={clippingPlanes} />
      ))}
      {/* C2VD V1 剖切帽盖：stencil writer+共享面片——材质断面区封实
          （水体/空腔区不入——writer 仅封闭构型件）；全 plane 件单元不挂 */}
      {capped ? <SectionCap nodes={nodes} plane={clipPlane} quad={capQuad} /> : null}
    </>
  );
}

export function ThumbnailStage({
  scene,
  onReady,
}: {
  scene: RenderScene;
  /** 全批完成回调（含全部成功截取的单元——一次性整批交付）。 */
  onReady: (thumbs: ReadonlyMap<string, string>) => void;
}) {
  // 单元构型分组+AABB 预派生（渲染序稳定——Map 建立序=solids 遭遇序；
  // C2-visual T2：waters 并入分组与 AABB（取景含水面稳定））
  const queue = useMemo(() => {
    const groups = groupUnitConstructs(scene);
    const waterGroups = groupUnitWaters(scene);
    const entries: Array<{ unitId: string; nodes: readonly RenderNode[]; waters: readonly RenderNode[]; bounds: { min: Vec3; max: Vec3 } }> = [];
    for (const [unitId, nodes] of groups) {
      const waters = waterGroups.get(unitId) ?? [];
      const bounds = unitBounds([...nodes, ...waters]);
      if (bounds !== null) {
        entries.push({ unitId, nodes, waters, bounds });
      }
    }
    return entries;
  }, [scene]);
  const [index, setIndex] = useState(0);
  const thumbsRef = useRef(new Map<string, string>());
  const onReadyRef = useRef(onReady);
  onReadyRef.current = onReady;
  // GD-01（D 一审修复）：scene 变（同键原地 refetch——重算后场景内容变）
  // 队列态/半成品批复位重渲——否则旧完成态 index 卡住或交付陈旧 Map
  // （跨项目切换经卸载重挂载幸免；同项目重算路径此前无复位）。
  useEffect(() => {
    setIndex(0);
    thumbsRef.current = new Map();
  }, [scene]);

  // 队列耗尽=整批交付（一次性 setState 上抛——消费面 Map 引用稳定）
  useEffect(() => {
    if (index >= queue.length) {
      if (queue.length > 0) {
        onReadyRef.current(thumbsRef.current);
      }
      return;
    }
  }, [index, queue.length]);

  if (queue.length === 0 || index >= queue.length) {
    return null; // 空批不挂 Canvas（V2 守门——零渲染开销）
  }
  const current = queue[index] as { unitId: string; nodes: readonly RenderNode[]; waters: readonly RenderNode[]; bounds: { min: Vec3; max: Vec3 } }; // 上界守卫后非空断言等价（TS noUncheckedIndexedAccess）
  return (
    <div style={STAGE_STYLE} aria-hidden>
      <Canvas
        frameloop="never"
        camera={CANVAS_CAMERA}
        style={{ width: THUMB_SIZE, height: THUMB_SIZE, background: SCENE_BG }}
        gl={CANVAS_GL}
        onCreated={({ gl }) => {
          gl.setSize(THUMB_SIZE, THUMB_SIZE, false);
          // T1 半剖前置：材质 clippingPlanes 生效需本地剖切开关
          // （Scene.tsx localClippingEnabled 先例同构）
          gl.localClippingEnabled = true;
        }}
      >
        <color attach="background" args={[SCENE_BG]} />
        <ambientLight intensity={AMBIENT_INTENSITY} />
        <directionalLight position={[40, 60, 28]} intensity={DIRECTIONAL_INTENSITY} />
        <Capture
          key={`${current.unitId}:${index}`}
          nodes={current.nodes}
          waters={current.waters}
          bounds={current.bounds}
          onCapture={(dataUrl) => {
            thumbsRef.current.set(current.unitId, dataUrl);
            setIndex((prev) => prev + 1); // 顺序队列推进（V2——每帧一单元）
          }}
        />
      </Canvas>
    </div>
  );
}
