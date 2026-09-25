/**
 * 任务 SSE EventSource 生命周期单源（B3-b：《裁决书》方案二 2b——
 * useTaskFeed/useExportBatch 双实现收敛至此；事件解读注入归消费方，
 * 本件零业务分支）。
 *
 * 输入:  taskId（URL ?task= 消费——null 不建连）+事件解读纯回调
 *        interpret(data)（畸形丢弃/归约/终态判定归消费方）+onTerminal/
 *        onConnection 可选回调（经 ref 透传——引用变更不重建连接）
 * 输入:  taskId（URL ?task= 消费——null 不建连）+事件解读纯回调
 *        interpret(data)（畸形丢弃/归约/终态判定归消费方）+onTerminal/
 *        onConnection 可选回调（经 ref 透传——引用变更不重建连接）
 *        +probeTaskStatus 可选探测注入（F2 B-2 轮询兜底——默认
 *        probeTaskStatusTerminal 走既有任务状态端点）
 * 输出:  useTaskEventSource 长订阅 hook（退避/慢探测恢复态机+probing
 *        轮询兜底）+subscribeTaskEvents 命令面（一次性等待——浏览器内建
 *        自动重连保留，治理归消费方）+TaskEventReading 解读协议+重连纯
 *        函数族（nextReconnectDelayMs/planRecovery）+probeTaskStatusTerminal
 *        默认探测（vitest 经注入桩直测）
 *
 * 规格说明（生命周期语义自 useTaskFeed 原件逐行搬家——B6 D3/B7 D3/
 * B7 D5 治理决策全部随迁；消费方差异经解读协议注入不内聚）：
 *   - 两消费面：features 互不 import（§13.5 门禁），EventSource 生命周期
 *     （建连/三命名事件/终态 close/卸载清理）此前双实现同款复制——本件
 *     为唯一 new EventSource 处（B3-b 收敛；URL 经 sseUrl 单源+token
 *     连接级现取〔重连时重建——设置页保存对下一次重连即时生效〕）；
 *   - 解读协议 TaskEventReading：{kind:"drop"}=畸形 data 丢弃且不计链路
 *     健康（长订阅口径：畸形不证链路恢复）；{kind:"event"}=健康事件
 *     （失败计数归零）；{kind:"terminal",state}=终态（计数归零+内核
 *     close 本流〔阻断服务端终态关流触发的浏览器自动重连——快照→关流
 *     →重连→快照死循环〕+转 onTerminal）。命令面消费方（awaitTerminal
 *     先归零后解析口径）在 interpret 闭包内自持计数——本件不代管；
 *   - 长订阅 hook（useTaskFeed 形态）：onerror 即 close（夺回浏览器内建
 *     无限重连控制权）→连续失败 n 次指数退避重建（1s/2s/4s…封顶 30s）
 *     →达上限 SSE_FAILURE_LIMIT 置错误态停连→60s 慢速周期探测自动恢复
 *     （planRecovery——零手动干预）；onConnection 四态通知（'reconnecting'
 *     =退避重建期/'probing'=达限慢探测期/'ok'=降级后重建连接成功——
 *     onopen 且 failures>0，transport 级真信号口径：服务端事件不重放
 *     历史+心跳为 EventSource 忽略的 comment 行，稀疏流下首事件不可靠；
 *     首连接 failures=0 不发=零噪音；failures 归零仍仅由事件到达承载——
 *     ok 不复位计数，恢复后再断连按余计数续走；'polling'=F2 B-2 降级
 *     标记：慢探测连续 SSE_PROBE_FALLBACK_ROUNDS 轮无终态——实时通道
 *     不可达已切轮询兜底〔消费方 stage 行文案面〕）；taskId 变更重建；
 *     卸载即 close+清退避定时器（disposed 守卫——卸载后定时器不复活
 *     连接）；服务端心跳 comment 行被 EventSource 忽略——长静默不断流，
 *     退避计数不受其扰动；
 *   - F2 B-2 probing 轮询兜底：每个 probing 周期（达限转 60s 慢探测时）
 *     叠加一次任务状态轮询（probeTaskStatus 注入——默认实现走既有
 *     GET /api/calc/tasks/{task_id}，终态集 done/failed/cancelled 与解读
 *     协议 terminal 同集）；轮询得终态即按 SSE 终态同款收口（close 本流
 *     +清重连定时器+转 onTerminal——消费方 invalidate 同现有终态路径）
 *     且 finished 守卫停后续重连；无终态计轮，连续
 *     SSE_PROBE_FALLBACK_ROUNDS 轮 → onConnection('polling') 降级标记
 *     （恰一次/轮询续走不静默——健康事件到达归零重计）；探测失败=无
 *     答复（同无终态计轮，轮询通道持续可观测）；
 *   - 命令面（awaitTerminal 形态）：不治理 onerror（浏览器内建自动重连
 *     保留——一次性等待语义，连续失败计数/总时长超时归消费方）；
 *     onOpen/onError 透传（治理策略归消费方——退避重建 vs 达限拒绝是
 *     业务裁量非生命周期本体）；close 句柄幂等（重复 close 无害）；
 *   - 事件三类 addEventListener（state/progress/stale——Event 命名事件
 *     不走 onmessage 默认面）；事件解读含消费方状态更新副作用（同步
 *     setView 等）合法——内核只关心 Reading 三态。
 */
