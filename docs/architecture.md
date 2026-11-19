# 工程架构（architecture）

> 本文描述 WaterPrint 的当前工程现状，分六组：目标与约束、系统边界与方案策略、
> 模块结构与关键运行流程、部署与横切约定、架构决策索引、质量目标与已知风险。
> 规则的执行权威是门禁脚本（`scripts/run_gates.py`）；决策详情见 `docs/adr/`；
> 逐文件职责见 `docs/file-contracts.md`；依赖与调用链细目见 `docs/structure-graph.md`。

## 1. 目标与约束

### 1.1 产品目标

污水处理工艺设计计算平台：用户在节点画布上布置工艺单元、连线成流程图，
平台完成全厂水力/水质/泥量计算、方案枚举与约束校核，产出概算、图纸
（DXF/IFC）、三维布置与计算说明书。覆盖市政污水与矿井水两条工艺线，
工艺单元库分 municipal / mine_water / sludge / conveyance 四线
（在役包数见 `docs/status.md`）。

### 1.2 质量目标

- **确定性**：同输入双跑字节级一致；序列化往返无损；incremental 结果与
  全量重算字节级一致（常驻测试）。
- **可复算**：结果 = f(design_hash, engine_version, data_version)；缓存只是
  优化不参与语义；输入变更后旧结果标 stale，不静默覆盖。
- **防双轨**：每个耦合量、每类数值只有一个真源（manifest 声明 / registry
  数据包 / 结果契约字段 ID）。
- **可审计**：数值带出处（GB 国标/行业标准/设计手册三类）；警告必带来源
  条文与调节方向；计算迹可回放。

### 1.3 工程硬约束（CI 门禁强制）

- 分层依赖只许向下（import-linter，见 §3.1）。
- `.py/.ts/.tsx/.md` 文件 ≤500 行；units_lib 的 compute.py ≤400 行。
- 禁占位实现、禁裸 `except`、禁魔法数字（数值真源=registry 数据包+manifest）。
- 测试目录只读（哈希清单校验，见 §4.6）。
- 仓内 markdown 禁 AI 模型代号；全部文件 UTF-8。

## 2. 系统边界与方案策略

### 2.1 系统与边界

| 系统 | 路径 | 职责 | 边界 |
|---|---|---|---|
| 计算内核 | `core/waterprint/` | 纯 Python：单元库、图引擎、枚举、导出 | 禁 import 服务层依赖（fastapi/structlog）；数值零字面量 |
| 服务层 | `server/waterprint_server/` | FastAPI：routers → services → jobs，计算进程池、任务注册表、导出 | 不含工艺计算逻辑（例外：FD design-map 可行域求值在进程内 asyncio.to_thread 同步直返——~1s 级 CPU 防阻塞，非计算进程池；其余同步端点内联执行轻投影面，async 阻塞策略两制为接受设计，见 §6.1 #19）；统一异常映射 |
| 前端 | `webapp/src/` | React + R3F 三维（feature 切片）；交互画布在 app 层（shellV4/thumbnailFlow），canvas 片承载投影/数据层 | API 客户端由 OpenAPI 生成（orval），禁手写 |
| 数据包 | `data/` | 版本化数值资产（assumptions/coefficients/constraint_kb/templates/unit_prices） | 全部带出处；随镜像分发，不占运行卷 |
| 契约源 | `api-contracts/openapi.json` | OpenAPI 契约 | 前端客户端唯一生成源 |
| agent 面 | `agent/waterprint_agent/` | 本地 chat CLI：LLM 对话经 toolspec 23 工具操作项目与计算（ADR-027），沙箱隔离 | 经 core.flows 共享编排层（ADR-022），不旁路内核；无 MCP/外部宿主面 |

### 2.2 关键方案策略

- **声明式单元**：每个工艺单元是一个声明式包（manifest 声明参数/端口/去除率/
  规范引用/工况映射），compute 是唯一计算正门；工况对参数的影响只走 manifest
  映射，代码内无工况 if 分支（ADR-007/011）。
- **字段 ID 契约**：内核输出契约 = result_schema 字段 ID（键集全 ASCII）；
  概算/图纸/三维按字段 ID 取数；参数/输出级中文名真源 = manifest 的
  label_zh 值字段，由 i18n 显示链路消费。
- **API 单源**：OpenAPI → orval 生成前端客户端；schema 变更走 ADR + 契约
  测试 + 前端重新生成三步。
- **工况语义**：flow_case 全局 2 档（design/avg）× pool 逐单元检修敏感性，
  运行次数 = 2 + k，禁止 2^n 全组合（ADR-007）。
- **枚举语义**：单单元枚举 + 全厂传播（ADR-005）；全厂联合枚举已落地为
  异步任务（`POST /api/solution/joint-enumerate`，ADR-025 分层 beam 方案）。
- **导出基线**：DXF R2018 为默认恒定交付格式（ADR-006）；DWG 经用户自装
  ODA 转换器可选；PDF 计算书经 Typst 引擎；IFC 三维交换。
