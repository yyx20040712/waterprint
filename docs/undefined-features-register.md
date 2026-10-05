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
>
> **追认台账位置说明（R1-6 2026-08-26）**：集中追认台账在仓库外
> 会话工作区（`.workflow/pending-domain-expert.md`，gitignore 明示
> 不入库——克隆者不可达）；本表各行'pending 追认/待追认'字样即
> in-repo 追认标记（UF-32 行=对照表整体+量纲列——已追认 2026-08-28 RATIFY2 扩批、UF-50 行=DXF v1
> 基准面裁量），units_lib manifest'待追认'注记同理——台账丢失时
> 以本表+注记为审计锚点。

## 一、种子项（总控拍板收录，UF-01~UF-15）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-01 | 数值语义 | 浮点断言容差无基准：测试该用 approx 还是绝对相等、容差多少，各规格头未写，实现者随手拍 | 已定义→GR-01 | conventions §1 |
| UF-02 | 数值语义 | NaN/±Inf 处置：规格头只列异常类型，0/0、溢出产生的 NaN 如何拦截未写（会静默流进出水裕度） | 已定义→GR-02 | conventions §1 |
| UF-03 | 数值语义 | Q=0 与负值语义：负值拒绝已有散点（quality R2），Q=0 是否合法、与厂界 flow.py R2（q>0）的口径分界未写 | 已定义→GR-04（厂界仍按 flow.py R2，分界说明见该条绑定；厂界口径随 T6/T7 propagate 冻结时定稿——总控 2026-08-23 已认可 GR-04 分界） | conventions §1 |
| UF-04 | 确定性 | set 迭代序：`sorted()` 与中文键 locale 陷阱无规格（跨进程/CI 双跑字节差且不可复现） | 已定义→GR-16 | conventions §4 |
| UF-05 | 错误处理 | 异常消息稳定性：消息可否随重构改写未定义（改写=跨版本计算迹 diff 全线飘红） | 已定义→GR-09 | conventions §2 |
| UF-06 | 汇流 | 汇流派生规则：q_avg_total=Σ、Kz_total=max、q_design 派生与两档加权一致性，propagate 规格只写 R1/R2 语义未列派生式，实现 mix() 前须冻结 | 已定义→business-logic §6a 汇流派生式冻结（批6k 2026-09-29 定版——propagated 实现已然，规格文字追认实现基线 graph/propagate.py T6 冻结面）：q_avg_total=Σq_avg_daily（求和序 GR-18）、Kz_total=max（保守）、q_design_total=q_avg_total×Kz_total（派生属性双轨根除口径同构）、水质两档加权（DESIGN→q_design/AVG→q_avg_daily，负荷加权非浓度平均）、直构造不经 make_flow（图内 Q=0 合法 GR-04）、SLUDGE 股 DS 守恒独立通道 | unified B1 / DS-09 → 批6k 闭项 |
| UF-07 | 工况 | sensitivity 工况 flow_case：曾未定义（DS-10 三缺口之一） | 已定义→contracts/condition.py 规格 R1（sensitivity 统一 design 档；求值细则 manifest.py R1c；T0FIX 已修） | unified A6 |
| UF-08 | 引擎 | 引擎技术参数落点：loop 阻尼/容差、LRU 512 条/512MB 等无合规去处——assumptions 要求规范出处（给不出）vs 代码字面量撞魔法数字门禁 | 已定义→RunEnv.engine_params（T4 D3 冻结，commit：97ae1f9）：以带调节影响元数据的引擎默认条目入 engine_params 字段（run_env.py R2/app 装配 T7）；数值 T7 executor 实现期冻结，禁散落代码字面量（GR-15）。**已实现·T7a（2026-08-25）**：类型面 contracts/run_env.py——EngineParam（value/source/note，GR-15 出处门槛）+engine_params 字段（commit 4fa8359）；数值面 registry/assumptions loop.* 三条条目——tolerance=1e-10/max_iterations=200/damping=0.8，source/note/tuning_impact 俱全、工程惯例类出处（commit c254292）；app 装配从 DEFAULT_ASSUMPTIONS 提取 loop.* 三键投影 EngineParam 归 T7b（run_env 规格 R2 投影口径已注记）；LRU 512 条/512MB 缓存参数不在本批（缓存属 incremental 优化层，随其实现任务冻结）。**投影闭环·T7b（2026-08-25，app 装配批 commit 374be2b 后续笔）**：app.run_full_calc 对缺 loop.* 任一键的 env 经私有 _engine_params 从合成视图（DEFAULT_ASSUMPTIONS+design.assumption_overrides）补齐——value=合成值、source/note=registry 条目原文（GR-15 出处随行）；纯函数构造新 RunEnv 替换原 env 不改 | unified B5 |
| UF-09 | 契约 | 温度字段位置：契约链无温度字段（AAO Kd 修正/消化 35℃ 需要），放 WaterQuality 还是 RunEnv 未定 | 已定义→单元参数承载定版：契约链不设温度字段（批6k 2026-09-29 设计裁量——WaterQuality/RunEnv 均否）：①温度是工艺分段量（消化 35℃ 中温档 vs 生物池常温）全局单值错误归一；②WaterQuality=浓度指标族，温度非浓度混入破坏 mix 负荷加权语义；③RunEnv.engine_params=引擎技术参数语义（GR-15 出处门槛）非工艺温度；④现行实现已用单元参数+系数带承载（xiaohua t_digest_temp range 33~37 中温档、hebing Kd₂₀/θ 修正带——有出处有执法面，定版=事实追认非新增语义）。季节温度工况（全局温度场）=新 UF 另立。xiaohua 四源文件+README+norms 表注记七处同批勘误 | unified C4 / DS-24 → 批6k 闭项 |
| UF-10 | 数据版本 | data_version 聚合算法：coefficients/constraint_kb/prices 多包版本如何聚成单一 data_version（max？拼接哈希？）未定义 | 已定义→T4 D3 冻结（commit：97ae1f9）：聚合算法=包名排序后 `name@version` 以 `+` 拼接（确定性、可读、审计友好；任一包版本或包集变化→聚合串变化）；app 装配层 T7 生成；coefficients 单包 data_version 照旧。ARCH1 D4 聚合口径定稿（2026-08-24，双源不一消解——run_env/app 规格"系数+单价聚合"为准）：**包集={coefficients, unit_prices} 两包**、name=目录实名（unit_prices 非 prices）；constraint_kb 不进聚合（装载路径定版见 UF-12 批6k——恰两面装载消费走 solution/constraints；不进聚合真由=约束面不进复算三元组）；templates 不进（静态资源，无版本聚合语义）；run_env.py 与 app.py 规格头已同步两包实名 | unified D / DS-23 |
| UF-11 | 污泥线 | 内回流 Ri 归属：business-logic §6 表/ports.py/包内部端口 vs SCC 迭代三处矛盾 | 已定义→包内部参数定版（批6k 2026-09-29 勘误归一——以包内实现为正基准）：Ri=AAO/CASS manifest 可枚举自由参数 r_internal（range 1.0~3.0 手册带+params_guard face④ 执法），AO-F14 内回流泵流量=包内平均时口径计算，全仓无 recycle 自边——**不进图迭代**（图级 recycle 边仅污泥外回流 R 与滤液/上清液回流两族）。勘误两处：business-logic §6 表 Ri 行迭代归属列（旧「SCC 回路组」系与实现矛盾记载）+contracts/ports.py R3 注释（旧举 Ri 为图边例证）；§2 耦合参数归属表 Ri 行（manifest 归属）正确保持 | unified C2 / DS-17 → 批6k 闭项 |
| UF-12 | 图谱 | 图谱缺边 elevation→registry、network→registry；constraint_kb 装载路径未定义 | 已定义→缺边补登确证+kb 装载路径定版（批6k 2026-09-29）：①两缺边已先后补登 structure-graph §1b（elevation→registry=ENG2 B3、network→registry=NET2——「先改图谱再动代码」纪律历史履行事实核验）；②constraint_kb 装载路径=恰两面——core：registry/effluent.py（effluent_standard 12 条，UF-39）；server：services/constraints.py（全量八键投影 ConstraintCatalog）+jobs/worker.py（枚举约束装配）；core solution/constraints.py=纯消费面不装载。kb 不进 data_version 聚合维持（约束面不进复算三元组——UF-10 行括号注记同批勘误）；定版注记落 structure-graph §1b 后 | unified C1 / DS-02 → 批6k 闭项 |
| UF-13 | 门禁 | server 层无 import-linter/行数门禁（core 有、server 无，边界随 M2 增重） | **已收口·SERVER D7（2026-08-26）**：server/pyproject [tool.importlinter] 两契约——分层（main→routers→services→jobs→settings）+UF-33 forbidden（waterprint_server→waterprint.{solution,trace,graph,units_lib,registry,project}，白名单只 app/contracts，allow_indirect_imports=true 直查口径[经 app 转发链合法，pint 契约同款]）；双根 root_packages=[waterprint_server, waterprint]（外部包子包不可作 forbidden 模块——工具链实测）；server 下 lint-imports 2 kept 0 broken+红探针（注入 waterprint.project.io→BROKEN→还原→KEPT）实录。行数门禁：四路由器 149/138/127/80≤150（规格头约束）+500 全仓预算门禁常绿。挂账：CI server job 接 lint-imports 步骤（本批 ci.yml 白名单动作限 D6 frozen——M3 前与 contract-drift 一并接线） | unified C3 / DS-14 |
| UF-14 | 测试 | 覆盖率口径：零语句骨架不进分母已澄清；分阶段阈值与否未决策 | 待定义→T12 决策（写入 pyproject/CI 注释） | unified B2 |
| UF-15 | 文档 | 规格头修订流程：曾为"记录备查"，修订无强制步骤（实现者顺手改规格迁就实现） | 已定义→GR-35（DS-18 升格） | unified D / DS-18 |

