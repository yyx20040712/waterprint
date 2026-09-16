/**
 * C2-3d V1/V2 地面/网格/灯位数据派生（Scene 抽离件——500 行预算门）。
 *
 * 输入:  RenderScene.bounds（全 placements∪红线 AABB——空场景=null）
 * 输出:  GroundPlan（地面尺寸/分层格数/中心/对角线——V2 灯位/阴影/雾
 *        全 bounds 派生数据锚）或 null（零场景零尺度基准沿 sceneCenter
 *        先例——地面/雾/灯位适配面全不挂）
 *
 * 规格说明（C2-3d V1/V2；Scene.tsx 2026-09-13 原位迁移零逻辑变更）：
 *   - 主格 10m：总尺寸=最大边×3.2 向上取整到 10m 倍数（gridHelper 中心
 *     对称布格——奇偶格数均可；3.2=由 2.2 调档至 3.2，雾远缘 3.2×
 *     对角同档淡出余量）；
 *   - 对角线驱动：V2 阴影正交相机半幅=对角线×0.75（灯位/阴影覆盖随
 *     场景）。
 */
import type { Vec3 } from "../assemble/types";

export type GroundPlan = {
  readonly size: number;
  readonly majorDivisions: number;
  readonly minorDivisions: number;
  readonly centerX: number;
  readonly centerZ: number;
  readonly diagonal: number;
};

export function groundPlan(
  bounds: { readonly min: Vec3; readonly max: Vec3 } | null,
): GroundPlan | null {
  if (bounds === null) {
    return null;
  }
  const sizeX = bounds.max[0] - bounds.min[0];
  const sizeZ = bounds.max[2] - bounds.min[2];
  const span = Math.max(sizeX, sizeZ, 10);
  const size = Math.ceil((span * 3.2) / 10) * 10;
  return {
    size,
    majorDivisions: size / 10,
    minorDivisions: size / 2,
    centerX: (bounds.min[0] + bounds.max[0]) / 2,
    centerZ: (bounds.min[2] + bounds.max[2]) / 2,
    diagonal: Math.hypot(sizeX, bounds.max[1] - bounds.min[1], sizeZ),
  };
}
