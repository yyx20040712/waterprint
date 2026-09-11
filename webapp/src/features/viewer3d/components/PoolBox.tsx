/**
 * 池体/渠道渲染器：按渲染描述生成图元（box/cylinder/plane/extrusion 四 kind 薄壳）。
 *
 * 输入:  RenderNode（投影层产出——dims/position/rotation/semantic 逐值透传；
 *        L5b 起 rotation 弧度直消费——core 装配层已换算，组件零换算）
 * 输出:  R3F 图元组（含 semanticColor 语义色查表——色值归 shared
 *        语义色真源 SC1；可选 EdgesGeometry 描边——C2VD V3 主视图对比度）
 *
 * 规格说明（FE1 实装 v1；L5b 总装模式 2026-09-03；SC1 语义色真源化；
 * C2VD V1/V3 2026-09-11）：
 *   - 前端零业务几何推导（§10.5/§16 A7）：dims 键直读；唯一换算=
 *     cylinder diameter→radius（three 接口适配，非业务推导）；
 *   - 封闭件几何规格=solidGeometry 单源消费（C2VD V1：box/extrusion→box
 *     spec、cylinder→cylinder spec、plane→null 开面片——与 SectionCap
 *     writer 同规格，几何规格双源根除）；
 *   - 旋转消费（L5b→L5R）：box/cylinder/extrusion 的 node.rotation
 *     （换轴后 (0, rz, 0)——绕世界竖轴）直喂 R3F rotation 属性；plane 的
 *     铺地基准（绕 X −90°）与平面旋转改嵌套组合（外层 rotation=平面
 *     旋转、内层 GROUND_TILT_X 铺地——换轴后欧拉分量加法不再可分解，
 *     见 plane 分支注记）；
 *   - 语义色纪律（§19.3）：蓝水线/棕泥线/其余灰阶——一切着色经
 *     semanticColor 查表（SC1 起真源=shared/ui/semanticColors.ts，
 *     本组件不再持本地表），禁散落色值；
 *   - C2VD V3 描边（edges=true——主视图挂：灰阶构筑物对蓝底/蓝网格
 *     对比度收口[终裁 L2 首选建议「摆放物加描边」]）：lineSegments=
 *     EdgesGeometry 同源几何（阈值 30°——box 90° 棱全收/cylinder 32
 *     段侧面棱[邻面角≈11°]全抑—— фасет 线噪点防线）；线色=语义色
 *     multiplyScalar(EDGE_BRIGHTEN) 派生亮化（零新字面值）；plane 开
 *     面片不描（ground 语义 #cfd6dc 本浅色高可见，非 L2 对比度问题面）；
 *     缩略图（ThumbnailStage）缺省不挂——n+38 已验收面零回归；
 *   - 几何 imperative useMemo+卸载 dispose（EdgesGeometry 需源几何
 *     实例——JSX 几何不可引用；场景 refetch 重建零泄漏防线）；
 *   - 图元组合优先，CSG 仅限开口场景（§12.6——opening 归后续批）；
 *   - extrusion（渠道拉伸体）v1 以盒体承载（断面=width×depth、拉伸=length）。
 */
import { useEffect, useMemo } from "react";
import * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";

import type { RenderNode, Vec3 } from "../lib/projectScene";
import { solidGeometry } from "../lib/thumbnailStage";

/** plane 铺地基准（绕 X −90°：XY 立面→XZ 水平面——R3F planeGeometry 形态适配）。 */
const GROUND_TILT_X = -Math.PI / 2;

/** 描边棱阈值（度）：>30° 面夹角才出棱——cylinder 侧面段棱（≈11°）全抑。 */
const EDGE_ANGLE_DEG = 30;

/** 描边线色亮化系数（语义色 multiplyScalar 派生——非新色值字面量）。 */
const EDGE_BRIGHTEN = 1.45;

type PoolBoxProps = {
  node: RenderNode;
  clippingPlanes?: THREE.Plane[];
  /** C2VD V3：主视图描边（缺省 false——缩略图零回归）。 */
  edges?: boolean;
};

