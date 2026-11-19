/**
 * AI 会话中央面（b4 功能面重涂 II 批 2026-11-19——稿 ai.html 中栏：
 * 会话头〔标题+本地设计助手副行+模型配置/连接设置钮〕+完整会话流
 * 〔用户泡/助手卡+工具调用卡〕+composer〔textarea+Enter 发送〕；沿革
 * b2 凝缩窗〔输入行+最近一轮摘要〕→b4 完整对话流呈现——会话通道/
 * 发送链/LLM 配置面零变）。
 *
 * 输入:  sessionId（aiZone 视图态——null=新会话未建档）+onSessionInit
 *        （首发建档上抛——aiZone 持久 sessionStorage）+onOpenSettings
 *        （连接设置上抛——shellV4 Modal 承载）+useChatHistory/
 *        useSendChatMessage（会话数据通道）
 * 输出:  中栏：pane-head〔标题+副行+两设置钮〕+消息流（用户=accent-soft
 *        泡右对齐/助手=头像+meta+正文+工具调用卡〔name+ok 状态〕+
 *        truncated 徽标）+composer（textarea+发送钮+键位提示）
 *
 * 规格说明（b4 批准稿 ai.html 中栏段——信息组织重造，数据流零变）：
 *   - 消息流=useChatHistory 全量呈现（ChatHistoryMessage role/text/
 *     turn/truncated/tool_steps 五键投影——服务端 agent 契约）；工具
 *     调用卡=tool_steps〔{name, ok}〕逐项（ok=true 完成/失败两态——
 *     失败不伪装成功）；未知形状行=名称缺席回退「工具调用」；
 *   - composer=textarea（Enter 发送/Shift Enter 换行——稿键位）；发送
 *     中=禁用+「发送中…」提示；失败轮=错误摘要行（history.isError
 *     面——不伪装成功回复）；
 *   - 首发建档：sessionId=null 时发送前 generateSessionId+onSessionInit
 *     上抛（ChatSeat generateSessionId 同形 hex32）。
 */
import { useState, type ReactNode } from "react";
import { RobotOutlined, SettingOutlined } from "@ant-design/icons";
import { Button, Modal } from "antd";

import {
  useChatHistory,
  useSendChatMessage,
} from "../../features/ai_chat/api/useAiChat";
import { LlmConfigSection } from "../../features/ai_chat/components/LlmConfigSection";
import type { ChatHistoryMessage } from "../../shared/api/generated/model/chatHistoryMessage";

/** 头行副题（稿 ai.html——白名单：说明文案）。 */
const CENTER_SUBTITLE = "本地设计助手，工具调用可见";
/** 空态引导（白名单：空态引导）。 */
const EMPTY_CHAT_HINT = "基于当前项目提问——工具调用与引用会显示在对话中";
/** 键位提示（稿 composer 左注）。 */
const COMPOSER_HINT = "Enter 发送，Shift Enter 换行";
/** 助手名（稿 message-meta——白名单：显示名）。 */
const ASSISTANT_NAME = "WaterPrint 助手";

