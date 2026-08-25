# municipal_chuchenchi —— 辐流初沉池（市政污水线；M2a2 已实装/M2 正式验收）

去除可沉悬浮物与部分 SS/BOD，降低生物处理负荷。

- 输入：上游端口量（chenshachi 旋流沉砂池）
- 输出：下游端口量（aao 生物池或 cass 生物池）
- 旧系统对应：mod `chuchenchi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2a2 已实装，真源=docs/norms/chuchenchi.md 起草表 2026-08-25
  数据策略 v2，数值面待追认）：CC-F1~F18（表面水力负荷法主线：单池
  流量/需蓄面积/池径/实际负荷/有效水深/径深比/中心筒/堰负荷/排泥量/
  泥斗与池底坡/总高/混凝土量）；追认口径按表冻结：双圈堰 L=2π(D−1)
  （CC-F9，单侧口径敏感性见三表注记）
- 系数通道：factor.chuchenchi.\*（data/coefficients 0.2.0+0.2.1，经
  app._unit_params 投影；排泥周期带=0.2.1 前置键）；去除率
  removal.chuchenchi.\*.mod_default
- 物理不变性（归后续批进 tests/properties.py）：去除率∈(0,1)、池容≥0、
  排泥 DS 与 SS 去除量守恒

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
