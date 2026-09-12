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
 *   - C2-3d（2026-09-10）：V1 地面/双层工程网格（10m/2m）+雾边融+
 *     画布底色黑→#0b1526（「黑背景无边融」痛点收口）；V2 光影档
 *     （环境 0.4/方向 1.4+阴影正交半幅随对角线+灯位 target=bounds
 *     中心）；V4 取景系数 1.5→1.25+iso 俯角 30（呈裁④「更近更俯」）；
 *     地面/网格/灯位全 bounds 派生（零场景零地面——零尺度基准沿
 *     sceneCenter 先例）；
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

import { useSceneQuery } from "../api/useSceneQuery";
import { useReadProjectApiProjectsProjectIdGet } from "../../../shared/api/generated/projects/projects";
import { WaterprintApiError } from "../../../shared/api/http";
import { semanticColor } from "../../../shared/ui/semanticColors";
import { claimTemplateUnits } from "../assemble/templateAssembly";
import { attachGlInfo, registerProbe } from "../assemble/probe";
import {
  SceneProjectionError,
  projectScene,
  type RenderNode,
  type RenderScene,
} from "../lib/projectScene";
import { placementSummary } from "../lib/placementSummary";
import { useViewer3dStore, type CameraPreset } from "../store/viewer3dStore";
import { Annotations } from "./Annotations";
import { Internals } from "./Internals";
import { PoolBox } from "./PoolBox";
import { SiteBoundary } from "./SiteBoundary";
import { SiteRoutes } from "./SiteRoutes";
import { TemplateUnit } from "./TemplateUnit";
import { ViewerToolbar } from "./ViewerToolbar";
import { WaterSurface } from "./WaterSurface";

// 批3 主体：探针注册（模块级——viewer3d 路由 chunk 载入即挂载；幂等）
registerProbe();

/** 节点 id 首段（{unit_id}::{part} 形态——裸 id=null 非单元构型件）。 */
function unitIdOf(nodeId: string): string | null {
  const sep = nodeId.indexOf("::");
  return sep > 0 ? nodeId.slice(0, sep) : null;
}

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
  // C2-3d V4（呈裁④「更近更俯」）：iso 俯角 25→30（俯瞰厂区感）
  iso: [30, 30, 30] as [number, number, number],
  top: [0, 60, 1] as [number, number, number],
  side: [40, 5, 0] as [number, number, number],
};

/** C2-3d V1 地面/雾色——批3 迭代二（用户批注 b-①）：绿草地可隐藏图层，
 * 关=回深蓝工程底（页面 --wp-bg-page 同值 #0b1526）；网格恒蓝系
 * （绿草地+蓝工程网格——GPS-X 厂区参考系）；
 * 网格两色=主格/次格分层。缩略图台（ThumbnailStage）恒绿世界底
 * ——与 PNG 资产同源，不随本图层开关。 */
