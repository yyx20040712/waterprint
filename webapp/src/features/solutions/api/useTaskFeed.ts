/**
 * 任务事件流订阅：事件归约薄壳（D2——SSE 不走 customInstance）。
 *
 * 输入:  taskId（URL ?task= 消费——null 不建连）+onTerminal 终态回调
 *        +onConnection 连接态回调（B7 D3——可选三态通知通道）
 * 输出:  TaskView|null（SSE 事件归约视图——null=taskId 空或尚未收到事件；
 *        事件解析/归约纯函数在 lib/taskFeed.ts）
 *
 * 规格说明（B3-b 生命周期收敛后形态）：EventSource 生命周期（建连/三命名
 * 事件/终态 close/退避/慢探测恢复/卸载清理）已迁 shared/api/
 * useTaskEventSource 单源（原双实现 useTaskFeed/useExportBatch 收敛——《裁决书》
 * 方案二 2b；治理决策史 B6 D3/D8、B7 D3/D5 见该件头注）；本壳=归约注入：
 * parseEventData 畸形拒 null→drop（不计链路健康）/合法事件 reduceTaskEvent
 * 进 view→event/state 终态（isTerminalState）→terminal（内核随 Reading
 * close 本流+转 onTerminal）。taskId 变更视图重置（null 面同走重置——
 * 生命周期重建由内核 taskId 单依赖承载）；interpret 闭包内联捕获 setView
 * （useState 稳定引用；内核经 ref 现读——闭包逐渲染重建无碍）。onTerminal/
 * onConnection 经 ref 透传语义由内核统一承载。
 *
 * 公开面稳定（消费方 import 零改动——executor/exports_support 再导出
 * 先例同旨）：ConnectionState 类型+重连纯函数族（nextReconnectDelayMs/
 * planRecovery/SSE_RECONNECT_*）自 shared 单源再导出（solutionsPane/
 * TaskPanel/useTaskFeed.test 既有 import 面不变）。
 */
import { useEffect, useState } from "react";

import {
  type ConnectionState,
  type TaskEventInterpreter,
  useTaskEventSource,
} from "../../../shared/api/useTaskEventSource";
import {
  isTerminalState,
  parseEventData,
  reduceTaskEvent,
  type TaskView,
} from "../lib/taskFeed";

// 再导出保公开面（B3-b 迁 shared 单源——消费方 import 零改动）
export {
  SSE_RECONNECT_BASE_MS,
  SSE_RECONNECT_CAP_MS,
  SSE_PROBE_INTERVAL_MS,
} from "../../../shared/api/useTaskEventSource";
export type { ConnectionState } from "../../../shared/api/useTaskEventSource";
export { nextReconnectDelayMs, planRecovery } from "../../../shared/api/useTaskEventSource";

/** 任务事件流订阅（返回归约视图——null=taskId 空或尚未收到事件）。 */
export function useTaskFeed(
  taskId: string | null,
  onTerminal?: (state: string) => void,
  onConnection?: (state: ConnectionState) => void,
): TaskView | null {
  const [view, setView] = useState<TaskView | null>(null);
  // 归约注入（生命周期内核的解读协议适配——lib 纯函数消费面；闭包捕获
  // setView 稳定引用，内核 interpretRef 现读逐渲染新闭包）
  const interpret: TaskEventInterpreter = (data) => {
    const parsed = parseEventData(data);
    if (parsed === null) {
      return { kind: "drop" }; // 畸形 data 丢弃（lib 拒 null——不崩流、不计健康）
    }
    setView((prev) => reduceTaskEvent(prev, parsed));
    if (
      parsed.type === "state" &&
      parsed.message !== null &&
      isTerminalState(parsed.message)
    ) {
      return { kind: "terminal", state: parsed.message };
    }
    return { kind: "event" };
  };
  // 任务切换视图重置（null 面同走重置——先于内核连接 effect 执行，
  // 与原单体 effect「重置后建连」序一致；生命周期重建由内核承载）
  useEffect(() => {
    setView(null);
  }, [taskId]);
  useTaskEventSource(taskId, interpret, onTerminal, onConnection);
  return view;
}
