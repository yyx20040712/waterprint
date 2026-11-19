# ADR-027：agent 面去 harness 化（MCP 面退役，只留本地 chat）

- 状态：**已接受**（用户裁决 2026-11-19：彻底取消与 ZCode 等外部 harness
  联动的内容，只保留本地的；e2e golden 改直驱保留与测试锁面重锁一并授权）。
- 背景：
  - agent 面原为两入口：MCP server（ADR-021，ZCode 等 MCP 宿主 stdio
    挂载驱动 23 工具）+ 本地 chat CLI（`python -m waterprint_agent.chat`，
    经 server ai_chat 子进程桥供 webapp 对话）。
  - 调查实证（2026-11-19）：chat 面零 MCP 协议依赖（toolspec.dispatch
    经 importlib 直调 `_*_impl`），两面共享 context/sandbox/pathguard/
    sessionlog 与 tools impl；server 侧 ai_connection 服务纯为 ZCode 接入器
    （向 `.zcode/config.json` 写 waterprint-mcp 注册条目），无本地对话职责。
  - 用户裁决取消外部 harness 联动面。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **MCP 面整体退役**：删 `main.py`、`agent/skills/`（ZCode 技能文档）、tools 七件的 register()/`wp_*` async 包装与 fastmcp 依赖、`waterprint-mcp` script 入口 | chat 面零依赖该层；保留即 MCP 期死壳（无生产消费面，仅锁定测试直调） |
| D2 | **server ai_connection 端点族退役**：删 services/routers 两件与 main_lib 异常映射行；openapi 再生 47→45 操作 | 该服务唯一职责=向 ZCode 注册 MCP；`/api/ai/config`（本地 LLM 三键配置）保留不动 |
| D3 | **toolspec 成为唯一工具 schema 真源**：23 工具清单、签名与分发全在 `chat/toolspec.py`；工具测试与 e2e golden 改经 `toolspec.dispatch` 生产路径驱动（原 fastmcp 客户端驱动退役） | 消除 _SPEC 对 MCP schema 的手工镜像无对账债；测试锚生产路径 |
| D4 | **沿承件**：沙箱五区+PathGuard 唯一 IO 门、会话审计链（sessionlog 脱敏三条款）、私有 Manager 装配填充（原 ADR-021 D2~D4 语义在 chat 面继续适用）；LLM 配置 UI（LlmConfigSection/useAiConfig）随端点保留迁入 ai_chat 切片、挂 dockBar AI 窗「模型配置」 | 本地面既有防线与可审计性不随 MCP 面退役而损失 |
| D5 | **ADR 关系**：ADR-021 整体 superseded（D1 同步调用语境随 MCP 消失）；ADR-020 分层契约继续适用（import-linter+check_module_graph L6 校验面不变）；ADR-019/022 不受影响 | 边界澄清；历史决策不改正文，由本 ADR 记 delta |

- 后果：
  - 正面：外部 harness 联动面清零（fastmcp 依赖、ZCode 注册器、技能文档
    全退役）；工具 schema 单源；agent 包依赖面缩小（uv.lock −1007 行）。
  - 代价：MCP 宿主无法再挂载 waterprint——如需恢复外部 AI 宿主接入，
    须新 ADR 重立项（D4 沿承件可直接复用）。
  - 锁面：test-lock 383→380 键（agent −test_main_smoke；server −两件
    ai_connection 测试），重锁经用户授权。
  - 关联：ADR-019/020/021（superseded）/022。
