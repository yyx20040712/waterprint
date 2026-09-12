/**
 * 模板剖切帽盖（spec.md §7 S4/S5 定案——批3 主体）。
 *
 * 输入:  装配计划（template 态——shell 组节点与组变换）+本实例 placement
 *        +全部 placements（邻池间距）+剖切面（主视图 §12.3 高度面）
 * 输出:  双 writer 组（shell 未标 __nc 子件——背面 IncrementWrap/正面
 *        DecrementWrap；对象克隆承载节点 TRS[量化重定心补偿位]）+
 *        逐实例 cap 面片（stencilRef 0/NotEqual——仅画材质断面区）
 *
 * 规格说明（S5 定案=逐实例 cap 面：每实例一枚=单元 AABB 投影剖切面+
 *   过幅 1.1×；过幅侵入邻池钳至间距内（95% 留隙）——共面帽盖零重复
 *   绘制；奇偶计数 NotEqual 0 多封闭体叠加保持；不采用逐实例清
 *   stencil/按池分 pass。S4 封盖材质集=仅 shell 未标 __nc 水密子件；
 *   trim/equipment/instance 恒不入（被剖穿帮入验收口径——材质
 *   DoubleSide 由 TemplateUnit 挂载）。C2VD SectionCap 同制迁移：
 *   renderOrder 色 0/writer 1/cap 2；帽盖无 clippingPlanes[恰卧剖切面
 *   浮点抖动，官方制同不挂]）。
 */

import { useMemo } from "react";
import * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";
import type { AssemblyPlan } from "../assemble/templateAssembly";
import type { Vec3 } from "../assemble/types";

const WRITER_ORDER = 1;
const CAP_ORDER = 2;

/** 剖切面高程（§12.3 恒法向 (0,−1,0)：plane y=constant；防御位=法向
 * 非 Y 轴时取常数面最近点，主视图口径下不可达）。 */
function planeHeight(plane: THREE.Plane): number {
  if (Math.abs(plane.normal.y) < 1e-6) {
    return plane.constant;
  }
  return -plane.constant / plane.normal.y;
}

/** 逐实例 cap 面（S5）：中心=placement 剖切面位；边长=足迹对角×1.1
 * 过幅，邻池距<过幅钳至间距 95%（钳制底=足迹对角——数据病时保覆盖）。 */
export function capQuadFor(
  placement: Vec3,
  placements: readonly Vec3[],
  target: { L: number; W: number },
  planeY: number,
): { center: [number, number, number]; size: number } {
  const diag = Math.hypot(target.L, target.W);
  let size = diag * 1.1;
  let nearest = Number.POSITIVE_INFINITY;
  for (const other of placements) {
    if (other === placement) {
      continue;
    }
    const distance = Math.hypot(other[0] - placement[0], other[2] - placement[2]);
    if (distance > 0 && distance < nearest) {
      nearest = distance;
    }
  }
  if (Number.isFinite(nearest)) {
    size = Math.min(size, nearest * 0.95);
  }
  return { center: [placement[0], planeY, placement[2]], size: Math.max(size, diag) };
}

/** writer 克隆对象（节点 TRS 保留——几何引用共享零拷贝；材质=stencil
 * 纯模板双 mesh 载体）。 */
function buildWriters(
  groups: ReadonlyArray<{ node: { object: THREE.Object3D } }>,
  plane: THREE.Plane,
): THREE.Object3D[] {
  const clones: THREE.Object3D[] = [];
  const sides: ReadonlyArray<[THREE.Side, THREE.StencilOp]> = [
    [THREE.BackSide, THREE.IncrementWrapStencilOp],
    [THREE.FrontSide, THREE.DecrementWrapStencilOp],
  ];
  for (const { node } of groups) {
    for (const [side, op] of sides) {
      const clone = node.object.clone(true);
      clone.traverse((child) => {
        const mesh = child as THREE.Mesh;
        if (!mesh.isMesh) {
          return;
        }
        mesh.material = new THREE.MeshBasicMaterial({
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
        });
        mesh.renderOrder = WRITER_ORDER;
        mesh.castShadow = false;
        mesh.receiveShadow = false;
      });
      clones.push(clone);
    }
  }
  return clones;
}

export function TemplateCap({
  plan,
  placement,
  placements,
  plane,
}: {
  plan: Extract<AssemblyPlan, { kind: "template" }>;
  placement: Vec3;
  placements: readonly Vec3[];
  plane: THREE.Plane;
}) {
  // S4 封盖材质集：shell 未标 __nc（trim/equipment/instance 恒不入）
  const shellNodes = useMemo(
    () => plan.groups.filter(({ node }) => node.group === "shell" && !node.nc),
    [plan],
  );
  const writers = useMemo(() => buildWriters(shellNodes, plane), [shellNodes, plane]);
  const quad = useMemo(
    () => capQuadFor(placement, placements, plan.target, planeHeight(plane)),
    [placement, placements, plan.target, plane],
  );
  const capMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: semanticColor("section_cap"),
        side: THREE.DoubleSide,
        stencilWrite: true,
        stencilRef: 0,
        stencilFunc: THREE.NotEqualStencilFunc,
        stencilFail: THREE.ReplaceStencilOp,
        stencilZFail: THREE.ReplaceStencilOp,
        stencilZPass: THREE.ReplaceStencilOp,
      }),
    [],
  );
  // 帽盖姿态：平面片 +z 法向 →水平面向上（§12.3 恒 Y 法向——绕 X −90°；
  // DoubleSide 免背面剔除，方向仅语义位）
  const quaternion = useMemo(
    () => new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0)),
    [],
  );
  const writerTransforms = shellNodes.map(({ transform }) => transform);
  return (
    <>
      {writers.map((object, index) => {
        const transform = writerTransforms[Math.floor(index / 2)];
        if (transform === undefined) {
          return null;
        }
        return (
          <group
            key={`w:${index}`}
            position={[
              transform.translation[0],
              transform.translation[1],
              transform.translation[2],
            ]}
            scale={[transform.scale[0], transform.scale[1], transform.scale[2]]}
          >
            <primitive object={object} />
          </group>
        );
      })}
      <mesh
        position={quad.center}
        quaternion={quaternion}
        renderOrder={CAP_ORDER}
        material={capMaterial}
      >
        <planeGeometry args={[quad.size, quad.size]} />
      </mesh>
    </>
  );
}
