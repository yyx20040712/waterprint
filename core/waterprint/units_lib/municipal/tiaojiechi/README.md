# municipal_tiaojiechi —— 调节池（市政污水线；M2b2 已实装/M2 正式验收）

均化进水水质水量（调节容积法 HRT 主线），稳定后续处理负荷。

- 输入：上游端口量（chenshachi 旋流沉砂池，沉砂后位置口径——与初沉池
  并列替代关系按工艺配置）
- 输出：下游端口量（aao 生物池或 cass 生物池，替代配置）
- 旧系统对应：mod `tiaojiechi`（交叉对照，非依据）
- golden 绑定：municipal_34760
- 公式组（M2b2 已实装，真源=docs/norms/tiaojiechi.md 起草表 2026-08-25
  数据策略 v2，数值面待追认）：TJ-F1~F13（调节容积停留时间法主线：需
  容积/单池几何 B·L 0.5 m 档/实际容积与停留时间校核/防沉积搅拌功率/
  出水泵平均时均匀输出/溢流管 DN 0.1 m 档/总高/混凝土量）；追认口径
  按表冻结：调节池沉砂后位置、无进水流量过程线按 HRT 法
- 系数通道：factor.tiaojiechi.\*（data/coefficients 0.3.0，经
  app._unit_params 投影）；去除率 removal.tiaojiechi.\*.mod_default
  全 0.0（物理均化无去除——出水质=入水质逐键透传，不经 apply）
- 物理不变性（归后续批进 tests/properties.py）：容积≥时段累积水量、
  水位非负

包内结构遵守 AGENTS.md §11 固定七件套，禁自由发挥；tests/test_compute.py
写毕后由人类执行 scripts/lock_tests.py 锁定。
