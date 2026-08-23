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
| UF-03 | 数值语义 | Q=0 与负值语义：负值拒绝已有散点（quality R2），Q=0 是否合法、与厂界 flow.py R2（q>0）的口径分界未写 | 已定义→GR-04（厂界仍按 flow.py R2，分界说明见该条绑定）→待定义 T6/T7 propagate 冻结时正式定稿厂界口径（总控 2026-08-23 已认可 GR-04 分界） | conventions §1 |
| UF-04 | 确定性 | set 迭代序：`sorted()` 与中文键 locale 陷阱无规格（跨进程/CI 双跑字节差且不可复现） | 已定义→GR-16 | conventions §4 |
| UF-05 | 错误处理 | 异常消息稳定性：消息可否随重构改写未定义（改写=跨版本计算迹 diff 全线飘红） | 已定义→GR-09 | conventions §2 |
| UF-06 | 汇流 | 汇流派生规则：q_avg_total=Σ、Kz_total=max、q_design 派生与两档加权一致性，propagate 规格只写 R1/R2 语义未列派生式，实现 mix() 前须冻结 | 待定义→T6/T7（propagate 实现任务首条冻结项） | unified B1 / DS-09 |
| UF-07 | 工况 | sensitivity 工况 flow_case：曾未定义（DS-10 三缺口之一） | 已定义→contracts/condition.py 规格 R1（sensitivity 统一 design 档；求值细则 manifest.py R1c；T0FIX 已修） | unified A6 |
| UF-08 | 引擎 | 引擎技术参数落点：loop 阻尼/容差、LRU 512 条/512MB 等无合规去处——assumptions 要求规范出处（给不出）vs 代码字面量撞魔法数字门禁 | 待定义→T4/T7（RunEnv/实现任务定落点） | unified B5 / GLM-01 |
| UF-09 | 契约 | 温度字段位置：契约链无温度字段（AAO Kd 修正/消化 35℃ 需要），放 WaterQuality 还是 RunEnv 未定 | 待定义→T3（冻结 result_schema 时拍板） | unified C4 / DS-24 |
| UF-10 | 数据版本 | data_version 聚合算法：coefficients/constraint_kb/prices 多包版本如何聚成单一 data_version（max？拼接哈希？）未定义 | 待定义→T4（RunEnv 实现时冻结） | unified D / DS-23 |
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
| UF-16 | 导出 | Excel 模板占位符约定：calcbook.py R3 只写"占位符语法 `{{field_id}}` 类"——精确语法、重复占位符、模板有占位符但字段未登记时的语义未写；excel_io.py R1"列位映射"同样无格式定义；data/templates 尚为空槽（0.0.0） | 待定义→随模板录入/计算书实现任务冻结（A8 类数据工作包同期） | 本批 sweep |
| UF-17 | 警告 | Warning 数据结构：unit_api.py 只写 `tuple[Warning, ...]`，全库无 Warning 类字段定义；business-logic §8 只定级别与必带信息，结构形态（severity/来源键/参数键/影响面字段集）未写 | 待定义→T3（result_schema/UnitResultSnapshot 冻结时） | 本批 sweep |
| UF-18 | 警告 | 警告跨工况×单元去重聚合：同一警告在 2+k 工况重复出现，UI 汇总/去重规则无规格（grep "去重" 仅 diagnose 冲突集一处） | 待定义→T3/前端展示层 | 本批 sweep |
| UF-19 | 水质 | 缺项指标进入下游 compute：quality.py 只定义"缺项不参与混合并记警告"；下游单元公式**需要**该指标时（如 AAO 需 BOD5 而进水缺项）异常还是跳过，无规格 | 待定义→T6/T7（propagate 派生规则同期，必要时单元 manifest 声明必需指标集） | 本批 sweep |
| UF-20 | 单位 | pint 单位别名集：quantity.py 未定义接受写法（`m3/d` vs `m³/d` 上标、大小写）；pint 默认接受面 vs 项目白名单未拍板，边界实现者自定 | 待定义→quantity 实现任务冻结白名单并测试锁定 | 本批 sweep |
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
grep -rn "闭区间\|端点\|inclusive" core/waterprint -r      # 0 命中
grep -rn "行业上下限" core/waterprint --include="*.py"     # 仅 flow.py R3（Kz 单点）
grep -rn "重启\|restart" server/waterprint_server -r       # 0 命中
grep -rn "percent" server/waterprint_server/jobs/*.py      # 仅"阶段百分比"粒度，无加权口径
grep -n "时间戳" core/waterprint/contracts/project_schema.py  # 只写含时间戳，无格式
grep -n "Σ\|除零\|sum.*==.*0\|权重为零" core/waterprint/graph/propagate.py  # 仅 R3 守恒/Σ 行，无 ΣQi=0 处置 → UF-23
```

> 新增登记项同样须走上述验证；处置变更（待定义→已定义）在冻结任务的 commit
> 中回写本表并引用任务号。
