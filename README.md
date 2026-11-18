# WaterPrint 智水蓝图

污水处理工艺设计计算平台：在节点画布上布置工艺单元、连线成全厂流程，
平台完成水力/水质/泥量计算、方案枚举与约束校核，产出概算、图纸、
三维布置与计算说明书。覆盖市政污水与矿井水两条工艺线（32 个工艺单元包）。

## 仓库布局

```
core/           计算内核（纯 Python，分层 L0~L4）
server/         FastAPI 服务（routers → services → jobs）
webapp/         React 前端（feature 切片，React Flow 画布 + R3F 三维）
agent/          MCP server（AI 宿主接入面）
data/           版本化数据包（assumptions/coefficients/constraint_kb/templates/unit_prices，全部带出处）
api-contracts/  OpenAPI 契约源（前端客户端由此生成）
docs/           工程文档（architecture/adr/结构图谱/文件职责表/规范摘录）
scripts/        CI 门禁脚本（纯标准库）
deploy/         Docker 双容器编排
tools/          Blender 参数化建模管线等工具链
```

## 快速开始（Linux）

```bash
# 计算内核：测试 + 架构门禁
cd core && uv sync && uv run pytest
cd .. && python3 scripts/run_gates.py

# 服务（默认只听 127.0.0.1:8000；数据包缺省自动定位 <仓库根>/data）
cd server && uv sync && uv run python -m waterprint_server.main

# 前端
pnpm install && pnpm -C webapp dev
```

## 部署（Docker 双容器）

```bash
docker compose -f deploy/compose.yml up -d --build
# 就绪后入口 = http://localhost:8080（唯一对外端口；server 8000 不出容器网桥）
```

对外可达的部署必须配置 `WATERPRINT_API_TOKEN`（安全红线与环境变量细目见
[docs/architecture.md](docs/architecture.md) §4）。

## 核心使用流程

1. 新建/导入项目 → 画布（canvas）布置工艺单元并连线；
2. 在参数面板（params）调整单元参数，可叠加假设覆盖；
3. 提交计算 → 任务面板跟踪 → 结果/警告聚合视图（跨工况去重）；
4. 无可行解时诊断面板给出调节建议（参数键/方向/幅度/依据）；
5. 导出：xlsx 概算 / DXF 图纸 / HTML 报告 / PDF 计算书 / IFC 三维。

## 文档索引

| 文档 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | 启动约束、常用命令、文档路由 |
| [docs/architecture.md](docs/architecture.md) | 工程架构（目标/边界/模块/部署/决策索引/风险与术语） |
| [docs/file-contracts.md](docs/file-contracts.md) | 逐文件职责表（机器校验） |
| [docs/structure-graph.md](docs/structure-graph.md) | 模块依赖/调用链/单元业务身份（机器校验） |
| [docs/adr/](docs/adr/) | 决策记录（ADR-001~026） |
| [docs/norms/](docs/norms/) | 规范摘录与手算对照表（测试期望唯一合法来源） |
| [docs/status.md](docs/status.md) | 项目计数（生成物） |
| [docs/archive/](docs/archive/) | 历史文档（默认不读） |

## 测试与门禁

pytest（core/server 分目录运行）+ vitest（webapp）；`python3 scripts/run_gates.py`
聚合全部架构门禁。测试目录只读（哈希清单校验），修改测试是人类显式流程，
详见 [docs/architecture.md](docs/architecture.md) §4.6。一切计数以
[docs/status.md](docs/status.md) 生成值为准，文档不手写数字。
