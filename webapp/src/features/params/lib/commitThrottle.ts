/**
 * 失焦连跳提交节流（B2 P3 V10——任务书 §二.⑦.5：ParamForm 失焦自动提交
 * 多任务连发代价——连发合并裁量；M1 缺省路径零消费=零行为变）。
 *
 * 输入:  fire 回调（提交通道——载荷在闭包侧取时点最新态）
 * 输出:  createCommitThrottle → { schedule, cancel }——leading 即发+
 *        trailing 合并尾发（窗内连发合并为一次最新载荷尾发）
 *
 * 规格说明（B2 任务书 §二.⑦.5——执行者定形落批档）：
 *   - 定形=连发合并（leading+trailing 节流而非防抖）：首调零延迟即发
 *     （工程师失焦即生效期望——三式提交语义不延迟）；窗内后续连发合并
 *     为一次尾发（最新载荷——中间草稿不逐任务提交，多任务连发代价
 *     N→≤2）；窗 1500ms（快速多字段连编典型间隔内合并）；
 *   - 消费面=ParamForm 失焦通道（commitOnBlurAndEnter 门内——v4 左栏）；
 *     Enter/按钮通道=显式意图不走节流（即时提交）；M1 缺省门关=零消费；
 *   - 卸载语义=flush（R1 W-V10：挂尾立即发——「失焦即提交」承诺窗内不
 *     损；旧 cancel 静默丢就此废止；cancel 保留给显式取消面）。
 */

/** 节流窗（ms——leading+trailing 合并窗）。 */
export const V10_COMMIT_WINDOW_MS = 1500;

/** 节流器句柄（fire 闭包侧持有时点最新态——本件零载荷面）。 */
export type CommitThrottle = {
  /** 提交通道（静默窗首调即发；窗内连发挂尾合并）。 */
  schedule: (fire: () => void) => void;
  /** 尾发立即执行（R1 W-V10 卸载面——挂尾不静默丢：timer 清+最新载荷
   *  即发；无挂尾=零动作幂等）。 */
  flush: () => void;
  /** 尾发消解（timer 清+挂尾丢弃——显式取消语义；卸载面用 flush）。 */
  cancel: () => void;
};

export function createCommitThrottle(options?: {
  windowMs?: number;
  setTimer?: (fn: () => void, ms: number) => ReturnType<typeof setTimeout>;
  clearTimer?: (id: ReturnType<typeof setTimeout>) => void;
}): CommitThrottle {
  const windowMs = options?.windowMs ?? V10_COMMIT_WINDOW_MS;
  // globalThis 面（node 直测无 window——浏览器/jsdom 同源全局）
  const setTimer = options?.setTimer ?? ((fn: () => void, ms: number) => setTimeout(fn, ms));
  const clearTimer = options?.clearTimer ?? ((id: ReturnType<typeof setTimeout>) => clearTimeout(id));
  let lastFireAt: number | null = null;
  let pendingFire: (() => void) | null = null;
  let timerId: ReturnType<typeof setTimeout> | null = null;

  const fireNow = (fire: () => void) => {
    lastFireAt = Date.now();
    fire();
  };

  const fireTrailing = () => {
    timerId = null;
    const fire = pendingFire;
    pendingFire = null;
    if (fire !== null) {
      fireNow(fire);
    }
  };

  return {
    schedule: (fire: () => void) => {
      const now = Date.now();
      if (lastFireAt === null || now - lastFireAt >= windowMs) {
        fireNow(fire); // leading：静默窗首调零延迟即发
        return;
      }
      // 窗内：挂尾（最新载荷覆盖中间载荷——连发合并）
      pendingFire = fire;
      if (timerId === null) {
        timerId = setTimer(fireTrailing, windowMs - (now - lastFireAt));
      }
    },
    flush: () => {
      if (timerId !== null) {
        clearTimer(timerId);
        timerId = null;
      }
      fireTrailing(); // 挂尾即发（无挂尾=零动作——pendingFire null 早退）
    },
    cancel: () => {
      if (timerId !== null) {
        clearTimer(timerId);
        timerId = null;
      }
      pendingFire = null;
    },
  };
}
