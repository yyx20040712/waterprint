/**
 * v4 AI 助手区（b2 壳重组批升独立入口→b4 功能面重涂 II 批 2026-11-19
 * 稿 ai.html 三栏重制：左=设计会话清单〔AiSessionsPane——切换/新建视图
 * 态〕+中=完整会话流〔AiChatFace——消息泡/工具调用卡/composer；b2 凝缩
 * 窗语义退役〕+右=对话语境〔当前项目/本轮工具/模型与降级说明+任务条
 * TaskStrip〕；会话通道/sessionStorage 续接/LLM 配置/任务 SSE 数据流
 * 全承袭零变）。
 *
 * 输入:  useProjectId+useProjectName（语境行）+useChatSessions（清单/标题
 *        面——同键缓存共享）+useChatHistory（本轮工具派生）+?task=/?enum=
 *        （任务轨双参）+useTaskFeed（SSE 进度）+任务快照
 *        （useGetTaskStatus）+TASK_EVENT 事件桥
 * 输出:  ai 页整幅三栏：ai-sessions/会话流（dock-ai）/语境栏（dock-tasks
 *        承任务条+语境三节）；sessionId=aiZone 视图态单源〔null=新会话
 *        ——首发建档经 DOCK_SESSION_KEY sessionStorage 持久跨卸载/刷新〕
 *
 * 规格说明（b4 批准稿 ai.html——布局与信息组织重造，数据流零变）：
 *   - 会话态单源在本件：AiSessionsPane 切换/AiChatFace 首发建档均经
 *     回调上抛（P3 d1-N7 续接语义沿承——键 wp-v4-dock-session 不变）；
 *   - 任务条=TaskStrip 原件（凝缩行进语境栏任务节——wp-v4-task-row/
 *     done 直达/failed 错误面断言链不变）；
 *   - 语境行=只读派生（项目名/选中单元 ?node=/本轮工具计数——零新
 *     数据通道，均为既有查询缓存或 URL 参数投影）。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  useChatHistory,
  useChatSessions,
} from "../../features/ai_chat/api/useAiChat";
import { useTaskFeed } from "../../features/solutions/api/useTaskFeed";
import {
  taskStatusToView,
  type TaskView,
} from "../../features/solutions/lib/taskFeed";
import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../../shared/api/generated/calc/calc";
import { TASK_EVENT } from "../../shared/events";
import { parseEnumParam, parseTaskParam } from "../projectParam";
import { parseNodeParam } from "../zoneParam";
import { useProjectId } from "../useProjectId";
import { useProjectName } from "../useProjectName";
import { AiChatFace } from "./aiChatFace";
import { AiSessionsPane } from "./aiSessionsPane";

/** 任务状态文案（TaskPanel STATE_LABELS 凝缩面子集）。 */
const STATE_TEXT: Record<string, string> = {
  queued: "排队中",
  running: "运行中",
  done: "已完成",
  cancelled: "已取消",
  failed: "失败",
};

/** 会话续接持久键（P3 d1-N7——AI 窗会话跨入口切换〔卸载/重挂〕与刷新
 *  两径恢复：sessionStorage 持久〔会话生命周期=标签页〕）。 */
const DOCK_SESSION_KEY = "wp-v4-dock-session";

/** 语境栏说明（稿 ai.html 右栏 notice——白名单：说明文案）。 */
const CONTEXT_MODEL_NOTE =
  "未配置聊天模型时，agent 环自动降级为关键词直译，支持建项与计算。前端不执行模型逻辑。";

/** 窄任务条：?task=/?enum= 双轨（task 优先）+SSE 进度凝缩行。
 *  B2（§一.4）：done 任务行点击→onTaskNavigate 直达分析表（枚举任务携
 *  result.unit_id=相关单元选中；calc 任务 unitId=null）；failed=错误
 *  提示行（白名单——快照 error 透出）。 */
