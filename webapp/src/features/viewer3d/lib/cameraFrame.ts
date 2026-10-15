/**
 * 取景机位纯函数（v2-20261015 笔5 自 Scene.tsx 169-195 cameraPosition 拆迁
 * ——制式改 AABB 投影紧致拟合，替代对角线×1.25 包围球制式：宽扁厂区场景
 * 机位距离按视锥实际需要的半延展求值，模型簇不再偏远）。
 *
 * 输入:  preset（iso/top/side）+bounds（取景 AABB——Scene effective bounds；
 *        null=空场景）+aspect（画布宽高比——CameraRig 自 useThree size 取；
 *        非有限/≤0 回退 1——R1-W1 纯函数层钳位）
 * 输出:  {position, center}——position=机位（center+方向×距离）；center=
 *        取景中心（bounds AABB 中心；空场景=原点——零场景零尺度基准沿
 *        sceneCenter 先例）；空场景回退 preset 方向绝对坐标（制式不变）
 */
import type { SceneBounds } from "./projectScene";

/** 相机档位键（store CameraPreset 同值域——纯函数零 store 依赖）。 */
export type CameraPresetKey = "iso" | "top" | "side";

/** 三 preset 方向（C2-3d V4 呈裁④：iso 俯角 30/top 近俯视微倾防正射退化
 *  （(0,60,1) 非纯竖直——OrbitControls up 轴退化防线）/side 侧视）。 */
const CAMERA_PRESETS: Record<CameraPresetKey, readonly [number, number, number]> = {
  iso: [30, 30, 30],
  top: [0, 60, 1],
  side: [40, 5, 0],
};

/** 垂直视场角（Scene Canvas fov 消费单源——投影三角半角 25°；R1-N2 导出）。 */
export const V_FOV_DEG = 50;

/** 紧致拟合余量（全盒入画安全边——拟合距离上浮 15%）。 */
const MARGIN = 1.15;

type Vec3 = readonly [number, number, number];

const dot3 = (a: Vec3, b: Vec3): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

const cross3 = (a: Vec3, b: Vec3): [number, number, number] => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

/** 单位化（零向量回退 fallback——防 NaN 面）。 */
function normalize3(v: Vec3, fallback: Vec3): [number, number, number] {
  const length = Math.hypot(v[0], v[1], v[2]);
  if (length === 0) {
    return [fallback[0], fallback[1], fallback[2]];
  }
  return [v[0] / length, v[1] / length, v[2] / length];
}

/** AABB 投影半延展（Σ e_i·|axis_i|——保守支撑半径）。 */
function projectedExtent(e: Vec3, axis: Vec3): number {
  return (
    e[0] * Math.abs(axis[0]) + e[1] * Math.abs(axis[1]) + e[2] * Math.abs(axis[2])
  );
}

/**
 * 紧致取景（v2 笔5）：半延展 e=ext/2；视线方向 dir=preset 方向归一；
 * right=normalize(cross(dir, up))（up=(0,1,0)）；相机竖屏轴 yAxis=
 * cross(dir, right)；extU/extR=AABB 沿 yAxis/right 的投影半延展；
 * fitting=max(extU/tan(vFov/2), extR/(tan(vFov/2)·aspect))×1.15（margin）；
 * distance=fitting+extD——extD=Σe_i·|dir_i| 深度支撑半径。
 * D5 公式两处修正项（批档自裁申报在案——冻结式过不了自身 NDC 验收线）：
 * ①extU 沿相机 yAxis 而非世界 up（俯仰/俯视机位两轴不重合——top 视景
 * 屏竖向实为 Z 延展非 Y 延展，沿世界 up 计会把屏竖向算小一个量级）；
 * ②深度项 extD（透视下近侧角比中心更近、角宽更大，仅按中心深度拟合
 * 在宽扁盒上八角 NDC 溢出视口且最近角可深度为负——golden 形态实测
 * NDC 达 1.26~1.49）。
 */
export function frameCamera(
  preset: CameraPresetKey,
  bounds: SceneBounds | null,
  aspect: number,
): { position: [number, number, number]; center: [number, number, number] } {
  // aspect 守卫（R1-W1）：非有限（NaN/Infinity）或 ≤0 回退 1（纯函数层
  // 钳位——除零/负宽高比面不入距离公式）
  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? aspect : 1;
  const direction = CAMERA_PRESETS[preset];
  if (bounds === null) {
    return { position: [direction[0], direction[1], direction[2]], center: [0, 0, 0] };
  }
  const center: [number, number, number] = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
  const dir = normalize3(direction, [0, 1, 0]);
  const up: Vec3 = [0, 1, 0];
  // 右向=视线×世界 up（top 微倾保证非零——正射退化防线）
  const right = normalize3(cross3(dir, up), [1, 0, 0]);
  // 相机竖屏轴（lookAt 基 y=z×x——与 right/dir 构成正交右手系）
  const yAxis = cross3(dir, right);
  const e: Vec3 = [
    (bounds.max[0] - bounds.min[0]) / 2,
    (bounds.max[1] - bounds.min[1]) / 2,
    (bounds.max[2] - bounds.min[2]) / 2,
  ];
  const tanHalf = Math.tan(((V_FOV_DEG / 2) * Math.PI) / 180);
  const extU = projectedExtent(e, yAxis);
  const extR = projectedExtent(e, right);
  const fitting = Math.max(extU / tanHalf, extR / (tanHalf * safeAspect)) * MARGIN;
  const distance = fitting + projectedExtent(e, dir);
  return {
    position: [
      center[0] + dir[0] * distance,
      center[1] + dir[1] * distance,
      center[2] + dir[2] * distance,
    ],
    center,
  };
}
