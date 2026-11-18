# AGENTS.md —— WaterPrint

> 规则的执行权威是门禁脚本（`scripts/run_gates.py` 一键全跑，逐门说明
> 见 `scripts/README.md`）。本文件只载启动约束、硬约束、常用命令与文档路由。

## 启动约束

1. 读 `docs/architecture.md` 了解工程现状；
2. 动代码前查两表：`docs/file-contracts.md`（文件职责）与
   `docs/structure-graph.md`（模块依赖与调用链）；
3. 读目标文件头部"规格说明"与对应镜像测试（`core/tests/**/test_*.py`，
   正确行为的定义）；
4. 规格与 `docs/architecture.md` 横切约定均无答案时停下来问，
   不就地自创语义。

## 硬约束

以下条目后果重或需人类流程，未跑门禁也应知悉；其余代码规则
（分层依赖、行数预算、占位实现、裸 except、魔法数字、模型代号）
由门禁强制，细则见 `scripts/README.md`。

- 测试目录由 `test-lock.manifest.json` 哈希锁定（`core/tests/`、
  `server/tests/`、units_lib 包内 `tests/`、`agent/tests/`）：修改测试
  与 manifest 属人类显式流程（`scripts/lock_tests.py`）。
- 生成物禁手编：`docs/status.md`（`gen_status.py` 单源）、structure-graph
  节点表与同层边声明块、file-contracts 的路径与导名列。
- 新源码文件先登记 `docs/file-contracts.md` 职责表（CI 双向校验）。
- 全部文件 UTF-8；Python 写文件显式 `encoding="utf-8"`。
- 提交信息中文、一个 commit 一个目的、首行完整一句话。

## 常用命令

```bash
# 计算内核（uv）
cd core && uv sync && uv run pytest

# 门禁全跑（零依赖，系统 Python 直跑）
python3 scripts/run_gates.py

# 服务（默认只听 127.0.0.1:8000；数据包缺省自动定位 <仓库根>/data）
cd server && uv sync && uv run python -m waterprint_server.main

# 前端（pnpm）
pnpm install && pnpm -C webapp dev

# 部署（Docker 双容器，唯一对外入口 http://localhost:8080）
docker compose -f deploy/compose.yml up -d --build

# 状态计数再生成与校验（docs/status.md 为生成物）
python3 scripts/gen_status.py --check
```

## 文档路由

| 文档 | 内容 |
|---|---|
| `docs/architecture.md` | 当前工程现状（架构/横切约定/部署/质量与风险） |
| `docs/file-contracts.md` | 逐文件职责表（机器校验） |
| `docs/structure-graph.md` | 模块依赖/调用链/单元业务身份（机器校验） |
| `docs/adr/` | 决策记录 |
| `docs/norms/` | 规范摘录与手算对照表（测试期望唯一合法来源） |
| `docs/status.md` | 项目计数（生成物，`gen_status.py` 单源） |
| `docs/archive/` | 历史文档与被替代材料（默认不读；`archive/README.md` 有新旧映射与旧宪法节号对照） |

行为或约束变化时，同批更新受影响的活文档。

## 多代理协作

协作系统=dev-troupe（五岗：research/planner/executor/reviewer/vision）。
工作区目录地图与环境事实见工作区根 `AGENTS.md`
（`/home/yyx/work/智水蓝图/AGENTS.md`）；过程文档放工作区
`.zcode/dev-troupe/<task>/`，不入本仓。
