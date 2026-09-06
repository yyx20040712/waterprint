/**
 * 任务事件流订阅：EventSource 自建薄壳（D2——SSE 不走 customInstance）。
 *
 * 输入:  taskId（URL ?task= 消费——null 不建连）+onTerminal 终态回调
 *        +onConnection 连接态回调（B7 D3——可选三态通知通道）
 * 输出:  TaskView|null（SSE 事件归约视图——null=尚未收到事件；事件解析/
 *        归约纯函数在 lib/taskFeed.ts，本壳只持连接生命周期）+
 *        nextReconnectDelayMs/planRecovery（重连治理纯函数——vitest 面）
 *
 * 规格说明（FE6 批 6b 段四 D2；B6 批 D3/D8 2026-09-06 增补）：
 *   - 挂载即 new EventSource(`/api/events/tasks/${taskId}`)；服务端终态
 *     任务连接即发一条快照 state 事件后收流（manager.py）——单一 SSE
 *     通道即可，不加轮询；
 *   - token 拼接走 shared/api/sseUrl.buildTaskStreamUrl 单源（B6 D8 下沉：
 *     useExportBatch 双实现收敛；参数名 token 对齐 server auth.py
 *     sseTokenQuery 双通道）；header 通道 EventSource 不可用=查询参数是
 *     唯一通道；
 *   - B6 D3（401 重连风暴治理——本批增补）：onerror 无 status 可读面，
 *     计数制同构覆盖 401/429/网络抖动三态——onerror 即 close()（夺回
 *     浏览器内建无限重连的控制权）→连续失败 n 次指数退避重建（1s/
 *     2s/4s…封顶 30s，nextReconnectDelayMs）；连续失败达上限 5 次→
 *     置错误态停连（不再激进重连）→60s 慢速周期探测自动恢复
 *     （planRecovery——零手动干预）；任何事件到达（state/progress/
 *     stale）=链路恢复，失败计数归零；错误态期间数据停更（视图保持
 *     末次快照——恢复语义由慢探测承载，「连接中断自动重连中」UI
 *     提示面归消费方，薄壳不改返回形态）；
 *   - 事件三类 addEventListener（state/progress/stale——Event 命名事件
 *     不走 onmessage 默认面）；畸形 data 经 lib 解析拒 null 静默丢弃；
 *   - 终态（done/cancelled/failed）即 es.close()+onTerminal 回调——不
 *     close 会因服务端关流触发浏览器自动重连（快照→关流→重连→快照
 *     死循环）；卸载即 close+清退避定时器（disposed 守卫——卸载后
 *     定时器不复活连接）；taskId 变更重建（视图重置）；
 *   - onTerminal 经 ref 透传——回调引用变更不重建连接（taskId 单依赖）；
 *   - 服务端 B6 心跳（": keepalive" comment 行）被 EventSource 忽略——
 *     长静默不断流，退避计数不受其扰动（D6）；
 *   - 时间逻辑纯函数化（nextReconnectDelayMs/planRecovery）——vitest
 *     直测，壳内零 fake timers 依赖（薄壳不测先例维持）；
 *   - B7 D3（onConnection 连接态通道——2026-09-06 增补）：第三可选参
 *     三态通知（'reconnecting'=退避重建期/'probing'=达限 60s 慢探测期/
 *     'ok'=降级后重建连接成功）——onerror 内 failures 递增后按
 *     planRecovery.mode 发 reconnecting（backoff）/probing（probe）；
 *     ok=重建连接 onopen 且 failures>0（transport 级真信号口径：服务端
 *     事件不重放历史+心跳为 EventSource 忽略的 comment 行——稀疏流下
 *     首事件不可靠，onopen 才是连接恢复真信号；首连接 failures=0 不发
 *     =零噪音）。回调经 ref 透传（沿 onTerminal——不入依赖数组）；
 *     **failures 归零语义不动**（仍仅任何事件到达归零——仅增通知通道，
 *     不改 B6 D3 状态机：ok 不复位计数，恢复后再断连按余计数续走）；
 *   - B7 D5：SSE_FAILURE_LIMIT 迁 shared/api/sseConstants 单源
 *     （useExportBatch 双源同值收敛——本地导出面不再保留）。
 */
import { useEffect, useRef, useState } from "react";

import { getApiToken } from "../../../shared/api/token";
import { buildTaskStreamUrl } from "../../../shared/api/sseUrl";
import { SSE_FAILURE_LIMIT } from "../../../shared/api/sseConstants";
import {
  isTerminalState,
  parseEventData,
  reduceTaskEvent,
  type TaskView,
} from "../lib/taskFeed";

