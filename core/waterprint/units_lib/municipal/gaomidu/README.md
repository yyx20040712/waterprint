# municipal_gaomidu —— 高密沉淀池（市政污水线；M2b2 已实装/M2 正式验收）

混凝+斜管澄清+污泥浓缩一体化的深度处理沉淀（快速混合 PAC+机械絮凝
PAM+斜管沉淀/清水区+污泥浓缩区+污泥回流）。

- 输入：上游端口量（erchunchi 二沉池，深度处理段首单元）
- 输出：下游端口量（vxinglvchi V 型滤池；出流 SS 满足 V 滤进水 <20 mg/L
  联动承诺，business-logic §5 链 1）
- 旧系统对应：mod `gaomidu`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2b2 已实装，真源=docs/norms/gaomidu.md 起草表 2026-08-25
  数据策略 v2，数值面待追认）：GM-F1~F20（液面负荷主控主线：单池流量/
  需蓄斜管面积/池边长 0.5 m 档/实际负荷校核/快混絮凝容积与 G 值法功率/
  GT 校核/污泥回流/干泥量与浓缩排泥/PAC·PAM 药剂/沉淀区总高与絮凝布置
  校核/总高 0.1 m 档/混凝土量）；追认口径按表冻结：仅污泥回流型
  Densadeg 类（ADR-008 ③ 逐字；Actiflo/磁混凝不纳入）；GM-F12 干泥量
  仅计 SS 去除项（PAC 水解絮体泥量增量待追认补键）
- 系数通道：factor.gaomidu.\*（data/coefficients 0.3.0，经
  app._unit_params 投影）；去除率 removal.gaomidu.\*.mod_default
  （出水质=入质×(1−r) 三指标，同 M1a 形态）
- 物理不变性（归后续批进 tests/properties.py）：上升流速≤限值、
  药剂量≥0（与矿井水高密各自独立成包）

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
