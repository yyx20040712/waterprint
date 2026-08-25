# 未定义特性登记表（逐项处置）

> 业务逻辑本征复杂度高，规格不可能穷举——凡是"规格沉默、实现者会自由发挥"
> 的特性都在此登记并给出处置。**发现新未定义项：先登记（标"疑似"）再继续，
> 禁止就地自创语义**（接手提示词第 3 步）。
> 处置四选一：**已定义→GR-xx 或既有规格条款**（GR-xx 指
> docs/engineering-conventions.md 条号；指向既有规格时注明文件与条号，
> 非"本批新增惯例"）/
> **待定义→T?**（随任务冻结）/ **显式不做**（一句理由）/ **领域专家待拍板**
> （列入问题清单）。归引用：`unified` = 仓库外统一审计清单
> `.workflow/review-unified.md`（A/B/C/D 编号）。

## 一、种子项（总控拍板收录，UF-01~UF-15）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-01 | 数值语义 | 浮点断言容差无基准：测试该用 approx 还是绝对相等、容差多少，各规格头未写，实现者随手拍 | 已定义→GR-01 | conventions §1 |
| UF-02 | 数值语义 | NaN/±Inf 处置：规格头只列异常类型，0/0、溢出产生的 NaN 如何拦截未写（会静默流进出水裕度） | 已定义→GR-02 | conventions §1 |
| UF-03 | 数值语义 | Q=0 与负值语义：负值拒绝已有散点（quality R2），Q=0 是否合法、与厂界 flow.py R2（q>0）的口径分界未写 | 已定义→GR-04（厂界仍按 flow.py R2，分界说明见该条绑定；厂界口径随 T6/T7 propagate 冻结时定稿——总控 2026-08-23 已认可 GR-04 分界） | conventions §1 |
| UF-04 | 确定性 | set 迭代序：`sorted()` 与中文键 locale 陷阱无规格（跨进程/CI 双跑字节差且不可复现） | 已定义→GR-16 | conventions §4 |
| UF-05 | 错误处理 | 异常消息稳定性：消息可否随重构改写未定义（改写=跨版本计算迹 diff 全线飘红） | 已定义→GR-09 | conventions §2 |
| UF-06 | 汇流 | 汇流派生规则：q_avg_total=Σ、Kz_total=max、q_design 派生与两档加权一致性，propagate 规格只写 R1/R2 语义未列派生式，实现 mix() 前须冻结 | 待定义→T6/T7（propagate 实现任务首条冻结项） | unified B1 / DS-09 |
| UF-07 | 工况 | sensitivity 工况 flow_case：曾未定义（DS-10 三缺口之一） | 已定义→contracts/condition.py 规格 R1（sensitivity 统一 design 档；求值细则 manifest.py R1c；T0FIX 已修） | unified A6 |
| UF-08 | 引擎 | 引擎技术参数落点：loop 阻尼/容差、LRU 512 条/512MB 等无合规去处——assumptions 要求规范出处（给不出）vs 代码字面量撞魔法数字门禁 | 已定义→RunEnv.engine_params（T4 D3 冻结，commit：97ae1f9）：以带调节影响元数据的引擎默认条目入 engine_params 字段（run_env.py R2/app 装配 T7）；数值 T7 executor 实现期冻结，禁散落代码字面量（GR-15）。**已实现·T7a（2026-08-25）**：类型面 contracts/run_env.py——EngineParam（value/source/note，GR-15 出处门槛）+engine_params 字段（commit 4fa8359）；数值面 registry/assumptions loop.* 三条条目——tolerance=1e-10/max_iterations=200/damping=0.8，source/note/tuning_impact 俱全、工程惯例类出处（commit c254292）；app 装配从 DEFAULT_ASSUMPTIONS 提取 loop.* 三键投影 EngineParam 归 T7b（run_env 规格 R2 投影口径已注记）；LRU 512 条/512MB 缓存参数不在本批（缓存属 incremental 优化层，随其实现任务冻结）。**投影闭环·T7b（2026-08-25，app 装配批 commit 374be2b 后续笔）**：app.run_full_calc 对缺 loop.* 任一键的 env 经私有 _engine_params 从合成视图（DEFAULT_ASSUMPTIONS+design.assumption_overrides）补齐——value=合成值、source/note=registry 条目原文（GR-15 出处随行）；纯函数构造新 RunEnv 替换原 env 不改 | unified B5 / GLM-01 |
| UF-09 | 契约 | 温度字段位置：契约链无温度字段（AAO Kd 修正/消化 35℃ 需要），放 WaterQuality 还是 RunEnv 未定 | 待定义→T3（冻结 result_schema 时拍板） | unified C4 / DS-24 |
| UF-10 | 数据版本 | data_version 聚合算法：coefficients/constraint_kb/prices 多包版本如何聚成单一 data_version（max？拼接哈希？）未定义 | 已定义→T4 D3 冻结（commit：97ae1f9）：聚合算法=包名排序后 `name@version` 以 `+` 拼接（确定性、可读、审计友好；任一包版本或包集变化→聚合串变化）；app 装配层 T7 生成；coefficients 单包 data_version 照旧。ARCH1 D4 聚合口径定稿（2026-08-24，双源不一消解——run_env/app 规格"系数+单价聚合"为准）：**包集={coefficients, unit_prices} 两包**、name=目录实名（unit_prices 非 prices）；constraint_kb 不进聚合（其装载属 UF-12 待定义，消费走 solution/constraints）；templates 不进（静态资源，无版本聚合语义）；run_env.py 与 app.py 规格头已同步两包实名 | unified D / DS-23 |
| UF-11 | 污泥线 | 内回流 Ri 归属：business-logic §6 表/ports.py/包内部端口 vs SCC 迭代三处矛盾 | 待定义→M2 前拍板 | unified C2 / DS-17 |
| UF-12 | 图谱 | 图谱缺边 elevation→registry、network→registry；constraint_kb 装载路径未定义 | 待定义→M2 前（先改图谱 §1 再动代码，AGENTS §13） | unified C1 / DS-02 |
| UF-13 | 门禁 | server 层无 import-linter/行数门禁（core 有、server 无，边界随 M2 增重） | 待定义→M2 前 | unified C3 / DS-14 |
| UF-14 | 测试 | 覆盖率口径：零语句骨架不进分母已澄清；分阶段阈值与否未决策 | 待定义→T12 决策（写入 pyproject/CI 注释） | unified B2 |
| UF-15 | 文档 | 规格头修订流程：曾为"记录备查"，修订无强制步骤（实现者顺手改规格迁就实现） | 已定义→GR-35（DS-18 升格） | unified D / DS-18 |

