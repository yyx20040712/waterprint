# AGENTS.md —— WaterPrint 项目宪法

> 适用于所有人类开发者与 AI 协作者。全部规则由 CI 机器强制（scripts/ + .github/workflows/），
> 不依赖自觉。规则来源：《AI辅助开发经验教训.md》与《重写计划》§6/§13/§14/§17。
> 本文件 ≤500 行（门禁检查）。与重写计划冲突时，以计划最新修订为准并更新本文件。

## 0. 阅读顺序（每次会话开始前）

1. 本文件；2. `docs/file-contracts.md`（你要动的文件职责）；
3. `docs/structure-graph.md`（依赖与调用链）与 `docs/business-logic.md`
   （单元间业务规则：参数链/耦合归属/守恒/可行解流程）；
4. 目标文件头部"规格说明"；5. 对应镜像测试 `core/tests/**/test_*.py`
   （正确行为的定义，只读）。

## 1. 分层与依赖（import-linter 强制，违反即 CI 失败）

- 只许向下依赖：L4 按装配顺序细分子层——L4.cli → L4.app →
  L4.project-trace（project 与 trace 同子层）→
  L3 graph/solution/elevation/cost/drafting/geometry/network
  → L2 units_lib → L1 registry → L0 contracts。依赖只许沿层序（含 L4
  子层序）向下：cli→app 合法；app→cli、project↔trace 等同/逆子层依赖
  与一切向上依赖 = 失败。
- L3 子系统之间互相独立（elevation/cost/drafting/geometry/graph/solution/network 互不 import），
  它们只消费 L0 的 result_schema，互不感知。
- 工艺单元包之间互相独立：units_lib 内任意两个单元包禁止互相 import。
- 跨包只走正门：只 import 目标包 `__init__.py` 暴露的名字；访问他包 `_` 前缀 = 失败。
- 装配点唯一：graph/executor.py 只依赖 contracts.unit_api 协议，禁止 import 任何具体单元；
  单元的发现/实例化只发生在 app.py。
- 计算内核（core/）禁止 import fastapi/structlog 等服务层依赖；network/ 不共享厂区图引擎。

## 2. 文件与规模（scripts/check_file_budgets.py 强制）

- 任何文件 ≤500 行；units_lib 的 compute.py ≤400 行（超限拆文件，无豁免清单）。
- 一个文件一个主概念：文件名 = 概念名；出现第二个主概念当天拆分。
- 每个新文件必须先登记 `docs/file-contracts.md` 职责表（CI 双向校验：表多=失败，表少=失败）。
- webapp 源文件的契约头（/** 职责/输入/输出 */）与 features 互不 import 分层
  由 `scripts/check_webapp.py` 强制（§13.5，M0.5 起）。
- 死代码即删：未被引用的文件/组件不提交；方案切换 = 删除旧方案，禁止并存。
- 不提交运行时产物（.recent_projects、缓存、构建输出、虚拟环境）。

## 3. 代码硬规则（scripts/check_grep_gates.py + ruff 强制）

- 禁止占位实现与未完成标记：`not implemented` / `placeholder` / `TODO` / `FIXME` 计数 = 0。
  未完成的功能不写存根，留空并更新职责表归属里程碑。
- 禁止裸 `except:` 与 `except Exception`；可预期错误用领域异常（InvalidUnitConfig /
  LoopDivergence 等）或 Result 风格返回；禁止让错误静默通过。
- 内核禁止抛 HTTP 语义异常；server 层统一 exception handler 做映射。
- compute.py 内禁止工况 if 分支：工况对参数的影响只走 manifest 声明式映射（ADR-007）。
- 单位规则（ADR-002）：pint 只存在于边界（输入/输出/schema/序列化）；内核热路径用规范单位
  裸数组（流量 m³/s、浓度 mg/L、几何 m），代码不出现换算逻辑；落盘一律"数值 + 显式 unit 字段"。