## 二、系统清查新增项（sweep，UF-16~UF-30、UF-55）

> 清查方法：按 conventions 十章逐章问"本项目哪个文件/场景会踩这条但规格没写"，
> 对每个候选 grep 既有规格头与 docs 验证"确实沉默"（命令摘要见文末）；
> 不确定项标 **疑似**，待总控复审。简报预期方向中两项（SSE 断线重连、
> 增量==全量口径）经验证**已被既有规格覆盖**，未收录（见报告说明）。

| 编号 | 领域 | 未定义特性（验证依据） | 处置 | 归属 |
|------|------|------------------------|------|------|
| UF-16 | 导出 | Excel 模板占位符约定：calcbook.py R3 只写"占位符语法 `{{field_id}}` 类"——精确语法、重复占位符、模板有占位符但字段未登记时的语义未写；excel_io.py R1"列位映射"同样无格式定义；data/templates 尚为空槽（0.0.0） | **部分已定义→M1b（2026-08-25）**：calcbook 占位符精确语法冻结 `{{trace[i].<field>}}`/`{{trace[i].inputs.<symbol>}}`/`{{summary.<key>}}`（summary 平键=点式扁平 f"{condition_key}.{字段ID}"），未知占位符=InvalidTemplateError；模板夹具测试内自造不经 data/，正式模板待 data/templates 录入批（excel_io 列位映射仍待定义）；**正式模板已录入（DRAFT 批 2026-08-26）**：data/templates 1.0.0（calcbook_unit/calcbook_plant 双模板零公式）+TEMPLATE_REGISTRY 扩两键+渲染端到端零残留（summary 面真值依赖 plant.summary——executor 空注入现状归 D10）；**D10 落地（2026-08-28）**：summary 真值经 app 层 run_full_calc `_summary_of` 纯投影注入（executor.py 零改动——trace/design_hash 回填同款 replace 先例），golden e2e replace workaround 移除+正式 calcbook_plant 模板渲染断言入库（六占位符零残留+值==expected 1e-12——平键集复核完成零变更） | 本批 sweep；M1b 回写；DRAFT 批回写；D10 批回写 |
| UF-17 | 警告 | Warning 数据结构：unit_api.py 只写 `tuple[Warning, ...]`，全库无 Warning 类字段定义；business-logic §8 只定级别与必带信息，结构形态（severity/来源键/参数键/影响面字段集）未写 | 已定义→contracts/unit_api.py Warning/Severity（T3 冻结，简报 D3：Severity=ERROR/WARN/INFO 字面量冻结；Warning frozen 六字段 severity/source/message/param_key/condition_key/affected_unit_ids——§8"来源+调节方向+影响面"三必带逐条落字段，param_key/condition_key 可 None=error 级可无调节指向；result_schema.UnitResultSnapshot 直接复用同层 import） | 本批 sweep |
| UF-18 | 警告 | 警告跨工况×单元去重聚合：同一警告在 2+k 工况重复出现，UI 汇总/去重规则无规格（grep "去重" 仅 diagnose 冲突集一处） | 已定义（1A8 批 2026-10-05——聚合规格落盘 docs/warning-aggregation.md〔去重键=code+param_key+影响面三元组/服务端聚合单一口径/命名消歧硬约束〕；**2A1 批 2026-10-05 server 消费面已接**：GET /api/calc/validation/{project_id} 聚合端点落地〔services/validation.py 两源聚合——规格十条款逐条绑定；worker calc-val 第三并列 artifact=源 A 数据源〕；T3 FE 聚合行展示层待） | 本批 sweep → 1A8 批闭项 |
| UF-19 | 水质 | 缺项指标进入下游 compute：quality.py 只定义"缺项不参与混合并记警告"；下游单元公式**需要**该指标时（如 AAO 需 BOD5 而进水缺项）异常还是跳过，无规格 | 已定义→缺项三层语义定版（批6k 2026-09-29——推荐案=已有实现确认）：①mix 汇流层：部分股缺项→在场股加权（全股缺项→结果缺项；在场权合计==0→缺项 GR-14）；②零依赖面（removal 修饰类）：缺项键不经修饰、出流保持缺项透传；③公式依赖面（计算前提指标）：进水缺项→InvalidUnitConfig 领域异常 fail-loud（GR-09，AAO AO-F1/F4 BOD5/TN 前提断言实现事实）——不跳过不默认 0。manifest 声明必需指标集=未来扩面另立（v1=compute 内断言）。规格正文=business-logic §6a | 本批 sweep → 批6k 闭项 |
| UF-20 | 单位 | pint 单位别名集：quantity.py 未定义接受写法（`m3/d` vs `m³/d` 上标、大小写）；pint 默认接受面 vs 项目白名单未拍板，边界实现者自定 | 已定义→T1 冻结白名单（ACCEPTED_INPUT_UNITS 十量类显式写法集，白名单外一律拒、pint 永不接触未审字符串；规格头新增【单位别名白名单】节；已锁定（SENS 批 S2 落盘，用户总授权），当期证据=实现报告负例命令） | 本批 sweep |
| UF-21 | 前端 | i18n 键命名：dimensions.py 只写 `i18n_key: str`，键格式（前缀/分隔符/命名空间）无约定；webapp 尚无 i18n 体系（grep 无 i18n_key 消费点） | 已定义→显式不做（滞后闭项·文档维护批 2026-09-30）：UF-25 批6h 已定版全仓中文单语、不引入 i18n 键层——本行"待定义"面被其整体覆盖（i18n 体系不建=键命名约定无消费场景）；dimensions.py `i18n_key` 字段维持声明、仓内无语义消费点（2026-09-30 全仓 grep 复证：命中=声明面〔registry/dimensions+32 包 manifest+graph builtin 造值〕、contracts 非空校验与测试镜像；agent knowledge 工具输出面显式剔除该键——无查找/显示消费；历史字段面，多语言翻案=独立勘误批，UF-25 同款条款） | 本批 sweep → UF-25 覆盖闭项 |
| UF-22 | 参数 | ParamSpec 范围端点语义：manifest.py 只写"范围（可选，约束层消费）"，闭/开区间未写——实现者可自创开区间误拒端点合法方案 | 已定义→GR-06（默认闭区间，开区间显式声明） | 本批 sweep |
| UF-23 | 汇流 | 汇流 ΣQi=0 的除零：propagate.py 负荷加权 ΣCi·Qi/ΣQi，权重全零时 0/0 处置未写 | 已定义→GR-02（运算产生 NaN=compute 内转领域异常上抛） | 本批 sweep |
| UF-24 | 参数 | 输入物理合理性带归属：flow.py R3 只对 Kz 言明"行业上下限属 constraint_kb 数据"；其余量（q_avg_daily 无上限、浓度上限等）的合理性带归属与数据载体未写 | 已定义→带归属声明表定版（批6k 2026-09-29——Kz 模式推广全量化）：契约只守数学不变量（正性/有限性/派生一致性）；行业合理性带=数据面（constraint_kb 条目或 manifest range，出处纪律+追认制）。闭项范围=**归属模式与载体定版**（每量唯一归属+执法面声明——挂账两处〔Kz 未录/水质上限带未录〕=数据值录入工作包承接非闭项阻断，闭项判据=归属声明表可判定新量落点）；六量声明表落 data/constraint_kb/README.md「输入合理性带归属声明」节：Kz（kb 规划位无来源未录挂账）/q_avg_daily 厂界带（params_guard builtin A-1~A-3 已落地）/单元参数 94 条（manifest range 已落地）/几何四量（kb geometry_guard 已落地）/枚举可行带（kb 存量已追认）/水质浓度（契约数学不变量在册+行业上限带数据面挂账） | 本批 sweep → 批6k 闭项 |
| UF-25 | 错误处理 | 用户可见文本语言策略：异常/警告消息中文单语已成事实（expr.py 等既有实现），但"中文单语 vs 走 i18n 键"未拍板；一旦多语言化与 GR-09 冻结规则的相容方式需定 | **显式不做 i18n**：中文单语定版（批6h 2026-09-27 闭项——预授权③主控推荐案〔用户 2026-09-26「全部安排上」全局规划指令〕；异常/警告/界面文案全仓中文单语不引入 i18n 键层，GR-09 消息稳定性/GR-20 冻结规则继续先行；用户翻案=独立勘误批） | 本批 sweep → 批6h 闭项 |
| UF-26 | 任务系统 | server 重启任务恢复：manager.py R4 只写"注册表在内存、replicas=1"，重启后 queued/running 任务与任务历史的恢复语义（丢失是否接受、是否持久化）未写 | 已定义→显式 v1 语义（批6f 2026-09-26 闭项——实装面回写；本行旧前提「只在内存」系 sweep 时点陈述，S2/ENG5 落盘化后失真）：单实例（api replicas=1）四条明示：①终态任务记录落盘（registry_dir 四时机原子写：submit 初档 queued/_pump running 迁移/_finish 终态/cancel·shutdown 的 queued 终态）重启恢复供读；②queued/running 非终态重启**不续跑**——恢复记录经 iter_restorable 变换为 failed（error_type=InterruptedByRestart，error_code=None 诚实——生命周期事件不入领域码表）可查不丢痕；③幂等表不恢复（ENG5 D5——重提交=新任务）；④前端对失效任务 id 重提交即新任务（TaskPanel statusError 指引文案在案）。deployment.md「单进程契约」节重启语义注记同口径；多副本=未来 Redis 化（ADR 不做）。 | 本批 sweep；批6f 闭项 |
| UF-27 | 序列化 | view 态时间戳格式：project_schema.py 只写 ViewState 含时间戳，格式（UTC？ISO？本地字符串）未写——本地时间字符串跨机排序错序 | 已定义→GR-19（UTC ISO 8601，禁本地时间字符串） | 本批 sweep |
| UF-28 | 可观测 | 进度事件 percent 口径：worker.py R3 只写"阶段百分比+逐工况粒度"，跨阶段/跨工况的总 percent 加权口径（工况数均分？单元数加权？）未写，实现者随手定 | **已冻结·SERVER（2026-08-26）**：percent=(index+1)/(total+1) 阶段幂商式（阶段表 _STAGES 为分母基；ADR-009 白名单字面量）——工况级加权口径挂起（core run 单调用无逐工况回调钩子，与 UF-49 协作钩子缺位同批）；events 背压丢旧保新语义已对账（manager._emit：进度满即弃最旧，state/stale 不丢） | 本批 sweep |
| UF-29 | 单元包 | 单元包导出契约：AGENTS §11 说"只暴露 manifest 与 compute 两个名字"，_template/compute.py 固定形态却要 `make_unit` 工厂由包 `__init__` 导出——白名单到底几名未冻结 | 已定义→双层口径定版（滞后闭项·文档维护批 2026-09-30）：①包 `__init__` 对外导出**三名** `UNIT_ID`/`make_unit`/`manifest`（AGENTS §11 现行文——M3a2 终裁 yI-1 2026-08-28 已收口；本行问题域引文「manifest 与 compute」系 sweep 时点更早旧文，宪法无残留待勘误）；②注册发现消费面白名单 `{manifest, make_unit}` **两名**（units_lib/__init__.py `discover_units`——`_register` 启动守卫四查：部分导出（消费面缺名）/manifest 非 UnitManifest/make_unit 不可调用/重复 unit_id 均 RuntimeError fail-loud），32 包全量按此实施（T7b D6 同源铁律） | unified B6 → 实现已冻结；2026-09-30 滞后闭项 |
| UF-30 | 工具链 | mypy strict 覆盖单元包内测试无豁免：首个包内测试（tests/ 目录）即触发（core pyproject 的 strict 范围未区分 src/tests） | 待定义→M1 期间（首个单元包落地时定豁免或全严格） | unified B7（本批 sweep 复核确认仍开放） |
| UF-55 | 参数 | 泥量输入参数量级合理性无规模相对校核面：绝对带不可辩护（超大型厂初沉干泥可达 2×10⁵ kg/d 量级——绝对上限会误伤），量级合理性=规模相对（ds_primary vs 全厂 SS 负荷互校），hebing 单元内无入流 SS 浓度/全厂 SS 负荷上下文（q_avg_daily 衔接参数虽有——互校基准面缺；随机数值测试 S2-40：sludge_hebing.ds_primary≈1.96e5 荒谬量级静默通过、零警告） | 已定义→1A3 批闭合（2026-10-04）：plant 级质量规模互校落地——constraint_kb 1.9.0 增 kind=mass_balance 条目 `sludge.primary_load_band`（对子=ds_primary vs 全厂进水 SS 负荷〔SS×q_avg_daily 换算 kg/d〕仅此一对，ds_bio/ds_chem 不入互校〔高溶解性 BOD5 废水可合法远超 SS 负荷〕；双侧带 0.2~1.0——上界=GB 50014-2021 §6.5 η<1 守恒包络/下界=η 下端 0.4×上游格栅/沉砂削减宽放 0.5；severity=WARN/enforcement=flag 仪表灯〔block 断路器归 P1 后续批〕）+core `app_validation` mass_balance 分支接线（kind 直判选条，违规产 `kb.sludge.primary_load_band` 警告码不阻断；缺任一面或零基准跳检=无进水声明/缺 SS 或 q_avg_daily/入流直值模式无 ds_primary 键/ss_load≤0 比值无定义——回炉 B1）；多泥量声明节点图形态仅校插入序首个（_inlet_values 同款口径）——多 hebing 图逐节点互校归后续批挂账；S2-40 形态自此触发警告码（复现型 ×100→ratio≈37.3 落带外）；条目起草待追认（1A3 批——P10 追认流程后续批消化） | fuzz-findings-2026-09-29 FZ-2 / FZ-1FZ-2 批 2026-09-30 / 1A3 批 2026-10-04 闭合 |

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