## 二、系统清查新增项（sweep，UF-16~UF-30）

> 清查方法：按 conventions 十章逐章问"本项目哪个文件/场景会踩这条但规格没写"，
> 对每个候选 grep 既有规格头与 docs 验证"确实沉默"（命令摘要见文末）；
> 不确定项标 **疑似**，待总控复审。简报预期方向中两项（SSE 断线重连、
> 增量==全量口径）经验证**已被既有规格覆盖**，未收录（见报告说明）。

| 编号 | 领域 | 未定义特性（验证依据） | 处置 | 归属 |
|------|------|------------------------|------|------|
| UF-16 | 导出 | Excel 模板占位符约定：calcbook.py R3 只写"占位符语法 `{{field_id}}` 类"——精确语法、重复占位符、模板有占位符但字段未登记时的语义未写；excel_io.py R1"列位映射"同样无格式定义；data/templates 尚为空槽（0.0.0） | **部分已定义→M1b（2026-08-25）**：calcbook 占位符精确语法冻结 `{{trace[i].<field>}}`/`{{trace[i].inputs.<symbol>}}`/`{{summary.<key>}}`（summary 平键=点式扁平 f"{condition_key}.{字段ID}"），未知占位符=InvalidTemplateError；模板夹具测试内自造不经 data/，正式模板待 data/templates 录入批（excel_io 列位映射仍待定义） | 本批 sweep；M1b 回写 |
| UF-17 | 警告 | Warning 数据结构：unit_api.py 只写 `tuple[Warning, ...]`，全库无 Warning 类字段定义；business-logic §8 只定级别与必带信息，结构形态（severity/来源键/参数键/影响面字段集）未写 | 已定义→contracts/unit_api.py Warning/Severity（T3 冻结，简报 D3：Severity=ERROR/WARN/INFO 字面量冻结；Warning frozen 六字段 severity/source/message/param_key/condition_key/affected_unit_ids——§8"来源+调节方向+影响面"三必带逐条落字段，param_key/condition_key 可 None=error 级可无调节指向；result_schema.UnitResultSnapshot 直接复用同层 import） | 本批 sweep |
| UF-18 | 警告 | 警告跨工况×单元去重聚合：同一警告在 2+k 工况重复出现，UI 汇总/去重规则无规格（grep "去重" 仅 diagnose 冲突集一处） | 待定义→T3/前端展示层 | 本批 sweep |
| UF-19 | 水质 | 缺项指标进入下游 compute：quality.py 只定义"缺项不参与混合并记警告"；下游单元公式**需要**该指标时（如 AAO 需 BOD5 而进水缺项）异常还是跳过，无规格 | 待定义→T6/T7（propagate 派生规则同期，必要时单元 manifest 声明必需指标集） | 本批 sweep |
| UF-20 | 单位 | pint 单位别名集：quantity.py 未定义接受写法（`m3/d` vs `m³/d` 上标、大小写）；pint 默认接受面 vs 项目白名单未拍板，边界实现者自定 | 已定义→T1 冻结白名单（ACCEPTED_INPUT_UNITS 十量类显式写法集，白名单外一律拒、pint 永不接触未审字符串；规格头新增【单位别名白名单】节；已锁定（SENS 批 S2 落盘，用户总授权），当期证据=实现报告负例命令） | 本批 sweep |
| UF-21 | 前端 | i18n 键命名：dimensions.py 只写 `i18n_key: str`，键格式（前缀/分隔符/命名空间）无约定；webapp 尚无 i18n 体系（grep 无 i18n_key 消费点） | 待定义→前端 i18n 层落地任务 | 本批 sweep |
| UF-22 | 参数 | ParamSpec 范围端点语义：manifest.py 只写"范围（可选，约束层消费）"，闭/开区间未写——实现者可自创开区间误拒端点合法方案 | 已定义→GR-06（默认闭区间，开区间显式声明） | 本批 sweep |
| UF-23 | 汇流 | 汇流 ΣQi=0 的除零：propagate.py 负荷加权 ΣCi·Qi/ΣQi，权重全零时 0/0 处置未写 | 已定义→GR-02（运算产生 NaN=compute 内转领域异常上抛） | 本批 sweep |
| UF-24 | 参数 | 输入物理合理性带归属：flow.py R3 只对 Kz 言明"行业上下限属 constraint_kb 数据"；其余量（q_avg_daily 无上限、浓度上限等）的合理性带归属与数据载体未写 | 待定义→constraint_kb 数据录入工作包（A8 类；契约只守数学不变量的 Kz 模式推广） | 本批 sweep |
| UF-25 | 错误处理 | 用户可见文本语言策略：异常/警告消息中文单语已成事实（expr.py 等既有实现），但"中文单语 vs 走 i18n 键"未拍板；一旦多语言化与 GR-09 冻结规则的相容方式需定 | **疑似**——领域专家/总控待拍板（先按中文单语现状执行，GR-09/GR-20 冻结规则先行） | 本批 sweep |
| UF-26 | 任务系统 | server 重启任务恢复：manager.py R4 只写"注册表在内存、replicas=1"，重启后 queued/running 任务与任务历史的恢复语义（丢失是否接受、是否持久化）未写 | **疑似**——待拍板（v1 单实例假设下倾向"重启即丢、前端重提交"，需明示） | 本批 sweep |
| UF-27 | 序列化 | view 态时间戳格式：project_schema.py 只写 ViewState 含时间戳，格式（UTC？ISO？本地字符串）未写——本地时间字符串跨机排序错序 | 已定义→GR-19（UTC ISO 8601，禁本地时间字符串） | 本批 sweep |
| UF-28 | 可观测 | 进度事件 percent 口径：worker.py R3 只写"阶段百分比+逐工况粒度"，跨阶段/跨工况的总 percent 加权口径（工况数均分？单元数加权？）未写，实现者随手定 | **疑似**——待定义（T4 server 实现时冻结，需与 events.py R4 背压丢弃语义对账） | 本批 sweep |
| UF-29 | 单元包 | 单元包导出契约：AGENTS §11 说"只暴露 manifest 与 compute 两个名字"，_template/compute.py 固定形态却要 `make_unit` 工厂由包 `__init__` 导出——白名单到底几名未冻结 | 待定义→M1 期间（首个单元包实现前拍板） | unified B6 / GLM-03（本批 sweep 复核确认仍开放） |
| UF-30 | 工具链 | mypy strict 覆盖单元包内测试无豁免：首个包内测试（tests/ 目录）即触发（core pyproject 的 strict 范围未区分 src/tests） | 待定义→M1 期间（首个单元包落地时定豁免或全严格） | unified B7 / GLM-02（本批 sweep 复核确认仍开放） |