- **单位制三层**：pint 只在边界（输入/输出/schema/序列化）；内核热路径用
  规范单位裸数组（流量 m³/s、浓度 mg/L、几何 m）。落盘口径分两形：
  数据包与边界 Quantity = 数值 + 显式 unit/dim 字段；结果树/诊断/项目
  文件 = 规范单位裸值，单位语义经字段 ID → registry 单位元数据恢复
  （ADR-002）。

## 3. 模块结构与关键运行流程

### 3.1 分层总览

层序（依赖只许向下，双向校验见 `docs/structure-graph.md` §1）：

```
L6  webapp / waterprint_agent        内核的两种客户端（浏览器 / 本地 chat CLI）
L5  server：main → routers → services → jobs → settings
L4  cli → flows → report → app(app_enumeration/app_export...) → project/trace
L3  graph / solution / elevation / cost / drafting / geometry / ifc_export / network
L2  units_lib（单元包，包间禁互 import）
L1  registry（assumptions/coefficients 装载）
L0  contracts（result_schema / unit_api / 领域异常 / 端口协议）
    data（DATA 数据包）· api-contracts（CONTRACT OpenAPI）
```

L3 子系统互不依赖（independence 契约），主消费面为 contracts 层；部分子系统另
有登记在册的 registry 与数据包边（假设默认值/公式/单价取数，细目见
structure-graph.md §1 边表）。装配：graph/executor.py 只依赖 contracts 层
（含 unit_api 协议），零具体单元依赖；单元发现/实例化实现在 app 节点的
伴生件 `app_assembly.py`（app.py 为装配门面）。

### 3.2 计算主链

```
项目文件（design 态，参与 content-hash）
  → graph 构建（节点=单元实例，边=端口连接；SCC 识别回路）
  → 汇流/缺项传播（graph/propagate，§3.4 规则）
  → executor 逐单元求值（manifest 工况映射 → compute 向量化路径）
  → result_schema 结果树 + 警告流（app_validation）
  → solution 约束过滤与方案排序（§3.5）
  → 产物导出：xlsx 概算 / DXF 图纸 / HTML 报告 / IFC 三维 / PDF 计算书
```

回路（污泥外回流 R、滤液/上清液回流）走 SCC 回路组固定点迭代 + 阻尼 +
发散诊断（ADR-003）；内回流 Ri 与高密池回流是包内参数，不进图迭代。

### 3.3 参数初始化链

```
manifest 默认值（带条文出处）
  → assumptions 注入（registry 唯一真源，含出处/适用条件/调节影响元数据；
    项目 assumption_overrides 覆盖）
  → 用户参数覆盖（design 态）
  → 工况映射（manifest 声明式规则）
  → compute 消费
```

初始参数不保证可行是设计预期：第一次计算允许约束失败，失败是方案空间
探索的入口（§3.5）。

### 3.4 单元间业务规则

**耦合量单一归属**（防双源，值只在一处拥有，他处经结果契约只读）：

| 耦合量 | 归属 |
|---|---|
| 外回流比 R、MLSS、污泥负荷 Ns、内回流比 Ri | AAO manifest（可枚举自由参数）；CASS 仅 ns/x_mlss |
| 二沉池固体负荷 | 二沉池派生量，不反向影响 AAO |
| 化学除磷 PAC 投加量（mg/L） | data/coefficients |
| 汇流 Kz | 取 max（graph/propagate 语义） |
| 泥量含水率链 | 各单元 manifest 改写并产出新 SludgeFlow，禁原地修改 |
| 工况键 condition_key | 图引擎分配，全链路只读 |

**汇流派生式**（WATER 股多股汇入同一 dst 端口）：q_avg_total=Σ（按 PortRef
排序求和）；Kz_total=max；q_design_total=q_avg_total×Kz_total（派生属性，
无双轨）；水质按当前工况流量负荷加权（非浓度平均）；SLUDGE 股独立走
sludge.mix（湿量/DS 双守恒）。

**缺项指标三层语义**：mix 层按在场股加权（全缺=键不存在）；零依赖面缺项
透传不伪值；公式依赖面进水缺项=InvalidUnitConfig 领域异常（不跳过不默认 0）。

**守恒断言点**（性质测试挂钩）：汇流节点流量/负荷守恒；污泥合并湿量与 DS
双守恒；浓缩/消化/脱水/干化 DS 守恒且含水率单调下降；化学除磷泥量计入
污泥线；高程链水面衔接连续（跌水/提升显式事件化）。

**约束联动链**（上游承诺字段 → 下游进水要求的跨单元校核，规划语义：
constraint_kb 现无跨单元条目，见 §6.1）：高密池出水 SS ↔ V 滤进水
SS<20（GB 50014-2021 §7.11.7）；V 滤出水 SS ≤10 ↔ 紫外消毒剂量前提；
AAO 进水 BOD5/TN≥4 ↔ 初沉超越开关依据。

**离散枚举对象**：管径、水泵台数、巴歇尔槽喉宽档、池数/分格数、CASS 周期档、
消化温度档、干化出泥档——档位即 manifest 声明的 grid。

耦合归属/汇流派生式/守恒断言/联动链细目见 [docs/business-logic.md](business-logic.md)。

