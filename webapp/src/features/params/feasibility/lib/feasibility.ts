/**
 * 可行域纯函数层（PD7）：吸附边界/回填格式化/1D 值定位/2D 最近可行格。
 *
 * 输入:  DesignMap 产物字段（segments/mask/axis_values——orval 生成类型）
 *        + 用户点击/当前值
 * 输出:  snapToBoundary（不可行值→最近可行段边界）/formatBackfill
 *        （number→草稿串）/valueAtRatio（条位→值）/nearestFeasibleCell
 *        （2D 点击→最近可行格值对）——零 React 零 antd（node 直测）
 *
 * 规格说明（FD 批 PD7 终裁 2026-09-09，P0-3 交互流）：
 *   - 不可行区点击=吸附最近可行段边界回填（引导行为——静默无响应弃）；
 *     值已可行=原值回填；无可行段=null（调用方诚实呈现，不编造）；
 *   - 等距并列取先段下界（确定性——首段优先，与 core widest 同精神）；
 *   - formatBackfill=String(number)（draft 通道既有形态——apply payload
 *     键零漂移，PD7 回填条款）；
 *   - 2D 最近可行格=数据空间欧氏距离最小格（等距取先行序——确定性）。
 */

/** 可行段类型（orval DesignSegment 同形——{start,end}）。 */
export type Segment = { start: number; end: number };

/**
 * 吸附最近可行段边界（PD7 终裁）：值在段内=原值；段外=最近边界；
 * 无可行段=null。等距并列取先段（确定性）。
 */
export function snapToBoundary(value: number, segments: Segment[]): number | null {
  if (segments.length === 0) {
    return null;
  }
  let best: number | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const segment of segments) {
    if (value >= segment.start && value <= segment.end) {
      return value; // 段内=可行原值
    }
    for (const boundary of [segment.start, segment.end]) {
      const distance = Math.abs(boundary - value);
      if (distance < bestDistance) {
        bestDistance = distance;
        best = boundary;
      }
    }
  }
  return best;
}

/** 回填格式化：number→draft 串（String 形态——既有草稿通道零漂移）。 */
export function formatBackfill(value: number): string {
  return String(value);
}

/** 1D 条位定位：比例（0~1）→轴值域线性值（越界钳制到端点）。 */
export function valueAtRatio(
  ratio: number,
  values: number[],
): number | null {
  const low = values[0];
  const high = values[values.length - 1];
  if (low === undefined || high === undefined) {
    return null;
  }
  const clamped = Math.min(1, Math.max(0, ratio));
  return low + clamped * (high - low);
}

/** 值→1D 可行判定（段内真；空段恒假）。 */
export function isFeasibleValue(value: number, segments: Segment[]): boolean {
  return segments.some((s) => value >= s.start && value <= s.end);
}

/**
 * 2D 最近可行格（PD7 吸附泛化）：数据空间欧氏距离最小的可行格值对；
 * 无可行格=null（诚实缺省）。等距取先行序（row-major 先见者胜——确定性）。
 */
export function nearestFeasibleCell(
  valueA: number,
  valueB: number,
  valuesA: number[],
  valuesB: number[],
  mask: number[][],
): { a: number; b: number } | null {
  let best: { a: number; b: number } | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (let i = 0; i < valuesA.length; i += 1) {
    const row = mask[i] ?? [];
    for (let j = 0; j < valuesB.length; j += 1) {
      if (row[j] !== 1) {
        continue;
      }
      const candidateA = valuesA[i];
      const candidateB = valuesB[j];
      if (candidateA === undefined || candidateB === undefined) {
        continue; // 防御面：值列与掩码长度漂移（生成物一致性由 server 锁）
      }
      const distance =
        (candidateA - valueA) ** 2 + (candidateB - valueB) ** 2;
      if (distance < bestDistance) {
        bestDistance = distance;
        best = { a: candidateA, b: candidateB };
      }
    }
  }
  return best;
}
