# server —— FastAPI 服务层

HTTP 编排层：`routers`（薄协议转换）→ `services`（用例编排，只调 core L4）
→ `jobs`（进程池调度）。业务计算全部在 `../core`，本包零计算。

> 当前状态：M2 已实装+FE 批扩面——25 源文件全实现+21 镜像测试
> 文件全激活（94 用例 0 skip——S2 落盘化批后实测）；OpenAPI 契约导出就绪（api-contracts/）。

## 分层规则（import-linter 机器强制，违反即失败）

`uv run lint-imports`（须在本目录下跑）两契约：

- 分层只许向下：`main → routers → services → jobs → settings`；
  router 文件 ≤150 行、禁业务逻辑；service 禁 import fastapi；
  job 只做序列化与 core 调用。
- core 调用只经 `waterprint.app` 与 `waterprint.contracts`（UF-33
  单入口——直连 solution/trace/graph/units_lib/registry/project 即红）。
- 领域异常 → HTTP 映射集中在 `main.py`（core 禁抛 HTTP 语义异常）。

## 启动

```bash
cd server
uv sync --frozen
uv run uvicorn waterprint_server.main:app --reload
```

环境变量（前缀 `WATERPRINT_`）：`PROJECTS_DIR`/`EXPORTS_DIR`/`DATA_DIR`
（三路径基点，默认 CWD 相对）、`CALC_WORKERS`（进程池大小，默认 CPU−1，
<1 启动即败）等——全字段见 `waterprint_server/settings.py` 规格头。

## 测试与契约

```bash
uv run pytest            # server/tests（21 文件 94 用例，全激活零 skip）
uv run python -m waterprint_server.dump_openapi   # OpenAPI → api-contracts/
```

```
tests/
├─ conftest.py               # test_settings/client(ASGITransport AsyncClient)
│                            #   /service_ctx 三 fixture + anyio 后端
├─ test_api_contract.py      # OpenAPI 契约（端点集 23/无 Any 泄漏/404-422-501/穿越 4xx）
├─ test_settings.py / test_app_factory.py
├─ routers/                  # 六路由器镜像（端点集逐件恰等/stale 409/幂等/SSE 头）
├─ services/                 # 六服务镜像（design_changed/回滚/无解 done/确定性命名）
└─ jobs/                     # manager/worker（优先级出队/取消丢弃/spawn 零副作用/文件句柄/终态落盘恢复）
```

镜像测试经 test-lock.manifest.json 只读锁定（AGENTS §7——变更测试=
显式事件走解锁流程）。核心用例四件（全流程计算/枚举/导出/项目 IO）
经 `waterprint.app` 正门接线，worker kind 映射表集中一处
（`jobs/worker.py` `_KIND_RUNNERS`）。
