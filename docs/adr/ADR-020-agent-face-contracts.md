# ADR-020：agent 面分层契约（UF-33 扩展 + audit 例外通道）

- 状态：**已接受**（同 ADR-019 授权链；对抗审核 B1 分层倒置项的
  终裁处置——core import-linter 实证 layers 链 cli 为 core 最高层，
  "core 之外共享层被 CLI import"属非法倒置）。
- 背景：
  - UF-33 既有铁律：server 只许经 waterprint.app 单入口消费内核，
    禁直连 L1~L3。agent 面是新增第四消费方（server/webapp/CLI 后），
    需要同款边界。
  - 审计报告（render_audit_html）位于 trace.audit，不在 app 门面
    再导出面——CLI 已有直连先例（M4a ③）。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **agent 面 import 白名单**：`waterprint.app`、`waterprint.flows`（ADR-022）、`waterprint.contracts.*`（L0 类型面）、`waterprint_server.{services,settings,jobs.manager}`；禁 core L1~L3 直连、禁 fastapi/starlette、禁 waterprint.cli | 与 server 同款"只经正门"纪律；services 层实证零 web 框架依赖可进程内复用（grep 全目录无 fastapi/starlette import） |
| D2 | **audit 例外通道**：audit HTML 渲染的正门=`flows.audit_render_flow`/`flows.export_flow("audit")`（core 内部调 trace.audit 天然合法）；agent 面直连 waterprint.trace.audit 仅作后备例外，须在本 ADR 登记（agent/pyproject.toml 的 ignore_imports 挂起注记随导出批落地恢复——正门已通则豁免保持注释态） | 单一真源优先；CLI 先例（export audit 直调 trace.audit）在 flows 落地后收敛为 flows 单源 |
| D3 | **契约机器化**：agent/pyproject.toml import-linter 双根（waterprint_agent+waterprint，SERVER D7 先例）+ forbidden 契约两条（L1-L3/cli/fastapi 面；trace 面）+ allow_indirect_imports=true（直查口径） | 无机器强制的边界=纸面边界；负向探针实证（注入 waterprint.graph import→exit 1） |
| D4 | **共享编排落 core.flows 而非"core 之外的共享层"**：CLI（core 内最高层）与 agent 面均向上 import flows——消除 cli→外层包的倒置环 | 对抗审核 B1 终裁；E4 实证 |

- 后果：
  - 正面：agent 面与既有面同纪律同机器闸；audit 渲染单一真源。
  - 代价：agent 面依赖 waterprint-server 包（path 依赖引入 fastapi
    等传递依赖装进 agent 环境——仅安装面无 import 面，lint 拦）。
  - 关联：ADR-021（装配模型）、ADR-022（flows 层）。