## 五、ARCHDEBT 架构审查新增项（2026-08-23；UF-31/33/34 已裁决落盘 SENS-B 2026-08-23，UF-32 已定义闭项——头注滞后勘误 2026-09-30）

> 来源：`.workflow/reports/task-ARCHDEBT-impl-report.md`（架构布局本征复杂度
> 审查）。四项均为"实现开始后必然撞墙"的结构性沉默，已 grep 验证（见文末）。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-31 | 分层 | RunEnv 类型归属：graph/executor.py(L3) 与 solution/enumerate.py(L3) 公开签名均引用 `env: RunEnv`，而该类型声明于 app.py(L4)【公开接口】——L3 实现要 import L4 即违反 layers 契约（import-linter 必拦）；类型下沉 contracts(L0)、executor 改收窄参数、还是 TYPE_CHECKING 类逃生口，规格均未写（TYPE_CHECKING 是否算违规 import 亦沉默） | 已定义→contracts/run_env.py：RunEnv 下沉 L0（app 装配并重新导出；engine_params 承接 UF-08 引擎参数条目，T4/T7 冻结数值）；executor/enumerate/app 规格头来源注记同步（SENS-B 2026-08-23） | ARCHDEBT |
| UF-32 | 总线 | 跨 L3 数据流的契约载体：ElevationProfile 定义于 elevation/profile.py(L3)，而 drafting 的 `__init__`/profile_drawing.py/section_view.py(L3) 规格头明文以其为输入（"标高唯一真源"）；independence 契约禁 L3 互 import、§1b drafting 仅→contracts，contracts 目录无此类型、result_schema 规格头亦无 Profile 条目——M2/M4 出图实现无合法取数路径。SceneGraph/EstimateSheet 同为子系统自有类型（仅 app ResultBundle 聚合），总线序列化形态同样未定 | 已定义→Ruling ① 方案②轻量几何取数契约（DRAFT 批 2026-08-26 落地）：①ElevationProfile/ProfileStation 类型迁 contracts/drawing_projection.py（L0——elevation 与 drafting 共同消费，L3 互不 import 解法；elevation 包内经 contracts 引用）；②13 单元 PROJECTION_TABLE 冻结取数对照（plan/section/primitive/counts 四类+non_drawn 显式列+dim_of 量纲列，249 键实跑对账——tests/contracts/test_drawing_projection.py 40 用例守卫）；③SceneGraph/EstimateSheet 维持子系统自有类型（app ResultBundle 聚合口径不变——方案②不并总线）；对照表整体+量纲列已追认（13 市政=MIGRATE-RATIFY D 项；夜间 19 单元扩行=RATIFY2 2026-08-28）；**M3D1 扩矿井 8 单元（2026-08-27 夜，已追认 2026-08-28 RATIFY2）**：drawing_projection.py 拆为 types/municipal/mine 三分线文件+聚合正门（消费方零改动），PROJECTION_TABLE 21 单元[市政 13+矿井 8]356 键，65 用例守卫（含分线 disjoint 新断言）；**M3D2 扩污泥 7 单元（2026-08-27 夜，已追认 2026-08-28 RATIFY2）**：分线表③ drawing_projection_sludge.py（SLUDGE_PROJECTIONS 7 条目，112 键——衔接链键六量 q_in/ds_in/p_in/q_out/ds_out/p_out 全线 non_drawn 总控预裁）+聚合正门扩 **SLUDGE_PROJECTIONS 分量（PROJECTION_TABLE 28 单元[13+8+7]468 键），86 用例守卫（disjoint 扩三线两两+并集）+scene _INSTANCE_KINDS 增 machine 语义标签（tuoshui 脱水机台数）**；**M3 ① 战役 32/32 全覆盖（M3D1~M3D3，2026-08-27 夜，已追认 2026-08-28 RATIFY2）**：M3D3 扩输送 4 单元——分线表④ drawing_projection_conveyance.py（CONVEYANCE_PROJECTIONS 4 条目 39 键：peishuiqu 全线唯一 water_depth 语义键=h_water 且无 plan/primitive 半槽[渠长是参数，ziwai 同裁]/三井 cylinder(d,h_total) 两槽全[peishuijing 井室为体孔口为口取井室径 d_well]/穿流校核量与 instance_counts 全空[n 是分流口数非设备台数]；量纲真源=4 包 FormulaSpec 实读 35 条真量纲 _L/_A/_V/_T/_F/_VEL——与污泥线全 _D 不同）+聚合正门扩 CONVEYANCE_PROJECTIONS 分量（PROJECTION_TABLE 32 单元[13+8+7+4]507 键），99 用例守卫（disjoint 扩四线两两+并集+新增 32/32 收口断言 len==32 且四线 13+8+7+4——重写计划 §7 验收行机器锚定）+矿井/污泥两镜像并集断言随批扩四线（M-2 指引先红后扩）+conveyance 薄镜像 3 用例；重写计划 §7 验收行"全部 32 个单元包有三维组件与单体图纸模板"达成（战役收口） | ARCHDEBT |
| UF-33 | 图谱 | server→core 依赖边缺位：调用链 §2 与规格头声明 services/projects→project/io、services/enumeration→solution/\*、services/exports→trace/calcbook+drafting、worker R2 kind 映射直连 solution/各渲染器；§1b 边表仅声明 services→app、jobs→app——按现规格实现即产生 §1b 之外的 import（违反 AGENTS §13"真实 import ⊆ 声明边"）。当前 check_module_graph 不校验"§2 链路步骤 ⊆ §1b 边表"、真实 import 扫描是 B3 待办，门禁暂不拦 | 已定义→方案 A：app.py 用例面收口（新增 run_enumeration/export_artifact/load_project+save_project 三用例），structure-graph §2 四链 server 段终点改经 app，worker R2 kind 映射与 services 三规格头调用对象表述同步，§1b 边表零新增（SENS-B 2026-08-23）；**core 侧已落地（M2-SOL 2026-08-26）**：run_enumeration/export_artifact 经 waterprint.app 正门可用（类型面与上游重建伴生件=app_enumeration.py，app 再导出保持单入口——app.py 500 行预算的宪法 §2 拆分正解，structure-graph §1a 节点行+pyproject import-linter 层序登记（waterprint.app | waterprint.app_enumeration 同层并列）+§1b 边表口径（app→app_enumeration 同层边与"严格向下"规则的相抵处置）=**server 批开工前置条件**——I-4 R1 升格 2026-08-26，未登记前 server 批不得开工）；server 段调用面接线归 server 批（第 2 块）；**server 段已收口·SERVER 批（2026-08-26）**：16 文件实装全部经 app 正门（run_full_calc/run_enumeration/export_artifact/load_project/save_project/Constraint/InvalidProjectError/DEFAULT_ASSUMPTIONS/RunEnv 再导出面），D7 forbidden 契约机器强制+红探针实录 | ARCHDEBT |
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
| UF-36 | 数值 | numpy 运行期警告/errstate 载体：GR-02 已定义 NaN/±Inf 政策（运算产生=转领域异常），但向量化 compute 的**执行载体**未写——`np.errstate(raise=...)` 上下文、算后 `isfinite` 守卫、`where=` 分母保护三种选择运行时行为不同（numpy 默认只发 warning 且值继续传播，恰是 GR-02 要禁的静默路径）；另 GR-02"禁 NaN 参与"与 enumerate.py R5"NaN 显式标注列放行"的相容口径（GR-02 管量/守恒路径、enumerate 管表格列？）未写 | 已定义→GR-37（conventions §11：compute 数值路径局部 np.errstate 承接、isfinite 仅二道网；GR-02 与 enumerate 结果表 NaN 标注列口径分界）；enumerate.py R5 已补引用（SENS-B 2026-08-23）；【M2-SOL 追记 2026-08-26】enumerate.py R1 现实口径：规格头原文"向量化批量喂入"与现状不符（formulas.apply 标量强类型+13 单元标量守卫是已锁定架构）——已修订为"同一 unit.compute 逐网格行驱动（防双轨实质=唯一计算源，N=1==单点锁定断言成立）"；apply 向量化增强挂账（万级 <5s 预算探针②实测数字见 M2-SOL 实现报告）；行级域拒口径（compute 领域异常→dims 全 NaN+nan_flag=True 进表）与工况映射（13 单元全空，非空映射与网格行优先序）一并记档 | ARCHDEBT |
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
| UF-39 | 数据装载 | 出水标准库装载机制：quality.py 规格仅一句"STANDARDS 数据驱动加载自 data/coefficients，构造时注入"——加载者（quality 自读 YAML？registry 注入？）、注入形态、与 GR-36"L0 禁 I/O"的调和均未写；data/coefficients 0.1.0 无标准条目（README 规划六文件亦无标准文件），镜像测试不触碰 STANDARDS（工厂内联构造 EffluentStandard）。**消歧注记（2026-08-28）：本条=出水标准库装载；流程旧文档曾以"UF-39"指 N/P 去除建模属编号误用——N/P 建模为另一特性，M3 N/P 批开新 UF 条目承载（handover §四.2）** | **疑似**→T2 只交付类型+margin+守卫（STANDARDS 整体挂起）；装载机制待定义→数据工作包同期（A8 类）或 T4，落点须过 GR-36（L0 禁 I/O→倾向 registry(L1) 加载后注入） | **已清偿（P2 次批 2026-09-12 ADR-012 D6）**：registry/effluent.py load_effluent_standards 落地（constraint_kb effluent_standard 12 条→EffluentStandard 族，fail-fast；GR-36 调和=registry(L1) 加载后由 server worker 注入 run_full_calc standards 参——quality.py 零 I/O 纪律保持，STANDARDS 符号不进 contracts） | T2 起草→P2 次批清偿 |

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
| UF-40 | 时间/序列化 | GR-19 时区口径三源不一：engineering-conventions.md:213"统一 UTC + ISO 8601（含 Z）" vs project_schema.py:25-26 规格头正文"非空必须 UTC ISO 8601" vs 同文件 :50-51 冻结注记"tz 必在"；实现 `_timestamp_utc_iso`（:97-115）取最宽口径——任意偏移时区（+08:00 等）均通过。自由发挥风险：io/migration 若按"含 Z 严格版"实现将与 project_schema 现行为互斥（旧版时区格式判别、序列化口径分裂） | 已定义→零偏移严格版（用户批准 roadmap 2026-08-24：时间戳非空必须零偏移 UTC——Z 或 +00:00 才通过；GR-19:213 原文即真源；锁定测试未触此路径已核）。**已实现·T7a commit a94d9ad（2026-08-25）**：`_timestamp_utc_iso` 增第三守卫 utcoffset()!=timedelta(0) 拒（Z 与 +00:00 过、+08:00/naive 拒，消息含原值+实得偏移 GR-09），规格头正文/冻结注记同步零偏移口径；探针⑤消息实证（Z/+00:00 过、+08:00/naive 拒） | REG9 2026-08-24 |
| UF-41 | CLI/管网 | cli.py v1 冻结子命令集（calc/export/new-unit/validate/selfcheck，:12-22）无管网子命令，而 structure-graph.md §1b:63 声明 cli→network 边（"管网子工具命令"）、§2:105 链 6 首环即"cli.py（独立命令）"——两侧规格不对齐。自由发挥风险：M3 实现管网时加子命令=擅破 v1 冻结集，不加=§1b 边永为孤边 | **已闭合**（九裁③扩 v2+NET2 2026-08-28 落地：cli 子命令集 v2 增 network 子命令[read→design_pipes→write 结果 sheet]+结构图谱 §1b:75 边实装对齐——8d60ad6/dc525b5） | 交接体检 2026-08-24 |
| UF-42 | 结果投影 | UnitResult→UnitResultSnapshot 投影规则规格沉默：UnitResult.outflows 为 Mapping[PortRef→WaterFlow\|SludgeFlow]（unit_api），UnitResultSnapshot.outflows 为 Mapping[str→float]（result_schema:135/137）——PortRef→str 键化格式、WaterFlow（含 q_avg_daily/kz/q_design 三量）→单 float 的字段选择或多槽、kz/q_design 是否随行、dims Any→Mapping[str,float]，均无规格。自由发挥风险：executor（T6/T7）落快照时各自发明投影，serialize 确定性与 golden 对照将锁死错误口径 | 已定义→T7b D3 投影表冻结（2026-08-25）。**已实现·T7b（commit 720ddee，2026-08-25）**：executor._snapshot 落地——键化格式 f"{unit_id}.{port_id}.{量}"（GR-09 展示形态同款）；WaterFlow 三键槽 q_avg_daily/kz/q_design（三量全随行，q_design 派生量同报）、SludgeFlow 三键槽 q_wet/ds/moisture；outqualities 指标键全逐项；dims str→float 逐项有限性校验（非该形状/非有限=InvalidExecutionError 带 unit_id，GR-02）；warnings/formula_ids 透传；不动 result_schema（487/500 拆分预案挂账不变） | 交接体检 2026-08-24 |
| UF-43 | 计算书 | 计算书链三处规格沉默：① TraceNodeSpec 五字段 vs TraceNode 六字段（多 norm_ref）——反查补齐路径无规格；② collector 规格头 record() 为 6 散参（M0 遗留）vs trace_api 单对象协议；③ TraceTree 类型全库未定义——树 vs 平铺未裁决 | 已定义→M1b 实现（2026-08-25，简报 D1 三合一）：① formulas.norm_ref_of(formula_id) 只读查询面新增、collector 反查落 TraceNode.norm_ref；② collector 规格头刷新为 record(node: TraceNodeSpec) 单对象（T0.5 协议对齐）；③ TraceTree=tuple[TraceNode, ...] 平铺+到达序（树形聚合归渲染层 calcbook/audit 自行分组）——三处均已实现闭合 | 交接体检 2026-08-24；M1b 回写 |
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
  **GOLDEN R1-3 注记（2026-08-26）**：golden e2e 计算书 summary 面现用
  replace 注入（executor summary={} 现状），D10 落地批 DoD 必含改真实
  plant.summary 并移除注入。
  **D10 落地（2026-08-28）**：summary 真值已由 app 层 `_summary_of` 注入
  +e2e replace 移除（见上表 UF-16 行 D10 注记）——本节挂账收口。
