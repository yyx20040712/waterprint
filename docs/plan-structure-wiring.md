# M0.5 结构接线计划（已执行记录）

> 目标：在 M0 骨架与 M1 实现之间补一个**结构接线**里程碑——把文件、
> 模块、业务三层逻辑关系从"文档描述"升级为"物理结构 + 机器强制"，
> **不写任何业务实现代码**。本文件是该里程碑的执行记录与遗留项清单。

## 做了什么（按工作包）

| 工作包 | 内容 | 落点 |
|--------|------|------|
| WP1 门禁对齐 | check_structure.py 按 §3 既定意图豁免单元包内文件逐条登记 | `scripts/check_structure.py` |
| WP2 单元包落地 | 32 个工艺单元包骨架（市政 13 / 矿井水 8 / 污泥 7 / 集配水 4），每包固定七件套，内容为契约头 + 单元专属规格（UNIT_ID/中文名/旧 mod 对应/典型上下游/物理不变性/里程碑）；公式数值一律不预设，随 M2/M3 由领域专家复核冻结 | `core/waterprint/units_lib/<线>/<单元>/` |
| WP3 登记与线初始化 | 32 包登记职责表 §3；四条业务线 `__init__` 更新为"骨架已就位 + 典型流程链" | `docs/file-contracts.md` §3 |
| WP4 结构图谱 | 模块依赖图（节点/边/层序）、六条端到端调用链、32 单元业务总表 | `docs/structure-graph.md` |
| WP5 图谱门禁 | 层序方向 + 无环 + 与 import-linter 双源一致 + 单元三方互验 + 调用链路径存在，接入 run_gates | `scripts/check_module_graph.py` |
| WP6 CI 雷点 | vitest 零测试文件不再必红 | `webapp/package.json` |
| WP7 治理同步 | AGENTS.md §13 结构图谱规则；mkdocs 导航；本计划入库；README 状态刷新 | 见各文件 |

## 判定"跑通"的验收标准（全部达成）

1. `python scripts/run_gates.py` 六门禁全绿（原五项 + 结构图谱）；
2. core `pytest -m arch` 全绿（休眠镜像测试不受扰动——未创建任何公开符号）；
3. 32 包 × 七件套齐全，职责表/图谱/目录三方一致（门禁证明，数字以门禁输出为准）；
4. 依赖边全部沿层序向下、无环、与 import-linter 契约一致。

## 遗留项（后续里程碑处理）

| 事项 | 时机 |
|------|------|
| vitest `--passWithNoTests` 在第一个真实前端测试落地时移除 | M0 接线期 / M2 |
| `wp new-unit` 脚手架命令（cli.py）——本轮 32 包为批量生成，工具化随 M1 CLI 实现补齐 | M1 |
| 实现期起，门禁可升级为"真实 import ⊆ 图谱声明边"扫描（当前文件零 import，检查空转） | M1 |
| 单元包内测试文件随交付编写后由人类执行 `lock_tests.py <包路径>` 转只读 | M2/M3 逐包 |
| 推 GitHub + CI 真实跑通一次（环境依赖 git/uv/pnpm 安装，见 README 环境待办） | 环境就绪后立即 |

## 明确不做（本轮边界）

- 任何业务实现（含 webapp providers.tsx/http.ts 接线，属实现期）；
- webapp feature 骨架文件（各 feature README"实装期创建"约定不变）；
- 手工编造 openapi.json（契约源必须是 FastAPI 导出）；
- 修改锁定测试 / 运行 lock_tests.py / git 提交（本机未装 git，提交由人类执行）。

---

# 第二轮（同日续：前端与测试收集接线）

> 目标不变：只完善结构、不写业务代码。本轮补齐 webapp 前端结构并使其机器化。

