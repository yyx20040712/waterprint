/**
 * 缩略图离屏舞台（C2-thumb V1/V2——顺序渲染队列+单帧截取）。
 *
 * 输入:  scene（RenderScene——与 Scene.tsx 同投影产出）+onReady（全批
 *        完成回调 Map<unit_id, dataURL>）
 * 输出:  隐藏 R3F Canvas（96×96——viewport 外定位非 display:none[WebGL
 *        零尺寸上下文风险规避]）+逐单元渲染→toDataURL→队列推进
 *
 * 规格说明（task-C2-thumb-plan.md V1/V2——在册推荐案 R3F 离屏 sprite）：
 *   - frameloop="never"：R3F 不自动渲染——Capture 内 rAF 后手动
 *     gl.render 一次即截取（确定性单帧/零持续 GPU 占用）；
 *   - 顺序队列：state index 单元指针——onCapture 推进（每 rAF 一单元，
 *     摊入交互空闲帧——19 单元全批预算 ≤350ms[设计书 V2]）；
 *   - 灯光/底色=C2-3d V2/V1 冻结口径（环境 0.4+方向 1.4/底色 #0b1526
 *     ——Scene.tsx 同值双源；无阴影——96px 阴影不可辨省 shadow map）；
 *   - waters 不入（呈裁③）；AABB 取景=thumbnailStage 纯函数派生
 *     （V4 iso 30/×1.25 复用）；构型渲染=PoolBox 直用（构型真源单点
 *     ——Scene.tsx 与缩略图同渲染器，改构型两面同步）；
 *   - 无构型单元（分组空/AABB null）不出图——UnitNode 回退象形图标
 *     （V3 回退态）；空批/全空=不挂 Canvas（零渲染开销守门）；
 *   - 本组件归 viewer3d 域（PoolBox 同域直用）——canvas 域消费经 app
 *     层组合穿线（features 互不依赖红线——libraryFocusId 先例同制）。
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";

import {
  groupUnitConstructs,
  thumbCamera,
  unitBounds,
} from "../lib/thumbnailStage";
import type { RenderNode, RenderScene, Vec3 } from "../lib/projectScene";
import { PoolBox } from "./PoolBox";

/** C2-3d 冻结口径（Scene.tsx 同值双源——V2 光比/V1 底色）。 */
const SCENE_BG = "#0b1526";

/** 缩略图边长（逻辑=物理像素——v1 不上 2x 密度[设计书 V1 裁量]）。 */
const THUMB_SIZE = 96;

/** 舞台容器（viewport 外——WebGL 上下文保真）。 */
const STAGE_STYLE: React.CSSProperties = {
  position: "fixed",
  left: -10000,
  top: 0,
  width: THUMB_SIZE,
  height: THUMB_SIZE,
  pointerEvents: "none",
};

/** 单单元截取器：挂载该单元构型→rAF 手动渲染→dataURL 回传。 */
function Capture({
  nodes,
  bounds,
  onCapture,
}: {
  nodes: readonly RenderNode[];
  bounds: { min: Vec3; max: Vec3 };
  onCapture: (dataUrl: string) => void;
}) {
  const gl = useThree((state) => state.gl);
  const camera = useThree((state) => state.camera);
  const scene = useThree((state) => state.scene);
  const captureRef = useRef(onCapture);
  captureRef.current = onCapture;
  const cameraSpec = useMemo(() => thumbCamera(bounds), [bounds]);
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
  }, [nodes, cameraSpec, camera, gl, scene]);
  return (
    <>
      {nodes.map((node) => (
        <PoolBox key={node.id} node={node} />
      ))}
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
  // 单元构型分组+AABB 预派生（渲染序稳定——Map 建立序=solids 遭遇序）
  const queue = useMemo(() => {
    const groups = groupUnitConstructs(scene);
    const entries: Array<{ unitId: string; nodes: readonly RenderNode[]; bounds: { min: Vec3; max: Vec3 } }> = [];
    for (const [unitId, nodes] of groups) {
      const bounds = unitBounds(nodes);
      if (bounds !== null) {
        entries.push({ unitId, nodes, bounds });
      }
    }
    return entries;
  }, [scene]);
  const [index, setIndex] = useState(0);
  const thumbsRef = useRef(new Map<string, string>());
  const onReadyRef = useRef(onReady);
  onReadyRef.current = onReady;

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
  const current = queue[index] as { unitId: string; nodes: readonly RenderNode[]; bounds: { min: Vec3; max: Vec3 } }; // 上界守卫后非空断言等价（TS noUncheckedIndexedAccess）
  return (
    <div style={STAGE_STYLE} aria-hidden>
      <Canvas
        frameloop="never"
        camera={{ fov: 50, near: 0.1, far: 4000, position: [30, 30, 30] }}
        style={{ width: THUMB_SIZE, height: THUMB_SIZE, background: SCENE_BG }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          gl.setSize(THUMB_SIZE, THUMB_SIZE, false);
        }}
      >
        <color attach="background" args={[SCENE_BG]} />
        <ambientLight intensity={0.4} />
        <directionalLight position={[40, 60, 28]} intensity={1.4} />
        <Capture
          key={`${current.unitId}:${index}`}
          nodes={current.nodes}
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