function TaskStrip({
  onTaskNavigate,
}: {
  onTaskNavigate?: (target: { state: string; unitId: string | null }) => void;
}) {
  const [taskId, setTaskId] = useState<string | null>(() =>
    parseTaskParam(window.location.search) ??
    parseEnumParam(window.location.search),
  );
  const queryClient = useQueryClient();

  // TASK_EVENT 重读（URL 单一真相——同值早退；seatTaskPage 同链）
  useEffect(() => {
    const onTaskParam = () => {
      const next =
        parseTaskParam(window.location.search) ??
        parseEnumParam(window.location.search);
      setTaskId((prev) => (prev === next ? prev : next));
    };
    window.addEventListener(TASK_EVENT, onTaskParam);
    return () => window.removeEventListener(TASK_EVENT, onTaskParam);
  }, []);

  const view = useTaskFeed(taskId, () => {
    if (taskId !== null) {
      void queryClient.invalidateQueries({
        queryKey: [`/api/calc/tasks/${taskId}`],
      });
    }
  });
  const statusQuery = useGetTaskStatusApiCalcTasksTaskIdGet(taskId ?? "", {
    query: { enabled: taskId !== null },
  });
  const snapshot: TaskView | null =
    statusQuery.data !== null && statusQuery.data !== undefined
      ? taskStatusToView(statusQuery.data)
      : null;
  const effective = view ?? snapshot;
  const state = effective?.state ?? "";
  const percent =
    state === "done"
      ? 100
      : effective?.percent != null
        ? Math.round(effective.percent * 100)
        : null;

  return (
    <div data-region="dock-tasks">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          marginBottom: 6,
        }}
      >
        <h4 style={{ fontSize: 11.5, color: "var(--wp-text-2)", letterSpacing: 0.5 }}>
          任务 · 校验
        </h4>
        {effective?.stale === true ? (
          <span style={{ color: "var(--wp-warning)", fontSize: 10.5 }}>结果已过期（参数已变更）</span>
        ) : null}
      </div>
      {taskId === null || effective === null ? (
        <div style={{ color: "var(--wp-text-2)", fontSize: 11, padding: "3px 0" }}>
          尚无进行中任务
        </div>
      ) : (
        <div
          className="wp-v4-task-row"
          data-testid="wp-v4-task-row"
          // B2 完成直达：done 行可点（title 述义——枚举任务携相关单元）
          title={state === "done" ? "点击查看分析表" : undefined}
          style={{ cursor: state === "done" ? "pointer" : undefined, padding: "3px 0" }}
          onClick={() => {
            if (state !== "done" || onTaskNavigate === undefined) {
              return;
            }
            const result = statusQuery.data?.result;
            const unitId =
              typeof result === "object" &&
              result !== null &&
              typeof (result as Record<string, unknown>)["unit_id"] === "string"
                ? String((result as Record<string, unknown>)["unit_id"])
                : null;
            onTaskNavigate({ state: "done", unitId });
          }}
        >
          <span title={taskId} style={{ fontFamily: "var(--wp-font-mono)" }}>
            任务 {taskId.slice(0, 8)}
          </span>
          <span
            aria-hidden
            style={{
              width: 90,
              height: 6,
              background: "var(--wp-bg-deep)",
              borderRadius: 3,
              overflow: "hidden",
              flex: "none",
            }}
          >
            <span
              style={{
                display: "block",
                height: "100%",
                width: `${percent ?? 0}%`,
                background: "var(--wp-accent)",
              }}
            />
          </span>
          <span>{percent === null ? "" : `${percent}%`}</span>
          <span
            style={{
              fontSize: 10,
              borderRadius: 3,
              padding: "0 5px",
              color: state === "done" ? "var(--wp-success)" : state === "failed" ? "var(--wp-error)" : "var(--wp-text-2)",
              background:
                state === "done"
                  ? "var(--wp-success-soft)"
                  : state === "failed"
                    ? "var(--wp-error-soft)"
                    : "var(--wp-bg-deep)",
            }}
          >
            {STATE_TEXT[state] ?? state}
          </span>
        </div>
      )}
      {/* failed=错误提示行（白名单：错误提示——SSE 快照组合 error 面） */}
      {state === "failed" && effective?.error != null ? (
        <div
          data-testid="wp-v4-task-error"
          style={{
            fontSize: 11,
            color: "var(--wp-error)",
            padding: "2px 0 1px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={effective.error}
        >
          {effective.error}
        </div>
      ) : null}
    </div>
  );
}

/** 语境栏（稿 ai.html 右栏：当前项目/本轮工具/模型与降级+任务节）。 */
function AiContextPane({
  sessionId,
  onTaskNavigate,
}: {
  /** 当前会话 id（AiZone 视图态透传——本轮工具投影数据面）。 */
  sessionId: string | null;
  onTaskNavigate?: (target: { state: string; unitId: string | null }) => void;
}) {
  const [projectId] = useProjectId();
  const projectName = useProjectName();
  // 选中单元=URL ?node= 投影（parseNodeParam 只读——零状态订阅）
  const [selectedUnit] = useState(() => parseNodeParam(window.location.search));
  return (
    <aside className="wp-v4-pane right" data-region="ai-context" style={{ width: 262 }}>
      <div className="wp-v4-pane-head">
        <h3>对话语境</h3>
        <span className="wp-v4-badge">本地项目</span>
      </div>
      <div className="wp-v4-pane-body">
        <div className="wp-v4-insp-sec">
          <h4>当前项目</h4>
          <strong style={{ fontSize: 12 }}>{projectName ?? "未选择项目"}</strong>
          <div className="wp-v4-kv" style={{ marginTop: 6 }}>
            <span className="k">项目 id</span>
            <span className="v" title={projectId ?? undefined}>
              {projectId ?? "—"}
            </span>
          </div>
          <div className="wp-v4-kv">
            <span className="k">选中单元</span>
            <span className="v" title={selectedUnit ?? undefined}>
              {selectedUnit ?? "—"}
            </span>
          </div>
        </div>
        <AiToolSummary sessionId={sessionId} />
        <div className="wp-v4-insp-sec">
          <h4>模型与降级</h4>
          <p style={{ margin: 0, color: "var(--wp-text-2)", fontSize: 11, lineHeight: 1.7 }}>
            {CONTEXT_MODEL_NOTE}
          </p>
          <p style={{ margin: "8px 0 0", color: "var(--wp-text-3)", fontSize: 10.5, lineHeight: 1.7 }}>
            配置入口在会话头「模型配置」钮。
          </p>
        </div>
        <div className="wp-v4-insp-sec">
          <TaskStrip onTaskNavigate={onTaskNavigate} />
        </div>
      </div>
    </aside>
  );
}

