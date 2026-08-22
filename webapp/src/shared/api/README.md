# shared/api —— 服务端耦合唯一入口

- `generated/`：orval 生成的 TS 类型 + TanStack Query hooks
  （**生成物禁手改、不入库**；重新生成：服务端导出 openapi.json → `pnpm orval`）；
- `http.ts`：请求实例（baseURL /api、错误归一化 WaterprintApiError）——
  orval mutator 引用此处，是本目录唯一允许手写的文件；
- 契约漂移防线：CI 校验 openapi.json 与服务端实际 schema 一致
  + 前端客户端必须同源生成（§6.7 类型单一源头）。

**禁止**：手写任何 request/response 类型（双份类型 = 漂移起点，教训 A2）。
