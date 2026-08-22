# 智水蓝图（WaterPrint）monorepo

污水处理工艺设计计算平台：计算内核（纯 Python）+ FastAPI 服务 + React 前端。

> 当前状态：**M0.5 结构接线 + 计算路线拍板完成**——
> ① 三层结构关系物理化并机器强制：32 个工艺单元包骨架、结构图谱
> （`docs/structure-graph.md`）、webapp 43 个源文件契约头+分层；
> ② 方法路线与默认值由领域专家拍板（ADR-008 四条主线 / ADR-009 十六项）；
> ③ 业务逻辑规格层就位（`docs/business-logic.md`：参数初始化链 /
> 耦合单一归属 / 守恒断言 / 可行解迭代流程 / 约束联动 / 回路清单）；
> ④ 八道门禁全绿（`scripts/run_gates.py`，含魔法数字门禁）。
> 所有源码仍仅含"契约头 + 规格说明"，不含业务实现；实现工作自 M1 起。

## 快速导览（新成员/AI 按此顺序阅读）

1. `AGENTS.md` —— 项目宪法（硬规则，CI 强制，违反即失败）
2. `../重写计划-技术路线与框架.md` —— 总体计划（架构、里程碑、风险、§20 执行记录）
3. `../AI辅助开发经验教训.md` —— 前车之鉴（本仓库所有规则的理由来源）
4. `docs/file-contracts.md` —— 逐文件职责表（新增/改名文件必须同步，CI 校验）
5. `docs/structure-graph.md` —— 结构图谱（谁依赖谁/调用链/32 单元业务身份，CI 校验）
6. `docs/business-logic.md` —— 业务逻辑规格（参数链/耦合归属/守恒点/可行解流程）
7. `docs/adr/` —— 已拍板决策（ADR-001~009）
8. 各源码文件头部的"规格说明"节 —— 实现该文件前必读，实现必须满足规格

## 一键命令（环境就绪后）

```bash
# Python 内核（需要 uv，见下方环境待办）
cd core && uv sync && uv run pytest          # 全量测试（含架构门禁测试）
uv run python ../scripts/run_gates.py        # 门禁脚本（行数/契约头/占位符/乱码/只读/结构图谱/webapp 结构/魔法数字）

# 前端（需要 pnpm，经 corepack 启用）
pnpm install && pnpm -C webapp dev

# 服务
cd server && uv sync && uv run uvicorn waterprint_server.main:app
```

## 环境待办（M0 第 0 天）

- [x] ~~镜像源配置~~（已入库：uv 走阿里云源见两个 pyproject 的
      `[[tool.uv.index]]`；pnpm 走 npmmirror 见根 `.npmrc`——本机网络
      实测官方源断流，见下节）
- [ ] 安装 git（`winget install Git.Git`）。仓库已在本地 init 并提交骨架
      基线（无 remote）；剩余动作：装 git 后**推 GitHub + CI 跑通一次**
- [ ] 安装 uv（`winget install astral-sh.uv`），由 uv 安装 Python 3.13
      并生成锁文件（`cd core && uv sync` 与 `cd server && uv sync`）
- [ ] 启用 pnpm（`corepack enable`），`pnpm install` 生成锁文件
- [ ] Docker Desktop 推迟到 M4 部署阶段

### 网络状况与对策（2026-08-22 本机实测）

| 目标 | 现象 | 对策（已落地/待办） |
|------|------|--------------------|
| PyPI 直连（files.pythonhosted.org） | 读超时 / SSL EOF 断流 | 已入库 uv 阿里云镜像（两个 pyproject） |
| pnpm 官方 registry | 不稳 | 已入库 `.npmrc`（npmmirror） |
| GitHub push/clone | 计划 §11 R13 记录直连 ~1.5KB/s 频繁重置；本机实测系统代理（127.0.0.1:7890）可用 | 仅对 github.com 启用代理：`git config --global http.https://github.com.proxy http://127.0.0.1:7890`（不影响其他远程；代理关闭时删除该配置）；备选 SSH-443 |
| winget 源更新 | 偶发失败（需管理员修复 `winget source reset`） | 重试或离线包安装 |

## 目录

```
core/           计算内核（纯 Python，分层 L0~L4，见 docs/file-contracts.md）
server/         FastAPI 服务（routers → services → jobs）
webapp/         React 前端（feature 切片）
data/           版本化数据资产（单价/约束/系数/Excel 模板，全部带出处）
docs/           ADR、逐文件职责表、结构图谱、业务逻辑规格、规范摘录、测试说明
api-contracts/  OpenAPI 契约源（FastAPI 导出 → orval 生成前端客户端）
scripts/        CI 门禁脚本（纯标准库，无第三方依赖）
```

## 测试文件只读机制

`core/tests/` 与 `server/tests/` 下全部文件（含 golden 数据）为**只读**：
由 `scripts/lock_tests.py` 生成 `test-lock.manifest.json`（sha256 清单）并
设置只读属性（仅 Windows 本地；CI/Linux 由哈希校验承担内容完整性）；
`scripts/check_readonly.py` 与 `core/tests/arch/test_lock.py` 在本地和 CI
双重校验。修改测试 = 人类执行的显式解锁流程（见 AGENTS.md §7），AI 不得
改动测试文件与清单。
