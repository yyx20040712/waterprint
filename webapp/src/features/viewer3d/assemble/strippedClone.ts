/**
 * inst 原型克隆剥离（段二——门二 P0 修复面单源）。
 *
 * 输入:  glTF 加载的原型节点（含 meshopt 量化补偿 TRS）
 * 输出:  克隆（position 归零——布局位=绝对模板位·几何中心语义）
 *
 * 规格：**只清 position，保留 rotation/scale**——meshopt 量化把几何
 *   归一化到单位盒、节点 TRS scale 承载尺寸恢复（连 scale 剥=7m 桁架
 *   渲成 2m 盒——门二 P0 实录）；量化网格原点≈几何 AABB 中心，布局
 *   y 锚同取中心（instanceLayout cy）——单偏移无半高差。
 */

import * as THREE from "three";

export function strippedClone(object: THREE.Object3D): THREE.Object3D {
  const clone = object.clone();
  clone.position.set(0, 0, 0);
  return clone;
}
