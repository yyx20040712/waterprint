/**
 * v4 AI 助手区（b2 壳重组批 2026-11-19——八入口「AI 助手」：AI 会话窗+
 * 窄任务条整页；沿革 B1 dockBar〔design 区底栏 92px 常驻〕→b2 升独立
 * 入口〔AiDockWindow/TaskStrip 两件逻辑零改——仅父容器由底栏换整页
 * flex；稿 ai.html 全页形——完整对话流/会话列表=后续功能批，本批凝缩
 * 窗语义沿承〕）。
 *
 * 输入:  useChatHistory/useSendChatMessage（ai_chat 数据通道——ChatSeat
 *        同 session_id 空间）+?task=/?enum=（任务轨双参——task 优先缺省
 *        回落 enum）+useTaskFeed（SSE 进度）+任务快照
 *        （useGetTaskStatus）+TASK_EVENT 事件桥
 * 输出:  ai 页整幅：左=dock-ai（输入框+发送钮+最近一轮摘要行——凝缩形
 *        〔整页高度下摘要区自滚——.wp-v4-dock-main overflow 承袭〕）+
 *        右=dock-tasks（任务行：任务 id+进度条+状态文案）
 *
 * 规格说明（B1 任务书 §三.8 承袭+b2 位置裁决；v4-1 终裁）：
 *   - AI 窗=全软件唯一 AI 窗（v4 壳内）：凝缩形态沿承（输入行+最近一轮
 *     摘要——会话通道与 ChatSeat 同源：session_id/历史/发言 hook 复用）；
 *     完整对话流呈现=后续功能批裁量；
 *   - 任务条=TaskPanel 凝缩形：单行进度（bar+percent+状态文案）；状态条
 *     「任务 ▴」快速入口=本页（非 AI 页在场）；
 *   - SSE 终态→失效任务快照+TASK_EVENT 派发（seatTaskPage 同链——本条
 *     自监听经 URL 重读同值早退幂等）；
 *   - B3 U3：AI 窗头行右缀连接设置入口；R1-W1：设置钮经 onOpenSettings
 *     上抛（Modal/AUTH_EVENT 自愈在 shellV4 恒挂载层）；
 *   - 本地 chat LLM 配置回挂（2026-11-19）：「模型配置」钮
 *     （RobotOutlined）——LlmConfigSection 迁 ai_chat 后重挂本窗。
 */
import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { RobotOutlined, SettingOutlined } from "@ant-design/icons";
import { Button, Modal } from "antd";

import {
  useChatHistory,
  useSendChatMessage,
} from "../../features/ai_chat/api/useAiChat";
import { LlmConfigSection } from "../../features/ai_chat/components/LlmConfigSection";
import { useTaskFeed } from "../../features/solutions/api/useTaskFeed";
import {
  taskStatusToView,
  type TaskView,
} from "../../features/solutions/lib/taskFeed";
import { useGetTaskStatusApiCalcTasksTaskIdGet } from "../../shared/api/generated/calc/calc";
import { TASK_EVENT } from "../../shared/events";
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

/** 会话续接持久键（P3 d1-N7——AI 窗会话跨入口切换〔卸载/重挂〕与刷新
 *  两径恢复：sessionStorage 持久〔会话生命周期=标签页〕）。 */
const DOCK_SESSION_KEY = "wp-v4-dock-session";

/** AI 凝缩窗：输入行+发送+最近一轮摘要（会话通道与 ChatSeat 同源）。
 *  R1-W1：连接设置开态经 onOpenSettings 上抛（Modal 承载在 shellV4 恒
 *  挂载层）；模型配置（本地 chat LLM 三键）开态本窗自持——Modal 就地
 *  承载（LlmConfigSection enabled 门控=开态，零挂载期请求扰动）。 */
function AiDockWindow({ onOpenSettings }: { onOpenSettings: () => void }) {
  // B2 会话续接（d1-N7）：初值=sessionStorage 持久面（无则 null 首发建档）
  const [sessionId, setSessionId] = useState<string | null>(() =>
    window.sessionStorage.getItem(DOCK_SESSION_KEY),
  );
  const [draft, setDraft] = useState("");
  const [llmOpen, setLlmOpen] = useState(false);
  const history = useChatHistory(sessionId);
  const send = useSendChatMessage();
  const messages = useMemo(() => history.data ?? [], [history.data]);
  // 最近一轮摘要（用户末问+助手末答各一行——超长截断）
  const lastUser = [...messages].reverse().find((m) => m.role === "user");
  const lastAssistant = [...messages].reverse().find((m) => m.role !== "user");

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
          <span style={{ color: "var(--wp-accent)" }}>发送中…</span>
        ) : null}
        {history.isError ? (
          <span style={{ color: "var(--wp-error)" }}>会话读取失败（中继不可达）</span>
        ) : null}
        {/* 连接设置入口（wp-v4-open-settings——R1-W1：onClick 上抛
            onOpenSettings，Modal 在 shellV4 承载） */}
        <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 2, flex: "none" }}>
          {/* 模型配置入口（wp-v4-llm-config——本地 chat LLM 三键面：
              LlmConfigSection 恢复迁 ai_chat 后挂本窗，Modal 就地承载） */}
          <Button
            type="text"
            size="small"
            icon={<RobotOutlined />}
            onClick={() => setLlmOpen(true)}
            aria-label="模型配置"
            title="模型配置"
            data-testid="wp-v4-llm-config"
          />
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            onClick={onOpenSettings}
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
      <div style={{ display: "flex", gap: 6, padding: "4px 10px 6px", borderTop: "1px solid var(--wp-border-2)", flex: "none" }}>
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
            background: "var(--wp-bg-elevated)",
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
            background: "var(--wp-accent)",
            color: "#ffffff",
            cursor: send.isPending ? "default" : "pointer",
          }}
        >
          发送
        </button>
      </div>
      {/* 模型配置 Modal（本地 chat LLM 三键——LlmConfigSection 迁 ai_chat
          恢复件；footer=null=区块自带「保存并生效」钮；open 门控查询零扰动） */}
      <Modal
        title="模型配置"
        open={llmOpen}
        onCancel={() => setLlmOpen(false)}
        footer={null}
        width={520}
      >
        <LlmConfigSection enabled={llmOpen} />
      </Modal>
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
          <span style={{ color: "var(--wp-warning)" }}>结果已过期（参数已变更）</span>
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
    </div>
  );
}

/** AI 助手整页（AiDockWindow+TaskStrip 两件零改——父容器=整页 flex
 *  〔左会话窗伸展/右任务条 320px 固定，稿 ai.html 两栏位〕）。 */
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
  return (
    <section
      className="wp-v4-ai-zone"
      data-region="ai-workspace"
      data-testid="wp-v4-ai-zone"
      style={{ flex: 1, minWidth: 0, display: "flex" }}
    >
      <AiDockWindow onOpenSettings={onOpenSettings} />
      <TaskStrip onTaskNavigate={onTaskNavigate} />
    </section>
  );
}