## 三、预期方向中未收录的验证结论（防重复登记）

| 候选 | 验证结论 |
|------|----------|
| SSE 断线重连语义 | **已定义**：events.py R3"事件不重放历史（连接即当前），状态查询走 tasks 端点"+R2 断线清理——不登记 |
| 增量计算与全量等价的验证口径 | **已定义**：AGENTS §6 与 incremental.py R1（字节级、hypothesis 随机编辑序列常驻）——不登记 |
| 多工况并行度无关性 | **已定义**：executor.py R1（工况间零共享可变状态）+ collector.py R2（固定迹序）+ R3 双跑字节级——不登记 |

## 四、sweep 验证方法（命令摘要，Windows Git Bash）

```bash
# 全部在仓库根执行；"0 命中/仅既有单点"= 规格确实沉默
grep -rn "占位符" core/waterprint --include="*.py"      # 仅 calcbook R3（"类"字样留口）
grep -rn "class Warning" core/waterprint -r               # 0 命中（无结构定义）
grep -rn "去重" core/waterprint --include="*.py"          # 仅 diagnose 冲突集
grep -rn "缺项" core/waterprint --include="*.py"          # 仅 quality.py（混合跳过）
grep -rn "别名\|³" core/waterprint/contracts/quantity.py  # 0 命中
grep -rln "i18n_key" webapp/src                            # 0 命中
grep -rn "闭区间\|端点\|inclusive" core/waterprint -r      # 0 命中（ParamSpec 范围闭/开端点语义未写，后立 GR-06）
grep -rn "行业上下限" core/waterprint --include="*.py"     # 仅 flow.py R3（Kz 单点）
grep -rn "重启\|restart" server/waterprint_server -r       # 0 命中
grep -rn "percent" server/waterprint_server/jobs/*.py      # 仅"阶段百分比"粒度，无加权口径
grep -n "时间戳" core/waterprint/contracts/project_schema.py  # 只写含时间戳，无格式
grep -n "Σ\|除零\|sum.*==.*0\|权重为零" core/waterprint/graph/propagate.py  # 仅 R3 守恒/Σ 行，无 ΣQi=0 处置 → UF-23
```

