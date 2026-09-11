/**
 * 剖切帽盖（C2VD V1）：stencil 双 writer+单元共享帽盖面片——缩略图纵向
 * 对角半剖的剖口实体断面封实（three 官方 webgl_clipping_stencil 技法）。
 *
 * 输入:  nodes（单元封闭构型件——Capture 构型组）+plane（剖切面 THREE.Plane
 *        ——Capture 派生）+quad（帽盖面片中心/边长——sectionCapQuad 派生）
 * 输出:  writer 双 mesh 组（背面 IncrementWrap/正面 DecrementWrap——
 *        depthTest/colorWrite/depthWrite 全关）+帽盖面片（stencilRef 0/
 *        NotEqual——仅画在材质断面区）
 *
 * 规格说明（briefs/task-c2vd-plan.md §一——单元级合成制）：
 *   - 模板语义（计数推演在案）：stencil+1 区=射线经被剖半进入实体区
 *     =剖切面∩实体材质区——壁板/底板断面封实；水体（无 writer）与
 *     空腔区恒 0 不画——**水体断面蓝与内部构件可见性保持**（n+38 终裁
 *     面零回归——帽盖不遮水体断面）；
 *   - 单元级合成（vs 官方 per-object）：单剖切面+多封闭实体→全 writer
 *     共序（renderOrder 1）+单元共享帽盖面片（renderOrder 2）——同面
 *     同色与逐件帽盖视觉等价；缩略图单帧渲染（frameloop never）每帧
 *     autoClear 清 stencil，零 clearStencil 复位簿记；
 *   - writer 几何=solidGeometry 单源规格（与 PoolBox 渲染同式——plane
 *     开面片计数不闭合[单面薄壳无背面]返 null 排除）；
 *   - 渲染序：色面 renderOrder 0（默认）先画写深度→writer 1（无深度
 *     无颜色纯模板）→帽盖 2（NotEqual 0 材质断面区封实——被剖半已
 *     discard 无深度竞争）；
 *   - 主视图（Scene.tsx §12.3 水平剖）不挂——本件=缩略图半剖语境专属
 *     （剖口封盖主视图面归后续裁量）。
 */
import { useMemo } from "react";
import * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";

import type { RenderNode, Vec3 } from "../lib/projectScene";
import { solidGeometry, type SolidGeometrySpec } from "../lib/thumbnailStage";

/** writer 渲染序（帽盖=+1——官方制 writers→cap 紧随）。 */
const WRITER_ORDER = 1;
const CAP_ORDER = 2;

/** writer mesh 三件套材质 props（共享——背面增/正面减只差 side 与 op）。 */
function writerProps(
  side: THREE.Side,
  op: THREE.StencilOp,
  plane: THREE.Plane,
) {
  return {
    side,
    depthWrite: false,
    depthTest: false,
    colorWrite: false,
    stencilWrite: true,
    stencilFunc: THREE.AlwaysStencilFunc,
    stencilFail: op,
    stencilZFail: op,
    stencilZPass: op,
    clippingPlanes: [plane],
  };
}

export function SectionCap({
  nodes,
  plane,
  quad,
}: {
  nodes: readonly RenderNode[];
  plane: THREE.Plane;
  quad: { center: Vec3; size: number };
}) {
  // 封闭件规格派生（plane 件排除——开面片计数不闭合）
  const writers = useMemo(
    () =>
      nodes
        .map((node) => ({ node, spec: solidGeometry(node) }))
        .filter(
          (entry): entry is { node: RenderNode; spec: SolidGeometrySpec } =>
            entry.spec !== null,
        ),
    [nodes],
  );
  // 帽盖面片姿态：PlaneGeometry 默认法向 +z →对齐剖切面法向（法向背向
  // 相机——材质 DoubleSide 免背面剔除；帽盖无 clippingPlanes：恰卧于
  // 剖切面，clip 判定 distance≥0 保留但浮点噪声在零点抖动，官方制同不挂）
  const quaternion = useMemo(
    () =>
      new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 0, 1),
        plane.normal,
      ),
    [plane],
  );
  return (
    <>
      {writers.map(({ node, spec }) => (
        <group key={node.id}>
          <mesh
            position={node.position}
            rotation={node.rotation}
            renderOrder={WRITER_ORDER}
          >
            {spec.kind === "box" ? (
              <boxGeometry args={spec.args} />
            ) : (
              <cylinderGeometry args={[spec.args[0], spec.args[1], spec.args[2], 32]} />
            )}
            <meshBasicMaterial
              {...writerProps(THREE.BackSide, THREE.IncrementWrapStencilOp, plane)}
            />
          </mesh>
          <mesh
            position={node.position}
            rotation={node.rotation}
            renderOrder={WRITER_ORDER}
          >
            {spec.kind === "box" ? (
              <boxGeometry args={spec.args} />
            ) : (
              <cylinderGeometry args={[spec.args[0], spec.args[1], spec.args[2], 32]} />
            )}
            <meshBasicMaterial
              {...writerProps(THREE.FrontSide, THREE.DecrementWrapStencilOp, plane)}
            />
          </mesh>
        </group>
      ))}
      <mesh position={quad.center} quaternion={quaternion} renderOrder={CAP_ORDER}>
        <planeGeometry args={[quad.size, quad.size]} />
        {/* 材质=MeshBasic 平涂（工程剖面封盖惯例——断面恒色不受光照；
            亦使帽盖与受光墙面[115-160 区]色距确定分离——无头像素桶
            断言确定性前提）。 */}
        <meshBasicMaterial
          color={semanticColor("section_cap")}
          side={THREE.DoubleSide}
          stencilWrite
          stencilRef={0}
          stencilFunc={THREE.NotEqualStencilFunc}
          stencilFail={THREE.ReplaceStencilOp}
          stencilZFail={THREE.ReplaceStencilOp}
          stencilZPass={THREE.ReplaceStencilOp}
        />
      </mesh>
    </>
  );
}