### 3.5 可行解闭环（核心产品语义）

```
计算 → 约束过滤（solution/constraints，pass_matrix）
  ├─ 有可行解 → 排序输出（裕度/成本）
  └─ 无可行解 → 诊断（最小冲突集）→ 建议清单（参数键/方向/幅度/依据/影响面）
        → 用户调整（手动或显式"建议应用"= design 变更）→ 重算，循环
```

建议来源现两条：约束知识库规则（失败建议方向由约束表达式算符推导，
constraint_kb 条目无独立建议字段）、枚举统计（可行域边缘分布）；
专家经验表（coefficients）为规划中的第三来源，solution/diagnose.py
尚未消费（开放面见 §6.1）。建议应用必须落
design 态变更 + 新 content-hash，不允许后台自调。

### 3.6 导出与图纸/三维

- **概算**：xlsx（openpyxl 直写，单价取 data/unit_prices；data/templates
  模板服务计算书与管网两产物）。
- **图纸**：DXF R2018（drafting 层；`sheet=profile` 厂级纵断图白名单路由）；
  DWG 可选（部署侧 ODA 转换器，失败只跳过 DWG 不阻塞 DXF）。
- **报告**：report 层产 Markdown（HTML 呈现由 webapp KaTeX 承担）与
  Typst 源（PDF 由 server 调 typst CLI 编译），公式源 = sympy 表达式树
  单源双态打印；HTML 审计报告是另一 artifact（trace/audit.py）。
- **三维**：IFC 交换（ifc_export）+ 前端 R3F 场景（viewer3d feature，server
  scene 端点供站序/布置）；Blender 参数化建模管线在 `tools/blender/`
  （渲染资产生产工具链）。

### 3.7 警告体系

三级：error（约束硬失败/配置非法）/ warn（越出建议带未违反强条）/ info
（假设生效提示）。每条警告必带来源（条文/知识库键）+ 调节方向（参数键）+
影响面。服务端聚合按去重键三元组 **(code, param_key, scope)** 跨工况聚合：
scope=影响面（"plant" 或节点 ID），命中=越门实例，severity 取最严重，
命中工况键清单按 ConditionSet 迭代序；API 字段名硬约束 `scope` +
`condition_keys[]`（客户端零去重逻辑）。core 两载体字段语义映射
（AUDIT-#5 裁决定案 2026-11-18：维持现名不改，接受设计非开放债，
见 §6.1）：PlantWarning.condition_key 载荷=影响面，
unit_api.Warning.condition_key=所属工况键。契约两处：单条警告=`core/waterprint/contracts/validation.py`
（PlantWarning），聚合响应行=`server/waterprint_server/services/validation.py`
（AggregatedWarning）。前端聚合视图已接线（webapp `features/validation`
切片消费，analysisPane 全厂面内嵌——T3 2026-11-19）。

### 3.8 单元包结构（脚手架生成，禁自由发挥）

```
units_lib/<line>/<unit>/
├─ manifest.py        # 声明式清单：参数/端口/去除率/规范引用/工况映射（唯一对外）
├─ compute.py         # 唯一计算源；≤400 行（形态两态见下注）
├─ constraints.py     # 声明式约束定义
├─ README.md          # 一段话职责 + 输入输出
└─ tests/             # test_compute.py（golden 数值）+ properties*.py（物理不变性；
                      #   向量化包另含 test_vector_baseline/variants.py）
```

单元对外只暴露 `UNIT_ID`、`make_unit`、`manifest` 三名（装配消费面按
两名铁律校验 manifest+make_unit）。compute 形态两态为受支持路径（ADR-011
豁免定案 2026-11-18）：municipal 13 包 = `_apply_batch` 同源向量路径，
其余三线 19 包 = `_apply` 标量路径——批量=逐行调用（19 包逐行 `_apply`
驱动、13 包 N=1 退化形态），非逐元素向量语义；向量包 N>1 批量的首元素
离散口径（aao/compute.py 四处取首）为已知边界，显式 N==1 拒绝守卫已随
审计治理批 b26 落地（`_first` 取首前域错误拒绝，消息注明成文前提；
N==1 数值与消息零变化）。新单元用
`uv run python -m waterprint.cli new-unit <line> <name>`（core 目录执行；
wp console script 未注册）从 `_template` 生成，先登记 structure-graph §3
与 file-contracts §3 再实现。预算墙拆件配方（ADR-024）：manifest 顶墙立
`formulas_<族名>.py` 兄弟声明件；compute 顶墙迁 `<段名>.py` 计算段；
compute.py 仍是唯一计算正门。

### 3.9 agent 面

`agent/waterprint_agent/`：本地 chat CLI（`python -m waterprint_agent.chat`），经 server
ai_chat 子进程桥供 webapp 对话；工具面=chat/toolspec 23 工具 schema+dispatch
直调 impl（ADR-027 去 harness 化后的唯一工具真源）；沙箱五区+PathGuard
与会话审计链沿承（原 ADR-021 D2~D4 语义继续适用）；用例编排复用 core.flows
层（ADR-022）；数值溯源第一铁律（ADR-019）。分层契约由 import-linter 与 check_module_graph L6 节点校验（ADR-020）。

