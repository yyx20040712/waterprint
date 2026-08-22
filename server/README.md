# server —— FastAPI 服务层

HTTP 编排层：`routers`（薄协议转换）→ `services`（用例编排，只调 core L4）
→ `jobs`（进程池调度）。业务计算全部在 `../core`，本包零计算。

> 当前状态：M0 骨架——全部文件仅含契约头+规格说明，无实现。

## 分层规则（CI 强制，违反即失败）

- router 文件 ≤150 行、禁业务逻辑；service 禁 import fastapi；
  job 只做序列化与 core 调用。
- core 调用只经 `waterprint.app`（L4 正门）。
- 领域异常 → HTTP 映射集中在 `main.py`（core 禁抛 HTTP 语义异常）。

## 启动（环境就绪后）

```bash
cd server
uv sync
uv run uvicorn waterprint_server.main:app --reload
```

## 测试

```bash
uv run pytest            # server/tests（12 个镜像测试文件，只读锁定）
```

```
tests/
├─ conftest.py               # fixtures 装配（实现期补 client/test_settings）
├─ test_api_contract.py      # OpenAPI 契约（端点集/无 Any 泄漏/路径安全）
├─ test_settings.py / test_app_factory.py
├─ routers/                  # 四路由器镜像（端点集/stale/幂等/SSE 头）
├─ services/                 # 四服务镜像（原子性/守护/确定性命名）
└─ jobs/                     # manager/worker（状态机/spawn 零副作用/IPC）
```

休眠机制与 core 同款：符号缺失自动 skip 并注明原因；skip 数随里程碑归零。
