# 警告聚合规格（UF-18——PlantWarning 跨工况×影响面去重聚合）

> 本件=**规格先行**（1A8 收官批 2026-10-05 落盘）：1A2~1A4 警告码全集
> 已稳定（源 A 选条族三 kind：input_band/mass_balance/param_band——
> 条目实数以 `GET /api/constraints` 现库为准，数据包版本以
> `data/constraint_kb/manifest.yaml` 为准；源 B 键面见 §4/§6），route
> 1A8 行前置条件达成；
> **实现批接线前本件零行为面**（消费方与接线批见 §5，现状锚见 §6）。
> 契约单源：`core/waterprint/contracts/validation.py`（PlantWarning
> 五字段/ValidationReport/kb 码规则）——本件零第二口径。

## 1. 命名消歧（第一原则——硬约束）

`PlantWarning.condition_key` 字段=**影响面（scope）**，不是工况：

- 厂级影响面=常量段 `"plant"`（进水面 input_band 族+泥量互校
  mass_balance 族）；
- 单元级影响面=节点 ID（节点 ID=unit_id 全仓约定——param_band 族）；
- 单源=`core/waterprint/app_validation.py` 规格头（R4/R8）。

**工况（condition）** 是另一根轴：ConditionSet 工况键（design 档/
校核档/sensitivity 各档）——求值轴，非影响面。

历史双义如实记（消歧动因）：`contracts/unit_api.py` 的 `Warning`
（UF-17 T3 冻结六字段）同名字段 `condition_key` 语义=「所属工况键」
（工况轴）；`contracts/validation.py` 的 `PlantWarning.condition_key`
语义=影响面（scope 轴）。同名字段两处承载不同轴——规格、API、前端
文案三面行文统一用词：**「影响面 scope」**与**「工况 condition」**，
禁裸用「条件键」一词承载两义。

**API 硬约束**：server API 扩展面（2A1 批）落地聚合字段时，命名必须
消歧——字段形态**硬约束**为 `scope`（影响面）+`condition_keys[]`
（命中工况键清单，§3）；**禁 `condition_key` 双义入 API**（「建议
形态」措辞不设——本节即 2A1 批的实现契约，偏离=契约违规）。

## 2. 去重键（聚合粒度）

三元组 **`(code, param_key, scope)`** = 同一警告的稳定标识（聚合
分组键）：

| 键元 | 取值 | 单源 |
|---|---|---|
| `code` | 警告码（kb 派生码=`kb.`+constraint_key） | `kb_warning_code`/`is_kb_code`（键↔码双向可逆，contracts.validation R1——禁他处复刻码拼接） |
| `param_key` | 调节方向指向（进水字段 ID/单元参数键） | kb 条目 expression 数据驱动单源（app_validation R4/R8） |
| `scope` | 影响面（`"plant"` 或节点 ID） | app_validation 单源（§1） |

- `message` 不入键：同键实例共享同一消息模板（三要素=**实际值+
  表达式原文+条目键**——validation 契约消息纪律，禁空话禁无出处），
  聚合行按**首例**展示。**序轴唯一源=ConditionSet 迭代序**（§3）：
  首例=序轴上首个命中实例（`ValidationReport.codes()` 去重保序
  首现序的码面单源先例，聚合键为其三元推广）；两源合并（§4）同键
  双现时，源 A 实例视为**序轴前置**（声明级先于工况面）——即同键
  双源现则 message 取源 A 实例。
- `severity` 不入键：聚合行分级见 §3（同级并列取序首实例——分级值
  相同无展示差，规则仅为确定性冻结）。

## 3. 跨工况聚合语义

聚合行形态=**去重键（§2）+命中工况键清单+severity 分级**：

- **命中语义（判据绑定——聚合视图=违规聚合非全键投影）**：「命中」
  =**越门实例**。源 A（PlantWarning 流）本征仅产越门实例（越带才有
  警告）；源 B（maint 标注键族）每适用条目恒发键（1.0 通过/0.0 越门
  ——§4 差异表），**仅 0.0 越门实例计入命中**，1.0 通过实例不入
  聚合（入聚合则全通过键泛滥视图且 severity 无实例可归——d1 轻量
  审 B1 二义就此冻结）。
- **命中工况键清单**：该去重键命中（越门）实例的工况键序列，按
  ConditionSet 迭代序（确定性——工况间零共享可变状态 executor R1
  同源，序不随执行方式变）。**源 A 的工况轴口径**：源 A=声明级
  一次、与工况无关（§4）→其命中清单=**空序列 ∅（声明级哨兵——
  无工况轴可数）**，不参与「≥2 工况」计数、不与工况聚合区混排
  （展示分区=声明级区）；同键双源现时清单=源 B 工况清单（源 A
  空清单并入不产生额外工况项——声明级证据随行展示）。
- **severity 分级取最严重**：聚合行 severity=max over 命中实例
  （ERROR>WARN>INFO）。现状警告码族 severity 全为 WARN、
  enforcement=flag（实数以 `GET /api/constraints` 现库为准）。
  **前向兼容条款（预留不实现）**：P1 断路器批后，任一命中工况
  block 即聚合行 block——分级函数语义本件先行冻结，行为面归 P1 批。