| 工作包 | 内容 | 落点 |
|--------|------|------|
| R2-1 前端骨架落地 | webapp 37 个规格骨架文件（7 个 feature 的 components/hooks/store + shared/ui + shared/store），全部为 TS 契约头 + 冻结规格注释；消除 shared/ui 与 app 的 ErrorBoundary 重复规划（app/ErrorBoundary.tsx 唯一承担） | `webapp/src/features/**`、`webapp/src/shared/**` |
| R2-2 前端结构门禁 | TS 契约头（/** 职责/输入/输出 */）+ §13.5 分层（features 互不 import / shared 不向上 / 入口只进 app），接入 run_gates | `scripts/check_webapp.py` |
| R2-3 README 同步 | 9 个前端 README 从"实装期创建"更新为"骨架已就位"；file-contracts §5 改为机器检查说明 | 各 README / `docs/file-contracts.md` §5 |
| R2-4 测试收集接线 | pytest testpaths 扩展到 `waterprint/units_lib`——单元包内测试随交付编写即被收集（此前不会运行） | `core/pyproject.toml` |
| R2-5 norms 目录化 | `docs/norms.md` 迁移为 `docs/norms/README.md`（其自规划的结构），新增单元手算对照表模板（条文摘录/算例/交叉对照/双签字栏）——M1 公式溯源流程的落点 | `docs/norms/` |

## 第二轮验收（全部实测）

- 七门禁全绿（新增 webapp 结构门禁）；
- `pytest -m arch` 与基线一致（新增 .tsx 骨架不含代码，不扰动任何测试）；
- check_webapp 负向测试：注入跨 feature import 被捕获（"features 互相 import"），还原后恢复绿色。

## 第二轮遗留项

| 事项 | 时机 |
|------|------|
| 新增 .tsx 骨架未经 tsc 实测（本机未装 pnpm/node_modules）；纯注释文件语法风险极低，pnpm 环境就绪后 `pnpm build` 复核 | 环境就绪后 |
| norms/README.md 的 mkdocs 导航已更新；gb50014-2021.md 条文摘录随 M1 首批单元创建 | M1 |

---

# 第三轮（同日续：计算路线拍板与业务逻辑落库）

> 规范调研（三路并行检索 + 关键声明复核证伪）→ 领域专家拍板 → 规格落库。

| 工作包 | 内容 | 落点 |
|--------|------|------|
| R3-1 方法路线拍板 | 四条主线：AAO 负荷法+泥龄校核、二沉表面负荷+固体校核、高密仅污泥回流型、污泥经验产率+机理互校 | `docs/adr/ADR-008` |
| R3-2 默认值拍板 | B1~B16 整批采纳 + 系数库三级层级（GB 条文说明>手册第 5 册>Metcalf）+ 标准版本事实（GB 50265-2022、GB/T 19837-2019、GB 18918 修改单、两条证伪、矿井水补 GB/T 41019-2021） | `docs/adr/ADR-009` |
| R3-3 业务逻辑规格 | 参数初始化链 / 耦合量单一归属表 / 守恒断言点 / 可行解迭代流程（无解→最小冲突集→带条文依据的调节建议→显式变更→重算，绝不静默改参数）/ 约束联动链 / 回路清单（滤液回流默认关）/ 警告三级 / 工程合理性交叉审计（10 项：8 过 2 警示 + Q1~Q3 待确认） | `docs/business-logic.md` |
| R3-4 骨架规格细化 | assumptions 假设五字段（新增 tuning_impact 调节影响）、diagnose 建议五字段与三来源优先级、_template R8 业务规则、units_lib 铁律引用 | 各文件规格头 |
| R3-5 魔法数字门禁 | 第 8 道门禁（区外捕获/真源区放行双向负向测试通过）；pyproject 补 pyyaml（YAML 数据包依赖缺口） | `scripts/check_magic_numbers.py` |

验收：八门禁全绿；arch 测试与基线一致。
遗留：Q1（滤液回流）/Q2（矿井水 III 类口径）/Q3（巴歇尔 C/n 表正式文本）待领域专家确认（business-logic §10）。
