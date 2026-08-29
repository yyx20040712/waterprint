/**
 * 任务事件流订阅：EventSource 自建薄壳（D2——SSE 不走 customInstance）。
 *
 * 输入:  taskId（URL ?task= 消费——null 不建连）+onTerminal 终态回调
 * 输出:  TaskView|null（SSE 事件归约视图——null=尚未收到事件；事件解析/
 *        归约纯函数在 lib/taskFeed.ts，本壳只持连接生命周期）
 *
 * 规格说明（FE6 批 6b 段四，D2；shared/api/http.ts:14 契约头冻结方向
 *   「SSE 订阅不走本实例（EventSource 直连 /api/events/*）」——生成
 *   useTaskEvents* 是 useQuery 一次性 JSON 读非流消费，不可用）：
 *   - 挂载即 new EventSource(`/api/events/tasks/${taskId}`)；服务端终态
 *     任务连接即发一条快照 state 事件后收流（manager.py:296-298）
 *     ——单一 SSE 通道即可，不加轮询；
 *   - 事件三类 addEventListener（state/progress/stale——Event 命名事件
 *     不走 onmessage 默认面）；畸形 data 经 lib 解析拒 null 静默丢弃；
 *   - 终态（done/cancelled/failed）即 es.close()+onTerminal 回调——不
 *     close 会因服务端关流触发浏览器自动重连（快照→关流→重连→快照
 *     死循环）；卸载即 close；taskId 变更重建（视图重置）；
 *   - onTerminal 经 ref 透传——回调引用变更不重建连接（taskId 单依赖）；
 *     连接层错误（网络断）交浏览器 EventSource 自动重连，不在壳内重试；
 *   - 薄壳不测（FE1 渲染器薄壳先例——jsdom 零新依赖红线）。
 */
import { useEffect, useRef, useState } from "react";

import {
  isTerminalState,
  parseEventData,
  reduceTaskEvent,
  type TaskView,
} from "../lib/taskFeed";

/** 任务事件流订阅（返回归约视图——null=taskId 空或尚未收到事件）。 */
export function useTaskFeed(
  taskId: string | null,
  onTerminal?: (state: string) => void,
): TaskView | null {
  const [view, setView] = useState<TaskView | null>(null);
  // 终态回调经 ref 透传（taskId 单依赖——回调引用变更不重建连接）
  const onTerminalRef = useRef(onTerminal);
  onTerminalRef.current = onTerminal;

  useEffect(() => {
    setView(null); // 任务切换视图重置（null 面同走重置）
    if (taskId === null) {
      return;
    }
    const source = new EventSource(
      // R4（zM-2）：taskId 源自 URL ?task=（用户可控）——路径段编码收口
      `/api/events/tasks/${encodeURIComponent(taskId)}`,
    );
    const consume = (event: MessageEvent) => {
      const parsed = parseEventData(
        typeof event.data === "string" ? event.data : "",
      );
      if (parsed === null) {
        return; // 畸形 data 静默丢弃（lib 拒 null——不崩流）
      }
      setView((prev) => reduceTaskEvent(prev, parsed));
      if (
        parsed.type === "state" &&
        parsed.message !== null &&
        isTerminalState(parsed.message)
      ) {
        // 终态即收流：close 阻断自动重连循环（服务端发快照后关流）
        source.close();
        onTerminalRef.current?.(parsed.message);
      }
    };
    source.addEventListener("state", consume as EventListener);
    source.addEventListener("progress", consume as EventListener);
    source.addEventListener("stale", consume as EventListener);
    return () => source.close(); // 卸载即清理（无泄漏句柄）
  }, [taskId]);

  return view;
}
