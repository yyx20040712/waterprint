# ADR-006：全厂联合枚举（分层 beam——supersede ADR-005 决策 4）

- 状态：**已接受（B4-3 落地）**（2026-09-20；三段链=调研→拟定→对抗审核
  [B1/W1~W12/N1~N6 全采纳]→主控终裁，定稿件 .workflow/b4-3/design-final.md）
- 背景：ADR-005 决策 4 将全厂联合枚举（跨单元同时寻优）列为远期研究项
  并由服务层显式拒绝多单元请求（防组合爆炸 10^10 量级误解需求）。B4-3
  批解冻该面：单单元枚举语义（ADR-005 决策 1-3/5）保持冻结不动，仅
  决策 4 由本 ADR supersede——多单元寻优经分层 beam 近似（非联合网格
  精确解）落地，单单元拒绝执法点（services/enumeration.py）不松。
- 决策：

| # | 决策 | 要点 |
|---|------|------|
| 1 | 解冻全厂联合枚举，落于 `solution/joint_enumeration/` 新模块；服务端新正门 `POST /api/solution/joint-enumerate`（异步 job 同 worker 制式，静态预检 422 在服务面） | 单单元拒绝执法点不松；多单元正门与旧门并存 |
| 2 | 搜索结构=**分层序列化 beam**：拓扑序逐单元枚举（基线上下文冻结）→top-k 冻结传播→末段 k 组合全厂真值复验（merged 瞬态 DesignState→execute_graph 全厂一次含全工况） | 联合网格+剪枝保留为远期研究项（条件：B12 接线+剪枝 η 有实验数据）；输出 `optimality:'beam_approx'`——推荐方案集非最优解，逼近全局最优仅随 beam_width 单调改善 |
| 3 | 评估口径=**逐行 unit.compute 绕过缓存**（enumerate_solutions 单实现双用——禁双轨实质=唯一计算源）；末段复验直调既有 execute_graph 编排（不新写拓扑序） | CacheKey 粒度改造与 recompute_scope 接线挂账随 B12 重估 |
| 4 | 工况=**基线工况搜索+末段全 ConditionSet 复验**（baseline design/avg 越限=不可行硬门；sensitivity 失守=降权标记不剔除）；all_outer 为一致口径备选（静态预检乘 W_s 统一执法） | 硬门=result summary 出水六指标 compliant 判定（既有 summary 面，不扩 pass_matrix 本体） |
| 5 | 护栏键 `solution.joint.*` 全量入 registry（max_units 6/beam_width 5/max_total_rows 5e5/timeout_s 120/max_full_plant_evals 25/relax_factor 2.0/stage 代理份额/objective 权重 opex.5·energy.3·carbon.2/validation_conditions）；**预算双轴**（rows+full_plant_evals）静态预检 422+运行截断诚实标注（truncated=true） | 双闸定序：rows 静态预检为主（事前拒绝优于事后截断），timeout 运行兜底；N 硬上限 8 由 rows 公式天然守域（N3） |
| 6 | 回路反馈边承载值冻结取**基线设计快照=已知近似**（loop_semantics:'frozen'——方向与单单元上游冻结相反：单单元冻结的是不受决策影响的上游，此处冻结的是下游反馈依赖），B12 recompute_scope 接线后升级不动点迭代 | 输出 `pruning_bias:'baseline_context'` 显式声明基线剪枝偏置（W4 已知限制——需无偏时用 all_outer） |

- 后果：
  - 正面：跨单元寻优从"显式拒绝"变为"分钟级近似推荐"（默认域
    N≤6/g≤500/k≤3 ≈1.8e5 行≈29s 搜索+≤25s 末段复验<120s 看门狗）；
    排序目标三真键（opex/energy/carbon，design 工况）与降权标记制
    （sensitivity 失守排同分纯可行之后）给工程决策面完整语义。
  - 代价：新增 L3 同层消费边 solution→graph（§1c 声明块登记
    independence=true——execute_graph 直调唯一现场=包根 __init__）；
    app_assembly 经类注入防环（solution 层序禁上行——AssembledView/
    AssembleFn/GraphExecutor 协议面+app 正门注入）；服务端端点集
    36→37 破面+假设清单 22→33 条（锁定测试同步=锁面笔）。
  - 风险与对策：beam 近似非全局最优（语义显式标注 beam_approx）；
    基线剪枝可能剪掉 sensitivity 更优组合（pruning_bias 声明+all_outer
    备选）；all_outer 行数×工况数（静态预检统一执法）。
- 细化归属：B4-3 实装批（beam/stage/ranking/diagnose/final_eval 五件
  +registry 伴生件+server 门面/router/worker 面）。
- 参照：.workflow/b4-3/design-final.md（终裁定稿全文——含终裁修正表
  19 项处置）；ADR-005（决策 1-3/5 保持，决策 4 由本文 supersede）。