## 4. 部署与横切约定

### 4.1 部署形态（Docker 双容器）

`docker compose -f deploy/compose.yml up -d --build`：server（FastAPI/uvicorn，
容器内 0.0.0.0:8000，**不发布宿主**）+ webapp（nginx 承载前端静态产物并反代
`/api`）。对外唯一入口 = http://localhost:8080，只应在可信内网/防火墙后暴露。

**安全红线**：任何经反代/端口映射对外可达的部署形态，无论绑定地址，必须配置
`WATERPRINT_API_TOKEN`（Bearer token，≥16 位；除三个公开只读 GET
〔assumptions/constraints/units〕外全部操作受保，受保面以
`api-contracts/openapi.json` 的 security 字段为准；token 空=鉴权关）。
机器防线：token 空且 `WATERPRINT_HOST` 不在回环集合时启动即失败。服务单进程
契约（api replicas=1 + calc workers=N），不可水平扩副本。

**PDF 计算书前置**：默认 server 镜像不安装 typst CLI 与 PDF 字体；PDF 导出
（`POST /api/exports/report_pdf`）要求服务主机具备 typst（PATH 发现或
`WATERPRINT_TYPST_PATH` 指定）及系统字体 Times New Roman + SimSun，缺失时
端点显式报错（安装细目见 [docs/archive/deployment.md](archive/deployment.md)
「导出格式」节）。

数据卷：`waterprint_wp-projects`（项目 *.wp.json）与 `waterprint_wp-exports`
（导出产物）；数据包打入镜像不占卷。缺数据包=启动即拒绝（双入口校验：
`python -m` 启动块+容器 entrypoint；校验面=五包
assumptions/coefficients/constraint_kb/templates/unit_prices，AUDIT-#3 b24
起 assumptions 收口进校验面，core 装载同走 `WATERPRINT_DATA_DIR`）。
本地开发注记：server venv 的 waterprint-core 为非 editable 拷贝安装——core 改动后须 `uv sync --reinstall-package waterprint-core` 刷新再跑 server 测试（CI fresh sync 无此问题）。
data_version 聚合串=三包 `assumptions@…+coefficients@…+unit_prices@…`
（包名排序拼接；assumptions 版本槽入聚合系 AUDIT-#4 b24，抬版仍需人工）。
服务重启不续跑任务：崩溃/强杀残留的排队与运行中任务转 failed
（InterruptedByRestart），优雅停机时排队任务转 cancelled；终态任务
记录可查。

开发态：`cd server && uv run python -m waterprint_server.main` 默认只听
127.0.0.1:8000；数据包缺省自动定位 `<仓库根>/data`。

### 4.2 环境变量（WATERPRINT_ 前缀）

