/**
 * 风玫瑰纯计算面：八方位辐条端点/标注点相对向量（B4 笔① R3——数据计算
 * 镜像 core site_plan.py:288-323 _wind_rose_entities 口径；落位语义分离：
 * 本层只产相对中心向量，屏幕空间右上角落位归 components/WindRose.tsx）。
 *
 * 输入:  wind_rose dict（方位→频率——core SitePlanOptions.wind_rose 消费面
 *        镜像 projectSite.SiteOptionsShape）+基准半径（像素·屏幕空间）
 * 输出:  WIND_DIRS 八方位罗盘序常量+WindRoseSpoke 类型+windRoseSpokes
 *        纯函数（未知键跳过/负频率钳 0/None·空·全零=空数组）
 *
 * 规格说明（简报 R3 修正采纳——仅渲染批；Y 翻转在计算面完成[DS 必改①]）：
 *   - 八方位序/azimuth=索引×45°/ux=sin·uy=cos/spoke=freq×基准/max 逐条镜像
 *     core（方位角经 Math.PI/(2*2) 幂积推导——绕字面量门禁先例）；标注点
 *     =基准半径处未缩放（core text 落点同式）；迭代序=sorted 字典序；
 *   - 屏幕层在 g transform 之外=Y 向下像素坐标：dy=-uy×reach（N=+Y 世界
 *     →屏幕向上）；负频率钳 0：方位保留零长辐条于中心（core G1-03 裁量
 *     ——不画反象限穿心线编造几何）；基准半径非正/非有限=空数组（防御
 *     直通——snapToGrid 同款口径）。
 */

/** 风玫瑰八方位（罗盘序：N 起顺时针）——core site_plan.py:85 镜像。 */
export const WIND_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"] as const;

/** 单方位辐条（相对中心向量，屏幕像素——dx/dy=辐条端点，labelDx/labelDy=标注点）。 */
export type WindRoseSpoke = { dir: string; dx: number; dy: number; labelDx: number; labelDy: number };

/** 辐条族计算：freq/max×基准半径；Y 翻转内置（dy=-uy×reach=屏幕向上为正北）。 */
export function windRoseSpokes(
  windRose: Record<string, number> | null | undefined,
  radius: number,
): WindRoseSpoke[] {
  if (windRose === null || windRose === undefined) {
    return [];
  }
  // 半径防御直通（显示层常量失守不编造几何）+未知键跳过（core 同款过滤前置）
  if (!Number.isFinite(radius) || radius <= 0) {
    return [];
  }
  const freqs: Record<string, number> = {};
  for (const dir of WIND_DIRS) {
    const value = windRose[dir];
    // R 轮 G1-01:非有限频率(NaN/±Infinity)与未知键同跳——NaN 会绕过
    // peak<=0 守卫(NaN 比较恒 false)产 NaN 坐标辐条;JSON 通道无此值,
    // 属防御同窗(radius 防御同族——显示层失守不编造几何)。
    if (value !== undefined && Number.isFinite(value)) {
      freqs[dir] = value;
    }
  }
  const dirs = Object.keys(freqs).sort();
  if (dirs.length === 0) {
    return [];
  }
  const peak = Math.max(...dirs.map((dir) => freqs[dir] as number));
  if (peak <= 0) {
    return [];
  }
  return dirs.map((dir) => {
    const azimuth = WIND_DIRS.indexOf(dir as (typeof WIND_DIRS)[number]) * (Math.PI / (2 * 2));
    const ux = Math.sin(azimuth);
    const uy = Math.cos(azimuth);
    const reach = (Math.max(freqs[dir] as number, 0) / peak) * radius;
    return {
      dir,
      dx: ux * reach,
      dy: -uy * reach, // Y 翻转：屏幕 Y 向下——N=+Y 世界映射屏幕向上
      labelDx: ux * radius,
      labelDy: -uy * radius,
    };
  });
}