> 新增登记项同样须走上述验证；处置变更（待定义→已定义）在冻结任务的 commit
> 中回写本表并引用任务号。

## 五、ARCHDEBT 架构审查新增项（2026-08-23；UF-31/33/34 已裁决落盘 SENS-B 2026-08-23，UF-32 待定义）

> 来源：`.workflow/reports/task-ARCHDEBT-impl-report.md`（架构布局本征复杂度
> 审查）。四项均为"实现开始后必然撞墙"的结构性沉默，已 grep 验证（见文末）。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-31 | 分层 | RunEnv 类型归属：graph/executor.py(L3) 与 solution/enumerate.py(L3) 公开签名均引用 `env: RunEnv`，而该类型声明于 app.py(L4)【公开接口】——L3 实现要 import L4 即违反 layers 契约（import-linter 必拦）；类型下沉 contracts(L0)、executor 改收窄参数、还是 TYPE_CHECKING 类逃生口，规格均未写（TYPE_CHECKING 是否算违规 import 亦沉默） | 已定义→contracts/run_env.py：RunEnv 下沉 L0（app 装配并重新导出；engine_params 承接 UF-08 引擎参数条目，T4/T7 冻结数值）；executor/enumerate/app 规格头来源注记同步（SENS-B 2026-08-23） | ARCHDEBT |
| UF-32 | 总线 | 跨 L3 数据流的契约载体：ElevationProfile 定义于 elevation/profile.py(L3)，而 drafting 的 `__init__`/profile_drawing.py/section_view.py(L3) 规格头明文以其为输入（"标高唯一真源"）；independence 契约禁 L3 互 import、§1b drafting 仅→contracts，contracts 目录无此类型、result_schema 规格头亦无 Profile 条目——M2/M4 出图实现无合法取数路径。SceneGraph/EstimateSheet 同为子系统自有类型（仅 app ResultBundle 聚合），总线序列化形态同样未定 | **疑似**→待定义（T3 result_schema 冻结扩展时拍板，或 M2 前专项） | ARCHDEBT |
| UF-33 | 图谱 | server→core 依赖边缺位：调用链 §2 与规格头声明 services/projects→project/io、services/enumeration→solution/\*、services/exports→trace/calcbook+drafting、worker R2 kind 映射直连 solution/各渲染器；§1b 边表仅声明 services→app、jobs→app——按现规格实现即产生 §1b 之外的 import（违反 AGENTS §13"真实 import ⊆ 声明边"）。当前 check_module_graph 不校验"§2 链路步骤 ⊆ §1b 边表"、真实 import 扫描是 B3 待办，门禁暂不拦 | 已定义→方案 A：app.py 用例面收口（新增 run_enumeration/export_artifact/load_project+save_project 三用例），structure-graph §2 四链 server 段终点改经 app，worker R2 kind 映射与 services 三规格头调用对象表述同步，§1b 边表零新增（SENS-B 2026-08-23） | ARCHDEBT |
| UF-34 | 分层 | L0 契约层准入标准：L0 现混合四类内容——数据 schema（flow/quality/sludge/project_schema/result_schema）、协议（ports/unit_api/trace_api）、声明 schema+DSL 文法（manifest/condition）、可执行引擎（expr.py，全库唯一真实现 331 行）与量纲真源（quantity）；"什么允许进 L0"无规格——任何"多下层都要用"的共享物都有理由下沉 L0，commons 温床风险（每文件单独看都合理，累积即成垃圾抽屉层） | 已定义→GR-36（conventions §11：L0 准入三类判据——冻结 schema/跨层协议/≥2 非 L4 层共消费的 DSL 内核或量纲真源，禁 I/O 与可变状态，file-contracts 行注明类别；run_env.py 行已按类②登记）（SENS-B 2026-08-23） | ARCHDEBT |

