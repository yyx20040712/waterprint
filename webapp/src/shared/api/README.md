# shared/api —— 服务端耦合唯一入口

- `generated/`：orval 生成的 TS 类型 + TanStack Query hooks
  （**生成物禁手改、不入库**；重新生成：服务端导出 openapi.json → `pnpm orval`）；
- `http.ts`：请求实例（baseURL /api、错误归一化 WaterprintApiError）——
  orval mutator 引用此处，是本目录唯一允许手写的文件；
- `token.ts`：API token 存取（R2-A 批2）——localStorage 单键
  `waterprint.api_token` 三函数（getApiToken/setApiToken/clearApiToken，
  同步现读+node 环境守卫）；消费方=http.ts（Bearer 注入）+
  useTaskEventSource（SSE ？token=——连接级现取）+tokenSettingsModal
  （设置页）+App（首参引导写入）；
- `sseUrl.ts`：SSE 订阅 URL 单源（B6 批 D8，2026-09-06）——
  buildTaskStreamUrl(taskId, token)（useTaskFeed/useExportBatch 双实现
  下沉；taskId 路径段编码+token 非空 ？token= 查询通道——EventSource
  无法自定义头的现实通道）；消费方=useTaskEventSource 单点
  （B3-b 起 EventSource 建连唯一处）；
- `useTaskEventSource.ts`：任务 SSE EventSource 生命周期单源（B3-b
  《裁决书》方案二 2b——useTaskFeed/useExportBatch 双实现收敛）——
  useTaskEventSource 长订阅 hook（退避/慢探测恢复态机+onConnection
  四态〔F2 B-2 增 'polling' 降级标记〕+probing 周期任务状态轮询兜底
  〔probeTaskStatus 可注入，默认 probeTaskStatusTerminal 走既有
  GET /api/calc/tasks/{task_id}——轮询得终态即同款收口转 onTerminal〕）
  +subscribeTaskEvents 命令面（一次性等待——浏览器内建自动重连
  保留，失败计数/超时治理归消费方）+TaskEventReading 解读协议
  （畸形丢弃/健康/终态三态——解析归约注入归消费方）+重连纯函数族
  （nextReconnectDelayMs/planRecovery）；消费方=useTaskFeed（归约薄壳
  ——solutions）+useExportBatch（awaitTerminal——drawings）+ChatPane
  （ai_chat——F2 批 R2 起）；
- 契约漂移防线：CI 校验 openapi.json 与服务端实际 schema 一致
  + 前端客户端必须同源生成（§6.7 类型单一源头）。

**禁止**：手写任何 request/response 类型（双份类型 = 漂移起点，教训 A2）。