import { useEffect, useRef } from "react";

import { buildTaskStreamUrl } from "./sseUrl";
import { getApiToken } from "./token";
import { SSE_FAILURE_LIMIT } from "./sseConstants";
import { getTaskStatusApiCalcTasksTaskIdGet } from "./generated";

/** 退避梯（B6 D3）：1s 基数指数增长，封顶 30s（失败序数 1 起步）。 */
export const SSE_RECONNECT_BASE_MS = 1000;
export const SSE_RECONNECT_CAP_MS = 30 * 1000;
/** 停连后慢速周期探测间隔（60s——自动恢复通道，B6 D3 必改4）。 */
export const SSE_PROBE_INTERVAL_MS = 60 * 1000;
/** B-2：慢探测连续无终态轮次达限——onConnection('polling') 降级标记
 * （「实时通道不可达——已切换轮询」消费方文案面；工单 round3 §1 B-2）。 */
export const SSE_PROBE_FALLBACK_ROUNDS = 5;

/** SSE 连接态四态（B7 D3/G1-04 三态+F2 B-2 降级标记：onConnection 通道
 * 与消费面 prop 的单源类型）。 */
export type ConnectionState = "reconnecting" | "probing" | "ok" | "polling";

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

/** 任务状态探测面（F2 B-2 轮询兜底注入）：返回终态名（done/failed/
 * cancelled）或 null（非终态/探测失败——下一周期续问）。 */
export type TaskStatusProbe = (taskId: string) => Promise<string | null>;

/** 终态名集（任务状态快照 state 字段域——与解读协议 terminal 同集）。 */
const TERMINAL_TASK_STATES = ["done", "failed", "cancelled"];

/** 默认探测实现（F2 B-2）：既有任务状态端点 GET /api/calc/tasks/{task_id}
 * （orval 生成物——零协议破面；探测失败=无答复 null，轮询续走）。 */
export async function probeTaskStatusTerminal(taskId: string): Promise<string | null> {
  try {
    const status = await getTaskStatusApiCalcTasksTaskIdGet(taskId);
    return TERMINAL_TASK_STATES.includes(status.state) ? status.state : null;
  } catch {
    return null; // 探测失败=无答复（同无终态计轮——轮询通道持续可观测）
  }
}

/** 事件解读结果（消费方纯回调面——解析/归约/业务守卫全归消费方）：
 * drop=畸形丢弃（不计链路健康）/event=健康事件（计数归零）/terminal=
 * 终态（计数归零+内核 close+转 onTerminal）。 */
export type TaskEventReading =
  | { kind: "drop" }
  | { kind: "event" }
  | { kind: "terminal"; state: string };

/** 事件解读协议（data 原文→Reading 三态；同步副作用合法）。 */
export type TaskEventInterpreter = (data: string) => TaskEventReading;

/** 订阅句柄（close 幂等——消费方收束/取代守卫共用面）。 */
export interface TaskStreamSubscription {
  close(): void;
}

/** 命令面可选回调束（治理策略归消费方——内核只透传）。 */
export interface TaskStreamCallbacks {
  /** 事件解读（见 TaskEventInterpreter——畸形丢弃语义归消费方）。 */
  interpret: TaskEventInterpreter;
  /** 终态回调（内核已 close 本流后触发）。 */
  onTerminal?: (state: string) => void;
  /** onopen 透传（transport 级信号——「降级后恢复」口径归消费方）。 */
  onOpen?: () => void;
  /** onerror 透传（不自动 close——浏览器内建自动重连保留；close 需求
   * 经返回句柄表达）。 */
  onError?: () => void;
}

/** 订阅任务事件流（命令面——awaitTerminal 等一次性等待消费；与 hook
 * 共享同一解读协议与终态 close 语义）。 */
export function subscribeTaskEvents(
  taskId: string,
  callbacks: TaskStreamCallbacks,
): TaskStreamSubscription {
  const source = new EventSource(buildTaskStreamUrl(taskId, getApiToken()));
  const consume = (event: MessageEvent) => {
    const reading = callbacks.interpret(
      typeof event.data === "string" ? event.data : "",
    );
    if (reading.kind === "terminal") {
      // 终态即收流：close 阻断自动重连循环（服务端发快照后关流）
      source.close();
      callbacks.onTerminal?.(reading.state);
    }
  };
  source.addEventListener("state", consume as EventListener);
  source.addEventListener("progress", consume as EventListener);
  source.addEventListener("stale", consume as EventListener);
  source.onopen = () => callbacks.onOpen?.();
  source.onerror = () => callbacks.onError?.();
  return {
    close: () => {
      source.close();
    },
  };
}

