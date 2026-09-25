/**
 * 会话历史退避重试（F2 B-1——首轮竞态 502 兜底）：history 失败且会话刚
 * 创建（本轮 POST 已返回、freshSessionId 命中）时的 500ms 起指数退避
 * refetch 调度器（工单 e2e-fix-round3-2026-09-25 §1 B-1）。
 *
 * 输入:  pending（重试条件布尔——消费方以「isError 且 freshSessionId 命中」
 *        汇出）+refetch（react-query history 查询句柄——退避到期触发）
 * 输出:  useHistoryRetry 调度 hook（500/1000/2000ms 三梯定时链自持，耗尽
 *        即停——两态文案渲染归 ChatPanel）+nextHistoryRetryDelayMs 纯函数
 *        （vitest 直测面）+HISTORY_RETRY_* 常量
 *
 * 规格说明：
 *   - 退避梯：500ms 起指数 ×3（500/1000/2000）——工单 B-1 口径；refetch
 *     落定（成败同）续排下一梯，三梯耗尽即停（禁无限静默重试——耗尽态
 *     文案归 ChatPanel「会话尚未落盘」分支，非吞错）；
 *   - 成功即停：pending 翻 false（错误解除/会话切换）→ effect 收卸截断
 *     在途定时链；新一轮竞态（pending 再真）重走全梯；
 *   - effect 单次装配：定时链在 effect 闭包内自持（refetch 句柄 react-query
 *     稳定身份——渲染抖动不重启梯）；refetch 承诺拒绝同续排（react-query
 *     refetch 恒落定，防御面兜底 502 reject 形态）。
 */
import { useEffect } from "react";

/** 退避梯基数（B-1：500ms 起指数——工单 e2e-fix-round3 §1 B-1）。 */
export const HISTORY_RETRY_BASE_MS = 500;
/** 重试梯数上限（三梯耗尽即停）。 */
export const HISTORY_RETRY_MAX = 3;

/** 指数退避延迟（纯函数——500/1000/2000ms）。 */
export function nextHistoryRetryDelayMs(retries: number): number {
  return HISTORY_RETRY_BASE_MS * 2 ** retries;
}

/** 历史读取退避重试调度（pending 期三梯 refetch；条件解除即截断清零）。 */
export function useHistoryRetry(pending: boolean, refetch: () => Promise<unknown>): void {
  useEffect(() => {
    if (!pending) {
      return; // 无重试条件——链不装配（在途链随上一 effect 收卸截断）
    }
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const attempt = (n: number) => {
      if (cancelled || n >= HISTORY_RETRY_MAX) {
        return; // 耗尽即停（两态文案归 ChatPanel 渲染面）
      }
      timer = setTimeout(() => {
        // 落定即续排（成功则 pending 翻 false→cleanup 截断链；拒绝同续排
        // ——502 reject 形态防御面，禁 unhandled rejection）
        void refetch().then(
          () => attempt(n + 1),
          () => attempt(n + 1),
        );
      }, nextHistoryRetryDelayMs(n));
    };
    attempt(0);
    return () => {
      cancelled = true;
      if (timer !== null) {
        clearTimeout(timer);
      }
    };
  }, [pending, refetch]);
}
