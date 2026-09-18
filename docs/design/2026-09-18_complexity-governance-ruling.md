# 复杂度治理战役裁决书（2026-09-18）

> 性质：本战役的用户裁决+五方案设计定案（与 ADR 同类的决策文档）。
> 执行投影=docs/handoff/relay.md（批次接力状态板——排程冲突时以本件为准并回改板）。
> 组织账本=.zcode/org-ledger.jsonl（裁决逐字原文与派发流水在彼处，本件为语义定案）。
> 沿革：本件前身=会话区方案文档（.workflow/plans/complexity-governance-plan-v1.md，
> 2026-09-18 升格入仓并中性化岗位词）。

# 复杂度治理五方案设计 v1（框架稿）

> 批次：complexity-gov-2026-09-18 ｜ 起草：主控 ｜ 状态：**框架稿待议**
> 性质：方案一/四=制度文档批（轻量双审）；方案二/三=架构级（实施前走
> 三段通道：社区调研→拟定者岗拟定→对抗审核（审核者岗）→主控终裁，技能 02 §8.6）；
> 方案五=路线规划（各业务立项时逐项走三段通道）。
> 调研底座：四岗探索报告（core/server/webapp/docs）+主档案权案区
> （总计划 §7 路线图、深度审计裁决书）。

## 裁决记录（用户 2026-09-18，逐字口径）

1. 同意立 sunset 机制，但形态要极简（一张登记表+触发条件，不新增门禁脚本）。
2. 给共享开正门，但只开「同层晋升」这一扇——分层铁律本身不动。
3. registry 走「分性质」方案：纯数值 YAML 化，公式留 Python 但按线分片。
4. README 砍成三行+指针，需要留的数字单独生成到 docs/status.md。
5. 优先级：操作链条集中 debug → 碳核算模块 → 联合枚举 → AI 集成 →
   最后矿井水和软著；软著部分用户亲自检查并修改核心代码。
6. （追加）清理失效文件。

**二轮裁决（2026-09-18 批 0 收口后）**：
①user_think.png 已过时直接删（已执行）；②软著「亲查核心码」范围=
**计算核心优先**（graph/registry/units_lib 先审，其余面随后）；③README
编年史迁移目标=归档区 `parent-docs/readme-status-history-2026-09.md`
确认；④碳核算前置探针批准搭车批 1——**碳核算本体须先详细调研再立项
添加，计算逻辑留用户审查**（同数据批起草-追认制纪律）。

---

## 方案零：清理批（先行，随本批执行）

| 对象 | 证据 | 处置 | git 面 |
|---|---|---|---|
| `.workflow/b4-window1/edge-profile` 603MB | 无头浏览器测试遗留的 Edge 用户数据目录（Crashpad/Ad Blocking 等 1107 文件） | 直删（零档案价值） | 不入库，无需 commit |
| waterprint 根 10 个 `*.log` + 智水蓝图根 `tmp-p2c-server.log`/`tmp_cass_pid.json` | 运行时产物，`*.log` 已 gitignore | 直删 | 同上 |
| `../.offline-cache/zz-garbage-tmp` | 命名自证垃圾 | 直删；`wheels/` 107MB 保留（网络受限环境的离线依赖资产） | 同上 |
| `webapp/src/shared/ui/{theme,SemanticColor,NumberCell}.tsx|ts` + `shared/store/{persist,devtools}.ts` | M2「结构预留」骨架零实装零引用：主题实际落 `app/providers.tsx`、语义色真源=`shared/ui/semanticColors.ts`（SC1）、数字格式化在 SolutionsTable 本地实现 | git rm；SolutionsTable 头注「SemanticColor 封装挂账」行改指 semanticColors.ts 真源（灭幽灵引用） | tracked，清理 commit |
| `docs/plan-structure-wiring.md` | M0.5 接线计划，8-24 起停更，接线早已完成（对象消失——sunset 首例） | git rm + mkdocs.yml nav 行同步删除 | tracked，清理 commit |
| `.gitignore` 增 `projects/`、`server/projects/` | 用户设计数据不应以 untracked 噪声出现（「不提交运行时产物」既有原则） | 追加两行 | 清理 commit |
| `webapp/public/assets/units/user_think.png` | 未追踪、用途不明 | **待用户裁决**（见待裁问题①） | —— |