/** 退避梯（B6 D3）：1s 基数指数增长，封顶 30s（失败序数 1 起步）。 */
export const SSE_RECONNECT_BASE_MS = 1000;
export const SSE_RECONNECT_CAP_MS = 30 * 1000;
/** 停连后慢速周期探测间隔（60s——自动恢复通道，B6 D3 必改4）。 */
export const SSE_PROBE_INTERVAL_MS = 60 * 1000;

/** 指数退避延迟（纯函数——1s/2s/4s/8s/16s…封顶 30s）。 */
export function nextReconnectDelayMs(failures: number): number {
  const ladder = Math.min(
    SSE_RECONNECT_BASE_MS * 2 ** (failures - 1),
    SSE_RECONNECT_CAP_MS,
  );
  return Math.max(ladder, SSE_RECONNECT_BASE_MS);
}

/** 重连计划（纯函数）：未达上限=指数退避；达上限=60s 慢探测（错误态）。 */
export function planRecovery(failures: number): { mode: "backoff" | "probe"; delayMs: number } {
  if (failures < SSE_FAILURE_LIMIT) {
    return { mode: "backoff", delayMs: nextReconnectDelayMs(failures) };
  }
  return { mode: "probe", delayMs: SSE_PROBE_INTERVAL_MS };
}

/** 任务事件流订阅（返回归约视图——null=taskId 空或尚未收到事件）。 */
export function useTaskFeed(
  taskId: string | null,
  onTerminal?: (state: string) => void,
  onConnection?: (state: "reconnecting" | "probing" | "ok") => void,
): TaskView | null {
  const [view, setView] = useState<TaskView | null>(null);
  // 终态回调经 ref 透传（taskId 单依赖——回调引用变更不重建连接）
  const onTerminalRef = useRef(onTerminal);
  onTerminalRef.current = onTerminal;
  // B7 D3：连接态回调同款 ref 透传（不入依赖数组）
  const onConnectionRef = useRef(onConnection);
  onConnectionRef.current = onConnection;

  useEffect(() => {
    setView(null); // 任务切换视图重置（null 面同走重置）
    if (taskId === null) {
      return;
    }
    let failures = 0; // 连续失败计数（任何事件到达即归零——链路恢复）
    let source: EventSource | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let disposed = false;

    const connect = () => {
      if (disposed) {
        return; // 卸载后定时器不复活连接
      }
      // token 连接级现取（重连时重建——设置页保存对下一次重连即时生效）
      const next = new EventSource(buildTaskStreamUrl(taskId, getApiToken()));
      source = next;
      const consume = (event: MessageEvent) => {
        const parsed = parseEventData(
          typeof event.data === "string" ? event.data : "",
        );
        if (parsed === null) {
          return; // 畸形 data 静默丢弃（lib 拒 null——不崩流）
        }
        failures = 0; // 事件到达=链路健康（B6 D3 恢复语义）
        setView((prev) => reduceTaskEvent(prev, parsed));
        if (
          parsed.type === "state" &&
          parsed.message !== null &&
          isTerminalState(parsed.message)
        ) {
          // 终态即收流：close 阻断自动重连循环（服务端发快照后关流）
          next.close();
          onTerminalRef.current?.(parsed.message);
        }
      };
      next.addEventListener("state", consume as EventListener);
      next.addEventListener("progress", consume as EventListener);
      next.addEventListener("stale", consume as EventListener);
      // B7 D3：ok=重建连接且此前降级（failures>0）——首连接 open 零噪音
      // （onopen 是 transport 级真信号；failures 归零仍仅由事件到达承载）。
      next.onopen = () => {
        if (failures > 0) {
          onConnectionRef.current?.("ok");
        }
      };
      next.onerror = () => {
        // B6 D3：onerror 无 status 面——401/429/网络抖动同构计数覆盖。
        // close 夺回控制权（弃用浏览器内建无限重连），按计划退避/慢探测。
        next.close();
        failures += 1;
        const plan = planRecovery(failures);
        // B7 D3：连接态通知（backoff 期=reconnecting/达限慢探测=probing）
        onConnectionRef.current?.(plan.mode === "probe" ? "probing" : "reconnecting");
        timer = setTimeout(connect, plan.delayMs);
      };
    };

    connect();
    return () => {
      // 卸载即清理（无泄漏句柄——连接+退避定时器双收口）
      disposed = true;
      if (timer !== null) {
        clearTimeout(timer);
      }
      source?.close();
    };
  }, [taskId]);

  return view;
}