仅列部署关键面；全字段与裸机缺省值见 `server/waterprint_server/settings.py`。
表中 /app/* 默认值为容器口径（Dockerfile ENV）；裸机缺省 projects/exports
为 CWD 相对、data 为包定位。

| 变量 | 默认 | 说明 |
|---|---|---|
| `WATERPRINT_PROJECTS_DIR` / `WATERPRINT_EXPORTS_DIR` | /app/projects、/app/exports | 项目/导出根（卷挂载点）；裸机缺省两基点不对称——projects_dir 保持 CWD 相对形态、exports_dir 构造期 resolve() 绝对化（接受设计，见 §6.1 #32） |
| `WATERPRINT_DATA_DIR` | /app/data | 数据包根（五包同根；AUDIT-#3 b24 起 assumptions 亦走本 env——core registry 装载与 server 启动校验同源） |
| `WATERPRINT_CALC_WORKERS` | max(1, CPU 数−1) | 计算进程池大小 |
| `WATERPRINT_API_TOKEN` | 空=鉴权关 | Bearer token，非空即生效，≥16 位 |
| `WATERPRINT_HOST` / `WATERPRINT_PORT` | 127.0.0.1:8000 | 裸机绑定面（容器内不生效） |
| `WATERPRINT_DWG_CONVERTER_PATH` / `..._TIMEOUT_S` | 空=关 / 100 | ODA DXF→DWG 可选转换 |
| `WATERPRINT_TYPST_PATH` / `..._TIMEOUT_S` | 空=PATH 发现 / 100 | PDF 计算书引擎 |
| `WATERPRINT_LOG_LEVEL` / `WATERPRINT_LOG_FILE` | INFO | 日志级别 / JSON 行落点 |
| `WATERPRINT_MAX_UPLOAD_MB` | 10 | 上传体积闸 |

### 4.3 单位制与数值

pint 只存在于边界；内核裸数组（m³/s、mg/L、m）；落盘"数值 + 显式 unit
字段"。数值真源唯一 = registry 数据包 + manifest 声明面；假设条目六字段
（键/默认值/量纲 dim/出处/备注 note/调节影响）。出处准入口径三类：GB 国标、行业标准
（CJJ 131-2009 等）、《给水排水设计手册》；现存数据包尚有旧系统基线与
"出处待核对"条目未按此口径收口（见 §6.1）。

### 4.4 错误处理

领域异常（InvalidUnitConfig/LoopDivergence 等）与程序缺陷二分；内核禁抛
HTTP 语义异常；server 层唯一翻译处按映射表注册 exception handler
（异常→状态码映射单源=server main_lib `_EXCEPTION_STATUS`，状态集以该表
为准；429 附 Retry-After 头。b28 起 ai_chat 路由直抛 HTTPException 破例
收编——全部路由异常经统一翻译处，错误体统一 {detail, error_type}）。
禁止裸 except 与错误静默通过；捕获后三选一（处理/转换再抛/终止）。

### 4.5 日志

structlog JSON 行（容器内 /app/waterprint-server.log）；日志是结构化事实
不是叙事文本；SSE 事件流（events 端点）推送任务进度。

### 4.6 测试体系

- 分层：架构门禁 → 镜像单测（骨架期休眠 skip，实现合入归零，CI `-ra`
  平台守卫白名单外 SKIP 即 FAIL）→ 性质测试（hypothesis，守恒/单调/往返/
  结合四模板）→ golden 端到端（期望值只在 `core/tests/golden/golden_data/`，
  基准来自 docs/norms 手算对照表）→ 快照回归（syrupy 锚 xlsx/DXF/HTML
  内容哈希，ADR-010）→ 性能基准。
- 只读锁：`core/tests/`、`server/tests/`、units_lib 包内 `tests/` 全部文件
  由 `test-lock.manifest.json`（sha256）锁定；改测试 = 人类显式流程
  （`scripts/lock_tests.py`），触碰三信任根的 commit 须带 `[HUMAN-LOCK]`。
- 门禁覆盖面（AUDIT-#20，b30 2026-11-18）：grep 三查（占位/宽族 except/
  乱码）SCAN_DIRS 全域含 `agent/`（tests 一并在扫，.venv 排除）；
  宽族 except 精确豁免登记=`gate_patterns.WIDE_EXCEPT_WAIVERS`（键=文件+
  函数限定名〔含类链〕+异常族〔AST 精确类型名，前缀连写不冒充〕+理由
  非空，行号不作键；一条豁免至多消费一个处理器，同键第二处必红——
  b30 回炉收 blocker/major）。豁免失效条件：函数改名/异常族变化/兜底
  删除（未消费豁免=腐烂报警）即转红触发审查；第四处宽族不在表必红，
  豁免无整文件/整目录排除形态。
- 红绿纪律：每个测试先失败一次再通过才算数。
- 前端：vitest（webapp/src/**/*.test.*）；计数以 `docs/status.md` 生成值为准。

### 4.7 序列化与确定性

项目文件双态（design 态参与 content-hash / 结果态绑定快照 hash，ADR-004）；
序列化键排序、round(x,10) 浮点定点、无随机 ID、保存两次字节级相同；
`__snapshots__` 更新走显式命令 + 人审。

## 5. 架构决策索引

| ADR | 决策（一句） |
|---|---|
| [ADR-001](adr/ADR-001-react-flow-canvas.md) | 节点画布采用 React Flow（含三维参数化 schema 与 R3F） |
| [ADR-002](adr/ADR-002-unit-strategy.md) | 单位制三层策略（pint 边界 / 裸数组内核 / 注册表元数据） |
| [ADR-003](adr/ADR-003-loop-iteration.md) | 回路迭代策略（固定点 + 阻尼 + 发散诊断） |
| [ADR-004](adr/ADR-004-project-dual-state.md) | 项目文件双态结构与确定性序列化 |
| [ADR-005](adr/ADR-005-enumeration-semantics.md) | 方案枚举语义（单单元枚举 + 全厂传播） |
| [ADR-006](adr/ADR-006-dxf-baseline.md) | DXF 制图基线（R2018 / UTF-8 / 国标字体 / ODA 外挂） |
| [ADR-007](adr/ADR-007-operating-conditions.md) | 工况语义（全局 2 档 × 逐单元检修敏感性，2+k） |
| [ADR-008](adr/ADR-008-process-calculation-routes.md) | 工艺计算方法路线 |
| [ADR-009](adr/ADR-009-defaults-and-coefficients.md) | 默认值与系数库层级 |
| [ADR-010](adr/ADR-010-export-snapshot-testing.md) | 导出产物快照测试 |
| [ADR-011](adr/ADR-011-vectorized-compute.md) | 向量化 compute 唯一化（批量=同源向量路径） |
| [ADR-012](adr/ADR-012-trust-diagnostics.md) | 结果可信度诊断通道（独立并列 artifact） |
| [ADR-013](adr/ADR-013-semantic-gates.md) | 语义门禁词汇面 |
| [ADR-014](adr/ADR-014-same-layer-edges.md) | 同层边一等公民化（生成器 + 双向校验） |
| [ADR-015](adr/ADR-015-lock-manifest-draft.md) | 锁面 manifest CI 草稿重生成 |
| [ADR-016](adr/ADR-016-contract-line-annotations.md) | file-contracts 行数注记数字生成化 |
| [ADR-017](adr/ADR-017-structure-nodes-generated.md) | structure-graph 节点表生成化 |
| [ADR-018](adr/ADR-018-multi-condition-compare-lock.md) | 多工况对比与锁定 |
| [ADR-019](adr/ADR-019-numeric-provenance.md) | 数值溯源（agent 面第一铁律） |
| [ADR-020](adr/ADR-020-agent-face-contracts.md) | agent 面分层契约 |
| [ADR-021](adr/ADR-021-mcp-sync-sandbox.md) | agent 面运行模型（MCP 同步 + 沙箱隔离）〔superseded by ADR-027〕 |
| [ADR-022](adr/ADR-022-core-flows-layer.md) | core.flows 用例流共享层 |
| [ADR-023](adr/ADR-023-status-generator-sunset.md) | status.md 计数生成源 |
| [ADR-024](adr/ADR-024-energy-dose-calculation-face.md) | 能耗药耗计算面（单元级输出 + 全厂聚合） |
| [ADR-025](adr/ADR-025-joint-enumeration.md) | 全厂联合枚举（分层 beam） |
| [ADR-026](adr/ADR-026-kb-block-gate.md) | kb 断路器运行时执法（design 帧阻断门） |
| [ADR-027](adr/ADR-027-agent-local-chat-only.md) | agent 面去 harness 化（MCP 面退役，只留本地 chat） |

