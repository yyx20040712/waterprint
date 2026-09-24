# 智水蓝图（WaterPrint）monorepo

污水处理工艺设计计算平台：计算内核（纯 Python）+ FastAPI 服务 + React 前端。

> 当前状态：M0~M5 功能底盘收官（计算三线单元库/布置/DXF/概算/IFC/导出/鉴权），
> C2 视觉重制+操作链 P0~P2+GOV 治理批已收——批次编年史见仓外档案区
> `readme-status-history-2026-09.md`；在册剩余面（纵断真实站距/ODA E2E/软著开源）见 `docs/`。
> **一切计数（门禁/锁键/端点/ADR/UF/数据包版本）以 [docs/status.md](docs/status.md) 生成值为准，本文件不手写数字。**

## 快速导览（按此顺序阅读）

1. `AGENTS.md` —— 项目宪法（硬规则，CI 强制，违反即失败）
2. `E:/zcode_md/waterprint-archive/parent-docs/重写计划-技术路线与框架.md` —— 总体计划（架构、里程碑、风险、§20 执行记录；**本地档案区文件，仓库外**——克隆后此文件不在库内，总计划快照以本 README 与 `docs/` 为准）
3. 历史经验与评审过程档案（仓库外档案区 `E:/zcode_md/waterprint-archive/`）——前车之鉴（本仓库所有规则的理由来源）
4. `docs/file-contracts.md` —— 逐文件职责表（新增/改名文件必须同步，CI 校验）
5. `docs/structure-graph.md` —— 结构图谱（谁依赖谁/调用链/32 单元业务身份，CI 校验）
6. `docs/business-logic.md` —— 业务逻辑规格（参数链/耦合归属/守恒点/可行解流程）
7. `docs/adr/` —— 已拍板决策（ADR-001~022）
8. 各源码文件头部的"规格说明"节 —— 实现该文件前必读，实现必须满足规格

## 一键命令（环境就绪后）

```bash
# Python 内核（需要 uv，见下方环境待办）
cd core && uv sync && uv run pytest          # 全量测试（含架构门禁测试）
uv run python ../scripts/run_gates.py        # 门禁全跑（计数见 docs/status.md；清单=scripts/run_gates.py GATES 元组——行数/契约头/弃用到期/占位符/乱码/只读/信任根/结构图谱/webapp/魔法数字/ruff/lint-imports 等）

# 前端（需要 pnpm，经 corepack 启用）
pnpm install && pnpm -C webapp dev

# 服务（默认只听 127.0.0.1:8000——对外绑定=WATERPRINT_HOST 显式覆盖）
# 数据包缺省自动定位 <仓库根>/data（包定位解析，CWD 无关）；自定义数据根用
# WATERPRINT_DATA_DIR 覆盖，缺包时启动即拒绝并给出指引（fail fast）。
cd server && uv sync && uv run python -m waterprint_server.main
```

## 部署（Docker 双容器）

一条命令起全栈（对外唯一入口=前端 nginx http://localhost:8080，`/api` 经
反代；server 8000 不发布宿主——安全口径见 deployment.md「安全红线」节，
项目/导出持久化卷）：`docker compose -f deploy/compose.yml up -d --build`。
前置、环境变量、冒烟清单与 FAQ 见 [`docs/deployment.md`](docs/deployment.md)。

> 本地开发用已装备的 `core/.venv`（46 个 wheel）与 `server/.venv`；`uv sync`
> 待网络恢复可生成锁文件后启用；测试入口 = 分包进入 `core/`、`server/`
> 目录运行（根目录聚合收集有已知 conftest 冲突）。

## 环境待办（M0 第 0 天）

- [x] ~~镜像源配置~~（已入库：uv 走阿里云源见两个 pyproject 的
      `[[tool.uv.index]]`；pnpm 走 npmmirror 见根 `.npmrc`——本机网络
      实测官方源断流，见下节）
- [x] ~~git 安装与 M0.5 入库~~（2026-08-22/23）
- [x] ~~uv 0.9.9 安装~~（wheel 直装，镜像索引异常绕过——见下节网络
      对策表；解释器版本见 `.python-version`，依赖以两个 pyproject 为准）
- [x] ~~pnpm 经 corepack 可用~~（pnpm@10.34.5，node-linker=hoisted
      应对 exFAT）
- [x] ~~推 GitHub + CI 全绿~~（github.com/yyx20040712/waterprint，
      CI 首跑 4/5 失败→修复批→run #12 五 job 成功；推送代理见下节
      网络对策表）
- [x] ~~uv.lock 生成与 CI frozen~~（core/uv.lock T7 期入库；server/
      uv.lock SERVER 批 2026-08-26 入库——两 job 均已 `--frozen`）
- [ ] Docker Desktop 推迟到 M4 部署阶段

### 网络状况与对策（2026-08-22 本机实测）

| 目标 | 现象 | 对策（已落地/待办） |
|------|------|--------------------|
| PyPI 直连（files.pythonhosted.org） | 读超时 / SSL EOF 断流 | 已入库 uv 阿里云镜像（两个 pyproject） |
| pnpm 官方 registry | 不稳 | 已入库 `.npmrc`（npmmirror） |
| GitHub push/clone | 计划 §11 R13 记录直连 ~1.5KB/s 频繁重置；本机实测系统代理（127.0.0.1:7890）可用 | 仅对 github.com 启用代理：`git config --global http.https://github.com.proxy http://127.0.0.1:7890`（不影响其他远程；代理关闭时删除该配置）；备选 SSH-443 |
| winget 源更新 | 偶发失败（需管理员修复 `winget source reset`） | 重试或离线包安装 |
| uv（rustls/native-tls）拉镜像 wheel | 间歇 TLS 断流，uv sync/lock 均不可用 | 本地依赖改 curl 拉 wheel + pip 离线装（会话工作区 fetch_deps.py）；CI 用 UV_DEFAULT_INDEX 官方源 |
| E 盘 exFAT | 不支持符号链接，pnpm 默认 linker 失败 | .npmrc node-linker=hoisted（本地/CI 同口径） |

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
双重校验。修改测试 = 人类执行的显式解锁流程（见 AGENTS.md §7），不得
改动测试文件与清单。
