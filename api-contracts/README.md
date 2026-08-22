# api-contracts —— OpenAPI 契约源（单一事实源）

前后端唯一耦合面（§1 架构图）：FastAPI 自动生成 → 导出入库 → orval
生成前端 TS 客户端。**禁止手写双份类型**（教训 A2：任何"手动保持
两处一致"的约定注定失守）。

## 流水线

```
server (FastAPI)                     CI 契约漂移检查
  │ uv run python -m                     │ openapi.json 与服务端实际
  │ waterprint_server.dump_openapi       │ schema diff，漂移 = 失败
  ▼                                      ▼
api-contracts/openapi.json    ────►    webapp `pnpm orval`
                                         │
                                         ▼
                            webapp/src/shared/api/generated/
                            （TS 类型 + TanStack Query hooks，禁手改）
```

## 文件规划

- `openapi.json`：服务端导出的契约快照（M2 服务实现后首次生成入库）；
- 服务端启动期契约自检（main.py R3）+ CI 漂移检查双防线。

## 规则

1. openapi.json 只能由 `dump_openapi` 重新生成，禁手改；
2. 前端引用的任何类型必须来自 generated/（评审拒绝手写 interface
   复制服务端模型）；
3. 契约变更 = 重新导出 + orval 重跑 + 前端类型错误清零，一个提交内完成。
