# municipal_ziwai —— 紫外消毒（市政污水线；M2b2 已实装/M2 正式验收）

明渠式模块化低压高强紫外消毒（剂量法主线：设计剂量选档+单灯处理量
估灯管数+灯管老化修正），灭活病原微生物保障出水卫生学指标。

- 输入：上游端口量（vxinglvchi V 型滤池，全厂终水上游段）
- 输出：下游端口量（bashi_jiliangcao 巴歇尔计量槽）
- 旧系统对应：mod `ziwai`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2b2 已实装，真源=docs/norms/ziwai.md 起草表 2026-08-25
  数据策略 v2，数值面待追认）：ZW-F1~ZW-F13（剂量法主线：双渠各半
  过流/渠内水深 0.1 m 档/灯管概算整支 ceil+老化修正/模块分置×渠/
  有效接触时间与粪大肠 log 去除/灯管淹没校核/渠总高/混凝土量）；
  追认口径按表冻结（R1 微修后口径）：双渠并联同时运行各半过流+
  超越/模块切换备用——单渠事故 0.78 m/s 超流速带为表内注记非运行时
  警告（运行时只校核实际过流态）
- 系数通道：factor.ziwai.\*（data/coefficients 0.3.0，经
  app._unit_params 投影；设计剂量/穿透率档为选型参数——剂量校核
  语义由 ZW-F4 概算链承载）；去除率 removal.ziwai.\*.mod_default
  全 0.0（物理消毒无去除——出水质=入水质逐键透传不经 apply，消毒
  指标=粪大肠经 dims 的 c_fecal_out 承载）
- 物理不变性（归后续批进 tests/properties.py）：剂量≥设计最小值、
  灯管数为正整数

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