- **UF-43①②③**：均已实现闭合（见上表处置列）。
- **UF-16**：calcbook 占位符语法已冻结；正式模板已录入（DRAFT 批
  2026-08-26 data/templates 1.0.0 双模板+TEMPLATE_REGISTRY）；summary
  真值已接（D10 批 2026-08-28 app 层 `_summary_of` 注入+平键集复核
  完成）——本条全链闭合。

## 十一、SERVER 批新增项（2026-08-26，M2 收口第 2 块）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-46 | 环境装配 | RunEnv 装配用例缺位：app 面无 load_run_env/build_env 用例（RunEnv 七字段装配归调用方），而 D7 forbidden 禁 server 直连 waterprint.registry（真源 Coefficients 装载在 L1）——两规相抵，server 侧装配无正门可走 | 已定义（闭合）→批6l 2026-09-29（UF-46 收口）：app 面 load_run_env(data_dir, project, *, engine_version=None) 用例正门就位（系数 registry.load_coefficients 真源+UF-10 聚合+假设覆盖合成+engine_version 覆写位〔缺省=core __version__ ADR-004，server 部署串经参传入=现行口径保持 golden 字节恒等〕）；worker._build_env CoefficientsView 协议适配器+jobs/datapack.py 整域退役删除（三符号全仓零消费 grep 实证）；flows.build_env_flow 薄壳委托=CLI/agent 零行为变化；design_map._env services 面手工装配末例同批收敛（邻域裁量——data_version 随正门含在场 unit_prices=UF-10 补全，DesignMap 产物面零可见） | SERVER 2026-08-26 |
| UF-47 | 哈希取用 | design_hash server 侧取用：calc/exports 的幂等键、快照绑定、stale 守门均需 submit 时 design 哈希，而 design_hash/dumps_design 在 waterprint.project（D7 forbidden）且 app 未再导出 | 已定义（闭合）→批6l 2026-09-29（UF-47 收口）：services/projects.design_digest B4 双胞胎退役删除（design_digest/_normalize/_ROUND_DIGITS 三符号随迁）——server 全域改经 core.design_hash（app 再导出面，P0-2 在册；D7 forbidden 由再导出面承接保持）；镜像测试 test_design_digest_mirror.py 同步删除（test_projects_site site 面改单源真值断言不缩水）；消费面五件（enumeration/joint_enumeration/calculation/project_lifecycle/exports）同批改道 | SERVER 2026-08-26 |
| UF-48 | 诊断交付 | 无解诊断交付面相抵：enumeration.py R4 写"diagnosis 端点可用"，而 calc 端点集 v1 冻结六件（A1 锁定 18 总数）无 /diagnosis 端点 | 已定义→SERVER 批：端点集冻结优先——诊断负载随 GET /api/calc/tasks/{id} 结果载荷交付（feasible_count=0 时 diagnosis 非空）；fetch_diagnosis 服务面保留（路由组装用）；专用端点归端点集变更批（升 v2 时评审） | SERVER 2026-08-26 |
| UF-49 | 取消/进度通路 | Windows spawn 下共享值通路受限（实测）：mp.Queue/Event 不能经 ProcessPoolExecutor.submit 参数传递（标准 pickle 拒）；core run 内长计算无协作取消钩子（spec R5"worker 每批迭代检查"在 run 单调用面无落点） | 已定义→SERVER 批：进度队列经池 initializer/initargs 注入 worker 模块全局（ForkingPickler 正门，实测通）；取消令牌=标记文件（cancel_dir/<task_id>.cancel，跨进程共享值的文件形态）；worker 在阶段边界与批迭代间轮询（run 内不可中断——结果落地前双检）。**挂账**：core 协作取消钩子（yield 式/回调式）归 core 后续批 | SERVER 2026-08-26 |
| UF-50 | 出图输入 | DXF 导出 v1 输入面裁量：进厂水面/地面标高是 design 态输入（profile R2 非假设），而 export_artifact('dxf') 签名无该通道——v1 以 ±0.00 相对标高基准出图（工程相对标高惯例，0/0 字面量零数值面）；管段损失同因无几何通道而空段（head_losses(())——水位恒平）；绝对标高/管段几何接线归 server 批（API 通道）与 M5 管线/布置批 | 已定义（闭合）→批6j 2026-09-29（UF-50 收口）：options 键 water_level/ground_elev 成对通道（仅 sheet=profile——批6i 案丙 DSL 先例免 design_hash 级联；带符号十进制白名单+成对闸+有限域，server 预校验+core 终闸双闸）；图面=基准平移（elev_baseline=进厂水面）+标注携绝对值+图脚高程基准注记（默认模式字节恒等——快照锚零重录实证）；_REL_DATUM core 侧退役（缺省=解析器文档化相对 ±0.00 默认）；ODA 本地手动冒烟工具落 tools/oda_smoke.py+清单（不入 CI）；挂账=server elevation API datum 输入面（M5/批6l 邻域）+单单元图剖面绝对化（图面批）+管段几何（M5） | 批6j 2026-09-29 |