## 6. 质量目标、已知风险与术语

### 6.1 已知风险与在册开放面

审计治理（2026-11-18，34 项）定档后的在册挂账如下表——本表为仓内挂账
唯一权威载体（编号=审计议题号；重启触发条件未发生即不重启）。#5/#26 为
用户裁决不改（接受设计，非开放债）；#10 为独立产品/schema 需求（未立项）；
#22 状态随 #1 不独立挂账——#1/#22 已随 b23（2026-11-18）四伴生件迁
solution 收口（L3→L4 上行 import 消除、伴生件入图谱节点进入校验覆盖，
表行随之退役）；#2（compute 双形态）已随 ADR-011 豁免定案
收口（现行口径见 §3.8，AAO N==1 守卫已随 b26 落地，不构成在册开放面）。

| AUDIT | 类型 | 当前决定 | 重启触发条件 | 代码锚 |
|---|---|---|---|---|
| #5 | 接受设计（裁决不改） | condition_key 双载体保留现名：PlantWarning.condition_key=影响面、unit_api.Warning.condition_key=工况键（§3.7 映射为定案） | core 公共契约准备做版本化迁移且旧 artifact 有处置方案 | core/waterprint/contracts/validation.py:80；contracts/unit_api.py:113 |
| #9 | 开放债（P3） | compareView 三格式化函数本层复刻 solutionsView 配方（12 行；features 互禁 import 的显式替代，注记在案） | 出现第三份复刻、格式规则漂移或 shared 层有明确通用归属 | webapp/src/features/compare/lib/compareView.ts:190-204 |
| #10 | 产品需求（未立项） | Constraint.source 存 kb 键、来源文本装载即弃；Suggestion.basis 只能引键，不扩 schema | 产品明确需要 Suggestion.basis 展示完整来源文本并批准 schema/ADR 涟漪 | core/waterprint/solution/constraints.py:412 |
| #12 | 接受设计 | 批量导出 _ITEM_FAILURES 宽族=H2 项级隔离策略（单项失败不株连批内他项，批终态 done+failures） | 出现 core 缺陷被折叠为项级 failures 的实际事故，或重新裁定项级/批共因边界 | server/waterprint_server/jobs/worker.py:342-344,450 |
| #15 | 开放债（P3） | elevation 纵断 water_depth 缺键静默 0（depth_key=None 分支有 INFO 警告——不对称） | 该输入路径成为用户可达或诊断缺失造成实际问题 | core/waterprint/elevation/profile.py:136 |
| #19 | 接受设计 | async 阻塞策略两制：design-map 进程内 asyncio.to_thread 同步直返例外（~1s 级 CPU 防阻塞），其余同步端点内联轻投影（§2.1 注记） | CPU profiling 证明事件循环阻塞，或新增重 CPU 端点 | server/waterprint_server/routers/calc.py:298-300 |
| #24 | 开放语义债 | manifest 容错两制：unit_prices 装载 fail-fast vs data_version 聚合读 manifest 缺失/畸形静默跳过——本轮不归一 | 部署确定「无 manifest 必须 fail-fast」或确认容忍为公开契约 | core/waterprint/app.py:324-330；core/waterprint/cost/prices.py:69-78 |
| #25 | 开放债（P3） | _design_scale_of 多进水 sorted 取首快照无警告（无输入节点流量已有 InvalidFlowError 兜底） | 多进水成为受支持场景或出现误用 | core/waterprint/flows/__init__.py:363-380 |
| #26 | 接受设计（裁决不改） | executor 恒等再导出壳（noqa F401）=锁名设计，镜像测试 `is` 恒等断言有意钉死；SLUDGE 初值 mm×mm 借用派生有注释+golden 锚 | 锁名意图本身被新架构裁决撤销 | core/waterprint/graph/executor.py:123-140,161-163 |
| #27b | 开放债 | 导出 stale 409 先于路由选项 422 校验的次序维持现状（#27a walrus 泄漏清理已随 b29 2026-11-18 收口——仅剩本次序开放面） | API 明确要统一错误优先级并批准锁测/契约变化 | server/waterprint_server/services/exports.py:299-315 |
| #31 | 开放债（P3） | formulas_kernel.evaluate_batch 空映射裸 StopIteration（正门 apply_batch 已拦，仅绕正门可达） | formulas_kernel 成为直接公共入口 | core/waterprint/registry/formulas_kernel.py:240 |
| #32 | 接受设计 | create_app AI 四键 os.environ.setdefault=B4-4b W1-k2 裁决的进程级注入点（worker 子进程桥只读 env）；路径基点不对称（§4.2 注记）仅注记 | 部署合同要统一 CWD/resolve 基点语义 | server/waterprint_server/settings.py:120,125；server/waterprint_server/main.py:235-244 |
| #33 | 开放债（P3） | drafting plan_view 零尺寸/gap_count 未守卫（max(count,1) 防除零，未防零长度分格产物） | 零/负尺寸成为合法输入或实际出现空分格产物 | core/waterprint/drafting/plan_view.py:124-139 |
| #34 | 接受设计 | flows 包内循环依赖以函数内懒 import 破环（export_batch_lib 先例，注记在案） | 循环依赖阻碍新功能或出现可简化的既有 errors 叶件 | core/waterprint/flows/params_guard.py:187-190 |

