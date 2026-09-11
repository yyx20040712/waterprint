# ADR-012：结果可信度诊断通道——独立并列 artifact（P2 次批 2026-09-12）

- 状态：**Accepted**（授权链=op-chain-fix-plan §五 P2 十项+n+41 批尾
  用户裁定「下批=结果可信度面板」+常设指令推荐序；简报
  briefs/task-p2-trust-plan.md）。
- 背景：
  - P2 十项「结果可信度面板（收敛/警告/质量平衡/限值——core 扩面）」
    要求把计算结果的可信度信息（回路收敛质量/单元警告汇总/水量闭合
    审计/出水达标裕度）透出前端。探查实锚（2026-09-12）：warnings
    六键已落 PlantResult 但无面板消费；收敛信息只在 LoopDivergence
    失败面（成功案例的迭代数/残差不记录——loop.py R4"M1 collector"
    记档从未落地）；质量平衡无运行时量化存位；quality.margin() 冻结
    但生产零调用、EffluentStandard 装载挂起（UF-39）而
    constraint_kb 实有 effluent_standard 12 条（GB 18918-2002 一级
    A/B×六项，Ruling 2026-08-31 已追认）。
  - 三个锁面约束方案空间：PlantResult 顶层 _ROOT_KEYS 严格校验
    （缺键/未知键均拒——顶层加键=旧 calc-{task_id}.json 全部拒读，
    scene/cost/elevation/site/exports 五消费方破面）；solve_loop
    四参形态锁定测试锁死（规格头「逐字不改」）；RunEnv 恰七字段
    （锁定集）。
- 决策：

| # | 决策 | 理由 |
|---|------|------|
| D1 | **DiagnosticsReport 走独立并列 artifact**（calc-diag-{task_id}.json，worker 原子写；PlantResult 总线零触碰） | 总线稳定（result_schema R1：总线变更=五消费方+旧项目结果全破；独立文件=旧结果仅缺 diag 文件，trust 端点 diagnostics_available=False 降级呈现，重算后可得） |
| D2 | **收敛统计=solve_loop 零触碰**：executor 在 _solve_loop_group 内包装 compute 闭包（计数=iterations；入参 state×返回 evaluated 按 _step 同款公式复算每步残差→final_residual——确定性计算复算恒等） | 四参锁红线不破；复算与 solve_loop 内部同公式同值 |
| D3 | **execute_graph 增第五可选参 diag_sink: DiagSink \| None = None**（默认 None 行为不变） | 入口冻结测试仅 callable 断言；可选参不破既有调用；诊断通道与 trace_sink 同构（协议注入） |
| D4 | **run_full_calc 增第四可选参 standards: tuple[EffluentStandard, ...] = ()**（server worker 装配注入） | RunEnv 七字段锁零触碰；标准装载归 server 数据装配（constraint_kb 由 server 装配先例）；core 单测可注入 fixture 标准 |
| D5 | **质量平衡=app 层纯投影**（PlantResult.outflows+assembled.edges 拓扑重建单元入流；水/泥线按流体分桶；WATER 取值按工况 flow_case：DESIGN→q_design、AVG→q_avg_daily） | executor 零触碰；终态 outflows 与边拓扑自洽（recycle 边终态值在 src 出端口） |
| D6 | **裕度装载器落地 registry/effluent.py**（load_effluent_standards 读 constraints.json kind=effluent_standard 条目→key 解析 standard_id/指标→expression 正则提限值→EffluentStandard） | L1 装载先例=load_coefficients 同制；quality.py 零 I/O 纪律保持（UF-39 装载面清偿——STANDARDS 符号本体仍不进 quality） |
| D7 | **警告 rollup=server 聚合**（plant.conditions 六键 warnings+unit_id 定位——core 不重复计算） | 数据已在总线；聚合是展示投影 |
| D8 | **新端点 GET /api/calc/trust/{project_id}**（31→32 三处同步） | 无 GET 结果端点先例补位；stale/result_is_stale 四端点先例同款 |

- 后果：
  - 正面：可信度四件套（收敛/警告/水量闭合/裕度）全链路透出；UF-39
    装载面清偿；旧结果文件零破坏（缺 diag 文件降级呈现）；solve_loop/
    RunEnv/PlantResult 三锁面零触碰。
  - 代价：calc 产物由一件变两件（calc-{task_id}.json+calc-diag-
    {task_id}.json，同 task_id 命名绑定+各自原子写；单机单用户无并发
    写同 task 场景，一致性由 worker 串行保证）。
  - 风险与对策：单元级水量偏差对污泥线减量单元（浓缩/消化/脱水/干化）
    属工艺性事实非数值错误——面板文案注记不判红（简报 §一.3）；
    orval 再生成前置杀 5173 vite 句柄（记档三）。
- 参照：简报 briefs/task-p2-trust-plan.md；ADR-003（回路迭代）、
  ADR-010（导出快照——diag artifact 同款确定性纪律）；UF-39。