- 全部源码/文档 UTF-8；写文件显式 `encoding="utf-8"`；Windows 开发设 `PYTHONUTF8=1`。
  提交前验证中文可读（乱码特征串计数 = 0）。
- 严禁魔法数字（`scripts/check_magic_numbers.py` 强制）：内核/服务代码数值
  字面量仅允许 0/1/2/10，其余数值只许出现在 `registry/**`、
  `contracts/quantity.py` 与 `units_lib/**/manifest.py` 真源区（白名单按
  "前缀+文件名"双条件精确命中——manifest.py 默认值 = 带出处的声明式真源；
  同前缀下 compute.py 等其余 units_lib 文件继续严管），或经假设清单/
  系数库注入（每条带出处与调节影响元数据，见 `docs/business-logic.md`
  §1/§4/§9）。
- ruff 复杂度预算：圈复杂度 ≤10（C901）、语句 ≤40（PLR0915）、参数 ≤5（PLR0913）、分支 ≤12（PLR0912）。
- 每个模块契约头（§5 格式）不可省略，CI 检查存在性。

## 4. 类型与契约（单一事实源）

- 类型只从单一源头生成，禁止手写双份：前端客户端由 OpenAPI 经 orval 生成
  （webapp/src/shared/api/，生成物禁止手改）；内核输出契约 = result_schema 字段 ID，
  中文名只存在于 i18n 显示层。
- 概算/图纸/三维按字段 ID 取数，禁止中文模糊匹配。
- result_schema 变更必须走 ADR + 契约测试 + 前端重新生成三步。
- 文档不手写测试数/覆盖率等数字，一律"以 CI 输出为准"。

## 5. 模块契约头格式（每个 .py 文件第一行 docstring，CI 检查）

```python
"""[一句话职责——这个文件存在的唯一理由]

输入:  <消费什么：类型/来源>
输出:  <产出什么：类型/去向>
"""
```

头部之后紧跟"规格说明"节（公开接口签名 / 行为规格 / 错误与边界 / 禁止事项 / 测试要求 / 参照），
实现前冻结，实现必须满足规格。

## 6. 测试纪律（红-绿 + 只读）

- 每个测试必须"先失败一次再通过"才算数；新功能必须自带测试。
- 镜像命名：`topo.py` ↔ `test_topo.py`；性质测试独立 `properties_topo.py`。
- 骨架期休眠测试：测试文件内用 `getattr(module, 符号, None)` 判定，符号缺失 = skip
  （理由注明缺什么）；实现合入后 skip 数必须归零（CI 以 `-ra` 输出 skip 原因）。
- 公式数值基准来自 docs/norms 的条文摘录 + 手算对照表（领域专家签字），不得编造数字；
  golden 端到端期望值只存放在 `core/tests/golden/golden_data/`（数据文件，非代码）。
- 同输入双跑 diff=0、序列化往返无损、incremental==全量重算（字节级）是常驻测试。

## 7. 测试只读机制（防投机取巧）

- `core/tests/` 与 `server/tests/` 下所有文件只读：文件系统只读属性
  （Windows 本地写屏障）+ 根目录 `test-lock.manifest.json`（sha256，
  跨平台内容真相——CI/Linux 上由它承担完整性校验）。
- 校验入口：本地 `scripts/check_readonly.py`；CI 与 pytest 侧
  `core/tests/arch/test_lock.py`。
- AI **禁止**：修改/删除/新增上述两目录下任何文件；运行 lock_tests.py；修改 manifest。
- 只有人类可以：解锁（清除只读属性）→ 修改/新增测试 → 重新运行
  `python scripts/lock_tests.py`（新增单元测试后可带路径参数追加）→
  该变更作为独立 commit 接受审查。测试变更是显式事件，不是顺手行为。

## 8. 修改与提交

- 每次改动一个逻辑单元；完成后 `git diff --stat` 自查范围蔓延（只应包含任务相关文件）。
- 改核心模块（graph/registry/contracts）前先跑其镜像测试；改输出格式必须更新快照
  （syrupy `--snapshot-update`）并显式说明。
