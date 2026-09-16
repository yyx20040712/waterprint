# ADR-021：agent 面运行模型（MCP 同步调用 + 私有 Manager + 沙箱隔离）

- 状态：**已接受**（同 ADR-019 授权链；用户裁决 R1 复用 ZCode/R4
  沙箱隔离/U1 fastmcp 依赖批准/U3 沙箱默认根）。
- 背景：
  - server 侧异步任务面（Manager 进程池+SSE）为 webapp 多用户设计；
  agent 面单用户本机场景下引入进程池+SSE 是纯成本。
  - benchmark 证据：run_full_calc（19 节点 5 工况 golden）<5s、
    design_map ≤2500 点 ~1s——同步直调完全可行。
  - ServiceContext.manager 为必填字段（frozen dataclass 无默认值），
    "不装 Manager"不可行（E2 实证）。
  - 用户裁决 R4：agent 默认不写正式 projects 区。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **同步调用模型**：MCP 工具内直调 core flows（同步返回），不提交后台任务、不引入 SSE；若未来工况规模突破 stdio 客户端超时，对策=客户端超时配置而非引入异步任务面 | 秒级计算不需要任务面；Manager 注册表单进程内存态与 webapp 本就不互通，引入只增复杂度 |
| D2 | **私有 Manager 装配填充**：AgentContext 构造 ThreadPoolExecutor(max_workers=1)+运行环+沙箱内 registry/cancel 目录的 Manager 实例——仅满足 ServiceContext 必填约束，不 start、不提交任务 | E2 实证路径；零 server 代码改动 |
| D3 | **沙箱隔离**：默认根 `E:\class\智水蓝图\ai-sandbox`（env WATERPRINT_AI_SANDBOX 覆盖，须 Windows 原生路径——POSIX 形态会静默回落，fail-fast 提示挂账）；五区 projects/exports/results/sessions/reports；PathGuard 唯一 IO 门（realpath+normcase 解 junction/盘符大小写，前缀逃逸/UNC/跨盘符拒）；正式区只读装载（open_readonly_external），改必先 save_as 落沙箱；沙箱→正式区提升通道不提供（用户裁决 T3） | R4 隔离语义；Windows 路径攻击面实证（乙轨测试覆盖） |
| D4 | **会话追溯链**：sessions/{session_id}.jsonl 逐事件（指令/工具调用/参数 patch 改前改后与被拒条目）→design_digest→计算迹→产物 .meta.json 八键，逐字段可对账；脱敏三条款（沙箱内相对化/正式区哈希/env 值掩蔽）——先路径后环境变量的顺序铁律（反序泄漏盘符前缀，实测复现） | 与既有 repro 三元组衔接成完整链条"会话→参数→计算迹→产物" |
| D5 | **SDK 选型**：FastMCP 3.0（pin >=3.0,<3.1，实测 3.0.2），懒加载（顶层零 core/server import，spawn→tools/list 实测 1.43s<1.5s 目标）；协议不兼容时降级官方 SDK 旧 API 面（工具函数体不动） | DX 与文档生态最优且与官方 SDK 同源；T1 挂载机制已结案（ZCode 工作区 .zcode/config.json mcp.servers stdio 自动连接） |

- 后果：
  - 正面：零 server 改动获得全 services 能力；写操作被沙箱+PathGuard
    双闸约束；会话可审计。
  - 代价：agent 与 webapp 两进程 Manager 不互通（任务历史隔离——
    接受）；沙箱路径 env 需原生路径（fail-fast 挂账）。
  - 关联：ADR-019/020/022。
