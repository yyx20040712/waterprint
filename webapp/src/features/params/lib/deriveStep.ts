/**
 * 缺省步长单源（PD8）：(max-min)/10——同时服务 ①ParamForm InputNumber
 * 箭头步进 ②FD 可行域轴缺省 step（core solution/design_map.py
 * derive_step 同式同注释——跨语言黄金值用例互锁：同一 range→同一
 * step 期望，防 Python/JS 派生漂移；core 侧 tests/solution/
 * test_design_map.py _GOLDEN_STEPS 与本件用例共享值）。
 *
 * 输入:  range 形状 {min,max}（META1 目录条目面——orval 可选归一后）
 *        /ParamEntry 形状 {grid?,range?}（isContinuousParam 消费面）
 * 输出:  deriveStep=缺省步长 number（11 档指引粒度 /10——宪法白名单数
 *        10；用户可在 FD 面板轴声明覆盖 step，仅影响 ②不影响 ①——
 *        InputNumber 键盘任意值不限，箭头增量恒派生值，P0-4 概念锁定）
 *        /isContinuousParam=boolean（PD7 入口精确条件：grid 缺席且
 *        range 在场——93 连续区间参数判定，undefined 归一 null 同判）
 */
export function deriveStep(range: { min: number; max: number }): number {
  return (range.max - range.min) / 10;
}

/** 连续区间参数判定（PD7 入口精确条件）：grid 缺席且 range 在场
 * （orval 生成面 grid/range 均可选——undefined 归一 null 同判）。 */
export function isContinuousParam(entry: {
  grid?: unknown;
  range?: { min: number; max: number } | null;
}): boolean {
  return (entry.range ?? null) !== null && (entry.grid ?? null) === null;
}