### 五项验证命令摘要（仓库根执行，2026-08-23）

```bash
# UF-31：类型声明在 L4、引用在 L3；docs 仅 UF-08/09/10 涉 RunEnv（均未涉类型家）
grep -rn "RunEnv" core/waterprint          # app.py:11（声明）/executor.py:14-15、enumerate.py:12（引用）
grep -rn "RunEnv" docs                     # 仅 undefined-features-register UF-08/09/10
grep -rn "TYPE_CHECKING" docs core/pyproject.toml AGENTS.md   # 0 命中（逃生口未定义）

# UF-32：drafting 侧明文引用 ElevationProfile，contracts 零命中
grep -rn "ElevationProfile" core/waterprint   # drafting/__init__.py、profile_drawing.py、
                                              # section_view.py 引用；contracts/ 0 命中
grep -n "Profile\|Scene\|Estimate" core/waterprint/contracts/result_schema.py  # 0 命中

# UF-33：§2 调用链 vs §1b 边表（§1b 的 services/jobs 行仅 jobs/settings/app 三向）
sed -n '96,106p' docs/structure-graph.md   # §2 枚举/导出链直达 solution/trace/drafting
grep -n "| \`waterprint_server.services\` |" docs/structure-graph.md
grep -n "| \`waterprint_server.jobs\` |" docs/structure-graph.md

# UF-34：全 docs 无 L0 准入判据（"准入"仅 conventions 新条目准入一义）
grep -rn "准入" docs/ AGENTS.md            # 无 L0 语境命中
```

## 六、ARCHDEBT 动态运行时补充审查新增项（2026-08-23 第二轮；UF-35~38 已裁决落盘 SENS-B 2026-08-23）