- 项目文件序列化必须确定性：键排序、round(x,10) 浮点定点、无随机 ID、保存两次字节级相同；
  content_hash 只覆盖 design 态。
- 提交信息中文描述意图；一个 commit 一个目的。

## 9. 并行协作（多代理/多人）

- 写不同文件 = 可并行；写同一文件或共享状态（docs/file-contracts.md、__init__.py、
  pyproject.toml、manifest）= 串行。
- 派发 AI 任务用五层规约模板（行为/接口/架构/生命周期/文化）+ 完成定义清单，见
  `docs/index.md` 附录；规约里写全文件路径与关键签名，不让实现者自行探索。

## 10. 完成定义（DoD，逐项打勾后才算完成）

- [ ] 功能代码 + 测试提交；全量测试通过（pytest / vitest，以 CI 为准）
- [ ] 占位符/裸 except/乱码门禁 = 0（`scripts/run_gates.py` 绿）
- [ ] 新文件已登记 file-contracts.md；`git diff --stat` 无范围蔓延
- [ ] 无死代码、无重复资产、无运行时产物入库
- [ ] 中文内容工具验证可读；文件 ≤500 行
- [ ] M2 起工艺单元四件套齐备：计算 + 测试 + 三维组件 + 图纸模板

## 11. 单元包固定结构（脚手架生成，禁止自由发挥）

```
units_lib/<line>/<unit>/
├─ manifest.py        # 声明式清单：参数/端口/去除率/规范引用/工况映射（唯一对外）
├─ compute.py         # 唯一计算源：向量化实现（标量 = N=1 特例），≤400 行
├─ constraints.py     # 声明式约束定义
├─ README.md          # 一段话职责 + 输入输出
└─ tests/             # test_compute.py（golden 数值）+ properties.py（物理不变性）
```

- 单元对外只暴露 `manifest` 与 `compute` 两个名字（包 `__init__.py` 白名单）。
- 新单元用 `wp new-unit <line> <name>`（core 的 cli.py）从 `_template` 生成。
- 单元测试完成后由人类执行锁定（`python scripts/lock_tests.py <路径>`）。

## 12. 业务语义冻结项（违反 = 评审拒绝）

- 工况语义按 ADR-007：flow_case 全局 2 档（design/avg）× pool 逐单元检修敏感性，
  运行次数 = 2 + k；禁止 2^n 全组合。
- 汇流加权使用**当前工况流量**（design 用 Q_design、avg 用 Q_avg），Kz 取 max（ADR-005/§14.2）。
- 污泥线 DS（干固体）守恒进性质测试；出水标准是数据不是代码分支。
- 枚举语义：单单元枚举 + 全厂传播；全厂联合枚举为远期研究，禁止伪装成本轮功能。
- 可复算三元组：结果 = f(design_hash, engine_version, data_version)；缓存只是优化不参与语义。
- 运行中任务结果落地即绑定快照 hash；输入变更后旧结果标 stale，禁止静默覆盖。

## 13. 结构图谱规则（scripts/check_module_graph.py 强制）

- 三层关系的单一事实源是 `docs/structure-graph.md`：§1 模块依赖图
  （节点表 + 依赖边表 + 层序）、§2 端到端调用链、§3 业务单元总表。
- **改依赖先改图谱**：新增/调整模块依赖必须先改 §1 边表再写代码；
  实现期真实 import 必须是 §1 声明边的子集（评审 + 门禁对照）。
- 图谱 §1a 层归属与 `core/pyproject.toml` 的 import-linter 契约**双源一致**
  （门禁双向覆盖校验；改一处必须同步另一处，否则 CI 失败）。
- **新单元三步**：先在图谱 §3 与 file-contracts.md §3 登记 → 再建包目录
  （_template 固定结构）→ 最后实现；三方一致性由门禁强制。业务线扩充时
  同步更新脚本内 EXPECTED_UNIT_COUNT 断言。
- 调用链 §2 引用的每个仓库路径必须真实存在（防链路指向幽灵文件）。