不做（显式）：`projects/`、`server/projects/` 内容不碰（用户数据）；
`test-lock.manifest.json` 信任根不碰；b4-window1 其余 ~2MB 过程产物
（截图/审档/probe-readout）保留原位（未超归档阈值）。

## 方案一：治理 sunset 机制（极简形态）

**新文件** `docs/governance-sunset.md`——单表登记，无脚本、无门禁、无流程件。

表列：`登记日期 | 治理件 | 类型 | 触发条件 | 处置动作 | 状态`。

**触发条件三类模板**（登记时引用编号，不自创新类）：
- **S1 对象消失**：规则守护的机制/文件/流程已被替代或删除。
- **S2 长期零触发**：连续 ≥10 个批次未在任何门禁输出、审查报告或
  回炉轮中出现（人工判断，不机检）。
- **S3 被覆盖**：新规则/ADR 明确覆盖旧规则语义（旧条标 superseded）。

**处置动作**：软退役（表内标 sunset 日期+理由；条款原文保留不删改
——历史红线纪律同技能 08 §3）→ 该文件下一次因任何批次被触碰时，随批
执行移除或迁归档区。**禁止**：借 sunset 批顺手改写条款语义。

**首批登记候选**（登记≠立即退役，逐条走触发条件核对）：
1. `docs/plan-structure-wiring.md`——S1，本批已直接清理（首例闭环）。
2. GR 英文过载词豁免类条款（若豁免清单已长期零增长——S2 候选）。
3. GOV2 去重后残留的规则同源引用（S3 候选，需逐条审）。
4. `docs/testing.md`/`index.md` 中将被 status.md 指针替代的计数句
（S3——被方案四覆盖）。

**红线**：sunset 表自身不设门禁不设脚本；表 >50 行即触发一次人工
「治理件盘点」（防登记表自身熵增——本条写入表头注记）。

## 方案二：同层晋升正门（复制收敛）

**原则（裁决②）**：跨层依赖铁律不动；「同层晋升」=共享件晋升为**同层
具名共享模块**（星型：共享件被同层消费、自身禁依赖任何消费方——结构
上无环，铁律语义不受损）。

**晋升准入五条**（防 shared 沦为传声筒）：
1. ≥2 处真实消费（复制已发生的证据）；
2. 无业务分支（纯取数/纯投影/纯常量/纯 hook），状态归属明确；
3. 命名中性（不带消费方语义——`latest_calc_result` ✓ `scene_result` ✗）；
4. 旧复制同批删除，禁并存（宪法 §2）；
5. 契约同步：core 走 structure-graph §1c 机器声明块（ADR-014 既有机制）；
   server/webapp 走 file-contracts/README 登记义务。

**收敛清单（按面分批）**：

| 批 | 面 | 收敛项 | 承载位置 | 验收 |
|---|---|---|---|---|
| 2a | server | `_latest_calc_result` ×7 复制 | `services/_shared/latest_calc.py`（新子包；共享件禁 import 任何 service——星型单向） | server 全量绿+7 消费面行为零变 |
| 2b | webapp | SSE EventSource 生命周期双实现（useTaskFeed/useExportBatch）；域色字面量双源（unitGlyph/global.css/CanvasFlow LEGEND_LINES） | 前者→`shared/api/useTaskEventSource.ts`；后者→semanticColors.ts 增 domain 键收编 JS 面（global.css `--wp-*` 轴保留——SVG 不能 var() 的根因性债另立 UF，不在本批强解） | vitest 全绿+视觉零漂移（同值搬家） |
| 2c | core | B4 双胞胎（app_assembly `_endpoint/_edges` vs executor_assembly）+`_DOMAIN_EXCEPTIONS`/`_ROW_DOMAIN_EXCEPTIONS` 两份人工同步 | 按 ADR-014 §1c 同层边申报+共享件单源 | golden 三案哈希零变+import-linter 绿 |

批 2c 为架构级——**三段通道**（含社区调研：分层架构中共享内核 vs 复制的取舍实践）。批 2a/2b 为常规实现批（双门全走）。

**明示不做**：flows 直通层与 app.py 再导出门面的拆除（UF-33 语义在役，
涉及 server 消费面全量改写——挂账至联合枚举批前重估）；500 行预算拆件
动机问题（行数预算本身不动——拆件策略随各批自审）。

