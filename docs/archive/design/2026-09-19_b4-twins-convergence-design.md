# B4 双胞胎+异常表两份收敛设计定案（批 3c / 方案二 2c）

> 性质：批 3c（批 3 第三步）架构级三段通道终裁定案（调研→拟定→对抗审核→主控终裁）。
> 战役：《复杂度治理战役裁决书》（2026-09-18）方案二批 2c 行。
> 通道档：调研摘要+事实包=`.workflow/briefs/b3c-drafter-brief.md`（仓外快照）；
> 设计书 v1=`b3c-drafter-output.md`；对抗审核（B0/W3/N7 PASS）=`b3c-auditor-output.md`。
> 本件=终裁记录+实装蓝图（B3-c 实施依据），与 registry-split-design（批 2 定案）同族。

## 1. 收敛对象与定案组合

| 双胞胎 | 现状 | 定案 |
|---|---|---|
| 甲：边转换 | `app_assembly._endpoint/_edges`（拒载体 InvalidAssemblyError→HTTP 400）vs `executor_assembly._endpoint/_edges_from_design`（拒载体 InvalidExecutionError→HTTP 422），逻辑逐行同构、消息微差 | 校验/消息/遍历结构单源下沉 `contracts/edge_parsing.py`（`endpoint_from`/`edges_from`，`error=` 异常类注入——批 3a `not_found` 先例同型）；两侧改同名绑定件（绑定各自异常类），私有名与定义位不动（镜像恒等钉零扰动） |
| 乙：异常表 | `executor._DOMAIN_EXCEPTIONS`（7 族）vs `enumerate._ROW_DOMAIN_EXCEPTIONS`（5 族），交集=contracts 层 4 族，两处头注互指「同源同步义务」 | 交集 4 族单源 `contracts/domain_exceptions.py::DOMAIN_EXCEPTIONS_CORE`；两消费面组合式复现（`CORE + 专属族`），成员集 7/5 字节级不变 |

结构路线=路线甲（全下沉 L0 contracts）：**零新增同层边、零 §1c 申报、零图谱面改动**（§1a 包级节点、§1b 既有向下边、check_module_graph 同节点忽略——三面均实证）；全部消费边（graph→contracts、solution→contracts、app→contracts）为既有合法向下边。

## 2. 决策记录（J1~J6+W/N 处置）

| # | 决策 | 依据与处置 |
|---|---|---|
| J1 结构路线 | 路线甲（contracts 下沉） | **W-1 对账（审核呈报缺口补齐）**：裁决书 A-3「承载位置=按 ADR-014 §1c 同层边申报」字面在路线甲下不触发（零同层边）。释义=该列承载的是「若设计引入同层边须走 §1c 申报」的机制指引，非「必须引入同层边」的硬性要求——裁决②「分层铁律本身不动」与方案二原则（星型同层晋升=防传声筒的正门，非必经之路）支撑意图读法；A-4 前提（动 import-linter 契约）不触发，6 kept 基线零变。**列 R-B3c-1 呈用户追认**（涉裁决书字面释义，同 B2-3 D1 先例纪律，不阻塞实施）。**W-2 补齐**：L1 registry 落点否决对账——异常表交集 4 族全部定义在 contracts（驻 registry 归属颠倒）、graph→registry 现状零边（新增耦合边）、无 L0 双消费内核先例（contracts.expr 在案）——三面皆劣，不入册为第四候选。 |
| J2 异常表形态 | 组合路线（核心元组+各侧组合） | 字节级复现两表成员集（except 元组次序无关语义）；继承路线否决（捕获集=派生集、新增子类自动扩面、isinstance 可观察面由假变真、触面 8+ 文件）。**N-1 补齐**：第三形态「contracts 各驻两份完整元组」一票否决——命名必带消费方语义（违准入③命名中性）。 |
| J3 消息文本 | 呈案 A：统一为含「得到」版 | `_edges` 侧两版现状已含「得到」、`_endpoint` 侧 executor 版补齐（两处微差）；**N-2 补齐**：呈案 A 下 app 侧文本零变→`validate_design_structure` 汇总清单面零连带（此为选 A 而非 C 的一条实证理由）；全库对四形态消息零断言（§B-5）。executor 侧两消息「得到」补字=客户端可见正文微差（状态码契约面零变），已呈终裁知情。 |
| J4 命名 | `edge_parsing.py`/`endpoint_from`/`edges_from`；`domain_exceptions.py`/`DOMAIN_EXCEPTIONS_CORE` | 命名中性对账成立（不带消费方语义）；文件名=概念名。 |
| J5 latent 不对称 | 不修，挂账 G1 | executor 不含 InvalidFormulaError（单点路径公式错不被 R5 包装原样上抛）——行为零变硬闸下本批禁触；是否收口留用户，收口=行为变更须另批。 |
| J6 图谱假设 | 已闭卷 | check_module_graph 第 427 行实证「同节点忽略」——包内新边零登记义务（主控独立复核，非假设）。 |

**审核 N 项处置汇总**：N-3 吸收（验收⑥ grep 锚=四形态全文：「须为对象（含 unit_id/port_id）」「须含字符串 unit_id/port_id」「须为对象（src/dst/recycle）」「recycle 须为布尔」）；N-4 吸收（绑定件形态对账：`functools.partial` 语义等价但内省面/docstring 劣化、别名导入不可行——`error` 为必填关键字参无法别名绑定、调用点直改必致恒等钉红被 [HUMAN-LOCK] 锁面封死；**绑定件的存在本身是锁面强制的非可选项**）；N-5 知情入册（绑定件与同名私有名外观被镜像钉永久锁定——不可逆安排，治理门槛=先动锁面测试）；N-6 吸收（executor/enumerate 旧 4 族 import 逐文件查残余用途后清理，ruff F401 兜底；绑定件带全注解与 docstring）；N-7 吸收（验收口径=「成功路径逻辑逐字同构搬迁，输出面零变」——非「不触成功路径」）。

