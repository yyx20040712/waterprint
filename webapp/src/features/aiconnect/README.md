# aiconnect —— AI 接入配置

AI 接入 Modal（AI2 批 2026-09-13 起）：Zcode 工具接入（MCP）状态四项检查+一键接入；
F1 批（2026-09-25）增挂聊天模型接入（LLM）配置区——对话 pane 的模型三键+超时
产品内可达配置面（修「AI 管线 LLM 三键全环境零配置」第一根因；MCP 面与聊天
LLM 面相互独立的显式声明——语义误导 R2 修复）。

## 文件清单（新文件先登记本清单——file-contracts.md §5 委托面）

| 文件 | 职责 | 状态 |
|------|------|------|
| `api/useAiConnection.ts` | orval 生成 hook 薄封装：status 查询（enabled 门控）+setup mutation（onSuccess invalidate 状态键） | AI2 实装（2026-09-13） |
| `api/useAiConfig.ts` | orval 生成 hook 薄封装：config 查询（enabled 门控）+保存 mutation（onSuccess invalidate 配置键） | F1 实装（2026-09-25） |
| `components/AiConnectButton.tsx` | 顶栏入口按钮（App.tsx 挂载受控 Modal） | AI2 实装 |
| `components/AiConnectModal.tsx` | Modal 门户壳：MCP 区块标题（「Zcode 工具接入（MCP）——与下方聊天模型相互独立」，F1 改题）+AiConnectPanel+LlmConfigSection 下挂（enabled=open 同门控） | AI2 实装；F1 增挂（2026-09-25） |
| `components/AiConnectPanel.tsx`（AiConnectModal.tsx 内） | 纯展示面板：四项 ✓/✗ 列表+ready 横幅+一键接入按钮+成功引导/失败展示（props 注入句柄——面板测试零 mock 直构） | AI2 实装 |
| `components/LlmConfigSection.tsx` | 聊天模型（LLM）配置区：三键+超时表单（api_key 永不回显——has_api_key 占位符）+configured 状态行+保存动作（buildSavePayload 纯函数：api_key 空输入不发送防误清除） | F1 实装（2026-09-25） |
| `components/AiConnectButton.test.tsx` | 入口按钮 vitest | AI2 实装 |
| `components/AiConnectModal.test.tsx` | 面板渲染/一键接入/成功引导/失败面 vitest（SSR renderToString 先例件）+useAiConnection Probe | AI2 实装；F1 增 MCP 区块标题断言（2026-09-25） |
| `components/LlmConfigSection.test.tsx` | 配置区渲染面/保存载荷/回填口径 vitest（buildSavePayload 纯函数直测+useAiConfig mock 穿线） | F1 实装（2026-09-25） |

## 规格要点

- MCP 面：GET /api/ai/connection 四项检查+POST setup 一键接入（业务全在
  services.ai_connection——server 面）；
- LLM 面（F1）：GET/PUT /api/ai/config（三键+超时；api_key 明文任何面禁回传）；
  保存成功 toast「已写入 .env 并即时生效（无需重启）」；
- 载荷纪律：api_key 空输入=键缺席（密钥不回显故空≠清除）；base_url/model
  恒发送（回显值原样重写无副作用；清空=显式清除）；config 未加载=空载荷
  且保存钮禁用（未知现值上禁盲写）。