## 方案三：registry 分性质改造

**事实底座**：`data/coefficients/factors.yaml` 147KB 单文件在库且 CI 绿
——证明数据 YAML 不受 500 行门禁约束（check_file_budgets 只管源码；
实施批首步跑门禁脚本复核此断言）。行数热点：assumptions.py 500/500、
formulas.py 487/500、dimension_specs.py 258、coefficients.py 283。

**三步（每步独立可验收，行为零变）**：

1. **纯数值 YAML 化**：`registry/assumptions.py` 的数值表外置
   `data/assumptions/{municipal,mine_water,sludge,conveyance}.yaml` +
   `manifest.yaml`（data_version 沿用现有键版本语义）；Python 面留
   装载器+schema 校验（目标 ≤200 行）。coefficients.py 已是装载器
   形态，不动。
   验收：golden 三案 serialize_bytes 哈希零变（数值等价搬家，
   data_version **不升版**）；键数装载探针不变。
2. **公式按线分片**：`registry/formulas.py` → `registry/formulas/
   {common,municipal,mine_water,sludge,conveyance}.py` + `__init__.py`
   聚合正门（对外 `from waterprint.registry import formulas` 消费面
   零改）。注册时机语义保持（import 即注册——聚合正门 import 全分片；
   若存在注册顺序依赖，分片内按原文件序排列，实施批以注册表全量
   dump 前后比对锁定）。
   验收：公式注册表 dump（id×条目哈希）前后一致；core 全量绿。
3. **量纲声明随片**：dimension_specs.py 若为逐公式输出量纲表，随线并入
   各分片（GR-42：量纲真源单归 FormulaSpec.output_dim——本步是把
   平行表收敛进公式对象）。dimensions.py（DimKey 刻度档）保留独立
   （它是类型面不是数据面）。
   验收：out_dims 对账门禁绿（14 道门禁面不动）。

**架构级——三段通道**（社区调研前置：公式注册表分片/数据外置的实践——symbol table 分包、lint 工具链的 rule 分目录等类比源）。

### 批 2 社区实践调研清单（2026-09-18 主控完成——三段通道第 0 步）