## 3. 实装蓝图（逐文件）

| # | 文件 | 性质 | 内容 |
|---|---|---|---|
| 1 | `core/waterprint/contracts/edge_parsing.py` | 新建（~65 行） | `endpoint_from(raw: object, side: str, index: int, *, error: type[Exception]) -> PortRef`；`edges_from(raw_edges: Sequence[object], *, error: type[Exception]) -> tuple[Edge, ...]`。消息四处统一含「得到」。仅 import 同包 ports+标准库（L0 零依赖铁律）。 |
| 2 | `core/waterprint/contracts/domain_exceptions.py` | 新建（~40 行） | `DOMAIN_EXCEPTIONS_CORE: Final[tuple[type[Exception], ...]] = (InvalidFlowError, InvalidQualityError, InvalidSludgeError, InvalidUnitConfig)`（序=executor 表现相对序）。import 同包 flow/quality/sludge/manifest。 |
| 3 | `core/waterprint/contracts/__init__.py` | 修改 | 聚合两新子模块公开面（3 名入 import+`__all__`）；规格头聚合口径注记 13→15 子模块同步更新。 |
| 4 | `core/waterprint/graph/executor_assembly.py` | 修改 | `_endpoint`/`_edges_from_design` 改绑定件（`error=InvalidExecutionError`），函数体校验/消息逻辑删除；注解与 docstring 保留；import 面按 F401 清理。 |
| 5 | `core/waterprint/app_assembly.py` | 修改 | 同手法（`error=InvalidAssemblyError`）；`assemble`/`validate_design_structure` 调用面零改。 |
| 6 | `core/waterprint/graph/executor.py` | 修改 | `_DOMAIN_EXCEPTIONS = DOMAIN_EXCEPTIONS_CORE + (InvalidPropagationError, InvalidNodeError, ExprSyntaxError)`；R5 注记改单源口径（新增 contracts 层族→改 CORE；新增 graph 层族→改本组合尾）；旧 4 族 import 清理（WaterFlow/WaterQuality/SludgeFlow 等注解用名保留）。 |
| 7 | `core/waterprint/solution/enumerate.py` | 修改 | `_ROW_DOMAIN_EXCEPTIONS = DOMAIN_EXCEPTIONS_CORE + (InvalidFormulaError,)`；行级域拒注记同步改口径；旧 4 族 import 清理。 |
| 8 | `docs/file-contracts.md` | 修改 | 新增文件 1/2 行；文件 3-7 行职责描述随改。 |

零删除文件、零新增测试、零触碰 core/tests/**、图谱/pyproject/§1c 零改动。回退=单批 revert（无联动面）。

## 4. 验收矩阵（实装后逐条跑）

1. golden e2e 4 文件全绿（基线已采：改动前 4 passed+776 passed 全量）——成功路径逻辑逐字同构搬迁，输出面零变（N-7 口径）；
2. core 全量 pytest 776 passed（恒等钉不红：绑定件保定义位+executor import 面不动）；
3. import-linter 6 kept（零 §1c、零契约改动）；
4. `scripts/run_gates.py` 15 门禁全绿；
5. `gen_status.py --check` 零漂移——**按 W-3 纪律=实跑核验非断言**（本批不触 status 生成输入面：测试收集数/test-lock 键/门禁数/OpenAPI/ADR/UF/数据包键/快照锚八源，预期 2158B 不变；若漂移按门禁程序呈报不静默重入库）；
6. 残留扫描：四形态消息全库仅存 edge_parsing.py；`_DOMAIN_EXCEPTIONS`/`_ROW_DOMAIN_EXCEPTIONS` 全消费面 grep（N-1——次序敏感暗面排查，预期仅两处 except 捕获位）；
7. 门一（ops-gate1-k2 备源承载，自包含审包）+门二（ops-probe 独立重跑矩阵）。

## 5. Rulings（呈用户，不阻塞实施）

- **R-B3c-1**：裁决书方案二 2c 行「承载位置=按 ADR-014 §1c 同层边申报+共享件单源」按**意图读法**执行——定案为零新增同层边+共享件下沉 L0 contracts（§1c 申报机制在引入同层边时才触发；字面读法=强制造一条同层边，与裁决②「分层铁律不动」相悖）。涉裁决书字面释义，呈追认（同 B2-3 D1/R-B2-3-1 先例）。

## 6. 挂账

- **G1（=设计书 G1/P10）**：executor `_DOMAIN_EXCEPTIONS` 不含 InvalidFormulaError——单点路径公式错不被 R5 隔离包装原样上抛（enumerate 行级域拒则捕获）。是否收口留用户；收口=行为变更另批。
- **G2（=设计书 G2/P11）**：`_NullSink`（graph/solution 各一）与 `_dims_of`（enumerate vs executor_projection，语义相异）不在本批字面范围，后续批次评估。
- **G3（=设计书 G3）**：双胞胎消息面全库零断言——后续可为 edge_parsing 补消息锚测试（新测试提案走锁面程序 [HUMAN-LOCK]，不在本批）。
