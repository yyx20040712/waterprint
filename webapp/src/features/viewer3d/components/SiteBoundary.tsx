/**
 * 场地红线渲染器：闭合折线（LineLoop）——总装模式地面边界（L5b）。
 *
 * 输入:  BoundaryNode（投影层产出——世界水平面点序 [[x, z], …]，core 压平
 *        键 x{i}/y{i} 已在投影层解码并换轴（L5R：北=−Z——组件层零轴知识）；
 *        闭合段末点→首点由本层 LineLoop 补——core 顶点序即权威）
 * 输出:  R3F 闭合折线（boundary 语义色——SC1 起与 siteplan 同源消费
 *        shared/ui/semanticColors.ts 真源表，字面平行拷贝已收编）
 *
 * 规格说明（L5b 总装模式 2026-09-03；L5R 换轴随行；SC1 语义色真源化）：
 *   - 世界 (x, z) → (x, 微抬, z)：Y-up 水平面=XZ，红线贴地零高度
 *     （core z=0 铁律）；微抬 0.02 防与地面图元深度冲突（渲染层类型化
 *     处理，非业务推导）；
 *   - 线材质不受光（lineBasicMaterial——红线为图示语义非实体）；
 *   - 组件薄壳零几何计算：点序直喂 BufferGeometry.setFromPoints。
 */
import { useEffect, useMemo } from "react";
import * as THREE from "three";

import { semanticColor } from "../../../shared/ui/semanticColors";

import type { BoundaryNode } from "../lib/projectScene";

/** 贴地微抬（米）——防与地面/池底图元深度冲突。 */
const BOUNDARY_LIFT_Y = 0.02;

export function SiteBoundary({ node }: { node: BoundaryNode }) {
  const geometry = useMemo(
    () =>
      new THREE.BufferGeometry().setFromPoints(
        node.points.map(
          ([x, z]) => new THREE.Vector3(x, BOUNDARY_LIFT_Y, z),
        ),
      ),
    [node.points],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <lineLoop geometry={geometry}>
      <lineBasicMaterial color={semanticColor("boundary")} />
    </lineLoop>
  );
}
