/**
 * 模板 inst 组布局（spec.md §11 S8/P7 裁定+P5 常量——批3 主体）。
 *
 * 输入:  原型节点 AABB（基座环位）+场景图 instance_count+壳缩放
 * 输出:  laid（逐实例位姿——模板本地系 anchor⊙s）或 skipped
 *        （无场景数量——不渲染+调用方登记 fallbackLog）
 *
 * 规格说明（P7 已裁：数量唯一真源=场景图 instance_count；禁由布置域÷
 *   间距常量推导[铁律 3 边界]。位姿=统一公式 σ=𝟙 形：p=anchor⊙s——
 *   立柱基座随壳缩放走（环半径/安装高度），几何恒定不缩[§3 instance
 *   行]；P5 间距常量（1.5m）=registry instanceSpacing 声明位——环上
 *   均布角距在典型尺寸近似该值，运行时零推导消费）。
 */

import type { Vec3 } from "./types";

export type InstanceLayoutResult =
  | { readonly kind: "laid"; readonly positions: readonly Vec3[] }
  | { readonly kind: "skipped"; readonly reason: "no_scene_count" };

/**
 * 环形均布（首实例角=原型基座角——原型位即 0 号位；σ=𝟙 位姿=anchor⊙s）。
 * count=null（场景图无数值）=skipped——P7：不渲染+登记，禁推导补数。
 */
export function instanceLayout(
  prototypeAabb: { readonly min: Vec3; readonly max: Vec3 },
  count: number | null,
  shell: Vec3,
): InstanceLayoutResult {
  if (count === null || !Number.isFinite(count) || count < 1) {
    return { kind: "skipped", reason: "no_scene_count" };
  }
  const cx = (prototypeAabb.min[0] + prototypeAabb.max[0]) / 2;
  const cz = (prototypeAabb.min[2] + prototypeAabb.max[2]) / 2;
  const radius = Math.hypot(cx, cz);
  const baseY = prototypeAabb.min[1];
  const theta0 = Math.atan2(cz, cx);
  const positions: Vec3[] = [];
  for (let i = 0; i < Math.floor(count); i += 1) {
    const theta = theta0 + (2 * Math.PI * i) / count;
    const anchorX = radius * Math.cos(theta);
    const anchorZ = radius * Math.sin(theta);
    // p=anchor⊙s（σ=𝟙——位姿随壳缩放走；0 分量归一防 −0 artifact）
    positions.push([
      anchorX === 0 ? 0 : anchorX * shell[0],
      baseY === 0 ? 0 : baseY * shell[1],
      anchorZ === 0 ? 0 : anchorZ * shell[2],
    ]);
  }
  return { kind: "laid", positions };
}