/** 首发建档会话 id（ChatSeat generateSessionId 同形——hex32）。 */
export const generateSessionId = () =>
  (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}new`).replace(/-/g, "");

/** 工具调用卡（稿 .tool-call：头行〔状态形+名〕+完成徽标）。 */
function ToolCallCard({ step }: { step: Record<string, unknown> }) {
  const name = typeof step["name"] === "string" ? step["name"] : "工具调用";
  const ok = step["ok"] === true;
  return (
    <div
      data-testid="wp-v4-ai-tool-call"
      style={{
        marginTop: 8,
        border: "1px solid var(--wp-border-2)",
        borderRadius: 4,
        background: "var(--wp-bg-deep)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 7,
          padding: "5px 9px",
          color: "var(--wp-text-2)",
          fontSize: 11,
        }}
      >
        <span aria-hidden style={{ color: ok ? "var(--wp-success)" : "var(--wp-error)" }}>
          {ok ? "✓" : "✕"}
        </span>
        <span>{name}</span>
        <span
          className={ok ? "wp-v4-badge ok" : "wp-v4-badge error"}
          style={{ marginLeft: "auto" }}
        >
          {ok ? "完成" : "失败"}
        </span>
      </div>
    </div>
  );
}

/** 单条消息（user=右对齐泡；assistant=头像+meta+正文+工具卡）。 */
function ChatMessage({ message }: { message: ChatHistoryMessage }) {
  if (message.role === "user") {
    return (
      <div
        data-testid="wp-v4-ai-msg-user"
        style={{ display: "flex", justifyContent: "flex-end", maxWidth: "78%", marginLeft: "auto" }}
      >
        <div>
          <div style={{ marginBottom: 3, color: "var(--wp-text-3)", fontSize: 10.5, textAlign: "right" }}>
            你
          </div>
          <div
            style={{
              padding: "7px 11px",
              borderRadius: 6,
              background: "var(--wp-accent-soft)",
              color: "var(--wp-text)",
              fontSize: 12,
              lineHeight: 1.7,
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
            }}
          >
            {message.text}
          </div>
        </div>
      </div>
    );
  }
  const steps = Array.isArray(message.tool_steps) ? message.tool_steps : [];
  const body: ReactNode[] = [];
  if (message.text !== "") {
    body.push(
      <p key="text" style={{ margin: 0, fontSize: 12, lineHeight: 1.75, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
        {message.text}
      </p>,
    );
  }
  for (const [index, step] of steps.entries()) {
    if (typeof step === "object" && step !== null) {
      body.push(<ToolCallCard key={`tool-${index}`} step={step as Record<string, unknown>} />);
    }
  }
  if (message.truncated === true) {
    body.push(
      <div key="truncated" className="wp-v4-badge warn" style={{ marginTop: 8 }}>
        本轮过长已截断
      </div>,
    );
  }
  return (
    <div data-testid="wp-v4-ai-msg-assistant" style={{ display: "flex", gap: 9, maxWidth: "92%" }}>
      <span
        aria-hidden
        style={{
          width: 26,
          height: 26,
          flex: "none",
          display: "inline-grid",
          placeItems: "center",
          border: "1px solid var(--wp-border)",
          borderRadius: "50%",
          color: "var(--wp-accent)",
          background: "var(--wp-bg-elevated)",
          fontSize: 12,
        }}
      >
        ◉
      </span>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ marginBottom: 3, color: "var(--wp-text-2)", fontSize: 10.5 }}>
          {ASSISTANT_NAME}
          {message.turn !== undefined ? ` · 第 ${message.turn} 轮` : ""}
        </div>
        {body.length > 0 ? body : <p style={{ margin: 0, color: "var(--wp-text-2)", fontSize: 12 }}>（空回复）</p>}
      </div>
    </div>
  );
}

export function AiChatFace({
  sessionId,
  sessionTitle,
  onSessionInit,
  onOpenSettings,
}: {
  /** 当前会话 id（null=新会话未建档）。 */
  sessionId: string | null;
  /** 会话标题（会话清单 title——缺席=「新会话」）。 */
  sessionTitle: string | null;
  /** 首发建档上抛（aiZone 持久 sessionStorage）。 */
  onSessionInit: (sessionId: string) => void;
  /** 连接设置入口（R1-W1 上抛——shellV4 Modal 承载）。 */
  onOpenSettings: () => void;
}) {
  const [draft, setDraft] = useState("");
  const [llmOpen, setLlmOpen] = useState(false);
  const history = useChatHistory(sessionId);
  const send = useSendChatMessage();
  const messages = history.data ?? [];

  const submit = () => {
    const text = draft.trim();
    if (!text || send.isPending) {
      return;
    }
    const sid = sessionId ?? generateSessionId();
    if (sessionId === null) {
      onSessionInit(sid);
    }
    send.mutate(
      { sessionId: sid, message: text },
      { onSuccess: () => setDraft("") },
    );
  };

  return (
    <section
      style={{ flex: 1, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", background: "var(--wp-bg-container)" }}
      data-region="dock-ai"
    >
      <div className="wp-v4-pane-head">
        <div style={{ minWidth: 0 }}>
          <h3>{sessionTitle ?? "新会话"}</h3>
          <span style={{ display: "block", color: "var(--wp-text-2)", fontSize: 10.5 }}>
            {CENTER_SUBTITLE}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 2, flex: "none" }}>
          {/* 模型配置入口（本地 chat LLM 三键面——Modal 就地承载；开态门控查询零扰动） */}
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
        </div>
      </div>
      {/* 会话流（完整历史——b2 凝缩摘要面退役） */}
      <div
        className="wp-v4-dock-main"
        data-testid="wp-v4-ai-log"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 16,
          padding: "16px 18px",
        }}
      >
        {history.isError ? (
          <div data-testid="wp-v4-ai-history-error" style={{ color: "var(--wp-error)", fontSize: 11 }}>
            会话读取失败（中继不可达）——发送仍可尝试
          </div>
        ) : null}
        {messages.length === 0 && !history.isError ? (
          <div style={{ color: "var(--wp-text-2)", fontSize: 11.5, padding: "12px 0" }}>
            {EMPTY_CHAT_HINT}
          </div>
        ) : null}
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {send.isPending ? (
          <div style={{ color: "var(--wp-accent)", fontSize: 11 }}>发送中…</div>
        ) : null}
      </div>
      {/* composer（稿 .chat-composer：框式 textarea+键位注+发送钮） */}
      <div style={{ flex: "none", padding: "10px 14px 14px", borderTop: "1px solid var(--wp-border-2)" }}>
        <div
          style={{
            border: "1px solid var(--wp-border)",
            borderRadius: 6,
            background: "var(--wp-bg-elevated)",
          }}
        >
          <textarea
            data-testid="wp-v4-ai-input"
            aria-label="AI 消息输入"
            placeholder={EMPTY_CHAT_HINT}
            value={draft}
            rows={3}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
            style={{
              display: "block",
              width: "100%",
              boxSizing: "border-box",
              border: "none",
              outline: "none",
              resize: "vertical",
              background: "transparent",
              color: "var(--wp-text)",
              fontSize: 12,
              lineHeight: 1.6,
              padding: "8px 11px",
              minHeight: 56,
            }}
          />
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 10,
              padding: "6px 9px 8px",
            }}
          >
            <span style={{ color: "var(--wp-text-3)", fontSize: 10.5 }}>{COMPOSER_HINT}</span>
            <button
              type="button"
              data-testid="wp-v4-ai-send"
              onClick={submit}
              disabled={send.isPending}
              style={{
                border: "1px solid var(--wp-accent)",
                borderRadius: 4,
                padding: "3px 12px",
                fontSize: 11,
                background: send.isPending ? "var(--wp-bg-deep)" : "var(--wp-accent)",
                color: send.isPending ? "var(--wp-text-3)" : "var(--wp-on-accent)",
                cursor: send.isPending ? "default" : "pointer",
              }}
            >
              发送
            </button>
          </div>
        </div>
      </div>
      {/* 模型配置 Modal（本地 chat LLM 三键——footer=null=区块自带保存钮；open 门控查询零扰动） */}
      <Modal
        title="模型配置"
        open={llmOpen}
        onCancel={() => setLlmOpen(false)}
        footer={null}
        width={520}
      >
        <LlmConfigSection enabled={llmOpen} />
      </Modal>
    </section>
  );
}