const SCENE_BG_GRASS = "#0e2415";
const SCENE_BG_DARK = "#0b1526";
const GRID_MAJOR = "#3d619c";
const GRID_MINOR = "#1b2c49";

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
  // C2-3d V4（呈裁④）：距离系数 1.5→1.25（更近一档——「偏远」感收口）
  const distance = diagonal * 1.25;
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
  // F9（C2-visual 批）：design.nodes 总数（摆放态横幅 M 值——shared orval
  // hook 经 shared 层合法引用，react-query 同键缓存与 canvas 面复用零
  // 额外请求；详情未就绪/形状异常=横幅不挂 fail-open）
  const projectQuery = useReadProjectApiProjectsProjectIdGet(projectId);
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
  const showGrass = useViewer3dStore((state) => state.showGrass);
  const showWater = useViewer3dStore((state) => state.showWater);
  const showInternals = useViewer3dStore((state) => state.showInternals);
  const showAnnotations = useViewer3dStore((state) => state.showAnnotations);
  const sceneBg = showGrass ? SCENE_BG_GRASS : SCENE_BG_DARK;

  const clippingPlanes = useMemo(() => {
    if (!clippingEnabled) {
      return undefined;
    }
    // Y-up 高度面：保留 height 以下（法向 -Y——剖掉上方，§12.3）
    const plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), clippingHeight);
    return [plane];
  }, [clippingEnabled, clippingHeight]);

  // C2-3d V1/V2 地面/网格/灯位数据面（bounds 派生——空场景 bounds=null
  // 零地面：零场景零尺度基准沿 sceneCenter 先例）
  const ground = useMemo(() => {
    const bounds = projection.scene?.bounds ?? null;
    if (bounds === null) {
      return null;
    }
    const sizeX = bounds.max[0] - bounds.min[0];
    const sizeZ = bounds.max[2] - bounds.min[2];
    const span = Math.max(sizeX, sizeZ, 10);
    // 主格 10m：总尺寸=最大边×3.2 向上取整到 10m 倍数（gridHelper 以
    // 中心对称布格——奇偶格数均可；3.2=glm 二轮 2.2→3.2 调档，雾远缘
    // 3.2×对角同档淡出余量）
    const groundSize = Math.ceil((span * 3.2) / 10) * 10;
    const diagonal = Math.hypot(sizeX, bounds.max[1] - bounds.min[1], sizeZ);
    return {
      size: groundSize,
      majorDivisions: groundSize / 10,
      minorDivisions: groundSize / 2,
      centerX: (bounds.min[0] + bounds.max[0]) / 2,
      centerZ: (bounds.min[2] + bounds.max[2]) / 2,
      // V2 灯位/阴影覆盖：对角线驱动（阴影正交相机半幅=对角线×0.75）
      diagonal,
    };
  }, [projection.scene]);
  // V2 方向光 target（bounds 中心——阴影相机随场景中心覆盖；primitive
  // 挂载进场景使 target 变换生效）
  const lightTarget = useMemo(() => new THREE.Object3D(), []);
  useEffect(() => {
    if (ground !== null) {
      lightTarget.position.set(ground.centerX, 0, ground.centerZ);
      lightTarget.updateMatrixWorld();
    }
  }, [lightTarget, ground]);

  // 批3 主体：模板族声明（assemble/claimTemplateUnits——取数节点=kind
  // 匹配 dimSource；多实例池节点在 internals——S5 相邻双池前提）
  const templateClaims = useMemo(
    () => claimTemplateUnits(projection.scene),
    [projection.scene],
  );

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
          style={{ padding: "4px 8px", color: semanticColor("pending"), fontSize: 12 }}
        >
          设计已修改但未重算——本场景基于旧结果集（重新提交计算后刷新）
        </div>
      ) : null}
      {/* F9（C2-visual 批）：摆放态解释横幅——scene 仅收已布置单元（core
          build_scene 诚实语义），部分摆放时显式告知防「三维骤降」误读
          （placementSummary 判据收口=structures 非空且 placed<total[GV-01
          R 轮]；兜底满场/全覆盖/详情不可达均返 null 不挂）。 */}
      {(() => {
        const summary = placementSummary(scene, projectQuery.data ?? null);
        return summary !== null ? (
          <div
            role="status"
            data-testid="placement-banner"
            style={{
              padding: "4px 8px",
              color: semanticColor("pending"),
              fontSize: 12,
            }}
          >
            三维仅显示已在「厂区布置」标签摆放的构筑物与相关管廊（
            {summary.placed}/{summary.total}）——未摆放单元不参与三维
            场景，摆放并重新计算后可见。
          </div>
        ) : null;
      })()}
      {/* ENG6 工具条（preset 按钮组+图层开关面——批3 迭代二抽件
          ViewerToolbar[行数预算门 500]；图层开关=用户批注 b-① 草地
          可隐藏+水面/内部/标注 store 三键同制补 UI 调用方） */}
      <ViewerToolbar />
      <Canvas
        camera={{ position: cameraPosition(cameraPreset, scene), fov: 50 }}
        shadows
        gl={{ localClippingEnabled: clippingEnabled }}
        onCreated={({ gl }) => {
          // 批3 主体：drawcalls/三角面探针读数位（验收 ≤120 消费）
          attachGlInfo(gl);
        }}
        style={{
          height: CANVAS_HEIGHT,
          minHeight: CANVAS_MIN_HEIGHT,
          background: sceneBg,
        }}
      >
        {/* C2-3d V1 雾边融：远缘网格/地面淡出至场景底色（近/远=对角线
            档距——bounds 空零地面时雾不挂；批3 迭代二：雾色随草地开关） */}
        {ground !== null && (
          <>
            <fog attach="fog" args={[sceneBg, ground.diagonal * 1.2, ground.diagonal * 3.2]} />
            <primitive object={lightTarget} />
          </>
        )}
        {/* C2-3d V2 光影：环境光降档+方向光提档（阴影对比度）；灯位/阴影
            正交半幅按对角线适配+target=bounds 中心（覆盖随场景） */}
        <ambientLight intensity={0.4} />
        {ground !== null ? (
          <directionalLight
            position={[
              ground.centerX + ground.diagonal * 0.5,
              ground.diagonal * 0.8,
              ground.centerZ + ground.diagonal * 0.35,
            ]}
            intensity={1.4}
            castShadow
            target={lightTarget}
            shadow-mapSize-width={4096}
            shadow-mapSize-height={4096}
            shadow-camera-left={-ground.diagonal * 0.75}
            shadow-camera-right={ground.diagonal * 0.75}
            shadow-camera-top={ground.diagonal * 0.75}
            shadow-camera-bottom={-ground.diagonal * 0.75}
            shadow-camera-far={ground.diagonal * 2.5}
            onUpdate={(light) => light.shadow.camera.updateProjectionMatrix()}
          />
        ) : (
          // 空场景回退档（bounds=null 零尺度基准——对角线派生面[灯位/
          // 阴影幅]不可得，v1 常量灯保持；非 V2 调档对象——A 二审
          // GD-N-04 口径记档）
          <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
        )}
        <CameraRig preset={cameraPreset} scene={scene} />
        {/* C2-3d V1 地面（V2 阴影承接面——批3 迭代二：草地=可隐藏图层，
            关=深蓝工程底+蓝网格恒在；y 分层避 z-fight：地面 -0.02<
            次格 -0.012<主格 -0.008） */}
        {ground !== null && showGrass && (
          <>
            <mesh
              position={[ground.centerX, -0.02, ground.centerZ]}
              rotation={[-Math.PI / 2, 0, 0]}
              receiveShadow
            >
              <planeGeometry args={[ground.size, ground.size]} />
              <meshStandardMaterial color="#2e5239" />
            </mesh>
          </>
        )}
        {ground !== null && (
          <>
            <gridHelper
              args={[ground.size, ground.majorDivisions, GRID_MAJOR, GRID_MAJOR]}
              position={[ground.centerX, -0.008, ground.centerZ]}
            />
            <gridHelper
              args={[ground.size, ground.minorDivisions, GRID_MINOR, GRID_MINOR]}
              position={[ground.centerX, -0.012, ground.centerZ]}
            />
          </>
        )}
        {/* 批3 主体：模板族装配分支——registry ready 条目按单元整族承载
            （取数节点=kind 匹配 dimSource[辐流=cylinder]；单元其余构型件
            [::channel 深度退化柱等]由模板承载不重复渲染；加载中/失败/
            出域降级链归 TemplateUnit 内部——原语/盒体保持不白屏） */}
        {scene.solids.map((node) => {
          const unitId = unitIdOf(node.id);
          const claim = unitId !== null ? templateClaims.get(unitId) : undefined;
          if (claim !== undefined && node === claim.dimNode) {
            return (
              <TemplateUnit
                key={node.id}
                entry={claim.entry}
                unitId={unitId ?? node.id}
                dimNode={node}
                scene={scene}
                clippingPlanes={clippingPlanes}
              />
            );
          }
          if (claim !== undefined) {
            return null; // 单元整族承载——构型件由模板呈现
          }
          return (
            // C2VD V3（终裁 L2）：主视图描边——灰阶构筑物对蓝底/蓝网格
            // 对比度收口（EdgesGeometry 棱线=语义色派生亮化；缩略图不挂）
            <PoolBox key={node.id} node={node} clippingPlanes={clippingPlanes} edges />
          );
        })}
        {showWater &&
          scene.waters.map((node) => (
            <WaterSurface key={node.id} node={node} clippingPlanes={clippingPlanes} />
          ))}
        {showInternals &&
          scene.internals.map((node) => {
            const unitId = unitIdOf(node.id);
            const claim = unitId !== null ? templateClaims.get(unitId) : undefined;
            if (claim !== undefined && node === claim.dimNode) {
              return (
                <TemplateUnit
                  key={node.id}
                  entry={claim.entry}
                  unitId={unitId ?? node.id}
                  dimNode={node}
                  scene={scene}
                  clippingPlanes={clippingPlanes}
                />
              );
            }
            if (claim !== undefined) {
              return null; // 整族承载（含未来 inst 计数承载节点——数据源不重复渲染）
            }
            return <Internals key={node.id} node={node} clippingPlanes={clippingPlanes} />;
          })}
        <SiteRoutes routes={scene.routes} />
        {scene.boundaries.map((node) => (
          <SiteBoundary key={node.id} node={node} />
        ))}
        {/* C2-3d V3：对角线传参（字号自适应——bounds 空=下钳） */}
        {showAnnotations && (
          <Annotations nodes={scene.solids} diagonal={ground?.diagonal ?? 0} />
        )}
      </Canvas>
    </>
  );
}