### 十一批验证命令摘要（仓库根执行，2026-08-26）

```bash
# UF-46（批6l 闭合）：装配正门在 app 面，适配器/datapack.py 已退役
grep -n "def load_run_env" core/waterprint/app.py               # 1 命中（用例正门）
grep -rn "_YamlCoefficients" server/waterprint_server/          # 仅 worker.py 编年史注记（产品码 0 命中）
# UF-47（批6l 闭合）：server 全域经 core.design_hash 单源，双胞胎已退役
grep -n "def design_digest" server/waterprint_server/services/projects.py    # 0 命中
# UF-48：诊断随状态载荷交付
grep -n "diagnosis" server/waterprint_server/services/enumeration.py
# UF-49：initializer 注入+文件取消令牌
grep -n "_init_progress_queue\|cancel_token" server/waterprint_server/jobs/worker.py
```

## 十二、NP1 批新增项（2026-08-28，N/P 建模段一——数据批）

> 来源：Ruling 九裁①（N/P 建模 golden 升版授权）+explore-NP1-freeze §二
> 建模形态裁决。两段制：段一=纯数据+文档批（本批），段二=实装+golden
> 15 锚重录批（用户追认后开工）。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-51 | 水质建模 | 市政生物段 aao/cass 出流水质 NH3N/TN/TP 语义：全链 removal_refs 仅 {BOD5,CODCR,SS} 三键，N/P 进水原值穿流（golden 五工况 NH3N 26/TN 43/TP 6.5 全同值=零去除透传；aao/cass manifest 头注"NH3N/TN/TP 不建条目"+包内透传断言在案）——生物脱氮除磷的出流建模形态（去除率键族 vs 机理导出量 tn_out=tn_eff）与数值规格双沉默，实现者可自创双轨或拍数值 | 已定义（临置）→**去除率键族路线**（NP1 冻结 §二裁决：removal.{aao,cass}.{nh3n,tn,tp}.mod_default 六键，与 BOD5/COD/SS 同构，出流=入质×(1−r) 遍历机制现成；否决机理导出量——出流与进流无关弱化回溯链+与 removal_refs 机制异构双轨）。**段一数据批已落（2026-08-28，coefficients 0.8.0；六键已追认 2026-08-28 RATIFY3）**：六键数值定稿（aao NH3N 0.90/TN 0.75/TP 0.93、cass NH3N 0.90/TN 0.70/TP 0.93，带值+一级A 校核注记必附；追认前禁进 golden/禁触实装）；docs/norms/{aao,cass}.md 衔接式 N/P 三行+参数档三行同步起草。**段二已完成（NP2 2026-08-28，be2629c）**：removal_refs 扩三键+头注刷新+断言改去除+golden 15 锚重录（实跑真值）——UF-51 闭合。**类防线加固（GOV1 2026-09-12，ADR-013 D3）**：`core/tests/units_lib/test_removal_semantics.py` 通用代数不变式常驻（discover_units 全部 removal_refs 单元 `out=in×(1−r)` 参数化断言，新单元入册自动纳入——本类缺陷"声明去除而透传"即刻红）。UF-39 消歧注记在案（UF-39=出水标准库装载；流程旧文档曾以"UF-39"指 N/P 建模系编号误用，见 §七行内注记） | NP1 2026-08-28 |

### 十二批验证命令摘要（仓库根执行，2026-08-28）

