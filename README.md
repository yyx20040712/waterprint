# 智水蓝图（WaterPrint）monorepo

污水处理工艺设计计算平台：计算内核（纯 Python）+ FastAPI 服务 + React 前端。

> 当前状态：**M4/M5 功能主体全交付（2026-09-09）——计算面三线 32/32 单元
> 四件套（UF-32 对照表 507 键）之上，工业化与图纸面收官**：布置编辑器
> （边界红线+间距校核黄红标示，L4）/全厂总图与单单元 CAD 图纸（DXF）/
> 高程纵断面图链（单单元纵断 DXF+总图目录行+横纵比例定制 h/v+批量面
> sheet 透传，PROFILE1~3）/概算书与审计报告导出/IFC 全厂模型导出/
> 服务端批量导出任务面（幂等键+SSE 进度+在途取消+页面重挂恢复，SVRB2）/
> DWG 转换挂点（ODA 边车，
> 可选）/三维场景与画布 webapp/下载端点（路径安全双闸）/鉴权与 SSE
> 限流（可配置）。**剩余面三类**：纵断真实站距与 L0 独立管底
> （专业精度，停档待领域专家与用户裁决）/表尺寸 ODA E2E 验收与字体随附
> （用户承办）/软著申请与开源准备（用户目标）——明细见会话工作区
> handover 三·bis 对照表。工程面：
> 门禁 11 项（含 GR-21 弃用到期门禁，TD1）/GR-01~GR-37 治理规则/
> test-lock 259 键只读锁/快照四哈希锚。此前：M0 骨架→M1 内核→M2
> 四块→M3 三线战役→M4 工业化→M5 图纸面。
> 数据面键计数基准（ENG3 2026-08-28 探针实测：load_coefficients/
> load_prices/templates manifest 装载正门）：coefficients 1.1.0（577 键）
> +unit_prices 1.0.0（81 键）+templates 1.1.0（3 模板）；norms 手算表
> 32 份（AI 起草+追认制，全部已追认——余 I3 已裁待回填/条号章级挂账）。
> 测试数/覆盖率以 CI 输出为准，文档不手写数字。

## 快速导览（新成员/AI 按此顺序阅读）

1. `AGENTS.md` —— 项目宪法（硬规则，CI 强制，违反即失败）
2. `../重写计划-技术路线与框架.md` —— 总体计划（架构、里程碑、风险、§20 执行记录；**本地工作区文件，仓库外**——克隆后此文件不在库内，总计划快照以本 README 与 `docs/` 为准）
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
uv run python ../scripts/run_gates.py        # 门禁脚本 11 项（清单见 scripts/run_gates.py——行数/契约头/弃用到期/占位符/乱码/只读/信任根/结构图谱/webapp/魔法数字/ruff）

# 前端（需要 pnpm，经 corepack 启用）
pnpm install && pnpm -C webapp dev

# 服务（默认只听 127.0.0.1:8000——对外绑定=WATERPRINT_HOST 显式覆盖）
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
双重校验。修改测试 = 人类执行的显式解锁流程（见 AGENTS.md §7），AI 不得
改动测试文件与清单。