export function PoolBox({ node, clippingPlanes, edges = false }: PoolBoxProps) {
  const position: Vec3 = node.position;
  // 封闭件几何（C2VD V1 单源规格——plane 开面片返 null 走 JSX plane 分支）。
  // deps=kind/dims 对象身份（CV-03 R 轮注记前提）：投影层 projectScene 在
  // Scene.tsx useMemo [query.data] 内产出——同数据态 node/dims 引用稳定，
  // 几何零重建；仅场景数据变更时重建（预期重建面+dispose 闭环）。
  const geometry = useMemo(() => {
    const spec = solidGeometry(node);
    if (spec === null) {
      return null;
    }
    return spec.kind === "box"
      ? new THREE.BoxGeometry(...spec.args)
      : new THREE.CylinderGeometry(spec.args[0], spec.args[1], spec.args[2], 32);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node.kind, node.dims]);
  // CV-N-02 R2 轮条件化：edges=false（缩略图缺省）不建棱线几何/色实例
  // ——顺序队列逐单元重挂载下免无谓分配。
  const edgeGeometry = useMemo(
    () =>
      edges && geometry !== null
        ? new THREE.EdgesGeometry(geometry, EDGE_ANGLE_DEG)
        : null,
    [edges, geometry],
  );
  const edgeColor = useMemo(
    () =>
      edges
        ? new THREE.Color(semanticColor(node.semantic)).multiplyScalar(EDGE_BRIGHTEN)
        : null,
    [edges, node.semantic],
  );
  // 卸载释放（imperative 几何不归 R3F 自动 dispose 面——refetch 重建防线）
  useEffect(
    () => () => {
      geometry?.dispose();
      edgeGeometry?.dispose();
    },
    [geometry, edgeGeometry],
  );
  if (geometry === null) {
    // plane 分支（L5R 换轴随行）：嵌套组合明确表达「先铺地（Rx −90°）后
    // 平面旋转（Ry rz）」的目标合成 Ry(rz)·Rx(−90°)。换轴前 rz 在 Z 槽时，旧
    // 分量加法 Rx(−90°)·Rz(rz) 与该目标恒等（L5R-A05 恒等式——旧代码
    // 因此碰巧精确）；rz 换 Y 槽后原样加法合成 Rx(−90°)·Ry(rz)=斜坡，
    // 故弃分量加法改嵌套（不依赖欧拉序恒等式，语义自明）。
    // 材质级剖切同接（CV-02 R 轮真修——§12.3 高度剖对 plane 件同步生效）。
    return (
      <group position={position} rotation={node.rotation}>
        <mesh rotation={[GROUND_TILT_X, 0, 0]} receiveShadow>
          <planeGeometry args={[node.dims["length"] ?? 1, node.dims["width"] ?? 1]} />
          <meshStandardMaterial
            color={semanticColor(node.semantic)}
            clippingPlanes={clippingPlanes}
          />
        </mesh>
      </group>
    );
  }
  return (
    <>
      <mesh
        geometry={geometry}
        position={position}
        rotation={node.rotation}
        castShadow
        receiveShadow
      >
        {/* C2VD V1 勘正：clippingPlanes 归材质级——旧版摊在 mesh 级系
            R3F 静默无效（无转发——expanda 落空），半剖/§12.3 主视图剖切
            对本组件从未生效；接通后缩略图近壁真剖+帽盖可见性成立。
            C2VD V3：polygonOffset 后推表面——共面棱线（EdgesGeometry
            与本体同深度）深度竞争稳定胜出（先例=z-fighting 消隐 flaky
            实录：同码两轮可见两轮不可见——GPU 深度并列裁决不稳定）。 */}
        <meshStandardMaterial
          color={semanticColor(node.semantic)}
          clippingPlanes={clippingPlanes}
          polygonOffset={edges}
          polygonOffsetFactor={1}
          polygonOffsetUnits={1}
        />
      </mesh>
      {edges && edgeGeometry !== null && edgeColor !== null ? (
        <lineSegments geometry={edgeGeometry} position={position} rotation={node.rotation}>
          <lineBasicMaterial color={edgeColor} clippingPlanes={clippingPlanes} />
        </lineSegments>
      ) : null}
    </>
  );
}