- **单工况实例=明细展开态**：聚合视图不吞明细——明细面=PlantWarning
  实例流原样，聚合行可展开回实例。
- **入聚合视图判据**：**源 B 命中（越门）工况数 ≥2** 才入「工况
  聚合视图」；单工况命中与源 A（∅ 哨兵）=**直通行**——与聚合行
  **同 schema**（去重键+清单+severity），仅清单长度与来源分区决定
  视图位次（UF-18 原文「2+k 工况重复」语义——去重价值面恰在重复；
  单工况项目〔ConditionSet 仅 1 档〕天然全直通行）。

## 4. 两源对齐（覆盖面差异如实记，不造第二口径）

两个警告/标注产出源以**去重键对齐**：

- **源 A——PlantWarning 流**：`app.run_full_calc` 第四字段
  `validation`（`validation_summary_of`：声明级一次——进水声明原始面
  +design.nodes params 声明面，与工况无关的静态声明面；「server
  消费面=挂账后续批」docstring 在案）。
- **源 B——maint 标注键族**：`summary` 的 `maint.<node>.kb.<key>`
  （`maintenance_summary_of`→`_maint_face`：逐单元×逐 sensitivity
  工况，offline dims 计算值面；1.0 通过/0.0 越门+`any_fail` 汇总键）。

对齐单源：`kb.<constraint_key>`（源 B 标注键中段）↔`kb_warning_code(
constraint_key)`（源 A 警告码）——键↔码双向可逆（contracts.validation
R1），聚合消费方按去重键合并两源即得全景，**禁第二键口径**。
**源 B 实例的三元组推导链**：code=键中段逆映射（R1 同一双向可逆）；
param_key/scope=自该 constraint_key 对应 kb 条目的 expression 与
unit_kinds 单源推导——与源 A 同一推导链（§2 键元单源列），单条目
单子句单字段=一键一值唯一，推导无二义。

**第三警告面显式排除（v1 边界冻结）**：`contracts/unit_api.py` 的
`Warning`（UF-17 T3 冻结六字段——单元级计算期警告，工况轴存在）
**不入本规格 v1 聚合面**（本件消费面=源 A+源 B 两源）；其跨工况
重复面若 2A1/T3 需要消费，=本规格版本升级另批扩源，禁实现批静默
扩面。

**两源覆盖面差异表**（差异系各源求值面本征，如实记非缺陷）：

| 维度 | 源 A（PlantWarning 流） | 源 B（maint 标注键族） |
|---|---|---|
| 求值面 | 声明原始面（design.nodes params——声明什么查什么，缺项跳检不警） | 计算值面（offline dims——sensitivity 工况实际算出什么查什么） |
| 求值次数 | 声明级一次（与工况无关） | 逐 sensitivity 工况（跨工况重复的现役载体） |
| 覆盖 kind | input_band+mass_balance+param_band 三族 | kb 全 kind 受适用判据收敛（unit_id∈unit_kinds 且表达式字段⊆offline dims 且 kind≠boundary_check） |
| 产出形态 | 越带才有警告（违规报告面） | 每适用条目恒发键（1.0/0.0 标注面——通过也发） |
| 字段准入 | 进水字段映射表/params 数值在场 | `_maint_face` 字段准入收敛（与离线 dims 同名参数键合法选中在册——如 aao 的 n/h2） |

- 同一 constraint_key 可仅单源出现（仅 A 或仅 B）——键集差异按上表
  语义消费方自明，聚合面不补不裁。
- 源 B 的 `maint.<node>.kb.any_fail` 汇总键（任一适用条目越门）是
  节点级仪表灯：中段非 constraint_key、不可逆映射回 kb 条目，不进
  聚合去重键族（聚合粒度=单条目键三元组）。

## 5. 聚合层归属（单一口径）

- **server API 层聚合=单一口径**：聚合/去重逻辑只做一处——server
  API 层（响应面聚合后交付），**客户端零去重逻辑**。先例同层：
  `server/waterprint_server/services/enumeration.py` diagnose 冲突集
  （服务端聚合先例——UF-18 sweep 时点全库唯一「去重」在案处）。
- **本规格消费方**：server API 消费批（2A1 扩展面——1A2 欠账
  「server API 响应面消费 validation」在案）+前端展示层（T3）。
- core 面不新增聚合 API：PlantWarning 流/maint 键族两源现状交付，
  聚合=消费面投影（app 家族「纯投影不重算」口径同构）。

## 6. 现状锚

- 1A2~1A4 警告码全集已稳定。**「三族」口径限定=源 A 选条族**
  （input_band/mass_balance/param_band——`validation_summary_of`
  三 kind 直判选条单源）；源 B 键面=kb 全 kind 受 §4 适用判据收敛
  （geometry_guard/enumeration_filter/param_band 子集等——实数与
  severity/enforcement 分布以 `GET /api/constraints` 现库为准，本件
  全文零写死计数，08 §6 易失数字纪律）。
- 接线批=2A1（server API 消费扩展面）+T3（前端展示层）；§1 命名
  硬约束（scope+condition_keys[] 形，禁 condition_key 双义入 API）
  对 2A1 批生效。
- 断路器分级行为面归 P1 后续批（§3 前向兼容条款预留）。
- UF 登记：`undefined-features-register.md` UF-18 行随本件落盘闭合
  （本件=其规格载体）。