> 背景：静态门禁合规 ≠ 动态运转正确。第二轮针对**运行时行为**（并行执行、
> 数值运行期警告、并发时序、产物落盘与留存）系统清查；来源：
> `.workflow/reports/task-ARCHDEBT-impl-report.md` §8。
> 注意与 §三"多工况并行度无关性（已定义不登记）"的区分：该条覆盖
> **工况间**，本批 UF-35 指同工况内**拓扑层内**并行，互不重叠。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-35 | 执行 | 层内并行的语义与等价性：executor.py R2"逐层（可并行）执行"、topo.py"同层可并行"——"可并行"是**许可**还是**要求**未定；若许可，"并行执行与串行执行字节级相同"无任何测试要求（"双跑 diff=0"只保证同模式双跑，并行路径带完成序累积 bug 时可同模式侥幸双绿）；若 v1 实为串行，规格也未写"并行是预留、v1 串行" | 已定义→executor.py R2 措辞裁决：逐层执行（v1 串行；并行预留——上线前提=并串字节级等价常驻测试先行入锁）（SENS-B 2026-08-23）。**v1 串行裁决落地·T7b（commit 720ddee，2026-08-25）**：executor 层-SCC 调度逐层串行执行（同层组先于单点——次序推演记档规格头 R2）；并行预留上线前提不变 | ARCHDEBT |
| UF-36 | 数值 | numpy 运行期警告/errstate 载体：GR-02 已定义 NaN/±Inf 政策（运算产生=转领域异常），但向量化 compute 的**执行载体**未写——`np.errstate(raise=...)` 上下文、算后 `isfinite` 守卫、`where=` 分母保护三种选择运行时行为不同（numpy 默认只发 warning 且值继续传播，恰是 GR-02 要禁的静默路径）；另 GR-02"禁 NaN 参与"与 enumerate.py R5"NaN 显式标注列放行"的相容口径（GR-02 管量/守恒路径、enumerate 管表格列？）未写 | 已定义→GR-37（conventions §11：compute 数值路径局部 np.errstate 承接、isfinite 仅二道网；GR-02 与 enumerate 结果表 NaN 标注列口径分界）；enumerate.py R5 已补引用（SENS-B 2026-08-23） | ARCHDEBT |
| UF-37 | 并发 | stale 判定时序与幂等并发窗口：calculation.py R1"完成时对比当前 hash"与 calc.py R1"完成后标 stale"是**完成时一次性标记**，exports.py R1 却是**消费时实时比对**——同一 stale 概念两种判定时机并存，标记后 design 再变则 calc 侧响应带过期 fresh 标志；"对比→标记/写入"check-then-act 窗口与 apply_solution 并发交错无规格（单进程 asyncio 假定下需写明"同一事件循环临界区"之类的保证）；幂等键并发双提交的查重窗口同样未写 | 已定义→守门一律消费时实时比对（exports.py R1 统一口径）；calculation"完成时对比"降级为 UI 提示性标记（不作守门依据）；幂等查重与 stale 标记须在同一事件循环临界区内完成（单进程 asyncio 契约）——calculation.py R1/calc.py R1/exports.py R1 三规格头已加注（SENS-B 2026-08-23） | ARCHDEBT |
| UF-38 | 落盘 | 非项目文件的落盘原子性与产物留存：原子写目前只有 project/io.py R4（临时文件+rename 同分区）一处先例；导出产物（dxf/xlsx/计算书）与枚举 arrow 结果文件的写入原子性未写（幂等重导出"覆盖校验"未说覆盖是否原子，半截产物文件可被消费）；已完成产物（arrow/exports）的**留存/清理策略**未写（磁盘无界增长，取消清理只覆盖临时产物） | 已定义→GR-38（conventions §11：一切落盘产物临时文件+同分区 rename 原子落盘，推广 io.py R4；留存上限与清理策略属 settings 配置，T4 冻结数值）；worker.py R3/exports.py R2 已补引用（SENS-B 2026-08-23） | ARCHDEBT |

### 六批验证命令摘要（仓库根执行，2026-08-23）

```bash
# UF-35："并行"全部出现点无一处要求并串等价或声明 v1 串行
grep -rn "并行" core/waterprint docs/*.md AGENTS.md   # topo.py:12/executor.py:21（仅"可并行"）/
                                                      # register §三（工况间，另一维度）
# UF-36：运行期数值警告载体 0 命中
grep -rni "errstate\|RuntimeWarning\|seterr" core/waterprint docs scripts AGENTS.md  # 0 命中

# UF-37：stale 两种判定时机并存；无锁/临界区字样
grep -rn "stale\|幂等" server/waterprint_server --include="*.py"
    # calculation.py:21（完成时对比）/calc.py:25（完成后标记）vs exports.py:16（消费时比对）
grep -rni "锁\|lock\|临界" server/waterprint_server    # 0 命中（io.py"锁探测"在 core 侧）

# UF-38：原子写仅 io.py 先例；留存策略 0 命中（"清理"仅断线客户端与取消临时产物）
grep -rn "原子" core/waterprint server/waterprint_server docs/file-contracts.md
grep -rn "保留\|清理\|retention" server/waterprint_server core/waterprint docs/file-contracts.md
```

## 七、T2 起草期新增项（2026-08-23，疑似待总控复审→随 T2 冻结半壁）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-39 | 数据装载 | 出水标准库装载机制：quality.py 规格仅一句"STANDARDS 数据驱动加载自 data/coefficients，构造时注入"——加载者（quality 自读 YAML？registry 注入？）、注入形态、与 GR-36"L0 禁 I/O"的调和均未写；data/coefficients 0.1.0 无标准条目（README 规划六文件亦无标准文件），镜像测试不触碰 STANDARDS（工厂内联构造 EffluentStandard） | **疑似**→T2 只交付类型+margin+守卫（STANDARDS 整体挂起）；装载机制待定义→数据工作包同期（A8 类）或 T4，落点须过 GR-36（L0 禁 I/O→倾向 registry(L1) 加载后注入） | T2 起草 |

