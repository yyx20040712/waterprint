# 警告聚合规格（UF-18——PlantWarning 跨工况×影响面去重聚合）

> 本件=**规格先行**（1A8 收官批 2026-10-05 落盘）：1A2~1A4 警告码全集
> 已稳定（input_band/mass_balance/param_band 三族 kind——条目实数以
> `GET /api/constraints` 现库为准，数据包版本以
> `data/constraint_kb/manifest.yaml` 为准），route 1A8 行前置条件达成；
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
消歧——建议形态 `scope`（影响面）+`condition_keys[]`（命中工况键
清单，§3）；**禁 `condition_key` 双义入 API**。本节对 2A1 批有
约束力。

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
  聚合行按**首例**展示（首现序——`ValidationReport.codes()` 去重
  保序首现序的码面单源先例，聚合键为其三元推广）。
- `severity` 不入键：聚合行分级见 §3。

## 3. 跨工况聚合语义

聚合行形态=**去重键（§2）+命中工况键清单+severity 分级**：

- **命中工况键清单**：该去重键命中的工况键序列，按 ConditionSet
  迭代序（确定性——工况间零共享可变状态 executor R1 同源，序不随
  执行方式变）。
- **severity 分级取最严重**：聚合行 severity=max over 命中实例
  （ERROR>WARN>INFO）。现状警告码族 severity 全为 WARN、
  enforcement=flag（实数以 `GET /api/constraints` 现库为准）。
  **前向兼容条款（预留不实现）**：P1 断路器批后，任一命中工况
  block 即聚合行 block——分级函数语义本件先行冻结，行为面归 P1 批。
- **单工况实例=明细展开态**：聚合视图不吞明细——明细面=PlantWarning
  实例流原样，聚合行可展开回实例。
- **入聚合视图判据**：≥2 工况命中才入「聚合视图」；单工况命中直通
  行（UF-18 原文「2+k 工况重复」语义——去重价值面恰在重复）。

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

- 1A2~1A4 警告码全集已稳定：input_band/mass_balance/param_band 三族
  kind（条目实数与 severity/enforcement 分布以 `GET /api/constraints`
  现库为准——本件全文零写死计数，08 §6 易失数字纪律）。
- 接线批=2A1（server API 消费扩展面）+T3（前端展示层）；§1 命名
  硬约束（scope+condition_keys[] 形，禁 condition_key 双义入 API）
  对 2A1 批生效。
- 断路器分级行为面归 P1 后续批（§3 前向兼容条款预留）。
- UF 登记：`undefined-features-register.md` UF-18 行随本件落盘闭合
  （本件=其规格载体）。