```bash
# UF-51：透传现状铁证（manifest 头注+removal_refs 三键面）
grep -n "NH3N/TN/TP 不建条目" core/waterprint/units_lib/municipal/{aao,cass}/manifest.py
    # aao manifest.py:17 / cass manifest.py:20（段二刷新）
grep -n "removal_refs" core/waterprint/units_lib/municipal/{aao,cass}/manifest.py
    # aao :267 / cass :372——现仅 {BOD5,CODCR,SS} 三键（段二扩 N/P 三键）
# 六键已入库（0.8.0 起草档；golden_municipal 槽位不建）
grep -c "removal.aao.nh3n.mod_default\|removal.aao.tn.mod_default\|removal.aao.tp.mod_default\|removal.cass.nh3n.mod_default\|removal.cass.tn.mod_default\|removal.cass.tp.mod_default" data/coefficients/removal_rates.yaml   # 6
```

## 十三、IDLE-Q5 批新增项（2026-09-02，单元库浏览界面立册）

> 来源：用户 Ruling 2026-09-02 ③（前端唯一既没做也没规划的功能面——
> 闲时队列立册+设计，实现另批）。设计件
> .workflow/reports/units-browser-design.md（Q5 产出同日）。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-52 | 单元库浏览 | 前端侧栏单元库自 App 骨架期占位「待实装」：36 条单元目录（GET /api/units 豁免端点——R2-A 批1 D3 认可面）无任何浏览面——单元有哪些/参数面长什么样/端口拓扑，用户只能翻源码或 manifest；canvas D2 中文名映射挂账同悬空 | 已定义→**已实装收口**（M2 批 2026-09-03 e9a96e964 替换侧栏占位实装→C2-lib 批 2026-09-10 重制[图标行/联动光环/foot 计数条/Drawer 标题图标]→P0-3 批 2026-09-11 编辑态双入口[叶行「＋」+Drawer 主钮「添加到画布」]→C2-ALIGN/GOV5 演进——批6m 2026-09-29 验收追认闭合：**计数口径**〔36 条目=32 unit+4 builtin；四线+内置〔5 组〕分组=13/4/8/7+4；foot 计数条左=kind=unit 条数 32/右=组数 5 含内置组——C2-lib GL-01 用户裁决 2026-09-10「视觉稿形态保留」在册口径〕；**验收证据（入库持久化+判据独立 oracle）**=tools/units_browser_probe.py〔18 断言族全绿——期望值 GET /api/units 实读推导零自证常数；前置/断言摘要=同目录 units_browser_probe.md；vitest 全量/check_webapp/tsc 同批全绿，数字不内嵌本表（易失值防失真——门一处置）〕；设计件 .workflow/reports/units-browser-design.md 会话件散佚〔.workflow 不入库——增补六十九先例〕，实现真源=.workflow/briefs/task-C2-lib-plan.md+webapp/src/app/README.md 行内引文；数据零新增兑现〔useListUnitsApiUnitsGet 生成 hook 直用——防 useUnitCatalog 三胞胎〕；拖拽建图=设计明示只设计不实装，添加通道=按钮双入口〔P0-3 已落〕；canvas D2 中文名映射挂账另悬〔批6m 未触——独立挂账面〕） | IDLE-Q5 2026-09-02 → M2/C2-lib 实装 → 批6m 验收闭项 |

### 十三批验证命令摘要（仓库根执行；2026-09-29 批6m 更新——占位面退役换实装面）

```bash
# UF-52：侧栏实装在位铁证（App.tsx Sider 装配 UnitLibrary——M2 批替换占位后）
grep -n "UnitLibrary" webapp/src/app/App.tsx | head -2
    # import 装配 + <UnitLibrary focusId=… /> Sider 装配两点
# 数据面既有铁证（豁免端点+orval hook 双就位——生成 hook 直用防三胞胎）
grep -n '"/units"' server/waterprint_server/routers/units.py
grep -n "useListUnitsApiUnitsGet" webapp/src/shared/api/generated/units/units.ts | head -1
# 树组装纯函数（四线分组+过滤+叶反查——18 用例）
cd webapp && pnpm vitest run src/app/unitLibraryTree.test.ts
# 批6m 验收探针（入库版——oracle 推导+18 断言族：分组/叶行/foot/码隐藏/Drawer
# 参数端口预览/中英文搜索/内置空态/console 零错/Drawer 宽度等价）
python tools/units_browser_probe.py   # 前置=uvicorn 8000+vite dev 5173（清单 units_browser_probe.md §一）
```

## 十四、B3-b 批新增项（2026-09-19，复杂度治理批 3 第二步——webapp 收敛）

> 来源：《裁决书》方案二 2b 域色收敛条文明示「global.css `--wp-*` 轴
> 保留——SVG 不能 var() 的根因性债另立 UF，不在本批强解」。

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-53 | 域色双轴 | 四域色+中性色 CSS/JS 双轴同值并行：B3-b 后 JS 面单源=semanticColors domain_* 五键（unitGlyph 域色/流色+CanvasFlow 图例线色+pipe 两键全收编），但 SVG 属性面（stroke/fill/Three.js color）不能消费 CSS 变量 var()，global.css `--wp-water/sludge/mine/convey` 轴必须保留——同值双源无机器同步防线，改色漂移风险=R-G3 清单人工联动 | 已定义→**双轴归一收口**（批6n 2026-09-29 CSS-in-JS 注入案——二案裁量〔构建期变量抽取案因磁盘双源未消+构建链风险否决，卷宗=.workflow 会话件〕：①真源=semanticColors.ts DOMAIN_COLORS〔改色规程基准面平移〕；②global.css :root 域色四行字面量退役+providers.tsx 模块装载期 installDomainColorAxis() 注入 documentElement 四轴〔app 组合根——入口分层规则禁 main 直引 shared；--wp-water/sludge/mine/convey=实际 CSS 消费面四键——neutral 零 var() 消费方不入轴（A2-N-06 死变量纪律，门一回炉双席 W 共指处置；#595959 同值面 PortHandle NEUTRAL_BORDER=B3-b D5 独立灰阶先例维持，R-G3 人工联动 2 处不扩）〕；③CSS var() 消费面〔App 品牌渐变〕零改动经注入轴取值——注入先于首帧无闪烁；SVG/Canvas/Three 不能 var() 根因面零改动〔本就消费 JS 键〕；④机器断言三面〔门一回炉后终态——原「CSS 侧漂移防线留空」销项口径=值面+声明面+接线面〕：值面=semanticColors.test（CSS 轴四键键集冻结+逐键===domain_* 键+注入契约 stub document+缺席守卫）；CSS 声明面+接线面=app 层新件 domainColorAxis.test（global.css 全文件零域色声明复入守卫〔#hex/rgb(/hsl(/color-mix( 四形态——门一正则扩形态处置〕+注入指针在场+providers 装载期注入行为级 smoke〔stub document+动态 import——删调用/条件化即红〕）。**防线边界如实记**：全仓任意文件任意形态域色字面量复现扫描=欠账（rgb 数值字面量无键名锚点防误伤不扩）；像素级快照比对=无视觉快照基建——验收「快照不变」以同 hex→同计算值推定+浏览器探针 computed style 实证（已知限制记档）；⑤rgba 派生面〔wp-lib-hit 光环/DOMAIN_ICON_STYLES/PortHandle NEUTRAL_BORDER〕=B3-b D5/R-G3 范围外维持〔派生非同值〕，color-mix(var()) 自动联动化=候选欠账呈报不擅动） | B3-b 2026-09-19 → 批6n 双轴归一收口 2026-09-29 |

### 十四批验证命令摘要（仓库根执行，2026-09-19）

```bash
# UF-53：双轴归一后单源铁证（批6n 2026-09-29 刷新——真源=semanticColors，CSS 轴启动期注入）
grep -n "DOMAIN_CSS_VARS\|installDomainColorAxis" webapp/src/shared/ui/semanticColors.ts | head -4
grep -n "installDomainColorAxis" webapp/src/app/providers.tsx
grep -cE -- "--wp-(water|sludge|mine|convey)[[:space:]]*:[[:space:]]*(#|rgb\(|hsl\()" webapp/src/app/global.css
    # 末条=0（global.css 域色声明退役——与 domainColorAxis.test 守卫正则同构〔[[:space:]]
    # 形态+四色形态〕，再引入即守卫红）；改色单源=DOMAIN_COLORS 一处（JS 派生键+
    # CSS 注入轴两轴同步，机器断言三面钉死）
```

## 十五、批6h 新增项（2026-09-27，wave6 卫生批——AUD-W10 闭项锚）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-54 | 比选·约束语义 | constraint severity 软语义：未勾选默认态是否提供「WARN 越带注记不滤」呈现（现=未勾选即不参与过滤、勾选即硬滤全级别=CP1 用户裁决 2026-08-31「勾选=过滤」；severity 仅随行元数据）——软档呈现属产品裁决位 | 已定义·**显式不做软语义**（2026-09-28 用户裁决·relay 增补六十三：拒绝「WARN 越带注记不滤」未勾选呈现——越带几何量〔如超大单池〕属应滤除设计，工程正解=上调池数而非单池做大，注记保留无价值；CP1「勾选=过滤」勾选即硬滤全级别维持定版；kb README/solution·constraints 规格头两注记随裁同步） | audit AUD-W10 / 批5 Rulings / 增补六十三 |