其余在册开放面（非上表审计编号体系）：

- **在册功能面**：厂级纵断图真实站距（现按站序排布）；ODA DWG 转换端到端
  冒烟（Linux AppImage 形态）；软著申请与开源准备；专家经验表第三建议
  来源接入（solution/diagnose.py 现仅消费约束条目与 grid 统计）。
- **架构在档挂账（审计执行修复项，随审计治理执行批处置）**：AUDIT-#1/
  #22（joint_enumeration 上行 import）已随 b23 迁移收口；AUDIT-#3/#4
  （assumptions 数据包启动校验+WATERPRINT_DATA_DIR 通道+版本槽入
  data_version 聚合）已随 b24（2026-11-18）收口——五包入校验面、core
  registry 探测序 env 前置、聚合串三包化（版本槽抬版仍人工）；
  AUDIT-#7/#8（确定性 JSON 参数 5+1 处与 loop.* 键集 4 处手工镜像+
  format_version 三源）已随 b25（2026-11-18）收编既有 L0 契约单源
  （result_schema.JSON_KWARGS / run_env.LOOP_KEYS /
  project_schema.CURRENT_FORMAT_VERSION，server projects.py 两镜像同批
  import as 退役——零新文件零新依赖边）——值逐字搬移序列化字节零漂、
  loop 键四引用同一对象（恒等钉同向兼容）；升版口径=当前版字面量
  单源于 project_schema，升版动作=改该常量+migration._FORMAT_HISTORY
  前缀追加旧当前版（两动作，迁移链不丢版）；二沉池
  与 AAO 同值参数双包独立声明、无一致性校核（AUDIT-#6）已随 b26
  （2026-11-18）收口——共同装配点 app_assembly.assemble 增
  `_check_linked_param_defaults`（两包同图装配时校核 x_mlss/r_external
  声明默认值同值，异值 InvalidAssemblyError 明确拒绝不静默选边；单包
  独立装载不校核，包间禁互 import 不破——校核在装配层，两包互不感知）。；AUDIT-#16/#17/#18（复制/惯式
  收敛）已随 b27（2026-11-18）收口——server 四份逐字复制
  _load_diagnostics〔trust/ops_debug/report/validation〕+site 取数降级
  变体收编 services/_shared/latest_calc 既有件（load_diagnostics/
  latest_done_result_or_none——行为对照表六态恒等 None 后机械合并，
  三态降级语义零变；site「无结果返 None 不抛」故意的降级语义保留为
  变体而非改正门）；core 五份同构 summary 合并 helper〔app._with_energy
  +四伴生件 _with_*〕单源=app_energy.merge_summary_fields（五消费面
  保名再导出——锁定测试 import 面恒等，合并前后结果树逐字节恒等，
  app.py 500→495 行预算减压）；原子写惯式四处按 H5 最严清理归一
  （flows 三处抽件内 _atomic_write 单源，project/io save_project 补
  全异常清理——半写 .tmp 不残留；result_persist_flow 的 uuid 唯一
  tmp 名=K-01 并发双写防护故意语义保留，io 与 flows 跨包不共享件
  记为例外非强行统一）；AUDIT-#11/#13/#14（AI 面异常族收编映射单源）
  已随 b28（2026-11-18）收口——ai_chat 路由两处直抛 HTTPException
  (502/422) 收编经 main_lib 类基表〔AiChatReadError→502 入表、
  ValueError→422 走兜底行，状态码不变、错误体统一带 error_type——
  §4.4 破例注记随之撤除〕；ai_chat runner 三处 process.wait 宽限
  超时 TimeoutExpired 领域化〔_wait_child 单源包装转
  AiChatBridgeTimeoutError 入 DOMAIN_ERROR_CODES 名义族（502）——
  failed 任务 error_code 不再 None 游离〕；WorkspaceLayoutError 拆基
  〔不再继承 UvNotFoundError——except UvNotFoundError 误捕布局错误面
  消除，400 经类基表显式注册、响应 400+error_type 不变〕。
  AUDIT-#23 三小项+#27a+#28+#29a/#29b（CLI/导出/agent/OpenAPI 小项）
  已随 b29（2026-11-18）收口——CLI：new-unit 重名拒绝退码 4→3
  （#23a 校验族正身）、calc --conditions 空段/未知单元键本地拒绝
  退出码 3（#23b——原空段静默吞、未知键静默白算敏感性帧；仅 CLI
  面，server worker/agent 各经 build_condition_set/API 不受影响）、
  四业务线名单单源化 units_lib.UNIT_LINES 公开常量（#23c——cli
  choices 与 app_assembly 线名前缀投影改引同源，第三处人工同步点
  消除；contracts.manifest_validation._BUSINESS_LINES 为 L0 分层
  隔离的独立声明面不随收编）；导出：批量命名推导段 walrus 泄漏
  循环变量清理（#27a——行为零变，stale 409 次序开放面见 #27b 行）；
  agent：run_tool 成功载荷不再物化 {"error": null} 入会话 JSONL
  （#28——失败载荷错误语义不变）；server：_safe_out_name docstring
  归位真 docstring 位（#29a——help() 可见，懒 import 语义零变）、
  GET /api/constraints 描述去冻「18 条」数量口径（#29b——openapi
  合法再生 diff 仅 description 一行，orval 生成面同步仅注释一行变）。
  AUDIT-#20/#21（门禁覆盖与计数口径）已随 b30（2026-11-18）收口——
  #20：agent/ 全量纳入 grep 三查 SCAN_DIRS（D7 裁决：纳管+精确豁免，
  不窄化兜底本体，agent 源零改动），三处注释在案的故意宽族兜底
  〔context.run_tool 工具错误 dict 兜底/tools.projects._update_params_impl
  undo 快照守护/tools.solution._run_joint_enumeration_impl 护栏族统一收敛〕
  按"文件+函数限定名+异常族+理由非空"精确豁免登记（WIDE_EXCEPT_WAIVERS，
  行号不作键；未消费豁免=腐烂报警——函数改名/异常族变化/兜底删除即转红
  触发审查；第四处宽族必红，红绿探针实录在案，覆盖面注记见 §4.6。
  b30 回炉（reviewer FAIL 1 blocker+1 major，同日）：豁免改单处理器精确
  消费+限定名入类链+异常族 AST 精确名（原前缀可冒充消费），回归探针）；
  #21：两门禁单元包计数口径明示——check_structure 33=实业务单元 32+
  _template 模板登记行 1、check_module_graph EXPECTED_UNIT_COUNT=32=
  登记 33 剔模板行（模板不注册，登记不删不凑数）。
