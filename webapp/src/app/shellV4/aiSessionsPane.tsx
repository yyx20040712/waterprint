/**
 * AI 设计会话侧栏（b4 功能面重涂 II 批 2026-11-19——稿 ai.html 左栏：
 * 新建会话+当前项目会话清单+本地沙箱说明；会话切换=sessionId 视图态
 * 上抛〔aiZone 单源〕，数据面=useChatSessions 既有端点只读消费）。
 *
 * 输入:  sessionId（当前会话——aiZone 视图态）+onSessionChange（切换/
 *        新建上抛：null=新会话〔下次发送建档〕）+projectId（当前项目
 *        ——会话清单 project_id 过滤面）
 * 输出:  左栏：pane-head〔设计会话〕+新建会话钮+「当前项目」会话行族
 *        〔标题+轮次副行+选中态〕+读取失败/空态行+底注 notice
 *
 * 规格说明（b4 批准稿 ai.html 左栏段——信息组织重造，数据流零变）：
 *   - 会话清单=GET /api/ai/sessions 只读消费（ChatSeat 同端点；开态
 *     门控=本页常开——AI 页即会话面）；project_id 过滤=当前项目子集，
 *     他项目/无归属行不入列（诚实分组——不虚造全局清单语义）；
 *   - 新建会话=视图态复位（sessionId→null：下次发送 generateSessionId
 *     建档——与 ChatSeat 新建同链，零新 API）；进行中会话不丢弃——
 *     清单可切回；
 *   - 标题缺席=「未命名会话」回退；turns 缺席=副行只显会话 id 前缀。
 */
import { useChatSessions } from "../../features/ai_chat/api/useAiChat";

/** 底注说明（稿 ai.html 左栏 notice——白名单：说明文案）。 */
const SESSIONS_NOTICE = "会话由本地 agent 沙箱保存。发送失败时保留输入草稿。";
/** 未命名回退（白名单：显示回退）。 */
const UNTITLED = "未命名会话";

export function AiSessionsPane({
  sessionId,
  projectId,
  onSessionChange,
}: {
  /** 当前会话 id（null=新会话未建档）。 */
  sessionId: string | null;
  /** 当前项目 id（会话清单过滤面）。 */
  projectId: string | null;
  /** 会话切换上抛（null=新建复位）。 */
  onSessionChange: (sessionId: string | null) => void;
}) {
  const sessionsQuery = useChatSessions(true);
  const sessions = (sessionsQuery.data ?? []).filter(
    (session) => projectId !== null && session.project_id === projectId,
  );
  return (
    <aside className="wp-v4-pane left" data-region="ai-sessions" style={{ width: 198 }}>
      <div className="wp-v4-pane-head">
        <h3>设计会话</h3>
        <span className="wp-v4-badge">{sessions.length} 会话</span>
      </div>
      <div className="wp-v4-pane-body">
        <div style={{ padding: "8px 10px" }}>
          <button
            type="button"
            data-testid="wp-v4-ai-new-session"
            onClick={() => onSessionChange(null)}
            style={{
              width: "100%",
              border: "1px solid var(--wp-accent)",
              borderRadius: 4,
              background: "var(--wp-accent)",
              color: "var(--wp-on-accent)",
              fontSize: 11,
              padding: "4px 8px",
              cursor: "pointer",
            }}
          >
            ＋ 新建会话
          </button>
        </div>
        <div className="wp-v4-insp-sec" style={{ paddingTop: 0 }}>
          <h4>当前项目</h4>
          {sessionsQuery.isError ? (
            <p style={{ color: "var(--wp-text-2)", fontSize: 11 }}>会话清单读取失败</p>
          ) : sessionsQuery.isPending ? (
            <p style={{ color: "var(--wp-text-2)", fontSize: 11 }}>正在读取会话…</p>
          ) : sessions.length === 0 ? (
            <p data-testid="wp-v4-ai-sessions-empty" style={{ color: "var(--wp-text-2)", fontSize: 11 }}>
              尚无本项目会话——发送首条消息自动建档
            </p>
          ) : (
            <div className="wp-v4-list">
              {sessions.map((session) => {
                const selected = session.session_id === sessionId;
                return (
                  <button
                    key={session.session_id}
                    type="button"
                    data-testid="wp-v4-ai-session-row"
                    className={selected ? "wp-v4-row selected" : "wp-v4-row"}
                    style={{ minHeight: 34 }}
                    onClick={() => onSessionChange(session.session_id)}
                  >
                    <span className="main">
                      <span className="t" style={{ fontFamily: "inherit" }}>
                        {session.title?.trim() ? session.title : UNTITLED}
                      </span>
                      <span className="s">
                        {session.turns !== undefined
                          ? `${session.turns} 轮对话 · ${session.session_id.slice(0, 8)}`
                          : session.session_id.slice(0, 8)}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
        <div className="wp-v4-pane-foot">{SESSIONS_NOTICE}</div>
      </div>
    </aside>
  );
}
