# municipal_vxinglvchi —— V型滤池（市政污水线；M2b2 已实装/M2 正式验收）

均质滤料 V 型滤池（恒水位过滤、气水反冲洗+表面扫洗三阶段），进一步
去除 SS 与浊度。

- 输入：上游端口量（gaomidu 高密沉淀池）
- 输出：下游端口量（ziwai 紫外消毒；出流=全厂终水上游段）
- 旧系统对应：mod `vxinglvchi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2b2 已实装，真源=docs/norms/vxinglvchi.md 起草表 2026-08-25
  数据策略 v2，数值面待追认）：XL-F1~F19（均质滤料正常滤速主线+强制
  滤速校核：过滤流量含自用水/需面积/分格几何 B·L 0.5 m 档/正常·强制
  滤速校核/气水反冲洗三阶段强度与单格次耗气耗水/日耗水率/池深组成/
  混凝土量）；强制滤速带 11~13 按单向上限校核（低于下限=保守合格）；
  反冲耗水率≤5% 无 data 键且被 selfuse_coef 覆盖（dims 承载，追认点）
- 系数通道：factor.vxinglvchi.\*（data/coefficients 0.3.0，经
  app._unit_params 投影）；去除率 removal.vxinglvchi.\*.mod_default
  （出水质=入质×(1−r) 三指标，同 M1a 形态）
- 物理不变性（归后续批进 tests/properties.py）：强制滤速≤限值、
  反冲洗强度在设计带内

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