**调研项 1：大注册表的分片与注册时机**
- 社区共识（多源交叉）：大插件/规则注册表倾向**运行时/惰性注册**——
  import 时自注册在大规模下有循环导入/部分初始化/启动慢三风险；
  小而受信的集合用急切注册（聚合正门 import 全分片）足够简单。
  来源：[The Registry Design Pattern in Python（Level Up Coding）](https://levelup.gitconnected.com)、
  [A Python Plugin Pattern（Vinnie dot Work）](https://www.vinnie.work)、
  [Module Federation Runtime Plugins](https://module-federation.io)。
- **本项目映射**：formulas 现状=import 时注册（manifest 装载即 register）。
  分片后聚合正门急切 import 全分片=最小变更路线（32 单元量级属「小而
  受信」端）；惰性注册=候选路线②。**拟定者须两案权衡**——急切保持
  注册序确定性（golden 依赖），惰性换启动面（当前 CLI/MCP 启动即全量，
  收益存疑→预期急切胜出，待证）。

**调研项 2：领域数值外置（YAML vs 代码常量）**
- 社区共识：领域常量用 YAML 等数据文件——数据/代码分离硬约束、领域
  专家可编辑、可独立版本化；Python 常量「过于灵活」是主要风险。
  **关键告警：YAML Norway 隐式类型强转（1.0→int、科学计数法误判）+
  严格场景须 schema 校验层**。来源：[SE StackExchange：Python 作配置之弊](https://softwareengineering.stackexchange.com)、
  [Stop Hardcoding Values – Use YAML（TDS）](https://towardsdatascience.com)、
  [YAML vs JSON（AWS）](https://aws.amazon.com)。
- **本项目映射**：coefficients YAML（579 键）生产在役=先例已验；
  assumptions YAML 化须**引号强制（数值字符串口径）+装载 schema 校验**，
  Norway 坑在浮点容差类条目（tolerance=1e-10）最易踩——装载器显式
  float() 收编并断言类型。

**调研项 3（仓内先例，非外部）**：import-linter layers 契约+ADR-014/017
生成器族=分片与登记面既有机型；formulas 分片不动层契约（registry 内部
子包化）——structure-graph §1a 节点为模块级，目录化后须复核生成器口径。

**锁面**：不新增测试文件（行为零变由既有 golden/全量承担）——锁面
零动作。若三段通道终裁要求新增分片守卫测试，走 [HUMAN-LOCK] 三连锁。

**收益**：新单元扩容槽位成型（新线/新单元=加 YAML 分文件+加公式分片，
registry 主文件不再逼近 500）。

## 方案四：README 瘦身 + docs/status.md 生成器

**新生成器** `scripts/gen_status.py`（纯标准库，与 ADR-015/016/017
生成器同族）→ 产出 `docs/status.md`（一页表：指标/值/来源）。

**首批指标**（全部机读，杜绝手写）：
| 指标 | 来源 |
|---|---|
| core/server 测试收集数 | `pytest --collect-only -q` 尾行解析 |
| test-lock 键数 | `test-lock.manifest.json` json load len（并分 core/server/agent 三计） |
| 门禁数 | import `scripts/run_gates.py` 的 GATES 列表 len |
| OpenAPI 操作数 | `api-contracts/openapi.json` paths×methods 计数 |
| ADR 件数 | `docs/adr/ADR-*.md` glob |
| UF 登记/闭合/临置/开放计数 | `docs/undefined-features-register.md` 状态标记 grep |
| 数据包键数 | 各 `data/*/manifest.yaml` 声明计数 |
| 快照哈希锚数 | `core/tests/snapshots/` 结构计数 |

**CI 挂载**：ci.yml 既有「生成物再生成比对」步骤族内并入 gen_status
重生成 diff=0 检查（不新增 GATES 条目——生成器纪律非门禁）。

**README 重写**：状态段 178 行 → 三行（一句话现状+里程碑指针+「一切
计数见 docs/status.md」）；178 行批次编年史全文迁归档区
`E:/zcode_md/waterprint-archive/parent-docs/readme-status-history-2026-09.md`
（仓外，克隆者本来就该从 docs/ 取状态）。README 其余节（导览/命令/
部署/网络对策/目录/只读机制）保留。

**顺带勘误**（漂移三说/两说一次收口）：testing.md 锁键句、index.md
「ADR-001~009」句、user-manual 端点计数句——全部改「以 docs/status.md
为准」指针；快照「四哈希」句勘正为三哈希。

性质：文档批+生成器——轻量双审。

## 方案五：未来业务路线与槽位建设

**排序（裁决⑤）**：①操作链集中 debug ②碳核算 ③联合枚举 ④AI 集成
⑤矿井水段二+软著。

| # | 业务 | 落点与槽位 | 前置依赖 | 通道 |
|---|---|---|---|---|
| ① | 操作链集中 debug | 观测面聚合：复用 calc-diag 独立 artifact（ADR-012）+任务事件流+trace——新增 `GET /api/debug/ops-chain`（或 events 流扩展）聚合一次操作链全链事件时间线；webapp 新「诊断」pane | 批 2a 投影共享件槽位（新结果面板=填槽） | 实现批 |
| ② | 碳核算模块 | 新 L3 子系统 `core/waterprint/carbon/`（互不依赖 L3 律照抄：只消费 result_schema）；碳排因子数据包 `data/carbon_factors/`（起草-追认制）；导出面=计算书新章节；webapp 新 pane | **前置探针结论（2026-09-18 实测，见下节）——路线修正为三段：先建能耗/药耗计算面→再运行成本面→最后碳核算**；每段计算逻辑均留用户审查 | 调研批（三段通道+用户审查计算逻辑） |
| ③ | 联合枚举 | solution/ 子系统内新模块（单单元枚举正门零动）；组合爆炸治理=约束剪枝+分层枚举 | ADR-005 语义修订（「远期研究」解冻须用户裁决）；方案三完成（registry 槽位承受新枚举键） | 三段通道 |
| ④ | AI 集成深化 | agent 面 21 工具扩展：操作链 debug 观测面对 agent 开放+知识检索扩碳核算/联合枚举+设计说明书管线（轨道丙）扩展 | ①②落地后价值最大 | 实现批 |
| ⑤a | 矿井水段二 | norms mine_water_sludge_line 手算表追认（用户域）→单元包脚手架 `wp new-unit` | 追认完成 | 表实合批 |
| ⑤b | 软著 | **用户亲查核心码**——组织形态：实现批任务书增「人类可读性优先」纪律；AI 不动计算语义只做辅助（注释/文档/命名面向审查者）；[HUMAN-LOCK] 纪律照走 | 用户时间窗 | 实现批（人类深度参与） |

**槽位建设=方案二/三的执行副产品**：registry 分片=单元扩容槽；
投影共享件=新结果面板槽；事件 hook=新 pane 槽。先建槽后进业务。

### 碳核算前置探针结果（2026-09-18 实测——批 1 搭车完成）

grep 实测（core/waterprint 全量+data/unit_prices+docs/business-logic）：

| 面 | 现状 | 证据 |
|---|---|---|
| 电耗计算 | **空白**：无任何单元输出装机功率/电耗字段 | result_schema 零命中 power/energy/电；units_lib 仅 tiaojiechi 有 w_stir（输入参数=搅拌功率密度，非输出）；曝气（AAO/CASS 最大电耗源）/泵类/搅拌三大耗电源均无功率计算 |
| 药耗计算 | **部分存在**：gaomidu 输出 m_pac/m_pam（kg/d，GM-F12/F14）；mine_water/ningjiao 有药剂面 | 各单元 manifest 实测；**无全厂聚合口径**（result_schema 无药剂聚合字段） |
| 类型面 | DimKey.POWER（W）已在刻度档白名单 | contracts/quantity.py:146/172 |
| 运行成本 | **不存在**：概算=纯建设投资（capex）；PAC/PAM 在单价表=设备购置项 | cost/ 零命中运行费/电费/药费；unit_prices/installations.yaml |

**结论**：碳核算不是「读现成电耗药耗×因子」，前置是**先建运营消耗
计算面**。修正路线（每段独立可验收、计算逻辑均呈用户审查）：
1. **能耗药耗计算批**：单元级 power/dose 输出（曝气供气→风机功率、
   泵扬程→轴功率、搅拌功率已有密度参数可升级）+result_schema 全厂
   聚合字段（电耗 kWh/d、药耗 kg/d 分项）；
2. **运行成本面**（opex）：电价/药价数据包+年运行成本计算——概算
   子系统升位或并列新 L3（三段通道裁决）；
3. **碳核算**：碳排因子数据包（调研 IPCC/行业指南后起草-追认）×
   能耗药耗——吨水碳强度等指标+导出面。
先做①②才能给③供数；①②本身即有独立工程价值（运营成本估算）。

## 批次编排总览

```
批 0（本批）   规则适配（AGENTS.md ORG-SEG v2）+清理+本设计稿
批 1（文档批） 方案一 sunset 表 + 方案四 README/status.md + 漂移勘误
批 2（架构批） 方案三 registry 分性质        ┐ 各自三段通道
批 3（架构批） 方案二 2a server 投影共享件    ┘ （2b/2c 随后）
批 4         方案五① 操作链 debug 观测面
批 5+        碳核算（三段）→联合枚举（三段）→AI 集成→矿井水/软著
```

顺序理由：sunset 纪律先行（后续所有批的退役规则）；槽位（批 2/3）
先于新业务（批 4+）；文档批最轻先收口建立节奏。

## 风险与回退

- 每批独立可回退（git revert 单批）；行为零变批以 golden/快照哈希
  为硬闸，红即回炉。
- 方案三 data_version 不升版的前提=数值等价搬家，若装载顺序差异导致
  浮点差异 → 立即停批上报（不许调 golden 迁就）。
- 方案二 2c 动 import-linter 契约——§1c 声明块先行（图谱先改后码，
  宪法 §13）。
- 软著批若与清理/重构冲突——软著申报以**稳定快照**为准（建议软著批
  从当前 HEAD 拉独立分支，重构不污染申报面）。

## 待用户裁决问题（2026-09-18 二轮裁决后全部闭卷）

1. ~~user_think.png 用途？~~ → 已裁：过时直接删（已执行）。
2. ~~软著亲查范围？~~ → 已裁：计算核心优先（graph/registry/units_lib）。
3. ~~README 历史迁移目标确认？~~ → 已裁：确认归档区路径。
4. ~~碳核算探针搭车批 1？~~ → 已裁：批准+探针已完成（见方案五探针节）；
   碳核算本体先详细调研再立项，计算逻辑留用户审查。
