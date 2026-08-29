/**
 * solutions 任务流纯函数层：SSE 线格式解析+事件归约+快照归一+终态判定。
 *
 * 输入:  SSE 事件块/事件 data 行（线格式 `event: {type}\ndata: {json}\n\n`
 *        ——routers/events.py:53）+TaskStatus 快照（弱类型 JSON 体）
 * 输出:  四纯函数族（parseSseBlock/parseEventData→TaskFeedEvent 事件对象/
 *        reduceTaskEvent→TaskView 归约视图/isTerminalState 终态判定/
 *        taskStatusToView→TaskView 快照归一；畸形 data 拒 null 不崩流）
 *
 * 规格说明（FE6 批 6b 段四，D2/D7）：
 *   - Event 载荷五字段 {type,task_id,percent,message,condition_key}
 *     （manager.py:121-129）；type∈{state,progress,stale}——state 事件
 *     message=state 名（queued/running/cancelled/done/failed），progress
 *     事件 message=stage（enumerate 面 load/run/rows、calc 面 load/run/
 *     serialize），percent=(index+1)/(total+1) 即 0~1；
 *   - 双源归一：SSE 流（持续进度）与 TaskStatus 快照（终态详情）归约到
 *     同一 TaskView 形——SSE 载荷无 error 字段（failed 详情走快照源
 *     error/error_type/error_code——taskStatusToView 组合呈现）；
 *   - 终态任务连接即发一条快照 state 事件后收流（manager.py:296-298）
 *     ——deep-link 直进终态任务同一归约路径；
 *   - stale 事件=提示性标记（R1/R2）→TaskView.stale=true（其余保留）；
 *   - 畸形宽容：data JSON 畸形/非对象/无 data 行→null（薄壳静默丢弃）；
 *     载荷字段类型异常归 null（不猜语义）；未知事件类型 no-op（前视兼容）；
 *   - 零运行期库 import（node 测试不拖 EventSource/DOM 链——薄壳
 *     useTaskFeed 持浏览器面）。
 */

/** SSE 事件对象（五字段 camelCase 归一——窄化宽容后形态）。 */
export type TaskFeedEvent = {
  type: string;
  taskId: string | null;
  percent: number | null;
  message: string | null;
  conditionKey: string | null;
};

/** 任务视图（SSE 流与 TaskStatus 快照双源归一的唯一形态）。 */
export type TaskView = {
  /** 任务态（queued/running/done/cancelled/failed——快照弱面 unknown）。 */
  state: string;
  /** 进度（0~1——SSE percent/快照 progress；缺 null）。 */
  percent: number | null;
  /** 最新阶段（state 名或 progress stage 文案）。 */
  stage: string;
  /** 失败详情组合串（仅快照源可详——SSE 恒 null）。 */
  error: string | null;
  /** 结果过期提示标记（stale 事件/快照 stale 面）。 */
  stale: boolean;
};

/** 窄化工具：plain object（非 null 非数组）。 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" && value !== null && !Array.isArray(value)
  );
}

/** 载荷对象 → 事件对象（字段类型宽容归 null；type 缺两头拒 null）。 */
function coerceEvent(
  obj: Record<string, unknown>,
  fallbackType?: string,
): TaskFeedEvent | null {
  const typeInPayload = obj["type"];
  const type =
    typeof typeInPayload === "string" && typeInPayload !== ""
      ? typeInPayload
      : (fallbackType ?? "");
  if (type === "") {
    return null;
  }
  const percent = obj["percent"];
  const message = obj["message"];
  const conditionKey = obj["condition_key"];
  return {
    type,
    taskId: typeof obj["task_id"] === "string" ? obj["task_id"] : null,
    percent:
      typeof percent === "number" && Number.isFinite(percent) ? percent : null,
    message: typeof message === "string" ? message : null,
    conditionKey: typeof conditionKey === "string" ? conditionKey : null,
  };
}

/** data 行直读解析（薄壳 EventSource e.data 面——JSON→事件对象/畸形 null）。 */
export function parseEventData(data: string): TaskFeedEvent | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return null;
  }
  if (!isRecord(parsed)) {
    return null;
  }
  return coerceEvent(parsed);
}

/**
 * SSE 线格式块解析：`event:`/`data:` 行 → 事件对象（多 data 行按 SSE 规范
 * 换行拼接；无 data 行/畸形 JSON/非对象载荷→null；载荷缺 type 时以
 * event 行名兜底）。
 */
export function parseSseBlock(block: string): TaskFeedEvent | null {
  let eventType: string | null = null;
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).replace(/^ /, ""));
    }
  }
  if (dataLines.length === 0) {
    return null;
  }
  const data = dataLines.join("\n");
  const fromPayload = parseEventData(data);
  if (fromPayload !== null) {
    return fromPayload;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return null;
  }
  if (!isRecord(parsed)) {
    return null;
  }
  return coerceEvent(parsed, eventType ?? undefined);
}

/**
 * 事件序列归约：view+event → TaskView（state 事件更新 state+stage+快照
 * percent；progress 事件只推 percent/stage；stale 事件置标记；未知类型
 * no-op——view 原样透传（null 透传 null））。
 */
export function reduceTaskEvent(
  view: TaskView | null,
  event: TaskFeedEvent,
): TaskView | null {
  if (event.type === "state") {
    const state = event.message ?? view?.state ?? "unknown";
    return {
      state,
      percent: event.percent ?? view?.percent ?? null,
      stage: event.message ?? view?.stage ?? "",
      error: view?.error ?? null,
      stale: view?.stale ?? false,
    };
  }
  if (event.type === "progress") {
    return {
      state: view?.state ?? "running",
      percent: event.percent ?? view?.percent ?? null,
      stage: event.message ?? view?.stage ?? "",
      error: view?.error ?? null,
      stale: view?.stale ?? false,
    };
  }
  if (event.type === "stale" && view !== null) {
    return { ...view, stale: true };
  }
  return view;
}

/** 终态判定（manager._TERMINAL——done/cancelled/failed；queued 非 pending）。 */
export function isTerminalState(state: string): boolean {
  return state === "done" || state === "cancelled" || state === "failed";
}

/**
 * TaskStatus 快照归一：弱类型 JSON 体 → TaskView（与 SSE 流同形双源归一；
 * failed 面 error 组合 error_type+error+error_code——SSE 源恒缺的详情面）。
 */
export function taskStatusToView(status: unknown): TaskView {
  const raw = isRecord(status) ? status : {};
  const stateRaw = raw["state"];
  const state = typeof stateRaw === "string" ? stateRaw : "unknown";
  const progress = raw["progress"];
  const stageRaw = raw["stage"];
  let error: string | null = null;
  if (state === "failed") {
    const errorType =
      typeof raw["error_type"] === "string" ? raw["error_type"] : null;
    const errorMessage =
      typeof raw["error"] === "string" ? raw["error"] : null;
    const parts: string[] = [];
    if (errorType !== null || errorMessage !== null) {
      parts.push(errorType ?? "未知异常");
      if (errorMessage !== null) {
        parts.push(`：${errorMessage}`);
      }
    } else {
      parts.push("失败详情缺失（error/error_type 均空）");
    }
    const errorCode = raw["error_code"];
    if (typeof errorCode === "number") {
      parts.push(`（HTTP ${errorCode}）`);
    }
    error = parts.join("");
  }
  return {
    state,
    percent:
      typeof progress === "number" && Number.isFinite(progress)
        ? progress
        : null,
    stage: typeof stageRaw === "string" ? stageRaw : "",
    error,
    stale: raw["stale"] === true,
  };
}
