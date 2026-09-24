# ai_chat —— 设计对话

自然语言设计助手 pane（B4-4b 子批 2 2026-09-24）：浮层 Drawer 形态（零路由破面
——aiconnect 先例），消费 /api/ai/sessions 三端点（清单/历史/发言→ai_chat 任务）；
对话编排真源=agent 环（server 薄中继+子进程桥，ADR-019 只编排不算数）。

## 文件清单（B4-4b 子批 2 实装 2026-09-24）

| 文件 | 职责 | 状态 |
|------|------|------|
| `api/useAiChat.ts` | orval 生成 hook 薄封装：useChatSessions（Drawer 开态门控）/useChatHistory（会话选中态门控）/useSendChatMessage（发言 mutation——sessionId 显式入参防态竞态） | B4-4b 实装 |
| `components/ChatPane.tsx` | Drawer 壳：hook 装配+任务 SSE 轮进度（TaskEventReading 三态协议——stage 文案经 sink 副作用外送）+终态历史失效刷新+首发客户端建档 ID（hex32 与 agent uuid4 同形态） | B4-4b 实装 |
| `components/ChatPanel.tsx` | 纯展示面板：会话切换 Select+消息流气泡（工具步卡行+截断标记）+轮进度行+输入框（busy 态禁发） | B4-4b 实装（6 测试绿） |
| `components/ToolCallCard.tsx` | 工具步折叠卡（✓/✗/进行中三态——社区基线「工具调用可见」） | B4-4b 实装（3 测试绿） |

## 规格要点

- 消息传输：POST 发言→task_id→**既有** GET /api/events/tasks/{id} SSE（SseLimiter
  四维零改——每轮=一任务）；进度=stage 中文标签（worker 桥从 agent JSONL 事件译）；
- 会话真源=agent 沙箱 JSONL（server 经 agent CLI 子进程读——零格式耦合，502 面）；
- 降级模式：LLM 三键未配置时 agent 环自动降级关键词直译（建项+计算），pane 无感
  透传 assistant 文本；
- 前端零 LLM 逻辑（智能在 agent 环——分层铁律）。