### 七批验证命令摘要（仓库根执行，2026-08-23）

```bash
# quality 规格仅一句且未写加载者；data 包无标准文件；register 无既有条目
grep -n "coefficients\|STANDARDS" core/waterprint/contracts/quality.py   # quality 落地后 3 行命中（接口行/规格头挂起注记/UF-39 引用，行号随实现漂移）
ls data/coefficients/                                                    # 无 standards 文件
grep -rn "18918\|一级A\|出水标准" data/ docs/norms/                    # 仅 README 规划句与 manifest 槽位注释
grep -n "标准库\|STANDARDS" docs/undefined-features-register.md          # 本条前零命中
```

## 八、交接体检批新增项（2026-08-24，T4 起点体检发现——疑似待裁决）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-40 | 时间/序列化 | GR-19 时区口径三源不一：engineering-conventions.md:213"统一 UTC + ISO 8601（含 Z）" vs project_schema.py:25-26 规格头正文"非空必须 UTC ISO 8601" vs 同文件 :50-51 冻结注记"tz 必在"；实现 `_timestamp_utc_iso`（:97-115）取最宽口径——任意偏移时区（+08:00 等）均通过。自由发挥风险：io/migration 若按"含 Z 严格版"实现将与 project_schema 现行为互斥（旧版时区格式判别、序列化口径分裂） | **已定义→零偏移严格版**（用户批准 roadmap 2026-08-24：时间戳非空必须零偏移 UTC——Z 或 +00:00 才通过；GR-19:213 原文即真源；锁定测试未触此路径已核）。**已实现·T7a commit a94d9ad（2026-08-25）**：`_timestamp_utc_iso` 增第三守卫 utcoffset()!=timedelta(0) 拒（Z 与 +00:00 过、+08:00/naive 拒，消息含原值+实得偏移 GR-09），规格头正文/冻结注记同步零偏移口径；探针⑤消息实证（Z/+00:00 过、+08:00/naive 拒） | REG9 2026-08-24 |
| UF-41 | CLI/管网 | cli.py v1 冻结子命令集（calc/export/new-unit/validate/selfcheck，:12-22）无管网子命令，而 structure-graph.md §1b:63 声明 cli→network 边（"管网子工具命令"）、§2:105 链 6 首环即"cli.py（独立命令）"——两侧规格不对齐。自由发挥风险：M3 实现管网时加子命令=擅破 v1 冻结集，不加=§1b 边永为孤边 | **疑似**→二选一：cli 冻结集扩管网子命令（升 v2）或链 6 改独立入口不经 cli；M3 前拍板 | 交接体检 2026-08-24 |
| UF-42 | 结果投影 | UnitResult→UnitResultSnapshot 投影规则规格沉默：UnitResult.outflows 为 Mapping[PortRef→WaterFlow\|SludgeFlow]（unit_api），UnitResultSnapshot.outflows 为 Mapping[str→float]（result_schema:135/137）——PortRef→str 键化格式、WaterFlow（含 q_avg_daily/kz/q_design 三量）→单 float 的字段选择或多槽、kz/q_design 是否随行、dims Any→Mapping[str,float]，均无规格。自由发挥风险：executor（T6/T7）落快照时各自发明投影，serialize 确定性与 golden 对照将锁死错误口径 | 已定义→T7b D3 投影表冻结（2026-08-25）。**已实现·T7b（commit 720ddee，2026-08-25）**：executor._snapshot 落地——键化格式 f"{unit_id}.{port_id}.{量}"（GR-09 展示形态同款）；WaterFlow 三键槽 q_avg_daily/kz/q_design（三量全随行，q_design 派生量同报）、SludgeFlow 三键槽 q_wet/ds/moisture；outqualities 指标键全逐项；dims str→float 逐项有限性校验（非该形状/非有限=InvalidExecutionError 带 unit_id，GR-02）；warnings/formula_ids 透传；不动 result_schema（487/500 拆分预案挂账不变） | 交接体检 2026-08-24 |
| UF-43 | 计算书 | 计算书链三处规格沉默：① TraceNodeSpec 五字段 vs TraceNode 六字段（多 norm_ref）——反查补齐路径无规格；② collector 规格头 record() 为 6 散参（M0 遗留）vs trace_api 单对象协议；③ TraceTree 类型全库未定义——树 vs 平铺未裁决 | **已定义→M1b 实现（2026-08-25，简报 D1 三合一）**：① formulas.norm_ref_of(formula_id) 只读查询面新增、collector 反查落 TraceNode.norm_ref；② collector 规格头刷新为 record(node: TraceNodeSpec) 单对象（T0.5 协议对齐）；③ TraceTree=tuple[TraceNode, ...] 平铺+到达序（树形聚合归渲染层 calcbook/audit 自行分组）——三处均已实现闭合 | 交接体检 2026-08-24；M1b 回写 |
| UF-44 | 测试锁定 | test_dimensions.py 模块级 skipif（:17-20）把 dtype_of 列入就绪门，而 dtype_of 规格明定落 T4（dimensions.py 规格头"本注记即唯一占位形态"）→ 整模块 4 用例自 T3④ 起永久 skip，dimensions 已实现行为（R2 单位校验/R3 重复拒/未登记拒）零有效测试覆盖；测试锁定与规格分期矛盾 | 已定义→已消解（T4⑤ 落地 dtype_of，commit：dde483c）：skipif 门四符号（FieldSpec/register_dimension/dimension_of/dtype_of）齐备自然激活，4 用例 skip→pass 实证（test_dimensions 全绿）；dtype_of 语义按 T4 D5 冻结（结构化 dtype/逐槽 <f8/字段序=输入序/三拒） | T4 简报必办 |

