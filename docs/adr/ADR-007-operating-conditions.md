# ADR-007：工况语义（flow 全局 2 档 × pool 逐单元检修敏感性）

- 状态：**已接受（已冻结）**（计划 §14.1；M2 落地）——曾有两版矛盾表述
  （全局 2×2 组合 vs 逐单元敏感性，§16 A3），本 ADR 是唯一语义源。
- 决策：
  1. 工况两轴：
     - `flow_case ∈ {design(最高日最高时), avg(平均时)}`——**全局档位**，
       覆盖 Kz 变化与双流量语义；
     - `pool_config`——**逐单元检修敏感性**：基线（全部全池）跑 flow 两档，
       再对每个勾选校核的单元各跑一次"该单元 n−1、其余全池"；
  2. 运行次数 = 2 + k（k = 受检单元数，线性）；**禁止 2^n 全组合**
     （build_condition_set 输出条数断言进测试）；
  3. 工况对参数的影响走 manifest 声明式映射（受限 DSL，正典写法
     `{"n_active": "n if pool.all_pools else n - 1"}`，DSL 规格见
     core/waterprint/contracts/manifest.py【工况映射 DSL】节）；compute
     内禁止工况 if 分支；
  4. 引擎逐工况整图计算，结果按 condition_key 索引；约束校核/三维/
     图纸/概算全部标注所属工况；UI 可并排对比；
  5. 远期扩展轴（季节水温等）只增枚举值与映射，不动引擎。
- 后果：覆盖 v_force 强制校核等检修场景；工况数线性可控（性能预算
  §18.1 按 2+k 口径）；单元包必须声明工况映射（manifest 校验）。
- 细化归属：M1 condition.py + executor；M2 全线接入。
