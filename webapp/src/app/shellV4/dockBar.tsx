/**
 * v4 底栏双区（B1 骨架批 2026-10-09——AI 唯一窗+窄任务条；design 区常驻；
 * 高预算 92px≤98——G3'' 密度判据 @1440×900 画布净高 706≥700 单口径）。
 *
 * 输入:  useChatHistory/useSendChatMessage（ai_chat 数据通道——ChatSeat
 *        同 session_id 空间；回炉 R10：useChatSessions 死代码摘除——
 *        V2 凝缩窗不消费会话列表，错误呈现随 B2 完整对话流批）+?task=/
 *        ?enum=（任务轨双参——task 优先缺省回落 enum）+useTaskFeed（SSE
 *        进度）+任务快照（useGetTaskStatus）+TASK_EVENT 事件桥
 * 输出:  dock-ai（输入框+发送钮+最近一轮摘要行——凝缩形）+dock-tasks
 *        （任务行：任务 id+进度条+状态文案——TaskPanel 凝缩形）
 *
 * 规格说明（B1 任务书 §三.8——plan §九.1；v4-1 终裁）：
 *   - AI 窗=全软件唯一 AI 窗（v4 壳内）：凝缩形态=B1 视觉微裁决——
 *     ChatPanel 消息区 minHeight 200 与 92px dock 预算不兼容，B1 取
 *     输入行+最近一轮摘要（会话通道与 ChatSeat 同源——session_id/历史/
 *     发言 hook 复用）；完整对话流呈现=B2/B3 批裁量（理由落批档
 *     visual-decisions.md）；
 *   - 任务条=TaskPanel 凝缩形：单行进度（bar+percent+状态文案）；校验
 *     结论呈现=B2 处置（校验钮→任务条）；回执页退役=B3；
 *   - SSE 终态→失效任务快照+TASK_EVENT 派发（seatTaskPage 同链——本条
 *     自监听经 URL 重读同值早退幂等）；
 *   - B3 U3：AI 窗头行右缀 AI 接入+连接设置两入口（legacy Header 右侧
 *     同族迁 v4）+AUTH_EVENT 401 自愈回路 parity（App.tsx:305-307 同款
 *     ——customInstance 401 派发→自动开 TokenSettingsModal）。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { SettingOutlined } from "@ant-design/icons";
import { Button } from "antd";

import {
  useChatHistory,
  useSendChatMessage,
} from "../../features/ai_chat/api/useAiChat";
import { AiConnectButton } from "../../features/aiconnect/components/AiConnectButton";
import { AiConnectModal } from "../../features/aiconnect/components/AiConnectModal";
import { useTaskFeed } from "../../features/solutions/api/useTaskFeed";
import {
  taskStatusToView,
  type TaskView,
} from "../../features/solutions/lib/taskFeed";
import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../../shared/api/generated/calc/calc";
import { AUTH_EVENT, TASK_EVENT } from "../../shared/events";
import { TokenSettingsModal } from "../tokenSettingsModal";
import { parseEnumParam, parseTaskParam } from "../projectParam";

/** 任务状态文案（TaskPanel STATE_LABELS 凝缩面子集）。 */
const STATE_TEXT: Record<string, string> = {
  queued: "排队中",
  running: "运行中",
  done: "已完成",
  cancelled: "已取消",
  failed: "失败",
};