### 八批验证命令摘要（仓库根执行，2026-08-24）

```bash
# UF-40：三源原文与实现口径
grep -n -A2 "GR-19" docs/engineering-conventions.md            # :213"统一 UTC + ISO 8601（含 Z）"
grep -n "UTC" core/waterprint/contracts/project_schema.py       # :25-26 正文 vs :50-51 注记 vs :97-115 实现（tzinfo 非 None 即过）
# UF-41：cli 冻结集无管网；§1b/§2 声明有
grep -n "wp \|子命令集" core/waterprint/cli.py                   # calc/export/new-unit/validate/selfcheck 五命令
grep -n "network" docs/structure-graph.md                       # :63 边声明 + :105 链 6 首环
# UF-42：投影规则零规格（两侧字段声明均存在，无投影表）
grep -n "outflows\|dims" core/waterprint/contracts/unit_api.py core/waterprint/contracts/result_schema.py
# UF-43：三处沉默（签名漂移/反查路径/类型未定义）
grep -n "record" core/waterprint/trace/collector.py core/waterprint/contracts/trace_api.py
grep -rn "TraceTree" core/waterprint --include="*.py"           # 仅引用无定义
# UF-44：skipif 门与规格分期冲突
sed -n '14,22p' core/tests/registry/test_dimensions.py          # dtype_of 在 skipif 元组内
grep -n "dtype_of" core/waterprint/registry/dimensions.py       # 仅规格头注记（T4 占位形态）
```

## 九、ARCH1 真源批新增项（2026-08-24；UF-45 备案即冻结）

> 来源：`.workflow/briefs/task-ARCH1-brief.md` D6(g)——异常命名族谱的
> 历史豁免备案（非待定义项：符号已冻结，本条为备案使其有档可查）。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-45 | 错误处理 | ExprSyntaxError 命名豁免 GR-11 Invalid* 族：GR-11（conventions §2）确立领域异常一律 Invalid* 族命名，而 contracts/expr.py 的 ExprSyntaxError 为 T0.5 冻结符号+锁定测试锁定（改名 = 破坏可复算与既有 import 面）；豁免无档可查则后续复审可能误判违例 | 已定义→豁免备案（ARCH1 D6(g)，2026-08-24）：ExprSyntaxError 为 GR-11 Invalid* 族唯一历史豁免（T0.5 冻结符号，锁定测试锁定，改名破坏可复算）；**后续新增领域异常一律 Invalid* 族命名**，不再产生新豁免 | ARCH1 真源批 |

## 十、M1b 回写注记（2026-08-25）

- **D10 记档消除**：executor R4"PlantResult.trace=()/summary={} 占位与计算迹
  完整性的冲突"——app.run_full_calc 已装配 TraceCollector 并回填实迹
  （trace 非空、平铺到达序、双跑同序列化）；summary={} 仍为 M1 数值批
  待填（executor.py 零改动，其规格头 D10 注记文字保留作历史档）。
- **UF-43①②③**：均已实现闭合（见上表处置列）。
- **UF-16**：calcbook 占位符语法已冻结；正式模板待 data/templates 录入批。
