# ADR-026：kb 断路器运行时执法（design 帧阻断门——P1 选项 3 落地）

- 状态：**已接受（kbblock 批落地）**（2026-10-06；授权链=用户裁决
  2026-10-03「P1=选项 3」kb 逐条声明式定级〔账本 ruling 行 runId=
  route-20261003〕→用户裁决 2026-10-04 R2「kb 起草态全量追认」+附条件②
  「运行时阻断消费接线归 P1 后续批」〔adjudication-batch-20261004.md〕→
  handover-2026-10-05-2 解锁待排期→本批兑现）
- 背景：kb（constraint_kb）消费面双轨——枚举面有行可滤（kb=筛选器语义
  完备），全厂面（run_full_calc）单方案求解无行可滤，自 uf61-axes 批起
  定格「标注不阻断」（maint.\<node\>.kb.\<key\>=1.0/0.0 仪表灯），「阻断」
  语义显式挂起（P1）。1A6 批（kb 1.8.0）全量 41 条+后续扩条至 155 条逐条
  增第九键 enforcement（flag 仪表灯/block 断路器，与 severity 正交），
  经 R2 全量追认生效——本批兑现其运行时消费接线（附条件②收口）。
- 决策：

| # | 决策 | 要点 |
|---|------|------|
| 1 | **异常全败丢弃**：design 帧 enforcement=block 条目越门→`KbBlockError`（定义 solution/constraints.py，violations 三联 (node, key, kind) 传入序确定性+逐条可读消息）；raise 点=run_full_calc 内 execute_graph 之后、summary 组装之前——半成品不进 summary/diagnostics/result | 「部分违规返回+标记」否决（污染 result_schema——契约面红线）；「降级 stale」否决（缓存正交面，快照绑定语义另域） |
| 2 | **求值面=design 帧独占**：仅 `ConditionSet.key(conditions.baseline[0])` 帧（禁字符串字面量）；逐 node 判据=app_maintenance._maint_face 三 conjunction 镜像（kind≠boundary_check ∧ unit_kinds∋manifest.unit_id ∧ 表达式字段⊆design dims）∧ enforcement=="block"；求值经 apply_constraints 单行 DataFrame（DSL 单源禁手写） | offline/sensitivity 帧零阻断求值=**架构性缺席**非运行时开关（禁在 app_maintenance.py 加开关——已审面）：offline 帧看 n−1 恶劣态，阻断=检修分析在最需亮灯时刻熄灯；工况分级线**已裁=全部豁免终态**（用户裁决 2026-10-06 P8 呈裁档 R3「按推荐」——adjudication-batch-20261006.md），实现面即终态零追加动作 |
| 3 | **enforcement 装载 fail-fast**：KbConstraint 增第七键 enforcement（缺省 "flag"=直接构造面保守零阻断）；load_kb_constraints 七键必备——缺失/值∉{flag,block}=InvalidConstraintError（装载宽容面零扩大，拼写错误禁静默降级仪表灯档） | 新模块 app_kbgate.py（根模块聚合执法件第十一例——app_maintenance 家族先例，不进 import-linter layers 契约）；app.py 恰 2 行净增接线（496→498 行，500 行墙内） |
| 4 | **消费面三端既有通道零改透出**：server DOMAIN_ERROR_CODES 恰一行 "KbBlockError": 422（名义表——task_status error_code 自动回填，webapp 任务面板/agent {error,hint} 通道既有消费面）；CLI _CALC_FAILURES 并入（退出码 4 族——错误消息+非零退出先例照抄） | **openapi 契约零改**：TaskStatus error_code=anyOf integer\|null，422 已在值域（LoopDivergence 先例同值），无 schema 变更即无 orval/tsc 三步契约工序 |
| 5 | **constraints=() 零行为变更**（铁律二）：空表注入时 run_full_calc 行为/产物与现状逐字节一致（golden serialize 双跑字节同锚）；data/constraint_kb/** 三件零改（本批纯消费不生产——enforcement 155 条已全量在数据） | 正常路径（零违规）零扰动=设计取向：result_schema 零改→无新增静默键；正常性由真实 fixtures 全量扫描零违规（P1 探针 19 件）+golden 零漂双锚证 |

- 替代案否决理由：
  - **选项 0 维持标注**（仪表盘哲学）：P1 用户裁决已选选项 3，逐条声明式
    定级使「全局开关」降解为数据声明——判断权分层（数据面专家逐条定级×
    运行时消费面机械执法）贴合项目声明式真源范式。
  - **工况分级阻断的 offline 侧执法**：分级线（全部豁免 or 仅容量类）纯
    业务判断——**已裁=全部豁免**（用户裁决 2026-10-06 R3，与本批默认
    实现面一致即终态）；effluent 全 block
    与检修工况的内在冲突（offline 帧 n−1 恶劣态）不因本批扩大。
  - **返回+标记**（result 带 blocked 字段）：污染 result_schema=契约面
    红线，且「半成品结果」无消费者语义（全败=诚实失败）。
  - **降级 stale**：stale=快照 vs 当前 design_hash 的缓存正交语义，混入
    阻断态=语义过载。
  - **全局阻断**（不分帧不分条）：杀死检修边缘观测+无视逐条定级数据面，
    选项空间完备性列示（route-20261003 §六）。
- 后果：
  - 正面：P1 挂起项收口——六环闭合（注入→求值→标注→汇总→诊断→**阻断**）；
    断路器逐条数据声明（18 条 block：effluent 12+geometry 拒收 4+spacing
    ERROR 1+红线 boundary 1〔后者经 kind 豁免由符号契约面执法，本门不
    重复〕），专家追认逐条覆盖；真实 fixtures 全量零违规实证（19 件）。
  - 代价：新增根模块 app_kbgate.py（+测试件）；constraints.py 装载器七键
    化（既有六键 fixture 面随批补键——装载宽容面收窄）；测试锁面 371→372
    键（新增 test_app_kbgate.py 一键；另 3 件既有测试件哈希变随批重锁）。
  - 风险与对策：误阻断（数据面 block 误标）→fail-visible 异常+逐条 key
    消息（诊断零猜测）；漏阻断（enforcement 缺失）→装载 fail-fast 拒
    （七键必备）；工况分级线已裁全部豁免终态（2026-10-06 R3）——未来
    若需求收窄为「仅容量类」→后续小批扩展面已隔离（D3 架构性缺席=
    单一接点扩展）。
- 细化归属：kbblock-20261006 实装批（装载面/门面/server 面/ADR 四笔）。
- 参照：.workflow/route-20261003/P1-kb-口径来龙去脉.md（裁决材料四层）；
  .workflow/adjudication-batch-20261004.md R2（追认链+附条件②）；
  ADR-012（诊断并列 artifact——半成品不进 diagnostics 的契约先例）；
  app_maintenance.py（判据镜像源）；docs/status.md（锁面/ADR 计数联动）。