/** 任务事件流长订阅（退避/慢探测恢复态机+probing 轮询兜底——useTaskFeed
 * 生命周期搬家处；事件归约归消费方 interpret 闭包）。 */
export function useTaskEventSource(
  taskId: string | null,
  interpret: TaskEventInterpreter,
  onTerminal?: (state: string) => void,
  onConnection?: (state: ConnectionState) => void,
  probeTaskStatus: TaskStatusProbe = probeTaskStatusTerminal,
): void {
  // 解读/终态/连接态/探测回调经 ref 透传（taskId 单依赖——回调引用变更
  // 不重建连接）
  const interpretRef = useRef(interpret);
  interpretRef.current = interpret;
  const onTerminalRef = useRef(onTerminal);
  onTerminalRef.current = onTerminal;
  const onConnectionRef = useRef(onConnection);
  onConnectionRef.current = onConnection;
  const probeRef = useRef(probeTaskStatus);
  probeRef.current = probeTaskStatus;

  useEffect(() => {
    if (taskId === null) {
      return;
    }
    let failures = 0; // 连续失败计数（健康事件到达即归零——链路恢复）
    let probeRounds = 0; // B-2：慢探测连续无终态轮次（健康事件归零重计）
    let open: TaskStreamSubscription | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let disposed = false;
    let finished = false; // B-2：轮询兜底终态收口后停面（连接/定时器双停）
    let probing = false; // 回炉 W3：单探测在飞守卫（悬置 fetch 不叠轮计）

    const wrapUp = () => {
      finished = true;
      if (timer !== null) {
        clearTimeout(timer);
      }
      open?.close();
    };

    // 回炉 W2：终态单口收口——SSE 与轮询两通道先到者 wrapUp（幂等），
    // 后到者被 finished 守卫拦截（原 SSE 路径不置位=onTerminal 可双调）
    const finishOnce = (state: string) => {
      if (finished || disposed) {
        return;
      }
      wrapUp();
      onTerminalRef.current?.(state);
    };

    // B-2：本 probing 周期的任务状态轮询（终态即收口；无终态计轮达限
    // 发降级标记——轮询续走不静默）
    const probeCycle = async () => {
      probing = true;
      try {
        const state = await probeRef.current(taskId);
        if (disposed || finished) {
          return;
        }
        if (state !== null) {
          finishOnce(state);
          return;
        }
        probeRounds += 1;
        if (probeRounds === SSE_PROBE_FALLBACK_ROUNDS) {
          // 降级标记恰一次（连续口径——健康事件到达归零重计）
          onConnectionRef.current?.("polling");
        }
      } finally {
        probing = false;
      }
    };

    const connect = () => {
      if (disposed || finished) {
        return; // 卸载/轮询终态收口后定时器不复活连接
      }
      const sub = subscribeTaskEvents(taskId, {
        interpret: (data) => {
          const reading = interpretRef.current(data);
          if (reading.kind !== "drop") {
            failures = 0; // 健康事件到达=链路健康（B6 D3 恢复语义）
            probeRounds = 0; // B-2：通道恢复——降级轮次重计
          }
          return reading;
        },
        onTerminal: (state) => finishOnce(state),
        // ok=重建连接且此前降级（failures>0）——首连接 open 零噪音
        // （onopen 是 transport 级真信号；failures 归零仍仅由事件到达承载）。
        onOpen: () => {
          if (failures > 0) {
            onConnectionRef.current?.("ok");
          }
        },
        onError: () => {
          // B6 D3：onerror 无 status 面——401/429/网络抖动同构计数覆盖。
          // close 夺回控制权（弃用浏览器内建无限重连），按计划退避/慢探测。
          sub.close();
          failures += 1;
          const plan = planRecovery(failures);
          // B7 D3：连接态通知（backoff 期=reconnecting/达限慢探测=probing）
          onConnectionRef.current?.(plan.mode === "probe" ? "probing" : "reconnecting");
          if (plan.mode === "probe" && !probing) {
            void probeCycle(); // B-2/W3：每 probing 周期一次轮询（在飞不叠加计轮）
          }
          timer = setTimeout(connect, plan.delayMs);
        },
      });
      open = sub;
    };

    connect();
    return () => {
      // 卸载即清理（无泄漏句柄——连接+退避定时器双收口）
      disposed = true;
      if (timer !== null) {
        clearTimeout(timer);
      }
      open?.close();
    };
  }, [taskId]);
}
