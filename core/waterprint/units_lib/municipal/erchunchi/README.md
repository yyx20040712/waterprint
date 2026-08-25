# municipal_erchunchi —— 辐流二沉池（市政污水线；M2a2 已实装/M2 正式验收）

泥水分离与污泥浓缩，维持生物系统污泥平衡。

- 输入：上游端口量（aao 或 cass 生物池）
- 输出：下游端口量（ziwai 紫外消毒或排放）
- 旧系统对应：mod `erchunchi（社区）`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2a2 已实装，真源=docs/norms/erchunchi.md 起草表 2026-08-25
  数据策略 v2，数值面待追认；路线=ADR-008 ②清水表面负荷主控+固体负荷
  校核）：EC-F1~F15（双控面积取大 max/池径/实际负荷校核/回流污泥浓度
  Xr/堰负荷/中心筒/池底坡/总高/混凝土量+校核 HRT）；追认口径按表冻结：
  双圈堰 L=2πD（EC-F11，堰圈口径与 chuchenchi 表 D−1 不对称系起草取舍）
- 系数通道：factor.erchunchi.\*（data/coefficients 0.2.0+0.2.1，经
  app._unit_params 投影；Xr 带/HRT 带=0.2.1 前置键）；去除率
  removal.erchunchi.\*.mod_default；R/X 与 aao 表联动（各包独立声明同值）
- 物理不变性（归后续批进 tests/properties.py）：固体通量≥0、回流污泥
  DS 与生物池排泥守恒

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