/** 首发建档会话 id（ChatSeat generateSessionId 同形——hex32）。 */
const generateSessionId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}new`).replace(/-/g, "");

/** 会话续接持久键（P3 d1-N7——dock-ai 会话跨 zone 切换〔卸载/重挂〕与
 *  刷新两径恢复：sessionStorage 持久〔会话生命周期=标签页——侧栏宽度
 *  localStorage 记忆 B1 全局规则同族但会话面不入长期存储〕）。 */
const DOCK_SESSION_KEY = "wp-v4-dock-session";

/** AI 凝缩窗：输入行+发送+最近一轮摘要（会话通道与 ChatSeat 同源）。 */
function AiDockWindow() {
  // B2 会话续接（d1-N7）：初值=sessionStorage 持久面（无则 null 首发建档）
  const [sessionId, setSessionId] = useState<string | null>(() =>
    window.sessionStorage.getItem(DOCK_SESSION_KEY),
  );
  const [draft, setDraft] = useState("");
  const history = useChatHistory(sessionId);
  const send = useSendChatMessage();
  const messages = useMemo(() => history.data ?? [], [history.data]);
  // 最近一轮摘要（用户末问+助手末答各一行——超长截断）
  const lastUser = [...messages].reverse().find((m) => m.role === "user");
  const lastAssistant = [...messages].reverse().find((m) => m.role !== "user");
  // B3 U3：AI 接入/连接设置两 Modal 开态（窗头行右缀入口）
  const [aiConnectOpen, setAiConnectOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // 401 自愈回路 parity（B3 U3）：AUTH_EVENT→自动开连接设置（legacy
  // App.tsx:305-307 同款——customInstance 401 派发面；卸载移除监听）。
  useEffect(() => {
    const openSettings = () => setSettingsOpen(true);
    window.addEventListener(AUTH_EVENT, openSettings);
    return () => window.removeEventListener(AUTH_EVENT, openSettings);
  }, []);

  const submit = () => {
    const text = draft.trim();
    if (!text || send.isPending) {
      return;
    }
    const sid = sessionId ?? generateSessionId();
    if (sessionId === null) {
      setSessionId(sid);
      window.sessionStorage.setItem(DOCK_SESSION_KEY, sid);
    }
    send.mutate(
      { sessionId: sid, message: text },
      { onSuccess: () => setDraft("") },
    );
  };

  return (
    <div className="wp-v4-dock-ai" data-region="dock-ai">
      <div className="wp-v4-dock-strip">
        <span>AI 对话</span>
        {send.isPending ? (
          <span style={{ color: "var(--wpv4-ac)" }}>发送中…</span>
        ) : null}
        {history.isError ? (
          <span style={{ color: "var(--wp-error)" }}>会话读取失败（中继不可达）</span>
        ) : null}
        {/* B3 U3：窗头行右缀两入口（AI 接入=共享件；连接设置=wp-v4-open-settings） */}
        <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 2, flex: "none" }}>
          <AiConnectButton onClick={() => setAiConnectOpen(true)} />
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => setSettingsOpen(true)}
            aria-label="连接设置"
            title="连接设置"
            data-testid="wp-v4-open-settings"
          />
        </span>
      </div>
      <div
        className="wp-v4-dock-main"
        data-testid="wp-v4-ai-log"
        style={{ fontSize: 11, color: "var(--wp-text-2)", lineHeight: 1.6 }}
      >
        {lastUser ? (
          <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            用户：{lastUser.text}
          </div>
        ) : null}
        {lastAssistant ? (
          <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            AI：{lastAssistant.text}
          </div>
        ) : null}
      </div>
      <div style={{ display: "flex", gap: 6, padding: "4px 10px 6px", borderTop: "1px solid var(--wp-border-2)" }}>
        <input
          data-testid="wp-v4-ai-input"
          aria-label="AI 消息输入"
          placeholder="描述设计意图…"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              submit();
            }
          }}
          style={{
            flex: 1,
            minWidth: 0,
            border: "1px solid var(--wp-border)",
            borderRadius: 12,
            padding: "2px 10px",
            fontSize: 11,
            background: "#ffffff",
            color: "var(--wp-text)",
            outline: "none",
          }}
        />
        <button
          type="button"
          data-testid="wp-v4-ai-send"
          onClick={submit}
          disabled={send.isPending}
          style={{
            border: "none",
            borderRadius: 4,
            padding: "2px 10px",
            fontSize: 11,
            background: "var(--wpv4-ac)",
            color: "#ffffff",
            cursor: send.isPending ? "default" : "pointer",
          }}
        >
          发送
        </button>
      </div>
      {/* B3 U3：AI 接入+连接设置两 Modal（共享件零改复用；关态零请求扰动
          ——useAiConnection enabled=open 门控/tokenSettings 零即时校验） */}
      <AiConnectModal open={aiConnectOpen} onClose={() => setAiConnectOpen(false)} />
      <TokenSettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}

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
    <div className="wp-v4-dock-tasks" data-region="dock-tasks">
      <div className="wp-v4-dock-strip">
        <span>任务 · 校验</span>
        {effective?.stale === true ? (
          <span style={{ color: "var(--wpv4-warn)" }}>结果已过期（参数已变更）</span>
        ) : null}
      </div>
      <div className="wp-v4-dock-main">
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
            style={{ cursor: state === "done" ? "pointer" : undefined }}
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
                width: 110,
                height: 6,
                background: "#f0f2f5",
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
                  background: "var(--wpv4-ac)",
                }}
              />
            </span>
            <span>{percent === null ? "" : `${percent}%`}</span>
            <span
              style={{
                fontSize: 10,
                borderRadius: 3,
                padding: "0 5px",
                color: state === "done" ? "var(--wpv4-ok)" : state === "failed" ? "var(--wp-error)" : "var(--wp-text-2)",
                background:
                  state === "done"
                    ? "var(--wpv4-ok-bg)"
                    : state === "failed"
                      ? "#fdeceb"
                      : "#f0f2f5",
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
    </div>
  );
}

export function DockBar({
  onTaskNavigate,
}: {
  /** B2 完成直达（§一.4）：done 任务行点击上抛——designZone→shellV4 承接
   *  （切 ?tab=design.analysis+相关单元选中）。 */
  onTaskNavigate?: (target: { state: string; unitId: string | null }) => void;
}) {
  return (
    <div className="wp-v4-dock" data-testid="wp-v4-dock">
      <AiDockWindow />
      <TaskStrip onTaskNavigate={onTaskNavigate} />
    </div>
  );
}
