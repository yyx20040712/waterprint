# ADR-022：core.flows 用例流层（CLI 与 agent 面的共享编排层）

- 状态：**已接受**（同 ADR-019 授权链；主控终裁 E4——对抗审核 B1
  分层倒置项的架构裁定）。
- 背景：
  - CLI（core/waterprint/cli.py）与 agent 面 MCP 工具都需要同一段
    用例编排（装载→环境装配→计算→序列化落盘→导出/审计渲染）。
  - "禁两套业务逻辑"（v2 设计 D6）要求共享；但共享层放哪决定分层
    合法性：cli 在 core 分层链最高层（L4.cli→L4.app→…），任何
    "core 之外的共享层"被 CLI import 都是包级倒置（import-linter
    实证）。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **flows 落 core 内新模块 `waterprint/flows`，分层位置=cli 之下、app 伴生件之上**（layers 链：cli → flows → app\|app_enumeration\|app_export → project\|trace → L3 → …）；flows 禁依赖 server/cli/fastapi，许可=app 门面+contracts+trace.audit（audit 渲染包装） | 共享点在内核侧=两壳（CLI/agent）都向上依赖，无倒置环；flows 是纯内核编排（不知道 HTTP/MCP 存在——与 core"不知道 React 存在"同哲学） |
| D2 | **公开签名 12 件冻结**（AI1 三轨并行契约面）：build_env_flow/build_condition_flow/build_standards_flow/run_calc_flow（CalcFlowResult）/result_persist_flow/validate_flow/export_flow(kind)/audit_render_flow/estimate_summary_flow（EstimateFlowResult）/enumeration_flow/design_map_flow/params_guard（ParamVerdict 清单式）；异常族 InvalidFlowError | 并行轨道按签名接线零漂移；params_guard 从 server calculation._validate_apply_params 提取（server 改整批拒转调，语义不变，AUDIT2 C-4 用例全绿实证） |
| D3 | **两壳分工**：CLI 壳=argparse+退出码 0/2/3/4+stdout 格式化，保持"用户态直接落文件、无边车"现状语义；agent 壳=工具注册+摘要压缩+沙箱/边车/会话日志（agent 面私有） | 用户态与 agent 态产物语义不同（无边车 vs 边车注册），各自壳层承接。**门一 W1/W6 追记（2026-09-13）**：两壳 conditions 缺省口径为有意的用户态差异——CLI 缺省=基线 design/avg 两档（人间保守缺省），agent 面 wp_run_calc 缺省=design.checked_units（对齐 server worker payload 语义，v2 D3 #8 原文）；两壳 help/工具描述各自明示，非漂移 |
| D4 | **形态=单文件 `flows/__init__.py`**（499 行）——check_structure 新文件须登记 file-contracts 与 tests/arch mirror 规则（每模块配 test_{stem}.py）双门禁约束下的豁免形态；契约头齐全 | 拆子模块必触两门禁（当时禁改）；本 ADR 落档后如需拆分按登记流程走 |
| D5 | **pint 契约 source 面纳入 flows**（集成批收口——轨道甲疑虑 1） | flows 与 cli/app 同层同守 ADR-002 边界 |

- 后果：
  - 正面：CLI 与 MCP 共享单一编排真源；server 参数守护收敛到
    flows.params_guard（消除影子实现）。
  - 代价：builtin kind 参数键面在 flows 内声明镜像（真源=graph.nodes
    `__init__` 校验，server units.py 同款声明面先例——影子双源挂账
    归数据批收敛）；engine_version 真源取 core `waterprint.__version__`
    （与 server settings 串并存记档）。
  - 关联：ADR-019/020/021。