- **文档登记债**：constraint_kb 无跨单元联动条目（§3.4 联动链示例为
  规划语义）。
- **数值溯源债务**：data/coefficients 部分条目仍为旧系统基线/"出处待核对"
  （removal_rates.yaml、factors.yaml 等），待专家按 §4.3 三类准入口径核定。
- **领域待确认**：浓缩上清液/脱水滤液回流是否纳入 golden 案例（决定回路
  默认值）；矿井水案例"III 类"执行口径（GB 3838 从严 or 地方标准）；
  巴歇尔槽 C/n 系数表按 CJ/T 3008.3-1993 正式文本核对。
- **扩展轴**：合流制截流校核（雨季）不在当前工况轴内（ADR-007 开放封闭）；
  全厂联合枚举已落地（ADR-025）；多副本任务续跑=Redis 化路线（当前不做）。
- **平台差异**：Linux 开发机无 Windows 只读属性屏障，测试完整性依赖哈希
  事后检测（改写会在下一次校验被抓，但无写入阻止）。

### 6.2 术语

| 术语 | 含义 |
|---|---|
| 工艺单元包 | units_lib 下一个自包含单元（manifest/compute/constraints/tests） |
| 工况（condition） | 求值轴：design/avg 两档 + 逐单元检修敏感性档 |
| 影响面（scope） | 警告的作用对象："plant" 或节点 ID（与工况轴正交） |
| 汇流 | 多股 WATER 流入同一 dst 端口的合并（流量求和、Kz 取 max、负荷加权） |
| Kz | 总变化系数（日变化），汇流取 max（保守语义） |
| DS | 干固体（Dry Solid），污泥线守恒量 |
| golden 案例 | 端到端验收案例，期望值存 core/tests/golden/golden_data/ |
| content-hash | design 态内容的确定性哈希，可复算三元组之一 |
| result_schema | L0 的内核输出契约（字段 ID 树） |
| constraint_kb | 约束知识库数据包（条文约束 + 失败建议） |
| 站序排布 | 三维场景缺省布置策略（按流程顺序摆放） |
| 手算对照表 | docs/norms 下测试期望的唯一合法来源（领域专家批量追认） |