/** 本轮工具节（最近一轮助手消息 tool_steps 投影——同键缓存零新请求）。 */
function AiToolSummary({ sessionId }: { sessionId: string | null }) {
  const history = useChatHistory(sessionId);
  const messages = history.data ?? [];
  const lastTools = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      if (message !== undefined && message.role !== "user" && Array.isArray(message.tool_steps)) {
        return message.tool_steps.filter(
          (step): step is Record<string, unknown> =>
            typeof step === "object" && step !== null,
        );
      }
    }
    return [];
  }, [messages]);
  return (
    <div className="wp-v4-insp-sec">
      <h4
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 6,
        }}
      >
        本轮工具
        {lastTools.length > 0 ? (
          <span className="wp-v4-badge ok">{lastTools.length} 次调用</span>
        ) : null}
      </h4>
      {lastTools.length === 0 ? (
        <p style={{ margin: 0, color: "var(--wp-text-2)", fontSize: 11 }}>尚无工具调用</p>
      ) : (
        <div className="wp-v4-list">
          {lastTools.map((step, index) => (
            <div key={index} className="wp-v4-row" style={{ minHeight: 30 }}>
              <span
                aria-hidden
                style={{ color: step["ok"] === true ? "var(--wp-success)" : "var(--wp-error)", flex: "none" }}
              >
                {step["ok"] === true ? "✓" : "✕"}
              </span>
              <span style={{ minWidth: 0, fontSize: 11.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {typeof step["name"] === "string" ? step["name"] : "工具调用"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/** AI 助手整页三栏（b4 稿 ai.html：会话清单/会话流/语境栏）。 */
export function AiZone({
  onTaskNavigate,
  onOpenSettings,
}: {
  /** B2 完成直达（§一.4）：done 任务行点击上抛——shellV4 承接（切分析
   *  入口+相关单元选中）。 */
  onTaskNavigate?: (target: { state: string; unitId: string | null }) => void;
  /** R1-W1：连接设置开态上抛（shellV4 恒挂载层承载 TokenSettingsModal/
   *  AUTH_EVENT 自愈监听）。 */
  onOpenSettings: () => void;
}) {
  const [projectId] = useProjectId();
  // B2 会话续接（d1-N7）：初值=sessionStorage 持久面（无则 null 首发建档）
  const [sessionId, setSessionId] = useState<string | null>(() => {
    try {
      return window.sessionStorage.getItem(DOCK_SESSION_KEY);
    } catch {
      return null;
    }
  });
  // 会话清单（标题查找面——与 AiSessionsPane 同键缓存共享零额外请求）
  const sessionsQuery = useChatSessions(true);
  const sessionTitle = useMemo(() => {
    if (sessionId === null) {
      return null;
    }
    const hit = (sessionsQuery.data ?? []).find(
      (session) => session.session_id === sessionId,
    );
    return hit?.title?.trim() ? hit.title : null;
  }, [sessionsQuery.data, sessionId]);

  /** 会话态写面（切换/新建/首发建档三入口合一——sessionStorage 先写）。 */
  const changeSession = (next: string | null) => {
    setSessionId(next);
    try {
      if (next === null) {
        window.sessionStorage.removeItem(DOCK_SESSION_KEY);
      } else {
        window.sessionStorage.setItem(DOCK_SESSION_KEY, next);
      }
    } catch {
      // 存储不可用不阻断会话（内存态仍可用）
    }
  };

  return (
    <section
      className="wp-v4-ai-zone"
      data-region="ai-workspace"
      data-testid="wp-v4-ai-zone"
      style={{ flex: 1, minWidth: 0, display: "flex" }}
    >
      <AiSessionsPane
        sessionId={sessionId}
        projectId={projectId}
        onSessionChange={changeSession}
      />
      <AiChatFace
        sessionId={sessionId}
        sessionTitle={sessionTitle}
        onSessionInit={changeSession}
        onOpenSettings={onOpenSettings}
      />
      <AiContextPane sessionId={sessionId} onTaskNavigate={onTaskNavigate} />
    </section>
  );
}