## 十六、FE-2/FE-4 批新增项（2026-09-30，webapp 主包代码分割+三维首帧反馈批——门一 R0~R3b 四轮+门二实证/重证/裁决部终裁 PASS 面外挂账）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-56 | 前端·首帧门 | 三维首帧 overlay（FirstFrameGate）无超时/失败退出路径：WebGL 上下文创建失败或渲染循环未启动时 useFrame 永不触发→「正在构建三维场景…」永久遮罩且拦截点击（实现者可自选静默等待或超时降级，规格沉默） | 已定义·**已清偿（2A4 批 2026-10-05：超时降级——cell armTimeout/disarmTimeout+signal 清窗幂等〔FIRST_FRAME_TIMEOUT_MS=10s，探针基线 363~439ms×20+ 余量〕+Scene timedOut 面板替代 Canvas 块+attempt 复位重试=子树重挂天然重建 GL；ErrorBoundary 路弃=渲染循环死锁不抛可捕错误）** | FE-20260930 批 / 2A4 批 |
| UF-57 | 前端·测试债 | FirstFrameGate hook 活链路（signal→订阅→重渲染→overlay 卸载）与五结果页签领域码门控分支零自动化测试锚：仓内 vitest 无 jsdom/testing-library 环境（禁新增依赖红线），测试面=纯核闭包+SSR 等价+源文断言，行为级覆盖全靠门二无头探针 DOM 断言（探针脚本是会话件不入库——回归防线非常驻 CI 面） | 已定义·**挂账环境升级批**（FE-20260930 门一 k2-W1/d1-N1/W1 共指；门二 G2b 10/10 兜底在案；候选出路=jsdom 环境引入裁决位或探针脚本纳入 CI 可选作业——与 fuzz_kernel.py CI 化建议同族） | FE-20260930 批 |
| UF-58 | 前端·构建 | vite manualChunks "three" 子串规则组面效应：共享 chunk（http/ErrorBoundary/empty 等）react jsx 运行时并入 three chunk→index.html modulepreload 19 项含 three（1095.72 kB）/tooltip（360.94 kB）且 three 首屏实拉——「三维懒加载」语义与首屏实际传输量貌合神离（首包减半口径以主 index chunk 1769.10→777.11 计，three 首拉基线同构非本批恶化） | 已定义·**挂账 manualChunks 精化批**（FE-20260930 门二实证观察①：候选修法=匹配规则收窄至 node_modules/three 路径或 canvas 懒化独立批——vite.config 触碰需独立简报+门禁面核查） | FE-20260930 批 |
| UF-59 | 前端·文案 | raw 服务端消息残留面三处：①Scene.tsx 404 错误分支「场景加载失败：{raw message}」（SceneSourceNotFoundError 面透「项目 X 最近无完成结果集（先 POST /api/calc/run）」——R3/R3b 门控收口覆盖五结果页签未含三维视图同型面）；②drawingsPane exportsQuery/unitQuery 分支（ExportSourceNotFoundError 服务端文案「先 POST /api/exports/* 生成」）；③CheckedUnitsPanel:81 工况校核保存失败面——前端领域码门控（Scene UX1 D5/R3 同款）与服务端消息用户语言化两路线均规格沉默 | 已定义·**已清偿（2A4 批 2026-10-05：三面门控移植——Scene 404/drawings exports 领域码固定摘要+CheckedUnits toast 码表门控〔ProjectNotFound/InvalidPayload〕；unitQuery 分支实证无 no-calc 领域码面不改——narrow 中文 Error/网络 raw=I-3 口径内）** | FE-20260930 批 / 2A4 批 |
| UF-60 | 前端·显示层 | 空态视觉语义与工况标识符本地化：结果页签「项目暂无完成的计算结果」空态沿用 Typography danger 红色（语义偏"故障"而非"暂无数据"——ds 视觉复判备注）；comparePane 说明行工况键 design/avg/design_offline_* 英文标识符直出（中文名只存在于 i18n 显示层的宪法 §4 原则在工况键显示面未落） | 已定义·**已清偿（2A4 批 2026-10-05：六 no-calc 分支中性化 secondary+前缀剥离+comparePane 说明行中文先行键名括注）** | FE-20260930 批 / 2A4 批 |

## 十七、cond 批新增项（2026-10-01，检修降级映射批——市政 11 单元 condition_mappings 声明+D4 通道解锁）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-61 | 工况·检修敏感性 | 检修敏感性观测面与降级校核深度：①观测面=逐工况 dims 几何对比（offline 档单池/单格/单渠承载全流量——n−1 后单池尺寸变大），summary 指标面（effluent/power/opex/carbon）n-不变=常数去除率模型的数学性质非缺陷（golden 实证 0 键漂移）；②固定几何检修校核（*_act 带在 n−1 重算下自愈——非「检修期固定几何+升负荷」专门校核）与 offline 档 kb 几何校核面（geometry_guard 只在枚举 design 帧执法（执法面=solution apply_constraints 三调用点：app.run_design_map/app_enumeration_gates.run_enumeration/joint_enumeration.stage.evaluate_stage；run_full_calc 工况帧零 kb 约束消费——2026-10-01 grep 实测））均为后续轴；③n_active 派生参数重构（案乙）已弃——与直写案数值等价（消费面同分母），ADR-007 正典写法系写法示例非新参数强制；④conveyance 三单元引擎 offline 计算链零覆盖（缺口）——根因=不在任何 golden 图（无行为载体）；**conv-golden-20261002 收口**：首个 conveyance golden 图落地——municipal_34760_conveyance 案例三件套+行为锚（offline 分化/位串恒等/汇流分流守恒/拒检面）；引擎 offline 计算链缺口闭（缺陷即修一件：executor_assembly.forward_stocks 检修饥饿边零股承接——offline 帧 n−1 后 out_n 边饥饿原裸 KeyError 逃逸，零股守恒恢复；基线帧 GR-08 行为保留，承接钳制为 unit 级——目标单元任意缺股口在 offline 帧均承接（口级/口集合规校验=后续批挂账，门二 C3），镜像锚四用例在册（含回炉轮 1 非目标缺股对偶封边第 4 用例））；缓释=grid [2,3,4] 下限 2→offline n−1≥1 无归零面+静态 grid 执法面已锚；附记两笔小账：mine 侧基线零漂移为 summary 级（市政为位串级——不对称记档；cifenli-20261002 批已升级位串级清偿）；unmapped 拒检抽 1/8 载体（D4 逻辑单元无关——参数化留后续）；**uf61-axes-20261002 余轴收口**：三轴落 app_maintenance.py 纯投影件（run_full_calc constraints 注入+summary maint.* 开放映射槽位，result_schema 零改）——①固定几何负荷校核=maint.\<node\>.fixgeom.min=min(1−off/des) over kb 覆盖字段∩ratio 可算域（aao 检修风机台数 ×2→−1.0 实锚）；②offline kb 执法面=maint.\<node\>.kb.\<key\>=1.0/0.0（solution.apply_constraints 单行 DataFrame 求值——DSL 单源，标注不阻断〔全厂计算无行可滤〕；装载器 solution.constraints.load_kb_constraints fail-fast 三态拒；kb 面生产接线=CLI/server 装载注入**已落地**〔kbwire-20261003 接线拆件批：CLI=cli_calc.py 宽容装载（kb 文件缺失→警告+() 不注入——build_standards_flow 同款；在场→fail-fast 注入，坏档→退出码 3）/server=jobs/calc_inputs.py fail-fast 双装载注入 constraints 参（缺文件=数据装配缺陷，standards D6 同口径）；cli.py 500/500、worker.py 498/500 贴墙实录拆件三件=cli_calc/cli_common/calc_inputs，run_full_calc 缺省 ()=零行为变更（golden 零漂移复证在册）〕）；③观测面=maint.\<node\>.ratio.\<field\>=offline/design **分化键集**口径（两帧同键+design 有限非零+offline 有限+exact != 才发键——全等不发；探针实证 aao 35 键恰 4 键漂移、几何四键全等：UF-61①「n−1 后单池变大」系 conveyance q_each 形态非 aao 形态——分化键集而非全字段即此依据）；kb 汇总键已兑现（kbwire-20261003）：maint.\<node\>.kb.any_fail=1.0（任一适用条目越门）/0.0（全过），applicable 非空才发——缺省 constraints=() 运行面仍静默，「kb 未注入」诊断标记（k2-N6）=DiagnosticsReport 契约变更（trust.py+serialize_diag+server 消费面）**改写独立小批挂账**——契约变更不搭结构重构车（ADR 三步工序理由，回炉轮 1 记档②③）；**口级合规落地**（原 C3 挂账）：executor_assembly._src_port_compliant（已声明 OUT 口 ∨ 动态实例口 \<declared_out\>_\<k\> k≥2 纯整数）承接分支前置——未声明口 offline 帧=响亮 InvalidExecutionError（零股承接禁吞布线缺陷 GR-09，原静默零股吞错），基线帧/非目标单元行为位串级零变（四既有用例+镜像锚⑤⑥⑦⑧在册——八锚，C2 勘正）；golden 四案 serialize 锚随录（漂移面=恰 maint.*.ratio.* 增键、数值面零变——批档 drift-diff-report.txt 树 diff 核查；mine 零漂移断言在册） | 已定义·**接线批收口后余欠挂账**（cond 批 2026-10-01：11 单元映射落地+D4 通道解锁；cond3 批 2026-10-01：三线 11 单元映射+8 单元明示不映射落地——cifenli 并联数=n_units 分离机台数（键名非 n，KS-F1/F9 并联机队语义）本批范围=键名 n 单元、映射评估落地（cifenli-20261002 批：n_units 正典三元式+头注勘正+测试表扩展；裁决部 W1 处置兑现，cifenli 移出后三线不合格 7）；④轴 conv-golden-20261002 收口在册——offline 分化/位串恒等/守恒/拒检四锚=e2e 全断言；①②③三轴+口级合规 uf61-axes-20261002 收口在册——kb 面生产接线+kb.any_fail 汇总键 kbwire-20261003 收口在册；「kb 未注入」诊断标记 kbflag-20261003 已落地（DiagnosticsReport 增档 kb_injected: bool 必填根字段〔kb_injected=bool(constraints) 于 run_full_calc 装配——注入≠适用〕+R4a 增档容认〔旧档缺键容认 False/非 bool 拒/serialize 恒发〕+server trust/ops 两消费面投影〔诊断件降级=None 不可知，禁伪造 False〕+契约工序三件套〔openapi 重导出恰两 schema kb_injected 面+orval 重跑+tsc 清零〕）；余欠=agent 面呈现裁量——**FE 观测 UI 已落地**〔2A1 批 2026-10-05：GET /api/calc/validation/{project_id} 观测端点〔maint.* 三面投影：kb bool 语义升级/any_fail/ratio/fixgeom_min〕+trust 页检修观测卡〔features/trust 三件式扩展 maintenanceView/MaintenanceObservationView/useValidationQuery——纯观测面渲染，聚合 warnings 行渲染归 T3〕+worker calc-val 第三并列 artifact 接线〕） | cond-20261001 批 / ADR-007 |

## 十八、inlet-m3d 批新增项（2026-10-02，进水流量单位统一批——市政参数面 m³/s→m³/d 契约批）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-62 | 进水·参数面单位 | 进水流量参数面单位双源漂移（用户实测首错呈报+2026-10-02 裁决「统一为 m³/d（推荐）」）：①前端 dimLabels「流量 m³/d」标签与 core 绑定点 m³/s 构造长期貌合神离（dimLabels.ts:11 注释声称「单位符号随 core CANONICAL_UNITS 真源」但 core 规范表 R1=FLOW→"m3/s"——注释不实句留档引证，本批起标签为真、注释勘正留 FE 批）；②q_avg_daily 双线双口径（municipal_input m³/s vs mine_water KI-F1 /86400 与 hebing 34760.7 的 m³/d 面）——用户按标签输入 50000 被 A-1 硬界拒（守护 fail-loud 正确，标签说谎是根因）。本批随附两面如实记档：③golden 工程手定值 34760.7 与注册表存量机械迁移值 34760.700003 并存（3e-6 m³/d（=3 mL/d）差=旧 10 位定点舍入尾差，round(x,6) 迁移定版——两数各自成立非缺陷；门一回炉 k2-W2/d1-W3 勘正单位换算 1000× 失实引述：1e-6 m³=1 mL 非 1 L）；④agent 概览/导出 stale 门对 <v4 存量项目保守判失配（读时迁移换轴后项目档 content_hash 与结果 repro digest 异源——「宁误报不漏报」安全向；server 面 idempotency 键/快照绑定双取数均经 read_project 迁移态=一致不受扰，agent 面=文件档 stored hash 直比受扰） | 已定义→**本批统一收口**（inlet-m3d-20261002 契约批：绑定点=graph/nodes.py municipal_input 以 m³/d 构造经 make_flow→pint 单源换算（R2 禁手写 86400），内部 WaterFlow m³/s 契约不变；params_guard 三常量去换算直用 m³/d 面；v3→v4 迁移链+io/server 版本头三源同笔；golden 三案 34760.7+漂移面恰达重录+浓度面位串级零漂守卫 test_inlet_m3d_drift）。余轴挂账：①**已清偿（2A2 批 2026-10-05）**：dimLabels.ts 两处+dimLabels.test.ts 两处不实句勘正——「随 CANONICAL_UNITS 真源/镜像」改手写显示层口径+FLOW 分歧如实注记（参数面 m³/d 标签为真、内核规范 m3/s、FLOW 输出面值标签错配=UF-63 随批新登记）；②agent stale 门 legacy 项目重对齐（结果 digest 与迁移后项目档 hash 归一——后续批裁量）；③~⑨裁决部 Q5 终版（批档 adjudicator-report）——**conv-golden-20261002 处置定版**：③v3 残留 10–60 静默窗=核实不动（读路径全经迁移已锚：迁移链 golden 对 v2/v3+跳级 1.0→4.0+v4 直通+server v3 存量档读时迁移幂等键恒等锚⑥新补——projects/ 存量 ~140 件读路径静默=安全态）；④迁移器未溢出巨大有限积=终版记档不动（层职责边界低危——params_guard 守业务带）；⑤magic-numbers 白名单文件级粒度=终版记档不动（现状=文件级声明面白名单，先例注释在 check_magic_numbers.py 39–71 行）；⑥幂等键派生面补锚=落地（server test_calculation 新用例：键==calc:{id}:{read_project 迁移态 design_hash}:{sorted conditions} 全文恒等+乱序归一+异源恒不等）；⑦round6 绝对口径注=落地（migration.py _ROUND_DIGITS_M3D 注记：十进制定点绝对位数口径非相对容差，3e-6 m³/d=3 mL/d 旧尾差例在册）；⑧v2 样本对更名=落地（v2_0_to_3_0_*→v2_0_to_4_0_*——expected 实为 4.0 到达态读路径链式迁移 v2→v3→v4，命名随到达版；migration.py L4a 注记+test_migration+README 三面同步，锁面随重锁更新）；⑨parents[3] 全仓既有约定=终版降级不动；serialize 守卫项=撤项（e2e 四案实有精确断言） | inlet-m3d-20261002 批 |

## 十九、2A2 批新增项（2026-10-05，dimLabels 注释勘正批——勘正取证时发现即登记）

| 编号 | 领域 | 未定义特性（场景：规格沉默处 + 自由发挥风险） | 处置 | 归属 |
|------|------|----------------------------------------------|------|------|
| UF-63 | 前端·输出面单位 | FLOW 维度**输出面**值标签错配：aao/cass `q_air`（manifest.out_dims dim=FLOW；公式 `o2_total*f_sor/(o2_per_air*ea*86400)`——除以 86400 即 d→s，值=内核规范单位 m3/s，FormulaSpec 量纲注原文「供气量 m3/s（AO-F21/CA-F29）」）在 FE 两输出面消费点——方案表 dim 列（solutionsView.buildTableColumns L271 `unit: dimUnitOf(outField.dim)`）与工况对比矩阵指标行（CompareMatrix L94 `unit: dimUnit(metric.dim)`，行源=server compare 服务 manifest.out_dims 投影）——单位标签均随 shared/dimLabels FLOW→「m³/d」：值 m3/s×标签 m³/d=**86400× 错配**（自 GOV5 out_dims 批起存在于代码，探针/审计均未对物理量级×标签做交叉断言故未现形；2A2 批 UF-62① 勘正取证时发现）。根因=DimKey.FLOW 双显示面（参数输入面绑定点 m³/d——inlet-m3d 用户裁决；输出面值=内核规范 m3/s）而 dimLabels 单表单标签，输出面显示单位口径规格沉默 | 待定义→后续 FE 批裁量（修法三候选均涉产品裁量：①dimUnit/dimUnitOf 增输出面语境参数；②manifest.out_dims 增显示单位声明键〔声明面扩键，core 契约变更〕；③输出面按真源 m³/s 呈现〔工程惯例供气量常以 m³/min·m³/h 呈现，非自明〕——FE 零换算纪律约束下禁值面转换，仅标签面裁量；可与 T3 聚合行展示层/2B4 迁移映射合流排期） | 2A2 批 2026-10-05 |

### 十九批验证命令摘要（仓库根执行；2026-10-05）

```bash
# UF-63：FLOW 输出面值标签错配证据链（值 m3/s×标签 m³/d）
grep -n "q_air = o2_total" core/waterprint/units_lib/municipal/aao/formulas_energy.py core/waterprint/units_lib/municipal/cass/formulas_energy.py
    # 两文件同式——除以 86400（d→s），输出=规范 m3/s
grep -n "供气量 m3/s" core/waterprint/units_lib/municipal/aao/formulas_energy.py core/waterprint/units_lib/municipal/cass/formulas_energy.py
    # FormulaSpec 量纲注原文（AO-F21/CA-F29）
grep -n "q_air" core/waterprint/units_lib/municipal/aao/manifest.py core/waterprint/units_lib/municipal/cass/manifest.py | grep FLOW
    # out_dims dim=FLOW 声明（FE dim 列/compare 行的 dim 来源）
grep -rn "dimUnitOf(outField.dim)\|dimUnit(metric.dim)" webapp/src/features
    # 两输出面消费点（solutionsView/CompareMatrix）——FLOW→「m³/d」
grep -n "FLOW:" webapp/src/shared/dimLabels.ts
    # FLOW: { name: "流量", unit: "m³/d" }（参数面口径——UF-62① 注记在案）
```
