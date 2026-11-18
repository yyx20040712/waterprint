# server —— FastAPI 服务层

HTTP 编排层：`routers`（薄协议转换）→ `services`（用例编排，只调 core L4）
→ `jobs`（进程池调度）。业务计算全部在 `../core`，本包零计算。

> 当前状态：全实现、镜像测试全激活零 skip；OpenAPI 契约导出就绪
> （api-contracts/）。计数以 `../docs/status.md` 生成值为准。

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
uv run python -m waterprint_server.main   # 默认只听 127.0.0.1:8000（settings host/port）
```

开发态热重载：`uv run uvicorn waterprint_server.main:app --reload
--host 127.0.0.1`（省略 --host 时 uvicorn 默认亦绑 127.0.0.1；对外绑定
是显式信任决策，须配 `WATERPRINT_API_TOKEN`：除公开只读 GET 外全部操作
受保，token 空=鉴权关；见 docs/architecture.md §4.1 安全红线）。

环境变量（前缀 `WATERPRINT_`）：`PROJECTS_DIR`/`EXPORTS_DIR`（CWD 相对，
exports 构造期绝对化）、`DATA_DIR`（数据包根，缺省=包定位自动探测；
assumptions 包例外见 architecture §6.1）、`CALC_WORKERS`（进程池大小，
默认 max(1, CPU−1)，<1 启动即败）、`HOST`/`PORT`（绑定面，默认
127.0.0.1:8000）等——全字段见 `waterprint_server/settings.py` 规格头。

## 测试与契约

```bash
uv run pytest            # server/tests（全激活零 skip；计数见 docs/status.md）
uv run python -m waterprint_server.dump_openapi   # OpenAPI → api-contracts/
```

```
tests/
├─ conftest.py               # test_settings/client(ASGITransport AsyncClient)
│                            #   /service_ctx 三 fixture + anyio 后端
├─ test_api_contract.py      # OpenAPI 契约（端点集恰等/无 Any 泄漏/404-422-501/穿越 4xx）
├─ test_settings.py / test_app_factory.py
├─ routers/                  # 路由器镜像（端点集逐件恰等/stale 409/幂等/SSE 头）
├─ services/                 # 服务镜像（design_changed/回滚/无解 done/确定性命名）
└─ jobs/                     # manager/worker（优先级出队/取消丢弃/spawn 零副作用/文件句柄/终态落盘恢复）
```

镜像测试经 test-lock.manifest.json 只读锁定（AGENTS 硬约束·测试只读——
变更测试=显式事件走解锁流程）。核心用例四件（全流程计算/枚举/导出/项目 IO）
经 `waterprint.app` 正门接线，worker kind 映射表集中一处
（`jobs/worker.py` `_KIND_RUNNERS`）。
